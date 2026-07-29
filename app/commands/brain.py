import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.services.brain_service import BrainService


def _serialize(value: Any) -> Any:
    """Convert MOVRvest domain objects into JSON-compatible values."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]

    return value


async def run() -> int:
    """Run and display the complete MOVRvest Brain pipeline."""

    brain = await BrainService().build()

    print(
        json.dumps(
            _serialize(brain),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    return 0
