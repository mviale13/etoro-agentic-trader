"""Shared wording for executive-brief surfaces.

Communication layer: these functions put words to figures the executive
layer already produced. They decide nothing — a label never feeds back
into a decision, and a dashboard renders the label it is given rather
than inventing its own thresholds.

The bands live here, in one place, so the API, the console renderer and
any future surface describe the same number with the same word.
"""

from __future__ import annotations


def health_label(score: float | None) -> str:
    """Put a word to a portfolio health score in [0, 1].

    An unmeasured score gets a word that is not a band. "At risk" and
    "Healthy" are both findings; a score nobody could compute is
    neither, and must not fall through to the bottom band.
    """

    if score is None:
        return "Not measured"

    if score >= 0.85:
        return "Healthy"

    if score >= 0.70:
        return "Stable"

    if score >= 0.50:
        return "Needs attention"

    return "At risk"


def conviction_label(conviction: int | None) -> str | None:
    """Put a word to the Artificial CIO's 0-100 conviction in a decision.

    Nothing where there is no conviction to label. "Low Conviction" is a
    judgment about a case, and a case the CIO declined to put a number on
    has not been judged that way — it has not been judged at all.
    """

    if conviction is None:
        return None

    if conviction >= 85:
        return "Very High Conviction"

    if conviction >= 70:
        return "High Conviction"

    if conviction >= 50:
        return "Moderate Conviction"

    return "Low Conviction"


def urgency_band(urgency: float) -> str:
    """Band a priority's urgency in [0, 1] into an attention queue.

    "now" asks for review today, "today" asks for review soon, and
    "monitor" reports an item the CIO is content to watch.
    """

    if urgency >= 0.6:
        return "now"

    if urgency >= 0.3:
        return "today"

    return "monitor"
