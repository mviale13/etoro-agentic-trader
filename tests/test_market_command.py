"""`movrvest market` records what it read and says what moved since."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from app.application.brain.perception.market_perception import MarketPerception
from app.application.market.market_snapshot_archive import MarketSnapshotArchive
from app.commands import market
from app.domain.market_snapshot import MarketData, MarketQuote
from app.domain.provenance import Provenance
from app.infrastructure.evidence.versioned_snapshot_store import (
    VersionedSnapshotStore,
)


class MarketStub:
    """A provider that prices the market however the reading needs it to."""

    def __init__(self, change_percent: float, at: datetime) -> None:
        self._change_percent = change_percent
        self._at = at

    async def snapshot(self) -> MarketData:
        return MarketData(
            quotes=(
                MarketQuote(
                    symbol="SPY",
                    name="S&P 500 ETF",
                    price=600.0,
                    change_percent=self._change_percent,
                    reading=Provenance(source="Yahoo Finance", observed_at=self._at),
                ),
            ),
            vix=16.0,
        )


class SilentSentiment:
    async def snapshot(self) -> None:
        return None


def _archive(tmp_path: Path) -> MarketSnapshotArchive:
    return MarketSnapshotArchive(store=VersionedSnapshotStore(tmp_path))


def _run(archive: MarketSnapshotArchive, provider: MarketStub) -> int:
    perception = MarketPerception(
        provider=provider,
        sentiment_provider=SilentSentiment(),
        archive=archive,
    )

    return asyncio.run(market.run(perception=perception, archive=archive))


def test_first_reading_records_and_has_nothing_to_compare(tmp_path, capsys) -> None:
    archive = _archive(tmp_path)

    code = _run(
        archive,
        MarketStub(change_percent=1.2, at=datetime(2026, 8, 3, 7, 0, tzinfo=UTC)),
    )

    output = capsys.readouterr().out

    assert code == 0
    assert "First recorded observation" in output
    # The reading was filed, so the archive now holds exactly one.
    assert len(archive.recent(5)) == 1


def test_second_reading_reports_what_moved(tmp_path, capsys) -> None:
    archive = _archive(tmp_path)

    # A first, positive observation goes on the record.
    _run(
        archive,
        MarketStub(change_percent=1.5, at=datetime(2026, 8, 3, 7, 0, tzinfo=UTC)),
    )
    capsys.readouterr()

    # The market turns negative on the next genuine read.
    code = _run(
        archive,
        MarketStub(change_percent=-1.5, at=datetime(2026, 8, 4, 7, 0, tzinfo=UTC)),
    )

    output = capsys.readouterr().out

    assert code == 0
    assert "Market mood moved from positive to negative" in output
    assert len(archive.recent(5)) == 2
