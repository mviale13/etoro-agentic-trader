"""Which framework a security is read with, and on what evidence."""

import pytest

from app.domain.asset_class import AssetClass
from app.domain.company_profile import CompanyProfile, Sector
from app.domain.playbook import PLAYBOOKS, PlaybookKind
from app.domain.research_plan import AnalystKey
from app.services.playbook_selector import PlaybookSelector


def profile(
    industry: str | None,
    sector: Sector = Sector.OTHER,
    asset_class: AssetClass = AssetClass.STOCK,
) -> CompanyProfile:
    return CompanyProfile(
        asset_class=asset_class,
        sector=sector,
        industry=industry,
    )


@pytest.mark.parametrize(
    ("industry", "kind"),
    [
        ("Software - Infrastructure", PlaybookKind.SOFTWARE),
        ("Internet Content & Information", PlaybookKind.PLATFORM),
        ("Aerospace & Defense", PlaybookKind.AEROSPACE_DEFENCE),
        ("Banks - Diversified", PlaybookKind.BANK),
        ("Insurance - Life", PlaybookKind.INSURANCE),
        ("Capital Markets", PlaybookKind.ASSET_MANAGER),
        ("REIT - Retail", PlaybookKind.REIT),
        ("Oil & Gas Midstream", PlaybookKind.ENERGY),
        ("Gold", PlaybookKind.MINING),
        ("Drug Manufacturers - General", PlaybookKind.PHARMA),
        ("Semiconductors", PlaybookKind.SEMICONDUCTOR),
    ],
)
def test_the_industry_the_provider_reported_decides(
    industry: str,
    kind: PlaybookKind,
) -> None:
    """Every rule is a substring of the field a reader can check."""

    assert PlaybookSelector().select(profile(industry)).kind is kind


def test_what_a_security_is_outranks_what_it_is_filed_under() -> None:
    """A token filed under financial services is still a token."""

    selected = PlaybookSelector().select(
        profile(
            "Banks - Diversified",
            sector=Sector.FINANCIALS,
            asset_class=AssetClass.CRYPTO,
        )
    )

    assert selected.kind is PlaybookKind.DIGITAL_ASSET


def test_a_reported_industry_with_no_lens_here_is_the_stated_default() -> None:
    """
    Not a specialisation. The general playbook says it is the default.
    """

    selected = PlaybookSelector().select(
        profile("Waste Management", sector=Sector.INDUSTRIALS)
    )

    assert selected.kind is PlaybookKind.GENERAL_CORPORATE
    assert "default" in selected.explanation


def test_no_industry_at_all_is_a_different_absence() -> None:
    """
    A default chosen without evidence is not a classification.

    The one bank in the investor's own book reports no industry from this
    platform's provider, so this is the case that actually occurs — and it
    must not read as though the platform decided anything.
    """

    selected = PlaybookSelector().select(profile(None))

    assert selected.kind is PlaybookKind.UNCLASSIFIED
    assert selected.is_classified is False

    # It is still analysed, on the ordinary accounts.
    assert selected.analysts


def test_a_declined_analyst_carries_the_reason_it_was_declined() -> None:
    """
    A shorter list of verdicts is ambiguous on its own.

    An analysis this platform chose not to run and one that failed to
    read mean opposite things about a case, so the reason travels with
    the exclusion.
    """

    bank = PLAYBOOKS[PlaybookKind.BANK]

    assert AnalystKey.CASH_FLOW not in bank.analysts

    declined = next(item for item in bank.excluded)

    assert declined.analyst is AnalystKey.CASH_FLOW
    assert "deposit" in declined.reason


def test_a_security_with_no_accounts_is_asked_nothing_and_says_why() -> None:
    """
    Bitcoin's missing valuation is the playbook, not a gap in the data.
    """

    digital = PLAYBOOKS[PlaybookKind.DIGITAL_ASSET]

    assert digital.analysts == ()
    assert len(digital.excluded) == 4
    assert all("no financial statements" in item.reason for item in digital.excluded)
