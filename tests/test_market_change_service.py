"""What the market did between two recorded observations."""

from datetime import UTC, datetime, timedelta

from app.application.change_feed.market_change_service import (
    MarketChangeService,
)
from app.application.services.market_service import MarketService
from app.domain.asset_class import AssetClass
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeSeverity,
)
from app.domain.holding_exposure import HoldingExposure
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot

BEFORE = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
AFTER = BEFORE + timedelta(days=1)


def observation(
    *,
    change_percent: float = 0.0,
    vix: float | None = 16.0,
    timestamp: datetime = BEFORE,
    sentiment: SentimentSnapshot | None = None,
) -> MarketSnapshot:
    return MarketService().build_snapshot(
        quotes=(
            MarketQuote(
                symbol="SPY",
                name="S&P 500 ETF",
                price=600.0,
                change_percent=change_percent,
                reading=Provenance(source="Yahoo Finance", observed_at=timestamp),
            ),
        ),
        vix=vix,
        timestamp=timestamp,
        sentiment=sentiment,
    )


def crypto(score: int, label: str) -> SentimentSnapshot:
    return SentimentSnapshot(
        score=score,
        label=label,
        subject=AssetClass.CRYPTO,
        reading=Provenance(source="Alternative.me", observed_at=AFTER),
    )


def equities(score: int, label: str) -> SentimentSnapshot:
    return SentimentSnapshot(
        score=score,
        label=label,
        subject=AssetClass.STOCK,
        reading=Provenance(source="Some equity index", observed_at=AFTER),
    )


def test_an_unmoved_market_reports_nothing() -> None:
    """A quiet feed means nothing moved, not that nothing was looked at."""

    service = MarketChangeService()

    assert service.changes(observation(), observation(timestamp=AFTER)) == ()


def test_a_changed_mood_is_reported() -> None:
    events = MarketChangeService().changes(
        observation(change_percent=1.5),
        observation(change_percent=-1.5, timestamp=AFTER),
    )

    assert len(events) == 1

    event = events[0]

    assert event.title == "Market mood moved from positive to negative"
    assert event.category is ChangeCategory.MARKET
    assert event.timestamp == AFTER

    # Two rungs apart on its own ladder — a measured distance, not an
    # opinion about importance.
    assert event.severity is ChangeSeverity.MEDIUM


def test_a_mood_moving_one_rung_is_the_lowest_severity() -> None:
    events = MarketChangeService().changes(
        observation(change_percent=0.0),
        observation(change_percent=1.5, timestamp=AFTER),
    )

    assert events[0].severity is ChangeSeverity.LOW


def test_a_volatility_band_change_states_both_vix_figures() -> None:
    events = MarketChangeService().changes(
        observation(vix=12.0),
        observation(vix=31.0, timestamp=AFTER),
    )

    assert len(events) == 1

    event = events[0]

    assert event.title == "Volatility moved from low to high"
    assert event.description == "The VIX read 12.00, and now reads 31.00."
    assert event.category is ChangeCategory.MACRO
    assert event.severity is ChangeSeverity.MEDIUM


def test_a_vix_that_moved_inside_its_band_is_not_an_event() -> None:
    """
    Reporting it would need a threshold for which move matters.

    Nothing here measures that, and a threshold picked to look sensible
    would be an invented figure on an investment surface. The readings are
    recorded, so the measure can be built later on evidence.
    """

    assert (
        MarketChangeService().changes(
            observation(vix=15.5),
            observation(vix=24.5, timestamp=AFTER),
        )
        == ()
    )


def test_a_vix_that_arrived_is_not_volatility_falling() -> None:
    """
    Moving out of "unknown" is a change in what could be seen.

    A VIX nobody could read is not a calm market, and reporting the
    reading's arrival as a movement would tell the investor volatility
    changed when only the platform's sight did.
    """

    assert (
        MarketChangeService().changes(
            observation(vix=None),
            observation(vix=16.0, timestamp=AFTER),
        )
        == ()
    )


def test_a_sentiment_label_change_is_reported_with_its_subject_named() -> None:
    events = MarketChangeService().changes(
        observation(sentiment=crypto(28, "Fear")),
        observation(sentiment=crypto(62, "Greed"), timestamp=AFTER),
    )

    assert len(events) == 1

    event = events[0]

    assert event.title == "Crypto sentiment moved from Fear to Greed"
    assert "Alternative.me read 28, and now reads 62" in event.description
    assert event.category is ChangeCategory.MARKET

    # 34 points of a 0-to-100 index: over a third of the published range.
    assert event.severity is ChangeSeverity.HIGH


def test_readings_of_different_asset_classes_are_not_one_change() -> None:
    """
    This is the whole reason a reading carries its subject.

    Crypto fear turning into equity greed is two indices, not a mood that
    moved, and the branch has already spent a commit on one index being
    read as another.
    """

    assert (
        MarketChangeService().changes(
            observation(sentiment=crypto(28, "Fear")),
            observation(sentiment=equities(62, "Greed"), timestamp=AFTER),
        )
        == ()
    )


def test_an_index_read_only_once_leaves_nothing_to_compare() -> None:
    service = MarketChangeService()

    assert (
        service.changes(
            observation(sentiment=None),
            observation(sentiment=crypto(28, "Fear"), timestamp=AFTER),
        )
        == ()
    )
    assert (
        service.changes(
            observation(sentiment=crypto(28, "Fear")),
            observation(sentiment=None, timestamp=AFTER),
        )
        == ()
    )


def test_several_things_moving_are_several_events() -> None:
    events = MarketChangeService().changes(
        observation(change_percent=1.5, vix=12.0, sentiment=crypto(28, "Fear")),
        observation(
            change_percent=-1.5,
            vix=31.0,
            sentiment=crypto(62, "Greed"),
            timestamp=AFTER,
        ),
    )

    assert [event.category for event in events] == [
        ChangeCategory.MARKET,
        ChangeCategory.MACRO,
        ChangeCategory.MARKET,
    ]


def test_a_market_move_asks_the_investor_for_nothing() -> None:
    """
    The market moving is not an instruction.

    `action_required` marks a decision the investor is being asked to make.
    A mood that moved is context, and flagging it would put the platform in
    the business of prompting trades on a market reading.
    """

    events = MarketChangeService().changes(
        observation(change_percent=1.5),
        observation(change_percent=-1.5, timestamp=AFTER),
    )

    assert all(not event.action_required for event in events)


# ------------------------------------------------------------------
# Individual instrument moves, judged against the instrument's own scale.
# ------------------------------------------------------------------

#: An annualised volatility whose daily standard deviation is exactly 1%, so a
#: change of N% is a move of N of the instrument's own daily sigmas.
DAILY_SIGMA_1PCT = 0.01 * (252**0.5)


def moving(
    change_percent: float,
    *,
    realized_volatility: float | None = DAILY_SIGMA_1PCT,
    timestamp: datetime = BEFORE,
) -> MarketSnapshot:
    return MarketService().build_snapshot(
        quotes=(
            MarketQuote(
                symbol="WTI",
                name="WTI Crude Oil",
                price=70.0,
                change_percent=change_percent,
                realized_volatility=realized_volatility,
                reading=Provenance(source="Yahoo Finance", observed_at=timestamp),
            ),
        ),
        vix=16.0,
        timestamp=timestamp,
    )


def instrument_events(events):
    return [event for event in events if event.title.startswith("WTI")]


def test_a_move_large_for_the_instrument_is_reported() -> None:
    events = MarketChangeService().changes(
        moving(0.5),
        moving(3.5, timestamp=AFTER),
    )

    named = instrument_events(events)

    assert len(named) == 1
    assert named[0].title == "WTI rose 3.5%"
    assert "3.5×" in named[0].description
    assert "typical daily move of 1.0%" in named[0].description
    assert named[0].category is ChangeCategory.MARKET
    assert named[0].severity is ChangeSeverity.MEDIUM


def test_a_small_move_for_the_instrument_is_not_reported() -> None:
    """A day-and-a-half sigma is inside what this instrument usually does."""

    events = MarketChangeService().changes(moving(0.0), moving(1.5, timestamp=AFTER))

    assert instrument_events(events) == []


def test_a_move_already_large_last_reading_is_not_named_again() -> None:
    """The same move is not news twice; only crossing the threshold is."""

    events = MarketChangeService().changes(
        moving(3.5),
        moving(2.5, timestamp=AFTER),
    )

    assert instrument_events(events) == []


def test_the_direction_of_the_move_is_named() -> None:
    events = MarketChangeService().changes(moving(0.0), moving(-3.5, timestamp=AFTER))

    named = instrument_events(events)

    assert named[0].title == "WTI fell 3.5%"


def test_severity_scales_with_how_far_past_its_own_scale_it_moved() -> None:
    low = instrument_events(
        MarketChangeService().changes(moving(0.0), moving(2.5, timestamp=AFTER))
    )
    high = instrument_events(
        MarketChangeService().changes(moving(0.0), moving(4.5, timestamp=AFTER))
    )

    assert low[0].severity is ChangeSeverity.LOW
    assert high[0].severity is ChangeSeverity.HIGH


def test_a_move_without_a_measured_typical_is_not_reported() -> None:
    """No year of history, no scale to judge the day against."""

    events = MarketChangeService().changes(
        moving(0.0, realized_volatility=None),
        moving(6.0, realized_volatility=None, timestamp=AFTER),
    )

    assert instrument_events(events) == []


# ------------------------------------------------------------------
# Which holdings a benchmark move touches, on measured exposure alone.
# ------------------------------------------------------------------


def benchmark_moving(
    change_percent: float,
    *,
    timestamp: datetime = BEFORE,
) -> MarketSnapshot:
    return MarketService().build_snapshot(
        quotes=(
            MarketQuote(
                symbol="SPY",
                name="S&P 500 ETF",
                price=600.0,
                change_percent=change_percent,
                realized_volatility=DAILY_SIGMA_1PCT,
                reading=Provenance(source="Yahoo Finance", observed_at=timestamp),
            ),
        ),
        vix=16.0,
        timestamp=timestamp,
    )


def exposure(
    symbol: str,
    *,
    weight: float | None = None,
    beta: float | None = None,
    correlation: float = 0.80,
    benchmark: str = "SPY",
) -> HoldingExposure:
    return HoldingExposure(
        symbol=symbol,
        weight_pct=weight,
        sensitivity=(
            MarketSensitivity(
                beta=beta,
                correlation=correlation,
                observations=250,
                benchmark=benchmark,
            )
            if beta is not None
            else None
        ),
    )


def benchmark_events(events):
    return [event for event in events if event.title.startswith("SPY")]


def touched(exposures: tuple[HoldingExposure, ...]) -> str:
    events = benchmark_events(
        MarketChangeService().changes(
            benchmark_moving(0.0),
            benchmark_moving(3.5, timestamp=AFTER),
            exposures,
        )
    )

    assert len(events) == 1

    return events[0].description


def test_a_benchmark_move_names_the_holdings_it_touches() -> None:
    description = touched(
        (
            exposure("NVDA", weight=12.3, beta=1.84, correlation=0.78),
            exposure("AAPL", weight=8.1, beta=1.12, correlation=0.65),
        )
    )

    assert (
        "Among the holdings, NVDA (12.3% of the account) moves 1.84× "
        "with it (correlation +0.78) and AAPL (8.1% of the account) "
        "1.12× (+0.65)." in description
    )


def test_holdings_are_ordered_by_how_much_of_the_account_moves() -> None:
    """Weight × |beta| ranks them, because both factors were measured."""

    description = touched(
        (
            # 5% at 2.0× is a tenth of the account moving; 20% at 1.0× a
            # fifth. The larger measured movement is named first.
            exposure("SMALL", weight=5.0, beta=2.0),
            exposure("LARGE", weight=20.0, beta=1.0),
        )
    )

    assert description.index("LARGE") < description.index("SMALL")


def test_more_measured_holdings_than_named_are_counted() -> None:
    description = touched(
        tuple(exposure(f"HOLD{n}", weight=10.0, beta=1.0) for n in range(5))
    )

    assert "2 more holdings carry a measured sensitivity to it." in description


def test_unmeasured_holdings_are_counted_not_dropped() -> None:
    """Naming only the measured would read as "the rest are untouched"."""

    description = touched(
        (
            exposure("NVDA", weight=12.3, beta=1.84),
            exposure("UUUU"),
            exposure("TAO"),
        )
    )

    assert (
        "No sensitivity is measured for the other 2 holdings, so what "
        "this move means for them is not stated." in description
    )


def test_a_book_with_nothing_measured_gets_no_holdings_line() -> None:
    """
    With no sensitivity measured anywhere, even the benchmark is unnamed.

    Which instrument these holdings would move with is itself unmeasured —
    the "SPY is the benchmark" fact lives in the provider that regresses,
    not in the exposures — so saying "none moves with SPY" would borrow a
    fact this evidence does not carry. The event tells the market's own
    story alone.
    """

    description = touched((exposure("UUUU"), exposure("TAO")))

    assert "UUUU" not in description
    assert "TAO" not in description
    assert description.endswith("typical daily move of 1.0%.")


def test_no_holdings_context_leaves_the_event_as_it_was() -> None:
    """A caller without an account gets the market's own story alone."""

    description = touched(())

    assert description.endswith("typical daily move of 1.0%.")


def test_a_non_benchmark_move_says_nothing_about_holdings() -> None:
    """
    A beta to SPY says nothing about an oil move.

    The absence of a holdings line is the absence of a claim, not a claim
    of no effect — connecting the two would need a sensitivity to WTI that
    was never measured.
    """

    events = instrument_events(
        MarketChangeService().changes(
            moving(0.0),
            moving(3.5, timestamp=AFTER),
            (exposure("NVDA", weight=12.3, beta=1.84),),
        )
    )

    assert len(events) == 1
    assert "NVDA" not in events[0].description
    assert events[0].description.endswith("typical daily move of 1.0%.")


def test_a_holding_whose_weight_could_not_be_read_says_so() -> None:
    description = touched((exposure("NVDA", weight=None, beta=1.84),))

    assert "NVDA (share of account unmeasured)" in description
