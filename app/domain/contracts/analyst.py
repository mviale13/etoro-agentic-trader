"""Framework-independent contract implemented by every MOVRvest analyst."""

from typing import Protocol, TypeVar, runtime_checkable

ContextT_contra = TypeVar("ContextT_contra", contravariant=True)
ReportT_co = TypeVar("ReportT_co", covariant=True)


@runtime_checkable
class Analyst(Protocol[ContextT_contra, ReportT_co]):
    """Produce factual analysis without making the final recommendation."""

    @property
    def name(self) -> str:
        """Return the stable analyst identifier."""
        ...

    def analyze(self, context: ContextT_contra) -> ReportT_co:
        """Analyze the supplied context and return a typed report."""
        ...
