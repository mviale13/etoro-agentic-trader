"""Recording what the market read, and reading it back."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.application.market.market_snapshot_archive import (
    MarketSnapshotArchive,
)
from app.application.services.market_service import MarketService
from app.domain.asset_class import AssetClass
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.infrastructure.evidence.versioned_snapshot_store import (
    VersionedSnapshotStore,
)

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def archive(tmp_path: Path) -> MarketSnapshotArchive:
    return MarketSnapshotArchive(store=VersionedSnapshotStore(root=tmp_path))


def quote(
    symbol: str = "SPY",
    price: float = 600.0,
    change_percent: float = 1.2,
    observed_at: datetime = NOW,
    last_known: bool = False,
) -> MarketQuote:
    return MarketQuote(
        symbol=symbol,
        name=f"{symbol} tracker",
        price=price,
        change_percent=change_percent,
        realized_volatility=0.18,
        max_drawdown=0.34,
        market_sensitivity=MarketSensitivity(
            beta=1.1,
            correlation=0.83,
            observations=240,
            benchmark="SPY",
        ),
        reading=Provenance(
            source="Yahoo Finance",
            observed_at=observed_at,
            last_known=last_known,
        ),
    )


def sentiment(
    score: int = 28,
    label: str = "Fear",
) -> SentimentSnapshot:
    return SentimentSnapshot(
        score=score,
        label=label,
        subject=AssetClass.CRYPTO,
        reading=Provenance(source="Alternative.me", observed_at=NOW),
    )


def snapshot(
    *,
    quotes: tuple[MarketQuote, ...] = (quote(),),
    vix: float | None = 16.0,
    timestamp: datetime = NOW,
    reading: SentimentSnapshot | None = None,
) -> MarketSnapshot:
    return MarketService().build_snapshot(
        quotes=quotes,
        vix=vix,
        timestamp=timestamp,
        sentiment=reading,
    )


def test_an_empty_archive_reports_no_history(tmp_path: Path) -> None:
    """A fresh clone has no market past, and says so rather than inventing one."""

    assert archive(tmp_path).recent() == ()


def test_an_observation_is_recorded_and_read_back(tmp_path: Path) -> None:
    store = archive(tmp_path)

    reference = store.record(snapshot(reading=sentiment()))

    assert reference is not None
    assert reference.path.exists()

    recorded = store.recent()

    assert len(recorded) == 1

    first = recorded[0]

    assert first.timestamp == NOW
    assert first.vix == 16.0
    assert len(first.quotes) == 1
    assert first.quotes[0].symbol == "SPY"
    assert first.quotes[0].price == 600.0
    assert first.quotes[0].realized_volatility == 0.18

    restored_sensitivity = first.quotes[0].market_sensitivity
    assert restored_sensitivity is not None
    assert restored_sensitivity.beta == 1.1
    assert restored_sensitivity.correlation == 0.83
    assert restored_sensitivity.benchmark == "SPY"
    assert first.sentiment is not None
    assert first.sentiment.score == 28
    assert first.sentiment.subject is AssetClass.CRYPTO


def test_a_recorded_quote_keeps_the_time_its_price_was_taken(
    tmp_path: Path,
) -> None:
    """
    The archive must not redate a reading to the moment it was filed.

    A price replayed from the fifteen-minute cache is filed later than it
    was taken, and a record that lost the difference would report a stale
    price as one observed at capture time.
    """

    taken = NOW - timedelta(minutes=14)

    store = archive(tmp_path)
    store.record(
        snapshot(
            quotes=(quote(observed_at=taken, last_known=True),),
            timestamp=NOW,
        )
    )

    restored = store.recent()[0]
    reading = restored.quotes[0].reading

    assert reading is not None
    assert reading.observed_at == taken
    assert reading.last_known is True

    # And the snapshot dates itself to its least reliable reading, not to
    # the moment it was captured.
    assert restored.reading is not None
    assert restored.reading.observed_at == taken


def test_the_classification_is_derived_on_the_way_out_not_stored(
    tmp_path: Path,
) -> None:
    """
    The Brain stores facts, never conclusions.

    Mood, volatility band and summary are derived from the quotes and the
    VIX. Storing them would file a conclusion, and file it under thresholds
    that may since have moved.
    """

    store = archive(tmp_path)
    reference = store.record(snapshot(vix=31.0))

    assert reference is not None

    written = json.loads(reference.path.read_text(encoding="utf-8"))["payload"]

    # `realized_volatility` is a measurement and stays; the band it would
    # be classified into is the conclusion, and is not written down.
    assert set(written) == {"schema_version", "vix", "quotes", "sentiment"}

    restored = store.recent()[0]

    assert restored.volatility == "high"
    assert restored.market_mood == "positive"
    assert restored.summary


def test_nothing_newly_observed_is_not_recorded_again(tmp_path: Path) -> None:
    """
    A cache replay is not an observation.

    Quotes are served from a fifteen-minute cache carrying the time the
    price was actually taken, so an identical payload means nothing new was
    seen. Filing it again would fill the series with rows that look like
    readings.
    """

    store = archive(tmp_path)

    assert store.record(snapshot()) is not None
    assert store.record(snapshot(timestamp=NOW + timedelta(minutes=5))) is None

    assert len(store.recent(limit=10)) == 1


def test_a_changed_price_is_a_new_observation(tmp_path: Path) -> None:
    store = archive(tmp_path)

    store.record(snapshot())
    store.record(
        snapshot(
            quotes=(quote(price=610.0, observed_at=NOW + timedelta(minutes=20)),),
            timestamp=NOW + timedelta(minutes=20),
        )
    )

    recorded = store.recent(limit=10)

    assert len(recorded) == 2

    # Newest first.
    assert recorded[0].quotes[0].price == 610.0
    assert recorded[1].quotes[0].price == 600.0


def test_history_is_read_newest_first_across_days(tmp_path: Path) -> None:
    store = archive(tmp_path)

    for day, price in ((1, 100.0), (2, 200.0), (3, 300.0)):
        moment = datetime(2026, 8, day, 12, 0, tzinfo=UTC)

        store.record(
            snapshot(
                quotes=(quote(price=price, observed_at=moment),),
                timestamp=moment,
            )
        )

    prices = [item.quotes[0].price for item in store.recent(limit=2)]

    assert prices == [300.0, 200.0]


def test_a_capture_with_no_usable_quote_is_not_a_market_reading(
    tmp_path: Path,
) -> None:
    """An unreadable entry is skipped, never guessed at."""

    store = VersionedSnapshotStore(root=tmp_path)
    store.save(
        broker=MarketSnapshotArchive.BROKER,
        environment=MarketSnapshotArchive.ENVIRONMENT,
        endpoint=MarketSnapshotArchive.ENDPOINT,
        payload={"schema_version": 1, "quotes": [], "vix": 16.0},
        captured_at=NOW,
    )

    assert MarketSnapshotArchive(store=store).recent() == ()


def test_a_sentiment_reading_that_lost_its_subject_is_not_restored(
    tmp_path: Path,
) -> None:
    """
    A mood with no market attached is not restored as one.

    The subject is what stops a crypto index being read as the mood of
    everything the investor holds, so a record missing it reports no
    sentiment rather than an unattributed one.
    """

    store = VersionedSnapshotStore(root=tmp_path)
    store.save(
        broker=MarketSnapshotArchive.BROKER,
        environment=MarketSnapshotArchive.ENVIRONMENT,
        endpoint=MarketSnapshotArchive.ENDPOINT,
        payload={
            "schema_version": 1,
            "vix": 16.0,
            "quotes": [
                {
                    "symbol": "SPY",
                    "name": "SPY tracker",
                    "price": 600.0,
                    "change_percent": 1.2,
                }
            ],
            "sentiment": {"score": 28, "label": "Fear"},
        },
        captured_at=NOW,
    )

    restored = MarketSnapshotArchive(store=store).recent()

    assert len(restored) == 1
    assert restored[0].sentiment is None
