"""Read each chain's own supply quantities, and store what they are.

The acquisition half of the supply vocabulary. S4.5's experiment stored
nothing on purpose — it was a measurement of this platform. S4.6 needs
the same readings on a dossier, and the platform's rule is that **a page
view serves what was acquired**, so the readings are taken here by
`movrvest acquire` and served from the store.

What is stored is a *concept*, not a number under a shared label: the
ledger's `supply` is recorded as emitted supply, its `circulation` as a
circulating estimate under the ledger's own definition, and Hyperliquid's
excluded addresses as excluded balances. The methodology travels with
each figure as a key, and is resolved on read — so a better wording
reaches a stored record without a re-read, the discipline the knowledge
layer already lives by.

Four chains answer today. A security with no reader here has no primary
supply evidence, which is different from having none in the world.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.supply_mappings import (
    CARDANO_CIRCULATION,
    CARDANO_SUPPLY,
    HYPERLIQUID_EXCLUSIONS,
    PROTOCOL_CAP,
    PROTOCOL_EMITTED,
)
from app.domain.supply_semantics import SupplyConcept, SupplyFact, SupplyMethodology
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.providers.primary_sources import (
    ArbitrumRpc,
    CardanoLedger,
    HyperliquidInfo,
    SubtensorRpc,
)

#: Every methodology a stored record may name, resolved on read.
METHODOLOGIES: dict[str, SupplyMethodology] = {
    methodology.key: methodology
    for methodology in (
        PROTOCOL_CAP,
        PROTOCOL_EMITTED,
        CARDANO_SUPPLY,
        CARDANO_CIRCULATION,
        HYPERLIQUID_EXCLUSIONS,
    )
}


class PrimarySupplyProvider:
    """One reading of every chain supply quantity this platform can reach."""

    def __init__(
        self,
        cardano: CardanoLedger | None = None,
        hyperliquid: HyperliquidInfo | None = None,
        arbitrum: ArbitrumRpc | None = None,
        subtensor: SubtensorRpc | None = None,
    ) -> None:
        self._cardano = cardano or CardanoLedger()
        self._hyperliquid = hyperliquid or HyperliquidInfo()
        self._arbitrum = arbitrum or ArbitrumRpc()
        self._subtensor = subtensor or SubtensorRpc()

    def facts(self, symbol: str) -> tuple[SupplyFact, ...]:
        """Every primary supply quantity for one security, or nothing."""

        normalized = symbol.upper().strip()

        if normalized == "ADA":
            return self._cardano_facts()

        if normalized == "HYPE":
            return self._hyperliquid_facts()

        if normalized == "ARB":
            return self._one(self._arbitrum.total_supply(), "ARB")

        if normalized == "TAO":
            return self._one(self._subtensor.total_issuance(), "TAO")

        return ()

    # ── one chain at a time ─────────────────────────────────────────

    @staticmethod
    def _one(computation: Any, unit: str) -> tuple[SupplyFact, ...]:
        """A single emitted-supply reading, wrapped as a concept."""

        return (
            SupplyFact(
                concept=SupplyConcept.EMITTED_SUPPLY,
                methodology=PROTOCOL_EMITTED,
                value=computation.value,
                unit=unit,
                authority=computation.authority,
                standing=computation.standing,
                source=computation.surface.name,
                observed_at=computation.window.observed_at,
                components=computation.inputs,
                because=computation.because,
                caveats=computation.caveats,
            ),
        )

    def _cardano_facts(self) -> tuple[SupplyFact, ...]:
        """The ledger's own quantities, each recorded as what it is.

        The reading that dissolves a three-way vendor disagreement: the
        ledger publishes the concepts, and every vendor turns out to be
        reporting one of them.
        """

        totals = self._cardano.totals()

        observed_at = datetime.now(UTC)

        unit = 1_000_000

        def _fact(
            field: str,
            concept: SupplyConcept,
            methodology: SupplyMethodology,
            caveats: tuple[str, ...] = (),
        ) -> SupplyFact:
            return SupplyFact(
                concept=concept,
                methodology=methodology,
                value=int(totals[field]) / unit,
                unit="ADA",
                authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                standing=EvidenceStanding.CLAIMED,
                source=CardanoLedger.SURFACE.name,
                observed_at=observed_at,
                reported_as=field,
                components=(f"GET /totals → [0].{field}",),
                because=(
                    "The ledger's own epoch accounting, read from the "
                    "chain rather than from a party's view of it."
                ),
                caveats=caveats,
            )

        return (
            _fact("supply", SupplyConcept.EMITTED_SUPPLY, CARDANO_SUPPLY),
            _fact(
                "circulation",
                SupplyConcept.CIRCULATING_ESTIMATE,
                CARDANO_CIRCULATION,
            ),
            _fact(
                "treasury",
                SupplyConcept.EXCLUDED_BALANCE,
                CARDANO_CIRCULATION,
                caveats=(
                    "Excluded by the ledger's own circulation figure and "
                    "counted by some vendors. Which is right is a policy "
                    "question, not a measurement.",
                ),
            ),
            _fact(
                "reward",
                SupplyConcept.EXCLUDED_BALANCE,
                CARDANO_CIRCULATION,
                caveats=(
                    "Earned and not withdrawn. Counting it is the whole "
                    "difference between two vendors' circulating figures.",
                ),
            ),
        )

    def _hyperliquid_facts(self) -> tuple[SupplyFact, ...]:
        """The protocol's own accounting, decomposed rather than copied.

        The decisive detail is `futureEmissions`: the protocol's
        `totalSupply` counts tokens that do not exist yet, so emitted
        supply is a subtraction rather than a field.
        """

        details = self._hyperliquid.token()

        observed_at = datetime.now(UTC)

        total = float(details["totalSupply"])
        future = float(details["futureEmissions"])
        circulating = float(details["circulatingSupply"])

        excluded = details.get("nonCirculatingUserBalances") or []

        facts = [
            SupplyFact(
                concept=SupplyConcept.EMITTED_SUPPLY,
                methodology=PROTOCOL_EMITTED,
                value=total - future,
                unit="HYPE",
                authority=EvidenceAuthority.PRIMARY_DERIVED,
                standing=EvidenceStanding.CLAIMED,
                source=HyperliquidInfo.SURFACE.name,
                observed_at=observed_at,
                components=(
                    "info(tokenDetails).totalSupply",
                    "info(tokenDetails).futureEmissions",
                ),
                because=(
                    "totalSupply minus futureEmissions. The protocol's "
                    "own total counts tokens it has not issued, so this "
                    "subtraction is what makes it a figure about the "
                    "present."
                ),
            ),
            SupplyFact(
                concept=SupplyConcept.FUTURE_EMISSIONS,
                methodology=PROTOCOL_EMITTED,
                value=future,
                unit="HYPE",
                authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                standing=EvidenceStanding.CLAIMED,
                source=HyperliquidInfo.SURFACE.name,
                observed_at=observed_at,
                reported_as="futureEmissions",
                components=("info(tokenDetails).futureEmissions",),
                because=(
                    "Published by the protocol, and counted inside its own totalSupply."
                ),
            ),
            SupplyFact(
                concept=SupplyConcept.CIRCULATING_ESTIMATE,
                methodology=HYPERLIQUID_EXCLUSIONS,
                value=circulating,
                unit="HYPE",
                authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                standing=EvidenceStanding.CLAIMED,
                source=HyperliquidInfo.SURFACE.name,
                observed_at=observed_at,
                reported_as="circulatingSupply",
                components=(
                    "info(tokenDetails).totalSupply",
                    "info(tokenDetails).nonCirculatingUserBalances",
                    "info(tokenDetails).futureEmissions",
                ),
                because=(
                    "The protocol's own figure, and it reconciles exactly "
                    "against its own components — emitted supply less the "
                    "four addresses it names."
                ),
                caveats=(
                    "The protocol's estimate under the protocol's policy. "
                    "Another party excluding a different set gets a "
                    "different and equally defensible number.",
                ),
            ),
            SupplyFact(
                concept=SupplyConcept.MAX_SUPPLY,
                methodology=PROTOCOL_CAP,
                value=float(details["maxSupply"]),
                unit="HYPE",
                authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                standing=EvidenceStanding.CLAIMED,
                source=HyperliquidInfo.SURFACE.name,
                observed_at=observed_at,
                reported_as="maxSupply",
                components=("info(tokenDetails).maxSupply",),
            ),
        ]

        for address, balance in ((str(row[0]), float(row[1])) for row in excluded):
            facts.append(
                SupplyFact(
                    concept=SupplyConcept.EXCLUDED_BALANCE,
                    methodology=HYPERLIQUID_EXCLUSIONS,
                    value=balance,
                    unit="HYPE",
                    authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                    standing=EvidenceStanding.CLAIMED,
                    source=HyperliquidInfo.SURFACE.name,
                    observed_at=observed_at,
                    reported_as=address,
                    components=("info(tokenDetails).nonCirculatingUserBalances",),
                    because=(
                        "Named by the protocol as not circulating. The "
                        f"balance at {address[:6]}…{address[-4:]} is one "
                        "of the four subtractions behind its own figure."
                    ),
                )
            )

        return tuple(facts)


class CachedPrimarySupplyProvider:
    """Chain supply once a day, behind the platform's two doors."""

    def __init__(
        self,
        provider: PrimarySupplyProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or PrimarySupplyProvider()
        self._cache = cache or JsonCache("data/cache/primary_supply")
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedPrimarySupplyProvider:
        """What has already been read, and nothing else."""

        return cls(cache=cache, acquires=False)

    def facts(self, symbol: str) -> tuple[SupplyFact, ...]:
        key = symbol.upper().strip()

        entry = self._cache.read(key)

        held = self._restore(entry) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return ()

        try:
            facts = self._provider.facts(key)
        except Exception:
            return held or ()

        if facts:
            self._cache.write(key, {"facts": [_encode(fact) for fact in facts]})

        return facts

    @staticmethod
    def _restore(entry: CachedEntry) -> tuple[SupplyFact, ...] | None:
        rows = entry.value.get("facts")

        if not isinstance(rows, list):
            return None

        restored = [_decode(row) for row in rows if isinstance(row, dict)]

        return tuple(item for item in restored if item is not None)


def _encode(fact: SupplyFact) -> dict[str, Any]:
    """Stored by concept and methodology *key* — never by prose.

    The wording of a methodology is resolved on read, so improving it
    reaches every stored record without a re-read.
    """

    return {
        "concept": fact.concept.value,
        "methodology": fact.methodology.key,
        "defined_by": fact.methodology.defined_by,
        "value": fact.value,
        "unit": fact.unit,
        "authority": fact.authority.value,
        "standing": fact.standing.value,
        "source": fact.source,
        "observed_at": (
            fact.observed_at.isoformat() if fact.observed_at is not None else None
        ),
        "reported_as": fact.reported_as,
        "components": list(fact.components),
        "because": fact.because,
        "caveats": list(fact.caveats),
    }


def _decode(row: dict[str, Any]) -> SupplyFact | None:
    from app.domain.supply_mappings import undisclosed

    try:
        concept = SupplyConcept(str(row["concept"]))
        authority = EvidenceAuthority(str(row["authority"]))
        standing = EvidenceStanding(str(row["standing"]))
        value = float(row["value"])
    except (KeyError, ValueError, TypeError):
        return None

    key = str(row.get("methodology") or "")

    methodology = METHODOLOGIES.get(key) or undisclosed(
        str(row.get("defined_by") or row.get("source") or "an unnamed source")
    )

    observed = row.get("observed_at")

    return SupplyFact(
        concept=concept,
        methodology=methodology,
        value=value,
        unit=str(row.get("unit") or ""),
        authority=authority,
        standing=standing,
        source=str(row.get("source") or ""),
        observed_at=(
            datetime.fromisoformat(str(observed)) if isinstance(observed, str) else None
        ),
        reported_as=row.get("reported_as"),
        components=tuple(row.get("components") or ()),
        because=row.get("because"),
        caveats=tuple(row.get("caveats") or ()),
    )
