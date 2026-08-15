"""Read a provider payload as claims, and promote them on the record.

The executable half of the boundary. `ValueProvider.from_info` still
produces exactly the `ValuationSnapshot` it always did — this slice
moves no decision — and this service reads the *same* payload into
the claim/translation layer so that every value the snapshot carries
can be asked what it stands on.

Deliberately a second reader of one payload rather than a rewrite of
the adapter, and the reason is the audit's own finding about
`market_snapshot_archive`: two implementations of one translation is
a defect. So this is not a second implementation of the *conversions*
— it performs none. It records what arrived, names the governing
translation, and carries the adapter's own value as the compatibility
value. `tests/test_provider_ledger_service.py` asserts field by field
that the ledger's value is the snapshot's value over the live corpus,
which is what keeps one translation from becoming two.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.provider_claim import ClaimAbsence, ProviderClaim
from app.domain.provider_fact import ProviderFact, ProviderFactLedger, promote
from app.domain.provider_translation import ProviderTranslation
from app.domain.provider_translations import (
    MERGED_INFO,
    QUOTE_SUMMARY,
    V7_QUOTE,
    YAHOO,
    governed,
    translation_for,
)
from app.domain.valuation_snapshot import ValuationSnapshot

#: The fundamentals crossings this service reads, as
#: (provider field, snapshot attribute, domain concept).
#:
#: `eps` and `dividendYield` are absent here and handled apart, because
#: each needs something this straight mapping cannot express: which
#: provider concept actually supplied the number, and which endpoint
#: served it.
_FUNDAMENTALS = (
    ("forwardPE", "forward_pe", "ValuationSnapshot.forward_pe"),
    ("trailingPE", "trailing_pe", "ValuationSnapshot.trailing_pe"),
    ("pegRatio", "peg_ratio", "ValuationSnapshot.peg_ratio"),
    ("marketCap", "market_cap", "ValuationSnapshot.market_cap"),
    ("revenueGrowth", "revenue_growth", "ValuationSnapshot.revenue_growth"),
    ("earningsGrowth", "earnings_growth", "ValuationSnapshot.earnings_growth"),
    ("grossMargins", "gross_margin", "ValuationSnapshot.gross_margin"),
    ("operatingMargins", "operating_margin", "ValuationSnapshot.operating_margin"),
    ("profitMargins", "net_margin", "ValuationSnapshot.net_margin"),
    ("returnOnEquity", "return_on_equity", "ValuationSnapshot.return_on_equity"),
    ("debtToEquity", "debt_to_equity", "ValuationSnapshot.debt_to_equity"),
    ("currentRatio", "current_ratio", "ValuationSnapshot.current_ratio"),
    (
        "operatingCashflow",
        "operating_cash_flow",
        "ValuationSnapshot.operating_cash_flow",
    ),
    ("freeCashflow", "free_cash_flow", "ValuationSnapshot.free_cash_flow"),
    ("netExpenseRatio", "expense_ratio", "ValuationSnapshot.expense_ratio"),
    ("circulatingSupply", "circulating_supply", "ValuationSnapshot.circulating_supply"),
    ("maxSupply", "max_supply", "ValuationSnapshot.max_supply"),
    ("volume24Hr", "volume_24h", "ValuationSnapshot.volume_24h"),
    ("sector", "sector", "ValuationSnapshot.sector"),
    ("industry", "industry", "ValuationSnapshot.industry"),
    ("startDate", "inception", "ValuationSnapshot.inception"),
)


class ProviderLedgerService:
    """What one provider payload actually established, per field."""

    def fundamentals(
        self,
        symbol: str,
        info: dict[str, Any],
        snapshot: ValuationSnapshot,
        requested_at: datetime,
        *,
        quote_summary: dict[str, Any] | None = None,
        v7_quote: dict[str, Any] | None = None,
    ) -> ProviderFactLedger:
        """Read a Yahoo fundamentals payload as promoted facts.

        `quote_summary` and `v7_quote` are the *unmerged* payloads,
        supplied where a caller fetched them separately. They are what
        makes the `dividendYield` conflict visible at all: the merged
        `info` dict has already discarded one of the two readings, and
        no amount of care downstream can recover it.
        """

        facts: list[ProviderFact] = [
            self._straight(field, concept, info, snapshot, attribute, requested_at)
            for field, attribute, concept in _FUNDAMENTALS
        ]

        facts.append(
            self._dividend_yield(
                info,
                snapshot,
                requested_at,
                quote_summary=quote_summary,
                v7_quote=v7_quote,
            )
        )

        facts.append(self._eps(info, snapshot, requested_at))

        return ProviderFactLedger(symbol=symbol, facts=tuple(facts))

    def _straight(
        self,
        field: str,
        concept: str,
        info: dict[str, Any],
        snapshot: ValuationSnapshot,
        attribute: str,
        requested_at: datetime,
    ) -> ProviderFact:
        translation = self._translation(field, concept)

        return promote(
            concept=concept,
            translation=translation,
            claims=(self._claim(field, info, requested_at),),
            value=getattr(snapshot, attribute),
        )

    def _dividend_yield(
        self,
        info: dict[str, Any],
        snapshot: ValuationSnapshot,
        requested_at: datetime,
        *,
        quote_summary: dict[str, Any] | None,
        v7_quote: dict[str, Any] | None,
    ) -> ProviderFact:
        """The two-schema field, kept as two claims wherever possible.

        Where the caller supplied the unmerged payloads, both readings
        are retained and `promote` finds them incompatible — so the
        promoted fact reads UNKNOWN and says which endpoint said what.
        Where only the merged dict is available (every stored record
        written before this boundary existed), one claim is recorded
        against the merged endpoint, and the field's registry warrant
        is already UNKNOWN for exactly that reason.
        """

        concept = "ValuationSnapshot.dividend_yield"

        translation = self._translation("dividendYield", concept)

        claims: list[ProviderClaim] = []

        for endpoint, payload in (
            (QUOTE_SUMMARY, quote_summary),
            (V7_QUOTE, v7_quote),
        ):
            if payload is None:
                continue

            claims.append(
                self._claim("dividendYield", payload, requested_at, endpoint=endpoint)
            )

        if not claims:
            claims.append(self._claim("dividendYield", info, requested_at))

        return promote(
            concept=concept,
            translation=translation,
            claims=tuple(claims),
            value=snapshot.dividend_yield,
        )

    def _eps(
        self,
        info: dict[str, Any],
        snapshot: ValuationSnapshot,
        requested_at: datetime,
    ) -> ProviderFact:
        """Earnings per share, and *which* earnings per share.

        The adapter's `info.get("trailingEps", info.get("forwardEps"))`
        produces one number under one name. Here the substitution stays
        visible: when the realised figure is absent and a forecast
        supplied the value, the fact is governed by the `forwardEps`
        translation, whose warrant is UNKNOWN and whose account says
        why. The value itself is untouched.
        """

        substituted = "trailingEps" not in info and "forwardEps" in info

        field = "forwardEps" if substituted else "trailingEps"

        concept = (
            "ValuationSnapshot.eps (substituted)"
            if substituted
            else "ValuationSnapshot.eps"
        )

        translation = self._translation(field, concept)

        claims = [self._claim(field, info, requested_at)]

        if substituted:
            # The realised figure's absence is part of the account: the
            # substitution happened *because* nothing reported it.
            claims.insert(
                0,
                ProviderClaim.absent(
                    provider=YAHOO,
                    endpoint=MERGED_INFO,
                    field="trailingEps",
                    requested_at=requested_at,
                    absence=ClaimAbsence.FIELD_ABSENT,
                ),
            )

        return promote(
            concept=concept,
            translation=translation,
            claims=tuple(claims),
            value=snapshot.eps,
        )

    @staticmethod
    def _claim(
        field: str,
        payload: dict[str, Any],
        requested_at: datetime,
        endpoint: str = MERGED_INFO,
    ) -> ProviderClaim:
        """One field of a payload, as the provider reported it.

        No cast and no conversion — a claim records what arrived. The
        absence is classified rather than flattened, because a key
        Yahoo omitted and a key Yahoo nulled are different statements
        and the client library has already conflated them once.
        """

        if field not in payload:
            return ProviderClaim.absent(
                provider=YAHOO,
                endpoint=endpoint,
                field=field,
                requested_at=requested_at,
                absence=ClaimAbsence.FIELD_ABSENT,
            )

        raw = payload[field]

        if raw is None:
            return ProviderClaim.absent(
                provider=YAHOO,
                endpoint=endpoint,
                field=field,
                requested_at=requested_at,
                absence=ClaimAbsence.REPORTED_NULL,
            )

        return ProviderClaim(
            provider=YAHOO,
            endpoint=endpoint,
            field=field,
            requested_at=requested_at,
            raw_value=raw,
            # Yahoo declares a currency for the *listing*, never a unit
            # for an individual fundamental. Left absent rather than
            # borrowed from a neighbouring field.
            declared_unit=None,
        )

    @staticmethod
    def _translation(field: str, concept: str) -> ProviderTranslation:
        """The registry's governing entry, or a refusal.

        An ungoverned crossing raises rather than defaulting to a
        permissive warrant: a field nobody declared is exactly the
        state this boundary exists to make impossible, and a silent
        default would recreate it inside the thing meant to prevent it.
        """

        translation = translation_for(YAHOO, MERGED_INFO, field) or governed(concept)

        if translation is None:
            raise KeyError(
                f"no governed translation for {YAHOO}'s {field} into "
                f"{concept}; a crossing must be declared before it can "
                "become a domain fact"
            )

        return translation
