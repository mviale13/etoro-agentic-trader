from dataclasses import FrozenInstanceError

import pytest

from app.domain.analyst_observation import AnalystObservation


def test_analyst_observation_is_immutable() -> None:
    observation = AnalystObservation(
        key="revenue_growth",
        label="Revenue growth",
        value=0.25,
    )

    assert observation.key == "revenue_growth"
    assert observation.label == "Revenue growth"
    assert observation.value == 0.25

    with pytest.raises(FrozenInstanceError):
        observation.value = 0.30  # type: ignore[misc]
