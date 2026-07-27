from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Observation:
    title: str
    message: str
    category: str
