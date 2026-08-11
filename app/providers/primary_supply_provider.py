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
from app.domain.supply_semantics import (
    ComponentReconciliation,
    PrimaryProvenance,
    SupplyConcept,
    SupplyFact,
    SupplyMethodology,
    UnitConstant,
)
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence_root import evidence_path
from app.providers.primary_sources import (
    ArbitrumRpc,
    CardanoLedger,
    HyperliquidInfo,
    SubtensorRpc,
)

#: The shape of a stored record. Bumped whenever a reader needs a field
#: an older record does not carry, so the store answers "nothing held"
#: rather than handing back a fact with the new half missing.
#:
#: 2 — S5.1 added `provenance`, which the establishment gate reads.
#:
#: Enforced by `JsonCache` rather than by this module. S5.2a moved the
#: check into the shared contract: this store was the only one that had
#: it, and a guard eleven stores each have to remember is a guard ten of
#: them will not.
SCHEMA = 2


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


#: What each chain reading can and cannot answer for the establishment
#: gate. Declared here beside the reader that takes it, because the
#: reader is the only place these facts are known — and stated in full
#: including the failures, so a gate that cannot be met says why rather
#: than going quiet.
_ARBITRUM_PROVENANCE = PrimaryProvenance(
    surface_is_canonical=True,
    # Deliberately *not* an identity confirmation. The call returns a
    # number and nothing else: no name, no symbol, no ticker. That the
    # address is ARB's is this platform's belief about an address, which
    # is the very shape invariant 2 was written about.
    identity_because="",
    rule_version=ArbitrumRpc.RULE,
    formula="eth_call totalSupply() ÷ 1e18",
    unreconciled_because=(
        "The contract publishes one number and no components, so there "
        "is no identity for it to satisfy. An ERC-20 total is what the "
        "contract says it is."
    ),
    constants=(
        UnitConstant(
            name="wei per ARB (1e18)",
            value=1e18,
            stated_by_source=False,
            cross_check=(
                "a wrong power of ten would move the figure by an order "
                "of magnitude, and CoinGecko's independent total of "
                "10,000,000,000 agrees with this one to 0.0001%"
            ),
        ),
    ),
)


_SUBTENSOR_PROVENANCE = PrimaryProvenance(
    surface_is_canonical=True,
    identity_because=(
        "The Subtensor RPC serves Bittensor's own state and "
        "`SubtensorModule.TotalIssuance` is the chain's storage item. "
        "There is no symbol parameter, so the figure cannot be another "
        "asset's."
    ),
    rule_version=SubtensorRpc.RULE,
    formula="state_getStorage(SubtensorModule.TotalIssuance) ÷ 1e9",
    unreconciled_because=(
        "The chain publishes total issuance and no components to check "
        "it against. Bittensor defines no circulating supply at all, so "
        "there is nothing for issuance to be reconciled with."
    ),
    constants=(
        UnitConstant(
            name="rao per TAO (1e9)",
            value=1e9,
            stated_by_source=False,
            cross_check=(
                "bounded on both sides by figures this platform holds "
                "independently: at 1e8 the chain would report 112m TAO, "
                "above the 21m protocol maximum, and at 1e10 it would "
                "report 1.1m, below every vendor's circulating estimate. "
                "Only 1e9 is consistent with both"
            ),
        ),
    ),
)


#: The parts Cardano's ledger publishes that must add up to its supply.
#: Every one of them, which is what makes the check worth running: drop
#: `fees` and the identity misses by 29,001 ADA, which is small enough
#: to look like rounding and is not.
_CARDANO_PARTS = (
    "circulation",
    "treasury",
    "reward",
    "deposits_stake",
    "deposits_drep",
    "deposits_proposal",
    "fees",
)


def _cardano_provenance(totals: dict[str, Any]) -> PrimaryProvenance:
    """Cardano's own accounting, checked against itself.

    The strongest reconciliation in the corpus and the reason the gate is
    arithmetic: the seven quantities the ledger publishes sum to its
    `supply` **exactly**, to the lovelace. A figure with that behind it
    cannot drift quietly.

    The denomination is checked by a second identity rather than
    remembered on faith — `supply + reserves` comes to 45,000,000,000
    ADA on the nose, which is Cardano's documented maximum. A wrong power
    of ten would not land on it.
    """

    components = tuple(
        (name, int(totals[name])) for name in _CARDANO_PARTS if totals.get(name)
    )

    supply = int(totals["supply"])

    reconciliation = ComponentReconciliation(
        identity=" + ".join(name for name, _ in components) + " = supply",
        components=components,
        total=sum(value for _, value in components),
        against=supply,
        base_unit="lovelace",
    )

    cap = (supply + int(totals["reserves"])) / 1_000_000

    return PrimaryProvenance(
        surface_is_canonical=True,
        identity_because=(
            "The ledger's `/totals` endpoint serves Cardano's own epoch "
            "accounting and takes no symbol, so the figure cannot be "
            "another asset's."
        ),
        rule_version=CardanoLedger.RULE,
        # The reading family, not one field: every Cardano quantity here
        # comes from the same call and the same denomination, and
        # naming one field would misdescribe the other four.
        formula="GET /totals → [0].<quantity> ÷ 1e6",
        reconciliation=reconciliation,
        constants=(
            UnitConstant(
                name="lovelace per ADA (1e6)",
                value=1e6,
                stated_by_source=False,
                cross_check=(
                    "the ledger's own `supply + reserves` comes to exactly "
                    f"{cap:,.0f} ADA at this denomination, which is "
                    "Cardano's documented maximum — a wrong power of ten "
                    "would not land on it"
                ),
            ),
        ),
    )


def _hyperliquid_provenance(
    details: dict[str, Any],
    excluded: list[Any],
) -> PrimaryProvenance:
    """The protocol's own decomposition, checked against its own total.

    `totalSupply − futureEmissions − Σ nonCirculatingUserBalances`
    reproduces the protocol's published `circulatingSupply` to within a
    rounding step. That identity is what lets emitted supply be a
    subtraction rather than a guess — and it is also the evidence that
    the protocol's `totalSupply` counts 412 million tokens that do not
    exist yet.

    No denomination constant appears anywhere: the API publishes decimal
    token units, so there is nothing for this platform to remember.
    """

    # Integers at eight decimal places, so the check is exact rather
    # than floating.
    scale = 100_000_000

    def _units(value: str | float) -> int:
        return round(float(value) * scale)

    def _decimals(value: object) -> int:
        text = str(value)

        return len(text.partition(".")[2]) if "." in text else 0

    parts = (
        ("totalSupply", _units(details["totalSupply"])),
        ("−futureEmissions", -_units(details["futureEmissions"])),
        *(
            (f"−{str(row[0])[:6]}…{str(row[0])[-4:]}", -_units(row[1]))
            for row in excluded
        ),
    )

    # The allowance is one rounding step at the *coarsest* precision the
    # protocol published, per figure in the identity — read from the
    # payload rather than assumed. Assuming eight decimals was tried
    # first and failed on a response that published `circulatingSupply`
    # to four: the identity was sound and the tolerance was fiction.
    published = [
        details["totalSupply"],
        details["futureEmissions"],
        details["circulatingSupply"],
        *(row[1] for row in excluded),
    ]

    step = 10 ** max(0, 8 - min(_decimals(value) for value in published))

    return PrimaryProvenance(
        surface_is_canonical=True,
        identity_because=(
            "The protocol's own `tokenDetails` response names the token "
            f"as {details.get('name', 'HYPE')}, so the figures are tied to "
            "this asset by the source rather than by an address this "
            "platform believes in."
        ),
        rule_version=HyperliquidInfo.RULE,
        formula=(
            "the tokenDetails decomposition — totalSupply, "
            "futureEmissions and the named non-circulating balances"
        ),
        reconciliation=ComponentReconciliation(
            identity=(
                "totalSupply − futureEmissions − nonCirculatingUserBalances "
                "= circulatingSupply"
            ),
            components=parts,
            total=sum(value for _, value in parts),
            against=_units(details["circulatingSupply"]),
            base_unit="HYPE at 8dp",
            # One rounding step per figure, at the precision the protocol
            # actually published. Cardano gets no such allowance because
            # its ledger publishes integers and its residual is zero.
            tolerance=len(parts) * step,
        ),
        constants=(),
    )


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
            return self._one(self._arbitrum.total_supply(), "ARB", _ARBITRUM_PROVENANCE)

        if normalized == "TAO":
            return self._one(
                self._subtensor.total_issuance(), "TAO", _SUBTENSOR_PROVENANCE
            )

        return ()

    # ── one chain at a time ─────────────────────────────────────────

    @staticmethod
    def _one(
        computation: Any,
        unit: str,
        provenance: PrimaryProvenance,
    ) -> tuple[SupplyFact, ...]:
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
                provenance=provenance,
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

        provenance = _cardano_provenance(totals)

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
                provenance=provenance,
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
            # The protocol maximum, derived from the ledger rather than
            # taken from a vendor. `supply + reserves` comes to exactly
            # 45,000,000,000 ADA: the reserves pot *is* the unissued
            # remainder, so the chain states its own cap by accounting
            # for every lovelace on either side of it. Two vendors say
            # the same number; this says why it is that number.
            SupplyFact(
                concept=SupplyConcept.MAX_SUPPLY,
                methodology=PROTOCOL_CAP,
                value=(int(totals["supply"]) + int(totals["reserves"])) / unit,
                unit="ADA",
                authority=EvidenceAuthority.PRIMARY_DERIVED,
                standing=EvidenceStanding.CLAIMED,
                source=CardanoLedger.SURFACE.name,
                observed_at=observed_at,
                components=(
                    "GET /totals → [0].supply",
                    "GET /totals → [0].reserves",
                ),
                because=(
                    "The ledger's issued supply plus the reserves it has "
                    "still to issue. Not a figure Cardano publishes as a "
                    "cap — it is the cap falling out of the chain's own "
                    "accounting, which is a stronger thing."
                ),
                provenance=provenance,
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

        provenance = _hyperliquid_provenance(details, list(excluded))

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
                provenance=provenance,
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
                provenance=provenance,
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
                provenance=provenance,
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
                provenance=provenance,
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
                    provenance=provenance,
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
        # Schema 2 with no migration from 1: a version-1 record carries
        # no provenance, and the establishment gate reads provenance, so
        # there is nothing to bring forward. It re-acquires instead —
        # which is a keyless chain read, and cheap.
        self._cache = cache or JsonCache(
            evidence_path("cache", "primary_supply"),
            schema=SCHEMA,
        )
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
        # No shape check here any more. `JsonCache` refuses a record
        # written under a different schema before this method sees it,
        # which is why the schema is declared where the cache is built.
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
        "provenance": _encode_provenance(fact.provenance),
    }


def _encode_provenance(provenance: PrimaryProvenance | None) -> dict[str, Any] | None:
    """Stored in full, because the gate runs on read.

    A reconciliation summarised to a boolean would be a stored verdict,
    and this platform's rule is that verdicts derive on read. The
    components are kept as integers so the identity can be re-added by
    whoever is reading it.
    """

    if provenance is None:
        return None

    return {
        "surface_is_canonical": provenance.surface_is_canonical,
        "identity_because": provenance.identity_because,
        "rule_version": provenance.rule_version,
        "formula": provenance.formula,
        "unreconciled_because": provenance.unreconciled_because,
        "constants": [
            {
                "name": constant.name,
                "value": constant.value,
                "stated_by_source": constant.stated_by_source,
                "cross_check": constant.cross_check,
            }
            for constant in provenance.constants
        ],
        "reconciliation": (
            {
                "identity": provenance.reconciliation.identity,
                "components": [
                    [name, value]
                    for name, value in provenance.reconciliation.components
                ],
                "total": provenance.reconciliation.total,
                "against": provenance.reconciliation.against,
                "base_unit": provenance.reconciliation.base_unit,
                "tolerance": provenance.reconciliation.tolerance,
            }
            if provenance.reconciliation is not None
            else None
        ),
    }


def _decode_provenance(row: Any) -> PrimaryProvenance | None:
    if not isinstance(row, dict):
        return None

    reconciliation = row.get("reconciliation")

    try:
        return PrimaryProvenance(
            surface_is_canonical=bool(row.get("surface_is_canonical")),
            identity_because=str(row.get("identity_because") or ""),
            rule_version=str(row.get("rule_version") or ""),
            formula=str(row.get("formula") or ""),
            unreconciled_because=row.get("unreconciled_because"),
            constants=tuple(
                UnitConstant(
                    name=str(constant["name"]),
                    value=float(constant["value"]),
                    stated_by_source=bool(constant.get("stated_by_source")),
                    cross_check=constant.get("cross_check"),
                )
                for constant in row.get("constants") or ()
                if isinstance(constant, dict)
            ),
            reconciliation=(
                ComponentReconciliation(
                    identity=str(reconciliation["identity"]),
                    components=tuple(
                        (str(name), int(value))
                        for name, value in reconciliation["components"]
                    ),
                    total=int(reconciliation["total"]),
                    against=int(reconciliation["against"]),
                    base_unit=str(reconciliation["base_unit"]),
                    tolerance=int(reconciliation.get("tolerance") or 0),
                )
                if isinstance(reconciliation, dict)
                else None
            ),
        )
    except (KeyError, TypeError, ValueError):
        # A record this platform cannot read is a record with no
        # provenance, which fails every gate that needs it. That is the
        # right outcome: a half-decoded reconciliation would establish a
        # figure on evidence nobody can see.
        return None


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
        provenance=_decode_provenance(row.get("provenance")),
    )
