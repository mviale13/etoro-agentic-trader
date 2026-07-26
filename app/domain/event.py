from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Event:
    timestamp: datetime
    event_type: str
    symbol: str | None
    payload: dict[str, Any]
