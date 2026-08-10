"""The crypto Fear & Greed index, read from the service it is credited to."""

from __future__ import annotations

import asyncio
import json
import urllib.request
from datetime import UTC, datetime, timedelta

from app.domain.asset_class import AssetClass
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.infrastructure.cache.json_cache import JsonCache


class CryptoFearGreedProvider:
    """
    Read Alternative.me's crypto Fear & Greed index.

    This returned a hardcoded 72, labelled "Greed", and printed
    "Source: Alternative.me" underneath it. The service is real and the
    number was not: on the day this was rewritten the published index read
    28, "Fear" — the opposite reading, under that service's name.

    A fabricated figure is bad. A fabricated figure with a citation is
    worse, because the citation is what tells the investor to trust it.

    When the index cannot be read, this reports nothing rather than the
    last mood it happened to see. Sentiment is a claim about how the market
    feels now, and a stale one served as current is the same mistake in
    slower form.
    """

    ENDPOINT = "https://api.alternative.me/fng/?limit=1"

    SOURCE = "Alternative.me"

    def __init__(
        self,
        cache: JsonCache | None = None,
        ttl: timedelta = timedelta(hours=1),
        timeout: float = 10.0,
    ) -> None:
        self._cache = cache or JsonCache(
            "data/cache/sentiment",
            # Schema 1, and records written before this store
            # declared one are accepted as schema 1 deliberately —
            # their shape is what schema 1 describes. The next bump
            # needs a migration or they re-acquire, which is the
            # protection: the store cannot change shape by accident.
            schema=1,
            accepts_unversioned=True,
        )
        self._ttl = ttl
        self._timeout = timeout

    async def snapshot(self) -> SentimentSnapshot | None:
        """Today's reading, or nothing when the index cannot be read."""

        entry = self._cache.read(self.SOURCE)

        if entry is not None and entry.is_fresh(self._ttl):
            return self._restore(entry.value)

        try:
            payload = await asyncio.to_thread(self._fetch)
        except Exception:
            return None

        snapshot = self._parse(payload)

        if snapshot is not None:
            self._cache.write(self.SOURCE, self._encode(snapshot))

        return snapshot

    def _fetch(self) -> object:
        with urllib.request.urlopen(  # noqa: S310
            self.ENDPOINT,
            timeout=self._timeout,
        ) as response:
            return json.load(response)

    @classmethod
    def _parse(
        cls,
        payload: object,
    ) -> SentimentSnapshot | None:
        """Read the index out of the response, or nothing if it is not one."""

        if not isinstance(payload, dict):
            return None

        data = payload.get("data")

        if not isinstance(data, list) or not data:
            return None

        reading = data[0]

        if not isinstance(reading, dict):
            return None

        try:
            score = int(str(reading["value"]))
            label = str(reading["value_classification"])
            observed_at = datetime.fromtimestamp(
                int(str(reading["timestamp"])),
                tz=UTC,
            )
        except (KeyError, TypeError, ValueError):
            return None

        if not 0 <= score <= 100 or not label:
            return None

        return SentimentSnapshot(
            score=score,
            label=label,
            # What this index is a reading of. It is the crypto Fear &
            # Greed index; it says nothing about equities, and anything
            # asking it to must first read this field.
            subject=AssetClass.CRYPTO,
            reading=Provenance(
                source=cls.SOURCE,
                observed_at=observed_at,
            ),
        )

    @staticmethod
    def _encode(
        snapshot: SentimentSnapshot,
    ) -> dict[str, object]:
        return {
            "score": snapshot.score,
            "label": snapshot.label,
            "subject": snapshot.subject.value,
            "observed_at": snapshot.reading.observed_at.isoformat(),
        }

    @classmethod
    def _restore(
        cls,
        value: dict[str, object],
    ) -> SentimentSnapshot | None:
        score = value.get("score")
        label = value.get("label")
        raw = value.get("observed_at")

        if not isinstance(score, int) or not isinstance(label, str):
            return None

        if not isinstance(raw, str):
            return None

        try:
            observed_at = datetime.fromisoformat(raw)
        except ValueError:
            # An entry that cannot say when it was published is not a
            # sentiment reading. Serving it undated would let an old mood
            # be read as the current one, which is what this provider
            # refuses to do with a stale reading anyway.
            return None

        return SentimentSnapshot(
            score=score,
            label=label,
            subject=AssetClass.CRYPTO,
            reading=Provenance(
                source=cls.SOURCE,
                observed_at=observed_at,
            ),
        )
