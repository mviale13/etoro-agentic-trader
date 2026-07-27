from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Signal:
    type: str

    severity: str

    title: str

    message: str
