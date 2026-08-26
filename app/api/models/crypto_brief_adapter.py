"""What the investor is being told, and why — composed, never authored.

**This is Communication, not the CIO, and the package matters.** It was
written under `app/cio/` and the intelligence layer's own import guard
rejected it: nothing in `app/cio/` may import `crypto_intelligence`,
because what is *happening* must never reach what is *decided*. The
guard was right and the placement was wrong. This layer reads a
decision that has already been made and explains it; it cannot feed
back into one, and living beside the other dossier adapters is what
makes that structural rather than a promise.

The crypto Overview was measured as *"a well-organized evidence report
rather than a CIO product"*: the course and its meaning were printed
twice, the conclusion read as a statement about the platform
(*"what these conclusions are worth to an investment case is not
established by this platform"*), and the three summary widgets carried
equal weight while carrying very unequal density.

This layer answers **why the asset is worth researching at all** and
supplies the one-line
setup the hero states beneath the course. *What would change the view*
was measured out of it: **not one watch item in the corpus resolves any
blocker** (7 blockers, 10 watch items, 0 connections), because a
blocker's refs are source names and committee keys while a watch item's
are metric refs. The research plan answers that question from the
blocker instead, and watch items stay where they belong, as contextual
evidence under Developments.

**What blocks capital moved out.** The blockers were listed here *and*
in the research plan, which names each one's resolution — the same kind
of information under two owners, and the plan is the only one of the
two that renders a blocker with what would settle it. The blocking side
is still derived here, because the setup sentence is built from it; it
is no longer carried as a field.

**It composes and it never authors.** Every sentence here is quoted
from the layer that owns it: a `Driver` from the intelligence snapshot,
an `UnresolvedQuestion` from the committee that raised it, a material
uncertainty from the assessment, a `WatchItem` from the intelligence
layer. Invariant 10 is the whole constraint — an established fact may
travel upward without its economic interpretation travelling with it,
and this layer receives facts that already carry their own words. It
adds headings, an order, and one connective. Nothing else.

**A précis quotes the claim and keeps the qualification beneath it.**
The domain's sentences are built to stand alone, so several carry a
claim and then qualify it: *"No mechanical issuance rule is held for
this asset. That is a statement about what this platform has read, not
about what the protocol does."* A hero line cannot carry both. So a
`BriefLine` splits them — `stated` is the claim clause, `qualification`
is the remainder — and both travel, with the full sentence recoverable
by joining them. The claim is never restated in this layer's own words,
which is the difference between a précis and a summary.

**Case is never repaired.** Joining two quoted clauses into one
sentence needs the second one lowercased, and lowercasing a clause that
opens on a proper noun corrupts it — the failure #99's validator
already found in the other direction, where *capitalised* was mistaken
for *a name*. So the joiner lowercases only openers it explicitly
recognises, and where it does not recognise one it emits two sentences
instead of one mangled sentence. There is no heuristic and nothing to
tune.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.cio.digital_asset_decision import DigitalAssetDecision
from app.domain.crypto_intelligence import (
    CryptoIntelligenceSnapshot,
    Direction,
)

#: How many findings each block carries on the Overview.
#:
#: Two, measured rather than chosen: at three the mobile Overview ran
#: 3,239px against a 2,600px target, and the brief alone was 1,021px of
#: it. A block that holds more says how many, so a capped list never
#: reads as a complete one and the rest is one tab away under Evidence.
BLOCK_LIMIT = 2

#: How many clauses a side of the setup sentence may quote. Two, because
#: one drops a finding the investor's eye is already on and three stops
#: being a sentence.
SETUP_CLAUSES = 2

#: Clause openers this layer may lowercase when joining. Every one is a
#: closed-class English word that no proper noun begins with, so the
#: transform is safe by construction rather than by inspection. An
#: opener outside this set is not a failure — the joiner emits two
#: sentences and the reader loses nothing.
LOWERCASEABLE = frozenset(
    {
        "a",
        "an",
        "available",
        "circulating",
        "economic",
        "every",
        "fee",
        "holder",
        "network",
        "no",
        "nothing",
        "several",
        "the",
        "these",
        "this",
        "tokens",
        "total",
        "trading",
        "two",
    }
)


def _split(sentence: str) -> tuple[str, str | None]:
    """The claim clause of a *decision-owned* sentence, and its qualification.

    **One splitter may not be pointed at two sentence shapes**, which
    the corpus proved on the first run. The decision's own sentences
    qualify themselves — *"No mechanical issuance rule is held for this
    asset. That is a statement about what this platform has read…"*,
    *"Tokens in existence cannot be stated as a single figure:
    available estimates run from 586.86 million to…"* — so a full stop
    or a colon separates a claim from its support.

    An intelligence driver does not have that shape. Its colon carries a
    **category**: *"Token economics: Hyperliquid Reports Strong Revenue,
    Supply Burn, and Ecosystem Expansion"*. Splitting it left the brief
    asserting *"Token economics"* as a finding, and TAO rendered that
    non-sentence twice in one block. So this function is applied to
    decision-owned sentences only, and drivers and watch items are
    quoted whole.

    The colon still has to earn its cut even here: it separates a claim
    from a continuation only where what follows is a continuation, and a
    continuation is lowercase. A capitalised right-hand side is a title,
    and the sentence is kept whole. It fails toward saying more, never
    toward inventing a claim.
    """

    text = sentence.strip()

    stop = text.find(". ")

    colon = text.find(": ")
    if colon != -1 and not text[colon + 2 : colon + 3].islower():
        colon = -1

    cuts = [x for x in (stop, colon) if x != -1]

    if not cuts:
        return text.rstrip("."), None

    cut = min(cuts)

    return text[:cut].rstrip("."), text[cut + 2 :].strip()


def _joinable(clause: str) -> str | None:
    """The clause lowercased for mid-sentence use, or None if unsafe."""

    first = clause.split(" ", 1)[0] if clause else ""

    if first.lower() not in LOWERCASEABLE:
        return None

    # Only the first character moves. A clause reading "No mechanical
    # issuance rule…" becomes "no mechanical issuance rule…" and every
    # other character, including an interior name, is untouched.
    return clause[0].lower() + clause[1:]


@dataclass(frozen=True, slots=True)
class BriefLine:
    """One quoted finding, with its owner and its own qualification."""

    #: The claim clause, in the owning layer's exact words.
    stated: str

    #: Who established it — a committee, the assessment, the
    #: intelligence layer. Never this layer.
    owner: str

    #: The remainder of the owning layer's sentence, where it qualified
    #: its own claim. Rendered beneath, never merged into a headline.
    qualification: str | None = None

    #: How the owning layer describes the evidence beneath it.
    support: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "stated": self.stated,
            "owner": self.owner,
            "qualification": self.qualification,
            "support": self.support,
        }


@dataclass(frozen=True, slots=True)
class CryptoInvestorBrief:
    """The Overview's answer: the view, what blocks it, what would move it."""

    symbol: str

    #: The course, stated once. The hero renders it; nothing else may.
    course: str

    #: What the course means for capital, in the decision's own terms —
    #: also stated once, and never repeated in a second card.
    course_means: str

    #: One sentence: what is supportive, and what is not established.
    #: None where neither side has anything to quote, in which case
    #: `setup_absent` says so.
    setup: str | None

    setup_absent: str | None

    current_view: tuple[BriefLine, ...] = ()
    current_view_absent: str | None = None

    #: How many findings each block is holding back, so a capped list
    #: never reads as a complete one.
    withheld: tuple[tuple[str, int], ...] = ()

    #: The platform boundary, carried once for the audit surface rather
    #: than the brief. Kept so the Overview can link to it without
    #: reprinting it.
    boundary: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "course": self.course,
            "course_means": self.course_means,
            "setup": self.setup,
            "setup_absent": self.setup_absent,
            "current_view": [line.as_dict() for line in self.current_view],
            "current_view_absent": self.current_view_absent,
            "withheld": [
                {"block": block, "count": count} for block, count in self.withheld
            ],
            "boundary": self.boundary,
        }


def _current_view(
    snapshot: CryptoIntelligenceSnapshot | None,
) -> tuple[list[BriefLine], int]:
    """What is supportive or contextual right now, in the drivers' words.

    Adverse drivers are deliberately absent: they are a risk, and this
    platform files them with the uncertainties rather than with the
    view. The decision layer already refuses to license an adverse
    reading of a structural conclusion, and a driver that cuts against
    the holder belongs beside what blocks progress.
    """

    if snapshot is None:
        return [], 0

    lines = [
        BriefLine(
            stated=driver.stated.rstrip("."),
            owner="Intelligence",
            qualification=driver.matters_because,
            support=driver.support.stated,
        )
        for driver in snapshot.drivers
        if driver.direction is not Direction.ADVERSE
    ]

    return lines[:BLOCK_LIMIT], max(0, len(lines) - BLOCK_LIMIT)


def _blocks_progress(
    decision: DigitalAssetDecision,
    snapshot: CryptoIntelligenceSnapshot | None,
) -> tuple[list[BriefLine], int]:
    """What stops the case progressing — open questions first.

    An unresolved committee question and a material uncertainty are
    different objects and stay in that order: a question nobody could
    answer constrains the case more than a figure two sources disagree
    about, and the decision layer owns the first while the assessment
    owns the second. Adverse developments join them last, because a
    development is current and the other two are structural.
    """

    lines: list[BriefLine] = []

    for question in decision.unresolved:
        claim, qualification = _split(question.stated)
        lines.append(
            BriefLine(stated=claim, owner=question.owner, qualification=qualification)
        )

    for uncertainty in decision.material_uncertainties:
        claim, qualification = _split(uncertainty)
        lines.append(
            BriefLine(
                stated=claim,
                owner="Investor assessment",
                qualification=qualification,
            )
        )

    for driver in snapshot.drivers if snapshot else ():
        if driver.direction is Direction.ADVERSE:
            lines.append(
                BriefLine(
                    stated=driver.stated.rstrip("."),
                    owner="Intelligence",
                    qualification=driver.matters_because,
                    support=driver.support.stated,
                )
            )

    return lines[:BLOCK_LIMIT], max(0, len(lines) - BLOCK_LIMIT)


#: How long the setup line may run before it stops being one sentence a
#: reader takes in at a glance. Measured against the corpus rather than
#: chosen: TAO's two committee clauses are 92 and 88 characters, and
#: joining both sides produced a 271-character sentence nobody would
#: read. Over this, each side quotes one clause instead of two.
SETUP_LIMIT = 200


def _side(clauses: list[str]) -> str | None:
    """One side of the setup, with every clause after the first joined in.

    The first clause opens the sentence and keeps its capital. Every
    clause after it is mid-sentence and must be lowercased, on either
    side of the connective — the first run left *"…and The asset has
    moved +37% over a month"* on the supportive side because only the
    blocked side was being lowered. Where a clause cannot be safely
    lowered, the side is refused rather than corrupted.
    """

    if not clauses:
        return None

    # The first clause opens the side and is quoted as it stands, so a
    # side that has anything to say always says something. Refusing the
    # whole side on an unlowerable *second* clause dropped ETH's three
    # supportive findings and left its setup opening on a blocker — a
    # side that degrades to one clause loses a finding the block below
    # still carries, and a side that vanishes loses the investor's half
    # of the sentence.
    joined = [clauses[0]]

    for clause in clauses[1:]:
        lowered = _joinable(clause)

        if lowered is None:
            break

        joined.append(lowered)

    return " and ".join(joined)


def _setup(
    supportive: list[BriefLine],
    blocking: list[BriefLine],
) -> tuple[str | None, str | None]:
    """One sentence: what holds up, set against what is not established.

    Composed from quoted clauses and one connective. Where the join
    cannot be made safely — an opener this layer will not lowercase —
    it degrades to two intact sentences rather than one corrupted one,
    and where it would run long it quotes one clause a side.
    """

    if not supportive and not blocking:
        return None, (
            "Nothing is currently established either for or against this "
            "asset, so no setup is stated. That is a statement about what "
            "this platform holds, not about the asset."
        )

    for take in (SETUP_CLAUSES, 1):
        left = _side([line.stated for line in supportive[:take]])
        right = _side([line.stated for line in blocking[:take]])

        if left is None and right is None:
            continue

        if left is None or right is None:
            sentence = f"{left or right}."
        else:
            lowered = _joinable(right)
            sentence = (
                f"{left}, but {lowered}."
                if lowered is not None
                else f"{left}. {right}."
            )

        if len(sentence) <= SETUP_LIMIT or take == 1:
            return sentence, None

    # Every clause opens on a word this layer will not lowercase, on
    # both sides. The blocks below still carry all of it.
    return None, (
        "The findings held for this asset cannot be stated as one line "
        "without rewording them, so they are stated in full below."
    )


def brief_for(
    decision: DigitalAssetDecision,
    snapshot: CryptoIntelligenceSnapshot | None,
) -> CryptoInvestorBrief:
    """Compose the Overview's brief from evidence that already has words."""

    view, view_withheld = _current_view(snapshot)
    blocked, _ = _blocks_progress(decision, snapshot)

    setup, setup_absent = _setup(view, blocked)

    withheld = tuple(
        (block, count) for block, count in (("current_view", view_withheld),) if count
    )

    return CryptoInvestorBrief(
        symbol=decision.symbol,
        course=decision.state.value
        if hasattr(decision.state, "value")
        else str(decision.state),
        course_means="No capital action is suggested." if decision.ceiling else "",
        setup=setup,
        setup_absent=setup_absent,
        current_view=tuple(view),
        current_view_absent=None
        if view
        else (
            "No driver is currently held for this asset. Nothing is "
            "asserted about what is moving it."
        ),
        withheld=withheld,
        boundary=decision.ceiling,
    )
