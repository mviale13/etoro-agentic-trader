"""Compose the asset profile from judged token facts, and derive nothing.

Every value here comes off a `TokenMarketFacts` the validation gate
produced; this module formats and groups. The two derived rows — the
issued share and the dilution ratio — are computed by the domain from
established inputs only, and are labelled as this platform's arithmetic
rather than dressed as provider observations.
"""

from __future__ import annotations

from datetime import datetime

from app.api.models.dossier import (
    AssetProfileResponse,
    RejectedReadingResponse,
    TokenFactGroupResponse,
    TokenFactRowResponse,
)
from app.domain.provenance import Provenance
from app.domain.token_fact_validation import FACT_LABELS
from app.domain.token_facts import TokenFact, TokenMarketFacts

#: How each fact's value is worded. Formatting only — the judging that
#: decided whether a value is served at all happened in the domain.
_MONEY = (
    "market_cap",
    "spot_volume_24h",
    "market_volume_24h",
    "fully_diluted_valuation",
)
_COUNT = ("circulating_supply", "total_supply", "max_supply")
_SIGNED_SHARE = ("spot_volume_change_24h", "price_change_24h")


def asset_profile_response(
    outcome: TokenMarketFacts | None,
) -> AssetProfileResponse | None:
    """The profile over the wire, or null where the subject has none."""

    if outcome is None:
        return None

    groups = [
        TokenFactGroupResponse(
            title="Market",
            rows=[
                _row(outcome, "market_cap"),
                _rank_row(outcome),
                _row(outcome, "price_change_24h"),
            ],
        ),
        TokenFactGroupResponse(
            title="Trading activity",
            rows=[
                _row(outcome, "spot_volume_24h"),
                _row(outcome, "spot_volume_change_24h"),
                _row(outcome, "market_volume_24h"),
            ],
        ),
        TokenFactGroupResponse(
            title="Supply",
            rows=[
                _row(outcome, "circulating_supply"),
                _row(outcome, "total_supply"),
                _row(outcome, "max_supply"),
                _issued_share_row(outcome),
            ],
        ),
        TokenFactGroupResponse(
            title="Dilution context",
            rows=[
                _row(outcome, "fully_diluted_valuation"),
                _dilution_row(outcome),
            ],
        ),
        TokenFactGroupResponse(
            title="History",
            rows=[
                _row(outcome, "project_age"),
            ],
        ),
    ]

    return AssetProfileResponse(
        groups=groups,
        rejected=[
            RejectedReadingResponse(statement=item.statement)
            for item in outcome.rejected
        ],
    )


def _row(outcome: TokenMarketFacts, name: str) -> TokenFactRowResponse:
    fact = outcome.fact(name)

    assert fact is not None, name

    return TokenFactRowResponse(
        label=FACT_LABELS.get(name, name),
        stated=_stated(fact),
        standing=fact.standing.value,
        standing_stated=fact.standing.stated,
        source=fact.source,
        age=_age(fact.source, fact.observed_at),
        because=fact.because,
    )


def _rank_row(outcome: TokenMarketFacts) -> TokenFactRowResponse:
    fact = outcome.fact("rank")

    assert fact is not None

    stated = (
        f"#{fact.value:,.0f}"
        if fact.value is not None and fact.standing.serves_value
        else None
    )

    return TokenFactRowResponse(
        label=FACT_LABELS["rank"],
        stated=stated,
        standing=fact.standing.value,
        standing_stated=fact.standing.stated,
        source=fact.source,
        age=_age(fact.source, fact.observed_at),
        because=fact.because,
    )


def _issued_share_row(outcome: TokenMarketFacts) -> TokenFactRowResponse:
    share = outcome.issued_share

    if share is None:
        return _calculated(
            "Share of maximum supply circulating",
            None,
            because=(
                "not computed: it takes an established circulating and "
                "maximum supply, and at least one is not established."
            ),
        )

    return _calculated(
        "Share of maximum supply circulating",
        f"{share * 100:.1f}%",
        because=(
            "MOVRvest's arithmetic over the established circulating and "
            "maximum supply — not a provider observation."
        ),
    )


def _dilution_row(outcome: TokenMarketFacts) -> TokenFactRowResponse:
    ratio = outcome.fdv_to_market_cap

    if ratio is None:
        return _calculated(
            "Fully diluted valuation over market value",
            None,
            because=(
                "not computed: it takes an established fully diluted "
                "valuation and market value, and at least one is not "
                "established."
            ),
        )

    return _calculated(
        "Fully diluted valuation over market value",
        f"{ratio:.1f}×",
        because=(
            "MOVRvest's arithmetic over two established figures — how "
            "many of today's market values the eventual supply would "
            "represent at the current price. Not a provider observation."
        ),
    )


def _calculated(
    label: str,
    stated: str | None,
    because: str,
) -> TokenFactRowResponse:
    return TokenFactRowResponse(
        label=label,
        stated=stated,
        standing="calculated" if stated is not None else "absent",
        standing_stated=(
            "MOVRvest-calculated" if stated is not None else "Not computed"
        ),
        source=None,
        age=None,
        because=because,
    )


def _stated(fact: TokenFact) -> str | None:
    if fact.value is None or not fact.standing.serves_value:
        return None

    if fact.fact in _MONEY:
        return _money(fact.value)

    if fact.fact in _COUNT:
        return f"{fact.value:,.0f}"

    if fact.fact in _SIGNED_SHARE:
        return f"{fact.value * 100:+.1f}%"

    return f"{fact.value:,.2f}"


def _money(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    return f"${value:,.0f}"


def _age(source: str | None, observed_at: datetime | None) -> str | None:
    """The observation's age, worded the way every reading on the page is."""

    if source is None or observed_at is None:
        return None

    return Provenance(source=source, observed_at=observed_at).stated()
