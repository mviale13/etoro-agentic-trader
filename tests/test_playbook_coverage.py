"""The coverage report measures; it never acquires, and never blends."""

from types import SimpleNamespace

import pytest

import app.services.playbook_coverage_service as coverage_module
from app.domain.company_knowledge import RevenueModel
from app.domain.playbook import PLAYBOOKS, PlaybookKind
from app.domain.playbook_coverage import (
    Blocker,
    CoverageOrigin,
    CoverageOutcome,
)
from app.domain.portfolio_position import PortfolioPosition
from app.domain.watchlist_item import WatchlistItem
from app.services.playbook_coverage_service import PlaybookCoverageService
from tests.test_playbook_mapping import MFG, observations_of, segment

STOCK = 5
CRYPTO = 10


def instrument_id_of(symbol: str) -> int:
    """A deterministic, effectively unique id per test symbol."""

    return int.from_bytes(symbol.encode(), "big") % 1_000_000


def item(symbol: str, asset_type_id: int = STOCK) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id_of(symbol),
        symbol=symbol,
        name=symbol,
        asset_type_id=asset_type_id,
        asset_type_subcategory_id=0,
        exchange_id=0,
        rank=0,
        avatar_url=None,
    )


def position(
    symbol: str,
    asset_class: str | None = "stock",
    instrument_id: int = 0,
) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=100.0,
        market_value_usd=100.0,
        unrealized_pnl_usd=0.0,
        asset_class=asset_class,
        instrument_id=instrument_id,
    )


def grounded_observations() -> tuple:
    """Five agreeing readings of a pure manufacturer: Industrial."""

    same = (segment("Only", share=0.95, earns=MFG),)

    return observations_of(same, same, same, same, same)


def unexplained_observations() -> tuple:
    """META's live shape: measured, and no way of earning established."""

    same = (
        segment("Family of Apps", share=0.99),
        segment("Reality Labs", share=0.01, row=2),
    )

    return observations_of(same, same, same, same, same)


def unmapped_observations() -> tuple:
    """A quorate conclusion the corpus has not earned a playbook for."""

    same = (segment("Only", share=0.95, earns=(RevenueModel.SERVICES,)),)

    return observations_of(same, same, same, same, same)


def below_quorum_observations() -> tuple:
    same = (segment("Only", share=0.95, earns=MFG),)

    return observations_of(same, same)


class FakeStore:
    def __init__(self, observations: dict[str, tuple]) -> None:
        self._observations = observations

    def latest(self, symbol: str) -> tuple:
        return self._observations.get(symbol, ())


class FakeResolver:
    """Watchlists first, then the broker's catalog — like the real one."""

    def __init__(
        self,
        watched: tuple[WatchlistItem, ...] = (),
        catalog: tuple[WatchlistItem, ...] = (),
    ) -> None:
        self._watched = {entry.instrument_id: entry for entry in watched}
        self._catalog = {entry.instrument_id: entry for entry in catalog}

    async def items(self) -> dict[int, WatchlistItem]:
        return dict(self._watched)

    async def items_for(self, instrument_ids) -> dict[int, WatchlistItem]:
        known = dict(self._watched)

        for instrument_id in instrument_ids:
            if instrument_id not in known and instrument_id in self._catalog:
                known[instrument_id] = self._catalog[instrument_id]

        return known


class FakeAccount:
    def __init__(self, *positions: PortfolioPosition) -> None:
        self._positions = positions

    async def snapshot(self) -> SimpleNamespace:
        return SimpleNamespace(positions=self._positions)


class FakeFacts:
    async def build(self, item: WatchlistItem) -> object:
        return object()


class FailingFacts:
    async def build(self, item: WatchlistItem) -> object:
        raise RuntimeError("provider returned 401")


class FakeProfiler:
    def profile(self, facts: object) -> object:
        return object()


class FakeIndustry:
    def __init__(self, kind: PlaybookKind = PlaybookKind.PLATFORM) -> None:
        self._kind = kind

    def select(self, profile: object):
        return PLAYBOOKS[self._kind]


class NeverCalled:
    def __getattr__(self, name: str):
        raise AssertionError("this route must not run in this scenario")


def service(**overrides) -> PlaybookCoverageService:
    defaults = {
        "store": FakeStore({}),
        "resolver": FakeResolver(),
        "account": FakeAccount(),
        "facts": FakeFacts(),
        "profiler": FakeProfiler(),
        "industry": FakeIndustry(),
    }
    defaults.update(overrides)

    return PlaybookCoverageService(**defaults)


# ── the measurement is read-only ────────────────────────────────────


def test_the_service_cannot_acquire() -> None:
    """The module must not even import the acquiring service: the
    knowledge store is consulted as it stands, and nothing else."""

    assert not hasattr(coverage_module, "CompanyKnowledgeService")


@pytest.mark.anyio
async def test_a_grounded_security_never_consults_the_industry_route() -> None:
    report = await service(
        store=FakeStore({"NVDA": grounded_observations()}),
        resolver=FakeResolver(watched=(item("NVDA"),)),
        facts=NeverCalled(),
        profiler=NeverCalled(),
        industry=NeverCalled(),
    ).report()

    (security,) = report.securities

    assert security.outcome is CoverageOutcome.GROUNDED
    assert security.playbook is PlaybookKind.INDUSTRIAL
    assert security.blocker is None
    assert security.blocking_claim is None
    assert security.width == 5
    assert security.quorate
    assert security.decided
    assert security.mapped


# ── one blocker each ────────────────────────────────────────────────


@pytest.mark.anyio
async def test_a_quorate_unexplained_company_is_blocked_on_mechanisms() -> None:
    """The blocking claim is the single cheapest unlock: the largest
    segment whose way of earning is not established."""

    report = await service(
        store=FakeStore({"META": unexplained_observations()}),
        resolver=FakeResolver(watched=(item("META"),)),
    ).report()

    (security,) = report.securities

    assert security.blocker is Blocker.NO_REVENUE_MECHANISMS
    assert security.blocking_claim == (
        "a way of earning established for 'Family of Apps' (99% of revenue)"
    )
    assert security.outcome is CoverageOutcome.FALLBACK
    assert security.playbook is PlaybookKind.PLATFORM
    assert not security.decided
    assert not security.mapped


@pytest.mark.anyio
async def test_below_quorum_blocks_with_the_missing_count() -> None:
    report = await service(
        store=FakeStore({"ASML": below_quorum_observations()}),
        resolver=FakeResolver(watched=(item("ASML"),)),
    ).report()

    (security,) = report.securities

    assert security.width == 2
    assert not security.quorate
    assert security.understanding
    assert security.blocker is Blocker.BELOW_QUORUM
    assert security.blocking_claim == "3 more observation(s) of the current filing"

    # A width-2 Manufacturer is decided and mapped — investor-visible
    # understanding the funnel counts — while authority still waits on
    # the quorum, which is exactly what `quorate` beside it says.
    assert security.decided
    assert security.mapped


@pytest.mark.anyio
async def test_an_unmapped_conclusion_blocks_on_the_missing_rule() -> None:
    report = await service(
        store=FakeStore({"ACN": unmapped_observations()}),
        resolver=FakeResolver(watched=(item("ACN"),)),
    ).report()

    (security,) = report.securities

    assert security.blocker is Blocker.NO_MAPPING
    assert "'Service business'" in (security.blocking_claim or "")
    assert security.decided
    assert not security.mapped


@pytest.mark.anyio
async def test_an_unread_equity_and_a_token_carry_different_blockers() -> None:
    """A filing nobody read and a filing that cannot exist are
    different absences, and the report keeps them apart."""

    report = await service(
        resolver=FakeResolver(
            watched=(item("MSFT"), item("BTC", asset_type_id=CRYPTO)),
        ),
    ).report()

    by_symbol = {security.symbol: security for security in report.securities}

    assert by_symbol["MSFT"].blocker is Blocker.NOT_READ
    assert by_symbol["BTC"].blocker is Blocker.NO_PRIMARY_SOURCE
    assert "publishes no annual report" in (by_symbol["BTC"].blocking_claim or "")


# ── identity resolution ─────────────────────────────────────────────


@pytest.mark.anyio
async def test_an_unnamed_holding_enters_the_report_as_unresolved() -> None:
    """A holding neither the watchlists nor the catalog can name must
    not vanish from a measurement of portfolio coverage — it enters
    under its placeholder with identity as its blocker."""

    report = await service(
        account=FakeAccount(position("", asset_class=None, instrument_id=777)),
    ).report()

    (security,) = report.securities

    assert security.symbol == "#777"
    assert security.origin is CoverageOrigin.PORTFOLIO
    assert security.blocker is Blocker.IDENTITY_UNRESOLVED
    assert security.blocking_claim == "a ticker symbol for broker instrument 777"
    assert security.outcome is CoverageOutcome.UNCLASSIFIED
    assert not security.is_company


@pytest.mark.anyio
async def test_a_holding_named_by_the_catalog_is_portfolio_not_both() -> None:
    """The broker's catalog resolves the identity; that does not make
    the security watched."""

    jpm = item("JPM")

    report = await service(
        resolver=FakeResolver(catalog=(jpm,)),
        account=FakeAccount(
            position("", asset_class="stock", instrument_id=jpm.instrument_id)
        ),
    ).report()

    (security,) = report.securities

    assert security.symbol == "JPM"
    assert security.origin is CoverageOrigin.PORTFOLIO
    assert security.blocker is Blocker.NOT_READ
    assert security.outcome is CoverageOutcome.FALLBACK


@pytest.mark.anyio
async def test_a_security_held_and_watched_appears_once_as_both() -> None:
    report = await service(
        resolver=FakeResolver(watched=(item("MSFT"),)),
        account=FakeAccount(position("MSFT")),
    ).report()

    (security,) = report.securities

    assert security.origin is CoverageOrigin.BOTH


@pytest.mark.anyio
async def test_a_holding_off_every_source_is_unclassified_with_a_note() -> None:
    report = await service(
        account=FakeAccount(position("JPM")),
    ).report()

    (security,) = report.securities

    assert security.origin is CoverageOrigin.PORTFOLIO
    assert security.outcome is CoverageOutcome.UNCLASSIFIED
    assert security.playbook is PlaybookKind.UNCLASSIFIED
    assert security.note is not None
    assert "no watchlist item" in security.note


@pytest.mark.anyio
async def test_a_provider_error_becomes_a_note_not_an_invented_outcome() -> None:
    report = await service(
        resolver=FakeResolver(watched=(item("MSFT"),)),
        facts=FailingFacts(),
    ).report()

    (security,) = report.securities

    assert security.outcome is CoverageOutcome.UNCLASSIFIED
    assert "could not be consulted" in (security.note or "")
    assert "provider returned 401" in (security.note or "")


# ── the arithmetic ──────────────────────────────────────────────────


@pytest.mark.anyio
async def test_the_distribution_counts_every_blocker_most_common_first() -> None:
    report = await service(
        store=FakeStore(
            {
                "NVDA": grounded_observations(),
                "META": unexplained_observations(),
                "ASML": below_quorum_observations(),
                "MSFT": (),
                "GOOG": (),
            }
        ),
        resolver=FakeResolver(
            watched=(
                item("NVDA"),
                item("META"),
                item("ASML"),
                item("MSFT"),
                item("GOOG"),
            ),
        ),
    ).report()

    assert report.total == 5
    assert len(report.grounded) == 1
    assert report.quorate == 2
    assert report.below_quorum == 1
    assert report.unread == 2

    assert report.blocker_distribution == (
        (Blocker.NOT_READ, 2),
        (Blocker.BELOW_QUORUM, 1),
        (Blocker.NO_REVENUE_MECHANISMS, 1),
    )

    assert report.grounded_kinds == ((PlaybookKind.INDUSTRIAL, 1),)


@pytest.mark.anyio
async def test_the_funnel_counts_investor_visible_understanding() -> None:
    """The KPI: portfolio first, each row strictly narrower than the
    one above, out-of-scope and unresolved counted beside — never
    inside — the companies."""

    report = await service(
        store=FakeStore(
            {
                "NVDA": grounded_observations(),
                "META": unexplained_observations(),
                "ASML": below_quorum_observations(),
                "MSFT": (),
            }
        ),
        resolver=FakeResolver(
            watched=(
                item("NVDA"),
                item("META"),
                item("ASML"),
                item("MSFT"),
                item("BTC", asset_type_id=CRYPTO),
            ),
        ),
        account=FakeAccount(
            position("NVDA"),
            position("", asset_class=None, instrument_id=777),
        ),
    ).report()

    portfolio = report.funnel(CoverageOrigin.PORTFOLIO)

    assert portfolio.companies == 1
    assert portfolio.read == 1
    assert portfolio.decided == 1
    assert portfolio.mapped == 1
    assert portfolio.quorate == 1
    assert portfolio.unresolved == 1
    assert portfolio.out_of_scope == 0

    watchlist = report.funnel(CoverageOrigin.WATCHLIST)

    assert watchlist.companies == 4
    assert watchlist.read == 3
    assert watchlist.decided == 2
    assert watchlist.mapped == 2
    assert watchlist.quorate == 1
    assert watchlist.unresolved == 0
    assert watchlist.out_of_scope == 1

    book = report.funnel()

    assert book.companies == 4
    assert book.unresolved == 1
    assert book.out_of_scope == 1
