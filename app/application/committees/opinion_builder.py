"""Compose a committee opinion from a finding ledger, by named rule.

Deterministic and total. The same ledger, remit and inputs produce the
same opinion, every time. Nothing here reads a document, asks a model
or consults a provider: it counts findings whose sense another layer
recorded, and applies one table.

The table is the whole of the judgment, and it is judgment about
*counts*, never about the company. Which findings exist is the
signals' business; this decides only what a set of them adds up to,
and it names the rule that decided so the answer can be argued with
rather than believed.

## Stance and confidence are orthogonal, on purpose

A committee that read two favourable findings out of a remit where
three of four inputs went unmeasured is *positive, on thin evidence* —
not *slightly positive*. Folding completeness into the stance is the
defect this platform already fixed once at the old committee layer,
where reporting the score as confidence meant a bearish view was by
construction a tentative one and a SELL could never be stated with
conviction. The stance says which way the findings point; the
confidence says how much was seen. Neither is allowed to soften the
other.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.committee.opinion import (
    CommitteeOpinion,
    Confidence,
    Stance,
    Uncertainty,
    UncertaintyKind,
)
from app.domain.finding import Dimension, FindingLedger, Sense

#: A committee shown nothing in its remit has no position to take.
#: Distinct in kind from every rule below it: those weigh findings,
#: this one reports that there were none.
RULE_NO_FINDINGS = "stance-abstains-without-findings-in-remit"

#: Unopposed, and more than a single observation. One favourable
#: finding with nothing against it is positive; it is not *strongly*
#: anything, because a lone observation is as easily a gap in reading
#: as a one-sided case.
RULE_UNOPPOSED_FAVOURABLE = "stance-strongly-positive-on-unopposed-findings"
RULE_UNOPPOSED_ADVERSE = "stance-strongly-negative-on-unsupported-findings"

RULE_FAVOURABLE_MAJORITY = "stance-positive-on-favourable-majority"
RULE_ADVERSE_MAJORITY = "stance-negative-on-adverse-majority"

#: Read on both sides, and they cancel. A real position — the
#: committee looked and found the case genuinely balanced — and not
#: the same object as an abstention, which is the absence of looking.
RULE_BALANCED = "stance-neutral-on-balanced-findings"

#: How many one-sided findings a strong stance needs.
STRONGLY = 2


@dataclass(frozen=True, slots=True)
class Input:
    """One measurable input a committee's remit asks for.

    An input whose `value` is None was not measured, and its
    `absent_because` is the wording of the layer that failed to measure
    it — carried through, never recomposed here.
    """

    name: str
    value: int | None
    absent_because: str | None = None

    @property
    def is_measured(self) -> bool:
        return self.value is not None


def build(
    *,
    committee: str,
    remit: frozenset[Dimension],
    ledger: FindingLedger,
    inputs: tuple[Input, ...] = (),
    uncertainty: tuple[Uncertainty, ...] = (),
    abstain_because: str | None = None,
) -> CommitteeOpinion:
    """This committee's opinion over the findings in its remit.

    `abstain_because`, where given, is a caller-known reason the
    committee cannot speak at all — nothing about the security was
    gathered, or the question does not apply to this asset. It
    short-circuits the table, because a stance derived from an empty
    remit would say the same thing for both and an investor cannot act
    on *neutral* when the truth is *nobody looked*.
    """

    supporting = ledger.where(sense=Sense.FAVOURABLE, dimensions=remit)
    opposing = ledger.where(sense=Sense.ADVERSE, dimensions=remit)

    unmeasured = tuple(
        Uncertainty(
            kind=UncertaintyKind.MEASUREMENT_ABSENT,
            about=item.absent_because or f"{item.name} was not measured.",
        )
        for item in inputs
        if not item.is_measured
    )

    # The caller's uncertainties first: it knows the ones that no count
    # can discover, such as a question this platform has no layer for.
    unresolved = _unique(uncertainty + unmeasured)

    confidence = Confidence(
        inputs_measured=sum(1 for item in inputs if item.is_measured),
        inputs_asked=len(inputs),
        supporting=len(supporting),
        opposing=len(opposing),
        unresolved=len(unresolved),
    )

    stance, decided_by = _stance(
        supporting=len(supporting),
        opposing=len(opposing),
        abstain_because=abstain_because,
    )

    return CommitteeOpinion(
        committee=committee,
        remit=remit,
        stance=stance,
        abstained_because=(
            _abstention(committee, abstain_because) if stance is None else None
        ),
        supporting=tuple(finding.ref for finding in supporting),
        opposing=tuple(finding.ref for finding in opposing),
        uncertainty=unresolved,
        # A committee that did not speak has no confidence in anything.
        # Reporting one here would be a number attached to a position
        # nobody took, and averaging it with real ones is exactly how an
        # unmeasurable input came to look like an objection.
        confidence=confidence if stance is not None else None,
        decided_by=decided_by,
        summary=_summary(
            committee=committee,
            stance=stance,
            confidence=confidence,
            abstained_because=_abstention(committee, abstain_because),
        ),
    )


def _stance(
    *,
    supporting: int,
    opposing: int,
    abstain_because: str | None,
) -> tuple[Stance | None, str]:
    """The position these counts add up to, and the rule that says so.

    Rules fire in a fixed order and the first that applies decides.
    The order is part of the meaning: an abstention precedes every
    weighing, and one-sidedness is checked before majority so that
    *nothing against* is never reported merely as *more for*.
    """

    if abstain_because is not None or not (supporting or opposing):
        return None, RULE_NO_FINDINGS

    if not opposing and supporting >= STRONGLY:
        return Stance.STRONGLY_POSITIVE, RULE_UNOPPOSED_FAVOURABLE

    if not supporting and opposing >= STRONGLY:
        return Stance.STRONGLY_NEGATIVE, RULE_UNOPPOSED_ADVERSE

    if supporting > opposing:
        return Stance.POSITIVE, RULE_FAVOURABLE_MAJORITY

    if opposing > supporting:
        return Stance.NEGATIVE, RULE_ADVERSE_MAJORITY

    return Stance.NEUTRAL, RULE_BALANCED


def _abstention(committee: str, because: str | None) -> str:
    """Why the committee did not speak, always as an abstention.

    Worded rather than left blank, and worded the same way every time:
    an abstention is not opposition, and a surface that printed silence
    beside four stated positions would invite the reader to supply the
    difference themselves.
    """

    return because or (
        f"The {committee} was shown no finding in its remit, so it takes "
        "no position. That is an abstention, not a neutral view."
    )


def _summary(
    *,
    committee: str,
    stance: Stance | None,
    confidence: Confidence,
    abstained_because: str,
) -> str:
    """One line, composed from the counts — never written about the company."""

    if stance is None:
        return abstained_because

    read = (
        f"{confidence.supporting} finding(s) for and "
        f"{confidence.opposing} against, in its remit"
    )

    return (
        f"The {committee} is {stance.stated} on {read}; "
        f"confidence {confidence.stated()}."
    )


def _unique(items: tuple[Uncertainty, ...]) -> tuple[Uncertainty, ...]:
    """The same absence, stated twice by two layers, is one uncertainty."""

    return tuple(dict.fromkeys(items))
