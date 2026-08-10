"""The economics behind a token: a second evidence family, kept honest.

The S2 acceptance cases. HYPE is the deep case — two entities under one
name whose figures differ by two orders of magnitude, and a
value-accrual mechanism that exists only because the provider states
it. Bitcoin is the applicability case: it must never read as incomplete
for lacking an exchange's metrics.
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_entities import entities_for
from app.domain.protocol_fundamentals import (
    MetricAvailability,
    MetricFamily,
    Periodicity,
    ProtocolEntityKind,
    ProtocolMetric,
    annualise,
)
from app.domain.provenance import Provenance
from app.providers.defillama_provider import (
    ProtocolClaimSet,
    ProtocolMetricClaim,
)
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService

READ = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)

#: The Hyperliquid figures the S2 measurement actually read.
HYPE_PROTOCOL = ProtocolClaimSet(
    entity_key="hyperliquid-protocol",
    source="DefiLlama",
    read=Provenance(source="DefiLlama", observed_at=READ),
    claims=(
        ProtocolMetricClaim(ProtocolMetric.TVL, 6_256_626_645.0, None),
        ProtocolMetricClaim(
            ProtocolMetric.FEES,
            842_720.0,
            "24 hours",
            methodology=(
                "Hyperliquid Perps: Include perps trading fees on crypto "
                "and HIP-3 deployed markets + builders fees."
            ),
            change_24h=0.3503,
        ),
        ProtocolMetricClaim(
            ProtocolMetric.PROTOCOL_REVENUE,
            534_851.0,
            "24 hours",
            methodology="Hyperliquid Perps: Protocol doesn't keep any fees.",
        ),
        ProtocolMetricClaim(
            ProtocolMetric.HOLDER_REVENUE,
            534_851.0,
            "24 hours",
            methodology=(
                "Hyperliquid Perps: 99% of fees go to Assistance Fund for "
                "buying HYPE tokens, excluding builders fees."
            ),
        ),
        ProtocolMetricClaim(ProtocolMetric.DEX_VOLUME, 38_730_237.0, "24 hours"),
        ProtocolMetricClaim(ProtocolMetric.OPEN_INTEREST, 10_865_754_650.0, None),
    ),
    defines=frozenset(ProtocolMetric),
)

HYPE_CHAIN = ProtocolClaimSet(
    entity_key="hyperliquid-l1-chain",
    source="DefiLlama",
    read=Provenance(source="DefiLlama", observed_at=READ),
    claims=(
        ProtocolMetricClaim(ProtocolMetric.TVL, 1_203_578_598.0, None),
        ProtocolMetricClaim(
            ProtocolMetric.FEES,
            3_769.0,
            "24 hours",
            methodology="Gas fees paid by users",
        ),
    ),
    defines=frozenset(
        {ProtocolMetric.TVL, ProtocolMetric.FEES, ProtocolMetric.PROTOCOL_REVENUE}
    ),
)

BITCOIN = ProtocolClaimSet(
    entity_key="bitcoin-chain",
    source="DefiLlama",
    read=Provenance(source="DefiLlama", observed_at=READ),
    claims=(
        ProtocolMetricClaim(ProtocolMetric.TVL, 3_561_082_562.0, None),
        ProtocolMetricClaim(
            ProtocolMetric.FEES,
            139_032.0,
            "24 hours",
            methodology="Gas fees paid by users",
        ),
    ),
    # The provider defines fees and revenue for Bitcoin and says nothing
    # about holder revenue — because the chain has no such mechanism.
    defines=frozenset(
        {ProtocolMetric.TVL, ProtocolMetric.FEES, ProtocolMetric.PROTOCOL_REVENUE}
    ),
)


class StubSource:
    """One protocol claimant, offline."""

    def __init__(self, *sets: ProtocolClaimSet) -> None:
        self._sets = {claims.entity_key: claims for claims in sets}

    def claim_set(self, entity_key: str) -> ProtocolClaimSet | None:
        return self._sets.get(entity_key)


def service(*sets: ProtocolClaimSet) -> ProtocolFundamentalsService:
    return ProtocolFundamentalsService(sources=(StubSource(*sets),))


# ── acceptance 3 and 4: identity is explicit, HYPE is deep-read ─────


def test_hype_maps_to_two_entities_that_are_not_interchangeable() -> None:
    """The same name covers a venue and a chain. Both are real, apart."""

    entities = entities_for("HYPE")

    assert [entity.kind for entity in entities] == [
        ProtocolEntityKind.PROTOCOL,
        ProtocolEntityKind.CHAIN,
    ]

    outcome = service(HYPE_PROTOCOL, HYPE_CHAIN).established("HYPE", AssetClass.CRYPTO)

    assert outcome is not None

    venue_fees = outcome.fact(ProtocolMetric.FEES, "hyperliquid-protocol")
    chain_fees = outcome.fact(ProtocolMetric.FEES, "hyperliquid-l1-chain")

    assert venue_fees is not None and chain_fees is not None
    assert venue_fees.value == 842_720.0
    assert chain_fees.value == 3_769.0

    # Two orders of magnitude apart, and each says which entity it is.
    assert venue_fees.entity.name == "Hyperliquid"
    assert chain_fees.entity.name == "Hyperliquid L1"

    # Every mapping states its basis, and none of them is the name.
    for entity in entities:
        assert entity.mapping_basis
        assert entity.measures


def test_a_security_with_no_mapped_entity_measures_nothing() -> None:
    """An unmapped token is not a token whose economics came back empty."""

    outcome = service().established("DOGE", AssetClass.CRYPTO)

    assert outcome is not None
    assert outcome.entities == ()
    assert outcome.facts == ()
    assert outcome.unmapped_because is not None
    assert "shared name does not establish one" in outcome.unmapped_because


# ── acceptance 5 and 7: three concepts, and accrual kept separate ───


def test_fees_revenue_and_holder_revenue_stay_three_concepts() -> None:
    outcome = service(HYPE_PROTOCOL, HYPE_CHAIN).established("HYPE", AssetClass.CRYPTO)

    assert outcome is not None

    fees = outcome.fact(ProtocolMetric.FEES, "hyperliquid-protocol")
    protocol = outcome.fact(ProtocolMetric.PROTOCOL_REVENUE, "hyperliquid-protocol")
    holders = outcome.fact(ProtocolMetric.HOLDER_REVENUE, "hyperliquid-protocol")

    assert fees is not None and protocol is not None and holders is not None

    # Three metrics, three values, three definitions — never one
    # "revenue" concept.
    assert fees.value != protocol.value
    assert {fees.metric, protocol.metric, holders.metric} == {
        ProtocolMetric.FEES,
        ProtocolMetric.PROTOCOL_REVENUE,
        ProtocolMetric.HOLDER_REVENUE,
    }

    # Value generation and holder accrual are different families: a
    # protocol can earn everything and pass holders nothing.
    assert fees.semantics.family is MetricFamily.VALUE_GENERATION
    assert protocol.semantics.family is MetricFamily.VALUE_GENERATION
    assert holders.semantics.family is MetricFamily.HOLDER_ACCRUAL

    # The mechanism is the provider's sentence, carried verbatim —
    # this platform never infers value capture from revenue existing.
    assert holders.provider_methodology is not None
    assert "Assistance Fund" in holders.provider_methodology
    assert protocol.provider_methodology is not None
    assert "doesn't keep any fees" in protocol.provider_methodology


def test_a_share_larger_than_the_whole_is_rejected() -> None:
    """Holder revenue above fees cannot be true, whatever the source says."""

    broken = ProtocolClaimSet(
        entity_key="bitcoin-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 1_000.0, "24 hours"),
            ProtocolMetricClaim(ProtocolMetric.PROTOCOL_REVENUE, 5_000.0, "24 hours"),
        ),
        defines=frozenset({ProtocolMetric.FEES, ProtocolMetric.PROTOCOL_REVENUE}),
    )

    outcome = service(broken).established("BTC", AssetClass.CRYPTO)

    assert outcome is not None

    revenue = outcome.fact(ProtocolMetric.PROTOCOL_REVENUE)

    assert revenue is not None
    assert revenue.standing is EvidenceStanding.REJECTED
    assert revenue.availability is MetricAvailability.SEMANTICS_UNRESOLVED
    assert revenue.value is None


# ── acceptance 6: derived arithmetic is labelled as ours ────────────


def test_annualisation_is_movrvest_arithmetic_and_says_so() -> None:
    outcome = service(HYPE_PROTOCOL, HYPE_CHAIN).established("HYPE", AssetClass.CRYPTO)

    assert outcome is not None

    # Nothing is annualised today: a run rate over a claim would dress
    # an uncorroborated figure in arithmetic's authority.
    assert outcome.derived == ()

    holders = outcome.fact(ProtocolMetric.HOLDER_REVENUE, "hyperliquid-protocol")

    assert holders is not None
    assert annualise(holders) is None

    # Over an established observation it computes, and the wording
    # separates the derivation from the observation beneath it.
    established = ProtocolFact_established(holders)

    figure = annualise(established)

    assert figure is not None
    assert figure.value == 534_851.0 * 365
    assert "MOVRvest's arithmetic" in figure.stated
    assert "not a year that happened" in figure.caveat


def ProtocolFact_established(fact):  # noqa: N802 - a fixture, not an API
    """The same fact as if a second source had corroborated it."""

    from dataclasses import replace

    return replace(fact, standing=EvidenceStanding.ESTABLISHED)


def test_a_level_is_never_annualised() -> None:
    outcome = service(HYPE_PROTOCOL).established("HYPE", AssetClass.CRYPTO)

    assert outcome is not None

    tvl = outcome.fact(ProtocolMetric.TVL, "hyperliquid-protocol")

    assert tvl is not None
    assert tvl.semantics.periodicity is Periodicity.INSTANT
    assert annualise(ProtocolFact_established(tvl)) is None

    # Open interest is a level too, however the provider fields it.
    interest = outcome.fact(ProtocolMetric.OPEN_INTEREST, "hyperliquid-protocol")

    assert interest is not None
    assert interest.window is None
    assert interest.semantics.periodicity is Periodicity.INSTANT


# ── acceptance 8 and 9: five absences, and Bitcoin is not incomplete ─


def test_bitcoin_is_not_penalised_for_an_exchanges_metrics() -> None:
    outcome = service(BITCOIN).established("BTC", AssetClass.CRYPTO)

    assert outcome is not None

    for metric in (ProtocolMetric.DEX_VOLUME, ProtocolMetric.OPEN_INTEREST):
        fact = outcome.fact(metric)

        assert fact is not None, metric
        assert fact.availability is MetricAvailability.NOT_APPLICABLE, metric
        assert fact.because is not None
        assert "does not have" in fact.because

    # And holder revenue: the source defines other measures for Bitcoin
    # and none for this one — the chain has no such mechanism.
    holders = outcome.fact(ProtocolMetric.HOLDER_REVENUE)

    assert holders is not None
    assert holders.availability is MetricAvailability.NOT_APPLICABLE
    assert holders.because is not None
    assert "not a mechanism this entity has" in holders.because


def test_the_five_absences_are_never_one_missing() -> None:
    """Not applicable, unavailable and unread are different sentences."""

    unread = service().established("BTC", AssetClass.CRYPTO)
    read = service(BITCOIN).established("BTC", AssetClass.CRYPTO)

    assert unread is not None and read is not None

    unread_fees = unread.fact(ProtocolMetric.FEES)
    read_revenue = read.fact(ProtocolMetric.PROTOCOL_REVENUE)

    assert unread_fees is not None and read_revenue is not None

    assert unread_fees.availability is MetricAvailability.UNAVAILABLE_FREE
    assert unread_fees.because is not None
    assert "Nothing has been read" in unread_fees.because

    assert read_revenue.availability is MetricAvailability.UNAVAILABLE_FREE
    assert read_revenue.because is not None
    assert "reported no figure" in read_revenue.because


def test_silence_from_a_source_that_documents_nothing_teaches_nothing() -> None:
    """A TVL-only entity is not an entity with no fee mechanism.

    Bittensor's shape: the source publishes capital and nothing else.
    Reading that as "it has no fees" would invent a finding out of a
    gap — the applicability evidence must come from the same family.
    """

    tvl_only = ProtocolClaimSet(
        entity_key="bittensor-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(ProtocolMetricClaim(ProtocolMetric.TVL, 44_955_669.0, None),),
        defines=frozenset({ProtocolMetric.TVL}),
    )

    outcome = service(tvl_only).established("TAO", AssetClass.CRYPTO)

    assert outcome is not None

    fees = outcome.fact(ProtocolMetric.FEES)

    assert fees is not None
    assert fees.availability is MetricAvailability.UNAVAILABLE_FREE


# ── acceptance 10, 11, 12: nothing consumes this, nothing moved ─────


def test_no_scorer_or_decision_path_can_import_protocol_fundamentals() -> None:
    """Acceptance 10, made structural.

    The same guard the third-party rating carries. A slice that wants
    protocol economics in a score has to argue with this test first —
    which is the point: S5 decides what these facts mean, not S2.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    reasoning = (
        "app/analysts",
        "app/application/brain",
        "app/application/committees",
        "app/application/executive",
        "app/cio",
        "app/committee",
        "app/domain/business_quality.py",
        "app/domain/playbook.py",
        "app/services/business_quality_service.py",
        "app/services/company_facts_service.py",
        "app/services/company_signal_service.py",
        "app/services/quality_signal_service.py",
    )

    offenders: list[str] = []

    for target in reasoning:
        path = root / target

        files = (
            sorted(path.rglob("*.py"))
            if path.is_dir()
            else ([path] if path.exists() else [])
        )

        for source in files:
            text = source.read_text(encoding="utf-8")

            if "protocol_fundamentals" in text or "defillama" in text.lower():
                offenders.append(str(source.relative_to(root)))

    assert offenders == []


def test_protocol_economics_are_shown_by_the_quality_model_and_scored_by_none() -> None:
    """S2 said S5 would decide what these facts mean. It decided: nothing.

    The quality model reads protocol economics — fees, capital
    committed, what a venue turns over, what reaches holders — and every
    one of them is a single provider's claim, so not one contributes a
    point. The guard above therefore narrows rather than lifts, and this
    is the property that replaces it: no question whose evidence is a
    protocol metric is scorable.
    """

    from app.domain.crypto_quality import readiness_for
    from app.domain.crypto_questions import QUESTIONS

    scored_from_protocol = [
        key
        for key, question in QUESTIONS.items()
        if readiness_for(key).readiness.scores
        and any(demand.protocol_metric is not None for demand in question.demands)
    ]

    assert scored_from_protocol == []


def test_the_canonical_layer_holds_no_provider_types() -> None:
    """Acceptance 2: DefiLlama objects terminate at the adapter."""

    root = pathlib.Path(__file__).resolve().parent.parent

    for target in (
        "app/domain/protocol_fundamentals.py",
        "app/domain/protocol_entities.py",
    ):
        text = (root / target).read_text(encoding="utf-8")

        assert "app.providers" not in text, target
        assert "requests" not in text, target


def test_a_second_protocol_provider_joins_without_canonical_change() -> None:
    """Acceptance 13: the pool is open here too.

    A source nobody wrote a line for contributes claims through the
    same object, and the service consumes it unchanged. When a second
    source eventually corroborates a figure, this is the seam where
    establishment will happen — under the token layer's rule, not a
    new one.
    """

    newcomer = ProtocolClaimSet(
        entity_key="bitcoin-chain",
        source="Acme Chain Data",
        read=Provenance(source="Acme Chain Data", observed_at=READ),
        claims=(ProtocolMetricClaim(ProtocolMetric.TVL, 3_560_000_000.0, None),),
        defines=frozenset({ProtocolMetric.TVL}),
    )

    outcome = ProtocolFundamentalsService(
        sources=(StubSource(newcomer),),
    ).established("BTC", AssetClass.CRYPTO)

    assert outcome is not None

    tvl = outcome.fact(ProtocolMetric.TVL)

    assert tvl is not None
    assert tvl.source == "Acme Chain Data"
    assert tvl.standing is EvidenceStanding.CLAIMED


def test_one_source_never_establishes_anything() -> None:
    """The S1 rule, applied uniformly to the second family."""

    outcome = service(HYPE_PROTOCOL, HYPE_CHAIN).established("HYPE", AssetClass.CRYPTO)

    assert outcome is not None

    for fact in outcome.facts:
        assert fact.standing is not EvidenceStanding.ESTABLISHED, fact.metric
        assert fact.established_value is None, fact.metric


def test_the_family_is_refused_for_anything_that_is_not_crypto() -> None:
    """Acceptance 15: equity behaviour is untouched."""

    for asset_class in (
        AssetClass.STOCK,
        AssetClass.ETF,
        AssetClass.COMMODITY,
        AssetClass.UNKNOWN,
        None,
    ):
        assert service(BITCOIN).established("AAPL", asset_class) is None
