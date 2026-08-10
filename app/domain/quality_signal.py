from dataclasses import dataclass

from app.domain.finding import Finding
from app.domain.score_basis import Contribution


@dataclass(frozen=True, slots=True)
class QualitySignal:
    quality: str
    confidence: int
    evidence: tuple[Finding, ...]

    #: The factors that were counted, and what each was worth. Empty
    #: where nothing could be read — which is not a score of zero, and
    #: the band is `UNKNOWN` there rather than `LOW`.
    contributions: tuple[Contribution, ...] = ()

    #: Points earned, and points there were to earn. `available` counts
    #: only the factors this company's data allowed a look at, so it is
    #: a statement about the reading rather than about the business.
    earned: int = 0
    available: int = 0

    #: Points the next band up requires, or nothing at the top band.
    #: What lets a surface say that a score was capped by unreadable
    #: data rather than by the company falling short.
    next_band_needs: int | None = None

    #: The signal's own account of why it reads as it does, where it has
    #: one. Carried because the composing layer cannot know it: asked to
    #: explain an UNKNOWN, the executive builder said "the figures a
    #: business is judged on could not be read" — about Bitcoin, which is
    #: not a business and whose one scorable question was answered at the
    #: top band. Absent here, that wording still stands for the company
    #: path, where it is true.
    basis: str | None = None
