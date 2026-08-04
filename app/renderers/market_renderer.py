from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.domain.change_feed.change_event import ChangeEvent
from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import NO_EQUITY_SENTIMENT, SentimentSnapshot


class MarketRenderer:
    @staticmethod
    def render(
        snapshot: MarketSnapshot,
        changes: Sequence[ChangeEvent] = (),
        previous_at: datetime | None = None,
    ) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print("Market Snapshot")
        print("────────────────────────────────")
        print()

        for quote in snapshot.quotes:
            arrow = "▲" if quote.change_percent >= 0 else "▼"

            print(
                f"{quote.symbol:<6}"
                f"${quote.price:>10,.2f}   "
                f"{arrow} {quote.change_percent:+.2f}%"
            )

        print()
        print(f"Market Mood : {snapshot.market_mood.title()}")
        print(f"Volatility  : {snapshot.volatility.title()}")
        print()
        print(snapshot.summary)
        print()

        MarketRenderer._render_sentiment(snapshot.sentiment)
        MarketRenderer._render_changes(changes, previous_at)

    @staticmethod
    def _render_sentiment(
        sentiment: SentimentSnapshot | None,
    ) -> None:
        """
        The one sentiment index the platform reads, and what it does not.

        The reading is labelled by the asset class it was taken of, never as
        "market sentiment", and the equity absence is stated beneath it every
        time — including the cycle the crypto index could not be read, when
        the score is gone but the gap it leaves for equities is not.
        """

        if sentiment is None:
            print("Crypto sentiment : not read")
        else:
            label = f"{sentiment.subject.value.capitalize()} sentiment"
            print(f"{label} : {sentiment.score} ({sentiment.label})")

        print(NO_EQUITY_SENTIMENT)
        print()

    @staticmethod
    def _render_changes(
        changes: Sequence[ChangeEvent],
        previous_at: datetime | None,
    ) -> None:
        """
        What moved since the previous recorded observation.

        Two observations are needed before anything can be said to have
        moved, so a first reading says so rather than comparing against a
        blank. A quiet feed on a later reading means the classification held,
        never that nothing was looked at — and only the classification is
        reported, because an individual instrument moving between any two
        reads is not yet a change this platform can measure.
        """

        print("Since the last reading")
        print("────────────────────────────────")

        if previous_at is None:
            print("First recorded observation — nothing to compare yet.")
            print()
            return

        if not changes:
            print(
                "Nothing in the market's classification moved since "
                f"{previous_at:%b %d, %H:%M} UTC."
            )
            print()
            return

        for change in changes:
            print(f"• {change.title}")
            print(f"  {change.description}")

        print()
