from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalystObservation:
    key: str
    label: str
    value: float

    #: How this observation is evidenced, in one sentence an investor can
    #: check against the source. Empty where the number arrived without
    #: evidence a reader could follow — which is the honest state of a
    #: provider-reported figure, and exactly what distinguishes it on the
    #: page from one read off a filing.
    stated: str = ""
