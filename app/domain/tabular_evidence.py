"""A number a document printed, and proof of what it is a number of.

Span grounding proves that quoted words appear in a source. It cannot
prove that those words *support the number attached to them* — and for a
quantity read out of a table, the words and the number are related by the
table's structure, which markup-stripped prose no longer has.

The live failure this module exists to prevent: reading Volkswagen's
segment table, the extraction cited a *column header* for two of three
segments. The shares were right, the quotes were genuinely in the text,
and the citations demonstrated nothing at all.

So a quantitative citation here is not a span the model copied. It is an
**address into a table this platform parsed itself** — table, row,
column — and the platform reads the cell at that address and compares it
with what it was told is there. The row label, the column header and the
caption are never taken from the model; they are read off the document.
A model cannot cite a header for a segment's revenue, because the address
it gives resolves to a cell whose contents the validator reads for
itself.

The distinction, in the platform's own words:

- **Evidence existence** — the cited content is in the source. What span
  grounding establishes.
- **Evidence applicability** — the cited content supports the specific
  fact asserted. What this module establishes.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

#: Two numbers are the same number when they agree to within reading
#: error. The model transcribes a printed cell; it does not compute, so
#: anything beyond a float's own imprecision is a different cell.
_SAME_NUMBER = 1e-6

_NOISE = re.compile(r"[^a-z0-9]+")

_NOT_NUMERIC = re.compile(r"[^\d.,\-]")

_HAS_DIGIT = re.compile(r"\d")

_THOUSANDS = re.compile(r"^\d{1,3}(?:([.,])\d{3})+$")


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


def read_number(printed: str) -> float | None:
    """
    The number a cell prints, or nothing where it prints something else.

    Nothing is the common answer and it is not a failure: most cells in a
    filing's tables hold labels, headers, currency symbols and spacing.
    A cell that does not print a number is exactly how a citation of a
    column header is caught.

    Separators are read by pattern rather than by locale, because the
    document's language is not always the one its numbers are typeset in
    and a wrong guess is a thousandfold error. Where both a comma and a
    full stop appear, the last of them is the decimal mark. Where only
    one appears, it is a thousands separator when the digits fall into
    exact groups of three — "322,284" and "322.284" are both 322284 —
    and a decimal mark otherwise.
    """

    text = printed.strip()

    if not text or not _HAS_DIGIT.search(text):
        return None

    # Accountants' parentheses, which are a minus sign wearing a hat.
    negative = text.startswith("(") and text.endswith(")")

    digits = _NOT_NUMERIC.sub("", text)

    if not digits or not _HAS_DIGIT.search(digits):
        return None

    negative = negative or digits.startswith("-")
    digits = digits.lstrip("-")

    if "," in digits and "." in digits:
        decimal = max(digits.rfind(","), digits.rfind("."))
        whole = _NOT_NUMERIC.sub("", digits[:decimal]).replace(",", "").replace(".", "")
        fraction = digits[decimal + 1 :]
    elif _THOUSANDS.match(digits):
        whole, fraction = digits.replace(",", "").replace(".", ""), ""
    elif "," in digits or "." in digits:
        separator = "," if "," in digits else "."
        whole, _, fraction = digits.partition(separator)
        fraction = fraction.replace(",", "").replace(".", "")
    else:
        whole, fraction = digits, ""

    if not whole.isdigit() or (fraction and not fraction.isdigit()):
        return None

    value = float(f"{whole}.{fraction or '0'}")

    return -value if negative else value


@dataclass(frozen=True, slots=True)
class TableRow:
    """One row of a table, as printed, cell by cell."""

    cells: tuple[str, ...]

    @property
    def label(self) -> str:
        """What the row is called, which is its leading cell."""

        return self.cells[0] if self.cells else ""

    @property
    def is_numeric(self) -> bool:
        """Whether this row prints any number at all."""

        return any(read_number(cell) is not None for cell in self.cells)


@dataclass(frozen=True, slots=True)
class SourceTable:
    """
    One table a document printed, with its structure kept.

    The structure *is* the evidence. A table flattened into prose still
    contains every word and every figure, and has lost the only thing
    that says which figure belongs to which row — which is precisely the
    relationship a quantitative fact asserts.

    Row 0 is treated as the header row without further inspection. A
    heuristic that decided which row was "really" the header would be a
    guess dressed as a fact; the model is shown the table exactly as
    parsed, addresses a cell within it, and the platform reports the
    labels it finds at that address for a reader to judge.
    """

    #: Position among the tables of the section this came from. Stable
    #: for one reading, and what a citation addresses.
    index: int

    #: The text immediately preceding the table, where a filer states
    #: the units and the scale — "in € million" — that the cells omit.
    caption: str

    rows: tuple[TableRow, ...]

    def cell(self, row: int, column: int) -> str | None:
        """What is printed at this address, or nothing where nothing is."""

        if not 0 <= row < len(self.rows):
            return None

        cells = self.rows[row].cells

        if not 0 <= column < len(cells):
            return None

        return cells[column]

    def column_header(self, column: int) -> str:
        """What row 0 calls this column, which is usually the period."""

        return self.cell(0, column) or ""

    def stated(self) -> str:
        """The table as an extraction is shown it: addressable, verbatim."""

        lines = [f"[table {self.index}] {self.caption}".rstrip()]

        for index, row in enumerate(self.rows):
            printed = " | ".join(
                f'c{column}="{cell}"' for column, cell in enumerate(row.cells)
            )
            lines.append(f"  r{index}: {printed}")

        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class CellReference:
    """Where in a document a number was read from."""

    table: int
    row: int
    column: int

    def stated(self) -> str:
        return f"table {self.table}, row {self.row}, column {self.column}"


class EvidenceNotApplicable(Exception):
    """The citation is real and does not support the fact it was given for.

    Deliberately not "the evidence is missing". The address resolves, the
    document prints what it prints, and the relationship claimed over it
    is untrue — which is the whole failure this module names.
    """


@dataclass(frozen=True, slots=True)
class ReportedFigure:
    """
    A number the filer printed, and everything that says what it measures.

    Every field except `value` and `cell` is read off the document by
    this platform rather than supplied by whatever asserted the fact. A
    reader is owed the filer's own words for the row, the column and the
    table, because those three are what turn "322,284" into "Passenger
    Cars revenue for 2024, in € million".
    """

    #: The row's own label, as the document prints it.
    label: str

    #: The column's header, as the document prints it. Usually a period,
    #: and required to be present — a figure in an unlabelled column is
    #: a figure whose period is unproven.
    column_header: str

    #: The cell exactly as printed, separators, currency and all.
    printed: str

    value: float

    cell: CellReference

    caption: str

    def stated(self) -> str:
        """The figure as an investor would check it."""

        return (
            f'"{self.label}" = {self.printed} under "{self.column_header}" '
            f"({self.caption or 'no caption'}, {self.cell.stated()})"
        )


class SharedAxis(StrEnum):
    """Which coordinate two figures agree on, and therefore what is proven.

    A table gives every number two coordinates, and the two figures of a
    share must agree on exactly one of them. Which one they agree on is
    not a detail — it decides what the agreement establishes and what
    names each figure.
    """

    #: The two sit in one column. The column header is the same for both
    #: — a period — and the row labels name the parts. The layout of
    #: Disney's segment table, and of most American filings.
    COLUMN = "column"

    #: The two sit in one row. The row label is the same for both — a
    #: line item, "Umsatzerlöse" — and the column headers name the parts.
    #: The layout of Volkswagen's segment table, and of IFRS segment
    #: notes generally, where the segments run across the top.
    ROW = "row"


@dataclass(frozen=True, slots=True)
class MeasuredShare:
    """
    One printed quantity as a fraction of another printed quantity.

    A share is not a fact a document states; it is arithmetic over two
    facts it does state. Asking a model for the share and a quote to go
    with it asks it to compute and then to evidence the computation with
    a span — which no span can do. So both quantities are cited, the
    platform divides, and the number it stores is one it worked out from
    evidence it checked.

    Both figures must come from the same table, and must agree on exactly
    one of their two coordinates. The shared coordinate is what makes
    them comparable — the same period, or the same line item — and the
    coordinate they differ on is what names the part and the whole. One
    table also means one scale, so a numerator in millions over a
    denominator in thousands cannot arise, without this platform having
    to parse a caption to discover what the scale was.

    What that does *not* prove, in the `ROW` orientation, is the period:
    a table whose columns are segments states its period in its caption
    rather than in its headers. Both figures' headers are recorded, so a
    reader sees what each one is — and this platform does not claim the
    period was established when it was not.
    """

    numerator: ReportedFigure
    denominator: ReportedFigure

    def __post_init__(self) -> None:
        here, there = self.numerator.cell, self.denominator.cell

        if here.table != there.table:
            raise EvidenceNotApplicable(
                f'"{self.numerator.label}" was measured against a total in '
                "another table, so the two are not known to share a scale."
            )

        if here == there:
            raise EvidenceNotApplicable(
                f'"{self.numerator.label}" was measured against itself.'
            )

        if here.row != there.row and here.column != there.column:
            raise EvidenceNotApplicable(
                f'"{self.numerator.label}" and the total it was measured '
                "against share neither a row nor a column, so nothing "
                "relates them beyond sitting in one table."
            )

        if self.denominator.value <= 0:
            raise EvidenceNotApplicable(
                f'The total for "{self.part}" is {self.denominator.printed}, '
                "which nothing can be a share of."
            )

        if not 0.0 <= self.numerator.value / self.denominator.value <= 1.0:
            raise EvidenceNotApplicable(
                f'"{self.part}" is {self.numerator.printed} of a total of '
                f"{self.denominator.printed}, which is not a share."
            )

    @property
    def shared(self) -> SharedAxis:
        """The coordinate the two figures agree on."""

        return (
            SharedAxis.COLUMN
            if self.numerator.cell.column == self.denominator.cell.column
            else SharedAxis.ROW
        )

    @property
    def part(self) -> str:
        """What the document calls the thing this is a share of revenue for."""

        by_column = self.shared is SharedAxis.COLUMN

        return self.numerator.label if by_column else self.numerator.column_header

    @property
    def whole(self) -> str:
        """What the document calls the total it was measured against."""

        by_column = self.shared is SharedAxis.COLUMN

        return self.denominator.label if by_column else self.denominator.column_header

    @property
    def basis(self) -> str:
        """The label both figures carry, which is what makes them comparable."""

        by_column = self.shared is SharedAxis.COLUMN

        return self.numerator.column_header if by_column else self.numerator.label

    @property
    def share(self) -> float:
        """The fraction, computed here from two figures already checked."""

        return self.numerator.value / self.denominator.value

    def stated(self) -> str:
        """
        The relationship as an investor would check it, in full.

        The table, the shared label and the caption are said once rather
        than twice, because the two figures are required to share all
        three and repeating them would suggest they might not.
        """

        under = "under" if self.shared is SharedAxis.COLUMN else "on"

        return (
            f"{self.share:.0%} — "
            f'"{self.part}" {self.numerator.printed} of '
            f'"{self.whole}" {self.denominator.printed}, '
            f'{under} "{self.basis}" '
            f"({self.numerator.caption or 'no caption'}, "
            f"table {self.numerator.cell.table})"
        )


def figure_at(
    tables: tuple[SourceTable, ...],
    reference: CellReference,
    asserted: float,
    described: str,
) -> ReportedFigure:
    """
    The figure at this address, or a worded refusal to believe the claim.

    `asserted` is what the reading says is printed there, and checking it
    is the point rather than a formality: an address alone cannot be
    wrong in a way anyone notices, because whatever cell it lands on
    becomes the answer. Requiring the reading to state the number as well
    turns a misaddressed citation into a disagreement between the reading
    and the document, which is caught here.

    `described` names what the figure was supposed to be, so a refusal
    reads as a fact about this company rather than as a stack trace.
    """

    if not 0 <= reference.table < len(tables):
        raise EvidenceNotApplicable(
            f"{described} cites {reference.stated()}, and the document has "
            f"{len(tables)} tables in the section that was read."
        )

    table = tables[reference.table]

    if reference.row == 0:
        raise EvidenceNotApplicable(
            f"{described} cites the header row of table {reference.table}, "
            "which labels the columns rather than measuring anything."
        )

    if reference.column == 0:
        raise EvidenceNotApplicable(
            f"{described} cites the label column of table {reference.table}, "
            "which names the rows rather than measuring anything."
        )

    printed = table.cell(reference.row, reference.column)

    if printed is None:
        raise EvidenceNotApplicable(
            f"{described} cites {reference.stated()}, where the table has no cell."
        )

    value = read_number(printed)

    if value is None:
        raise EvidenceNotApplicable(
            f"{described} cites {reference.stated()}, which prints "
            f"{printed.strip()!r} — not a number. The citation is real and "
            "supports nothing."
        )

    if not math.isclose(value, asserted, rel_tol=_SAME_NUMBER, abs_tol=_SAME_NUMBER):
        raise EvidenceNotApplicable(
            f"{described} was read as {asserted:g}, and {reference.stated()} "
            f"prints {printed.strip()!r}. The reading and the document "
            "disagree about what is there."
        )

    header = table.column_header(reference.column).strip()
    label = table.rows[reference.row].label.strip()

    # Both coordinates must be named. Which of the two names the part of
    # the business and which names the period depends on how the filer
    # laid the table out, and this is enforced before anyone knows —
    # a figure missing either name is a figure that cannot be described.
    if not header or not label:
        missing = "column carries no header" if not header else "row carries no label"

        raise EvidenceNotApplicable(
            f"{described} cites {reference.stated()}, whose {missing}, so "
            "there is nothing to say what the number measures."
        )

    return ReportedFigure(
        label=label,
        column_header=header,
        printed=printed.strip(),
        value=value,
        cell=reference,
        caption=table.caption,
    )
