"""Read a token's published rating from TokenInsight, once a day."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import requests

from app.config import get_settings
from app.domain.provenance import Provenance
from app.domain.token_rating import RatingDimension, TokenRating
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache

#: The rater's own identifier for each token this platform watches.
#:
#: Declared rather than looked up, and every entry verified against the
#: provider by hand: each returns a rating whose `symbol` is the one
#: below. The provider is asked to confirm it again on every read, so a
#: wrong entry here shows up as a refusal rather than as another token's
#: rating printed under this one's name — the lesson `NESN.ZU` taught,
#: applied before it can go wrong rather than after.
TOKEN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "ARB": "arbitrum",
    "1INCH": "1inch",
    "HYPE": "hyperliquid",
    "TAO": "bittensor",
}

#: The six dimensions the rater publishes, worded for the investor.
DIMENSIONS = (
    ("underlying_technology_security", "Technology and security"),
    ("token_economics", "Token economics"),
    ("roadmap_progress", "Roadmap progress"),
    ("team_partners_investors", "Team, partners and investors"),
    ("ecosystem_development", "Ecosystem development"),
    ("token_performance", "Token performance"),
)

API_KEY_ENV = "TOKENINSIGHT_API_KEY"


class RatingUnavailable(LookupError):
    """No rating could be read, and the reason is worded for a surface."""


class TokenInsightProvider:
    """
    One published rating, or a worded reason there is none.

    The rating is somebody else's work and is labelled with their name
    everywhere it travels. This class reads it and checks one thing
    before handing it on: that the token the rater answered about is the
    token that was asked about.
    """

    SOURCE = "TokenInsight"

    BASE = "https://api.tokeninsight.com/api/v1"

    #: The provider sits behind a bot filter that rejects the default
    #: library signature outright, key or no key. A browser's user agent
    #: is what it will answer, so it is sent with an otherwise ordinary
    #: authenticated request.
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )

    TIMEOUT = 20

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def key(self) -> str:
        """The configured key, environment first and `.env` second."""

        if self._api_key is not None:
            return self._api_key

        configured = os.environ.get(API_KEY_ENV) or get_settings().tokeninsight_api_key

        return str(configured or "")

    def rating(self, symbol: str) -> TokenRating:
        normalized = symbol.upper().strip()

        key = self.key()

        if not key:
            raise RatingUnavailable(
                f"No {self.SOURCE} key is configured, so no published rating was read."
            )

        token_id = TOKEN_IDS.get(normalized)

        if token_id is None:
            raise RatingUnavailable(
                f"{self.SOURCE} is not asked about {normalized}: this platform "
                "has not verified which token the rater means by it."
            )

        response = requests.get(
            f"{self.BASE}/rating/coin/{token_id}",
            headers={
                "TI_API_KEY": key,
                "accept": "application/json",
                "user-agent": self.USER_AGENT,
            },
            timeout=self.TIMEOUT,
        )

        if not response.ok:
            raise RatingUnavailable(
                f"{self.SOURCE} answered {response.status_code} for {normalized}."
            )

        rows = (response.json() or {}).get("data") or []

        if not rows:
            raise RatingUnavailable(
                f"{self.SOURCE} publishes no rating for {normalized}."
            )

        return self._read(normalized, rows[0])

    @classmethod
    def _read(cls, symbol: str, row: dict[str, Any]) -> TokenRating:
        # The identity check, before anything is carried. The rater
        # answers with the symbol it rated; if that is not the token
        # asked about, the mapping is wrong and a rating printed under
        # the wrong name is worse than none.
        rated = str(row.get("symbol", "")).upper().strip()

        if rated and rated != symbol:
            raise RatingUnavailable(
                f"{cls.SOURCE} answered about {rated} when asked about "
                f"{symbol}, so the rating was not read."
            )

        level = str(row.get("rating_level", "")).strip()
        score = cls._percentage(row.get("rating_score"))

        if not level or score is None:
            raise RatingUnavailable(f"{cls.SOURCE} returned no rating for {symbol}.")

        dimensions = tuple(
            RatingDimension(label=label, score=value)
            for field, label in DIMENSIONS
            if (value := cls._percentage(row.get(field))) is not None
        )

        return TokenRating(
            symbol=symbol,
            name=str(row.get("name") or symbol),
            level=level,
            score=score,
            dimensions=dimensions,
            reviewed_at=cls._moment(row.get("review_time")),
            page_url=cls._link(row.get("rating_page")),
            report_url=cls._link(row.get("rating_report")),
            reading=Provenance(source=cls.SOURCE, observed_at=datetime.now(UTC)),
        )

    @staticmethod
    def _percentage(value: object) -> float | None:
        """A score the rater published as "86.20%" or "80.63"."""

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)

        if not isinstance(value, str):
            return None

        try:
            return float(value.strip().rstrip("%"))
        except ValueError:
            return None

    @staticmethod
    def _moment(value: object) -> datetime | None:
        """A millisecond timestamp, where the rater sent one."""

        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None

        try:
            return datetime.fromtimestamp(float(value) / 1000, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None

    @staticmethod
    def _link(value: object) -> str | None:
        text = str(value or "").strip()

        return text if text.startswith("https://") else None


class CachedTokenInsightProvider:
    """
    Read a rating once a day, and remember it.

    A rating is reviewed periodically rather than continuously — the
    review date comes with it — so reading it more than daily spends a
    credit to learn nothing. The investor's allowance is 5,000 a month
    and the whole watched universe is eight tokens, so one acquisition
    cycle a day costs about 240 of them.

    Two doors, like everything else. A surface opens `stored` and never
    reaches the provider; `movrvest acquire` opens the other. A rating
    never read is absent, and its absence carries the reason.
    """

    def __init__(
        self,
        provider: TokenInsightProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or TokenInsightProvider()
        self._cache = cache or JsonCache(
            "data/cache/ratings",
            # Schema 1, and records written before this store
            # declared one are accepted as schema 1 deliberately —
            # their shape is what schema 1 describes. The next bump
            # needs a migration or they re-acquire, which is the
            # protection: the store cannot change shape by accident.
            schema=1,
            accepts_unversioned=True,
        )
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedTokenInsightProvider:
        """The ratings already read, and no others."""

        return cls(cache=cache, acquires=False)

    def rating(self, symbol: str) -> TokenRating | None:
        key = symbol.upper().strip()
        entry = self._cache.read(key)

        held = self._restore(entry) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            rating = self._provider.rating(key)
        except Exception:
            # A rating that could not be re-read leaves the last one
            # standing. It carries its own review date, so an old
            # opinion is visibly an old opinion.
            return held

        self._cache.write(key, self._encode(rating))

        return rating

    @staticmethod
    def _encode(rating: TokenRating) -> dict[str, Any]:
        return {
            "symbol": rating.symbol,
            "name": rating.name,
            "level": rating.level,
            "score": rating.score,
            "dimensions": [
                {"label": dimension.label, "score": dimension.score}
                for dimension in rating.dimensions
            ],
            "reviewed_at": (
                rating.reviewed_at.isoformat() if rating.reviewed_at else None
            ),
            "page_url": rating.page_url,
            "report_url": rating.report_url,
            "source": rating.reading.source,
            "observed_at": rating.reading.observed_at.isoformat(),
        }

    @staticmethod
    def _restore(entry: CachedEntry) -> TokenRating | None:
        value = entry.value

        level = value.get("level")
        score = value.get("score")

        if not isinstance(level, str) or not isinstance(score, (int, float)):
            return None

        def moment(field: str) -> datetime | None:
            raw = value.get(field)

            if not isinstance(raw, str):
                return None

            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                return None

        raw_dimensions = value.get("dimensions")

        dimensions = tuple(
            RatingDimension(label=str(item["label"]), score=float(item["score"]))
            for item in (raw_dimensions if isinstance(raw_dimensions, list) else ())
            if isinstance(item, dict)
            and isinstance(item.get("label"), str)
            and isinstance(item.get("score"), (int, float))
        )

        return TokenRating(
            symbol=str(value.get("symbol", "")),
            name=str(value.get("name", "")),
            level=level,
            score=float(score),
            dimensions=dimensions,
            reviewed_at=moment("reviewed_at"),
            page_url=(
                value.get("page_url")
                if isinstance(value.get("page_url"), str)
                else None
            ),
            report_url=(
                value.get("report_url")
                if isinstance(value.get("report_url"), str)
                else None
            ),
            reading=Provenance(
                source=str(value.get("source", TokenInsightProvider.SOURCE)),
                observed_at=moment("observed_at") or entry.stored_at,
            ),
        )
