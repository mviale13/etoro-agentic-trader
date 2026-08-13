"""Read structural facts out of a filing, and refuse anything else."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    DescriptionRepair,
    EconomicRelationship,
    RevenueModel,
    SegmentDescription,
)
from app.domain.evidence import EvidenceNotApplicable, normalised
from app.domain.primary_source import SourceDocument
from app.domain.prose_evidence import Naming, Region, describes, namings, owning
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredShare,
    ReportedFigure,
    SourceTable,
    cited_number,
    cited_reference,
    figure_at,
)
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)

#: How much room the extraction gets. The business section runs to tens
#: of thousands of characters and the answer is a short structured list.
MAX_TOKENS = 8000

#: How many times a reading may be asked for before the failure stands.
#:
#: Quoting a filing verbatim is not reliably repeatable: measured over
#: Disney's 10-K, one attempt in three produced a span that survived the
#: grounding check, the others paraphrasing across a table boundary. The
#: contract is not what should give way — a retry asks the same question
#: again and holds the answer to the same rule, where relaxing the check
#: would let the paraphrase through.
MAX_ATTEMPTS = 3

#: Segments sum past a consolidated total, and legitimately: consolidated
#: revenue is the segments *less* what they sold each other. Measured,
#: Disney's three segments are 102% of its group revenue and Volkswagen's
#: three are 108.5% of its — the difference being how much business the
#: parts do with each other, which no constant can predict.
#:
#: So this is a backstop rather than the guard it once was. What catches
#: a misread figure now is the cell it was read from: two segments cannot
#: cite one cell, and a cell whose label does not correspond to the
#: segment is refused. This only has to separate heavy intersegment trade
#: from a segment counted twice, which in a three-segment company would
#: land near 140%. A mix past it is discarded rather than normalised,
#: because a silently rescaled revenue mix is a fabricated one.
SHARE_TOLERANCE = 1.25

MIX_SYSTEM_PROMPT = """\
You locate numbers in tables a company printed in its annual report. You
do not analyse the company, and you do not calculate anything at all.

You are given the tables exactly as they were parsed out of the document.
Every cell is addressed: `[table N]`, then `rR` for the row, then `cC`
for the column.

The columns are named by the first row that labels more than one of
them. That is usually `r0`, but a filer who typesets a title inside the
table — "Sales and Revenues by Segment" — puts it in `r0` alone, and
then `r1` names the columns. Read the rows you are given rather than
assuming which one it is.

Tables are laid out one of two ways, and both are normal:
- Segments as ROWS, periods as columns. Then the total is another row,
  and every segment cell sits in the SAME COLUMN as the total.
- Segments as COLUMNS, line items as rows. Then the total is another
  column — "Group", "Konzern", "Total" — and every segment cell sits in
  the SAME ROW as the total, the row for revenue.

Rules:
- First locate `total`: the one cell holding TOTAL revenue for the whole
  company, for the most recent period the table reports.
- Then, for each segment name you are given, locate the cell holding THAT
  SEGMENT's revenue. Use the names you are given and no others.
- Every segment cell must be in the SAME TABLE as the total, and must
  share either its row or its column with the total — whichever the
  table's layout calls for. Omit any segment whose revenue is not there.
- Never cite the naming row, any row above it, or column `c0`. They name
  the rows and columns and measure nothing.
- Never cite a cell holding a percentage, a change, a margin, an operating
  income or a label. Revenue only.
- `value` is the number that cell prints, written plainly: no thousands
  separators, no currency, no scale applied. 322,284 is 322284.
- Omit a segment rather than guess at it. Every cell you cite is read back
  out of the document and compared with what you said is in it, and an
  answer that disagrees with the document is discarded in full.
"""

REPAIR_SYSTEM_PROMPT = """\
You are given one claim a previous reading of this filing already made,
and the citation it offered for that claim, which was refused. Your only
job is to find a better citation for THE SAME claim.

You are not re-reading the document. You are not looking for a different
claim, a better claim, or another segment. The claim is fixed. The only
thing in question is which words of the filing evidence it.

Rules:
- Return one SHORT verbatim span — between five and fifteen words —
  copied exactly from the filing text, character for character, from a
  single run of prose. Do not join text across a table cell, a bullet or
  a line break, and do not tidy the wording.
- The span must sit where the filing names THIS segment, and must be
  what the document says about it. Not a sentence about the company as a
  whole, not a note about accounting or restated figures, and not words
  the filing prints under a different segment's name. That is why the
  previous citation was refused.
- If this filing contains no such span, return an empty `quoted`. That
  is a complete and correct answer. An honest empty answer is worth more
  here than a reached-for one, because a span that does not belong to
  this segment will be refused again and the claim will be recorded as
  unevidenced either way.
- You are asked once. There is no further attempt.
"""

ASKED_BY_NAME_SYSTEM_PROMPT = """\
A previous reading of this filing reported a segment and offered no
words describing it. Your only job is to answer, for THAT ONE segment:
does this filing print words that say what it does?

You are not re-reading the document, and you are not looking for other
segments or better claims. One segment, named below, once.

Rules:
- Return one SHORT verbatim span — between five and fifteen words —
  copied exactly from the filing text, character for character, from a
  single run of prose. Do not join text across a table cell, a bullet or
  a line break, and do not tidy the wording.
- The span must sit where the filing names THIS segment, and must be
  what the document says about it — what it makes, sells, operates or
  provides. A table's labels, headers and figures are not a description,
  and neither is a note about accounting, restated figures or legal
  form.
- If this filing prints no such words, return an empty `quoted`. That is
  a complete and correct answer, and on some filings it is the true one:
  a document can name its segments in a table and describe them nowhere
  this text reaches. An honest empty answer is worth more here than a
  reached-for one, because a span that does not describe this segment
  will be refused and the claim will be recorded as unevidenced either
  way.
- You are asked once. There is no further attempt.
"""

SUPPLEMENTAL_SYSTEM_PROMPT = """\
A reading of this company's tagged filing text reported a segment by
name and found no words describing it there. The text below is
different text: prose from the same filer's report, taken from around
the filer's own uses of that segment's name. Your only job is to
answer, for THAT ONE segment: does this prose say what it does, and
which ways of earning does it describe for it?

Rules:
- Return one SHORT verbatim span — between five and fifteen words —
  copied exactly from the text below, character for character, from a
  single run of prose. Do not join text across a table cell, a bullet
  or a line break, and do not tidy the wording.
- The span must sit where the text names THIS segment, and must be what
  the document says about it — what it makes, sells, operates or
  provides. Not a sentence about the company as a whole, not market
  commentary, not a note about emissions, accounting or legal form.
- Report the revenue models ONLY where this text describes that way of
  earning for THIS segment. A revenue model you cannot point at words
  for does not belong in the answer.
- If this text prints no such words, return an empty `quoted` and no
  revenue models. That is a complete and correct answer. An honest
  empty answer is worth more than a reached-for one, because a span
  that does not describe this segment will be refused and the claim
  recorded as unevidenced either way.
- You are asked once. There is no further attempt.
"""

RELATIONSHIP_SYSTEM_PROMPT = """\
You are asked one narrow question about a company's annual report: does
the filing EXPLICITLY STATE that one of its named businesses is
economically driven by another of the company's businesses, or by a
stated underlying demand engine?

You are looking for the filer's own causal or business-model sentences —
"the business model of X consists essentially in supporting sales of Y",
"deliveries of Y are decisive for new X contracts". Nothing else counts.

Rules:
- Report a relationship ONLY where the filing states it in so many
  words. NEVER infer one from a segment's name ("Financial Services",
  "Services", "Leasing" imply nothing). NEVER infer one from segments
  transacting with each other or from intersegment revenue. NEVER infer
  one from business logic you know from outside this text.
- `dependent` must be one of the segment names you are given, exactly
  as given.
- `driver` is what the filing says drives that business, in the
  filing's own terms — another business of the company, or the demand
  beneath it ("vehicle deliveries of the Group").
- `quoted` is one verbatim span copied from the text, character for
  character, containing the filer's causal or business-model claim.
- `statement` is the claim in plain English, continuing the frame
  "<company> states that this business …" (begin lowercase). PRESERVE
  the filer's own degree exactly: if the filing says "essentially" or
  "predominantly", your statement says so; never harden a qualified
  claim into total dependence, and never soften a stated one.
- Most filings state no such relationship. An empty list is the
  ordinary, correct answer, and it is worth more than a reached-for
  one: a relationship that is not stated in the text will be refused.
- You are asked once. There is no further attempt.
"""

SYSTEM_PROMPT = """\
You extract structural facts from a company's annual report. You do not
analyse the company, rate it, or classify it.

Rules:
- Use only the filing text supplied. Never use anything you know about
  the company from elsewhere.
- Report only segments the filing names. A segment the document never
  calls by name is not one of this company's, and reporting it discards
  the whole answer.
- Every segment you report must include `quoted`: a SHORT verbatim span
  copied from the filing text — between five and fifteen words, taken
  from a single run of prose. Copy it exactly, character for character.
  Do not join text across a table cell, a bullet or a line break, and do
  not tidy the wording.
- `quoted` must be what the filing says about THAT segment, taken from
  where the filing names it. Not a sentence about the company, not a note
  about accounting or restated figures, and not words that describe a
  different segment. Each segment needs its own span; the same sentence
  cannot describe two of them.
- A segment whose description you cannot find is still worth reporting.
  Give the name and leave `quoted` empty rather than reaching for a
  nearby sentence: an empty description is recorded as unknown, and a
  borrowed one is discarded.
- Report the revenue models the filing describes for each segment.
- Report no figures and no sizes. You are reading what the business is,
  not how large its parts are. Anything you could only get by reading a
  table belongs to a different question and is not asked here.
- Do not judge the company. Do not say whether a business is good, "high
  quality", durable, moaty, or attractive. You are reading, not deciding.
"""


class ExtractionRejected(Exception):
    """The extraction failed its grounding contract, with the reason worded."""


def extraction_schema() -> dict[str, Any]:
    """The structured contract an extraction must fill."""

    return {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": (
                    "One sentence on what the company does, from the filing."
                ),
            },
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "revenue_models": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [model.value for model in RevenueModel],
                            },
                        },
                        "quoted": {
                            "type": "string",
                            "description": (
                                "A verbatim span from the filing describing "
                                "this segment. Copied exactly."
                            ),
                        },
                    },
                    "required": [
                        "name",
                        "revenue_models",
                        "quoted",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["description", "segments"],
        "additionalProperties": False,
    }


def user_prompt(document: SourceDocument) -> str:
    source = document.source

    return "\n".join(
        (
            f"Company: {source.company}",
            f"Document: {source.stated()}",
            "",
            "Report the operating segments this document describes and what "
            "each one sells.",
            "",
            "--- DOCUMENT TEXT BEGINS ---",
            document.business_description,
            "--- DOCUMENT TEXT ENDS ---",
        )
    )


def _cell_schema(described: str) -> dict[str, Any]:
    """The address of one printed number, and what it is said to print."""

    return {
        "type": "object",
        "description": described,
        "properties": {
            "table": {"type": "integer"},
            "row": {"type": "integer"},
            "column": {"type": "integer"},
            "value": {
                "type": "number",
                "description": (
                    "The number this cell prints, with no separators, no "
                    "currency and no scale applied."
                ),
            },
        },
        "required": ["table", "row", "column", "value"],
        "additionalProperties": False,
    }


def mix_schema() -> dict[str, Any]:
    """
    The contract a revenue-mix reading must fill.

    Cells, not shares. A share is arithmetic over two figures, and asking
    a reading for the arithmetic is asking it for something the document
    does not contain — which is why the old contract's quotes could be
    exact and prove nothing. Here the reading points at two cells and the
    platform does the dividing.
    """

    segment = _cell_schema("The cell holding this segment's revenue.")

    properties = dict(segment["properties"])
    properties["segment"] = {"type": "string"}

    return {
        "type": "object",
        "properties": {
            "total": {
                "anyOf": [
                    _cell_schema("The cell holding total revenue."),
                    {"type": "null"},
                ],
                "description": (
                    "Null where no table reports a total revenue you can read."
                ),
            },
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": properties,
                    "required": [*segment["required"], "segment"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["total", "segments"],
        "additionalProperties": False,
    }


def repair_schema() -> dict[str, Any]:
    """
    The contract a repair fills, and everything it deliberately cannot.

    One field. There is nowhere here to put a segment name, a revenue
    model, or a correction to the claim — so a repair that wanted to
    change what is being claimed has no way to express it. The boundary
    between *evidence this claim* and *find an acceptable claim* is held
    by the shape of this object rather than by the wording above it.
    """

    return {
        "type": "object",
        "properties": {
            "quoted": {
                "type": "string",
                "description": (
                    "A verbatim span from the filing that the document "
                    "prints under this segment's own name, or empty if "
                    "the filing contains none."
                ),
            },
        },
        "required": ["quoted"],
        "additionalProperties": False,
    }


def repair_prompt(
    document: SourceDocument,
    segment: str,
    refused: str,
    refused_because: str,
) -> str:
    """One claim, its refused citation, and the filing it came from."""

    return "\n".join(
        (
            f"Company: {document.source.company}",
            f"Segment: {segment}",
            "",
            "The claim, unchanged: this filing describes what "
            f"{segment!r} does, and the previous reading cited these "
            "words for it:",
            f"  {refused!r}",
            "",
            "That citation was refused:",
            f"  {refused_because}",
            "",
            f"Find the words this filing prints under {segment!r} that say "
            "what it does, or return an empty span if it prints none.",
            "",
            "--- FILING BEGINS ---",
            document.business_description,
            "--- FILING ENDS ---",
        )
    )


def asked_by_name_prompt(document: SourceDocument, segment: str) -> str:
    """One segment the first reading left wordless, asked about by name."""

    return "\n".join(
        (
            f"Company: {document.source.company}",
            f"Segment: {segment}",
            "",
            f"A previous reading of this filing reported the segment "
            f"{segment!r} and offered no words describing it.",
            "",
            f"Find the words this filing prints under {segment!r} that say "
            "what it does, or return an empty span if it prints none.",
            "",
            "--- FILING BEGINS ---",
            document.business_description,
            "--- FILING ENDS ---",
        )
    )


#: How far either side of a name's occurrence the filer's prose is
#: taken, and how much of it one ask may carry. Measured on the one
#: multi-document package in the corpus: Volkswagen's division
#: descriptions sit within a few hundred characters of the division's
#: own name, and the digit-dense regions the same names head — delivery
#: tables, emission inventories — are what the prose filter exists to
#: drop.
_NEIGHBOURHOOD_RADIUS = 1_500
_NEIGHBOURHOOD_DIGIT_CEILING = 0.04
_NEIGHBOURHOOD_CAP = 24_000


def named_passage(
    text: str,
    name: str,
    *,
    radius: int = _NEIGHBOURHOOD_RADIUS,
    digit_ceiling: float = _NEIGHBOURHOOD_DIGIT_CEILING,
    cap: int = _NEIGHBOURHOOD_CAP,
) -> tuple[str, bool]:
    """The filer's prose around its own uses of one segment's name.

    No headings are hunted and no language is assumed: the anchor is the
    name the filer's tagged text already established, exactly as
    printed. Occurrences are merged into regions, regions that are
    mostly figures are dropped — a delivery table headed by a segment's
    name is not prose about it — and what remains is returned in
    document order under a stated cap. The second value says whether the
    cap dropped anything, because a truncation a reader cannot see would
    make "the text prints none" claim more than was checked.
    """

    if not name.strip():
        return "", False

    positions = []
    start = 0

    while True:
        found = text.find(name, start)

        if found < 0:
            break

        positions.append(found)
        start = found + 1

    if not positions:
        return "", False

    regions: list[tuple[int, int]] = []

    for hit in positions:
        low, high = max(0, hit - radius), min(len(text), hit + radius)

        if regions and low <= regions[-1][1]:
            regions[-1] = (regions[-1][0], high)
        else:
            regions.append((low, high))

    prose = []
    total = 0
    truncated = False

    for low, high in regions:
        passage = text[low:high]

        digits = sum(character.isdigit() for character in passage)

        if digits / max(1, len(passage)) >= digit_ceiling:
            continue

        if total + len(passage) > cap:
            truncated = True
            break

        prose.append(passage)
        total += len(passage)

    return "\n\n".join(prose), truncated


def supplemental_schema() -> dict[str, Any]:
    """The one-segment contract a supplemental reading must fill."""

    return {
        "type": "object",
        "properties": {
            "revenue_models": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [model.value for model in RevenueModel],
                },
            },
            "quoted": {
                "type": "string",
                "description": (
                    "A verbatim span from the text describing this "
                    "segment. Copied exactly, or empty."
                ),
            },
        },
        "required": ["revenue_models", "quoted"],
        "additionalProperties": False,
    }


def supplemental_prompt(
    document: SourceDocument,
    segment: str,
    passage: str,
) -> str:
    """One named segment, asked against the filer's untagged prose."""

    return "\n".join(
        (
            f"Company: {document.source.company}",
            f"Segment: {segment}",
            "",
            f"The tagged filing text named the segment {segment!r} and "
            "printed no words describing it. The prose below is from the "
            "same filer's report, around its own uses of that name.",
            "",
            f"Find the words this prose prints about {segment!r} that say "
            "what it does and how it earns, or return an empty span if it "
            "prints none.",
            "",
            "--- REPORT PROSE BEGINS ---",
            passage,
            "--- REPORT PROSE ENDS ---",
        )
    )


#: The relationship ask reads a tighter neighbourhood than the
#: description ask, on a measured property of its evidence: a causal
#: sentence *names the business it is about*, so the span sits within a
#: few hundred characters of the name — Volkswagen's business-model
#: sentence and its titled dependence disclosure both land inside a 21k
#: passage at radius 300, where the description path's wider radius
#: pushed them past its budget. E1's description constants are
#: untouched; these are this question's own.
_RELATIONSHIP_RADIUS = 300
_RELATIONSHIP_SEGMENT_CAP = 40_000


def relationship_schema() -> dict[str, Any]:
    """The structured contract a relationship reading must fill."""

    return {
        "type": "object",
        "properties": {
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dependent": {"type": "string"},
                        "driver": {"type": "string"},
                        "statement": {"type": "string"},
                        "quoted": {"type": "string"},
                    },
                    "required": ["dependent", "driver", "statement", "quoted"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["relationships"],
        "additionalProperties": False,
    }


def relationship_prompt(
    document: SourceDocument,
    segments: tuple[str, ...],
    passage: str,
) -> str:
    """The one relationship question, over the assembled passage."""

    return "\n".join(
        (
            f"Company: {document.source.company}",
            "",
            "Named businesses, exactly as reported. `dependent` must be "
            "one of these and no other:",
            *(f"- {name}" for name in segments),
            "",
            "Does this text explicitly state that one of those businesses "
            "is economically driven by another of the company's businesses "
            "or by a stated demand engine? Report only what is stated, or "
            "an empty list.",
            "",
            "--- REPORT TEXT BEGINS ---",
            passage,
            "--- REPORT TEXT ENDS ---",
        )
    )


#: English absolutes that may not appear in a relationship statement
#: unless the quoted span itself carries one — in any of the corpus's
#: filing languages. The guard for the rule that a filer's
#: "predominantly" must never harden into total dependence: refused by
#: a validator rather than merely asked for in a prompt, which is the
#: writer-contract lesson applied here.
_ABSOLUTE_STATED = (
    "entirely",
    "wholly",
    "exclusively",
    "solely",
    "100%",
    "completely",
    "only source",
)
_ABSOLUTE_QUOTED = (
    "entirely",
    "wholly",
    "exclusively",
    "solely",
    "100",
    "ausschließlich",
    "vollständig",
    "gänzlich",
    "uniquement",
    "exclusivement",
)


def faithful_quantifier(statement: str, quoted: str) -> bool:
    """Whether the statement's degree could have come from the quote.

    A heuristic with a stated limit: it catches the hardening this
    slice's ruling names — a qualified claim becoming an absolute one —
    and does not attempt the reverse direction or non-listed wording.
    """

    lowered = statement.casefold()

    if not any(term in lowered for term in _ABSOLUTE_STATED):
        return True

    span = quoted.casefold()

    # Casefolded on both sides: German "ß" folds to "ss", so a listed
    # "ausschließlich" would otherwise never match the folded span.
    return any(term.casefold() in span for term in _ABSOLUTE_QUOTED)


def mix_prompt(document: SourceDocument, segments: tuple[str, ...]) -> str:
    return "\n".join(
        (
            f"Company: {document.source.company}",
            "",
            "Segments, exactly as reported. Use these names and no others:",
            *(f"- {name}" for name in segments),
            "",
            "Locate total revenue, and each segment's revenue, in the tables "
            "below. Omit any segment whose revenue does not share a row or a "
            "column with the total, in the same table.",
            "",
            "--- TABLES BEGIN ---",
            *(table.stated() for table in document.performance_tables),
            "--- TABLES END ---",
        )
    )


class CompanyKnowledgeExtractor:
    """
    Turn a filing into structural facts, or into a worded refusal.

    The model reads; it never decides. What it returns is checked against
    the document it read: every segment carries a span the filing must
    actually contain, and an answer whose quotes are not there is
    discarded whole rather than partly trusted. A model cannot assert a
    segment into existence, because the assertion is not what is stored —
    the sentence from the filing is.

    Nothing here classifies. Which archetype these facts add up to is a
    rule's decision, taken later, from facts that have already survived
    this.
    """

    def __init__(self, provider: NarrativeProvider) -> None:
        self._provider = provider

    async def extract(
        self, symbol: str, document: SourceDocument
    ) -> CompanyKnowledgeObservation:
        """
        Read this document, asking again where the reading is not grounded.

        A rejection is not necessarily a fact about the document: a model
        asked to copy from a filing sometimes paraphrases, and the same
        question put again is usually answered exactly. So the request is
        repeated, and every attempt is held to the identical contract.
        The last failure's wording is what survives, because that is what
        a reader is owed when nothing could be read.
        """

        rejection: ExtractionRejected | None = None

        for _ in range(MAX_ATTEMPTS):
            try:
                return await self._attempt(symbol, document)
            except ExtractionRejected as rejected:
                rejection = rejected

        raise rejection or ExtractionRejected("The document could not be read.")

    async def _attempt(
        self,
        symbol: str,
        document: SourceDocument,
    ) -> CompanyKnowledgeObservation:
        request = DraftRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt(document),
            schema=extraction_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
        except NarrativeDeclined as declined:
            raise ExtractionRejected(str(declined)) from declined

        if not draft.text.strip():
            raise ExtractionRejected(
                "The extractor returned nothing, so no facts were read from the filing."
            )

        try:
            payload = json.loads(draft.text)
        except json.JSONDecodeError as error:
            raise ExtractionRejected(
                "The extractor returned unreadable output."
            ) from error

        knowledge = self._validated(symbol, document, payload, draft.model)

        repaired = await self._with_repaired_descriptions(knowledge, document, payload)

        measured = await self._with_revenue_mix(repaired, document)

        return await self._with_relationships(measured, document)

    async def _with_repaired_descriptions(
        self,
        knowledge: CompanyKnowledgeObservation,
        document: SourceDocument,
        payload: dict[str, Any],
    ) -> CompanyKnowledgeObservation:
        """
        One bounded second request per claim whose citation did not apply.

        **This is not a retry, and the difference is the whole design.**
        A retry asks the same open question again and takes whichever
        answer passes, which turns the reader's objective from *read this
        document* into *find something acceptable*. A repair asks a
        closed question about a claim that has already been made: these
        words were refused as evidence for it — is there better evidence
        in this document, or none?

        What makes that boundary real rather than instructed:

        - **The claim cannot move.** The second request supplies a span
          and nothing else; the ways of earning come from the first
          reading, and `repair_schema` has nowhere to put a new one.
        - **Exactly one attempt.** No loop, and a second request that
          fails is not asked again.
        - **The refusal still stands if it fails.** The span is held to
          the identical applicability contract, and an answer that
          cannot meet it leaves the description absent with both
          reasons.

        A segment the reading described with *no words at all* was once
        left exactly as it arrived, on the argument that it made no
        claim and asking would be searching for something acceptable.
        The defect taxonomy overturned that with a measurement: on one
        filing, two readings in five found describing words the other
        three returned empty — the words were in the document and the
        first pass's attention was the only thing that varied. So an
        empty arrival is now *asked about once, by name*: a closed
        question about one segment, whose honest answer may be that the
        text prints none — which is a finding, worded apart, not a
        failure. Every guard above applies unchanged, and the answer is
        recorded exactly as a repair is, so it is never presented as a
        first reading.

        Everything else about the segment — its name, its size, the other
        segments' descriptions — is untouched either way.
        """

        claimed = {
            str(raw.get("name") or "").strip(): raw
            for raw in payload.get("segments") or ()
        }

        prose = document.business_description
        named = tuple(seg.name for seg in knowledge.segments)

        partition = namings(prose, named)
        owners = owning(document.business_regions, named)

        segments = []

        for segment in knowledge.segments:
            raw = claimed.get(segment.name) or {}
            refused = str(raw.get("quoted") or "").strip()

            if segment.description is not None:
                segments.append(segment)
                continue

            if refused:
                outcome = await self._repaired(
                    segment,
                    document,
                    prose,
                    partition,
                    owners.get(segment.name),
                    raw,
                    refused,
                )
            else:
                outcome = await self._asked_by_name(
                    segment,
                    document,
                    prose,
                    partition,
                    owners.get(segment.name),
                    raw,
                )

            # A segment still wordless after the tagged text has been
            # asked twice, where the package carries untagged prose the
            # first reading was never shown. Volkswagen's five readings
            # each ended here — honestly, about text that genuinely
            # printed nothing — while the division descriptions sat in a
            # management report no tag reaches.
            if outcome.description is None and document.unstructured_text:
                outcome = await self._supplemental(outcome, document, named)

            segments.append(outcome)

        return replace(knowledge, segments=tuple(segments))

    async def _repaired(
        self,
        segment: BusinessSegment,
        document: SourceDocument,
        prose: str,
        partition: tuple[Naming, ...],
        owner: Region | None,
        raw: dict[str, Any],
        refused: str,
    ) -> BusinessSegment:
        """Ask once for better evidence, and hold the answer to the same rule."""

        first_refused_because = segment.undescribed_because or "It did not apply."

        request = DraftRequest(
            system_prompt=REPAIR_SYSTEM_PROMPT,
            user_prompt=repair_prompt(
                document,
                segment.name,
                refused,
                first_refused_because,
            ),
            schema=repair_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
            quoted = str(json.loads(draft.text).get("quoted") or "").strip()
        except (NarrativeDeclined, json.JSONDecodeError, ValueError) as failed:
            return _unrepaired(
                segment,
                first_refused_because,
                f"A repair was attempted and could not be read: {failed}",
            )

        if not quoted:
            return _unrepaired(
                segment,
                first_refused_because,
                "A repair was attempted, and the reader found no words in "
                "this filing that describe this segment.",
            )

        try:
            described = describes(prose, partition, segment.name, quoted, owner)
        except EvidenceNotApplicable as inapplicable:
            # The repair is held to the identical contract, so a second
            # inapplicable span changes nothing except that a reader now
            # knows the document was asked twice.
            return _unrepaired(
                segment,
                first_refused_because,
                f"A repair was attempted and was refused too: {inapplicable}",
            )

        # The claim, unchanged, now evidenced. The ways of earning are the
        # first reading's — a repair may not add one, and there is nowhere
        # in its contract to put one.
        return replace(
            segment,
            description=SegmentDescription(
                evidence=described,
                revenue_models=_models(raw),
                repair=DescriptionRepair(
                    first_refused_because=first_refused_because,
                    reader=draft.model,
                ),
            ),
            undescribed_because=None,
        )

    async def _asked_by_name(
        self,
        segment: BusinessSegment,
        document: SourceDocument,
        prose: str,
        partition: tuple[Naming, ...],
        owner: Region | None,
        raw: dict[str, Any],
    ) -> BusinessSegment:
        """One segment the first reading left wordless, asked about once.

        The closed question the empty arrival earns: does this filing
        print words that say what this one segment does? It reuses the
        repair's one-field contract deliberately — there is still
        nowhere to put a revenue model or a different segment — and its
        honest answer may be empty, which is worded as its own finding:
        an absence that survived being asked for by name is a fact
        about the text this platform reads, no longer about one pass's
        attention.
        """

        first = segment.undescribed_because or (
            f"The description of {segment.name!r} arrived with no words at all."
        )

        request = DraftRequest(
            system_prompt=ASKED_BY_NAME_SYSTEM_PROMPT,
            user_prompt=asked_by_name_prompt(document, segment.name),
            schema=repair_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
            quoted = str(json.loads(draft.text).get("quoted") or "").strip()
        except (NarrativeDeclined, json.JSONDecodeError, ValueError) as failed:
            return _unrepaired(
                segment,
                first,
                f"A follow-up by name was attempted and could not be read: {failed}",
            )

        if not quoted:
            return _unrepaired(
                segment,
                first,
                "Asked once more by name, the reader found no words "
                "describing it in the text this platform reads.",
            )

        try:
            described = describes(prose, partition, segment.name, quoted, owner)
        except EvidenceNotApplicable as inapplicable:
            return _unrepaired(
                segment,
                first,
                f"Asked once more by name, the span offered was refused "
                f"too: {inapplicable}",
            )

        # Described now — and claiming only what the first reading
        # claimed. A segment that arrived with words of earning and no
        # span keeps those models; one that arrived with neither is
        # described and names no way of earning, which is the narrower
        # honest claim rather than an invitation to add one.
        return replace(
            segment,
            description=SegmentDescription(
                evidence=described,
                revenue_models=_models(raw),
                repair=DescriptionRepair(
                    first_refused_because=first,
                    reader=draft.model,
                ),
            ),
            undescribed_because=None,
        )

    async def _supplemental(
        self,
        segment: BusinessSegment,
        document: SourceDocument,
        named: tuple[str, ...],
    ) -> BusinessSegment:
        """One wordless segment, asked against the filer's untagged prose.

        **This is a first reading, not a repair.** The repair doctrine —
        the claim cannot move, a span and nothing else — governs asking
        again about text a reading has already seen, where a new claim
        appearing on the second ask is suspicious by construction. The
        text supplied here is text no reading has seen: prose from the
        package's untagged documents, taken from around the filer's own
        uses of this segment's name. A way of earning read out of it for
        the first time is a first claim, held to the same evidence
        contract as the primary pass — the span must exist in the prose
        supplied, and it must sit under this segment's own naming, which
        is the positional ownership mechanism the partition provides.

        Bounded like everything else here: one segment, one ask, one
        attempt, and an honest empty answer recorded with both reasons.
        The passage builder's cap is stated in the absence wording when
        it dropped anything, because "the text prints none" must never
        claim more than was checked.
        """

        first = segment.undescribed_because or (
            f"The description of {segment.name!r} arrived with no words at all."
        )

        passage, truncated = named_passage(
            document.unstructured_text,
            segment.name,
        )

        if not passage:
            return replace(
                segment,
                undescribed_because=(
                    f"{first} The package's untagged report text prints no "
                    "prose around the filer's own uses of the name either."
                ),
            )

        checked = (
            f"the first {_NEIGHBOURHOOD_CAP:,} characters of it".replace(",", " ")
            if truncated
            else "all of it"
        )

        request = DraftRequest(
            system_prompt=SUPPLEMENTAL_SYSTEM_PROMPT,
            user_prompt=supplemental_prompt(document, segment.name, passage),
            schema=supplemental_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
            payload = json.loads(draft.text)
            quoted = str(payload.get("quoted") or "").strip()
        except (NarrativeDeclined, json.JSONDecodeError, ValueError) as failed:
            return _unrepaired(
                segment,
                first,
                "A reading of the package's untagged report text was "
                f"attempted and could not be read: {failed}",
            )

        if not quoted:
            return _unrepaired(
                segment,
                first,
                "Asked against the package's untagged report text "
                f"({checked}), the reader found no words describing it "
                "there either.",
            )

        try:
            described = describes(
                passage,
                namings(passage, named),
                segment.name,
                quoted,
                None,
            )
        except EvidenceNotApplicable as inapplicable:
            return _unrepaired(
                segment,
                first,
                "A span offered from the package's untagged report text "
                f"was refused: {inapplicable}",
            )

        return replace(
            segment,
            description=SegmentDescription(
                evidence=described,
                # A first reading of first-seen text may claim ways of
                # earning — that is what a first reading is. The models
                # are validated against the same vocabulary as the
                # primary pass and travel with the description they were
                # read beside, or not at all.
                revenue_models=_models(payload),
                repair=DescriptionRepair(
                    first_refused_because=(
                        f"{first} The words were found in the package's "
                        "untagged report text, which the tagged reading "
                        "is never shown."
                    ),
                    reader=draft.model,
                ),
            ),
            undescribed_because=None,
        )

    async def _with_relationships(
        self,
        knowledge: CompanyKnowledgeObservation,
        document: SourceDocument,
    ) -> CompanyKnowledgeObservation:
        """One bounded ask: does the filing state an economic dependence?

        Asked over the tagged business text plus each segment's tighter
        relationship neighbourhood of the untagged prose, because the
        two acceptance filers keep this evidence in different places —
        Caterpillar's role sentence sits in its Item 1, Volkswagen's in
        the untagged management report. Every claim that comes back is
        held to the full contract: the dependent must be a named
        segment, the span must exist in the supplied text under that
        segment's own naming, and a statement that hardens the filer's
        qualifier into an absolute is refused. A claim that fails any
        of it is dropped — an unproven relationship is an absence, not
        a hedge. Empty is the ordinary answer and an evidence state.
        """

        named = tuple(segment.name for segment in knowledge.segments)

        if not named:
            return knowledge

        sections = [document.business_description]

        for name in named:
            neighbourhood, _ = named_passage(
                document.unstructured_text,
                name,
                radius=_RELATIONSHIP_RADIUS,
                cap=_RELATIONSHIP_SEGMENT_CAP,
            )

            if neighbourhood:
                sections.append(neighbourhood)

        passage = "\n\n".join(sections)

        request = DraftRequest(
            system_prompt=RELATIONSHIP_SYSTEM_PROMPT,
            user_prompt=relationship_prompt(document, named, passage),
            schema=relationship_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
            payload = json.loads(draft.text)
        except (NarrativeDeclined, json.JSONDecodeError, ValueError):
            # The question could not be asked; the observation stands
            # without it, which reads exactly as a filing that states
            # nothing — the conservative direction for this claim.
            return knowledge

        partition = namings(passage, named)

        accepted: list[EconomicRelationship] = []

        for raw in payload.get("relationships") or ():
            dependent = str(raw.get("dependent") or "").strip()
            driver = str(raw.get("driver") or "").strip()
            statement = str(raw.get("statement") or "").strip()
            quoted = str(raw.get("quoted") or "").strip()

            if dependent not in named or not driver or not statement or not quoted:
                continue

            if not faithful_quantifier(statement, quoted):
                continue

            try:
                describes(passage, partition, dependent, quoted, None)
            except EvidenceNotApplicable:
                continue

            accepted.append(
                EconomicRelationship(
                    dependent=dependent,
                    driver=driver,
                    statement=statement,
                    quoted=quoted,
                )
            )

        if not accepted:
            return knowledge

        # One claim per dependent: a reading that offered two answers
        # for one business did not settle which it meant, and picking
        # would be this platform choosing the claim it prefers.
        by_dependent: dict[str, EconomicRelationship] = {}
        duplicated: set[str] = set()

        for relationship in accepted:
            if relationship.dependent in by_dependent:
                duplicated.add(relationship.dependent)
            else:
                by_dependent[relationship.dependent] = relationship

        return replace(
            knowledge,
            relationships=tuple(
                relationship
                for dependent, relationship in by_dependent.items()
                if dependent not in duplicated
            ),
        )

    async def _with_revenue_mix(
        self,
        knowledge: CompanyKnowledgeObservation,
        document: SourceDocument,
    ) -> CompanyKnowledgeObservation:
        """
        How large each segment is, measured out of the tables that state it.

        A second reading, of a second section, because the two facts live
        apart: Item 1 describes the segments and reports no figures, and
        the discussion reports the figures against names it assumes you
        already have. Knowing that a company sells subscriptions, tickets
        and licences is directional; knowing which of them is most of the
        revenue is the fact a classification can rest on.

        And it is a reading of the *tables*, not of the prose beside them.
        A share is not something a filing says; it is arithmetic over two
        figures a filing prints, and a span quoted from flattened prose
        cannot show that a number belongs to the row it was found next to.
        So the reading locates cells, this platform reads those cells back
        out of the document, and it divides one by the other itself.

        A filing whose tables could not be read, or in which no total was
        found, keeps its segments and leaves their sizes absent. That is
        the honest outcome and the shares are never apportioned from what
        is left over.
        """

        if not knowledge.segments:
            return knowledge

        if not document.performance_tables:
            return _unmeasured(knowledge, _no_tables(document))

        request = DraftRequest(
            system_prompt=MIX_SYSTEM_PROMPT,
            user_prompt=mix_prompt(
                document,
                tuple(segment.name for segment in knowledge.segments),
            ),
            schema=mix_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
            payload = json.loads(draft.text)
        except (NarrativeDeclined, json.JSONDecodeError):
            # The segments stand; only their sizes are unread.
            return _unmeasured(
                knowledge,
                "The reading of this filing's tables did not complete, so no "
                "figure was located for any segment. Nothing here is a "
                "statement about the filing.",
            )

        measured = self._measured(knowledge, document.performance_tables, payload)

        if not measured:
            return _unmeasured(
                knowledge,
                "No table in this filing's performance discussion was read as "
                "reporting a total revenue, so there was nothing to measure a "
                "segment against.",
            )

        return replace(
            knowledge,
            segments=tuple(
                replace(
                    segment,
                    revenue=measured.get(segment.name.casefold()),
                    unmeasured_because=(
                        None
                        if segment.name.casefold() in measured
                        else (
                            "The reading located no cell reporting this "
                            "segment's revenue in the tables this filing's "
                            "performance discussion prints, though it located "
                            "the total and other segments' figures there."
                        )
                    ),
                )
                for segment in knowledge.segments
            ),
        )

    def _measured(
        self,
        knowledge: CompanyKnowledgeObservation,
        tables: tuple[SourceTable, ...],
        payload: dict[str, Any],
    ) -> dict[str, MeasuredShare]:
        """
        Each segment's size, checked against the cells it was read from.

        Every one of them is measured against the *same* total cell. A
        mix whose segments were each divided by a different denominator
        would not be a mix of anything — the parts would not be parts of
        one whole — and requiring one denominator makes the shares add up
        to something a reader can interpret rather than a coincidence.
        """

        try:
            total = self._total(tables, payload.get("total"))
        except EvidenceNotApplicable as inapplicable:
            raise ExtractionRejected(str(inapplicable)) from inapplicable

        if total is None:
            return {}

        known = {segment.name.casefold() for segment in knowledge.segments}

        measured: dict[str, MeasuredShare] = {}
        cited: set[CellReference] = {total.cell}

        for raw in payload.get("segments") or ():
            name = str(raw.get("segment") or "").strip()

            if name.casefold() not in known:
                raise ExtractionRejected(
                    f"The revenue mix names a segment, {name!r}, that the "
                    "filing's business description never reported."
                )

            try:
                figure = figure_at(
                    tables,
                    cited_reference(raw),
                    cited_number(raw, "value"),
                    f"The revenue of {name!r}",
                )

                if figure.cell in cited:
                    raise EvidenceNotApplicable(
                        f"The revenue of {name!r} cites a cell already read as "
                        "another figure, so one of the two is not what it "
                        "was said to be."
                    )

                share = MeasuredShare(numerator=figure, denominator=total)

                # Against the coordinate that names the part, which is
                # the row where the segments run down the page and the
                # column header where they run across it.
                if not _corresponds(name, share.part):
                    raise EvidenceNotApplicable(
                        f"The revenue of {name!r} cites a cell the filing "
                        f"labels {share.part!r}, which is a different thing."
                    )

                measured[name.casefold()] = share
            except (EvidenceNotApplicable, TypeError, ValueError) as inapplicable:
                raise ExtractionRejected(str(inapplicable)) from inapplicable

            cited.add(figure.cell)

        stated = sum(share.share for share in measured.values())

        if stated > SHARE_TOLERANCE:
            raise ExtractionRejected(
                f"The measured revenue shares sum to {stated:.0%} of "
                f"{total.printed}, which cannot be a share of one company's "
                "revenue. The mix was discarded rather than rescaled."
            )

        return measured

    @staticmethod
    def _total(
        tables: tuple[SourceTable, ...],
        raw: Any,
    ) -> ReportedFigure | None:
        """The cell every segment is measured against, or nothing at all."""

        if not isinstance(raw, dict):
            # No table reported a total this reading could locate. The
            # segments keep their descriptions and lose their sizes,
            # which is the honest outcome rather than a failure.
            return None

        try:
            return figure_at(
                tables,
                cited_reference(raw),
                cited_number(raw, "value"),
                "The company's total revenue",
            )
        except (TypeError, ValueError) as unreadable:
            raise EvidenceNotApplicable(
                "The total revenue arrived without a number, so nothing "
                "could be measured against it."
            ) from unreadable

    def _validated(
        self,
        symbol: str,
        document: SourceDocument,
        payload: dict[str, Any],
        model: str,
    ) -> CompanyKnowledgeObservation:
        description = str(payload.get("description") or "").strip()

        if not description:
            raise ExtractionRejected(
                "The extractor described no business, so nothing was read."
            )

        prose = document.business_description

        named = tuple(
            str(raw.get("name") or "").strip() for raw in payload.get("segments") or ()
        )

        # The document's own naming of its segments, which partitions the
        # prose the way row labels partition a table. Computed here, once,
        # from the document — never taken from the reading.
        partition = namings(prose, tuple(name for name in named if name))

        # And its own structure, where it has any: the section each
        # segment is described in, which owns a description more directly
        # than the segment's nearest mention does. A segment with no
        # region here falls back to the partition above.
        owners = owning(document.business_regions, tuple(n for n in named if n))

        segments = tuple(
            self._segment(raw, prose, partition, owners)
            for raw in payload.get("segments") or ()
        )

        source = document.source

        return CompanyKnowledgeObservation(
            symbol=symbol.upper().strip(),
            description=description,
            segments=segments,
            source=source,
            reading=Provenance(
                source=f"{source.identifier} via {source.provider}, read by {model}",
                observed_at=datetime.now(UTC),
            ),
        )

    @staticmethod
    def _segment(
        raw: dict[str, Any],
        prose: str,
        partition: tuple[Naming, ...],
        owners: dict[str, Region],
    ) -> BusinessSegment:
        """
        One segment, with each of its claims held to its own contract.

        Identity is checked first and hardest, because everything else
        hangs off it: a segment the document never names is not a segment
        of that company, however confidently it was reported, and the
        whole reading goes rather than one part of it.

        The description is checked next and fails *alone*. It used to be
        the thing that proved the segment existed, so a citation that did
        not apply took the segment's name and its measured size with it —
        facts that had been established by something else entirely. Now
        an inapplicable description leaves the segment standing and says
        nothing about what it does.
        """

        name = str(raw.get("name") or "").strip()

        if not name:
            raise ExtractionRejected("A segment arrived without a name.")

        # Identity. The document naming it is what makes it a part of
        # this company — and unlike a span the reading chose, this is
        # something the platform went and found.
        if not any(naming.segment == name for naming in partition):
            raise ExtractionRejected(
                f"The reading reports a segment, {name!r}, that the filing "
                "never names. The whole reading was discarded."
            )

        models = _models(raw)

        try:
            described = describes(
                prose,
                partition,
                name,
                str(raw.get("quoted") or ""),
                owners.get(name),
            )
        except EvidenceNotApplicable as inapplicable:
            # Absent, not fatal. The segment is real, its size may well be
            # measured, and what it does is simply not something this
            # document was shown to say. The reason travels with the
            # absence, because "the filing says nothing about this" and
            # "the reading cited another segment's words" are different
            # facts and only one of them is about the filing.
            return BusinessSegment(
                name=name,
                revenue=None,
                description=None,
                undescribed_because=str(inapplicable),
            )

        return BusinessSegment(
            name=name,
            revenue=None,
            description=SegmentDescription(evidence=described, revenue_models=models),
        )


def _models(raw: dict[str, Any]) -> tuple[RevenueModel, ...]:
    """The ways of earning a reading claimed, as this platform holds them.

    Shared by the first reading and by a repair, because a repair
    evidences the *same* claim: the models it ends up carrying must be
    the ones already asserted, read out of the same payload, rather than
    anything the second request had a chance to influence.
    """

    return tuple(
        RevenueModel(value)
        for value in raw.get("revenue_models") or ()
        if value in {model.value for model in RevenueModel}
    )


def _unrepaired(
    segment: BusinessSegment,
    first_refused_because: str,
    outcome: str,
) -> BusinessSegment:
    """A claim whose evidence could not be repaired, with both reasons.

    Deliberately two sentences rather than one. Why the first citation
    was refused is a fact about that citation; that a repair was
    attempted and did not succeed is a fact about this platform's
    effort, and a reader deciding whether the gap is worth chasing needs
    both. Everything else about the segment is untouched.
    """

    return replace(
        segment,
        description=None,
        undescribed_because=f"{first_refused_because} {outcome}",
    )


#: Shorter than this and a located section is not the discussion itself.
#: Measured: JPMorgan's Item 7 is 395 characters, all of them saying on
#: which pages of a separately filed document the discussion appears.
#: The four filings that carry their own discussion run from 28,000 to
#: 80,000, so nothing sits near this line.
_STUB_WIDEST = 2_000


def _unmeasured(
    knowledge: CompanyKnowledgeObservation, because: str
) -> CompanyKnowledgeObservation:
    """Every segment's size absent, and every one of them saying why.

    The reason belongs on each segment rather than on the reading,
    because a size is a claim about a segment and its absence is too —
    and because sizes fail one at a time as well as all at once, so a
    reader who found the explanation somewhere else would have to know
    which kind of failure this had been to know where to look.
    """

    return replace(
        knowledge,
        segments=tuple(
            segment
            if segment.revenue is not None
            else replace(segment, unmeasured_because=because)
            for segment in knowledge.segments
        ),
    )


def _no_tables(document: SourceDocument) -> str:
    """Why a filing's performance discussion yielded no table to read.

    Three different facts, and only the last is about the company being
    unusual. A section this platform never located, a section that is a
    pointer to a document filed separately, and a discussion that really
    does print no table of segment revenue call for three different
    responses — and reported as one sentence they would call for none.
    """

    discussion = document.performance_discussion.strip()

    if not discussion:
        return (
            "This platform located no management's discussion in this filing, "
            "so it read no tables and measured no segment. This is a fact "
            "about the reading, not about the company."
        )

    if len(discussion) <= _STUB_WIDEST:
        return (
            f"This filing's management discussion is {len(discussion):,} "
            "characters long and prints no table, which makes it a pointer to "
            "a document filed separately rather than the discussion itself. "
            "The figures exist; they are not in the document this platform read."
        )

    return (
        "This filing's management discussion prints no table this platform "
        "could read a figure out of, so no segment was measured."
    )


def _corresponds(name: str, label: str) -> bool:
    """
    Whether a filing's own label and a segment name are the same thing.

    The last applicability check, and the one the live failure needed: a
    cell whose figure is real, in the right table and on the right axis,
    and about a different part of the company. The two readings are of
    two sections, so the wording is rarely identical — "Experiences" is
    labelled "Experiences" in one and "Experiences segment" in the other
    — and containment either way is what tolerates that without
    tolerating a different part.
    """

    segment, printed = normalised(name), normalised(label)

    if not segment or not printed:
        return False

    return segment in printed or printed in segment
