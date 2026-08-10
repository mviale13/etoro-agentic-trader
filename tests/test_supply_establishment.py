"""S5.1: when a chain reading may establish without a second vendor.

The Model C gate. One test per requirement, plus the two findings that
decided the slice: that Cardano's ledger reconciles to the lovelace, and
that the emitted share and the supply an investor is actually exposed to
can move in opposite directions.

**Nothing here reads the live store or the network.** Every case runs on
the readings recorded during the S5.1 measurement on 2026-08-10 — the
ledger's own epoch totals and the protocol's own token accounting —
pushed through the real provider and the real gate.
"""

from __future__ import annotations

import inspect
import pathlib
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.provenance import Provenance
from app.domain.supply_establishment import ModelCRequirement, assess
from app.domain.supply_mappings import PROTOCOL_EMITTED
from app.domain.supply_semantics import (
    ComponentReconciliation,
    PrimaryProvenance,
    SupplyConcept,
    SupplyFact,
    UnitConstant,
)
from app.domain.token_fact_validation import TokenClaimSet
from app.providers.primary_supply_provider import (
    SCHEMA,
    PrimarySupplyProvider,
    _decode,
    _encode,
)
from app.services.supply_semantics_service import SupplySemanticsService

READ = datetime(2026, 8, 10, 13, 0, tzinfo=UTC)


# ── the recorded readings ───────────────────────────────────────────

#: Cardano's ledger at epoch 648, in lovelace, exactly as it published
#: them. The seven quantities below sum to `supply` with no residual,
#: which is the measurement the whole gate turns on.
_ADA_LEDGER = {
    "epoch_no": 648,
    "circulation": "36550320207145109",
    "treasury": "1450053248585177",
    "reward": "797735740883044",
    "supply": "38803572882173527",
    "reserves": "6196427117826473",
    "fees": "29001560197",
    "deposits_stake": "4404684000000",
    "deposits_drep": "530000000000",
    "deposits_proposal": "500000000000",
}

#: Hyperliquid's own accounting. `totalSupply` counting 412m unissued
#: tokens is the finding, not a transcription slip.
_HYPE_TOKEN = {
    "name": "HYPE",
    "maxSupply": "1000000000.0",
    "totalSupply": "999044028.5858",
    "circulatingSupply": "299022746.6799",
    "futureEmissions": "412513564.9696",
    "nonCirculatingUserBalances": [
        ["0x43e9abea1910387c4292bca4b94de81462f8a251", "241194257.8480974734"],
        ["0xfefefefefefefefefefefefefefefefefefefefe", "46311782.5847392306"],
        ["0x0000000000000000000000000000000000000000", "1673.78676324"],
        ["0x000000000000000000000000000000000000dead", "2.71671343"],
    ],
}


class _FakeCardano:
    SURFACE = type("S", (), {"name": "Cardano ledger totals"})
    RULE = "ada-ledger-supply/1"

    @staticmethod
    def totals() -> dict[str, object]:
        return dict(_ADA_LEDGER)


class _FakeHyperliquid:
    SURFACE = type("S", (), {"name": "Hyperliquid info API"})
    RULE = "hype-supply-reconciliation/1"

    @staticmethod
    def token() -> dict[str, object]:
        return dict(_HYPE_TOKEN)


def _facts(symbol: str) -> tuple[SupplyFact, ...]:
    provider = PrimarySupplyProvider(
        cardano=_FakeCardano(),  # type: ignore[arg-type]
        hyperliquid=_FakeHyperliquid(),  # type: ignore[arg-type]
    )

    return provider.facts(symbol)


def _of(symbol: str, concept: SupplyConcept) -> SupplyFact:
    for fact in _facts(symbol):
        if fact.concept is concept:
            return fact

    raise AssertionError((symbol, concept))


# ── gate 2: the reconciliation that decided the slice ───────────────


def test_cardano_reconciles_to_the_lovelace() -> None:
    """The strongest evidence in the corpus, and it is arithmetic.

    Seven quantities the ledger publishes, summing to its own `supply`
    with a residual of exactly zero. A figure with that behind it cannot
    drift quietly; one without has nowhere to fail.
    """

    fact = _of("ADA", SupplyConcept.EMITTED_SUPPLY)

    assert fact.provenance is not None

    reconciliation = fact.provenance.reconciliation

    assert reconciliation is not None
    assert reconciliation.residual == 0
    assert reconciliation.holds
    assert reconciliation.base_unit == "lovelace"

    # Every part, not a convenient subset: drop `fees` and the identity
    # misses by 29,001 ADA, which is small enough to look like rounding.
    names = [name for name, _ in reconciliation.components]

    assert "fees" in names
    assert len(names) == 7


def test_dropping_one_component_breaks_the_identity() -> None:
    """The check has teeth, demonstrated rather than asserted."""

    fact = _of("ADA", SupplyConcept.EMITTED_SUPPLY)

    assert fact.provenance is not None

    full = fact.provenance.reconciliation

    assert full is not None

    without_fees = ComponentReconciliation(
        identity=full.identity,
        components=tuple(
            (name, value) for name, value in full.components if name != "fees"
        ),
        total=sum(value for name, value in full.components if name != "fees"),
        against=full.against,
        base_unit=full.base_unit,
    )

    assert not without_fees.holds
    assert without_fees.residual == -29_001_560_197


def test_hyperliquid_reproduces_its_own_circulating_figure() -> None:
    """`totalSupply − futureEmissions − excluded = circulatingSupply`.

    The identity that lets emitted supply be a subtraction rather than a
    guess — and the evidence that the protocol's own total counts 412
    million tokens that do not exist yet.
    """

    fact = _of("HYPE", SupplyConcept.EMITTED_SUPPLY)

    assert fact.provenance is not None

    reconciliation = fact.provenance.reconciliation

    assert reconciliation is not None
    assert reconciliation.holds

    # Rounded inputs, so the allowance is one rounding step per figure
    # at the precision the protocol published — never a percentage, and
    # never a number this platform assumed. This response publishes
    # `circulatingSupply` to four decimals, so the step is 1e-4 and the
    # allowance is six of them: 0.0006 HYPE against a billion.
    assert abs(reconciliation.residual) <= reconciliation.tolerance
    assert reconciliation.tolerance == len(reconciliation.components) * 10_000
    assert reconciliation.tolerance / 100_000_000 < 0.001


# ── gate 3: the constant that caused all this ───────────────────────


def test_a_remembered_constant_with_no_cross_check_fails() -> None:
    """The blob-fee regression, as a rule rather than a memory.

    Computed with the protocol constant this platform *knew*, Ethereum's
    blob base fee came out wrong by about 850 million times. A constant
    is safe when the source states it or when a wrong value would have
    been visibly contradicted — never merely because the arithmetic ran.
    """

    remembered = UnitConstant(
        name="a protocol parameter this platform knew",
        value=3_338_477.0,
        stated_by_source=False,
        cross_check=None,
    )

    assert not remembered.is_safe

    fact = SupplyFact(
        concept=SupplyConcept.EMITTED_SUPPLY,
        methodology=PROTOCOL_EMITTED,
        value=1.0,
        unit="X",
        authority=EvidenceAuthority.PRIMARY_DERIVED,
        standing=EvidenceStanding.CLAIMED,
        source="a chain",
        observed_at=READ,
        components=("an input",),
        provenance=PrimaryProvenance(
            surface_is_canonical=True,
            identity_because="the endpoint is the chain",
            rule_version="x/1",
            formula="f(x)",
            # Every other gate satisfied, so the constant is the only
            # thing left to fail on.
            reconciliation=ComponentReconciliation(
                identity="a = a",
                components=(("a", 1),),
                total=1,
                against=1,
                base_unit="unit",
            ),
            constants=(remembered,),
        ),
    )

    failed = {gate.requirement for gate in assess(fact).failed}

    assert ModelCRequirement.CONSTANTS in failed
    assert not assess(fact).establishes


def test_hyperliquid_needs_no_constant_at_all() -> None:
    """The safest possible answer to gate 3: nothing to remember.

    The protocol publishes decimal token units, so no denomination is
    applied anywhere.
    """

    fact = _of("HYPE", SupplyConcept.EMITTED_SUPPLY)

    assert fact.provenance is not None
    assert fact.provenance.constants == ()


def test_cardanos_denomination_is_checked_by_a_second_identity() -> None:
    """Remembered, and caught if wrong.

    `supply + reserves` comes to exactly 45,000,000,000 ADA at 1e6,
    which is Cardano's documented maximum. A wrong power of ten would
    not land on it.
    """

    fact = _of("ADA", SupplyConcept.EMITTED_SUPPLY)

    assert fact.provenance is not None

    constant = fact.provenance.constants[0]

    assert not constant.stated_by_source
    assert constant.cross_check is not None
    assert "45,000,000,000" in constant.cross_check
    assert constant.is_safe


# ── the corpus outcome ──────────────────────────────────────────────


def test_ada_and_hype_emitted_supply_establish() -> None:
    """Two readings clear all six. They are the first on this platform."""

    for symbol in ("ADA", "HYPE"):
        fact = _of(symbol, SupplyConcept.EMITTED_SUPPLY)

        verdict = assess(fact, _comparisons(symbol))

        assert verdict.establishes, (symbol, verdict.because)
        assert verdict.standing is EvidenceStanding.ESTABLISHED
        assert len(verdict.gates) == 6
        assert verdict.failed == ()


def test_cardanos_maximum_is_derived_from_the_chain() -> None:
    """The cap stops being a vendor claim.

    `supply + reserves` is 45,000,000,000 ADA exactly: the reserves pot
    *is* the unissued remainder, so the chain states its own maximum by
    accounting for every lovelace on either side of it.
    """

    fact = _of("ADA", SupplyConcept.MAX_SUPPLY)

    assert fact.value == 45_000_000_000.0
    assert fact.authority is EvidenceAuthority.PRIMARY_DERIVED
    assert fact.source == "Cardano ledger totals"

    assert assess(fact, _comparisons("ADA")).establishes


def test_a_vendor_figure_is_never_offered_the_primary_route() -> None:
    """Model C is about canonical state, not a shortcut for one source."""

    picture = _picture("ADA")

    for fact in picture.facts:
        if fact.authority.is_primary:
            continue

        verdict = assess(fact, picture.comparisons)

        assert verdict.gates == ()
        assert not verdict.establishes
        assert "does not apply" in verdict.because


def test_a_reading_with_no_provenance_fails_rather_than_passes() -> None:
    """An unevaluable gate is a failed gate.

    Not knowing whether a computation leaned on a remembered constant is
    exactly the state the blob fee was in, and treating an unknown as a
    pass would rebuild the hole the gate was cut to close.
    """

    bare = SupplyFact(
        concept=SupplyConcept.EMITTED_SUPPLY,
        methodology=PROTOCOL_EMITTED,
        value=1.0,
        unit="X",
        authority=EvidenceAuthority.PRIMARY_OBSERVATION,
        standing=EvidenceStanding.CLAIMED,
        source="a chain",
        observed_at=READ,
    )

    verdict = assess(bare)

    assert not verdict.establishes
    assert len(verdict.failed) >= 4


# ── the finding that kept the question unscored ─────────────────────


def test_the_emitted_share_and_the_overhang_can_move_apart() -> None:
    """Section 8, measured. This is why Option A was refused.

    Arbitrum is 100% emitted and between a third and seven-eighths of
    its maximum sits in balances nobody names as circulating. Cardano is
    86.2% emitted with 18.8% outstanding, every lovelace of it named by
    the ledger. A band on the emitted share would rank Arbitrum above
    Cardano on the strength of the ratio being higher.
    """

    shares: dict[str, float] = {}
    overhangs: dict[str, float] = {}

    for symbol in ("ADA", "ARB"):
        picture = _picture(symbol)

        cap = picture.of(SupplyConcept.MAX_SUPPLY)[0].value

        emitted = sorted(
            picture.of(SupplyConcept.EMITTED_SUPPLY),
            key=lambda fact: (not fact.authority.is_primary,),
        )[0]

        circulating = [
            fact
            for fact in picture.of(SupplyConcept.CIRCULATING_ESTIMATE)
            if fact.value <= cap
        ]

        shares[symbol] = emitted.value / cap

        # The *smallest* overhang any source supports, so the finding
        # cannot be accused of picking a flattering estimate.
        overhangs[symbol] = min((cap - fact.value) / cap for fact in circulating)

    assert shares["ARB"] > shares["ADA"]
    assert overhangs["ARB"] > overhangs["ADA"]


def test_the_supply_question_is_still_not_scored() -> None:
    """Option B. The evidence arrived and the question stayed unscored.

    Two assets' emitted supply now establishes, which S5 named as the
    blocker. It was not the only one: the ratio measures the wrong
    thing, and no schedule is held for any of the eight.
    """

    from app.domain.crypto_quality import RULES, QualityReadiness, readiness_for
    from app.domain.crypto_questions import CryptoQuestionKey

    ruling = readiness_for(CryptoQuestionKey.SUPPLY_AND_DILUTION)

    assert ruling.readiness is QualityReadiness.VISIBLE_NOT_SCORED
    assert CryptoQuestionKey.SUPPLY_AND_DILUTION not in RULES

    # And what would change it is the schedule, not more corroboration.
    assert ruling.would_change is not None
    assert "schedule" in ruling.would_change


def test_the_quality_quorum_is_unchanged() -> None:
    """The ruling's hard boundary. One question scores; a band needs two."""

    from app.domain.crypto_quality import MINIMUM_SCORED, READINESS, RULES

    assert MINIMUM_SCORED == 2

    scorable = [key for key, ruling in READINESS.items() if ruling.readiness.scores]

    assert len(scorable) == 1
    assert len(RULES) == 1


# ── the store ───────────────────────────────────────────────────────


def test_provenance_survives_the_store() -> None:
    """The gate runs on read, so the store must carry what it reads.

    A reconciliation summarised to a boolean on write would be a stored
    verdict, and this platform derives verdicts on read.
    """

    fact = _of("ADA", SupplyConcept.EMITTED_SUPPLY)

    restored = _decode(_encode(fact))

    assert restored is not None
    assert restored.provenance is not None

    original = fact.provenance
    round_tripped = restored.provenance

    assert original is not None
    assert round_tripped.reconciliation is not None
    assert original.reconciliation is not None
    assert round_tripped.reconciliation.residual == 0
    assert round_tripped.reconciliation.components == original.reconciliation.components
    assert round_tripped.constants == original.constants

    assert assess(restored, _comparisons("ADA")).establishes


def test_a_record_written_under_an_older_shape_is_treated_as_absent(
    tmp_path: pathlib.Path,
) -> None:
    """Found the hard way, and the guard now lives in the shared cache.

    Records written before `provenance` existed decoded into facts with
    none, every gate that needs it failed, and the store went on serving
    them until the daily expiry. S5.2a moved the check into `JsonCache`,
    so this asserts the *store's* behaviour end to end rather than a
    private method: a version-1 record is a miss, and the store declares
    no migration because a record without provenance has nothing to
    bring forward.
    """

    from app.infrastructure.cache.json_cache import JsonCache
    from app.providers.primary_supply_provider import CachedPrimarySupplyProvider

    assert SCHEMA == 2

    facts = [_encode(_of("ADA", SupplyConcept.EMITTED_SUPPLY))]

    # A store at the old schema writes what the old code wrote.
    JsonCache(tmp_path, schema=1).write("ADA", {"facts": facts})

    stale = CachedPrimarySupplyProvider.stored(cache=JsonCache(tmp_path, schema=SCHEMA))

    assert stale.facts("ADA") == ()

    # And the same record under the current schema is served in full.
    JsonCache(tmp_path, schema=SCHEMA).write("ADA", {"facts": facts})

    current = CachedPrimarySupplyProvider.stored(
        cache=JsonCache(tmp_path, schema=SCHEMA)
    )

    served = current.facts("ADA")

    assert served
    assert served[0].provenance is not None


# ── the boundaries the ruling set ───────────────────────────────────


def test_the_gate_scores_nothing_and_interprets_nothing() -> None:
    """An established emitted supply is a quantity, not a judgment."""

    code = inspect.getsource(
        __import__("app.domain.supply_establishment", fromlist=["x"])
    )

    for forbidden in ("dilut", "band", "points", "score", "quality"):
        assert forbidden not in code.casefold(), forbidden


#: Every vendor's supply claim on 2026-08-10, per security. Recorded
#: rather than read: a test that consulted `data/cache` passes on the
#: machine that ran `movrvest acquire` and fails on a clean checkout —
#: which is exactly how the first version of this file failed its
#: `git archive HEAD` isolation run.
_CLAIMS: dict[str, dict[str, dict[str, float]]] = {
    "ADA": {
        "TokenInsight": {
            "circulating_supply": 38_803_572_882.0,
            "max_supply": 45_000_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 37_353_519_634.0,
            "total_supply": 45_000_000_000.0,
            "max_supply": 45_000_000_000.0,
        },
        "Yahoo Finance": {"circulating_supply": 36_550_320_128.0},
    },
    "HYPE": {
        "TokenInsight": {
            "circulating_supply": 336_685_219.0,
            "max_supply": 1_000_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 222_445_714.0,
            "total_supply": 955_307_079.4341414,
            "max_supply": 1_000_000_000.0,
        },
    },
    # The inversion case: a fully emitted token whose two vendors put
    # its circulating supply 419% apart.
    "ARB": {
        "TokenInsight": {
            "circulating_supply": 1_275_000_000.0,
            "max_supply": 10_000_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 6_614_056_381.0,
            "total_supply": 10_000_000_000.0,
            "max_supply": 10_000_000_000.0,
        },
    },
}


class _Vendor:
    def __init__(self, name: str) -> None:
        self._name = name

    def claim_set(self, symbol: str) -> TokenClaimSet | None:
        values = _CLAIMS.get(symbol.upper(), {}).get(self._name)

        if values is None:
            return None

        return TokenClaimSet(
            source=self._name,
            read=Provenance(source=self._name, observed_at=READ),
            symbol_echo=symbol.upper(),
            **values,  # type: ignore[arg-type]
        )


class _Chain:
    """The recorded chain readings, produced by the real provider."""

    @staticmethod
    def facts(symbol: str) -> tuple[SupplyFact, ...]:
        return _facts(symbol)


def _picture(symbol: str):  # type: ignore[no-untyped-def]
    service = SupplySemanticsService(
        sources=(
            _Vendor("TokenInsight"),  # type: ignore[arg-type]
            _Vendor("CoinGecko"),  # type: ignore[arg-type]
            _Vendor("Yahoo Finance"),  # type: ignore[arg-type]
        ),
        primary=_Chain(),  # type: ignore[arg-type]
    )

    picture = service.established(symbol, AssetClass.CRYPTO)

    assert picture is not None

    return picture


def _comparisons(symbol: str):  # type: ignore[no-untyped-def]
    """The vendor comparisons the perimeter gate reads."""

    return _picture(symbol).comparisons
