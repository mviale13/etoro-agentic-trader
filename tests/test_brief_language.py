"""The one place a brief's numbers are put into words.

The dashboard used to band these figures itself, in TypeScript, with
thresholds nobody on the backend had agreed to. These tests pin the
canonical wording so every surface describes the same number the same way.
"""

from app.renderers.brief_language import (
    conviction_label,
    health_label,
    urgency_band,
)


class TestHealthLabel:
    def test_a_strong_score_is_healthy(self) -> None:
        assert health_label(0.9) == "Healthy"

    def test_the_healthy_band_starts_at_85(self) -> None:
        assert health_label(0.85) == "Healthy"
        assert health_label(0.849) == "Stable"

    def test_the_stable_band_starts_at_70(self) -> None:
        assert health_label(0.70) == "Stable"
        assert health_label(0.699) == "Needs attention"

    def test_the_attention_band_starts_at_50(self) -> None:
        assert health_label(0.50) == "Needs attention"
        assert health_label(0.499) == "At risk"

    def test_a_collapsed_score_is_at_risk(self) -> None:
        assert health_label(0.0) == "At risk"


class TestConvictionLabel:
    def test_very_high_starts_at_85(self) -> None:
        assert conviction_label(85) == "Very High Conviction"
        assert conviction_label(84) == "High Conviction"

    def test_high_starts_at_70(self) -> None:
        assert conviction_label(70) == "High Conviction"
        assert conviction_label(69) == "Moderate Conviction"

    def test_moderate_starts_at_50(self) -> None:
        assert conviction_label(50) == "Moderate Conviction"
        assert conviction_label(49) == "Low Conviction"

    def test_no_conviction_is_low(self) -> None:
        assert conviction_label(0) == "Low Conviction"


class TestUrgencyBand:
    def test_now_starts_at_point_six(self) -> None:
        assert urgency_band(0.6) == "now"
        assert urgency_band(0.59) == "today"

    def test_today_starts_at_point_three(self) -> None:
        assert urgency_band(0.3) == "today"
        assert urgency_band(0.29) == "monitor"

    def test_a_quiet_priority_is_monitored(self) -> None:
        assert urgency_band(0.0) == "monitor"

    def test_an_unmeasured_agreement_is_maximally_urgent(self) -> None:
        # The brief builder derives urgency as 1 - confidence, treating a
        # case nobody could review as the most urgent thing it can say.
        assert urgency_band(1.0) == "now"
