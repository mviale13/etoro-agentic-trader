"""Framework-independent contract implemented by every MOVRvest reasoner."""

from typing import Protocol, TypeVar, runtime_checkable

ContextT_contra = TypeVar("ContextT_contra", contravariant=True)
ResultT_co = TypeVar("ResultT_co", covariant=True)


@runtime_checkable
class Reasoner(Protocol[ContextT_contra, ResultT_co]):
    """Interpret context without formatting presentation output."""

    @property
    def name(self) -> str:
        """Return the stable reasoner identifier."""
        ...

    def reason(self, context: ContextT_contra) -> ResultT_co:
        """Interpret the supplied context and return a typed result."""
        ...
