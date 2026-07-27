from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MemoryEvent:
    timestamp: datetime
    event_type: str
    subject: str
    value: str
