"""S3: which investment questions legitimately apply to a token.

One test per acceptance criterion in the ruling, plus the structural
guards. The ones that matter most are the two that cannot be checked by
reading the code: that applicability never consults a figure, and that
nothing in the reasoning path can import any of this.

**Nothing here reads the live store.** Every evidence case runs on the
recorded claim sets below — the exact payloads the S2 corpus read on
2026-08-10, methodology sentences verbatim — pushed through the real
services. A test that consulted `data/cache` would pass on this machine,
fail in CI, and quietly change its own subject the next time
`movrvest acquire` ran.
"""

from __future__ import annotations

import inspect
import pathlib
from datetime import UTC, datetime

import pytest

from app.domain.asset_class import AssetClass
from app.domain.crypto_archetype import (
    ARCHETYPES,
    ASSIGNMENTS,
    AnalyticalCapability,
    ArchetypeConfidence,
    TokenArchetype,
    archetype_for,
)
from app.domain.crypto_playbook import QuestionCell
from app.domain.crypto_questions import (
    ASKED_BY,
    DECLINED,
    QUESTIONS,
    CryptoQuestionKey,
    QuestionApplicability,
    applicability_for,
    questions_for,
)
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_entities import entities_for
from app.domain.protocol_fundamentals import (
    MetricAvailability,
    ProtocolEntity,
    ProtocolEntityKind,
    ProtocolFact,
    ProtocolFundamentals,
    ProtocolMetric,
)
from app.domain.provenance import Provenance
from app.domain.token_fact_validation import TokenClaimSet, judge
from app.domain.token_facts import TOKEN_FACTS, TokenFact, TokenMarketFacts
from app.domain.token_value_flow import (
    ValueFlowKind,
    ValueStage,
    recognise,
    value_chains,
)
from app.providers.defillama_provider import ProtocolClaimSet, ProtocolMetricClaim
from app.services.crypto_playbook_service import CryptoPlaybookService
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService

CORPUS = ("BTC", "ETH", "SOL", "ADA", "ARB", "1INCH", "HYPE", "TAO")

READ = datetime(2026, 8, 10, tzinfo=UTC)


class _NoFacts:
    """A token-facts service that holds nothing at all."""

    @staticmethod
    def established(
        symbol: str,
        name: str,
        asset_class: AssetClass | None,
    ) -> TokenMarketFacts | None:
        if asset_class is not AssetClass.CRYPTO:
            return None

        return TokenMarketFacts(
            symbol=symbol,
            provider_id=None,
            facts=tuple(
                TokenFact(fact=fact, standing=EvidenceStanding.ABSENT)
                for fact in TOKEN_FACTS
            ),
            rejected=(),
        )


class _NoProtocol:
    """A protocol service that holds nothing at all."""

    @staticmethod
    def established(
        symbol: str,
        asset_class: AssetClass | None,
    ) -> ProtocolFundamentals | None:
        if asset_class is not AssetClass.CRYPTO:
            return None

        return ProtocolFundamentals(
            symbol=symbol,
            entities=entities_for(symbol),
            facts=(),
        )


def _empty_service() -> CryptoPlaybookService:
    return CryptoPlaybookService(
        facts=_NoFacts(),  # type: ignore[arg-type]
        protocol=_NoProtocol(),  # type: ignore[arg-type]
    )


# ── the recorded corpus, replayed through the real services ─────────

#: DefiLlama's answers on 2026-08-10, verbatim. The methodology strings
#: are the evidence this slice reasons from, so they are reproduced
#: exactly rather than paraphrased — a test on a paraphrase would prove
#: nothing about a reader that runs on the source's own wording.
#:
#: `defines` mirrors the adapter's own reading of which fee-family
#: metrics the provider documents for the entity, which is what carries
#: Bitcoin's "no holder mechanism" and Cardano's alike.
_RECORDED: dict[str, ProtocolClaimSet] = {
    "bitcoin-chain": ProtocolClaimSet(
        entity_key="bitcoin-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(
                ProtocolMetric.FEES,
                139_032.0,
                "24 hours",
                methodology="Gas fees paid by users",
            ),
            ProtocolMetricClaim(
                ProtocolMetric.TVL,
                3_561_082_562.0,
                None,
                methodology=(
                    "Value of assets held in protocols deployed on this "
                    "chain, as the provider computes it."
                ),
            ),
        ),
        defines=frozenset(
            {
                ProtocolMetric.FEES,
                ProtocolMetric.PROTOCOL_REVENUE,
                ProtocolMetric.TVL,
            }
        ),
    ),
    "ethereum-chain": ProtocolClaimSet(
        entity_key="ethereum-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(
                ProtocolMetric.FEES,
                175_154.0,
                "24 hours",
                methodology=(
                    "Total ETH gas fees (base fees + priority fees) plus "
                    "blob fees (post-EIP-4844, type-3 blob-carrying "
                    "transactions) paid by users"
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.PROTOCOL_REVENUE,
                32_159.0,
                "24 hours",
                methodology=(
                    "Amount of ETH burned — base fees plus blob fees "
                    "(both are permanently burned, accruing to no proposer)"
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                32_159.0,
                "24 hours",
                methodology="Amount of ETH burned — base fees plus blob fees",
            ),
            ProtocolMetricClaim(
                ProtocolMetric.TVL,
                41_993_354_638.0,
                None,
                methodology=(
                    "Value of assets held in protocols deployed on this "
                    "chain, as the provider computes it."
                ),
            ),
        ),
        defines=frozenset(
            {
                ProtocolMetric.FEES,
                ProtocolMetric.PROTOCOL_REVENUE,
                ProtocolMetric.HOLDER_REVENUE,
                ProtocolMetric.TVL,
            }
        ),
    ),
    "hyperliquid-protocol": ProtocolClaimSet(
        entity_key="hyperliquid-protocol",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(
                ProtocolMetric.FEES,
                842_720.0,
                "24 hours",
                methodology=(
                    "Hyperliquid Perps: Include perps trading fees on "
                    "crypto and HIP-3 deployed markets + builders fees, "
                    "excluding all spot fees."
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.PROTOCOL_REVENUE,
                534_851.0,
                "24 hours",
                methodology=(
                    "Hyperliquid Perps: 99% of fees go to Assistance Fund "
                    "for buying HYPE tokens, excluding builders fees. "
                    "Hyperliquid HLP: No revenue."
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                534_851.0,
                "24 hours",
                methodology=(
                    "Hyperliquid Perps: 99% of fees go to Assistance Fund "
                    "for buying HYPE tokens, excluding builders fees. "
                    "Hyperliquid HLP: Fees going to governance token holders"
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.TVL,
                6_256_626_645.0,
                None,
                methodology=(
                    "Value of assets held across the protocol's own "
                    "contracts, as the provider computes it."
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.DEX_VOLUME,
                38_730_237.0,
                "24 hours",
                methodology=(
                    "Include spot trading fees and unit protocol fees, "
                    "excluding perps fees."
                ),
            ),
            ProtocolMetricClaim(
                ProtocolMetric.OPEN_INTEREST,
                10_865_754_650.0,
                None,
                methodology="Fees paid by users",
            ),
        ),
        defines=frozenset(ProtocolMetric),
    ),
    "hyperliquid-l1-chain": ProtocolClaimSet(
        entity_key="hyperliquid-l1-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(
                ProtocolMetric.FEES,
                3_769.0,
                "24 hours",
                methodology="Gas fees paid by users",
            ),
            ProtocolMetricClaim(
                ProtocolMetric.PROTOCOL_REVENUE,
                3_769.0,
                "24 hours",
                methodology="Burned coins",
            ),
            # A figure with no definition beside it: the amount is known
            # and what it means is not.
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                3_769.0,
                "24 hours",
            ),
            ProtocolMetricClaim(
                ProtocolMetric.TVL,
                1_203_595_452.0,
                None,
                methodology=(
                    "Value of assets held in protocols deployed on this "
                    "chain, as the provider computes it."
                ),
            ),
        ),
        defines=frozenset(
            {
                ProtocolMetric.FEES,
                ProtocolMetric.PROTOCOL_REVENUE,
                ProtocolMetric.TVL,
            }
        ),
    ),
    # Figures published with no methodology at all — the shape that
    # leaves the mechanism demand unmet while the amounts are read.
    "1inch-protocol": ProtocolClaimSet(
        entity_key="1inch-protocol",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 1_845.0, "24 hours"),
            ProtocolMetricClaim(ProtocolMetric.PROTOCOL_REVENUE, 329.0, "24 hours"),
        ),
        defines=frozenset(),
    ),
}


class _RecordedProtocolClaims:
    """The S2 corpus as a pool claimant, reading no store."""

    @staticmethod
    def claim_set(entity_key: str) -> ProtocolClaimSet | None:
        return _RECORDED.get(entity_key)


#: HYPE's supply as the two vendors reported it: internally coherent,
#: 51% apart on what counts as circulating, agreeing on price and cap.
_HYPE_PRICE = 54.62942692718245


def _hype_claims(circulating: float, source: str) -> TokenClaimSet:
    return TokenClaimSet(
        source=source,
        read=Provenance(source=source, observed_at=READ),
        symbol_echo="HYPE",
        provider_id="hyperliquid",
        price=_HYPE_PRICE,
        market_cap=_HYPE_PRICE * circulating,
        circulating_supply=circulating,
        max_supply=1_000_000_000.0,
    )


class _RecordedTokenFacts:
    """The S1 conflict, judged by the real rule and reading no store."""

    @staticmethod
    def established(
        symbol: str,
        name: str,
        asset_class: AssetClass | None,
    ) -> TokenMarketFacts | None:
        if asset_class is not AssetClass.CRYPTO or symbol != "HYPE":
            return None

        return judge(
            "HYPE",
            [
                _hype_claims(336_685_219.0, "TokenInsight"),
                _hype_claims(222_445_714.0, "CoinGecko"),
            ],
        )


def _recorded_service() -> CryptoPlaybookService:
    return CryptoPlaybookService(
        facts=_RecordedTokenFacts(),  # type: ignore[arg-type]
        protocol=ProtocolFundamentalsService(
            sources=(_RecordedProtocolClaims(),),
        ),
    )


# ── acceptance 1: nothing is classified from a vendor label ─────────


def test_no_asset_is_classified_from_a_vendor_category_label() -> None:
    """Acceptance 1, made structural rather than promised.

    The archetype layer may not consult a rater, a category or any
    provider name — a label is another party's opinion of an asset, and
    what this platform classifies from is the structural evidence it can
    re-check.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/crypto_archetype.py",
        "app/domain/crypto_questions.py",
    ):
        text = (root / module).read_text(encoding="utf-8")

        # Checked on what the module can *reach*, not on what it
        # mentions: naming TokenInsight's grade as a basis this layer
        # refuses is exactly what `not_classified_from` is for, and a
        # word-level ban would forbid saying so.
        imports = [
            line for line in text.splitlines() if line.startswith(("import ", "from "))
        ]

        for line in imports:
            assert "app.providers" not in line, (module, line)
            assert "token_rating" not in line, (module, line)
            assert "company_profile" not in line, (module, line)
            assert "app.services" not in line, (module, line)


def test_tao_refuses_the_ai_label_and_says_so() -> None:
    """The corpus case the ruling names.

    TAO is the asset a vendor category would classify instantly, and the
    honest answer is that this platform has read nothing that
    distinguishes its design. `UNKNOWN` is that answer, with the refused
    basis stated where a reader can see it.
    """

    assignment = archetype_for("TAO")

    assert assignment.archetype is TokenArchetype.UNKNOWN
    assert assignment.confidence is ArchetypeConfidence.UNESTABLISHED
    assert any("AI" in line for line in assignment.not_classified_from)


def test_every_corpus_assignment_names_the_evidence_it_rests_on() -> None:
    for symbol in CORPUS:
        assignment = ASSIGNMENTS[symbol]

        assert assignment.rests_on, symbol
        assert assignment.because, symbol
        assert assignment.not_classified_from, symbol


# ── acceptance 2: BTC does not inherit a protocol's questions ───────


def test_bitcoin_is_not_asked_a_protocols_revenue_questions() -> None:
    """Acceptance 2, and the whole point of the slice.

    The bank's leverage question one asset class over: the answer would
    be *none*, the number would be real, and the question would be the
    wrong instrument.
    """

    asked = questions_for(TokenArchetype.MONETARY_NETWORK)

    for question in (
        CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
        CryptoQuestionKey.PROTOCOL_CAPTURE,
        CryptoQuestionKey.ECONOMIC_ACTIVITY,
    ):
        assert question not in asked

        applicability = applicability_for(TokenArchetype.MONETARY_NETWORK, question)

        assert applicability.state is QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE


def test_bitcoins_declines_are_worded_rather_than_omitted() -> None:
    """A declined question and an omitted one look identical otherwise."""

    playbook = _empty_service().established("BTC", AssetClass.CRYPTO)

    assert playbook is not None

    declined = playbook.declined

    assert declined

    for item in declined:
        assert len(item.applicability.because) > 40, item.question.key


# ── acceptance 3 and 4: HYPE ────────────────────────────────────────


def test_hype_asks_the_token_value_accrual_question() -> None:
    """Acceptance 3."""

    applicability = applicability_for(
        TokenArchetype.EXCHANGE_NETWORK,
        CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
    )

    assert applicability.state is QuestionApplicability.ASK
    assert applicability.asked_by is AnalyticalCapability.TOKEN_VALUE_CAPTURE


def test_hypes_venue_and_chain_stay_distinct_through_the_playbook() -> None:
    """Acceptance 4.

    Two entities, two value chains, and the mechanisms differ — the
    venue's own methodology names the token and the chain's publishes
    nothing. A single chain per security would have averaged a 224x gap.
    """

    playbook = _recorded_service().established("HYPE", AssetClass.CRYPTO)

    assert playbook is not None
    assert len(playbook.chains) == 2

    by_entity = {chain.entity.name: chain for chain in playbook.chains}

    assert set(by_entity) == {"Hyperliquid", "Hyperliquid L1"}

    venue = by_entity["Hyperliquid"]
    chain = by_entity["Hyperliquid L1"]

    assert venue.mechanism is ValueFlowKind.TOKEN_BUYBACK
    assert chain.mechanism is not ValueFlowKind.TOKEN_BUYBACK

    venue_fees = venue.link(ValueStage.FEES)
    chain_fees = chain.link(ValueStage.FEES)

    assert venue_fees is not None and venue_fees.value is not None
    assert chain_fees is not None and chain_fees.value is not None
    assert venue_fees.value > chain_fees.value * 100


def test_hypes_accrual_evidence_names_the_entity_that_supplied_it() -> None:
    """A figure that loses its entity loses the whole S2 discipline."""

    playbook = _recorded_service().established("HYPE", AssetClass.CRYPTO)

    assert playbook is not None

    accrual = playbook.question(CryptoQuestionKey.HOLDER_VALUE_ACCRUAL.value)

    assert accrual is not None

    met = [item for item in accrual.covered if item.is_met]

    assert met
    assert all(item.entity is not None for item in met)


# ── acceptance 5: a shared name is not an identity ──────────────────


def test_1inch_is_not_asked_a_venues_questions() -> None:
    """Acceptance 5, carried forward from S2's Aqua finding.

    The provider's DEX list holds a similarly named product. The
    aggregator is declined the venue questions outright, so there is no
    slot another business's book could be read into.
    """

    playbook = _recorded_service().established("1INCH", AssetClass.CRYPTO)

    assert playbook is not None

    venue = playbook.question(CryptoQuestionKey.VENUE_ACTIVITY.value)

    assert venue is not None
    assert venue.cell is QuestionCell.NOT_APPLICABLE
    assert venue.covered == ()

    decline = next(
        item
        for item in DECLINED[TokenArchetype.APPLICATION_PROTOCOL]
        if item.question is CryptoQuestionKey.VENUE_ACTIVITY
    )

    assert "shared name" in decline.reason


# ── acceptance 6: the same word, different mechanisms ───────────────


def test_the_word_fees_means_a_different_thing_per_asset() -> None:
    """Acceptance 6, measured across the three cases the ruling names."""

    service = _recorded_service()

    mechanisms = {}

    for symbol in ("BTC", "ETH", "HYPE"):
        playbook = service.established(symbol, AssetClass.CRYPTO)

        assert playbook is not None

        mechanisms[symbol] = playbook.chains[0].mechanism

    assert mechanisms["BTC"] is ValueFlowKind.NOT_PRESENT
    assert mechanisms["ETH"] is ValueFlowKind.BURNED
    assert mechanisms["HYPE"] is ValueFlowKind.TOKEN_BUYBACK

    assert len(set(mechanisms.values())) == 3


def test_every_mechanism_is_recognised_from_the_sources_own_wording() -> None:
    """A mechanism this platform declared would not be evidence.

    Each phrase below is a live sentence from the DefiLlama corpus, and
    the last is the reason the buyback clause outranks the holder one:
    Hyperliquid's methodology contains both, and 99% of the fees are the
    buyback.
    """

    assert recognise("Amount of ETH burned — base fees plus blob fees") is (
        ValueFlowKind.BURNED
    )
    assert recognise("Transaction base fees paid by users were burned") is (
        ValueFlowKind.BURNED
    )
    assert recognise("Fees going to governance token holders") is (
        ValueFlowKind.DISTRIBUTED_TO_HOLDERS
    )
    assert (
        recognise(
            "99% of fees go to Assistance Fund for buying HYPE tokens, "
            "excluding builders fees. Hyperliquid HLP: Fees going to "
            "governance token holders"
        )
        is ValueFlowKind.TOKEN_BUYBACK
    )

    # An unrecognised sentence is shown verbatim rather than forced into
    # the nearest member.
    assert recognise("Gas fees paid by users") is None
    assert recognise(None) is None


def test_a_figure_without_a_definition_leaves_the_mechanism_unmet() -> None:
    """1inch's shape: amounts published, no methodology at all.

    The amount is known and what it means is not, and the demand for the
    mechanism stays unmet rather than being satisfied by the figure.
    """

    playbook = _recorded_service().established("1INCH", AssetClass.CRYPTO)

    assert playbook is not None

    accrual = playbook.question(CryptoQuestionKey.HOLDER_VALUE_ACCRUAL.value)

    assert accrual is not None

    mechanism = next(item for item in accrual.covered if item.demand.wants_methodology)

    assert not mechanism.is_met


# ── acceptance 7 and 8: applicability never depends on evidence ─────


def test_applicability_is_identical_with_the_stores_empty() -> None:
    """Acceptance 7, and the structural heart of the slice.

    Run the whole layer against stores that hold nothing and every
    applicability is unchanged. A platform whose questions moved with
    its data would be choosing its questions to suit what it happens to
    have.
    """

    full = _recorded_service()
    empty = _empty_service()

    for symbol in CORPUS:
        with_evidence = full.established(symbol, AssetClass.CRYPTO)
        without = empty.established(symbol, AssetClass.CRYPTO)

        assert with_evidence is not None and without is not None

        assert [item.applicability.state for item in with_evidence.coverage] == [
            item.applicability.state for item in without.coverage
        ], symbol


def test_applicability_cannot_see_evidence_at_all() -> None:
    """The same guarantee, one level down: the signature admits nothing.

    `applicability_for` takes an archetype and a question. There is no
    parameter through which a figure could reach it, which is why the
    property above holds rather than merely happening to.
    """

    with pytest.raises(TypeError):
        applicability_for(  # type: ignore[call-arg]
            TokenArchetype.MONETARY_NETWORK,
            CryptoQuestionKey.LIQUIDITY,
            None,
        )


def test_not_applicable_is_never_produced_by_missing_evidence() -> None:
    """Acceptance 8.

    With every store empty, no question anywhere becomes inapplicable.
    Everything that applies still applies, and reads as evidence
    insufficient instead.
    """

    empty = _empty_service()

    for symbol in CORPUS:
        playbook = empty.established(symbol, AssetClass.CRYPTO)

        assert playbook is not None

        for item in playbook.coverage:
            if item.cell is QuestionCell.NOT_APPLICABLE:
                assert (
                    item.applicability.state
                    is QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE
                )


def test_an_unknown_archetype_declines_nothing() -> None:
    """A statement about this platform is never dressed as one about the asset.

    TAO's design is unread, so no question about its design is refused —
    they are undetermined, which is the different claim.
    """

    playbook = _recorded_service().established("TAO", AssetClass.CRYPTO)

    assert playbook is not None
    assert playbook.declined == ()

    undetermined = [
        item for item in playbook.coverage if item.cell is QuestionCell.UNDETERMINED
    ]

    assert len(undetermined) == 15


# ── acceptance 9: no claimed value is promoted ──────────────────────


def test_no_protocol_claim_becomes_established_through_this_layer() -> None:
    """Acceptance 9.

    Every protocol figure is a single provider's uncorroborated claim
    after S2, and joining it to a question does not corroborate it.
    """

    service = _recorded_service()

    for symbol in CORPUS:
        playbook = service.established(symbol, AssetClass.CRYPTO)

        assert playbook is not None

        for item in playbook.coverage:
            for covered in item.covered:
                if covered.entity is None:
                    continue

                assert covered.standing is not EvidenceStanding.ESTABLISHED, (
                    symbol,
                    item.question.key,
                )


def test_hypes_supply_conflict_survives_intact() -> None:
    """Acceptance 11.

    The supply question reads answerable on an established cap while the
    circulating count remains contested, and the contest is shown rather
    than absorbed.
    """

    playbook = _recorded_service().established("HYPE", AssetClass.CRYPTO)

    assert playbook is not None

    supply = playbook.question(CryptoQuestionKey.SUPPLY_AND_DILUTION.value)

    assert supply is not None
    assert supply.conflicts

    assert any(
        item.demand.token_fact == "circulating_supply" for item in supply.conflicts
    )


# ── acceptance 10 and 13: nothing moved ─────────────────────────────


def test_no_scorer_or_decision_path_can_import_the_crypto_playbook() -> None:
    """Acceptance 10, made structural.

    The guard the third-party rating and the protocol fundamentals both
    carry. A slice that wants applicability inside a score has to argue
    with this test first — which is the point: S5 decides what these
    questions are worth, not S3.
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
        "app/domain/financial_question.py",
        "app/services/business_quality_service.py",
        "app/services/company_facts_service.py",
        "app/services/playbook_selector.py",
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

            if any(
                name in text
                for name in (
                    "crypto_archetype",
                    "crypto_questions",
                    "crypto_playbook",
                    "token_value_flow",
                )
            ):
                offenders.append(str(source.relative_to(root)))

    assert offenders == []


def test_only_the_crypto_quality_model_may_read_the_question_layer() -> None:
    """S5 argued with the guard above, and the guard narrowed rather than went.

    S3 wrote that a slice wanting applicability inside a score would
    have to argue with its import test first. S5 is that slice, under a
    ruling, and it reads the question layer by design — so the boundary
    moves to exactly one module instead of disappearing.

    `company_signal_service` reaches the questions *through* that
    module and names none of them itself, which is the shape that keeps
    the equity path from ever seeing a crypto question.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    permitted = {
        "app/domain/crypto_quality.py",
        "app/services/crypto_asset_quality_service.py",
    }

    for target in sorted(permitted):
        assert (root / target).exists(), target

    signal = (root / "app/services/company_signal_service.py").read_text(
        encoding="utf-8"
    )

    for name in ("crypto_archetype", "crypto_questions", "crypto_playbook"):
        assert name not in signal, name


def test_the_equity_question_layer_is_untouched() -> None:
    """Acceptance 13: no equity playbook learned anything from this."""

    root = pathlib.Path(__file__).resolve().parent.parent

    text = (root / "app/domain/financial_question.py").read_text(encoding="utf-8")

    assert "crypto" not in text.casefold()

    playbook = (root / "app/domain/playbook.py").read_text(encoding="utf-8")

    assert "archetype_for" not in playbook


def test_applicability_still_cannot_be_reached_through_a_score() -> None:
    """Acceptance 10, restated for the model that consumed S3.

    The thing S3 was protecting was never the four thresholds; it was
    that no figure could make a question applicable. S5 reads
    applicability and must not be able to change it, so the guard is
    now the property itself: the quality model asks
    `applicability_for` for nothing, because it takes what the playbook
    already settled — and the playbook settles it before reading any
    evidence.
    """

    code = pathlib.Path("app/services/crypto_asset_quality_service.py").read_text(
        encoding="utf-8"
    )

    assert "applicability_for" not in code

    # And readiness — S5's own new axis — is a property of the question
    # alone. A function that could see a symbol would let a well-covered
    # asset make a question scorable that stays unscorable elsewhere.
    from app.domain import crypto_quality

    signature = inspect.signature(crypto_quality.readiness_for)

    assert list(signature.parameters) == ["question"]


# ── acceptance 12: evidence maturity is not calendar age ────────────


def test_evidence_maturity_never_demands_a_project_age() -> None:
    """Acceptance 12.

    The old age factor measured how long a ticker had existed, which is
    not evidence that anything survived anything. What this question
    demands is observed behaviour — history, drawdowns, incidents — and
    every demand is unmet across the corpus, which is the finding.
    """

    question = QUESTIONS[CryptoQuestionKey.EVIDENCE_MATURITY]

    assert all(demand.token_fact != "project_age" for demand in question.demands)
    assert question.acquisition_demands == question.demands

    service = _recorded_service()

    for symbol in CORPUS:
        playbook = service.established(symbol, AssetClass.CRYPTO)

        assert playbook is not None

        maturity = playbook.question(CryptoQuestionKey.EVIDENCE_MATURITY.value)

        assert maturity is not None
        assert maturity.cell is QuestionCell.ASK_EVIDENCE_INSUFFICIENT
        assert len(maturity.unmet) == len(question.demands), symbol


# ── acceptance 14: a future stablecoin is not forced through these ──


def test_a_stablecoin_is_asked_neither_bitcoins_nor_hypes_questions() -> None:
    """Acceptance 14.

    Declared as a boundary and not as a model: scarcity is inverted for
    a stablecoin and accrual is a question about an issuer's terms, so
    both are refused outright — and the questions it actually needs are
    named as unbuilt rather than silently missing.
    """

    asked = questions_for(TokenArchetype.STABLECOIN)

    assert CryptoQuestionKey.MONETARY_SCARCITY not in asked
    assert CryptoQuestionKey.HOLDER_VALUE_ACCRUAL not in asked
    assert CryptoQuestionKey.VENUE_ACTIVITY not in asked

    for question in (
        CryptoQuestionKey.MONETARY_SCARCITY,
        CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
    ):
        applicability = applicability_for(TokenArchetype.STABLECOIN, question)

        assert applicability.state is QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE
        assert len(applicability.because) > 40

    assert len(ARCHETYPES[TokenArchetype.STABLECOIN].unmodelled) >= 5


# ── the composition itself ──────────────────────────────────────────


def test_hype_composes_rather_than_naming_a_bespoke_kind() -> None:
    """The architectural claim, checked.

    An exchange network owns no question and no refusal of its own: its
    reading is exactly the union of lenses that exist independently of
    it. Four of its five lenses are shared with other archetypes, and
    the fifth — the venue — is the only one no other corpus member
    happens to need, which is a fact about the corpus rather than a
    bespoke rule for one token.
    """

    definition = ARCHETYPES[TokenArchetype.EXCHANGE_NETWORK]

    parts: set[CryptoQuestionKey] = set()

    for capability in definition.capabilities:
        parts |= set(ASKED_BY[capability])

    assert set(questions_for(TokenArchetype.EXCHANGE_NETWORK)) == parts

    # No refusal written for this archetype alone.
    assert TokenArchetype.EXCHANGE_NETWORK not in DECLINED

    exclusive = {
        capability
        for capability in definition.capabilities
        if not any(
            capability in ARCHETYPES[archetype].capabilities
            for archetype in TokenArchetype
            if archetype is not TokenArchetype.EXCHANGE_NETWORK
        )
    }

    assert exclusive == {AnalyticalCapability.VENUE_ECONOMICS}


def test_no_question_or_lens_branches_on_a_symbol() -> None:
    """One-off logic for a single token is what composition prevents.

    The question table and the mechanism reader are the two places a
    "if symbol == HYPE" would hide. Neither may name a ticker at all;
    the only place a symbol appears is the assignment table, where it is
    data with a stated basis.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in ("app/domain/crypto_questions.py", "app/domain/token_value_flow.py"):
        text = (root / module).read_text(encoding="utf-8")

        code = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )

        for symbol in CORPUS:
            assert f'"{symbol}"' not in code, (module, symbol)
            assert f"'{symbol}'" not in code, (module, symbol)


def test_every_capability_changes_the_question_set() -> None:
    """A lens that asks nothing new is metadata, and is not kept."""

    for capability in AnalyticalCapability:
        assert ASKED_BY[capability], capability

        others: set[CryptoQuestionKey] = set()

        for other in AnalyticalCapability:
            if other is not capability:
                others |= set(ASKED_BY[other])

        assert set(ASKED_BY[capability]) - others, capability


def test_every_archetypes_lenses_are_supported_by_its_mapped_entities() -> None:
    """The table is falsifiable against S2's entity mapping.

    A security read through the venue lens must have a venue mapped to
    it. Anything else is a claim the evidence does not support, and it
    would be a defect in this table rather than a property of the asset.
    """

    for symbol in CORPUS:
        assignment = ASSIGNMENTS[symbol]

        unsupported = assignment.definition.unsupported_by(entities_for(symbol))

        assert unsupported == (), (symbol, unsupported)


def test_every_question_is_asked_by_something_and_defined_once() -> None:
    asked: set[CryptoQuestionKey] = set()

    for keys in ASKED_BY.values():
        asked |= set(keys)

    assert asked == set(CryptoQuestionKey)
    assert set(QUESTIONS) == set(CryptoQuestionKey)


def test_every_bound_demand_names_a_fact_this_platform_can_hold() -> None:
    """A demand pointing at nothing would be a permanently unmet gap."""

    for question in QUESTIONS.values():
        for demand in question.demands:
            if demand.token_fact is not None:
                assert demand.token_fact in TOKEN_FACTS, question.key

            if demand.protocol_metric is not None:
                assert demand.protocol_metric in ProtocolMetric, question.key


def test_a_security_outside_the_corpus_is_unknown_rather_than_guessed() -> None:
    assignment = archetype_for("DOGE")

    assert assignment.archetype is TokenArchetype.UNKNOWN
    assert "resembling" in assignment.because


def test_nothing_but_a_cryptocurrency_gets_a_crypto_playbook() -> None:
    service = CryptoPlaybookService()

    for asset_class in (AssetClass.STOCK, AssetClass.ETF, AssetClass.UNKNOWN, None):
        assert service.established("BTC", asset_class) is None


def test_a_declined_question_carries_no_evidence_list() -> None:
    """Listing what would have answered a refused question reads as a gap."""

    playbook = _recorded_service().established("BTC", AssetClass.CRYPTO)

    assert playbook is not None

    for item in playbook.declined:
        assert item.covered == ()


def test_an_unmapped_security_measures_nothing_rather_than_zero() -> None:
    """A shared name does not establish an economic system."""

    class _Unmapped:
        @staticmethod
        def established(
            symbol: str,
            asset_class: AssetClass | None,
        ) -> ProtocolFundamentals | None:
            return ProtocolFundamentals(
                symbol=symbol,
                entities=(),
                facts=(),
                unmapped_because="No economic system has been mapped.",
            )

    service = CryptoPlaybookService(
        facts=_NoFacts(),  # type: ignore[arg-type]
        protocol=_Unmapped(),  # type: ignore[arg-type]
    )

    playbook = service.established("BTC", AssetClass.CRYPTO)

    assert playbook is not None
    assert playbook.chains == ()
    assert playbook.unmapped_because == "No economic system has been mapped."

    activity = playbook.question(CryptoQuestionKey.NETWORK_SECURITY.value)

    assert activity is not None
    assert activity.best_standing is EvidenceStanding.ABSENT


def test_a_sibling_absence_reads_as_no_mechanism_not_as_a_gap() -> None:
    """S2's rule, carried into the value chain.

    A source that defines the rest of the fee family and defines no
    holder mechanism is saying the mechanism does not exist here. A
    source that has published nothing at all is saying nothing.
    """

    entity = ProtocolEntity(
        key="test-chain",
        name="Test",
        kind=ProtocolEntityKind.CHAIN,
        measures="transaction fees",
        mapping_basis="the chain's native asset",
    )

    def _chain_for(availability: MetricAvailability) -> ValueFlowKind:
        return value_chains(
            ProtocolFundamentals(
                symbol="TEST",
                entities=(entity,),
                facts=(
                    ProtocolFact(
                        metric=ProtocolMetric.HOLDER_REVENUE,
                        entity=entity,
                        availability=availability,
                        standing=EvidenceStanding.ABSENT,
                    ),
                ),
            )
        )[0].mechanism

    assert _chain_for(MetricAvailability.NOT_APPLICABLE) is ValueFlowKind.NOT_PRESENT
    assert _chain_for(MetricAvailability.UNAVAILABLE_FREE) is ValueFlowKind.UNREAD
