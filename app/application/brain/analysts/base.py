"""Common analyst contract."""

from __future__ import annotations

from typing import Protocol, TypeVar

from app.brain import Brain

AssessmentT_co = TypeVar(
    "AssessmentT_co",
    covariant=True,
)


class Analyst(Protocol[AssessmentT_co]):
    """Every specialist analyst evaluates the Brain."""

    def assess(
        self,
        brain: Brain,
    ) -> AssessmentT_co: ...
