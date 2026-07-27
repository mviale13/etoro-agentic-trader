from app.domain.doctor_snapshot import DoctorSnapshot
from app.domain.portfolio_health import PortfolioHealth


class DoctorSnapshotService:
    def build(
        self,
        health: PortfolioHealth,
    ) -> DoctorSnapshot:
        diagnosis = tuple(check.message for check in health.checks)

        prescriptions = (health.recommendation,)

        projected_health = min(
            health.overall_score + 10,
            100,
        )

        return DoctorSnapshot(
            health=health.overall_score,
            diagnosis=diagnosis,
            prescriptions=prescriptions,
            projected_health=projected_health,
            confidence=80,
        )
