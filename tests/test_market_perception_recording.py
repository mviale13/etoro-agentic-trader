"""Perception keeps what it saw, so a later cycle can say what moved."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from app.application.brain.perception.market_perception import MarketPerception
from app.application.market.market_snapshot_archive import (
    MarketSnapshotArchive,
)
from app.domain.market_snapshot import MarketData, MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.infrastructure.evidence.versioned_snapshot_store import (
    VersionedSnapshotStore,
)

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


class MarketStub:
    def __init__(self, price: float = 600.0) -> None:
        self._price = price

    async def snapshot(self) -> MarketData:
        return MarketData(
            quotes=(
                MarketQuote(
                    symbol="SPY",
                    name="S&P 500 ETF",
                    price=self._price,
                    change_percent=1.2,
                    reading=Provenance(source="Yahoo Finance", observed_at=NOW),
                ),
            ),
            vix=16.0,
        )


class SentimentStub:
    async def snapshot(self) -> None:
        return None


class UnwritableArchive:
    def record(self, snapshot: MarketSnapshot) -> object:
        raise OSError("no space left on device")


def perceive(
    archive: object,
    price: float = 600.0,
) -> MarketSnapshot:
    return asyncio.run(
        MarketPerception(
            provider=MarketStub(price),
            sentiment_provider=SentimentStub(),
            archive=archive,  # type: ignore[arg-type]
        ).execute()
    )


def test_perceiving_the_market_records_what_it_read(tmp_path: Path) -> None:
    """
    Quotes were cached for fifteen minutes and discarded.

    Nothing in the repository held two market readings at once, so no
    question about the market beginning "since" could be answered.
    """

    archive = MarketSnapshotArchive(store=VersionedSnapshotStore(root=tmp_path))

    perceive(archive)

    recorded = archive.recent()

    assert len(recorded) == 1
    assert recorded[0].quotes[0].symbol == "SPY"
    assert recorded[0].quotes[0].price == 600.0
    assert recorded[0].vix == 16.0


def test_two_cycles_leave_a_series(tmp_path: Path) -> None:
    archive = MarketSnapshotArchive(store=VersionedSnapshotStore(root=tmp_path))

    perceive(archive, price=600.0)
    perceive(archive, price=610.0)

    assert [item.quotes[0].price for item in archive.recent()] == [610.0, 600.0]


def test_an_archive_that_cannot_be_written_costs_the_record_not_the_cycle(
    tmp_path: Path,
) -> None:
    """
    The investor asked what the market is doing.

    A full disk is not a reason to refuse to answer, and the failure shows
    as a gap in the series rather than as a fabricated entry.
    """

    market = perceive(UnwritableArchive())

    assert market.quotes
    assert market.quotes[0].price == 600.0
