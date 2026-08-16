"""Absence is not neutral — the guards for the first warrant consumer.

Neutral is an analytical conclusion. These tests fix the difference
between drawing it and manufacturing it, and they are written against
the domain types so that renaming a variable cannot make them pass.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.domain.company_facts import CompanyFacts
from app.domain.daily_change import ChangeBasis, DailyChange
from app.domain.market_snapshot import MarketQuote
from app.domain.provenance import Provenance
from app.domain.provider_claim import ClaimAbsence
from app.domain.provider_translation import TranslationWarrant
from app.services.company_facts_service import CompanyFactsService
from app.services.momentum_signal_service import (
    ELIGIBLE_WARRANTS,
    MomentumSignalService,
)

READ_ON = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


def _facts(change: DailyChange | None = None, **kwargs: object) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Co",
        asset_type="stock",
        exchange="TEST",
        daily_change=change,
        **kwargs,  # type: ignore[arg-type]
    )


def _measured(
    percent: float,
    warrant: TranslationWarrant = TranslationWarrant.ASSUMED,
    basis: ChangeBasis = ChangeBasis.SAME_SESSION,
) -> DailyChange:
    return DailyChange.measured(percent, warrant=warrant, basis=basis)


class TestAbsenceIsNotNeutral:
    """The defect this slice exists to repair."""

    def test_insufficient_history_cannot_become_neutral(self) -> None:
        change = DailyChange.unmeasured(
            ClaimAbsence.INSUFFICIENT_HISTORY,
            warrant=TranslationWarrant.ASSUMED,
        )

        signal = MomentumSignalService().build(_facts(change))

        assert signal.trend == "UNKNOWN"
        assert signal.confidence == 20
        assert "0.00%" not in signal.evidence[0].statement

    def test_a_malformed_stored_value_cannot_become_neutral(self) -> None:
        change = DailyChange.unmeasured(
            ClaimAbsence.MALFORMED_STORED_VALUE,
            warrant=TranslationWarrant.ASSUMED,
        )

        signal = MomentumSignalService().build(_facts(change))

        assert signal.trend == "UNKNOWN"

    def test_an_unavailable_provider_cannot_become_neutral(self) -> None:
        change = DailyChange.unmeasured(
            ClaimAbsence.PROVIDER_UNAVAILABLE,
            warrant=TranslationWarrant.ASSUMED,
        )

        assert MomentumSignalService().build(_facts(change)).trend == "UNKNOWN"

    def test_every_absence_reaches_unknown(self) -> None:
        """No member of the vocabulary may quietly reach a band."""

        for absence in ClaimAbsence:
            change = DailyChange.unmeasured(absence, warrant=TranslationWarrant.ASSUMED)

            signal = MomentumSignalService().build(_facts(change))

            assert signal.trend == "UNKNOWN", absence

    def test_the_refusal_names_the_absence(self) -> None:
        change = DailyChange.unmeasured(
            ClaimAbsence.INSUFFICIENT_HISTORY,
            warrant=TranslationWarrant.ASSUMED,
        )

        statement = MomentumSignalService().build(_facts(change)).evidence[0].statement

        assert "too little history" in statement


class TestZeroIsStillAValue:
    """A genuine flat session must survive the repair."""

    def test_a_measured_zero_is_neutral(self) -> None:
        signal = MomentumSignalService().build(_facts(_measured(0.0)))

        assert signal.trend == "NEUTRAL"
        assert signal.strength == "WEAK"
        assert signal.confidence == 60

    def test_a_measured_zero_and_an_absence_are_different_signals(self) -> None:
        """The distinction the whole slice turns on."""

        measured = MomentumSignalService().build(_facts(_measured(0.0)))

        manufactured = MomentumSignalService().build(
            _facts(
                DailyChange.unmeasured(
                    ClaimAbsence.INSUFFICIENT_HISTORY,
                    warrant=TranslationWarrant.ASSUMED,
                )
            )
        )

        assert measured.trend == "NEUTRAL"
        assert manufactured.trend == "UNKNOWN"
        assert measured.confidence != manufactured.confidence

    def test_a_daily_change_refuses_to_hold_both_a_value_and_an_absence(self) -> None:
        with pytest.raises(ValueError, match="never both"):
            DailyChange(
                percent=0.0,
                warrant=TranslationWarrant.ASSUMED,
                absence=ClaimAbsence.FIELD_ABSENT,
            )

    def test_a_daily_change_refuses_to_hold_neither(self) -> None:
        with pytest.raises(ValueError, match="no value and no reason"):
            DailyChange(percent=None, warrant=TranslationWarrant.ASSUMED)


class TestBandsAreUnchanged:
    """The thresholds did not move, and this proves the claim."""

    @pytest.mark.parametrize(
        ("percent", "trend", "strength", "confidence"),
        [
            (2.5, "BULLISH", "STRONG", 85),
            (2.0, "BULLISH", "STRONG", 85),
            (1.0, "BULLISH", "MODERATE", 70),
            (0.5, "BULLISH", "MODERATE", 70),
            (0.4, "NEUTRAL", "WEAK", 60),
            (0.0, "NEUTRAL", "WEAK", 60),
            (-0.4, "NEUTRAL", "WEAK", 60),
            (-0.5, "BEARISH", "MODERATE", 70),
            (-1.0, "BEARISH", "MODERATE", 70),
            (-2.0, "BEARISH", "STRONG", 85),
            (-3.0, "BEARISH", "STRONG", 85),
        ],
    )
    def test_every_band_boundary_is_where_it_was(
        self,
        percent: float,
        trend: str,
        strength: str,
        confidence: int,
    ) -> None:
        signal = MomentumSignalService().build(_facts(_measured(percent)))

        assert (signal.trend, signal.strength, signal.confidence) == (
            trend,
            strength,
            confidence,
        )


class TestWarrantEligibility:
    """A consumer must state what authority it requires."""

    def test_an_unknown_warrant_cannot_become_an_analytical_opinion(self) -> None:
        """Numerically plausible, semantically unreadable."""

        change = _measured(2.5, warrant=TranslationWarrant.UNKNOWN)

        signal = MomentumSignalService().build(_facts(change))

        assert signal.trend == "UNKNOWN"
        assert "cannot be read as a price move" in signal.evidence[0].statement

    @pytest.mark.parametrize(
        "warrant",
        [
            TranslationWarrant.VERIFIED,
            TranslationWarrant.VALIDATED,
            TranslationWarrant.DECLARED,
            TranslationWarrant.ASSUMED,
        ],
    )
    def test_every_eligible_warrant_is_banded(
        self, warrant: TranslationWarrant
    ) -> None:
        signal = MomentumSignalService().build(_facts(_measured(2.5, warrant=warrant)))

        assert signal.trend == "BULLISH"

    def test_eligibility_is_membership_not_an_ordering(self) -> None:
        """No 'at least DECLARED' — the set is enumerated, and UNKNOWN is out."""

        assert ELIGIBLE_WARRANTS == frozenset(
            {
                TranslationWarrant.VERIFIED,
                TranslationWarrant.VALIDATED,
                TranslationWarrant.DECLARED,
                TranslationWarrant.ASSUMED,
            }
        )

        assert TranslationWarrant.UNKNOWN not in ELIGIBLE_WARRANTS

    def test_the_consumer_owns_the_requirement(self) -> None:
        """The input does not know which warrants are good enough."""

        change = _measured(2.5, warrant=TranslationWarrant.ASSUMED)

        assert change.admissible_under(ELIGIBLE_WARRANTS)
        assert not change.admissible_under(frozenset({TranslationWarrant.VERIFIED}))


class TestTemporalClaims:
    """The sentence may not claim more than the dates support."""

    def test_a_same_session_move_may_say_today(self) -> None:
        signal = MomentumSignalService().build(
            _facts(_measured(2.5, basis=ChangeBasis.SAME_SESSION))
        )

        assert "today" in signal.evidence[0].statement

    def test_a_last_session_move_must_not_say_today(self) -> None:
        """A Friday close read on a Sunday is not today's move."""

        signal = MomentumSignalService().build(
            _facts(_measured(2.5, basis=ChangeBasis.LAST_AVAILABLE_SESSION))
        )

        statement = signal.evidence[0].statement

        assert "today" not in statement
        assert "last session" in statement

    def test_an_undated_move_must_not_say_today(self) -> None:
        signal = MomentumSignalService().build(
            _facts(_measured(2.5, basis=ChangeBasis.UNKNOWN_SESSION))
        )

        assert "today" not in signal.evidence[0].statement

    def test_only_one_basis_establishes_today(self) -> None:
        establishing = [basis for basis in ChangeBasis if basis.establishes_today]

        assert establishing == [ChangeBasis.SAME_SESSION]

    def test_a_request_timestamp_alone_cannot_justify_today(self) -> None:
        """The composition rule: no session date, no temporal claim.

        The quote is read now, so its acquisition time is today — and
        that is precisely the evidence #133 found substituting for the
        close's own date. Without the close's date the basis must not
        resolve to SAME_SESSION.
        """

        quote = MarketQuote(
            symbol="TEST",
            name="Test",
            price=10.0,
            change_percent=2.5,
            session_date=None,
            reading=Provenance(source="Yahoo Finance", observed_at=READ_ON),
        )

        change = CompanyFactsService._daily_change(quote)

        assert change is not None
        assert change.basis is ChangeBasis.UNKNOWN_SESSION
        assert "today" not in change.window


class TestTheCompositionFromAQuote:
    """What the live path actually builds."""

    def test_a_same_day_close_establishes_today(self) -> None:
        quote = MarketQuote(
            symbol="TEST",
            name="Test",
            price=10.0,
            change_percent=1.0,
            session_date=date(2026, 8, 16),
            reading=Provenance(source="Yahoo Finance", observed_at=READ_ON),
        )

        change = CompanyFactsService._daily_change(quote)

        assert change is not None
        assert change.basis is ChangeBasis.SAME_SESSION

    def test_an_earlier_close_establishes_the_last_session(self) -> None:
        quote = MarketQuote(
            symbol="TEST",
            name="Test",
            price=10.0,
            change_percent=1.0,
            session_date=date(2026, 8, 14),
            reading=Provenance(source="Yahoo Finance", observed_at=READ_ON),
        )

        change = CompanyFactsService._daily_change(quote)

        assert change is not None
        assert change.basis is ChangeBasis.LAST_AVAILABLE_SESSION

    def test_a_manufactured_zero_arrives_as_an_absence(self) -> None:
        """The end-to-end shape of the repaired defect."""

        quote = MarketQuote(
            symbol="TEST",
            name="Test",
            price=10.0,
            change_percent=0.0,
            change_absence=ClaimAbsence.INSUFFICIENT_HISTORY,
            reading=Provenance(source="Yahoo Finance", observed_at=READ_ON),
        )

        change = CompanyFactsService._daily_change(quote)

        assert change is not None
        assert not change.is_measured
        assert MomentumSignalService().build(_facts(change)).trend == "UNKNOWN"

    def test_the_registry_supplies_the_warrant(self) -> None:
        """Not hardcoded: the composition reads the governed translation."""

        quote = MarketQuote(
            symbol="TEST",
            name="Test",
            price=10.0,
            change_percent=1.0,
            reading=Provenance(source="Yahoo Finance", observed_at=READ_ON),
        )

        change = CompanyFactsService._daily_change(quote)

        assert change is not None
        assert change.warrant is TranslationWarrant.ASSUMED


class TestTheLegacyFloatPath:
    """Twenty callers pass a bare float, and it still means what it said."""

    def test_a_bare_float_is_read_as_a_measured_change(self) -> None:
        signal = MomentumSignalService().build(_facts(daily_change_pct=1.0))

        assert signal.trend == "BULLISH"

    def test_a_bare_none_is_still_unknown(self) -> None:
        signal = MomentumSignalService().build(_facts(daily_change_pct=None))

        assert signal.trend == "UNKNOWN"

    def test_the_rich_field_wins_where_both_are_present(self) -> None:
        """The live path fills both; the one carrying standing governs."""

        facts = _facts(
            DailyChange.unmeasured(
                ClaimAbsence.INSUFFICIENT_HISTORY,
                warrant=TranslationWarrant.ASSUMED,
            ),
            daily_change_pct=0.0,
        )

        assert MomentumSignalService().build(facts).trend == "UNKNOWN"


class TestUnrelatedSignalsAreUntouched:
    """One vertical slice: no other consumer learned to read a warrant."""

    def test_no_other_signal_service_consults_a_warrant(self) -> None:
        import inspect

        from app.services import (
            quality_signal_service,
            risk_signal_service,
            value_signal_service,
        )

        for module in (
            value_signal_service,
            quality_signal_service,
            risk_signal_service,
        ):
            source = inspect.getsource(module)

            assert "TranslationWarrant" not in source, module.__name__
            assert "ELIGIBLE_WARRANTS" not in source, module.__name__
