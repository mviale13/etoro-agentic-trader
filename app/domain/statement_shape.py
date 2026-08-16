"""What shape a filer's own statements have, and whose absence each absence is.

A measurement of this platform against a document, in the family of
`reader_stability`: it reads, it reports, and it concludes nothing. No
model is asked anywhere in it.

It exists because of a distinction the statement stream could not draw.
A `FinancialStatementConsensus` says *gross profit: no figure located*,
and that sentence covers three completely different situations:

- the filer printed no gross profit line — a fact about the company;
- the filer printed one under a label this platform does not accept — a
  fact about this platform's vocabulary;
- this platform located the wrong section, or none, and read nothing —
  a fact about acquisition.

Told apart, the first is evidence. Confused with the other two, it is
the confident-sounding absence invariant 1 exists to prevent. Measured
on MUFG's 20-F, every one of the eight concepts came back absent at
5 of 5 readings — which reads exactly like a bank's statements and is
in fact a section this platform could not read at all.

So the shape of a statement is reported as three findings rather than
one, and the strongest claim available — *the filer prints no such
line* — is made only where this platform can also show it read the
statement: some concept of that statement located, and no label near
the missing one left unread.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.financial_statements import (
    STATEMENT_NAMES,
    StatementConcept,
    StatementKind,
    concepts_of,
    matches_concept,
    statement_contenders,
    statement_tables,
    statement_text,
)
from app.domain.primary_source import SourceDocument
from app.domain.tabular_evidence import SourceTable, read_number

#: Words that name a concept in a filer's own row labels, used for one
#: purpose only: to weaken an absence this platform would otherwise
#: report as the filer's.
#:
#: Deliberately generous, and deliberately one-directional. A word here
#: can only ever turn "the statement prints no such line" into "this
#: platform cannot tell", never the other way round — so a form nobody
#: thought of costs a downgraded finding rather than a wrong one. That
#: is the opposite of `CONCEPT_LABELS`, where a form must be exact
#: because it decides whether a figure is read.
#:
#: Only the concepts whose *absence* this platform reasons from are
#: listed. A concept nobody draws a conclusion from needs no qualifier.
CONCEPT_WORDS: dict[StatementConcept, tuple[str, ...]] = {
    StatementConcept.GROSS_PROFIT: ("gross",),
    StatementConcept.OPERATING_INCOME: (
        "operating income",
        "operating profit",
        "operating earnings",
        "operating result",
        "income from operations",
        "loss from operations",
        "result from operations",
    ),
    # Revenue and the bottom line, added after a measurement found the
    # two concepts that most often blame a company were the two this
    # table had no entry for — so their `NOT_PRINTED` could never be
    # weakened, and the platform asserted that Coca-Cola prints no
    # revenue line while its own reading had located a figure three
    # rows below `Net Operating Revenues`
    # (`PROFITABILITY_EVIDENCE_SEMANTICS.md`).
    #
    # `revenue` is bare on purpose, as `gross` already is: every label
    # carrying the word names revenue of some kind, and a filer that
    # prints revenue lines but no total this platform accepts is a
    # filer this platform cannot claim prints none. The bottom-line
    # forms are phrases rather than the bare word `income`, which would
    # match every interest and fee line on a bank's statement and
    # weaken the finding on evidence that has nothing to do with it.
    StatementConcept.TOTAL_REVENUE: (
        "revenue",
        "turnover",
        "net sales",
        "total sales",
    ),
    StatementConcept.NET_INCOME: (
        "net income",
        "net earnings",
        "net profit",
        "net loss",
        "profit for the",
        "profit attributable",
        "profit after tax",
    ),
    StatementConcept.TOTAL_CURRENT_ASSETS: ("total current assets",),
    StatementConcept.TOTAL_CURRENT_LIABILITIES: ("total current liabilities",),
}


class Presence(StrEnum):
    """What this platform can say about one concept on one statement."""

    #: A row this platform reads as answering the concept prints a number.
    PRINTED = "printed"

    #: No such row, and no label near it that this platform failed to
    #: read. The strongest absence available: the filer printed no line.
    NOT_PRINTED = "not printed"

    #: No such row, but the statement prints a label a reader would
    #: expect to answer the concept and this platform does not accept.
    #: The absence is this platform's, and it is not evidence about the
    #: company.
    UNREAD = "unread"

    #: Nothing was read at all — no statement located, or no table under
    #: the one located. Says nothing about any concept.
    UNLOCATED = "unlocated"


@dataclass(frozen=True, slots=True)
class ConceptShape:
    """One concept, as the located statement prints it or does not."""

    concept: StatementConcept

    presence: Presence

    #: The filer's own row label, where one answers the concept.
    printed_as: str | None = None

    #: Labels this platform did not read as answering it, where any name
    #: it. Populated only for `UNREAD`, which is what that state means.
    unread: tuple[str, ...] = ()

    @property
    def is_printed(self) -> bool:
        return self.presence is Presence.PRINTED


@dataclass(frozen=True, slots=True)
class StatementShape:
    """One primary statement, as located and as read by this platform alone."""

    statement: StatementKind

    #: How many places in the document could have opened it. 0 means no
    #: title began a block anywhere, and nothing below was read.
    contenders: int

    #: How many tables were printed under the title this platform chose,
    #: and how many of their rows carry both a label and a number.
    tables: int
    numeric_rows: int

    concepts: tuple[ConceptShape, ...]

    #: Why nothing was read, where nothing was. A statement whose title
    #: never began a block and a located statement printing no readable
    #: table are different findings, and only the second is about the
    #: document — so the absence carries which it is rather than leaving
    #: a reader to infer it.
    unlocated_because: str | None = None

    @property
    def is_located(self) -> bool:
        """Whether a statement with readable rows was located at all."""

        return self.tables > 0 and self.numeric_rows > 0

    @property
    def is_read(self) -> bool:
        """Whether some concept was located, which is what proves it read.

        The guard every absence on this statement rests on. A statement
        whose every concept is absent is indistinguishable from one this
        platform failed to read, so its absences are not evidence — and
        this is the property that says so.
        """

        return any(concept.is_printed for concept in self.concepts)

    @property
    def provenance_uncertain(self) -> bool:
        return self.contenders > 1

    def of(self, concept: StatementConcept) -> ConceptShape | None:
        for shaped in self.concepts:
            if shaped.concept is concept:
                return shaped

        return None

    def evidences_absence(self, concept: StatementConcept) -> bool:
        """Whether *the filer printed no such line* is a claim this supports.

        Two conditions, and neither is sufficient alone. The concept must
        be missing with no label near it left unread — otherwise the gap
        is this platform's vocabulary. And the statement must have been
        read at all, shown by some other concept being located — because
        a statement where nothing was found looks identical to a bank's
        whatever the document says.

        Deliberately a method on the statement rather than a property of
        the concept: the guard needs both, and a concept that answered
        this on its own would answer it wrongly for MUFG.
        """

        shaped = self.of(concept)

        return (
            self.is_read
            and shaped is not None
            and shaped.presence is Presence.NOT_PRINTED
        )

    @property
    def name(self) -> str:
        return STATEMENT_NAMES[self.statement]


@dataclass(frozen=True, slots=True)
class DocumentShape:
    """One filing's three statements, as shape rather than as figures.

    Nothing here is a classification and nothing here is scored. What a
    shape means for how a company should be read financially is a
    question for a rule that has been earned against a corpus; this only
    supplies the facts such a rule would have to be earned against.
    """

    symbol: str

    #: The document as an investor would cite it.
    source: str

    statements: tuple[StatementShape, ...]

    def of(self, statement: StatementKind) -> StatementShape | None:
        for shaped in self.statements:
            if shaped.statement is statement:
                return shaped

        return None


def shape_of(symbol: str, document: SourceDocument) -> DocumentShape:
    """The shape of every primary statement this platform can locate.

    Deterministic, and derived from the document alone: the row labels
    are the filer's, the acceptance rule is `matches_concept` — the same
    one a reading is held to — and no model is involved at any point.
    """

    return DocumentShape(
        symbol=symbol.upper().strip(),
        source=document.source.stated(),
        statements=tuple(
            _statement_shape(document, statement) for statement in StatementKind
        ),
    )


def _statement_shape(
    document: SourceDocument, statement: StatementKind
) -> StatementShape:
    """One statement, measured against the concepts it is asked for."""

    tables = statement_tables(document, statement)
    labels = _numeric_labels(tables)

    return StatementShape(
        statement=statement,
        contenders=statement_contenders(document, statement),
        tables=len(tables),
        numeric_rows=len(labels),
        concepts=tuple(
            _concept_shape(concept, labels, _every_label(tables))
            for concept in concepts_of(statement)
        ),
        unlocated_because=(None if labels else _unlocated_because(document, statement)),
    )


def _concept_shape(
    concept: StatementConcept,
    measuring: tuple[str, ...],
    every: tuple[str, ...],
) -> ConceptShape:
    """One concept, against the labels the located statement prints.

    Two label sets, and the asymmetry is the whole design. A concept is
    *printed* only where a row that carries a figure answers it — the
    same rule a reading is held to, since a row measuring nothing cannot
    supply a figure. But the downgrade scans **every** label, figure or
    not: a statement printing "Gross profit" as a heading over a
    breakdown does print the concept, and claiming it prints no such
    line would be this platform's blindness stated as the filer's.
    """

    if not measuring:
        return ConceptShape(concept=concept, presence=Presence.UNLOCATED)

    for label in measuring:
        if matches_concept(concept, label):
            return ConceptShape(
                concept=concept,
                presence=Presence.PRINTED,
                printed_as=label,
            )

    unread = tuple(
        label
        for label in dict.fromkeys(every)
        if any(word in label.casefold() for word in CONCEPT_WORDS.get(concept, ()))
    )

    if unread:
        return ConceptShape(
            concept=concept,
            presence=Presence.UNREAD,
            unread=unread,
        )

    return ConceptShape(concept=concept, presence=Presence.NOT_PRINTED)


def _every_label(tables: tuple[SourceTable, ...]) -> tuple[str, ...]:
    """Every row label below a header row, whether it measures or not.

    Read only to weaken a finding, which is why it is deliberately the
    wider set: a heading that names a concept and prints nothing still
    proves the filer accounts for it somewhere.
    """

    return tuple(
        label
        for table in tables
        for index, row in enumerate(table.rows)
        if index > table.header_row and (label := row.label.strip())
    )


def _numeric_labels(tables: tuple[SourceTable, ...]) -> tuple[str, ...]:
    """Every row label below a header row whose row prints a number.

    The same rule `row_figures` reads a row under: a label alone names
    something without measuring it, and a section heading inside a
    statement prints no figure. Restricting to rows that print one is
    what keeps a heading from being read as the line it heads.
    """

    labels: list[str] = []

    for table in tables:
        for index, row in enumerate(table.rows):
            if index <= table.header_row:
                continue

            label = row.label.strip()

            if not label:
                continue

            if any(read_number(cell) is not None for cell in row.cells[1:]):
                labels.append(label)

    return tuple(labels)


def _unlocated_because(document: SourceDocument, statement: StatementKind) -> str:
    """Why a statement yielded no shape, in the wording the stream uses.

    Two different facts, worded apart, exactly as the extractor words
    them: a statement this platform never located, and a located
    statement that printed no table it could read.
    """

    named = STATEMENT_NAMES[statement]

    if not statement_text(document, statement).strip():
        return (
            f"This platform located no {named} in this document — no {named} "
            "title begins a block here — so it read no row. This is a fact "
            "about the reading, not about the company."
        )

    return (
        f"This document prints a {named} title, and no table this platform "
        "could read appears under it, so no row was read."
    )
