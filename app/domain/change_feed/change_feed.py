from __future__ import annotations

from dataclasses import dataclass

from .change_event import ChangeEvent


@dataclass(frozen=True, slots=True)
class ChangeFeed:
    events: tuple[ChangeEvent, ...]

    @property
    def total(self) -> int:
        return len(self.events)

    @property
    def action_required(self) -> bool:
        return any(event.action_required for event in self.events)
