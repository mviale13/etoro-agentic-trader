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

    Letters means *letters*, not ASCII. This rule and the indexed fold
    beside it in `prose_evidence` are two halves of one comparison, and
    they disagreed for years without a symptom: the old `[a-z0-9]` form
    deleted every accented character from the needle while the index
    kept them in the haystack, so a span quoted from German or French
    prose — "conçoit", "Geschäftsmodell" — was refused as words the
    document does not print. English filings never carried the letters
    that trigger it, which is why EDGAR reading never noticed. Folded
    per character exactly as the index folds, because "ß" becomes "ss"
    and a rule that folded the string whole would disagree with the
    index about length.
    """

    return "".join(
        folded
        for character in text
        for folded in character.casefold()
        if folded.isalnum()
    )
