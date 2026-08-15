"""What a committee established, in a form an investment layer may consume.

The bridge between *the committees know things* and *the investment
system can use what they know* — and it is deliberately not a score.

**The investigation that shaped it.** Before this module existed, the
crypto committee layer was reached by nothing that decides anything: all
nine named decision modules — the Artificial CIO, its policy, its
evidence builder, the executive pipeline, the thesis builder, the
ranking — reach it in no number of hops. Its only consumers outside the
CLI and the read-only surfaces are the two intelligence-synthesis
modules, which communicate and never decide.

**And the decision layer could not have consumed a verdict if it tried.**
`DecisionEvidence` is the Artificial CIO's only input, and every branch
of its state machine tests a 0-100 score or a boolean flag. There is no
structural input of any kind. So a bridge that wanted to move a decision
today would have to emit a number, and that number does not exist:

- an `EligibleFinding` carries `ref`, `stated`, `claim_type` and
  `established_by`, and **no sense** — where the equity `Finding` carries
  one, recorded by the signal that read it, which is what `Stance`
  counts;
- Supply Governance's own verdict vocabulary says it: *"deliberately not
  ordered … a rule nobody can change is also a rule nobody can fix, and
  this platform has established no view on which an investor should
  prefer"*;
- Fee Capture's `MECHANISM_EVIDENCED` is documented as a structural fact
  and explicitly not a favourable one.

The domain has therefore already refused, with the reason written down,
the exact transformation a numeric bridge would need. **So this module
carries structural conclusions and says, per conclusion, that their
investment meaning is not established.** That sentence is the product:
this platform can now say *the Value Capture Committee established X*
to a layer that consumes it, without X quietly becoming *and therefore
buy*.

**It knows nothing about any committee.** There is no import of a
committee implementation, no committee key in this file, no branch on a
verdict token's spelling and no vocabulary from fees or supply. A third
committee reaches an investment layer through here without this file
changing, which is the architectural test.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.domain.committee_judgment import Applicability, Confidence
from app.domain.committee_protocol import CommitteeIdentity, Comparability
from app.domain.judgment_history import EvidenceSemantics, JudgmentPosture

#: The version of the licensing table below.
#:
#: Carried on every consideration, for the reason PR #127 established for
#: evidence semantics: **if the meaning of a rule changes later,
#: everything produced under the old meaning must not silently acquire
#: the new one.** A consideration is a projection rather than a record,
#: so nothing is stored and nothing needs migrating — but a projection
#: taken today and quoted tomorrow still has to say which rules produced
#: it.
BRIDGE_POLICY_VERSION = 1


class InvestmentEffect(StrEnum):
    """Whether this platform knows what a conclusion means for an investor.

    **One member, and the emptiness is the finding rather than a
    placeholder.** A second member — favourable, adverse, anything with a
    direction — is not withheld for tidiness: no layer of this platform
    has established that any crypto structural verdict should improve or
    reduce an investment case, and the two committees that produce those
    verdicts both say in their own vocabularies that their answers are
    not grades.

    Adding a member means adding a rule to `LICENSED_EFFECTS`, and adding
    a rule means writing down who established it. That is the whole
    fence: the vocabulary cannot grow by accident, and it cannot grow
    without a licensor.
    """

    #: No rule licenses an investment meaning for this conclusion. **Not
    #: neutral, and not an absence of evidence**: the committee may have
    #: answered with full confidence, and what is missing is this
    #: platform's view of what its answer is worth.
    UNRESOLVED = "unresolved"

    @property
    def stated(self) -> str:
        return {
            InvestmentEffect.UNRESOLVED: (
                "what this conclusion means for an investment case is not "
                "established by this platform"
            ),
        }[self]


#: Which committee conclusions have an established investment meaning.
#:
#: Keyed on `(committee key, verdict token)` and **empty**. A lookup
#: rather than a branch, so a committee this file has never heard of is
#: handled by the same line as one it has: adding a third committee
#: requires no edit here, and neither does adding a rule for an existing
#: one.
#:
#: It is empty because the corpus says so. Sixteen live judgments, eight
#: of them answered, and not one has a licensed investment effect —
#: because no layer has ever written the rule that would give it one.
LICENSED_EFFECTS: dict[tuple[str, str], InvestmentEffect] = {}


@dataclass(frozen=True, slots=True)
class InvestmentConsideration:
    """One committee's conclusion, addressed to an investment layer.

    Everything here is copied from a recorded judgment or read from the
    licensing table. **Nothing is derived, combined, weighted or
    ordered**, and there is no field in which a second committee's
    conclusion could be mixed into this one.
    """

    asset: str

    #: Who established it, under which contract. **Never flattened to a
    #: name**: the fingerprint is what lets a later reader ask whether
    #: two considerations were produced under the same terms.
    committee: CommitteeIdentity

    #: The question this committee owns, in its own words. `None` where
    #: the committee that reached the judgment is no longer registered.
    question: str | None

    #: Where the judgment stood. **Five states, never collapsed** — the
    #: distinction between *the question does not apply here*, *we cannot
    #: tell whether it applies*, *it applies and we lack the evidence*
    #: and *the machinery did not run* is the thing this platform paid
    #: for across #112 and #113, and a bridge that flattened them would
    #: spend it.
    posture: JudgmentPosture

    applicability: Applicability

    #: The committee's own answer token and its own sentence, quoted.
    #: `None` on every posture but `ANSWERED` — a consideration never
    #: invents a conclusion for a committee that reached none.
    conclusion: str | None
    conclusion_stated: str | None

    #: The committee's own account, in its own words.
    because: str | None

    #: As the committee expresses it. **Carried, never compared** — two
    #: committees' confidences are calibrated to different evidence
    #: shapes, which #116 measured.
    confidence: Confidence | None

    #: What the conclusion means for an investment case, where anything
    #: has established that.
    effect: InvestmentEffect

    #: Which rule set decided the line above.
    policy_version: int

    # ── provenance: §6, and it is not optional ──────────────────────

    #: The exact judgment this rests on. A consideration that cannot be
    #: traced back to one is not a consideration.
    judgment_id: str

    #: Whether that judgment was reached under the committee's current
    #: contract. `None` where the committee is no longer registered.
    comparability: Comparability | None

    #: The findings the conclusion cited, and how much eligible evidence
    #: stood behind it — **with the meaning that count was recorded
    #: under**, because PR #127 established that two records can mean
    #: different things by it.
    refs: tuple[str, ...] = ()
    evidence_count: int = 0
    evidence_semantics: EvidenceSemantics = EvidenceSemantics.HELD_AT_RECORDING

    @property
    def is_conclusive(self) -> bool:
        """Whether a committee answered. Not whether the answer is good."""

        return self.posture.is_answered

    @property
    def has_established_effect(self) -> bool:
        return self.effect is not InvestmentEffect.UNRESOLVED

    @property
    def stated(self) -> str:
        """This consideration in one line, from enumerations and quotes.

        Two halves that must not merge: what the committee established,
        and what this platform can do with it. The second half is always
        present, so a reader never receives a structural conclusion with
        the question of its investment meaning left silently open.
        """

        if self.is_conclusive and self.conclusion_stated:
            established = (
                f"{self.committee.name} established that {self.conclusion_stated}"
            )
        else:
            established = (
                f"{self.committee.name} reached no conclusion: {self.posture.stated}"
            )

        return f"{established}. On its investment meaning, {self.effect.stated}."

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "committee": {
                "key": self.committee.key,
                "name": self.committee.name,
                "version": self.committee.version,
                "fingerprint": self.committee.fingerprint,
            },
            "question": self.question,
            "posture": self.posture.value,
            "posture_stated": self.posture.stated,
            "applicability": self.applicability.value,
            "conclusive": self.is_conclusive,
            "conclusion": self.conclusion,
            "conclusion_stated": self.conclusion_stated,
            "because": self.because,
            "confidence": self.confidence.value if self.confidence else None,
            "confidence_stated": self.confidence.stated if self.confidence else None,
            "effect": self.effect.value,
            "effect_stated": self.effect.stated,
            "policy_version": self.policy_version,
            "judgment_id": self.judgment_id,
            "comparability": (self.comparability.value if self.comparability else None),
            "refs": list(self.refs),
            "evidence_count": self.evidence_count,
            "evidence_semantics": self.evidence_semantics.value,
            "stated": self.stated,
        }


@dataclass(frozen=True, slots=True)
class AssetConsiderations:
    """Every committee's conclusion about one asset, addressed onward.

    A list, and deliberately only a list. **There is no overall effect,
    no agreement, no score, no rank and no ordering that means
    anything** — #116's refusal, inherited rather than restated, because
    two committees answering different structural questions are not two
    votes on one proposition and this layer is one hop closer to a
    decision than that one was.

    `silent` names the registered committees that have concluded nothing
    at all. **A committee that never ran and a committee that ran and
    could not answer are different facts**, and the second produces a
    consideration while the first does not — so an investment layer can
    tell *nobody asked* from *we asked and got no usable answer*.
    """

    asset: str

    considerations: tuple[InvestmentConsideration, ...] = ()

    #: Registered committees with no recorded judgment for this asset.
    silent: tuple[str, ...] = ()

    @property
    def conclusive(self) -> tuple[InvestmentConsideration, ...]:
        return tuple(item for item in self.considerations if item.is_conclusive)

    @property
    def with_established_effect(self) -> tuple[InvestmentConsideration, ...]:
        """Those an investment layer may currently act on. Today: none."""

        return tuple(
            item for item in self.considerations if item.has_established_effect
        )

    def by_committee(self, key: str) -> InvestmentConsideration | None:
        for item in self.considerations:
            if item.committee.key == key:
                return item

        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "policy_version": BRIDGE_POLICY_VERSION,
            "considerations": [item.as_dict() for item in self.considerations],
            "silent": list(self.silent),
        }


def effect_for(committee_key: str, conclusion: str | None) -> InvestmentEffect:
    """What a conclusion means for an investment case, or that nothing does.

    A dictionary lookup and nothing else. It cannot branch on a committee
    name because it does not read one, and it cannot interpret a verdict
    because it never opens the token — a spelling it has no rule for
    resolves exactly as a spelling it has never seen.

    A conclusion of `None` is not a lookup failure. A committee that
    reached no answer has nothing to license, and asking the table would
    be asking what an absent verdict is worth.
    """

    if conclusion is None:
        return InvestmentEffect.UNRESOLVED

    return LICENSED_EFFECTS.get(
        (committee_key, conclusion), InvestmentEffect.UNRESOLVED
    )
