"""Fundamentals that stay still while the day does."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.identity_observation import ProviderIdentityObservation
from app.domain.monetary import DenominationBasis, MarketCapDenomination
from app.domain.provenance import Provenance
from app.domain.provider_identity import (
    ProviderIdentityClaim,
    join_identity,
)
from app.domain.valuation_snapshot import ValuationSnapshot
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence.identity_observation_store import (
    IdentityObservationStore,
)
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
        observations: IdentityObservationStore | None = None,
    ) -> None:
        self._provider = provider or ValueProvider()
        # The identity observation stream — written by the observing
        # acquisition path only, before the cache's replacement, and by
        # nothing else in this class. Resolved at construction (#118).
        self._observations = observations or IdentityObservationStore()
        self._cache = cache or JsonCache(
            evidence_path("cache", "fundamentals"),
            # Schema 2 added `expense_ratio`; schema 3 added the market
            # cap's denomination, established at acquisition from the
            # payload's own arithmetic; schema 4 adds the vendor's
            # identity claim, recorded verbatim so the cross-provider
            # join (#134) can be asked of a stored record. All
            # migrations are the identity: an old record's figures keep
            # their meaning, and each new field restores as absent — a
            # pre-boundary market cap has no established denomination
            # and a pre-capture record holds no vendor account, which
            # is exactly what their silence downstream should say.
            # Schema 5 adds `financial_currency` — the provider's own
            # statement of its figures' denomination, audited present
            # in the live payload on 2026-08-23 — under the same rule:
            # a pre-5 record restores with the denomination not
            # established, never with one inferred.
            # Records written before this store declared a schema are
            # accepted as schema 1 deliberately — their shape is what
            # schema 1 describes.
            schema=5,
            migrations={
                1: lambda value: value,
                2: lambda value: value,
                3: lambda value: value,
                4: lambda value: value,
            },
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

    def snapshot_observing(
        self,
        symbol: str,
        broker: ProviderIdentityClaim,
        *,
        subject: str,
    ) -> ValuationSnapshot:
        """The acquiring read that also remembers what it observed.

        `snapshot` with one addition and one caller: before the cache's
        destructive latest-value replacement, the identity claims this
        funded read actually observed — the broker's, supplied by the
        acquisition that knows it, and the vendor's, from the payload
        just fetched — are appended to the observation stream, with the
        standing derived from them at this moment and the raw tenancy
        fields the payload happened to carry.

        **Two symbols, two jobs, never conflated.** `symbol` is the
        vendor's, and it keys the fundamentals cache exactly as the
        plain door keys it. `subject` is the canonical MOVRvest symbol
        the broker and the investor know, and it is what the
        observation is filed under and what the join is asked about:
        the broker says BTC and the vendor prices BTC-USD, and an
        identity history filed under the vendor's translation would be
        a history of a symbol the investor never held. Neither
        provider's claim is rewritten to make their symbols agree —
        each keeps its own spelling verbatim, because the difference is
        part of what was observed.

        **The order is the contract**: observation first, replacement
        second, so the store that forgets can never get ahead of the
        one that remembers. And only this method appends — a read
        served from today's cache observed nothing new, a failure that
        serves the last known reading observed nothing at all, and the
        plain `snapshot` door stays exactly what every read path
        already consumes.
        """

        key = symbol.upper().strip()
        filed = subject.upper().strip()
        entry = self._cache.read(key)

        held = self._restore(entry) if entry is not None else None

        if held is not None and held.carries_nothing:
            held = None
            entry = None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return UNREAD

        try:
            observed = self._provider.observed(symbol)
        except Exception:
            if entry is not None:
                return self._restore(entry, last_known=True)

            raise

        snapshot = observed.snapshot
        vendor = snapshot.vendor_identity

        # A payload offering no identity claim leaves nothing to
        # preserve: recording an empty vendor account would read as the
        # vendor having said something.
        if vendor is not None:
            reading = snapshot.reading

            self._observations.append(
                ProviderIdentityObservation(
                    symbol=filed,
                    captured_at=(
                        reading.observed_at
                        if reading is not None
                        else datetime.now(UTC)
                    ),
                    broker=broker,
                    vendor=vendor,
                    standing=join_identity(filed, (broker, vendor)).standing,
                    first_trade_date_ms=observed.first_trade_date_ms,
                    ipo_expected_date=observed.ipo_expected_date,
                )
            )

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
            "vendor_identity": (
                {
                    "provider": snapshot.vendor_identity.provider,
                    "symbol": snapshot.vendor_identity.symbol,
                    "name": snapshot.vendor_identity.name,
                    "taxonomy": snapshot.vendor_identity.taxonomy,
                    "exchange": snapshot.vendor_identity.exchange,
                }
                if snapshot.vendor_identity is not None
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
            "financial_currency": snapshot.financial_currency,
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
            vendor_identity=cls._vendor_identity(value.get("vendor_identity")),
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
            financial_currency=text("financial_currency"),
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
    def _vendor_identity(raw: object) -> ProviderIdentityClaim | None:
        """A stored vendor claim, or nothing — never a reconstructed one.

        A record that predates the capture restores with the vendor
        having said nothing, so the identity join downstream rests on
        the broker's claim alone and stays honestly assumed.
        """

        if not isinstance(raw, dict):
            return None

        def text(field: str) -> str | None:
            value = raw.get(field)

            return value if isinstance(value, str) and value.strip() else None

        symbol = text("symbol")
        name = text("name")
        taxonomy = text("taxonomy")
        exchange = text("exchange")

        if not (symbol or name or taxonomy or exchange):
            return None

        return ProviderIdentityClaim(
            provider=text("provider") or ValueProvider.SOURCE,
            symbol=symbol or "",
            name=name,
            taxonomy=taxonomy,
            exchange=exchange,
            isin=None,
        )

    @staticmethod
    def _timestamp(raw: object) -> datetime | None:
        if not isinstance(raw, str):
            return None

        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None
