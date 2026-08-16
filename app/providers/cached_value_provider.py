"""Fundamentals that stay still while the day does."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.monetary import DenominationBasis, MarketCapDenomination
from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence_root import evidence_path
from app.providers.value_provider import ValueProvider

#: A company this platform has never read the fundamentals of.
#:
#: Every figure absent and undated, which is what it is. Not a snapshot of
#: zeroes and not one dated now: the analysts already read an absent figure
#: as unknown, and an undated one cannot be mistaken for a reading.
UNREAD = ValuationSnapshot(
    forward_pe=None,
    trailing_pe=None,
    peg_ratio=None,
    dividend_yield=None,
)


class CachedValueProvider:
    """
    Read a company's fundamentals once a day, and remember them.

    Two properties matter more than the saved requests:

    Determinism. Fundamentals are published at most daily, so two runs on
    the same day must produce the same evidence. Without that, a rate-limit
    hiccup changes a score, the score changes a decision, and the platform
    records that the Artificial CIO changed its mind about a company when
    nothing about the company changed.

    Truthful age. A snapshot replayed from cache keeps the observation time
    it was fetched with. When the provider fails and yesterday's reading is
    served instead, it is served as yesterday's reading — old evidence is
    still evidence, but it is never dated today.
    """

    def __init__(
        self,
        provider: ValueProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or ValueProvider()
        self._cache = cache or JsonCache(
            evidence_path("cache", "fundamentals"),
            # Schema 2 added `expense_ratio`; schema 3 adds the market
            # cap's denomination, established at acquisition from the
            # payload's own arithmetic. Both migrations are the
            # identity: an old record's figures keep their meaning, and
            # the new field restores as absent — a pre-boundary market
            # cap has no established denomination, which is exactly
            # what its silence downstream should say. Records written
            # before this store declared a schema are accepted as
            # schema 1 deliberately — their shape is what schema 1
            # describes.
            schema=3,
            migrations={1: lambda value: value, 2: lambda value: value},
            accepts_unversioned=True,
        )
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedValueProvider:
        """
        The fundamentals this platform has already read, and no others.

        The read-only door. A company read some days ago is served as
        read some days ago — this class already believed old evidence is
        still evidence when it carries its date, and this is that rule
        with the fetch removed.

        A company never read carries nothing, and every figure derived
        from it is absent rather than estimated.
        """

        return cls(cache=cache, acquires=False)

    def snapshot(
        self,
        symbol: str,
    ) -> ValuationSnapshot:
        key = symbol.upper().strip()
        entry = self._cache.read(key)

        held = self._restore(entry) if entry is not None else None

        # An entry carrying no figure at all is a refusal that was cached
        # as a reading, before the provider learned to raise on one. It is
        # treated as nothing held, so an acquisition reads the company
        # again instead of being told it already has it — twelve companies
        # were stored this way, and `is_from_today` would have served
        # McDonald's as unmeasured until midnight.
        if held is not None and held.carries_nothing:
            held = None
            entry = None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return UNREAD

        try:
            snapshot = self._provider.snapshot(symbol)
        except Exception:
            # The provider rate-limits. Dropping the company's fundamentals
            # would flip its evidence to "unknown" and, with it, the
            # decision — so the last real reading is served, still carrying
            # the date it was actually taken.
            #
            # And marked. Served under its own date it is indistinguishable
            # from a reading taken on schedule, which would hide a provider
            # outage behind a plausible-looking figure.
            if entry is not None:
                return self._restore(entry, last_known=True)

            raise

        self._cache.write(key, self._encode(snapshot))

        return snapshot

    @staticmethod
    def _encode(
        snapshot: ValuationSnapshot,
    ) -> dict[str, object]:
        reading = snapshot.reading or Provenance(
            source=ValueProvider.SOURCE,
            observed_at=datetime.now(UTC),
        )

        return {
            "forward_pe": snapshot.forward_pe,
            "trailing_pe": snapshot.trailing_pe,
            "peg_ratio": snapshot.peg_ratio,
            "dividend_yield": snapshot.dividend_yield,
            "market_cap": snapshot.market_cap,
            "market_cap_denomination": (
                {
                    "currency": snapshot.market_cap_denomination.currency,
                    "basis": snapshot.market_cap_denomination.basis.value,
                    "because": snapshot.market_cap_denomination.because,
                }
                if snapshot.market_cap_denomination is not None
                else None
            ),
            "eps": snapshot.eps,
            "circulating_supply": snapshot.circulating_supply,
            "max_supply": snapshot.max_supply,
            "volume_24h": snapshot.volume_24h,
            "expense_ratio": snapshot.expense_ratio,
            "inception": (
                snapshot.inception.isoformat()
                if snapshot.inception is not None
                else None
            ),
            # Fundamentals read from the same call. Dropped on a cache hit,
            # they would leave the analysts nothing to analyse for the rest
            # of the day the reading was taken.
            "revenue_growth": snapshot.revenue_growth,
            "earnings_growth": snapshot.earnings_growth,
            "gross_margin": snapshot.gross_margin,
            "operating_margin": snapshot.operating_margin,
            "net_margin": snapshot.net_margin,
            "return_on_equity": snapshot.return_on_equity,
            "debt_to_equity": snapshot.debt_to_equity,
            "current_ratio": snapshot.current_ratio,
            "operating_cash_flow": snapshot.operating_cash_flow,
            "free_cash_flow": snapshot.free_cash_flow,
            "sector": snapshot.sector,
            "industry": snapshot.industry,
            "source": reading.source,
            "observed_at": reading.observed_at.isoformat(),
        }

    @classmethod
    def _restore(
        cls,
        entry: CachedEntry,
        last_known: bool = False,
    ) -> ValuationSnapshot:
        value = entry.value

        def number(field: str) -> float | None:
            raw = value.get(field)

            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                return None

            return float(raw)

        def text(field: str) -> str | None:
            raw = value.get(field)

            return raw if isinstance(raw, str) and raw.strip() else None

        observed_at = entry.stored_at

        raw_observed = value.get("observed_at")

        if isinstance(raw_observed, str):
            try:
                observed_at = datetime.fromisoformat(raw_observed)
            except ValueError:
                observed_at = entry.stored_at

        source = value.get("source")

        return ValuationSnapshot(
            forward_pe=number("forward_pe"),
            trailing_pe=number("trailing_pe"),
            peg_ratio=number("peg_ratio"),
            dividend_yield=number("dividend_yield"),
            market_cap=number("market_cap"),
            market_cap_denomination=cls._denomination(
                value.get("market_cap_denomination")
            ),
            eps=number("eps"),
            circulating_supply=number("circulating_supply"),
            max_supply=number("max_supply"),
            volume_24h=number("volume_24h"),
            expense_ratio=number("expense_ratio"),
            inception=cls._timestamp(value.get("inception")),
            revenue_growth=number("revenue_growth"),
            earnings_growth=number("earnings_growth"),
            gross_margin=number("gross_margin"),
            operating_margin=number("operating_margin"),
            net_margin=number("net_margin"),
            return_on_equity=number("return_on_equity"),
            debt_to_equity=number("debt_to_equity"),
            current_ratio=number("current_ratio"),
            operating_cash_flow=number("operating_cash_flow"),
            free_cash_flow=number("free_cash_flow"),
            sector=text("sector"),
            industry=text("industry"),
            reading=Provenance(
                source=source if isinstance(source, str) else ValueProvider.SOURCE,
                observed_at=observed_at,
                last_known=last_known,
            ),
        )

    @staticmethod
    def _denomination(raw: object) -> MarketCapDenomination | None:
        """A stored denomination, or nothing — never a guessed one.

        A record that predates the boundary, or whose stored shape
        cannot be read back, restores as no denomination at all: the
        magnitude then stays incomparable, which is the pre-boundary
        truth rather than a new claim.
        """

        if not isinstance(raw, dict):
            return None

        basis = raw.get("basis")
        currency = raw.get("currency")
        because = raw.get("because")

        try:
            parsed = DenominationBasis(basis) if isinstance(basis, str) else None
        except ValueError:
            return None

        if parsed is None or not isinstance(because, str):
            return None

        try:
            return MarketCapDenomination(
                currency=currency if isinstance(currency, str) else None,
                basis=parsed,
                because=because,
            )
        except ValueError:
            return None

    @staticmethod
    def _timestamp(raw: object) -> datetime | None:
        if not isinstance(raw, str):
            return None

        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None
