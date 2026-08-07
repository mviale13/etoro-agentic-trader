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
from bisect import bisect_left
from dataclasses import dataclass

from app.domain.prose_evidence import Region
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

#: Emphasis, however the filer expresses it. SEC filers do not use
#: `<h1>`: a heading is a short span typeset bold, and the tag that says
#: so is the tag the filer happened to reach for.
_EMPHASIS = re.compile(r"(?is)<(span|b|strong)\b([^>]*)>([^<]*)</\1\s*>")

#: The block element a heading sits alone inside. What makes it a
#: heading rather than a bold phrase mid-sentence is that the block
#: holds nothing else, so both ends are checked.
_BLOCK_OPENS = re.compile(r"(?is)<(div|p|td|li|h[1-6])\b[^>]*>\s*$")
_BLOCK_CLOSES = re.compile(r"(?is)\s*</(div|p|td|li|h[1-6])\s*>")

#: How far back to look for the block that opens a heading. A filer
#: writes a long style attribute and nothing else between the two.
_TAG_WIDEST = 300

#: What the filer wrote to mean bold, as a style declaration.
_BOLD = ("font-weight:700", "font-weight:bold")

#: Longer than this and a block typeset bold is a paragraph the filer
#: emphasised, not a heading over a section. Measured: every one of the
#: seventeen headings in Meta's Item 1 is between 8 and 50 characters,
#: and nothing in that section is bold, alone in its block, and longer.
_HEADING_WIDEST = 120

#: Every element a filer starts a new block of text with. Wider than the
#: set a heading may sit alone inside, because this one only has to say
#: where a block *begins*: a section title typeset into a table cell is
#: still a section title, and the row and the table around it open the
#: block just as a paragraph does.
_BLOCK_EDGE = re.compile(r"(?is)<\s*/?\s*(p|div|td|th|tr|table|li|h[1-6]|body)\b[^>]*>")


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

    def text_index(self, markup_at: int) -> int:
        """Where a position in the markup lands in the text read from it.

        The inverse of `markup_span`, and what lets structure found in
        the markup — a heading — be expressed as a position in the prose
        this platform actually reads and cites. Origins only ever rise,
        so the first character kept from a markup position onwards is
        the first origin that reaches it.
        """

        return bisect_left(self.origin, markup_at)


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


def read_regions(
    markup: str,
    flat: Flattened,
    start: int,
    end: int,
) -> tuple[Region, ...]:
    """
    The regions a section's own headings introduce, in its prose coordinates.

    Where the structural half of narrative ownership comes from. A
    heading is found in the markup — that is the only place it survives,
    since flattening turns bold into ordinary words — and is then
    expressed as a position in the prose the platform reads and cites, so
    that everything downstream can stay markup-free.

    Each region runs to the next heading, which is what makes it the
    smallest region the document offers. Bounding one at the end of the
    section instead would hand the last segment every word the filer
    wrote afterwards about competition, regulation and its workforce.

    Coordinates are relative to the section as a caller receives it,
    stripped, because a region that described a different string from the
    one being searched would be silently off by the document's leading
    whitespace.
    """

    opens, closes = flat.markup_span(start, end)

    raw = flat.text[start:end]
    lead = len(raw) - len(raw.lstrip())
    body = len(raw.strip())

    if body <= 0:
        return ()

    headings: list[tuple[int, str]] = []

    for at, heading in _headings(markup[opens:closes]):
        # From a position in the whole document's markup to one in the
        # section's own prose.
        where = flat.text_index(opens + at) - start - lead

        if 0 <= where < body:
            headings.append((where, heading))

    headings.sort()

    return tuple(
        Region(
            heading=heading,
            at=at,
            ends=headings[index + 1][0] if index + 1 < len(headings) else body,
        )
        for index, (at, heading) in enumerate(headings)
    )


def typesets_blocks(markup: str) -> bool:
    """Whether this document lays its text out in blocks at all.

    What `begins_a_block` may be asked about. A document carrying no
    block element offers no structure to prefer, and asking anyway is
    not merely useless but wrong: the first position in it begins a
    block trivially, because nothing precedes it — so an unstructured
    document would answer that its table-of-contents entry is the only
    real heading it has.
    """

    return _BLOCK_EDGE.search(markup) is not None


def begins_a_block(markup: str, flat: Flattened, at: int) -> bool:
    """
    Whether the filer began a block of text at this position in the prose.

    The difference between a section and a mention of it. A filer prints
    the words "Item 7. Management's Discussion and Analysis" over the
    section itself *and* inside sentences elsewhere in the document that
    refer to it — and flattened to prose the two are the same string, so
    nothing that reads the words alone can tell a heading from a
    cross-reference.

    The markup can. A heading opens its block; a cross-reference is
    part of a sentence, with the rest of that sentence typeset ahead of
    it. So the question asked here is only whether any words precede
    this one inside the block it sits in — deliberately weaker than
    `_headings`, which additionally requires bold and shortness. A
    section title is not always typeset bold, and one that runs to a
    hundred and twenty characters is ordinary.

    Measured across the calibration corpus: every correctly located
    section begins its block, and every cross-reference that had been
    competing with one carries between 127 and 540 characters of the
    sentence it belongs to.
    """

    opens, _ = flat.markup_span(at, at)

    last = 0

    for edge in _BLOCK_EDGE.finditer(markup, 0, opens):
        last = edge.end()

    return not _TAG.sub("", markup[last:opens]).replace("\xa0", " ").strip()


def _headings(markup: str) -> list[tuple[int, str]]:
    """
    Every heading this markup prints, as where it begins and what it says.

    A heading is a block element whose entire content is one short span
    typeset bold. That is the idiom, measured on filings rather than
    assumed: SEC filers do not use `<h1>`, and both of the headings that
    Meta's 10-K puts over its two segments are exactly this shape.

    Deliberately not a rule about what the heading *says*. Matching a
    heading to a segment is a separate judgement, made in the domain
    where the segment names live, and a detector that only admitted
    headings it recognised would decide that question here by accident.
    """

    found: list[tuple[int, str]] = []

    for match in _EMPHASIS.finditer(markup):
        tag, attrs, content = match.group(1), match.group(2), match.group(3)

        declared = attrs.replace(" ", "").casefold()

        if tag.casefold() not in ("b", "strong") and not any(
            weight in declared for weight in _BOLD
        ):
            continue

        # Alone in its block at both ends, or it is emphasis inside a
        # sentence rather than a heading over a section.
        before = markup[max(0, match.start() - _TAG_WIDEST) : match.start()]

        if not _BLOCK_OPENS.search(before):
            continue

        if not _BLOCK_CLOSES.match(markup, match.end()):
            continue

        heading = " ".join(flatten(content).text.split())

        if heading and len(heading) <= _HEADING_WIDEST:
            found.append((match.start(), heading))

    return found


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
