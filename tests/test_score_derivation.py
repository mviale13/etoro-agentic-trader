"""Why the score is the number it is, in arithmetic an investor can check.

The claim this slice makes: a score stops being a band name the reader
must accept and becomes a sum they can verify. The claims it refuses to
make are just as load-bearing — no invented weights, no penalties that
do not exist, and no decomposition for a score that has none.
"""

from app.domain.company_facts import CompanyFacts
from app.domain.finding import Sense
from app.domain.score_basis import Contribution, ScoreDerivation
from app.services.quality_signal_service import QualitySignalService


def facts(**overrides: object) -> CompanyFacts:
    base: dict[str, object] = {
        "instrument_id": 1,
        "symbol": "EXA",
        "name": "Example",
        "asset_type": "stock",
        "exchange": "NASDAQ",
    }
    base.update(overrides)

    return CompanyFacts(**base)  # type: ignore[arg-type]


def quality(**overrides: object):
    return QualitySignalService().build(facts(**overrides))


# ── the factors survive ─────────────────────────────────────────────


def test_the_count_behind_a_band_is_no_longer_thrown_away() -> None:
    """
    A score that began as *3 of 3* used to reach the dashboard as *80*.

    The signal computed the count, banded it, and dropped it — the same
    defect `Sense` and `Dimension` had, one layer down.
    """

    signal = quality(market_cap=2_000_000_000_000, eps=8.0, dividend_yield=0.7)

    assert signal.quality == "HIGH"
    assert signal.earned == 3
    assert signal.available == 3

    assert signal.contributions == (
        Contribution("Large-cap company.", 1, Sense.FAVOURABLE),
        Contribution("Positive earnings.", 1, Sense.FAVOURABLE),
        Contribution("Dividend-paying business.", 1, Sense.FAVOURABLE),
    )


def test_a_contribution_says_the_same_thing_as_its_finding() -> None:
    """One wording, so the breakdown and the evidence cannot diverge."""

    signal = quality(market_cap=2_000_000_000_000, eps=8.0, dividend_yield=0.7)

    assert [item.statement for item in signal.contributions] == [
        finding.statement for finding in signal.evidence
    ]


# ── what it refuses to claim ────────────────────────────────────────


def test_nothing_ever_subtracts() -> None:
    """
    A factor the company fails earns no point; it does not lose one.

    This is a fact about the scoring, not about the company, and the
    contribution carries the sense so a bare zero cannot be read as a
    penalty. Inventing a -8 here would be the plausible figure on a
    dashboard that invariant 1 exists to forbid.
    """

    signal = quality(market_cap=2_000_000_000_000, eps=-1.2, dividend_yield=0.0)

    assert signal.earned == 1

    points = {item.statement: item.points for item in signal.contributions}

    assert points["Negative earnings."] == 0
    assert points["No dividend."] == 0

    assert all(item.points >= 0 for item in signal.contributions)


def test_a_zero_distinguishes_not_applicable_from_failed() -> None:
    """Two zeroes that mean different things, and the sense tells them apart."""

    signal = quality(market_cap=2_000_000_000_000, eps=-1.2, dividend_yield=0.0)

    senses = {item.statement: item.sense for item in signal.contributions}

    assert senses["Negative earnings."] is Sense.ADVERSE
    assert senses["No dividend."] is Sense.NEUTRAL


def test_every_factor_is_worth_exactly_one_point() -> None:
    """
    No weighting exists, so none is shown.

    A column reading +18 / +15 / -8 would be four measurements this
    platform never took. Weights are earned when something measures
    them, not when a dashboard would look better with them.
    """

    signal = quality(market_cap=2_000_000_000_000, eps=8.0, dividend_yield=0.7)

    assert {item.points for item in signal.contributions} == {1}


# ── the honest edge: capped by what could be read ───────────────────


def test_a_score_capped_by_unreadable_data_says_so() -> None:
    """
    Every readable factor scored, and the band still fell short.

    The bands are absolute, so a company whose dividend could not be
    read cannot reach HIGH however good it is. Without this the investor
    reads MEDIUM as a verdict on the business.
    """

    signal = quality(market_cap=2_000_000_000_000, eps=8.0)

    assert signal.quality == "MEDIUM"
    assert signal.earned == 2
    assert signal.available == 2
    assert signal.next_band_needs == 3

    derivation = ScoreDerivation(
        contributions=signal.contributions,
        earned=signal.earned,
        available=signal.available,
        band=signal.quality,
        score=62,
        scale=(("HIGH", 80), ("MEDIUM", 62), ("LOW", 40)),
        required=signal.next_band_needs,
    )

    assert derivation.is_capped_by_unreadable_factors
    assert "as far as 2 factors reach" in derivation.stated()


def test_a_full_count_is_not_reported_as_capped() -> None:
    signal = quality(market_cap=2_000_000_000_000, eps=8.0, dividend_yield=0.7)

    derivation = ScoreDerivation(
        contributions=signal.contributions,
        earned=signal.earned,
        available=signal.available,
        band=signal.quality,
        score=80,
        scale=(("HIGH", 80),),
        required=signal.next_band_needs,
    )

    assert signal.next_band_needs is None
    assert not derivation.is_capped_by_unreadable_factors
    assert derivation.stated() == "3 of 3 points earned → HIGH → 80."


def test_a_shortfall_the_company_owns_is_not_blamed_on_the_platform() -> None:
    """Three factors readable, one earned — that is the company, not the read."""

    signal = quality(market_cap=2_000_000_000_000, eps=-1.2, dividend_yield=0.0)

    derivation = ScoreDerivation(
        contributions=signal.contributions,
        earned=signal.earned,
        available=signal.available,
        band=signal.quality,
        score=40,
        scale=(("HIGH", 80), ("MEDIUM", 62), ("LOW", 40)),
        required=signal.next_band_needs,
    )

    assert not derivation.is_capped_by_unreadable_factors
    assert derivation.stated() == "1 of 3 points earned → LOW → 40."


# ── nothing read is not a score of zero ─────────────────────────────


def test_a_company_nothing_could_be_read_about_has_no_derivation() -> None:
    """UNKNOWN, not LOW, and no arithmetic to show."""

    signal = quality()

    assert signal.quality == "UNKNOWN"
    assert signal.contributions == ()
    assert signal.available == 0


# ── the score the decision uses is unchanged ────────────────────────


def test_the_band_is_exactly_what_it_was_before() -> None:
    """
    Additive only. The decomposition explains the number; it never moves it.

    A transparency feature that changed a recommendation would be a
    reasoning change wearing a disclosure's clothes.
    """

    assert quality(market_cap=2e12, eps=8.0, dividend_yield=0.7).quality == "HIGH"
    assert quality(market_cap=2e12, eps=8.0, dividend_yield=0.0).quality == "MEDIUM"
    assert quality(market_cap=1e9, eps=8.0, dividend_yield=0.0).quality == "LOW"
    assert quality(market_cap=1e9, eps=-1.0, dividend_yield=0.0).quality == "LOW"


# ── amendment 1: verdict and coverage as first-class fields ─────────


def grounded(symbol: str):
    """The dossier's own quality derivation for a corpus company."""

    from app.application.executive.decision_evidence_builder import (
        DecisionEvidenceBuilder,
    )
    from app.domain.financial_question import FinancialModel
    from app.services.business_quality_service import quality_of
    from app.services.company_understanding_service import (
        CompanyUnderstandingService,
    )

    understanding = CompanyUnderstandingService().understanding(symbol)

    quality = quality_of(symbol, understanding.financial, FinancialModel.GENERIC)

    return DecisionEvidenceBuilder._quality_basis(None, quality).derivation


def test_the_verdict_is_carried_as_data_never_as_prose() -> None:
    """
    A surface that recovered it by splitting a sentence would be doing
    domain reasoning where none belongs.
    """

    derivation = grounded("JPM")

    assert derivation is not None

    verdicts = [item.verdict for item in derivation.contributions]

    assert verdicts == ["excellent", "weak", "declining"]

    # And the statement is the question alone, with no verdict folded in.
    assert all("—" not in item.statement for item in derivation.contributions)


def test_coverage_answers_a_different_question_from_the_share() -> None:
    """
    *One favourable of three answered* reads the business; *three of
    three read* reads this platform. A 62 on a full set and a 62 on a
    third of one are not the same claim.
    """

    derivation = grounded("PG")

    assert derivation is not None

    assert (derivation.earned, derivation.available) == (1, 3)
    assert (derivation.established_factors, derivation.candidate_factors) == (3, 3)
    assert derivation.coverage == "3 of 3 read"


def test_three_companies_at_the_same_score_are_distinguishable() -> None:
    """
    The whole point of the slice. AAPL, PG and JPM all show 62; the
    collapsed row must not present them as the same finding.

    Distinguishable from *fields alone* — no string is parsed and no
    threshold is compared to tell them apart.
    """

    shapes = {}

    for symbol in ("AAPL", "PG", "JPM"):
        derivation = grounded(symbol)

        assert derivation is not None
        assert derivation.score == 62

        shapes[symbol] = (
            tuple(item.sense for item in derivation.contributions),
            tuple(item.verdict for item in derivation.contributions),
        )

    assert len({shapes[symbol] for symbol in shapes}) == 3

    # The sense mix alone separates AAPL; only the verdicts separate
    # PG from JPM, which is why the verdict had to become a field.
    assert shapes["PG"][0] == shapes["JPM"][0]
    assert shapes["PG"][1] != shapes["JPM"][1]


def test_a_score_that_knows_no_candidate_set_leaves_coverage_absent() -> None:
    """Optional and additive: absent is a real state, not a zero."""

    from app.domain.score_basis import ScoreDerivation

    bare = ScoreDerivation(
        contributions=(),
        earned=1,
        available=2,
        band="MEDIUM",
        score=62,
        scale=(("HIGH", 80),),
    )

    assert bare.coverage is None
    assert bare.contributions == ()
