"""A record of what the market actually read, observation by observation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.application.services.market_service import MarketService
from app.domain.asset_class import AssetClass
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.infrastructure.evidence.versioned_snapshot_store import (
    SnapshotReference,
    StoredSnapshot,
    VersionedSnapshotStore,
)

JsonObject = dict[str, Any]


class MarketSnapshotArchive:
    """
    Keep every market observation, so the platform can say what moved.

    Quotes were fetched, cached for fifteen minutes and discarded. Nothing
    in the repository held two market readings at once, so no question
    about the market beginning "since" could be answered at all — the
    change feed could only report decisions, because decisions were the
    only thing anything wrote down.

    This is the same archive the eToro responses go to, not a second one.
    `VersionedSnapshotStore` already stores dated, immutable, hashed
    captures; the only thing it lacked was a way to read them back.

    **Facts are stored; the classification is not.** A snapshot's mood,
    volatility band and summary are derived from its quotes and its VIX
    reading, so writing them down would be storing a conclusion — and a
    conclusion reached under thresholds that may since have changed. The
    figures are recorded and the classification is derived again on the way
    out, by the one service that classifies markets anywhere.
    """

    #: Where these captures live under the archive root.
    #:
    #: The store's three path segments namespace a capture. For a broker
    #: they name the broker, its environment and the endpoint; there is no
    #: broker behind a market observation, so they name the source family
    #: instead. Market readings are public and not per account, which is
    #: what "public" records here.
    BROKER = "market"
    ENVIRONMENT = "public"
    ENDPOINT = "snapshot"

    def __init__(
        self,
        store: VersionedSnapshotStore | None = None,
        market_service: MarketService | None = None,
    ) -> None:
        self._store = store or VersionedSnapshotStore()
        self._market_service = market_service or MarketService()

    def record(
        self,
        snapshot: MarketSnapshot,
    ) -> SnapshotReference | None:
        """
        Write this observation down, unless it is one already recorded.

        A quote served from the fifteen-minute cache carries the time the
        price was actually taken, so a snapshot whose payload is identical
        to the last recorded one contains nothing that was newly observed.
        Recording it again would fill the series with rows that look like
        readings and are replays of one. Nothing new observed returns
        nothing recorded.
        """

        payload = self._encode(snapshot)

        latest = self._store.recent(
            broker=self.BROKER,
            environment=self.ENVIRONMENT,
            endpoint=self.ENDPOINT,
            limit=1,
        )

        if latest and latest[0].reference.content_hash == self._hash(payload):
            return None

        return self._store.save(
            broker=self.BROKER,
            environment=self.ENVIRONMENT,
            endpoint=self.ENDPOINT,
            payload=payload,
            captured_at=snapshot.timestamp,
        )

    def recent(
        self,
        limit: int = 2,
    ) -> tuple[MarketSnapshot, ...]:
        """
        The most recently recorded observations, newest first.

        Fewer than asked for is a complete answer: a fresh clone has no
        market history, and two readings are needed before anything can be
        said to have changed.
        """

        return tuple(
            snapshot
            for snapshot in (
                self._restore(stored)
                for stored in self._store.recent(
                    broker=self.BROKER,
                    environment=self.ENVIRONMENT,
                    endpoint=self.ENDPOINT,
                    limit=limit,
                )
            )
            if snapshot is not None
        )

    def _hash(self, payload: JsonObject) -> str:
        return self._store.content_hash(payload)

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    @classmethod
    def _encode(
        cls,
        snapshot: MarketSnapshot,
    ) -> JsonObject:
        """The measured facts of one observation, and nothing derived."""

        return {
            "schema_version": 1,
            "vix": snapshot.vix,
            "quotes": [cls._encode_quote(quote) for quote in snapshot.quotes],
            "sentiment": (
                cls._encode_sentiment(snapshot.sentiment)
                if snapshot.sentiment is not None
                else None
            ),
        }

    @staticmethod
    def _encode_quote(
        quote: MarketQuote,
    ) -> JsonObject:
        return {
            "symbol": quote.symbol,
            "name": quote.name,
            "price": quote.price,
            "change_percent": quote.change_percent,
            "currency": quote.currency,
            "realized_volatility": quote.realized_volatility,
            "max_drawdown": quote.max_drawdown,
            # A measurement of the observed window, kept with the other two.
            # It is stored, not derived on the way out, because the year of
            # history it was taken from is not in the archive to derive it
            # from again.
            "market_sensitivity": MarketSnapshotArchive._encode_sensitivity(
                quote.market_sensitivity
            ),
            # The reading travels into the archive with the price. A
            # recorded quote that could not say when its price was taken
            # would date itself by the moment it was filed, which is the
            # substitution `Provenance` exists to stop.
            "reading": MarketSnapshotArchive._encode_reading(quote.reading),
        }

    @staticmethod
    def _encode_sensitivity(
        sensitivity: MarketSensitivity | None,
    ) -> JsonObject | None:
        if sensitivity is None:
            return None

        return {
            "beta": sensitivity.beta,
            "correlation": sensitivity.correlation,
            "observations": sensitivity.observations,
            "benchmark": sensitivity.benchmark,
        }

    @staticmethod
    def _encode_sentiment(
        sentiment: SentimentSnapshot,
    ) -> JsonObject:
        return {
            "score": sentiment.score,
            "label": sentiment.label,
            # Never dropped. A reading whose subject is lost is a mood with
            # no market attached, and the next reader will attach one.
            "subject": sentiment.subject.value,
            "reading": MarketSnapshotArchive._encode_reading(sentiment.reading),
        }

    @staticmethod
    def _encode_reading(
        reading: Provenance | None,
    ) -> JsonObject | None:
        if reading is None:
            return None

        return {
            "source": reading.source,
            "observed_at": reading.observed_at.isoformat(),
            "last_known": reading.last_known,
        }

    # ------------------------------------------------------------------
    # Decoding
    # ------------------------------------------------------------------

    def _restore(
        self,
        stored: StoredSnapshot,
    ) -> MarketSnapshot | None:
        """
        Rebuild one observation, classifying it as it is read.

        A capture this cannot read is skipped rather than raised on, and a
        capture with no usable quote is not a market reading at all.
        """

        payload = stored.payload

        if not isinstance(payload, dict):
            return None

        raw_quotes = payload.get("quotes")

        quotes = (
            tuple(
                quote
                for quote in (
                    self._restore_quote(item)
                    for item in raw_quotes
                    if isinstance(item, dict)
                )
                if quote is not None
            )
            if isinstance(raw_quotes, list)
            else ()
        )

        if not quotes:
            return None

        vix = payload.get("vix")

        return self._market_service.build_snapshot(
            quotes=quotes,
            vix=float(vix) if isinstance(vix, (int, float)) else None,
            # When the observation was assembled, taken from the capture
            # itself rather than from the moment it is being read.
            timestamp=stored.reference.captured_at,
            sentiment=self._restore_sentiment(payload.get("sentiment")),
        )

    @classmethod
    def _restore_quote(
        cls,
        value: JsonObject,
    ) -> MarketQuote | None:
        symbol = value.get("symbol")
        price = value.get("price")

        if not isinstance(symbol, str) or not isinstance(price, (int, float)):
            return None

        def ratio(field: str) -> float | None:
            raw = value.get(field)

            return float(raw) if isinstance(raw, (int, float)) else None

        change = value.get("change_percent")

        return MarketQuote(
            symbol=symbol,
            name=str(value.get("name", symbol)),
            price=float(price),
            change_percent=float(change) if isinstance(change, (int, float)) else 0.0,
            currency=str(value.get("currency", "USD")),
            realized_volatility=ratio("realized_volatility"),
            max_drawdown=ratio("max_drawdown"),
            market_sensitivity=cls._restore_sensitivity(
                value.get("market_sensitivity")
            ),
            reading=cls._restore_reading(value.get("reading")),
        )

    @staticmethod
    def _restore_sensitivity(
        value: object,
    ) -> MarketSensitivity | None:
        if not isinstance(value, dict):
            return None

        beta = value.get("beta")
        correlation = value.get("correlation")
        observations = value.get("observations")
        benchmark = value.get("benchmark")

        if not isinstance(beta, (int, float)) or not isinstance(
            correlation, (int, float)
        ):
            return None

        if not isinstance(observations, int) or not isinstance(benchmark, str):
            return None

        return MarketSensitivity(
            beta=float(beta),
            correlation=float(correlation),
            observations=observations,
            benchmark=benchmark,
        )

    @classmethod
    def _restore_sentiment(
        cls,
        value: object,
    ) -> SentimentSnapshot | None:
        if not isinstance(value, dict):
            return None

        score = value.get("score")
        label = value.get("label")
        subject = value.get("subject")
        reading = cls._restore_reading(value.get("reading"))

        if not isinstance(score, int) or not isinstance(label, str):
            return None

        # A reading that cannot name its subject or its source is not
        # restored. Both are what stop a crypto index being read as the
        # mood of everything the investor holds.
        if not isinstance(subject, str) or reading is None:
            return None

        try:
            asset_class = AssetClass(subject)
        except ValueError:
            return None

        return SentimentSnapshot(
            score=score,
            label=label,
            subject=asset_class,
            reading=reading,
        )

    @staticmethod
    def _restore_reading(
        value: object,
    ) -> Provenance | None:
        if not isinstance(value, dict):
            return None

        source = value.get("source")
        observed_at = value.get("observed_at")

        if not isinstance(source, str) or not isinstance(observed_at, str):
            return None

        try:
            moment = datetime.fromisoformat(observed_at)
        except ValueError:
            return None

        return Provenance(
            source=source,
            observed_at=moment,
            last_known=value.get("last_known") is True,
        )
