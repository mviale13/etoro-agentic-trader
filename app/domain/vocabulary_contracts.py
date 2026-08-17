"""Which accepted forms each producing contract had, so an absence can be read.

An absence is a claim about a reader: *no cell holding this concept was
located.* BQ17 made every new observation record the vocabulary
fingerprint it was read under, which says **which** contract made that
claim — and a fingerprint is one-way, so it does not say what that
contract could accept. This module closes that half.

It exists because two companies independently reached the same
deadlock. Coca-Cola holds five readings saying *no figure located* for
`total_revenue` beside five saying `Net Operating Revenues`; Union
Pacific holds five and five for `Total operating revenues`. Five against
five is no majority, so the claim is unsettled, every margin loses its
denominator, and both sit at UNKNOWN — while the newer readings are
right and the older ones were reading under a vocabulary that could not
have accepted the label they were looking at.

## What is recorded here, and what is not

One entry per **published** vocabulary of one concept: its fingerprint,
its accepted forms verbatim, the commit that introduced it, and whether
observations produced under it carry a native stamp. The forms are the
point — the fingerprint alone can prove two contracts *differ* and can
never prove that a particular label was *outside* one of them, and it is
the second question supersession turns on.

This is a record of what was, not a rule about what should be. Nothing
here reads a band, a score or a company, and it grows only when a
vocabulary is published — which is a slice with its own ruling, its own
falsification sweep and its own arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.evidence import normalised
from app.domain.financial_statements import (
    CONCEPT_LABELS,
    StatementConcept,
    concept_vocabulary_fingerprint,
    without_footnote,
)


@dataclass(frozen=True, slots=True)
class PublishedVocabulary:
    """One concept's accepted forms, as one released contract had them."""

    concept: StatementConcept
    fingerprint: str
    forms: tuple[str, ...]

    #: The commit that introduced it, so the claim is checkable.
    introduced_by: str

    #: Whether a reading produced under this contract carries a native
    #: `produced_under` stamp. False for everything before BQ17, and
    #: that is what lets an *unstamped* record be bounded: it cannot
    #: have come from a contract that stamps.
    stamps_its_readings: bool

    def accepts(self, label: str) -> bool:
        """Whether this contract could have accepted the filer's label."""

        printed = normalised(without_footnote(label))

        return any(printed == normalised(form) for form in self.forms)


#: Every `TOTAL_REVENUE` vocabulary published under statement schema 3,
#: reconstructed from the repository and fingerprinted with the live
#: function. The lineage is totally ordered — each step only adds — and
#: it is complete for the era: `git log -S` over `CONCEPT_LABELS` since
#: `301cfdf`, the commit that began schema 3, returns exactly the two
#: widenings below.
#:
#: Only `TOTAL_REVENUE` appears, because it is the only concept whose
#: vocabulary has moved in this era. A concept absent from this registry
#: has an unknown history, and §`bounded_contracts` refuses rather than
#: assuming one.
PUBLISHED: tuple[PublishedVocabulary, ...] = (
    PublishedVocabulary(
        concept=StatementConcept.TOTAL_REVENUE,
        fingerprint="ba55a427097938f3",
        introduced_by="301cfdf — schema 3 begins",
        stamps_its_readings=False,
        forms=(
            "total net revenue",
            "total net revenues",
            "total revenue",
            "total revenues",
            "net revenues",
            "net revenue",
            "revenues",
            "revenue",
            "net sales",
            "total net sales",
            "total sales and revenues",
            "total revenues and other income",
        ),
    ),
    PublishedVocabulary(
        concept=StatementConcept.TOTAL_REVENUE,
        fingerprint="3cdbddd6a1fcf0e6",
        introduced_by="6c96ea0 — BQ11 earns `net operating revenues`",
        stamps_its_readings=False,
        forms=(
            "total net revenue",
            "total net revenues",
            "total revenue",
            "total revenues",
            "net revenues",
            "net revenue",
            "revenues",
            "revenue",
            "net sales",
            "total net sales",
            "total sales and revenues",
            "total revenues and other income",
            "net operating revenues",
        ),
    ),
    PublishedVocabulary(
        concept=StatementConcept.TOTAL_REVENUE,
        fingerprint="ea9df9c5adbc7f44",
        introduced_by="c49955b — BQ19 earns `total operating revenues`",
        stamps_its_readings=True,
        forms=(
            "total net revenue",
            "total net revenues",
            "total revenue",
            "total revenues",
            "net revenues",
            "net revenue",
            "revenues",
            "revenue",
            "net sales",
            "total net sales",
            "total sales and revenues",
            "total revenues and other income",
            "net operating revenues",
            "total operating revenues",
        ),
    ),
)


def published(
    concept: StatementConcept, fingerprint: str
) -> PublishedVocabulary | None:
    """The contract with this fingerprint, where this registry knows it."""

    for vocabulary in PUBLISHED:
        if vocabulary.concept is concept and vocabulary.fingerprint == fingerprint:
            return vocabulary

    return None


def bounded_contracts(
    concept: StatementConcept, stamped: str | None
) -> tuple[PublishedVocabulary, ...] | None:
    """Every contract a reading could have been produced under, or nothing.

    Two ways a producing contract is knowable, and one way it is not:

    - **the record says so.** A stamped reading names its fingerprint,
      so the candidate set is that one contract — or nothing at all
      where the registry has never heard of it.
    - **the record's silence says so.** An unstamped reading cannot have
      come from a contract that stamps its readings, and every stored
      reading is of the current schema because the store refuses any
      other. So the candidates are the era's non-stamping contracts.
    - **neither**, where the era's history is not recorded here. Then
      the set is unbounded and this returns `None`, which every caller
      must read as *cannot prove* rather than *nothing to prove*.
    """

    era = tuple(v for v in PUBLISHED if v.concept is concept)

    if not era:
        return None

    if stamped is not None:
        known = published(concept, stamped)

        return (known,) if known is not None else None

    earlier = tuple(v for v in era if not v.stamps_its_readings)

    return earlier or None


def registry_is_current(concept: StatementConcept) -> bool:
    """Whether the live vocabulary is the newest one recorded here.

    A guard rather than a convenience. If a vocabulary is widened and
    the registry is not extended, every bound this module computes is
    silently short by one contract — so callers check first and refuse
    to reason at all rather than reason from a stale lineage.
    """

    era = [v for v in PUBLISHED if v.concept is concept]

    if not era:
        return False

    return era[-1].fingerprint == concept_vocabulary_fingerprint(concept)


def live_forms(concept: StatementConcept) -> tuple[str, ...]:
    """The accepted forms as the running code has them."""

    return CONCEPT_LABELS[concept]
