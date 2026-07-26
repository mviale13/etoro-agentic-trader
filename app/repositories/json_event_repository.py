import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.event import Event
from app.repositories.event_repository import EventRepository


class JsonEventRepository(EventRepository):
    def __init__(
        self,
        directory: Path | str = "data/events",
    ) -> None:
        self.directory = Path(directory)

    def save(self, event: Event) -> None:
        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = self._path_for(event.timestamp)
        records = self._read_records(path)

        records.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "symbol": event.symbol,
                "payload": event.payload,
            }
        )

        path.write_text(
            json.dumps(
                records,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def load_all(self) -> list[Event]:
        if not self.directory.exists():
            return []

        events: list[Event] = []

        for path in sorted(self.directory.glob("*.json")):
            events.extend(
                self._events_from_records(
                    self._read_records(path),
                )
            )

        return sorted(
            events,
            key=lambda event: event.timestamp,
        )

    def load_latest(
        self,
        limit: int = 1,
    ) -> list[Event]:
        if limit <= 0:
            return []

        events = self.load_all()

        return list(
            reversed(events[-limit:]),
        )

    def _path_for(
        self,
        timestamp: datetime,
    ) -> Path:
        filename = f"{timestamp.date().isoformat()}.json"

        return self.directory / filename

    @staticmethod
    def _read_records(
        path: Path,
    ) -> list[dict[str, Any]]:
        if not path.exists():
            return []

        content = path.read_text(
            encoding="utf-8",
        ).strip()

        if not content:
            return []

        data = json.loads(content)

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON list in {path}.")

        return data

    @staticmethod
    def _events_from_records(
        records: list[dict[str, Any]],
    ) -> list[Event]:
        return [
            Event(
                timestamp=datetime.fromisoformat(
                    str(record["timestamp"]),
                ),
                event_type=str(record["event_type"]),
                symbol=(
                    str(record["symbol"]) if record.get("symbol") is not None else None
                ),
                payload=dict(record.get("payload", {})),
            )
            for record in records
        ]
