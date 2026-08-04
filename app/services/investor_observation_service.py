from collections.abc import Sequence

from app.domain.observation import Observation
from app.domain.signal import Signal


class InvestorObservationService:
    def observe(self, signals: Sequence[Signal]) -> Observation:
        primary_signal = self._select_primary_signal(signals)

        if primary_signal is None:
            return Observation(
                title="Steady Course",
                message=(
                    "Your portfolio appears balanced. "
                    "Staying disciplined is often an advantage."
                ),
                category="general",
            )

        return Observation(
            title=primary_signal.title,
            message=primary_signal.message,
            category=self._category_for(primary_signal),
        )

    @staticmethod
    def _select_primary_signal(
        signals: Sequence[Signal],
    ) -> Signal | None:
        if not signals:
            return None

        severity_priority = {
            "critical": 0,
            "warning": 1,
            "info": 2,
        }

        return min(
            signals,
            key=lambda signal: severity_priority.get(
                signal.severity,
                3,
            ),
        )

    @staticmethod
    def _category_for(signal: Signal) -> str:
        categories = {
            "cash": "cash",
            "concentration": "risk",
            "diversification": "diversification",
        }

        return categories.get(
            signal.type,
            "general",
        )
