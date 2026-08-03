"""What the Artificial CIO says when a question does not apply."""

from app.cio import ArtificialCIO, DecisionEvidence, DecisionState
from app.domain.asset_class import AssetClass


def evidence(**overrides: object) -> DecisionEvidence:
    return DecisionEvidence(
        **{
            "symbol": "BTC",
            "quality_score": None,
            "evidence_score": 69,
            "valuation_score": None,
            "risk_score": 65,
            "portfolio_fit_score": 97,
            **overrides,
        }  # type: ignore[arg-type]
    )


def test_a_token_is_not_told_its_quality_is_merely_unmeasured() -> None:
    """
    "Business quality has not been measured" promises a measurement.

    None is coming. A cryptocurrency has no business and no earnings, so
    the case would sit at INVESTIGATE forever while the wording implied a
    later cycle might close the gap.
    """

    decision = ArtificialCIO().decide(evidence(asset_class=AssetClass.CRYPTO))

    assert decision.state is DecisionState.INVESTIGATE
    assert "cryptocurrency has no business quality" in decision.rationale
    assert "has not been measured" not in decision.rationale


def test_the_limit_is_stated_as_the_platform_s_own() -> None:
    """It is not a claim that the asset is unworthy, only unassessable here."""

    rationale = (
        ArtificialCIO().decide(evidence(asset_class=AssetClass.CRYPTO)).rationale
    )

    assert "this platform judges an investment case on both" in rationale
    assert "measured risk and portfolio fit are reported" in rationale


def test_a_company_whose_quality_is_missing_still_reads_as_pending() -> None:
    """For a business the measurement genuinely may arrive."""

    decision = ArtificialCIO().decide(evidence(asset_class=AssetClass.STOCK))

    assert "has not been measured" in decision.rationale


def test_an_unclassified_asset_is_not_told_it_has_no_business() -> None:
    """
    UNKNOWN means the platform could not classify it, nothing more.

    Treating "not known to have a company" as "known to have none" would
    assert something nobody established — the substitution the rest of the
    decision path stopped making.
    """

    for asset_class in (None, AssetClass.UNKNOWN):
        rationale = ArtificialCIO().decide(evidence(asset_class=asset_class)).rationale

        assert "has not been measured" in rationale
        assert "no business" not in rationale
