"""Every security reaches a playbook, and the playbook decides the plan."""

import pytest

from app.domain.asset_class import AssetClass
from app.domain.company_profile import CompanyProfile, Sector
from app.domain.playbook import PlaybookKind
from app.services.research_strategy_factory import ResearchStrategyFactory


def profile(
    asset_class: AssetClass = AssetClass.STOCK,
    sector: Sector = Sector.TECHNOLOGY,
    industry: str | None = "Software - Infrastructure",
) -> CompanyProfile:
    return CompanyProfile(
        asset_class=asset_class,
        sector=sector,
        industry=industry,
    )


def test_the_industry_the_provider_reported_chooses_the_playbook() -> None:
    playbook = ResearchStrategyFactory().playbook(profile())

    assert playbook.kind is PlaybookKind.SOFTWARE


def test_nothing_raises_for_a_business_this_platform_has_no_lens_for() -> None:
    """
    The factory used to accept one business model and raise for the rest.

    That was safe only because the profiler could not produce another one,
    and it would have failed the moment the classification became real.
    """

    playbook = ResearchStrategyFactory().playbook(
        profile(sector=Sector.CONSUMER, industry="Auto Manufacturers"),
    )

    assert playbook.kind is PlaybookKind.GENERAL_CORPORATE


@pytest.mark.parametrize(
    ("asset_class", "kind"),
    [
        (AssetClass.CRYPTO, PlaybookKind.DIGITAL_ASSET),
        (AssetClass.ETF, PlaybookKind.FUND),
    ],
)
def test_what_a_security_is_outranks_the_industry_it_is_filed_under(
    asset_class: AssetClass,
    kind: PlaybookKind,
) -> None:
    """A token filed under financial services is still a token."""

    playbook = ResearchStrategyFactory().playbook(
        profile(
            asset_class=asset_class,
            sector=Sector.FINANCIALS,
            industry="Banks - Diversified",
        ),
    )

    assert playbook.kind is kind


def test_the_strategy_runs_exactly_what_its_playbook_asks_for() -> None:
    factory = ResearchStrategyFactory()

    bank = profile(sector=Sector.FINANCIALS, industry="Banks - Regional")

    assert factory.create(bank).create_plan().analyst_keys == (
        factory.playbook(bank).analysts
    )
