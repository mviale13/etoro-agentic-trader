from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalystObservation:
    key: str
    label: str
    value: float
