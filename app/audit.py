import json
from datetime import UTC, datetime
from pathlib import Path

AUDIT_FILE = Path("audit.jsonl")


def record(event_type: str, payload: dict) -> None:
    event = {
        "created_at": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, default=str) + "\n")


def recent(limit: int = 100) -> list[dict]:
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:]][::-1]
