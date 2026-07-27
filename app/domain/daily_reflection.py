from dataclasses import dataclass


@dataclass(frozen=True)
class DailyReflection:
    title: str
    message: str
    source: str
