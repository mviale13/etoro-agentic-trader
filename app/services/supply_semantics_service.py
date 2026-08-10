"""One token's supply, read as a vocabulary rather than as a number.

A read-only door in the family every crypto service on this platform
belongs to: it asks the stores what was acquired and stops. It fetches
nothing, asks no model and writes nothing.

What it does is the S4.6 rule, applied:

> Two numbers only conflict if they claim to represent the same thing.

Vendor claims arrive from the token-facts store under labels they share.
Each is mapped to the quantity it actually reports, chain readings are
added as the quantities the ledger itself defines, and every comparable
pair is judged. Cardano's three-way disagreement dissolves because the
three vendors were measuring three ledger concepts; Hyperliquid's
survives, because two of its three sources publish no definition and an
unexplained figure is not evidence of a different one.

**No standing is rewritten and no score can move.** The token-facts gate
keeps its own verdicts — `CompanyFactsService` reads them and the crypto
quality signal reads that, so promoting a standing here would change a
factor. This layer reports what the semantics show; wiring it into
`judge()` is a ruling the owner has not made.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.supply_mappings import mappings_for
from app.domain.supply_semantics import (
    SupplyComparison,
    SupplyFact,
    SupplyPicture,
    compare,
)
from app.domain.token_fact_validation import TokenClaimSet
from app.providers.primary_supply_provider import CachedPrimarySupplyProvider
from app.services.token_facts_service import (
    CoinGeckoClaimSource,
    GeneralistClaimSource,
    NativeClaimSource,
)

#: The labels a vendor publishes that this layer reads at all.
_SUPPLY_FACTS = ("circulating_supply", "total_supply", "max_supply")


class PrimarySupplyReader(Protocol):
    """The stored chain readings, read-only."""

    def facts(self, symbol: str) -> tuple[SupplyFact, ...]: ...


class ClaimSource(Protocol):
    """One vendor's unjudged claims — the same door the gate reads."""

    def claim_set(self, symbol: str) -> TokenClaimSet | None: ...


class SupplySemanticsService:
    """What each supply number counts, and which of them really disagree."""

    def __init__(
        self,
        sources: tuple[ClaimSource, ...] | None = None,
        primary: PrimarySupplyReader | None = None,
    ) -> None:
        # The *unjudged* claims, not the gate's verdicts. A conflicted
        # fact serves no value, and the vendors whose figures S1
        # conflicted are precisely the ones this layer exists to read —
        # so taking the judged output would hide its own evidence.
        self._sources: tuple[ClaimSource, ...] = sources or (
            NativeClaimSource(),
            CoinGeckoClaimSource(),
            GeneralistClaimSource(),
        )

        self._primary: PrimarySupplyReader = (
            primary or CachedPrimarySupplyProvider.stored()
        )

    def established(
        self,
        symbol: str,
        asset_class: AssetClass | None,
    ) -> SupplyPicture | None:
        """One token's supply picture, or None for anything that is not one."""

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()

        vendor = self._vendor_facts(normalized)

        chain = self._chain_facts(normalized)

        facts = chain + vendor

        if not facts:
            return SupplyPicture(
                symbol=normalized,
                unavailable_because=(
                    "Nothing has been read about this token's supply. "
                    "Reading it is an explicit spend, and no surface "
                    "takes it — `movrvest acquire` does."
                ),
            )

        return SupplyPicture(
            symbol=normalized,
            facts=facts,
            comparisons=self._compare(facts),
            unresolved=self._unresolved(normalized, chain, facts),
        )

    # ── the two sources of fact ─────────────────────────────────────

    def _chain_facts(self, symbol: str) -> tuple[SupplyFact, ...]:
        try:
            return tuple(self._primary.facts(symbol))
        except Exception:
            return ()

    def _vendor_facts(self, symbol: str) -> tuple[SupplyFact, ...]:
        """Every vendor claim, mapped to the quantity it actually reports.

        Read from the claim sources rather than from the gate. Cardano is
        the reason twice over: the gate serves no value for a conflicted
        fact, and the reading it *rejected* turned out to match the
        ledger's own circulation exactly. A layer that only saw survivors
        would have hidden its own best evidence.
        """

        facts: list[SupplyFact] = []

        for source in self._sources:
            try:
                claims = source.claim_set(symbol)
            except Exception:
                claims = None

            if claims is None:
                continue

            facts.extend(self._mapped(symbol, claims))

        return tuple(facts)

    @staticmethod
    def _mapped(symbol: str, claims: TokenClaimSet) -> tuple[SupplyFact, ...]:
        facts: list[SupplyFact] = []

        values = {
            "circulating_supply": claims.circulating_supply,
            "total_supply": claims.total_supply,
            "max_supply": claims.max_supply,
        }

        for mapping in mappings_for(symbol, claims.source):
            value = values.get(mapping.fact)

            if not value:
                continue

            facts.append(
                SupplyFact(
                    concept=mapping.concept,
                    methodology=mapping.methodology,
                    value=value,
                    unit="tokens",
                    # Mapping a vendor's number to a ledger concept
                    # explains what it counts. It does not turn the
                    # vendor into a chain.
                    authority=EvidenceAuthority.SECONDARY_AGGREGATE,
                    standing=EvidenceStanding.CLAIMED,
                    source=claims.source,
                    observed_at=claims.read.observed_at,
                    reported_as=mapping.reported_as,
                    because=mapping.basis or None,
                    caveats=mapping.caveats,
                )
            )

        return tuple(facts)

    # ── the rule ────────────────────────────────────────────────────

    @staticmethod
    def _compare(facts: tuple[SupplyFact, ...]) -> tuple[SupplyComparison, ...]:
        """Every pair worth judging, judged.

        Pairs of different concepts are skipped rather than reported as
        coexisting: they were never candidates for a conflict, and
        listing them would bury the two or three comparisons that carry
        information.
        """

        comparisons: list[SupplyComparison] = []

        for index, left in enumerate(facts):
            for right in facts[index + 1 :]:
                if left.concept is not right.concept:
                    continue

                if left.source == right.source:
                    continue

                comparisons.append(compare(left, right))

        return tuple(comparisons)

    @staticmethod
    def _unresolved(
        symbol: str,
        chain: tuple[SupplyFact, ...],
        facts: tuple[SupplyFact, ...],
    ) -> tuple[str, ...]:
        """What is still missing, named rather than left blank."""

        missing: list[str] = []

        if not chain:
            missing.append(
                f"No chain reading for {symbol}. Every figure here is a "
                "vendor's, so nothing can say what any of them counts."
            )

        undisclosed = sorted(
            {
                fact.source
                for fact in facts
                if fact.concept.is_methodology_dependent
                and not fact.methodology.disclosed
            }
        )

        if undisclosed:
            missing.append(
                "The exclusion set behind "
                + ", ".join(undisclosed)
                + "'s circulating figure is not published, so this "
                "platform cannot say whether it counts the same tokens "
                "as anyone else's."
            )

        return tuple(missing)
