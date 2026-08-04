from fastapi import APIRouter

from app.api.models.doctor import DoctorResponse
from app.services.doctor_snapshot_service import DoctorSnapshotService
from app.services.portfolio_health_service import PortfolioHealthService

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("", response_model=DoctorResponse)
def get_doctor() -> DoctorResponse:
    health = PortfolioHealthService().build()

    snapshot = DoctorSnapshotService().build(health)

    return DoctorResponse(
        health=snapshot.health,
        diagnosis=list(snapshot.diagnosis),
        prescriptions=list(snapshot.prescriptions),
        projected_health=snapshot.projected_health,
        confidence=snapshot.confidence,
    )
