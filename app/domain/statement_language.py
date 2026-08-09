"""Which financial language a company's income statement is written in.

An observation about a document, derived from consensus figures by a
pure function. It is deliberately *not* a financial model, and nothing
here may be handed to `model_for`: what language a statement speaks and
which model should read a company are two questions, and this module
answers only the first.

**That separation is now a ruled boundary rather than a pending
connection** (`docs/architecture/FINANCIAL_DOMAIN_BOUNDARY.md`,
accepted). Financial statements establish financial language; they do
not establish prudential regulatory status. `INTEREST_BASED` is true of
mortgage REITs, which no regulator supervises as banks, and `BANK` is a
contract about deposit funding and regulatory capital. Connecting this
enum to `FinancialModel` — even as one term of a larger rule — is
forbidden until a Prudential Understanding layer exists to supply the
other term.

## Why this exists, and why it is positive

The corpus measurement that preceded it
(`docs/architecture/FINANCIAL_LANGUAGE_CORPUS.md`) established that the
*shape* of a filer's statements — no gross profit, no operating income,
an unclassified balance sheet — identifies a financial-institution
family and stops there. Eight banks and five insurers matched it
identically, so shape cannot name which of the two a company is. Worse,
a filing this platform failed to read matches it too.

The conclusion was that bank-specific behaviour needs **positive
evidence of bank financial language, never the absence of generic
industrial concepts**:

```text
Canonical statements → Financial understanding
                     → Positive financial-language evidence → Financial model
```

So this module reads two lines a filer actually prints. A bank strikes
a subtotal for interest — it earns by lending at more than it pays, and
its statement is built around that. An insurer earns a premium and pays
claims, and prints no interest subtotal at all. Both are amounts on the
face of the income statement, grounded to a cell like every other figure
this platform holds.

## What it deliberately does not do

It does not read expenses. Five insurers print five different labels for
claims and policyholder benefits, and Citigroup prints "Total provisions
for credit losses and for benefits and claims" — one bank row that would
have made an insurance rule fire on a bank. There is no stable row to
ground, so no concept was acquired for it.

It does not read interest income or interest expense on their own.
Coca-Cola, Tesla, Walmart and Procter & Gamble all print them. A rule
resting on those would call a beverage company a bank.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.agreement import Agreement
from app.domain.financial_statement_consensus import FinancialStatementConsensus
from app.domain.financial_statements import StatementConcept, StatementKind
from app.domain.tabular_evidence import ReportedFigure


class StatementLanguage(StrEnum):
    """What the income statement establishes about how the filer earns."""

    #: The statement strikes a net interest subtotal: the filer accounts
    #: for its performance as interest earned against interest paid.
    INTEREST_BASED = "interest based"

    #: The statement prints premium revenue and no interest subtotal.
    INSURANCE_BASED = "insurance based"

    #: Both are printed. Unexercised in the corpus that earned this
    #: vocabulary, and present because the derivation must be total: a
    #: bancassurer prints both lines, and a function unable to say so
    #: would have to pick one and would be silently wrong the first time
    #: it met one. Named for the evidence rather than for this
    #: platform's difficulty with it — "both" is what the statement
    #: says, "ambiguous" would be a claim about the reader.
    BOTH = "interest based and insurance based"

    #: Neither line is printed, on a statement this platform did read.
    #: An ordinary operating company's answer — and, in this corpus,
    #: also one insurer's, which is why it is worded as an absence of
    #: evidence rather than as evidence of a generic business.
    NEITHER = "neither established"

    #: Nothing is claimed, because the statement was not read. Distinct
    #: from `NEITHER` in exactly the way the corpus proved it must be:
    #: an unread statement produces the same empty answer a bank's would
    #: if its rows could not be parsed.
    NOT_ESTABLISHED = "not established"


@dataclass(frozen=True, slots=True)
class LanguageMarker:
    """One printed line that evidences a language, or its absence."""

    concept: StatementConcept

    #: The checked cell, where the statement printed the line.
    figure: ReportedFigure | None

    #: How firmly, over the readings that addressed it.
    agreement: Agreement | None

    #: Why there is none, in the consensus's own words.
    absent_because: str | None = None

    @property
    def is_established(self) -> bool:
        return self.figure is not None


@dataclass(frozen=True, slots=True)
class EstablishedLanguage:
    """What one filing's income statement says about its financial language.

    Carries the markers as well as the conclusion, because the
    conclusion is worthless without them: a reader who is told
    *interest based* is owed the row, the cell and the width beneath it.
    """

    symbol: str

    language: StatementLanguage

    #: Both markers, always, established or not — so a reader never has
    #: to infer whether a marker was absent or never looked for.
    markers: tuple[LanguageMarker, ...]

    #: Whether the income statement was read at all. False makes the
    #: language `NOT_ESTABLISHED` whatever the markers say.
    statement_read: bool

    #: Why nothing is claimed, where nothing is.
    absent_because: str | None = None

    def marker(self, concept: StatementConcept) -> LanguageMarker | None:
        for marker in self.markers:
            if marker.concept is concept:
                return marker

        return None

    @property
    def established(self) -> tuple[LanguageMarker, ...]:
        return tuple(marker for marker in self.markers if marker.is_established)

    @property
    def support(self) -> Agreement | None:
        """The narrowest agreement beneath the markers that carried it.

        A language is exactly as established as the weakest line under
        it, the rule `FinancialUnderstanding` already holds its measures
        to. None where nothing was established.
        """

        widths = [
            marker.agreement
            for marker in self.established
            if marker.agreement is not None
        ]

        if not widths:
            return None

        return min(widths, key=lambda counted: counted.agreeing / counted.readings)


#: The two lines that evidence a language, in the order a reader meets them.
MARKERS: tuple[StatementConcept, ...] = (
    StatementConcept.NET_INTEREST_INCOME,
    StatementConcept.PREMIUM_REVENUE,
)


def language_of(consensus: FinancialStatementConsensus) -> EstablishedLanguage:
    """What this income statement's consensus establishes about its language.

    Deterministic and total. Raises nothing and infers nothing: a
    consensus for another statement, or one whose income statement was
    never read, yields `NOT_ESTABLISHED` with the reason worded.
    """

    if consensus.statement is not StatementKind.INCOME_STATEMENT:
        return EstablishedLanguage(
            symbol=consensus.symbol,
            language=StatementLanguage.NOT_ESTABLISHED,
            markers=(),
            statement_read=False,
            absent_because=(
                "A financial language is established from the income "
                f"statement, and this consensus is of the {consensus.statement}."
            ),
        )

    markers = tuple(_marker(consensus, concept) for concept in MARKERS)

    if not _was_read(consensus):
        return EstablishedLanguage(
            symbol=consensus.symbol,
            language=StatementLanguage.NOT_ESTABLISHED,
            markers=markers,
            statement_read=False,
            absent_because=(
                "This platform located no figure at all in the income "
                "statement it read, so its rows establish nothing — an "
                "absence here is a fact about the reading rather than about "
                "the company. Measured on MUFG, whose statement rows are "
                "labelled only 'Total'."
            ),
        )

    interest = markers[0].is_established
    insurance = markers[1].is_established

    return EstablishedLanguage(
        symbol=consensus.symbol,
        language=_language(interest, insurance),
        markers=markers,
        statement_read=True,
        absent_because=(
            None
            if interest or insurance
            else (
                "This income statement was read, and prints neither a net "
                "interest subtotal nor a premium revenue line."
            )
        ),
    )


def _language(interest: bool, insurance: bool) -> StatementLanguage:
    """The four answers two established facts can produce."""

    if interest and insurance:
        return StatementLanguage.BOTH

    if interest:
        return StatementLanguage.INTEREST_BASED

    if insurance:
        return StatementLanguage.INSURANCE_BASED

    return StatementLanguage.NEITHER


def _marker(
    consensus: FinancialStatementConsensus, concept: StatementConcept
) -> LanguageMarker:
    """One marker, read straight off the consensus and never recomputed."""

    fact = consensus.fact(concept)

    if fact is None:
        return LanguageMarker(
            concept=concept,
            figure=None,
            agreement=None,
            absent_because=(
                "No reading of this statement was asked for this line. It "
                "was read before this platform knew to look for it, and "
                "observing the statement again asks it."
            ),
        )

    return LanguageMarker(
        concept=concept,
        figure=fact.anchor,
        agreement=fact.agreement,
        absent_because=fact.unlocated_because,
    )


def _was_read(consensus: FinancialStatementConsensus) -> bool:
    """Whether the statement established any figure at all.

    The reading-validity guard, in the form the statement stream can
    state it: a consensus every one of whose concepts is absent is
    indistinguishable from a bank's, an insurer's and an ordinary
    company's, so it evidences none of them. The guard is deliberately
    over the *whole* statement rather than the two markers — a filing
    that establishes its revenue and its net income has demonstrably
    been read, and its silence about interest is then the filer's.
    """

    return bool(consensus.located_facts)
