from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BrainMetadata:
    generated_at: datetime
    version: str
