"""What every citation in this platform is held to, whatever its shape.

Two things belong here because they are one idea used twice. A citation
can fail in two independent ways, and the second is the one that hides:

- **Evidence existence** — the cited content is in the source. A quoted
  span is checked against the document; a cell address resolves to a
  cell. This is what grounding establishes.
- **Evidence applicability** — the cited content supports the *specific*
  claim it was cited for. A column header can be exactly present and
  evidence no revenue. A sentence about restated prior-year figures can
  be exactly present and describe no segment.

Existence without applicability is the defect this platform has now met
three times: in a genuine filing about the wrong company, in a genuine
column header cited for a segment's revenue, and in a genuine footnote
cited as three different segments' description. Each time the evidence
was real and the *relationship* was unproven.
"""

from __future__ import annotations

import re

_NOISE = re.compile(r"[^a-z0-9]+")


class EvidenceNotApplicable(Exception):
    """The citation is real and does not support the claim it was given for.

    Deliberately not "the evidence is missing". The words are in the
    document, or the address resolves to a cell; what is untrue is the
    relationship claimed over them. A reader told "no evidence" would go
    looking for some, and there is plenty — it just does not say this.
    """


def normalised(text: str) -> str:
    """
    Text reduced to the characters that carry meaning.

    The comparison rule used wherever this platform checks that something
    it was told matches something a document printed. A filing's markup
    leaves stray spacing inside words — "B USINESS" is a real heading —
    so an exact match would reject content that is genuinely present.
    Removing everything but letters and digits keeps the check strict
    about the words and their order while forgiving the typography the
    document arrived with.
    """

    return _NOISE.sub("", text.casefold())
