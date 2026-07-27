from dataclasses import dataclass


@dataclass(frozen=True)
class DoctorSnapshot:
    health: int
    diagnosis: tuple[str, ...]
    prescriptions: tuple[str, ...]
    projected_health: int
    confidence: int
