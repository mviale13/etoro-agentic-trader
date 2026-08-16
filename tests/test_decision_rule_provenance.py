"""Every decision-bearing rule is named, versioned, and cannot move quietly.

The Decision Philosophy Audit found eighteen decision-bearing
transformations of which one is licensed. This slice names them — and
these tests are what make the names mean something.

**The fingerprint is the contract.** Each rule's governed constants are
hashed from the live modules and pinned here beside the rule's key and
version. The pin fails in exactly three interesting ways:

- a threshold moves while the version claims to be the same rule —
  the fingerprint no longer matches the pinned triple;
- the version is bumped while behaviour is unchanged — the pinned
  version no longer matches, and the fingerprint says nothing moved;
- a basis stops carrying its rules — the carriage tests fail.

Changing a rule is therefore a two-line, written-down act: move the
constant *and* re-pin the triple with the new version. That is the
whole point — the same discipline committee contracts earned in #113.

**Naming a rule does not validate it.** Enforced below: exactly one
rule is LICENSED, exactly one is ARGUED, and a test would fail if a
future edit upgraded a status without this file changing beside it.
"""

from __future__ import annotations

import ast
import hashlib
import pathlib

import pytest

from app.application.brain.reasoning.portfolio_analyst import PortfolioAnalyst
from app.application.brain.reasoning.risk_analyst import RiskAnalyst
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.cio.artificial_cio import ArtificialCIO
from app.cio.decision_policy import DecisionPolicy
from app.domain.business_quality import (
    BAND_SCORES,
    HIGH_DENOMINATOR,
    HIGH_NUMERATOR,
    MEDIUM_DENOMINATOR,
    MEDIUM_NUMERATOR,
    MINIMUM_ANSWERED,
)
from app.domain.decision_participation import (
    REQUIRED_PARTICIPATING_SIGNALS,
    REQUIRED_RELATIVE_COVERAGE,
)
from app.domain.decision_rules import (
    DECISION_RULES,
    RuleKind,
    RuleStatus,
)
from app.domain.risk_signal import RiskSignal
from app.services.company_committee_service import CompanyCommitteeService
from app.services.momentum_signal_service import MomentumSignalService
from app.services.quality_signal_service import QualitySignalService
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService
from tests.conftest import admissible_market_cap


def _fingerprint(payload: object) -> str:
    """A short stable hash over a rule's governed constants."""

    return hashlib.sha256(repr(payload).encode()).hexdigest()[:12]


#: What each rule governs, read from the live modules. The values here
#: are *references into the implementations*, so a moved constant moves
#: the fingerprint with no test edit — which is what trips the pin.
GOVERNED: dict[str, object] = {
    "risk-bands": (
        RiskSignalService.CALM,
        RiskSignalService.ACTIVE,
        RiskSignalService.VIOLENT,
        RiskSignalService.SHALLOW_DRAWDOWN,
        RiskSignalService.DEEP_DRAWDOWN,
    ),
    "risk-severity": tuple(sorted(RiskSignal.SEVERITIES.items())),
    "pe-bands": (
        ValueSignalService.PE_CHEAP_BELOW,
        ValueSignalService.PE_FAIR_BELOW,
    ),
    "valuation-scores": tuple(sorted(DecisionEvidenceBuilder.VALUATION_SCORES.items())),
    "provider-quality": (
        QualitySignalService.LARGE_CAP_THRESHOLD,
        QualitySignalService.FACTORS,
        QualitySignalService.BANDS,
        tuple(sorted(QualitySignalService.CONFIDENCE.items())),
        tuple(sorted(DecisionEvidenceBuilder.QUALITY_SCORES.items())),
    ),
    "quality-grounded": (
        MINIMUM_ANSWERED,
        (HIGH_NUMERATOR, HIGH_DENOMINATOR),
        (MEDIUM_NUMERATOR, MEDIUM_DENOMINATOR),
        tuple(sorted((band.value, score) for band, score in BAND_SCORES.items())),
    ),
    # The authority rule's constant is the completeness requirement
    # itself — the ruler it gates is fingerprinted separately as
    # `provider-quality`, and is untouched.
    "quality-authority": (QualitySignalService.FACTORS,),
    # The comparison policy: the threshold's declared currency and the
    # rule that only identical denominations compare. The threshold's
    # AMOUNT stays under provider-quality, exactly as it always was.
    "monetary-comparison": (
        QualitySignalService.LARGE_CAP.currency,
        "identical-currency-only",
    ),
    "momentum-bands": (
        MomentumSignalService.STRONG_POSITIVE_THRESHOLD,
        MomentumSignalService.POSITIVE_THRESHOLD,
        MomentumSignalService.NEGATIVE_THRESHOLD,
        MomentumSignalService.STRONG_NEGATIVE_THRESHOLD,
    ),
    # The eligibility rule's constant is a *membership*, not a
    # threshold — sorted so the fingerprint is stable across the set's
    # iteration order, which is not guaranteed between runs.
    "momentum-input-eligibility": tuple(
        sorted(warrant.value for warrant in MomentumSignalService.ELIGIBLE_WARRANTS)
    ),
    # Canonicalised the same way and for the same reason: the membership
    # is unordered, so it is sorted before hashing.
    "market-cap-input-eligibility": tuple(
        sorted(
            warrant.value
            for warrant in QualitySignalService.ELIGIBLE_MARKET_CAP_WARRANTS
        )
    ),
    # The two authority gates. Independent constants, hashed together
    # because they are one rule: a call is actionable only if both hold.
    "decision-authority": (
        REQUIRED_RELATIVE_COVERAGE,
        REQUIRED_PARTICIPATING_SIGNALS,
    ),
    "signal-vote": (
        CompanyCommitteeService.VALUE_WEIGHT,
        CompanyCommitteeService.QUALITY_WEIGHT,
        CompanyCommitteeService.MOMENTUM_WEIGHT,
        CompanyCommitteeService.BUY_THRESHOLD,
        CompanyCommitteeService.SELL_THRESHOLD,
    ),
    "vote-confidence": (
        CompanyCommitteeService.CONFIDENCE_BASE,
        CompanyCommitteeService.CONFIDENCE_SPAN,
    ),
    "cognitive-confidence": (
        PortfolioAnalyst.CONFIDENCE_FLOOR,
        RiskAnalyst.CONFIDENCE,
        "mean-of-three",
    ),
    "evidence-score": (
        DecisionEvidenceBuilder.UNEVIDENCED_DISCOUNT,
        "mean-of-cognitive-and-vote-confidence",
    ),
    "portfolio-fit": ("mean-of-policy-rooms-x100",),
    "decision-gates": tuple(sorted(DecisionPolicy().model_dump().items())),
    "conviction-mean": (
        "unweighted-mean-of-present-scores",
        tuple(
            sorted(
                (state.value, cap)
                for state, cap in ArtificialCIO.CONVICTION_LIMITS.items()
            )
        ),
    ),
    "actionable-buy": ("recommendation == BUY",),
    "veto-sell": ("recommendation == SELL",),
}


#: The pin. (key, version, status, fingerprint) for every rule — the
#: acceptance corpus from the audit, signed. **Editing a row of this
#: table is the deliberate act that changing a rule requires**: the row
#: records that somebody moved the rule and said so.
PINNED: dict[str, tuple[int, RuleStatus, str]] = {
    "risk-bands": (1, RuleStatus.UNSOURCED, "6623b9c87a91"),
    "risk-severity": (1, RuleStatus.ARGUED, "9ec65a79b41c"),
    "pe-bands": (1, RuleStatus.UNSOURCED, "891ea597c522"),
    "valuation-scores": (1, RuleStatus.UNSOURCED, "297b17fef407"),
    "provider-quality": (1, RuleStatus.UNSOURCED, "3adc0fd3fd9f"),
    "quality-grounded": (1, RuleStatus.LICENSED, "02dffb0feb63"),
    "momentum-bands": (1, RuleStatus.UNSOURCED, "2ef4de85d277"),
    "quality-authority": (1, RuleStatus.ARGUED, "4079e4af87d7"),
    "monetary-comparison": (1, RuleStatus.ARGUED, "12627d19b901"),
    "momentum-input-eligibility": (1, RuleStatus.ARGUED, "03e3e0ae4ccf"),
    "market-cap-input-eligibility": (1, RuleStatus.ARGUED, "a3f6c145c2de"),
    "signal-vote": (1, RuleStatus.UNSOURCED, "f2fdf881fe4f"),
    "decision-authority": (1, RuleStatus.ARGUED, "45b26f7f2a21"),
    "vote-confidence": (1, RuleStatus.UNSOURCED, "16d0753d000f"),
    "cognitive-confidence": (1, RuleStatus.UNSOURCED, "d9b82416ea5b"),
    "evidence-score": (1, RuleStatus.UNSOURCED, "3c712b232fa7"),
    "portfolio-fit": (1, RuleStatus.UNSOURCED, "f487032fc7dd"),
    "decision-gates": (1, RuleStatus.UNSOURCED, "526d6052908c"),
    "conviction-mean": (1, RuleStatus.UNSOURCED, "7a0e480ff48b"),
    "actionable-buy": (1, RuleStatus.UNSOURCED, "87618568469b"),
    "veto-sell": (1, RuleStatus.UNSOURCED, "7734b674289c"),
}


# ── 1. the registry and the pin agree, both ways ────────────────────


def test_every_rule_is_pinned_and_every_pin_is_a_rule() -> None:
    assert set(DECISION_RULES) == set(PINNED) == set(GOVERNED)


@pytest.mark.parametrize("key", sorted(PINNED))
def test_a_rule_cannot_move_under_an_unchanged_version(key: str) -> None:
    """The mutation contract, one rule at a time.

    A threshold edit changes the live fingerprint and fails against the
    pin; a version bump changes the rule and fails against the pin; only
    editing both — the constant and this table's row — passes, and that
    edit is the written-down act.
    """

    version, status, fingerprint = PINNED[key]
    rule = DECISION_RULES[key]

    assert rule.version == version, f"{key}: version moved without re-pinning"
    assert rule.status is status, (
        f"{key}: status moved without re-pinning — naming a rule does "
        "not validate it, and neither does editing one"
    )
    assert _fingerprint(GOVERNED[key]) == fingerprint, (
        f"{key}@{version}: the governed constants moved while the "
        "version claims to be the same rule"
    )


# ── 2. naming a rule does not validate it ───────────────────────────


def test_exactly_one_rule_is_licensed() -> None:
    """The audit's finding, preserved structurally.

    Grounded quality is the one transformation with a measured, cited
    basis. If this count ever rises, the new licence must have arrived
    with its measurement — and with an edit to this test saying so.
    """

    licensed = [r for r in DECISION_RULES.values() if r.status is RuleStatus.LICENSED]

    assert [r.key for r in licensed] == ["quality-grounded"]


def test_exactly_six_rules_are_argued() -> None:
    """Naming a rule still validates nothing; arguing one says where.

    The count moves once per warrant consumer, and each entry earns the
    status the same way: an argument written at the implementation.
    `momentum-input-eligibility` is argued from the scale-invariance of
    a ratio over two closes of one series;
    `market-cap-input-eligibility` is argued from the *absence* of any
    such invariance for an absolute comparison, measured over the live
    corpus. A future rule cannot join this list without this line
    changing beside it.
    """

    argued = [r for r in DECISION_RULES.values() if r.status is RuleStatus.ARGUED]

    assert [r.key for r in argued] == [
        "risk-severity",
        "quality-authority",
        "monetary-comparison",
        "momentum-input-eligibility",
        "market-cap-input-eligibility",
        "decision-authority",
    ]


def test_every_rule_says_why_its_status_is_what_it_is() -> None:
    for rule in DECISION_RULES.values():
        assert rule.because

        if rule.status is RuleStatus.UNSOURCED:
            assert "unsourced" in rule.because


def test_the_status_vocabulary_does_not_endorse() -> None:
    """Versioning means *produced under this exact rule*, nothing more."""

    for status in RuleStatus:
        for word in ("correct", "valid", "good", "right", "optimal"):
            assert word not in status.stated


# ── 3. provenance travels with the values ───────────────────────────


def _facts(**readings: float) -> object:
    from app.domain.company_facts import CompanyFacts

    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Co",
        asset_type="stock",
        exchange="TEST",
        **readings,
    )


def test_the_builder_stamps_rules_on_every_scored_basis() -> None:
    """Where a meaning was assigned, the rule that assigned it rides along.

    Absence exits carry no rules on purpose: a score nobody computed
    had no meaning assigned, and a stamp there would claim one was.
    """

    from app.domain.business_quality import BusinessQuality, QualityBand

    builder = DecisionEvidenceBuilder()

    absent_quality = builder._quality_basis(None, None)
    assert absent_quality.rules == ()

    absent_valuation = builder._valuation_basis(None)
    assert absent_valuation.rules == ()

    absent_safety = builder._safety_basis(None)
    assert absent_safety.rules == ()

    unknown_grounded = BusinessQuality(
        symbol="TEST",
        band=QualityBand.UNKNOWN,
        factors=(),
        excluded=(),
        favourable=0,
        answered=0,
        source="test fixture",
    )
    assert builder._grounded_quality_basis(unknown_grounded).rules == ()


def test_every_scored_basis_carries_the_rules_that_scored_it() -> None:
    """The positive half, or dropping a stamp would pass silently.

    A full company fixture reaches every scored exit, and each basis
    must name the exact chain that produced its number.
    """

    from app.domain.company_signals import CompanySignals

    # An admissible magnitude, so all three quality factors read and
    # `provider-quality`'s ruler is actually reached — since
    # `quality-authority@1` a partial question set abstains and would
    # never stamp the band rule at all.
    facts = _facts(
        forward_pe=12.0,
        market_cap=20_000_000_000,
        market_cap_magnitude=admissible_market_cap(20_000_000_000),
        eps=4.2,
        dividend_yield=0.02,
        daily_change_pct=1.0,
        realized_volatility=0.25,
        max_drawdown=0.10,
    )

    signals = CompanySignals(
        value=ValueSignalService().build(facts),
        momentum=MomentumSignalService().build(facts),
        quality=QualitySignalService().build(facts),
        risk=RiskSignalService().build(facts),
    )

    company = CompanyCommitteeService().evaluate("TEST", signals)

    builder = DecisionEvidenceBuilder()

    quality = builder._quality_basis(company, None)
    assert [rule.key for rule in quality.rules] == ["provider-quality"]

    valuation = builder._valuation_basis(company)
    assert [rule.key for rule in valuation.rules] == ["pe-bands", "valuation-scores"]

    safety = builder._safety_basis(company)
    assert [rule.key for rule in safety.rules] == ["risk-bands", "risk-severity"]


def test_the_signals_carry_their_band_rules() -> None:
    facts = _facts(
        forward_pe=12.0,
        market_cap=20_000_000_000,
        market_cap_magnitude=admissible_market_cap(20_000_000_000),
        eps=4.2,
        dividend_yield=0.02,
        daily_change_pct=1.0,
    )

    value = ValueSignalService().build(facts)
    assert value.rule is not None and value.rule.key == "pe-bands"

    quality = QualitySignalService().build(facts)
    assert quality.rule is not None and quality.rule.key == "provider-quality"

    momentum = MomentumSignalService().build(facts)
    assert momentum.rule is not None and momentum.rule.key == "momentum-bands"

    unknowable = _facts()

    assert ValueSignalService().build(unknowable).rule is None

    # Quality's abstention is rule-governed since `quality-authority@1`,
    # for the same reason Momentum's is: a rule decided that the
    # question set was too incomplete to band, and a reader should be
    # able to see which.
    silent_quality = QualitySignalService().build(unknowable)

    assert silent_quality.quality == "UNKNOWN"
    assert silent_quality.rule is not None
    assert silent_quality.rule.key == "quality-authority"

    # Momentum's abstention is itself rule-governed since the first
    # warrant consumer: it names `momentum-input-eligibility`, the rule
    # that decided the input could not be read as a price move. The
    # other two still carry nothing, because nothing decided their
    # silence — the evidence simply was not there.
    silent = MomentumSignalService().build(unknowable)

    assert silent.trend == "UNKNOWN"
    assert silent.rule is not None
    assert silent.rule.key == "momentum-input-eligibility"


def test_the_vote_carries_its_rules() -> None:
    from app.domain.company_signals import CompanySignals

    facts = _facts(
        forward_pe=12.0,
        market_cap=20_000_000_000,
        eps=4.2,
        dividend_yield=0.02,
        daily_change_pct=1.0,
    )

    signals = CompanySignals(
        value=ValueSignalService().build(facts),
        momentum=MomentumSignalService().build(facts),
        quality=QualitySignalService().build(facts),
    )

    recommendation = CompanyCommitteeService().evaluate("TEST", signals)

    # Three since the kernel separated direction from authority: the
    # vote says what the evidence points at, its confidence formula
    # scores that, and `decision-authority` decides whether the
    # direction may be acted on at all. A recommendation that carried
    # only the first two could not tell a reader why a lean was
    # withheld.
    assert [rule.key for rule in recommendation.rules] == [
        "signal-vote",
        "vote-confidence",
        "decision-authority",
    ]


def test_the_decision_carries_the_rules_it_was_decided_under() -> None:
    from app.cio.executive_decision import DecisionEvidence

    decision = ArtificialCIO().decide(
        DecisionEvidence(symbol="TEST", evidence_score=50)
    )

    assert [rule.key for rule in decision.decided_under] == [
        "decision-gates",
        "conviction-mean",
    ]


# ── 4. anonymous policy is hard to reintroduce ──────────────────────

#: The governed path: every module whose comparisons assign investment
#: meaning. A numeric threshold added here must be a named attribute —
#: which is what makes it reachable by a rule fingerprint — or this
#: guard fails.
GOVERNED_MODULES = (
    "app/services/value_signal_service.py",
    "app/services/quality_signal_service.py",
    "app/services/momentum_signal_service.py",
    "app/services/risk_signal_service.py",
    "app/services/company_committee_service.py",
    "app/cio/artificial_cio.py",
)

#: Zero is a semantic boundary (positive earnings, any dividend), not a
#: tuned threshold. Everything else must be named.
ALLOWED_LITERALS = {0}


@pytest.mark.parametrize("module", GOVERNED_MODULES)
def test_no_anonymous_threshold_in_the_governed_path(module: str) -> None:
    """`if score >= 73:` cannot appear here without a name.

    A comparison against a bare number is an unnamed rule: nothing can
    fingerprint it and no basis can cite it. Comparisons must read
    named attributes — `self.PE_CHEAP_BELOW`, `policy.maximum_...` —
    which is precisely what makes them governable.
    """

    tree = ast.parse(pathlib.Path(module).read_text(encoding="utf-8"))

    offences: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue

        for side in (node.left, *node.comparators):
            if (
                isinstance(side, ast.Constant)
                and isinstance(side.value, int | float)
                and side.value not in ALLOWED_LITERALS
            ):
                offences.append(f"line {side.lineno}: bare {side.value!r}")

    assert not offences, (
        f"{module} compares against anonymous numbers — name them so a "
        f"rule can govern them: {offences}"
    )


def test_the_rule_registry_is_immutable_at_the_type() -> None:
    rule = DECISION_RULES["pe-bands"]

    with pytest.raises(AttributeError):
        rule.version = 2  # type: ignore[misc]


def test_kinds_partition_the_registry() -> None:
    """Every rule answers whether it interprets or governs. No third pile."""

    interprets = {
        r.key for r in DECISION_RULES.values() if r.kind is RuleKind.INTERPRETS_EVIDENCE
    }
    governs = {
        r.key for r in DECISION_RULES.values() if r.kind is RuleKind.GOVERNS_DECISION
    }

    assert interprets | governs == set(DECISION_RULES)
    assert not interprets & governs
    assert {"decision-gates", "signal-vote", "actionable-buy", "veto-sell"} <= governs
