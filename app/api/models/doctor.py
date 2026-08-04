from pydantic import BaseModel


class DoctorResponse(BaseModel):
    health: int
    diagnosis: list[str]
    prescriptions: list[str]
    projected_health: int
    confidence: int
