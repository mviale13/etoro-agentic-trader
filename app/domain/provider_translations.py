"""The governed translation inventory — #133's measurement, as code.

The Provider Semantics Audit produced a table. A table in a document
is a historical claim about what the adapters did on the day someone
read them; this registry is the same content in the form the adapters
actually consult, so the inventory and the behaviour cannot drift
apart without a test failing.

`docs/architecture/PROVIDER_TRANSLATION_INVENTORY.md` is **generated
from this module** (`movrvest translations --markdown`) and checked
by `tests/test_provider_translation_inventory.py`. Editing the
document by hand is a test failure, which is the point: one source of
truth, and the rendered copy is a view of it.

The warrants below are the audit's measured findings, not aspirations.
Most of this boundary is ASSUMED, three fields are UNKNOWN, and the
single VERIFIED entry is the venue table somebody checked by hand.
Recording that honestly is the deliverable — repairs are a later
slice, and a warrant upgraded without evidence would forfeit the only
thing this registry is for.
"""

from __future__ import annotations

from app.domain.provider_translation import (
    DecisionRelevance,
    DomainRepresentation,
    ProviderTranslation,
    TranslationKind,
    TranslationWarrant,
)

YAHOO = "Yahoo Finance"
ETORO = "eToro"

#: The two Yahoo endpoints the client library merges into one `info`
#: dict. Named apart because that merge is the `dividendYield` defect:
#: 31 keys collide, one of them differs, and the winner is decided by
#: whether an HTTP call happened to succeed.
QUOTE_SUMMARY = "quoteSummary"
V7_QUOTE = "v7/finance/quote"
MERGED_INFO = "Ticker.info (merged)"
YF_DOWNLOAD = "yf.download"
ETORO_WATCHLISTS = "/api/v1/watchlists"
ETORO_INSTRUMENTS = "/api/v1/market-data/instruments"


def _assumed_fundamental(
    field: str,
    concept: str,
    relevance: DecisionRelevance,
    representation: DomainRepresentation | None = None,
    kinds: tuple[TranslationKind, ...] = (TranslationKind.SEMANTIC,),
) -> ProviderTranslation:
    """One Yahoo fundamental crossing on the platform's own authority.

    The shape of ~57 of these. Written as a helper rather than
    repeated so the registry reads as what it is: a large body of
    identical unwarranted crossings, and a handful of interesting
    ones spelled out in full below.
    """

    return ProviderTranslation(
        provider=YAHOO,
        provider_field=field,
        endpoint=MERGED_INFO,
        domain_concept=concept,
        kinds=kinds,
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=relevance,
        representation=representation,
    )


#: Every governed crossing on the equity/broker path.
TRANSLATIONS: tuple[ProviderTranslation, ...] = (
    # ---- The three seeds, spelled out in full -------------------------
    ProviderTranslation(
        provider=YAHOO,
        provider_field="dividendYield",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.dividend_yield",
        kinds=(TranslationKind.UNIT, TranslationKind.SEMANTIC),
        warrant=TranslationWarrant.UNKNOWN,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.DECIMAL_RATIO,
        because=(
            "two provider schemas serve this key at two scales — "
            "quoteSummary as a fraction (0.0517), /v7/finance/quote as "
            "percentage points (5.17) — and the client library merges "
            "them, so which arrived depends on whether an HTTP call "
            "succeeded. No interpretation of the merged field is "
            "justified; measured over 77 stored records, 33 are "
            "percent-scale and 1 is a fraction"
        ),
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="forwardPE",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.forward_pe",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.MULTIPLE,
    ),
    ProviderTranslation(
        provider=ETORO,
        provider_field="assetTypeId",
        endpoint=ETORO_WATCHLISTS,
        domain_concept="AssetClass",
        kinds=(TranslationKind.VOCABULARY,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.SELECTS_ANALYSIS,
    ),
    ProviderTranslation(
        provider=ETORO,
        provider_field="instrumentTypeID",
        endpoint=ETORO_INSTRUMENTS,
        domain_concept="AssetClass",
        kinds=(TranslationKind.VOCABULARY,),
        warrant=TranslationWarrant.UNKNOWN,
        decision_relevance=DecisionRelevance.SELECTS_ANALYSIS,
        because=(
            "read through the same four-row table as the watchlist's "
            "assetTypeId, and nothing establishes that the two eToro "
            "endpoints share a codespace. The broker publishes a "
            "taxonomy endpoint that would declare it; nothing calls it"
        ),
    ),
    # ---- Identity ----------------------------------------------------
    ProviderTranslation(
        provider=YAHOO,
        provider_field="<symbol>",
        endpoint=MERGED_INFO,
        domain_concept="YahooInstrument.yahoo_symbol",
        kinds=(TranslationKind.IDENTITY,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.IDENTIFIER,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="<venue suffix>",
        endpoint=MERGED_INFO,
        domain_concept="YahooInstrument.yahoo_symbol (venue)",
        kinds=(TranslationKind.IDENTITY,),
        warrant=TranslationWarrant.VERIFIED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.IDENTIFIER,
        because=(
            "the one entry (ZU to SW) was checked against the provider by "
            "hand before it was written: NESN.ZU returns a single empty "
            "field and NESN.SW returns Nestle with 169 of them. Every "
            "other suffix on the book was measured identical at both "
            "vendors and passes through untouched"
        ),
    ),
    # ---- Quotes ------------------------------------------------------
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close",
        endpoint=YF_DOWNLOAD,
        domain_concept="MarketQuote.price",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.DISPLAY_ONLY,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="<none — hardcoded>",
        endpoint=YF_DOWNLOAD,
        domain_concept="MarketQuote.currency",
        kinds=(TranslationKind.VOCABULARY,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.DISPLAY_ONLY,
        representation=DomainRepresentation.IDENTIFIER,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close (pair)",
        endpoint=YF_DOWNLOAD,
        domain_concept="MarketQuote.change_percent",
        kinds=(TranslationKind.UNIT, TranslationKind.SEMANTIC),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.PERCENT_POINTS,
    ),
    # ---- ^TNX: one field, two translations ---------------------------
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close (^TNX)",
        endpoint=YF_DOWNLOAD,
        domain_concept="MarketQuote.price (^TNX)",
        kinds=(TranslationKind.SEMANTIC, TranslationKind.UNIT),
        warrant=TranslationWarrant.UNKNOWN,
        decision_relevance=DecisionRelevance.DISPLAY_ONLY,
        because=(
            "the value is a yield under the CBOE's times-ten convention "
            "(42.5 is 4.25%) entering a field named price, and the "
            "currency beside it is invented. Two translations on one "
            "field, neither of them checked; the representation is left "
            "unnamed because what it should be is exactly what is in "
            "dispute"
        ),
    ),
    # ---- The EPS fallback --------------------------------------------
    ProviderTranslation(
        provider=YAHOO,
        provider_field="trailingEps",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.eps",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="forwardEps",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.eps (substituted)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.UNKNOWN,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
        because=(
            "a forecast standing in for a realised figure under one field "
            "name. The substitution is decision-visible exactly where "
            "trailing and forward earnings differ in sign — the turnaround "
            "case — where a loss-making company earns the platform's "
            "positive-earnings point on an estimate"
        ),
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="volume24Hr",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.volume_24h",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.UNCONSUMED,
        representation=DomainRepresentation.COUNT,
    ),
    # ---- The denomination corroboration inputs (#142) ----------------
    # Three fields read solely as inputs to the market-cap denomination
    # identity check. Each is ASSUMED on its own; what the check
    # *derives* from their agreement is a VALIDATED denomination on the
    # magnitude, carried with its because — the inputs never reach a
    # domain fact directly.
    #
    # `impliedSharesOutstanding` is deliberately not here and not read
    # at all: nothing warrants it as a report independent of the
    # market-cap claim, and it was measured reconstructing cap ÷ price
    # for 64 of 64 live securities — a circular input would make the
    # corroboration a tautology (PR #143 amendment).
    ProviderTranslation(
        provider=YAHOO,
        provider_field="currency",
        endpoint=MERGED_INFO,
        domain_concept="MarketCapDenomination (corroboration input)",
        kinds=(TranslationKind.VOCABULARY,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.IDENTIFIER,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="regularMarketPrice",
        endpoint=MERGED_INFO,
        domain_concept="MarketCapDenomination (corroboration input)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="sharesOutstanding",
        endpoint=MERGED_INFO,
        domain_concept="MarketCapDenomination (corroboration input)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.COUNT,
    ),
    # ---- The FX translation rates (C6) -------------------------------
    # Four pair closes read as "USD per one unit of the base currency"
    # — the direct quote, inverted zero times on this path. Each is
    # ASSUMED on its own (the pair symbol's meaning is a convention
    # this platform has not verified against provider documentation);
    # what the translation *derives* under fx-translation@1 is a dated,
    # sourced, direction-fixed monetary claim that authorises a
    # comparison only on the day it shares with the figure it
    # translates.
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close (CHFUSD=X)",
        endpoint=YF_DOWNLOAD,
        domain_concept="ExchangeRate CHF→USD (translation input)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close (DKKUSD=X)",
        endpoint=YF_DOWNLOAD,
        domain_concept="ExchangeRate DKK→USD (translation input)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close (EURUSD=X)",
        endpoint=YF_DOWNLOAD,
        domain_concept="ExchangeRate EUR→USD (translation input)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
        because=(
            "the same field the portfolio display reads inverted once "
            "for its USD→EUR direction; this path reads it direct, and "
            "each seam writes its own direction down exactly once"
        ),
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="Close (GBPUSD=X)",
        endpoint=YF_DOWNLOAD,
        domain_concept="ExchangeRate GBP→USD (translation input)",
        kinds=(TranslationKind.SEMANTIC,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.GATES_A_DECISION,
        representation=DomainRepresentation.CURRENCY_AMOUNT,
        because=(
            "the pound's rate, for a cap established GBP by the "
            "minor-unit identity — the translation multiplies the "
            "POUNDS figure, never the pence quote and never the "
            "statement dollars"
        ),
    ),
    # ---- The two conversions that exist ------------------------------
    ProviderTranslation(
        provider=YAHOO,
        provider_field="debtToEquity",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.debt_to_equity",
        kinds=(TranslationKind.UNIT,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.SHAPES_RESEARCH,
        representation=DomainRepresentation.DECIMAL_RATIO,
    ),
    ProviderTranslation(
        provider=YAHOO,
        provider_field="netExpenseRatio",
        endpoint=MERGED_INFO,
        domain_concept="ValuationSnapshot.expense_ratio",
        kinds=(TranslationKind.UNIT,),
        warrant=TranslationWarrant.ASSUMED,
        decision_relevance=DecisionRelevance.DISPLAY_ONLY,
        representation=DomainRepresentation.DECIMAL_RATIO,
    ),
    # ---- The remaining fundamentals ----------------------------------
    _assumed_fundamental(
        "trailingPE",
        "ValuationSnapshot.trailing_pe",
        DecisionRelevance.UNCONSUMED,
        DomainRepresentation.MULTIPLE,
    ),
    _assumed_fundamental(
        "pegRatio",
        "ValuationSnapshot.peg_ratio",
        DecisionRelevance.UNCONSUMED,
        DomainRepresentation.MULTIPLE,
    ),
    _assumed_fundamental(
        "marketCap",
        "ValuationSnapshot.market_cap",
        DecisionRelevance.GATES_A_DECISION,
        DomainRepresentation.CURRENCY_AMOUNT,
    ),
    _assumed_fundamental(
        "revenueGrowth",
        "ValuationSnapshot.revenue_growth",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.DECIMAL_RATIO,
    ),
    _assumed_fundamental(
        "earningsGrowth",
        "ValuationSnapshot.earnings_growth",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.DECIMAL_RATIO,
    ),
    _assumed_fundamental(
        "grossMargins",
        "ValuationSnapshot.gross_margin",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.DECIMAL_RATIO,
    ),
    _assumed_fundamental(
        "operatingMargins",
        "ValuationSnapshot.operating_margin",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.DECIMAL_RATIO,
    ),
    _assumed_fundamental(
        "profitMargins",
        "ValuationSnapshot.net_margin",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.DECIMAL_RATIO,
    ),
    _assumed_fundamental(
        "returnOnEquity",
        "ValuationSnapshot.return_on_equity",
        DecisionRelevance.UNCONSUMED,
        DomainRepresentation.DECIMAL_RATIO,
    ),
    _assumed_fundamental(
        "currentRatio",
        "ValuationSnapshot.current_ratio",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.MULTIPLE,
    ),
    _assumed_fundamental(
        "operatingCashflow",
        "ValuationSnapshot.operating_cash_flow",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.CURRENCY_AMOUNT,
    ),
    _assumed_fundamental(
        "freeCashflow",
        "ValuationSnapshot.free_cash_flow",
        DecisionRelevance.SHAPES_RESEARCH,
        DomainRepresentation.CURRENCY_AMOUNT,
    ),
    _assumed_fundamental(
        "sector",
        "ValuationSnapshot.sector",
        DecisionRelevance.SELECTS_ANALYSIS,
        DomainRepresentation.IDENTIFIER,
        kinds=(TranslationKind.VOCABULARY,),
    ),
    _assumed_fundamental(
        "industry",
        "ValuationSnapshot.industry",
        DecisionRelevance.SELECTS_ANALYSIS,
        DomainRepresentation.IDENTIFIER,
        kinds=(TranslationKind.VOCABULARY,),
    ),
    _assumed_fundamental(
        "circulatingSupply",
        "ValuationSnapshot.circulating_supply",
        DecisionRelevance.UNCONSUMED,
        DomainRepresentation.COUNT,
    ),
    _assumed_fundamental(
        "maxSupply",
        "ValuationSnapshot.max_supply",
        DecisionRelevance.UNCONSUMED,
        DomainRepresentation.COUNT,
    ),
    _assumed_fundamental(
        "startDate",
        "ValuationSnapshot.inception",
        DecisionRelevance.UNCONSUMED,
        DomainRepresentation.TIMESTAMP,
    ),
)


def translation_for(
    provider: str,
    endpoint: str,
    field: str,
) -> ProviderTranslation | None:
    """The governing translation for one crossing, or nothing."""

    return next(
        (item for item in TRANSLATIONS if item.key == (provider, endpoint, field)),
        None,
    )


def governed(concept: str) -> ProviderTranslation | None:
    """The translation producing this domain concept, or nothing."""

    return next(
        (item for item in TRANSLATIONS if item.domain_concept == concept),
        None,
    )


def under(warrant: TranslationWarrant) -> tuple[ProviderTranslation, ...]:
    """Every translation standing on one warrant."""

    return tuple(item for item in TRANSLATIONS if item.warrant is warrant)


def counted() -> dict[TranslationWarrant, int]:
    """How the boundary is distributed across warrants.

    The audit's census, recomputed from the live registry rather than
    quoted from a document — so the number in the report is the number
    in the code, always.
    """

    return {
        warrant: len(under(warrant)) for warrant in TranslationWarrant if under(warrant)
    }


def awaiting_warrant() -> tuple[ProviderTranslation, ...]:
    """Unwarranted translations, ranked by how far they reach.

    Deliverable 14 of the audit brief, as a function rather than a
    list somebody maintains: what should be repaired first is a
    product of *warrant × reach*, and both terms live here.

    Ranked by reach only. A tie is broken by the domain concept's
    name, never by registry order, so the ranking is a fact about the
    system rather than about how the file was typed.
    """

    unwarranted = tuple(
        item
        for item in TRANSLATIONS
        if not item.establishes_domain_fact
        and item.warrant is not TranslationWarrant.DECLARED
    )

    return tuple(sorted(unwarranted, key=lambda item: item.repair_rank))
