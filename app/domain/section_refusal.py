"""Why one numbered section could not be supplied from a document.

An empty section is not a fact about a company, and until now this
platform had no way to say which of four different things had happened.
Barclays' 20-F is 3.7 million characters of a real annual report, and
Citigroup's 10-K is 1.53 million; both would hand a surface an empty
string, and a surface that expects prose renders that as *"the company
describes no business"* — a claim about the filer, produced by a limit
of this reader. That is Invariant 1 inverted, and this module is the
instrument that stops it.

**The reason is about the document, never about the company.** Each
member below names what was observed in the filing and what capability
is missing, and each says in its own words that no claim about the
business follows from it.

**A reason is established, never inferred from emptiness.** Producing
one requires structural evidence that a particular case applies; "the
text came back empty" is the symptom every case shares and evidence for
none of them.

This is deliberately *not* a `KnowledgeState`. The state says what
operational situation occurred; this says why this document could not
supply this section. `PrimarySourceUnavailable` stays what it was — the
provider holds no document, a gap in coverage — because a document that
was retrieved and parsed successfully is not a coverage gap, and telling
a reader to try another provider would be telling them to do the one
thing that cannot help.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SectionRefusal(StrEnum):
    """Which of the four things happened to one expected section."""

    #: The filer represents this section through an index of item
    #: numbers against page ranges or captions in another component.
    #: Measured: Citigroup prints `FORM 10-K CROSS-REFERENCE INDEX —
    #: Item Number | Page` with rows like *"1. Business 4-36, 121-127,
    #: 129, 160-164, 299-300"*, and Barclays and NatWest do the same on
    #: a 20-F. The content exists; following page ranges into another
    #: component is a capability this platform does not have.
    CROSS_REFERENCE_INDEX = "cross_reference_index"

    #: The form is mapped and the filing prints no candidate for the
    #: expected section, with no cross-reference index to explain it.
    EXPECTED_SECTION_NOT_PRINTED = "expected_section_not_printed"

    #: Candidates were discovered and no coherent structural location
    #: survived. The distinction from the case above is the whole point:
    #: one is a filing that did not print the section, the other is a
    #: reader that could not settle where it began.
    SECTION_LOCATION_REFUSED = "section_location_refused"

    #: The regulator's form carries no section mapping on this platform.
    #: Never a default: a form this platform has not mapped is refused
    #: by name rather than read with another form's item numbers.
    UNSUPPORTED_FORM = "unsupported_form"


@dataclass(frozen=True, slots=True)
class RefusedSection:
    """One expected section, and why this document could not supply it.

    Carried on the section rather than raised, because a document whose
    business section cannot be read may still carry audited financial
    statements this platform reads perfectly well. Citigroup is exactly
    that: its Item 1 is a page range, and its income statement, balance
    sheet and cash flow statement are printed in full.
    """

    reason: SectionRefusal

    #: What was expected, in this platform's own words — "business
    #: description", "performance discussion". Named semantically rather
    #: than as an item number, because the item differs by form.
    expected: str

    #: The regulator's designation for the filing, as it was stated.
    #: Empty where the publisher has none.
    form: str = ""

    #: How the document was cited, for a reader who wants to check.
    filing: str = ""

    #: What was seen in the document. The producer's own observation —
    #: never a guess, and never a restatement of the reason.
    observed: str = ""

    def stated(self) -> str:
        """The refusal as an investor reads it.

        Five things, in this order: the filing is real, what was
        expected, what was observed, what capability is missing, and
        that no claim about the company follows. The last is not
        decoration — it is the sentence that keeps a limit of this
        reader from being read as a fact about the filer.

        **The first of the five is load-bearing and is worded the same
        way in every branch.** A refusal that opens by describing what
        the document does *not* print, without first establishing that
        the document is there, reads as a statement about the filer's
        disclosure. Every member says the filing *is available* before
        it says anything else, and a test pins that on all of them.
        """

        named = f"{self.form} filing" if self.form else "filing"
        cited = f" ({self.filing})" if self.filing else ""
        seen = f" {self.observed}" if self.observed else ""

        if self.reason is SectionRefusal.CROSS_REFERENCE_INDEX:
            return (
                f"The SEC {named}{cited} is available, but its "
                f"{self.expected} is supplied through a cross-reference "
                "index pointing to content outside the document component "
                f"this platform reads.{seen} MOVRvest did not follow those "
                "page or component references, so no "
                f"{self.expected} was established from this filing. "
                "Nothing follows from this about what the company does."
            )

        if self.reason is SectionRefusal.EXPECTED_SECTION_NOT_PRINTED:
            return (
                f"The SEC {named}{cited} is available, and it prints no "
                f"section this platform could read as the {self.expected}, "
                "nor a cross-reference index explaining where it went."
                f"{seen} No "
                f"{self.expected} was established from this filing. "
                "Nothing follows from this about what the company does."
            )

        if self.reason is SectionRefusal.SECTION_LOCATION_REFUSED:
            return (
                f"The SEC {named}{cited} is available, and it prints "
                f"candidates for the {self.expected} this platform could not "
                f"resolve into a section it can say begins anywhere.{seen} "
                "It is refused rather "
                "than guessed at, so no "
                f"{self.expected} was established from this filing. "
                "Nothing follows from this about what the company does."
            )

        # The form is named rather than articled — "regulator form 8-K",
        # never "a 8-K" — because the designation is a token the
        # regulator assigned and not a noun this sentence may inflect.
        # An unstated designation is said as an absence and never
        # papered over with the word "filing" standing in for a form.
        mapping = (
            f"this platform has no section mapping for regulator form {self.form}"
            if self.form
            else (
                "no regulator form designation was supplied with it, so this "
                "platform has no section mapping to apply"
            )
        )

        return (
            f"The SEC filing{cited} is available, but {mapping}. It "
            f"therefore did not look for or establish a {self.expected} in "
            f"this document.{seen} Nothing follows from this about what the "
            "company does."
        )
