"""Choose the playbook a security is evaluated with, from what is known."""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.company_profile import CompanyProfile, Sector
from app.domain.playbook import PLAYBOOKS, InvestmentPlaybook, PlaybookKind


class PlaybookSelector:
    """
    Read the security's kind off its asset class and reported industry.

    Deterministic and evidence-driven, in that order of importance. Every
    rule below is a substring of the industry string the data provider
    actually returns, so the classification can be checked against the
    same field the reader can see. Nothing is inferred from the name of
    the company, its size, or how it has been performing.

    Where the industry is reported but this platform has no specialised
    reading for it, the answer is the general corporate playbook — stated
    as the default rather than dressed as a choice. Where no industry is
    reported at all, the answer is that the security is not classified,
    which is a different thing and is kept apart from it.
    """

    #: Industry substrings that identify a playbook, most specific first.
    #:
    #: Matched against the provider's own industry string, lower-cased.
    #: Order matters where one substring contains another.
    _BY_INDUSTRY: tuple[tuple[str, PlaybookKind], ...] = (
        ("semiconductor", PlaybookKind.SEMICONDUCTOR),
        ("software", PlaybookKind.SOFTWARE),
        ("information technology services", PlaybookKind.SOFTWARE),
        ("internet content", PlaybookKind.PLATFORM),
        ("internet retail", PlaybookKind.PLATFORM),
        ("aerospace", PlaybookKind.AEROSPACE_DEFENCE),
        ("banks", PlaybookKind.BANK),
        ("bank", PlaybookKind.BANK),
        ("insurance", PlaybookKind.INSURANCE),
        ("asset management", PlaybookKind.ASSET_MANAGER),
        ("capital markets", PlaybookKind.ASSET_MANAGER),
        ("reit", PlaybookKind.REIT),
        ("real estate", PlaybookKind.REIT),
        ("utilities", PlaybookKind.UTILITIES),
        ("oil & gas", PlaybookKind.ENERGY),
        ("coal", PlaybookKind.ENERGY),
        ("uranium", PlaybookKind.MINING),
        ("gold", PlaybookKind.MINING),
        ("silver", PlaybookKind.MINING),
        ("copper", PlaybookKind.MINING),
        ("industrial metals", PlaybookKind.MINING),
        ("other precious metals", PlaybookKind.MINING),
        ("drug manufacturers", PlaybookKind.PHARMA),
        ("biotechnology", PlaybookKind.PHARMA),
        ("pharmaceutical", PlaybookKind.PHARMA),
    )

    #: Sectors whose every industry reads the same way, used only where
    #: the industry string itself matched nothing above.
    _BY_SECTOR: dict[Sector, PlaybookKind] = {
        Sector.UTILITIES: PlaybookKind.UTILITIES,
        Sector.ENERGY: PlaybookKind.ENERGY,
        Sector.REAL_ESTATE: PlaybookKind.REIT,
    }

    def select(
        self,
        profile: CompanyProfile,
    ) -> InvestmentPlaybook:
        return PLAYBOOKS[self._kind(profile)]

    def _kind(
        self,
        profile: CompanyProfile,
    ) -> PlaybookKind:
        # What the security *is* outranks what industry it is filed
        # under: a token filed under "financial services" is still a
        # token, and asking it about margins would be the error this
        # whole layer exists to prevent.
        if profile.asset_class is AssetClass.CRYPTO:
            return PlaybookKind.DIGITAL_ASSET

        if profile.asset_class is AssetClass.ETF:
            return PlaybookKind.FUND

        industry = (profile.industry or "").strip().casefold()

        for fragment, kind in self._BY_INDUSTRY:
            if fragment in industry:
                return kind

        if profile.sector in self._BY_SECTOR:
            return self._BY_SECTOR[profile.sector]

        # An industry that was reported and simply has no specialised
        # reading here is a company read the ordinary way. One that was
        # never reported was not classified at all, and saying so is the
        # difference between a default and a decision.
        if industry or profile.sector is not Sector.OTHER:
            return PlaybookKind.GENERAL_CORPORATE

        return PlaybookKind.UNCLASSIFIED
