"""S5: which durable qualities of a token this platform can judge today.

One test per acceptance criterion in the ruling. The ones that matter
most cannot be read off the code: that a question's readiness never
depends on an asset, that a conflicted figure leaves a question
unanswered rather than answered badly, and that a missing answer never
becomes a bad one.

**Nothing here reads the live store or the network.** Every case runs on
the readings recorded during the S5 measurement on 2026-08-10 — each
vendor's claim, the ledger totals and the provider's protocol figures —
pushed through the real services. A test that consulted `data/cache`
would pass on this machine, fail on a clean checkout, and change its own
subject the next time `movrvest acquire` ran.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.crypto_quality import (
    MARKET_ROBUSTNESS_RULE,
    MINIMUM_SCORED,
    READINESS,
    RULES,
    QualityReadiness,
    QuestionParticipation,
    headline_for,
    readiness_for,
)
from app.domain.crypto_questions import QUESTIONS, CryptoQuestionKey
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_fundamentals import ProtocolFundamentals, ProtocolMetric
from app.domain.provenance import Provenance
from app.domain.supply_semantics import SupplyFact, SupplyPicture
from app.domain.token_fact_validation import TokenClaimSet, judge
from app.domain.token_facts import TokenMarketFacts
from app.providers.defillama_provider import ProtocolClaimSet, ProtocolMetricClaim
from app.services.crypto_asset_quality_service import (
    CryptoAssetQualityService,
    signal_of,
)
from app.services.crypto_playbook_service import CryptoPlaybookService
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService

READ = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


def _identifiers(module: str) -> str:
    """What a module can reach: names, attributes, imports. No prose.

    Every guard below asks what a module can *reach*, never what it
    mentions. The quality model says in as many words that it will not
    read `CompanyFacts.circulating_supply`, and a raw text search would
    forbid it from saying so — the same lesson the market-context suite
    learned about naming the thing it refuses.
    """

    tree = ast.parse(pathlib.Path(module).read_text(encoding="utf-8"))

    words: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            words.append(node.id)
        elif isinstance(node, ast.Attribute):
            words.append(node.attr)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            words.append(node.name)
        elif isinstance(node, ast.alias):
            words.append(f"{node.name} {node.asname or ''}")
        elif isinstance(node, ast.ImportFrom):
            words.append(node.module or "")
        elif isinstance(node, ast.arg):
            words.append(node.arg)

    return "\n".join(words)


# ── the recorded readings ───────────────────────────────────────────

#: Each vendor's market claim on 2026-08-10, per security. Prices and
#: supplies are the real ones, so a market capitalisation is the product
#: the vendor actually published.
_MARKET: dict[str, dict[str, dict[str, float]]] = {
    "BTC": {
        "TokenInsight": {
            "price": 65_212.05,
            "circulating_supply": 20_068_225.0,
            "max_supply": 21_000_000.0,
        },
        "CoinGecko": {
            "price": 65_210.0,
            "circulating_supply": 20_068_243.0,
            "max_supply": 21_000_000.0,
        },
    },
    # The S1 conflict, unchanged: two coherent claimants 51% apart on
    # what counts as circulating, so no market capitalisation is served.
    "HYPE": {
        "TokenInsight": {
            "price": 54.62942692718245,
            "circulating_supply": 336_685_219.0,
            "max_supply": 1_000_000_000.0,
        },
        "CoinGecko": {
            "price": 54.62942692718245,
            "circulating_supply": 222_445_714.0,
            "max_supply": 1_000_000_000.0,
        },
    },
    # Small enough to fall through the floor: $119m against a $500m band.
    "1INCH": {
        "TokenInsight": {
            "price": 0.08455767548381632,
            "circulating_supply": 1_412_361_326.1953669,
            "max_supply": 1_500_000_000.0,
        },
        "CoinGecko": {
            "price": 0.08496,
            "circulating_supply": 1_405_573_965.7275,
            "max_supply": 1_500_000_000.0,
        },
    },
    # Between the two thresholds.
    "ADA": {
        "TokenInsight": {
            "price": 0.19813210779360507,
            "circulating_supply": 38_803_572_882.17353,
            "max_supply": 45_000_000_000.0,
        },
        "CoinGecko": {
            "price": 0.1975,
            "circulating_supply": 37_353_519_633.58835,
            "max_supply": 45_000_000_000.0,
        },
    },
}


def _claims(symbol: str, source: str) -> TokenClaimSet:
    values = _MARKET[symbol][source]

    return TokenClaimSet(
        source=source,
        read=Provenance(source=source, observed_at=READ),
        symbol_echo=symbol,
        price=values["price"],
        market_cap=values["price"] * values["circulating_supply"],
        circulating_supply=values["circulating_supply"],
        max_supply=values["max_supply"],
    )


class _RecordedTokenFacts:
    """The recorded claims, judged by the real S1 gate, reading no store."""

    @staticmethod
    def established(
        symbol: str,
        name: str,
        asset_class: AssetClass | None,
    ) -> TokenMarketFacts | None:
        if asset_class is not AssetClass.CRYPTO or symbol not in _MARKET:
            return None

        return judge(symbol, [_claims(symbol, source) for source in _MARKET[symbol]])


#: Hyperliquid's economics as the provider published them: a mechanism
#: in the provider's own sentence, and an amount only it reports.
_PROTOCOL: dict[str, ProtocolClaimSet] = {
    "hyperliquid-protocol": ProtocolClaimSet(
        entity_key="hyperliquid-protocol",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 842_720.0, "24 hours"),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                534_851.0,
                "24 hours",
                methodology=(
                    "Hyperliquid Perps: 99% of fees go to Assistance Fund "
                    "for buying HYPE"
                ),
            ),
            ProtocolMetricClaim(ProtocolMetric.TVL, 6_256_626_645.166655, "instant"),
            ProtocolMetricClaim(ProtocolMetric.DEX_VOLUME, 38_730_237.0, "24 hours"),
        ),
        defines=frozenset({ProtocolMetric.HOLDER_REVENUE}),
    ),
    "bitcoin-chain": ProtocolClaimSet(
        entity_key="bitcoin-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(ProtocolMetricClaim(ProtocolMetric.FEES, 139_032.0, "24 hours"),),
        defines=frozenset(),
    ),
}


class _RecordedProtocolClaims:
    @staticmethod
    def claim_set(entity_key: str) -> ProtocolClaimSet | None:
        return _PROTOCOL.get(entity_key)


class _NoSupply:
    """A supply layer that holds nothing, for the cases that ignore it."""

    @staticmethod
    def established(
        symbol: str,
        asset_class: AssetClass | None,
    ) -> SupplyPicture | None:
        return SupplyPicture(symbol=symbol, unavailable_because="nothing read")


def _service(supply: object | None = None) -> CryptoAssetQualityService:
    return CryptoAssetQualityService(
        playbook=CryptoPlaybookService(
            facts=_RecordedTokenFacts(),  # type: ignore[arg-type]
            protocol=ProtocolFundamentalsService(
                sources=(_RecordedProtocolClaims(),),
            ),
        ),
        supply=supply or _NoSupply(),  # type: ignore[arg-type]
    )


def _for(symbol: str, supply: object | None = None):  # type: ignore[no-untyped-def]
    quality = _service(supply).established(symbol, AssetClass.CRYPTO)

    assert quality is not None

    return quality


def _answer(symbol: str, question: CryptoQuestionKey, supply: object | None = None):  # type: ignore[no-untyped-def]
    for answer in _for(symbol, supply).answers:
        if answer.question is question:
            return answer

    raise AssertionError(question)


# ── acceptance 1 and 2: the supply concepts, explicitly ─────────────


def test_the_legacy_generic_circulating_field_is_not_the_scoring_authority() -> None:
    """Acceptance 1.

    The ruling's first instruction. `CompanyFacts.circulating_supply` is
    a number with no concept attached, and S4.6 proved a number without
    its concept cannot be compared with anything. The quality model
    never reads it — not to repair the old issuance factor, and not
    anywhere else.
    """

    for module in (
        "app/domain/crypto_quality.py",
        "app/services/crypto_asset_quality_service.py",
    ):
        code = _identifiers(module)

        assert "CompanyFacts" not in code, module
        assert "circulating_supply" not in code, module


def test_the_supply_question_consumes_the_s46_concepts_by_name() -> None:
    """Acceptance 2.

    The emitted share is computed from `EMITTED_SUPPLY` over
    `MAX_SUPPLY` — two named concepts — and reported with the source and
    the authority of each. Cardano's own ledger is the case: 86.2% of a
    45bn cap emitted, which the vendor field published as 100%.
    """

    from app.domain.evidence_authority import EvidenceAuthority
    from app.domain.supply_mappings import CARDANO_SUPPLY
    from app.domain.supply_semantics import SupplyConcept, SupplyMethodology

    vendor = SupplyMethodology(
        key="vendor-max",
        defined_by="TokenInsight",
        stated="the protocol's stated maximum",
        disclosed=True,
    )

    class _Cardano:
        @staticmethod
        def established(
            symbol: str,
            asset_class: AssetClass | None,
        ) -> SupplyPicture:
            return SupplyPicture(
                symbol=symbol,
                facts=(
                    SupplyFact(
                        concept=SupplyConcept.EMITTED_SUPPLY,
                        methodology=CARDANO_SUPPLY,
                        value=38_803_572_882.17353,
                        unit="tokens",
                        authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                        standing=EvidenceStanding.CLAIMED,
                        source="Cardano ledger totals",
                    ),
                    SupplyFact(
                        concept=SupplyConcept.MAX_SUPPLY,
                        methodology=vendor,
                        value=45_000_000_000.0,
                        unit="tokens",
                        authority=EvidenceAuthority.SECONDARY_AGGREGATE,
                        standing=EvidenceStanding.CLAIMED,
                        source="TokenInsight",
                    ),
                ),
            )

    answer = _answer("ADA", CryptoQuestionKey.SUPPLY_AND_DILUTION, _Cardano())

    assert answer.participation is QuestionParticipation.SHOWN
    assert any(
        "86.2% of that maximum has been emitted" in line for line in answer.shown
    )
    assert any("Cardano ledger totals" in line for line in answer.shown)


# ── acceptance 3 and 4: emitted share is not dilution ───────────────


def test_the_emitted_share_is_never_called_dilution() -> None:
    """Acceptance 3.

    A share of a cap that has been issued is a fact. What the rest
    arriving does to a holder depends on when it arrives and to whom,
    and neither is read — so the ratio is reported as an emitted share
    and the word does not appear.
    """

    for ruling in READINESS.values():
        assert "dilution risk" not in ruling.because.casefold()

    answer = _answer("BTC", CryptoQuestionKey.SUPPLY_AND_DILUTION)

    for line in answer.shown:
        assert "dilut" not in line.casefold()


def test_future_supply_pressure_stays_separate_and_unscored() -> None:
    """Acceptance 4.

    Two assets at the same emitted share can face entirely different
    futures. Where no schedule is held the model says so, in the place a
    schedule would have gone, rather than letting the ratio stand in for
    it.
    """

    from app.domain.evidence_authority import EvidenceAuthority
    from app.domain.supply_semantics import SupplyConcept, SupplyMethodology

    disclosed = SupplyMethodology(
        key="protocol-max",
        defined_by="Hyperliquid",
        stated="the protocol's own maximum",
        disclosed=True,
    )

    class _NoSchedule:
        @staticmethod
        def established(
            symbol: str,
            asset_class: AssetClass | None,
        ) -> SupplyPicture:
            return SupplyPicture(
                symbol=symbol,
                facts=(
                    SupplyFact(
                        concept=SupplyConcept.MAX_SUPPLY,
                        methodology=disclosed,
                        value=1_000_000_000.0,
                        unit="tokens",
                        authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                        standing=EvidenceStanding.CLAIMED,
                        source="Hyperliquid info API",
                    ),
                ),
            )

    answer = _answer("HYPE", CryptoQuestionKey.SUPPLY_AND_DILUTION, _NoSchedule())

    assert any("No emission schedule is held" in line for line in answer.shown)
    assert answer.participation is QuestionParticipation.SHOWN


# ── acceptance 5: age does not return ───────────────────────────────


def test_project_age_is_gone_and_evidence_maturity_is_outside_the_score() -> None:
    """Acceptance 5, and the ruling's eleventh section.

    Bitcoin must not become HIGH for being old. The question that used
    to carry age is classified as outside asset quality altogether —
    which promises no future score, unlike NOT_READY, and can only be
    changed by a ruling.
    """

    ruling = readiness_for(CryptoQuestionKey.EVIDENCE_MATURITY)

    assert ruling.readiness is QualityReadiness.OUTSIDE_ASSET_QUALITY
    assert ruling.would_change is None

    answer = _answer("BTC", CryptoQuestionKey.EVIDENCE_MATURITY)

    assert answer.participation is QuestionParticipation.OUTSIDE
    assert answer.points == 0


# ── acceptance 8 and 9: absence is never a mark against ─────────────


def test_a_conflicted_figure_leaves_a_question_unanswered_not_failed() -> None:
    """Acceptance 8, on the corpus case that forces it.

    Hyperliquid's market capitalisation is conflicted: two coherent
    claimants 51% apart on what circulates. The rule reads established
    evidence only, so the question is unanswered — and unanswered
    subtracts nothing, because the denominator counts answers.
    """

    quality = _for("HYPE")

    answer = _answer("HYPE", CryptoQuestionKey.MARKET_ROBUSTNESS)

    assert answer.participation is QuestionParticipation.SCORABLE_UNANSWERED
    assert answer.band is None
    assert answer.points == 0

    # The unanswered question is not in the denominator. Nothing was
    # judged, so nothing is available to have been lost.
    assert quality.available == 0
    assert quality.earned == 0

    assert "conflicted" not in quality.quality.casefold()
    assert quality.quality == "UNKNOWN"


def test_claimed_protocol_economics_never_become_quality_points() -> None:
    """Acceptance 9.

    Hyperliquid's fee economics are the most economically compelling
    evidence in the corpus and every figure is one provider's claim.
    Compelling is not a standing.
    """

    quality = _for("HYPE")

    for answer in quality.answers:
        if answer.question in (
            CryptoQuestionKey.ECONOMIC_ACTIVITY,
            CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
            CryptoQuestionKey.CAPITAL_COMMITTED,
            CryptoQuestionKey.VENUE_ACTIVITY,
        ):
            assert answer.points == 0
            assert not answer.scored


# ── acceptance 10: HYPE's accrual stays visible ─────────────────────


def test_hype_value_accrual_is_applicable_visible_and_unscored() -> None:
    """Acceptance 10, the case the ruling names.

    Three separate statements, all true at once: the question applies,
    the mechanism is evidenced in the provider's own words, and the
    amount is a claim. A platform that showed only the first would look
    ignorant, and one that scored the third would be wrong.
    """

    answer = _answer("HYPE", CryptoQuestionKey.HOLDER_VALUE_ACCRUAL)

    assert answer.participation is QuestionParticipation.SHOWN
    assert not answer.scored

    shown = " ".join(answer.shown)

    assert "Assistance Fund" in shown
    assert "provider claim" in shown.casefold()


# ── acceptance 11: liquidity, refused on measurement ────────────────


def test_liquidity_is_not_scored_because_the_question_cannot_be_answered() -> None:
    """Acceptance 11.

    The refusal is measured, not asserted: the inherited turnover ratio
    ranks Bitcoin below 1inch. No rule exists for the question and its
    readiness names what would change it.
    """

    ruling = readiness_for(CryptoQuestionKey.LIQUIDITY)

    assert ruling.readiness is QualityReadiness.NOT_READY
    assert CryptoQuestionKey.LIQUIDITY not in RULES
    assert ruling.would_change is not None

    answer = _answer("BTC", CryptoQuestionKey.LIQUIDITY)

    assert answer.participation is QuestionParticipation.UNANSWERABLE


# ── acceptance 12: every factor has a named rule and a basis ────────


def test_every_scorable_question_has_a_named_versioned_measured_rule() -> None:
    """Acceptance 12.

    No score exists without a rule table, and no rule table without the
    measurement that set its thresholds.
    """

    scorable = {key for key, ruling in READINESS.items() if ruling.readiness.scores}

    assert set(RULES) == scorable

    for rule in RULES.values():
        assert rule.name
        assert rule.version
        assert rule.measured_basis
        assert rule.bands
        assert rule.bands[-1].at_least is None, rule.name

        # Bands descend, so the first match is the right one.
        floors = [band.at_least for band in rule.bands[:-1]]

        assert floors == sorted(floors, reverse=True), rule.name


def test_every_question_is_classified_exactly_once() -> None:
    """The model covers the question set and invents nothing."""

    assert set(READINESS) == set(QUESTIONS)


def test_the_market_robustness_bands_are_the_measured_ones() -> None:
    """The thresholds, asserted at the values the measurement produced.

    $10bn survived from the inherited table because the measurement
    supported it; $1bn did not, and became $500m. A later slice moving
    either has to do it deliberately.
    """

    rule = MARKET_ROBUSTNESS_RULE

    assert [band.at_least for band in rule.bands] == [
        10_000_000_000,
        500_000_000,
        None,
    ]
    assert [band.points for band in rule.bands] == [2, 1, 0]
    assert [band.verdict for band in rule.bands] == ["robust", "adequate", "fragile"]


def test_the_bands_land_where_the_corpus_says_they_should() -> None:
    """The three outcomes, each on a real asset.

    Bitcoin clears the upper threshold, Cardano sits between the two,
    and 1inch falls through the floor at $119m.
    """

    assert _answer("BTC", CryptoQuestionKey.MARKET_ROBUSTNESS).band is not None
    assert _answer("BTC", CryptoQuestionKey.MARKET_ROBUSTNESS).band.verdict == "robust"
    assert (
        _answer("ADA", CryptoQuestionKey.MARKET_ROBUSTNESS).band.verdict == "adequate"
    )
    assert (
        _answer("1INCH", CryptoQuestionKey.MARKET_ROBUSTNESS).band.verdict == "fragile"
    )


# ── acceptance 13: different archetypes, different questions ────────


def test_two_archetypes_are_asked_different_questions() -> None:
    """Acceptance 13.

    Bitcoin is asked nine questions and Hyperliquid fifteen, and neither
    set is a subset of the other's failures. A shared headline would not
    mean they passed the same tests, which is why the composition is
    reported beside it.
    """

    bitcoin = {
        answer.question
        for answer in _for("BTC").answers
        if answer.participation
        not in (
            QuestionParticipation.NOT_APPLICABLE,
            QuestionParticipation.UNDETERMINED,
        )
    }
    hyperliquid = {
        answer.question
        for answer in _for("HYPE").answers
        if answer.participation
        not in (
            QuestionParticipation.NOT_APPLICABLE,
            QuestionParticipation.UNDETERMINED,
        )
    }

    assert CryptoQuestionKey.MONETARY_SCARCITY in bitcoin
    assert CryptoQuestionKey.MONETARY_SCARCITY not in hyperliquid

    assert CryptoQuestionKey.HOLDER_VALUE_ACCRUAL in hyperliquid
    assert CryptoQuestionKey.HOLDER_VALUE_ACCRUAL not in bitcoin

    # And the questions both are asked are asked of both.
    assert CryptoQuestionKey.MARKET_ROBUSTNESS in bitcoin & hyperliquid


# ── acceptance 14: a headline reports its coverage ──────────────────


def test_a_headline_requires_a_quorum_and_reports_why_it_is_absent() -> None:
    """Acceptance 14, and the ruling's sixteenth section.

    One question is scorable and a band needs two, so no crypto asset
    carries a band today. The reason is stated as a fact about the
    platform's evidence — never as a fact about the asset.
    """

    assert MINIMUM_SCORED == 2

    quality = _for("BTC")

    assert quality.quality == "UNKNOWN"
    assert quality.coverage.scorable == 1
    assert quality.coverage.answered == 1
    assert "not about the asset" in quality.because

    # Bitcoin answered its one scorable question at the top band and
    # still gets no headline. The points are kept so the reason is
    # checkable rather than merely stated.
    assert quality.earned == 2
    assert quality.available == 2


def test_coverage_and_quality_are_different_numbers() -> None:
    """The ruling's tenth section, made structural.

    Confidence is computed from coverage alone. No band, no figure and
    no verdict enters it, so a strong reading cannot raise it and a
    weak one cannot lower it.
    """

    from app.services.crypto_asset_quality_service import _confidence

    body = ast.parse(inspect.getsource(_confidence)).body[0]

    assert isinstance(body, ast.FunctionDef)

    # The docstring says the rule; the code must obey it.
    reachable = "\n".join(
        node.attr for node in ast.walk(body) if isinstance(node, ast.Attribute)
    )

    for forbidden in ("band", "earned", "points", "value", "quality", "verdict"):
        assert forbidden not in reachable, forbidden

    # It reads coverage and nothing else.
    assert list(inspect.signature(_confidence).parameters) == ["coverage"]


def test_an_unestablished_archetype_lowers_confidence_rather_than_raising_it() -> None:
    """The inversion found while measuring, and fixed.

    Counting only *applicable* questions rewarded the one security with
    no archetype: Bittensor was asked four questions instead of nineteen
    and came out the best-covered asset in the corpus. Undetermined
    questions now count in the denominator.
    """

    from app.domain.crypto_quality import QualityCoverage

    established = QualityCoverage(
        applicable=9, scorable=1, answered=1, shown=2, unanswerable=5, outside=1
    )
    unclassified = QualityCoverage(
        applicable=4,
        scorable=1,
        answered=1,
        shown=1,
        unanswerable=1,
        outside=1,
        undetermined=15,
    )

    assert unclassified.in_scope > established.in_scope
    assert unclassified.judged_reach < established.judged_reach


# ── acceptance 15: TAO may remain UNKNOWN ───────────────────────────


def test_an_unclassified_asset_is_unknown_and_not_poor() -> None:
    """Acceptance 15.

    An incomplete classification makes a headline unavailable. It must
    not make one bad: `UNKNOWN` is emitted, `LOW` is not, and the reason
    names the platform.
    """

    quality = _service().established("TAO", AssetClass.CRYPTO)

    assert quality is not None
    assert quality.quality == "UNKNOWN"
    assert quality.coverage.undetermined > 0


# ── acceptance 16 and 17: nothing else moved ────────────────────────


def test_no_decision_threshold_changed() -> None:
    """Acceptance 16.

    The band-to-score mapping the platform already fixed is untouched,
    and the quality model emits the same four words it always emitted.
    """

    from app.application.executive.decision_evidence_builder import (
        DecisionEvidenceBuilder,
    )

    assert DecisionEvidenceBuilder.QUALITY_SCORES == {
        "HIGH": 80,
        "MEDIUM": 62,
        "LOW": 40,
    }

    assert headline_for(2, 2) == "HIGH"
    assert headline_for(1, 2) == "MEDIUM"
    assert headline_for(0, 2) == "LOW"
    assert headline_for(0, 0) == "UNKNOWN"


def test_equity_scoring_is_untouched() -> None:
    """Acceptance 17.

    Asset-class applicability carries the difference. The company
    quality signal knows nothing about any of this.
    """

    equity = inspect.getsource(
        __import__("app.services.quality_signal_service", fromlist=["x"])
    )

    assert "crypto" not in equity.casefold()


# ── the signal adapter ──────────────────────────────────────────────


def test_the_signal_carries_the_scored_question_and_the_shown_evidence() -> None:
    """The model reaches the surfaces that already render a signal.

    Scored questions become contributions with their rule's own verdict
    word; shown evidence becomes neutral findings, because a claim that
    argued for or against a case through its tone would be scoring by
    another route.
    """

    from app.domain.finding import Sense

    signal = signal_of(_for("BTC"))

    assert signal.quality == "UNKNOWN"
    assert len(signal.contributions) == 1
    assert signal.contributions[0].verdict == "robust"

    shown = [
        finding
        for finding in signal.evidence
        if finding.statement != signal.evidence[0].statement
    ]

    for finding in shown:
        assert finding.sense is Sense.NEUTRAL


def test_a_token_is_never_asked_a_company_question() -> None:
    """The routing, at the seam.

    `CompanySignalService` sends a cryptocurrency to this model and
    hands it no `CompanyFacts`, so a token's market capitalisation can
    never be read as a company's equity value again.
    """

    routing = inspect.getsource(
        __import__("app.services.company_signal_service", fromlist=["x"])
    )

    assert "CryptoAssetQualityService" in routing
    assert "Large-cap" not in routing


# ── the read-only rule ──────────────────────────────────────────────


def test_the_model_fetches_nothing_and_asks_no_model() -> None:
    """A page view may sit behind this door.

    The rule both knowledge services live by, extended to the crypto
    family. Stubs that raise on any acquisition are threaded through and
    the whole corpus is read.
    """

    class _Exploding:
        def established(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("a page view acquired something")

    class _StoreOnly:
        """A playbook whose evidence services would fail if called."""

        @staticmethod
        def established(
            symbol: str,
            asset_class: AssetClass | None,
        ) -> ProtocolFundamentals | None:
            return None

    service = CryptoAssetQualityService(
        playbook=CryptoPlaybookService(
            facts=_RecordedTokenFacts(),  # type: ignore[arg-type]
            protocol=_StoreOnly(),  # type: ignore[arg-type]
        ),
        supply=_NoSupply(),  # type: ignore[arg-type]
    )

    for symbol in ("BTC", "HYPE", "ADA", "1INCH", "TAO"):
        assert service.established(symbol, AssetClass.CRYPTO) is not None


def test_nothing_that_is_not_a_token_is_answered() -> None:
    """The same rule every crypto service lives by."""

    for asset_class in (AssetClass.STOCK, AssetClass.ETF, None):
        assert _service().established("AAPL", asset_class) is None


def test_readiness_is_a_property_of_the_question_alone() -> None:
    """The structural guarantee beneath the ruling's tenth section.

    `readiness_for` takes no symbol and no figure. A function that could
    see either would let a well-covered asset make a question scorable
    that stays unscorable for everything else, and *this platform
    cannot judge this yet* would become *this asset does badly here*.
    """

    assert list(inspect.signature(readiness_for).parameters) == ["question"]

    # And the same set is scorable for every asset in the corpus.
    scorable_everywhere = {
        symbol: {
            answer.question
            for answer in _for(symbol).answers
            if answer.participation
            in (
                QuestionParticipation.SCORED,
                QuestionParticipation.SCORABLE_UNANSWERED,
            )
        }
        for symbol in ("BTC", "HYPE", "ADA", "1INCH")
    }

    assert len(set(map(frozenset, scorable_everywhere.values()))) == 1


def test_a_question_the_archetype_refuses_is_never_a_gap() -> None:
    """The S3 discipline, carried into the score.

    Bitcoin is not short of a holder-accrual figure. It is not asked for
    one, and the model reports the refusal rather than an absence — so
    no acquisition slice is ever pointed at evidence that would answer
    the wrong question.
    """

    answer = _answer("BTC", CryptoQuestionKey.HOLDER_VALUE_ACCRUAL)

    assert answer.participation is QuestionParticipation.NOT_APPLICABLE
    assert answer.shown == ()
    assert "monetary asset's return is not a distribution" in answer.because


def test_a_token_is_never_told_its_business_figures_are_unreadable() -> None:
    """The defect the dossier showed, and the seam it came through.

    Asked to explain an UNKNOWN, the executive builder had one sentence:
    *the figures a business is judged on could not be read*. It printed
    that about Bitcoin — which is not a business, and whose one scorable
    question was answered at the top band. Only the signal knows why it
    reads as it does, so the signal now carries the account.
    """

    signal = signal_of(_for("BTC"))

    assert signal.basis is not None
    assert "business" not in signal.basis
    assert "a band requires 2" in signal.basis
