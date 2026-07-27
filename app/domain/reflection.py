from dataclasses import dataclass


@dataclass(frozen=True)
class Reflection:
    title: str
    summary: str
