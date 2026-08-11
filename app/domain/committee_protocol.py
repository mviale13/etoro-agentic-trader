"""The contract every crypto committee satisfies, discovered from one.

Extracted from the Value Capture Committee and Judgment History rather
than designed ahead of them, and the extraction was a **relocation, not
an invention**: measuring the two implementations showed that the
framework's *logic* was already generic and only its *vocabulary* was
not. Every decision Judgment History makes runs on four things — did the
committee speak, is this the same answer as last time, does the question
apply, and were the two produced under the same contract — and none of
them needs to know what an answer means.

One line proved otherwise, and it is the whole reason this module
exists:

```python
JudgmentPosture.EVIDENCE_OF_PRESENCE
if verdict is Verdict.MECHANISM_EVIDENCED
else JudgmentPosture.EVIDENCE_OF_ABSENCE
```

The framework was reading a Fee Capture verdict and deciding what it
*meant*. It never used the result for anything but wording, so nothing
downstream depended on it — but the next committee's verdicts would have
had to be squeezed into presence and absence, two words chosen for fees.

So the rule this module enforces:

> **The framework may know that Committee X answered question Y with
> verdict Z under contract C. It may never know what Z means.**

A verdict is an opaque token with a sentence attached. The framework
carries it, compares it with another token for identity, quotes its
sentence, and stops. Whether Z is favourable, adverse, stronger, weaker
or worth anything at all belongs to a layer that has not been earned.

**What stayed with the committee**: the question, the applicability
rule, the verdict vocabulary, the economic meaning of its evidence.
**What became generic**: identity and versioning, applicability *states*
(not rules), the answered/abstained/unavailable trichotomy, evidence
eligibility, support counting, and the lifecycle.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.domain.committee_judgment import (
        ApplicabilityBasis,
        CommitteeJudgment,
        EligibleFinding,
    )


@runtime_checkable
class StructuralVerdict(Protocol):
    """What a committee may answer with. Opaque to everything above it.

    Two members, and the omissions are the point: there is no `rank`, no
    `is_favourable`, no `polarity` and no score. A committee's verdicts
    are a *set of names for structural findings*, and the framework is
    given exactly enough to store one, recognise it again, and print the
    committee's own sentence for it.

    A `StrEnum` on a committee satisfies this structurally, which is why
    no committee has to inherit anything.
    """

    @property
    def value(self) -> str:
        """The stored token. Stable, because history compares it."""

    @property
    def stated(self) -> str:
        """The committee's own sentence for this answer."""


class Comparability(StrEnum):
    """Whether two judgments answer the same question in the same terms.

    The two failures are told apart deliberately: a bumped version is
    somebody declaring a change, and a changed fingerprint under an
    unchanged version is a change nobody declared. The second is a defect
    in this platform and saying so is more useful than treating them as
    one.
    """

    COMPARABLE = "comparable"

    #: A different question entirely.
    DIFFERENT_COMMITTEE = "different_committee"

    #: The committee was versioned, so its verdicts may not mean the
    #: same thing. Declared, and therefore honest.
    DIFFERENT_VERSION = "different_version"

    #: Same declared version, different contract. Nobody bumped the
    #: number, and the fingerprint noticed.
    CONTRACT_CHANGED = "contract_changed"

    @property
    def is_comparable(self) -> bool:
        return self is Comparability.COMPARABLE

    @property
    def stated(self) -> str:
        return {
            Comparability.COMPARABLE: (
                "both judgments were produced under the same committee contract"
            ),
            Comparability.DIFFERENT_COMMITTEE: (
                "the two judgments answer different questions, so neither "
                "says anything about the other"
            ),
            Comparability.DIFFERENT_VERSION: (
                "the committee was versioned between them, so a verdict "
                "produced under the earlier version may not mean what the "
                "same word means now"
            ),
            Comparability.CONTRACT_CHANGED: (
                "the committee's contract changed without its version "
                "changing, so the two are not compared and this platform "
                "cannot say what the earlier verdict meant"
            ),
        }[self]


def fingerprint_of(
    question: str,
    applicability_rule: str,
    eligible: frozenset[str],
    verdicts: tuple[str, ...],
) -> str:
    """A digest over everything that gives a verdict its meaning.

    Four inputs, and each one is a way a verdict can silently change
    meaning while keeping its name: the question it answers, the rule
    deciding whether that question applies, the evidence admitted to it,
    and the vocabulary of the answer itself.

    Derived rather than declared, so it cannot drift from the code. A
    record persists the fingerprint it was produced under; comparing it
    with today's live one is what makes longitudinal comparability
    structural instead of remembered.
    """

    payload = "|".join(
        (
            question.strip(),
            applicability_rule.strip(),
            ",".join(sorted(eligible)),
            ",".join(sorted(verdicts)),
        )
    )

    return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class CommitteeIdentity:
    """What a judgment record persists about who produced it.

    Deliberately smaller than the contract it comes from. A record must
    stay readable when the committee that wrote it has been reworded,
    reversioned or deleted, so it carries the four things that can be
    read without any live code: the key it was filed under, what it was
    called at the time, its declared version and its fingerprint.

    The question, the verdict vocabulary and the applicability rule are
    **not** here on purpose — they are today's code, and a record that
    embedded them would be asserting that yesterday's committee asked
    what today's file says.
    """

    key: str
    name: str
    version: int
    fingerprint: str

    @property
    def stated(self) -> str:
        return f"{self.name} v{self.version}"

    def comparability(self, other: CommitteeIdentity) -> Comparability:
        """Whether a judgment under this contract may be compared with
        one under the other's."""

        if self.key != other.key:
            return Comparability.DIFFERENT_COMMITTEE

        if self.version != other.version:
            return Comparability.DIFFERENT_VERSION

        if self.fingerprint != other.fingerprint:
            return Comparability.CONTRACT_CHANGED

        return Comparability.COMPARABLE


@dataclass(frozen=True, slots=True)
class CommitteeContract:
    """The declaration a committee makes about itself. Its own semantics.

    Everything here is the committee's to choose, and the framework
    reads exactly one field for meaning — `verdicts`, and only to
    fingerprint it. The question is quoted, never parsed; the
    applicability rule is an opaque identifier that exists so that
    changing the rule changes the fingerprint.

    **`verdicts` is a vocabulary, not a scale.** They are stored sorted
    into the fingerprint precisely so that no order can leak out of this
    object and be mistaken for a ranking.
    """

    #: Stable storage key. Never renamed once records exist under it —
    #: a rename is a new committee, because history filed under the old
    #: key would otherwise silently vanish.
    key: str

    #: What this committee is called today.
    name: str

    #: The one question it answers, in its own words.
    question: str

    version: int

    #: An opaque identifier for the rule deciding whether the question
    #: applies. Named rather than inspected: the framework cannot check
    #: an economic rule, but it can notice that the rule changed.
    applicability_rule: str

    #: Every answer this committee can give. Opaque tokens.
    verdicts: tuple[str, ...]

    #: The claim types this committee admits, as the fingerprint sees
    #: them. Recorded per committee so that a future committee admitting
    #: a different set is visibly a different contract — the framework's
    #: own eligibility floor still applies underneath.
    eligible_claim_types: frozenset[str]

    @property
    def fingerprint(self) -> str:
        return fingerprint_of(
            question=self.question,
            applicability_rule=self.applicability_rule,
            eligible=self.eligible_claim_types,
            verdicts=self.verdicts,
        )

    @property
    def identity(self) -> CommitteeIdentity:
        """What a record of this committee's judgment will carry."""

        return CommitteeIdentity(
            key=self.key,
            name=self.name,
            version=self.version,
            fingerprint=self.fingerprint,
        )

    @property
    def stated(self) -> str:
        return f"{self.name} v{self.version}"

    def admits(self, verdict: StructuralVerdict) -> bool:
        """Whether this answer is one this committee may give.

        Checked at the point a judgment is built, so a committee cannot
        record an answer outside the vocabulary its own fingerprint was
        computed from — which would make the fingerprint a description
        of something the record does not contain.
        """

        return verdict.value in self.verdicts


@runtime_checkable
class Committee(Protocol):
    """The lifecycle MOVRvest can run without knowing what a committee is.

    Four members, each earned by something a caller already does:
    `judge` because `movrvest judge` runs it, `evidence` because the
    record digests what the committee was given, `basis` because
    applicability must be recorded directly rather than reconstructed,
    and `contract` because history must file the judgment under an
    identity that cannot disagree with it.

    Notably **not** here: anything that would let a caller ask whether a
    verdict is good, compare two committees, or weigh one against
    another. A protocol is also a statement about what may not be asked.
    """

    @property
    def contract(self) -> CommitteeContract:
        """Who this committee is, and under what terms it answers."""

    def basis(self, symbol: str) -> ApplicabilityBasis:
        """Whether the question applies here, why, and from what role."""

    def evidence(self, symbol: str) -> tuple[EligibleFinding, ...]:
        """Everything this committee is allowed to see. Nothing else reaches it."""

    async def judge(self, symbol: str) -> CommitteeJudgment:
        """The answer, or the reason there is none."""
