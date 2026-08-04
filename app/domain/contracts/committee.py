"""Framework-independent contract implemented by every MOVRvest committee."""

from collections.abc import Sequence
from typing import Protocol, TypeVar, runtime_checkable

ReportT_contra = TypeVar("ReportT_contra", contravariant=True)
DecisionT_co = TypeVar("DecisionT_co", covariant=True)


@runtime_checkable
class Committee(Protocol[ReportT_contra, DecisionT_co]):
    """Deliberate over analyst reports and return a typed decision."""

    @property
    def name(self) -> str:
        """Return the stable committee identifier."""
        ...

    def deliberate(self, reports: Sequence[ReportT_contra]) -> DecisionT_co:
        """Combine typed reports into a committee decision."""
        ...
