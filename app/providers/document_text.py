"""Reading a filing's markup as words, and as the tables it prints.

One implementation, because every provider faces the identical problem:
an annual report arrives as megabytes of markup, and what this platform
reads out of it is a couple of sections of prose and the tables inside
them.

Tags were stripped and thrown away for as long as the platform only read
prose. A table stripped of its tags still contains every word and every
figure and has lost the one thing that says which figure belongs to which
row — so the structure is now parsed rather than discarded, and
`flatten` keeps a map back to the markup so a section located in the text
can be cut out of the markup it came from.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from app.domain.tabular_evidence import SourceTable, TableRow, read_number

_TAG = re.compile(r"<[^>]+>")

_ENTITY = re.compile(r"&(?:#\d+|#[xX][0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);")

#: The horizontal whitespace a rendered page collapses. Newlines are not
#: in it: a paragraph break is worth keeping, and three of them are not.
_HORIZONTAL = " \t\r\f\v"

_TABLE = re.compile(r"(?is)</?table\b[^>]*>")

#: Stylesheets and scripts, which are not words a reader sees. Left alone
#: when reading prose, because that reduction has always kept them and a
#: filer puts them where they do no harm. Dropped when reading tables,
#: because a rule set that lands inside a cell becomes that cell's
#: contents and a cell is quoted verbatim in evidence.
_EMBEDDED = re.compile(r"(?is)<(style|script)\b.*?</\1\s*>")

_ROW = re.compile(r"(?is)<tr\b[^>]*>")

_CELL = re.compile(r"(?is)<t[dh]\b[^>]*>")

#: How many columns of the grid a cell occupies. Honouring it is what
#: makes a filing's table a grid at all: a filer pads with wide empty
#: cells rather than with several narrow ones, so counting cells without
#: expanding them puts the same column at a different index on every row.
_COLSPAN = re.compile(r'(?is)\bcolspan\s*=\s*["\']?\s*(\d+)')

#: An upper bound on that, because the number is written by whoever wrote
#: the document and a cell claiming ten thousand columns is not one.
_WIDEST = 64

_ROW_END = re.compile(r"(?is)</tr\s*>")

#: Where one sentence of a caption ends and the next begins. Rough on
#: purpose: the caption is carried so a reader can see what the figures
#: are denominated in, and cutting a page of preceding prose down to the
#: line the filer wrote above the table is all it has to do.
_SENTENCE = re.compile(r"(?<=[.:;])\s+")

#: Numbers at the front of a caption, which are the last row of whatever
#: table came before it rather than anything this one is called.
_LEADING_FIGURES = re.compile(r"^(?:[–\-(]?[\d.,]+\)?\s+)+")

#: A currency symbol a filer typeset in a cell of its own, which belongs
#: to the figure beside it rather than being a value in its own right.
_CURRENCY = frozenset({"$", "€", "£", "¥"})

#: What a filer puts in a cell when the cell is there for the layout
#: rather than for the content. A column of nothing but these carries no
#: information and can leave, as long as it leaves from every row.
_SPACING = frozenset({"", *_CURRENCY})

#: A table with fewer numbers than this is being used for layout, which
#: filers do constantly. Dropping them is not a loss of evidence: a
#: citation into this platform's tables is a citation of a number.
_MINIMUM_FIGURES = 3


@dataclass(frozen=True, slots=True)
class Flattened:
    """A document as words, and where each word came from in the markup."""

    text: str

    #: `origin[i]` is where `text[i]` began in the markup it was read
    #: from. What makes it possible to find a section in the text and
    #: then cut that same section out of the markup, tables intact.
    origin: tuple[int, ...]

    def markup_span(self, start: int, end: int) -> tuple[int, int]:
        """Where a span of the text sits in the markup behind it."""

        if not self.origin:
            return (0, 0)

        first = self.origin[max(0, min(start, len(self.origin) - 1))]
        last = self.origin[max(0, min(end, len(self.origin) - 1))]

        return (first, last)


def flatten(markup: str) -> Flattened:
    """
    Markup reduced to the words a reader would see, without losing its place.

    Every tag becomes one space, every entity becomes what it stands for,
    runs of horizontal whitespace collapse, and a run of blank lines
    becomes one blank line. That is the reduction this platform has always
    read filings through, character for character — kept identical on
    purpose, because the sections are located by searching this text and a
    different reduction would silently locate different sections.

    What is new is `origin`: where each surviving character began in the
    markup. A section found in the text can therefore be cut out of the
    markup it came from, tables intact.
    """

    characters: list[str] = []
    origin: list[int] = []

    position = 0
    length = len(markup)

    while position < length:
        character = markup[position]

        if character == "<":
            match = _TAG.match(markup, position)

            if match is not None:
                characters.append(" ")
                origin.append(position)
                position = match.end()
                continue

        if character == "&":
            match = _ENTITY.match(markup, position)

            if match is not None:
                for glyph in html.unescape(match.group(0)):
                    characters.append(glyph)
                    origin.append(position)

                position = match.end()
                continue

        characters.append(character)
        origin.append(position)
        position += 1

    return _collapsed(characters, origin)


def _collapsed(characters: list[str], origin: list[int]) -> Flattened:
    """Whitespace as a page renders it, with each survivor's place kept."""

    text: list[str] = []
    places: list[int] = []

    index = 0
    length = len(characters)

    while index < length:
        character = characters[index]

        if character in _HORIZONTAL:
            run = index

            while run < length and characters[run] in _HORIZONTAL:
                run += 1

            text.append(" ")
            places.append(origin[index])
            index = run
            continue

        if character == "\n":
            run = index

            while run < length and characters[run] == "\n":
                run += 1

            # Three or more blank lines are typesetting; one is meaning.
            kept = min(run - index, 2) if run - index > 2 else run - index

            for offset in range(kept):
                text.append("\n")
                places.append(origin[index + offset])

            index = run
            continue

        text.append(character)
        places.append(origin[index])
        index += 1

    return Flattened(text="".join(text), origin=tuple(places))


def read_tables(markup: str) -> tuple[SourceTable, ...]:
    """
    Every table this markup prints that actually reports numbers.

    Indexed by their order in the document, which is what a citation
    addresses. The index is stable for one reading of one document, and
    a document is immutable, so a stored citation keeps pointing at the
    cell it was checked against.

    Nested tables are read as part of the cell that contains them, rather
    than as tables of their own. A filer nests for layout, and a nested
    table addressed as a peer of its parent would give two different
    addresses for one number.
    """

    without_embedded = _EMBEDDED.sub(" ", markup)

    tables: list[SourceTable] = []

    for start, end in _table_spans(without_embedded):
        rows = _rows(_without_nested(without_embedded[start:end]))

        figures = sum(
            1 for row in rows for cell in row.cells if read_number(cell) is not None
        )

        if len(rows) < 2 or figures < _MINIMUM_FIGURES:
            continue

        tables.append(
            SourceTable(
                index=len(tables),
                caption=_caption(without_embedded, start),
                rows=rows,
            )
        )

    return tuple(tables)


def _table_spans(markup: str) -> list[tuple[int, int]]:
    """Where each outermost table begins and ends."""

    spans: list[tuple[int, int]] = []

    depth = 0
    opened = 0

    for match in _TABLE.finditer(markup):
        if match.group(0).startswith("</"):
            depth = max(0, depth - 1)

            if depth == 0 and opened:
                spans.append((opened, match.end()))
                opened = 0

            continue

        if depth == 0:
            opened = match.start()

        depth += 1

    return spans


def _without_nested(table: str) -> str:
    """
    One table's markup, with any table inside it reduced to its words.

    A nested table's own rows and cells would otherwise be read as the
    outer table's, cutting its rows in the wrong places — so a filer's
    layout nesting would corrupt the structure that the evidence rests
    on. Reduced rather than dropped: what a nested table prints is part
    of what the cell containing it prints.
    """

    pieces: list[str] = []

    depth = 0
    opened = 0
    last = 0

    for match in _TABLE.finditer(table):
        if match.group(0).startswith("</"):
            depth = max(0, depth - 1)

            if depth == 1:
                pieces.append(table[last:opened])
                pieces.append(flatten(table[opened : match.end()]).text)
                last = match.end()

            continue

        if depth == 1:
            opened = match.start()

        depth += 1

    pieces.append(table[last:])

    return "".join(pieces)


def _rows(table: str) -> tuple[TableRow, ...]:
    """The table's rows, as a grid with the empty edges of it pruned."""

    starts = [match.start() for match in _ROW.finditer(table)]

    printed = []

    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(table)

        closing = _ROW_END.search(table, start, end)

        printed.append(_cells(table[start : closing.start() if closing else end]))

    return _gridded(printed)


def _gridded(printed: list[tuple[str, ...]]) -> tuple[TableRow, ...]:
    """
    Rows of cells made into a grid, and the spacing pruned as a grid.

    Half of a filing's table is typesetting: blank cells between columns,
    a currency symbol in a column of its own, a blank row for air. It
    reads badly and it costs tokens, so it is worth removing — but it has
    to be removed *whole columns at a time*.

    Removing blanks cell by cell is what breaks the table. Volkswagen's
    revenue table leaves the label cell of its total row empty, so a
    per-row prune shifted that one row left by one and moved every figure
    on it under the wrong heading — quietly destroying the one assumption
    a share of a total rests on. A column that is empty in every row can
    go without disturbing anything, because every row loses the same one.
    """

    if not printed:
        return ()

    width = max(len(cells) for cells in printed)

    grid = [(*cells, *("",) * (width - len(cells))) for cells in printed]

    columns = [
        index
        for index in range(width)
        if any(row[index] not in _SPACING for row in grid)
    ]

    rows = [
        TableRow(cells=tuple(row[index] for index in columns))
        for row in grid
        if any(cell for cell in row)
    ]

    return tuple(rows)


def _cells(row: str) -> tuple[str, ...]:
    """
    What the row's cells print, every one of them, empty ones included.

    A filer's table is half spacing: blank cells between columns, a
    currency symbol in a column of its own. Dropping them reads better
    and is wrong — an index only means the same thing on two rows if
    both rows are counted the same way, and the blanks are not printed
    consistently. Volkswagen's revenue table leaves the label cell of
    its total row empty, so dropping blanks shifted that one row left by
    one and silently moved every figure on it under the wrong heading.

    The blanks stay. A cell that carries nothing is refused as evidence
    later, on the grounds that it prints no number, which costs nothing
    and keeps the grid a grid.
    """

    opened = list(_CELL.finditer(row))

    cells: list[str] = []

    for index, match in enumerate(opened):
        end = opened[index + 1].start() if index + 1 < len(opened) else len(row)

        cells.append(flatten(row[match.start() : end]).text.strip())

        spans = _COLSPAN.search(match.group(0))
        width = min(int(spans.group(1)), _WIDEST) if spans else 1

        # The columns a wide cell covers beyond its first. Empty, so a
        # uniformly empty one is pruned with the rest of the spacing.
        cells.extend("" for _ in range(max(0, width - 1)))

    return _with_currency_absorbed(cells)


def _with_currency_absorbed(cells: list[str]) -> tuple[str, ...]:
    """
    A lone currency symbol taken as the prefix of the figure beside it.

    Filers typeset "$ 42,466" as two cells and "17,672" as one, on
    alternating rows of the same table. Visually the numbers line up;
    structurally they sit in different columns, so a column index means
    the 2025 figure on one row and nothing at all on the next.

    A symbol on its own is not a value — it is the front of the value to
    its right. Moving that value into the symbol's cell puts every figure
    of a column in one column, and empties the one the value came from so
    the grid prunes it away.
    """

    for index, cell in enumerate(cells):
        if cell not in _CURRENCY:
            continue

        for ahead in range(index + 1, min(index + 4, len(cells))):
            if not cells[ahead]:
                continue

            cells[index] = f"{cell} {cells[ahead]}"
            cells[ahead] = ""
            break

    return tuple(cells)


def _caption(markup: str, start: int) -> str:
    """
    What the document says immediately above a table.

    Where a filer states the units and the scale — "in € million" — that
    the cells themselves leave out. Not parsed and not relied upon: it is
    carried into the evidence so a reader can see what the numbers are
    denominated in, while the arithmetic stays inside one column of one
    table where the scale cannot differ.
    """

    window = markup[max(0, start - 1200) : start]

    # A fixed-width window opens wherever it opens, which is regularly
    # inside a tag — and the tail of that tag is not text the document
    # printed. Where the window begins mid-tag, it starts again after it.
    if ">" in window and (window.find(">") < window.find("<") or "<" not in window):
        window = window[window.find(">") + 1 :]

    preceding = " ".join(flatten(window).text.split())

    sentences = [piece for piece in _SENTENCE.split(preceding) if piece.strip()]

    if not sentences:
        return ""

    caption = sentences[-1]

    # A last sentence of "2024" is a page's worth of table headings, not
    # a caption. One more back is usually where the filer wrote what the
    # table is.
    if len(caption) < 40 and len(sentences) > 1:
        caption = f"{sentences[-2]} {caption}"

    # Figures trailing off the end of the previous table, which the
    # sentence split has no way to tell from the start of this caption.
    return _LEADING_FIGURES.sub("", caption)[-200:].strip()
