"""The Capital Action Envelope, end to end — owner ruling 2026-08-23.

P1 #1 of the golden-path acceptance. The envelope's price gate read
`brain.market.quotes` — the SPY/QQQ/IWM market strip, a collection that
cannot contain a holding — so every capital-asking course ever recorded
refused with *"no market quote was acquired this cycle"* beside its own
record saying 26 priced of 26. The acquisition stage owns the quotes it
took; these pin that they travel, that they are the exact observations,
and that every existing refusal still refuses.

Nothing about the envelope contract changes here: capacity arithmetic,
security-risk ceilings, STARTER/STANDARD limits, the drawdown and
staleness gates, the crypto refusal and conviction's structural
exclusion are all the merged behaviour, exercised through the real
`envelope_for`.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.capital_envelope import (
    EnvelopeKind,
    envelope_for,
    price_observation_for,
    security_risk_ceiling_for,
)
from app.domain.market_acquisition import AcquiredSecurity, MarketAcquisition
from app.domain.market_snapshot import MarketQuote
from app.domain.provenance import Provenance
from tests.test_capital_action_envelope import (
    MOMENT,
    capacity,
    observed_portfolio,
    policy,
    quote_for,
)

CALM = security_risk_ceiling_for(
    policy=policy(), volatility_band="LOW", drawdown_band="LOW"
)


def envelope(course: str, quote: MarketQuote | None, **overrides):
    """One course through the real contract, with one quote map entry."""

    batch = (quote,) if quote is not None else ()
    quotes = {held.symbol.upper().strip(): held for held in batch}
    symbol = overrides.pop("symbol", "DIS")
    resolved = quotes.get(symbol.upper().strip())

    return envelope_for(
        symbol=symbol,
        course=course,
        policy=policy(),
        capacity=overrides.pop("cap", capacity()),
        named_gaps=overrides.pop("gaps", ()),
        quality_authority=overrides.pop("authority", None) or _grounded(),
        hard_floor_passes=True,
        price=price_observation_for(
            symbol=symbol, quote=resolved, policy=policy(), now=MOMENT
        ),
        portfolio_as_of="eToro account response received at 2026-08-19 14:58 UTC",
        drawdown_depth_pct=overrides.pop("drawdown", 2.0),
        is_equity=overrides.pop("equity", True),
        security_risk=overrides.pop("security_risk", CALM),
        **overrides,
    )


def _grounded():
    from app.domain.capital_envelope import QualityAuthority

    return QualityAuthority.GROUNDED


# ── 1 & 2: a cycle's own quote computes the envelope ────────────────


def test_a_fresh_holding_quote_computes_its_add_envelope() -> None:
    """Control 1: DIS no longer says no quote was acquired."""

    result = envelope("add", quote_for("DIS", minutes_old=2.0, price=107.78))

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct is not None and result.final_pct > 0
    assert "no market quote" not in result.stated


def test_a_venue_suffixed_holding_is_resolved_by_its_canonical_symbol() -> None:
    """Control 2: BNP.PA keys on MOVRvest's symbol, not the vendor's."""

    result = envelope("add", quote_for("BNP.PA", minutes_old=2.0), symbol="BNP.PA")

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.symbol == "BNP.PA"


def test_a_funded_open_candidate_receives_an_envelope() -> None:
    """Control 3: an OPEN course is a capital course."""

    result = envelope("open", quote_for("MSFT", minutes_old=2.0), symbol="MSFT")

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct is not None


def test_a_reduce_course_still_produces_its_compliance_floor() -> None:
    result = envelope(
        "reduce", quote_for("DIS", minutes_old=2.0), cap=capacity(weight=25.0)
    )

    assert result.kind is EnvelopeKind.REDUCTION_FLOOR
    assert result.final_pct == 5.0


# ── 4 & 5: every existing refusal still refuses ─────────────────────


def test_a_genuinely_absent_quote_refuses_in_the_existing_words() -> None:
    """Control 4: the typed refusal is unchanged, and now truthful."""

    result = envelope("add", None)

    assert result.kind is EnvelopeKind.REFUSED
    assert "no market quote for DIS was acquired this cycle" in result.because


def test_a_stale_quote_refuses() -> None:
    result = envelope("add", quote_for("DIS", minutes_old=40.0))

    assert result.kind is EnvelopeKind.REFUSED
    assert "older than the policy" in result.because


def test_an_undated_quote_refuses() -> None:
    result = envelope("add", quote_for("DIS", dated=False))

    assert result.kind is EnvelopeKind.REFUSED


def test_a_last_known_quote_refuses() -> None:
    result = envelope("add", quote_for("DIS", minutes_old=2.0, last_known=True))

    assert result.kind is EnvelopeKind.REFUSED
    assert "recency cannot repair a degraded reading" in result.because


def test_a_future_dated_quote_refuses() -> None:
    future = MarketQuote(
        symbol="DIS",
        name="DIS",
        price=107.78,
        change_percent=0.0,
        reading=Provenance(
            source="Yahoo Finance", observed_at=MOMENT + timedelta(minutes=5)
        ),
    )

    result = envelope("add", future)

    assert result.kind is EnvelopeKind.REFUSED
    assert "clock fault" in result.because


def test_a_naive_observation_time_refuses() -> None:
    naive = MarketQuote(
        symbol="DIS",
        name="DIS",
        price=107.78,
        change_percent=0.0,
        reading=Provenance(
            source="Yahoo Finance", observed_at=datetime(2026, 8, 19, 15, 0)
        ),
    )

    result = envelope("add", naive)

    assert result.kind is EnvelopeKind.REFUSED
    assert "carries no timezone" in result.because


# ── 6: crypto stays refused even with an established spot price ─────


def test_crypto_remains_refused_by_its_own_contract() -> None:
    """Control 6: a priced token is still outside v1 sizing."""

    result = envelope(
        "add",
        quote_for("HYPE", minutes_old=2.0),
        symbol="HYPE",
        equity=False,
        crypto_price_established=True,
    )

    assert result.kind is EnvelopeKind.REFUSED
    assert "does not size cryptocurrencies" in result.because
    assert result.final_pct is None


# ── 7 & 8: the acquisition's own observations, carried verbatim ─────


def test_the_acquisition_carries_its_quotes_verbatim() -> None:
    """Control 7: byte-equal in value and provenance."""

    quote = quote_for("DIS", minutes_old=2.0, price=107.78)

    acquisition = MarketAcquisition(
        securities=(
            AcquiredSecurity(
                symbol="DIS", priced=True, fundamentals=True, calendar=True
            ),
        ),
        instruments=(),
        vix=None,
        quotes=(quote,),
    )

    carried = {q.symbol.upper().strip(): q for q in acquisition.quotes}

    assert carried["DIS"] is quote
    assert carried["DIS"].price == 107.78
    assert carried["DIS"].reading == quote.reading


def test_a_failed_batch_carries_no_quotes_and_refuses() -> None:
    """Control 8's other half: absence stays absence, never a fetch."""

    acquisition = MarketAcquisition(
        securities=(
            AcquiredSecurity(
                symbol="DIS", priced=False, fundamentals=False, calendar=None
            ),
        ),
        instruments=(),
        vix=None,
    )

    assert acquisition.quotes == ()

    carried = {q.symbol.upper().strip(): q for q in acquisition.quotes}

    assert envelope("add", carried.get("DIS")).kind is EnvelopeKind.REFUSED


def test_priced_true_is_not_a_quote() -> None:
    """The flag says the store holds one; the envelope needs the figure.

    An `AcquiredSecurity` marked priced with no quote in the batch must
    still refuse — otherwise the gate is back to trusting a boolean.
    """

    acquisition = MarketAcquisition(
        securities=(
            AcquiredSecurity(
                symbol="DIS", priced=True, fundamentals=True, calendar=True
            ),
        ),
        instruments=(),
        vix=None,
        quotes=(),
    )

    carried = {q.symbol.upper().strip(): q for q in acquisition.quotes}

    assert acquisition.securities[0].priced is True
    assert envelope("add", carried.get("DIS")).kind is EnvelopeKind.REFUSED


def test_the_evaluation_clock_never_substitutes_for_the_observation_time() -> None:
    """The price is aged from the provider's own moment, not `now`."""

    quote = quote_for("DIS", minutes_old=40.0)

    fresh_by_evaluation_clock = price_observation_for(
        symbol="DIS", quote=quote, policy=policy(), now=quote.reading.observed_at
    )
    aged_properly = price_observation_for(
        symbol="DIS", quote=quote, policy=policy(), now=MOMENT
    )

    assert fresh_by_evaluation_clock.fresh is True
    assert aged_properly.fresh is False, "the provider's moment decides"


# ── 9: the security-risk ceiling now reaches a real course ──────────


def test_a_severe_security_receives_its_ceiling_on_a_real_course() -> None:
    """#236's ceilings could never compose while the price gate refused."""

    severe = security_risk_ceiling_for(
        policy=policy(), volatility_band="SEVERE", drawdown_band="MODERATE"
    )

    result = envelope(
        "add", quote_for("AMD", minutes_old=2.0), symbol="AMD", security_risk=severe
    )

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.security_risk_ceiling_pct == 1.0
    assert result.security_risk_capped is True
    assert "under your security-risk policy" in result.stated.lower()


def test_the_portfolio_drawdown_gate_still_precedes_a_priced_course() -> None:
    result = envelope("add", quote_for("DIS", minutes_old=2.0), drawdown=25.0)

    assert result.kind is EnvelopeKind.REFUSED
    assert "drawdown budget" in result.because


def test_conviction_remains_structurally_excluded() -> None:
    import inspect

    parameters = inspect.signature(envelope_for).parameters

    assert "conviction" not in parameters
    assert not any("confidence" in name for name in parameters)


def test_the_portfolio_clock_is_still_a_receipt_clock() -> None:
    """Two different kinds of fact, unchanged by this slice."""

    observation = observed_portfolio(minutes_old=2.0)

    assert "receipt time" in observation.as_of
    assert "eToro states no account observation time" in observation.as_of
