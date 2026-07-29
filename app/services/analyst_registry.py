from collections.abc import Mapping
from typing import Any

from app.domain.research_plan import AnalystKey


class AnalystRegistry:
    """Resolves stable analyst keys into registered analyst instances."""

    def __init__(
        self,
        analysts: Mapping[AnalystKey, Any],
    ) -> None:
        self._analysts = dict(analysts)

    def get(self, key: AnalystKey) -> Any:
        try:
            return self._analysts[key]
        except KeyError as exc:
            raise KeyError(f"No analyst registered for key: {key.value}") from exc
