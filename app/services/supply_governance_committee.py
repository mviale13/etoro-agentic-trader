"""The Supply Governance Committee — who can change the rule you are holding.

The second real committee, and it was **selected by measurement rather
than chosen**. Nineteen investor questions are already discovered in
`crypto_questions.py`; the candidates were scored on evidence actually
held across the eight-asset corpus, and this one won because it is the
only question with primary-grade evidence, genuine corpus contrast, and
a structural answer that cannot be read as a grade.

The question:

> **What would it take to change the rule that creates this token's new
> supply?**

An investor holding a token is exposed to the schedule that creates more
of it. *Who is able to change that schedule* is a different fact from
*how fast it runs* — and only the first is answerable from evidence this
platform holds without a threshold.

**Independent of Fee Capture by construction, and demonstrably so.**
Different evidence (issuance rules read from chain state, never
DefiLlama's fee readings), a different economic question, and — the test
that matters — a different applicability split. Fee Capture declines BTC
and asks 1INCH; this committee asks BTC and declines 1INCH. Neither can
see the other's verdict; neither imports the other.

**Neither verdict is favourable.** S5.3 measured this and the finding is
load-bearing here: BTC, ADA and SOL are *equally* explicit and *equally*
projectable, and their five-year expansion runs 2.73% / 10.64% / 14.51%.
The protocol-fixed asset expands least — but a governance-set rule is
not thereby worse, it is differently constrained, and the magnitude that
separates them was parked outside quality for a reason. This committee
reports **who holds the power to change the rule** and refuses to say
whether that is good.

**Both verdicts are positive findings**, which is the shape that makes
this committee unlike Fee Capture rather than a second view of it. Fee
Capture answers *evidenced* or *evidenced absent*; this one answers
*consensus-bound* or *governance-set* — two things that are true, not
one thing and its negation.

**No model is asked anything.** Fee Capture needs a judge because
weighing a figure against a stated mechanism is a judgment. Here the
judgment is an eligibility rule over primary evidence — are the
parameters all sourced, does the path reproduce, is the mutability
established — and a model asked to apply it would be an unchecked
lookup. That the protocol accommodates a committee with no model seam is
a finding, not a shortcut.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from app.domain.committee_judgment import (
    ELIGIBLE_CLAIM_TYPES,
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    EligibleFinding,
    JudgmentState,
    abstain,
    confidence_from,
)
from app.domain.committee_protocol import CommitteeContract
from app.domain.crypto_archetype import (
    AnalyticalCapability,
    ArchetypeConfidence,
    archetype_for,
)
from app.domain.crypto_intelligence import ClaimType
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.mechanical_issuance import MechanicalIssuance, RuleMutability
from app.providers.cached_issuance_provider import CachedIssuanceRuleProvider

#: The applicability rule, named so a change to it changes the
#: committee's identity rather than passing unnoticed downstream.
APPLICABILITY_RULE = "issues-to-secure-itself@1"


class Verdict(StrEnum):
    """The two answers. Both positive findings, neither a grade.

    **Not Fee Capture's pair wearing different words.** That committee
    answers whether a mechanism is evidenced or evidenced to be absent —
    a presence and its negation. These two are both presences: every
    asset reaching a verdict here *has* a mechanical rule, and the
    answer says who is able to change it.

    Deliberately not ordered. A protocol-fixed rule is harder to change
    and that is not the same as better: a rule nobody can change is also
    a rule nobody can fix, and this platform has established no view on
    which an investor should prefer. There is no `rank`, and adding one
    would mean editing this file with the reason written down.
    """

    #: Changing the rule would require a consensus change the whole
    #: network has to adopt.
    CONSENSUS_BOUND = "consensus_bound"

    #: The rule is a protocol parameter the chain's own governance can
    #: change without a fork, so the schedule holds while the parameter
    #: does.
    GOVERNANCE_SET = "governance_set"

    @property
    def stated(self) -> str:
        return {
            Verdict.CONSENSUS_BOUND: (
                "new supply is created by a mechanical rule this platform "
                "has read and re-run, and changing that rule would require a "
                "consensus change the whole network has to adopt"
            ),
            Verdict.GOVERNANCE_SET: (
                "new supply is created by a mechanical rule this platform "
                "has read and re-run, and that rule is a protocol parameter "
                "the chain's own governance can change without a fork"
            ),
        }[self]


QUESTION = (
    "Is this token's new supply created by a mechanical rule this platform "
    "can read and re-run, and what would it take to change that rule?"
)

CONTRACT = CommitteeContract(
    key="supply_governance",
    name="Supply Governance Committee",
    question=QUESTION,
    version=1,
    applicability_rule=APPLICABILITY_RULE,
    verdicts=tuple(verdict.value for verdict in Verdict),
    eligible_claim_types=frozenset(claim.value for claim in ELIGIBLE_CLAIM_TYPES),
)


class SupplyGovernanceCommittee:
    """One question, one asset, one answer — or an honest absence."""

    CONTRACT = CONTRACT

    def __init__(self, issuance: CachedIssuanceRuleProvider | None = None) -> None:
        # The stored door by default. A committee is read by surfaces,
        # and a surface that fetched would make opening a page an
        # acquisition — the rule both knowledge services already live by.
        self._issuance = issuance or CachedIssuanceRuleProvider.stored()

    @property
    def contract(self) -> CommitteeContract:
        return CONTRACT

    # ── applicability, in this committee's own economic terms ───────

    def basis(self, symbol: str) -> ApplicabilityBasis:
        """Whether asking who governs new supply is meaningful here.

        **This committee's rule, reading the archetype layer as evidence
        rather than delegating to it** — PR #112's finding, applied
        again because the failure it prevents is the same one: a
        forwarded rule would make this a generic supply judgment wearing
        a narrow remit, and would change meaning the next time that
        taxonomy was edited for somebody else's purpose.

        The economics, in one clause: a token whose protocol **creates
        new supply to pay for its own operation or security** has an
        issuance rule as part of what the token is, and the holder is
        exposed to it. A governance or distribution token whose supply
        was created once and is released from allocations has no such
        rule to govern — its supply question is *when do existing tokens
        reach the market*, which is a different question and would need
        evidence this platform cannot currently reach.

        Read from the archetype's capabilities rather than its name, so
        an asset that is several things at once is asked the question if
        **any** of what it is issues to secure itself. That is why
        Hyperliquid is asked: it runs its own chain.
        """

        assignment = archetype_for(symbol)

        if assignment.confidence is ArchetypeConfidence.UNESTABLISHED:
            return ApplicabilityBasis(
                applicability=Applicability.UNESTABLISHED,
                because=(
                    "No economic role is established for this asset, so this "
                    "platform cannot say whether its protocol creates new "
                    "supply to secure itself at all."
                ),
            )

        role = assignment.definition.name

        issues_to_secure = {
            AnalyticalCapability.MONETARY_NETWORK,
            AnalyticalCapability.SMART_CONTRACT_NETWORK,
        } & set(assignment.capabilities)

        if not issues_to_secure:
            return ApplicabilityBasis(
                applicability=Applicability.NOT_ECONOMICALLY_APPLICABLE,
                because=(
                    f"This asset's established economic role — {role} — is "
                    "not one where the protocol creates new supply to pay "
                    "for its own security. Its supply was created once and "
                    "reaches the market by release rather than by issuance, "
                    "so asking what governs the issuance rule is the wrong "
                    "instrument and the question is left unanswered rather "
                    "than answered adversely."
                ),
                economic_role=role,
            )

        lens = sorted(capability.label for capability in issues_to_secure)

        return ApplicabilityBasis(
            applicability=Applicability.APPLICABLE,
            because=(
                f"This asset's established economic role — {role} — is read "
                f"through the {', '.join(lens).lower()} lens, where the "
                "protocol creates new supply to pay for its own security. "
                "What governs that creation is part of what the holder owns."
            ),
            economic_role=role,
        )

    # ── the evidence, established in code ───────────────────────────

    def evidence(self, symbol: str) -> tuple[EligibleFinding, ...]:
        """Everything this committee may see. Nothing else reaches it.

        Assembled from the issuance rule alone — never from a vendor's
        supply figures, and the exclusion is measured rather than
        stylistic. A vendor's `total_supply` is the protocol maximum for
        83 of 145 capped assets in the top 250 (S5), and reading it here
        would put Cardano at 100% emitted where its own ledger says
        86.2%. A committee reasoning from that would be confidently
        wrong about the very quantity it exists to describe.
        """

        rule = self._issuance.rule(symbol)

        if rule is None:
            return ()

        findings: list[EligibleFinding] = [
            EligibleFinding(
                ref="M.mechanism",
                stated=(
                    f"{rule.symbol}: new supply is created by "
                    f"{rule.mechanism.described}, read from {rule.source}."
                ),
                claim_type=ClaimType.REPORTED,
                established_by=f"Mechanical issuance — {rule.provenance.rule_version}",
            ),
            EligibleFinding(
                ref="M.formula",
                stated=f"{rule.symbol}: the rule is {rule.formula}.",
                claim_type=ClaimType.MEASURED,
                established_by="Mechanical issuance — the rule in one line",
            ),
        ]

        # Every parameter is its own finding, because the committee's
        # eligibility rule turns on whether each names the surface it was
        # read from. Rolled into one sentence they could not be counted.
        findings.extend(
            EligibleFinding(
                ref=f"P.{parameter.name}",
                stated=(
                    f"{rule.symbol}: {parameter.name} = {parameter.value:,.8g} "
                    f"{parameter.unit} — {parameter.means}, read from "
                    f"{parameter.read_from}."
                ),
                claim_type=ClaimType.MEASURED,
                established_by="Mechanical issuance — a parameter and its surface",
            )
            for parameter in rule.parameters
        )

        if rule.mutability is not RuleMutability.UNKNOWN:
            findings.append(
                EligibleFinding(
                    ref="M.mutability",
                    stated=(
                        f"{rule.symbol}: {rule.mutability.stated.lower()} — "
                        f"{rule.mutability.because}."
                    ),
                    claim_type=ClaimType.REPORTED,
                    established_by="Mechanical issuance — what could change the rule",
                )
            )

        findings.extend(
            EligibleFinding(
                ref=f"R.{index}",
                stated=(
                    f"{rule.symbol}: over {step.horizon} the rule creates "
                    f"{step.issuance:,.8g} {step.unit}, which is "
                    f"{step.share_of_emitted:.2%} of what has already been "
                    f"issued — MOVRvest's arithmetic under the currently "
                    f"observed rule, not a forecast."
                ),
                claim_type=ClaimType.MEASURED,
                established_by=f"Mechanical issuance — projection {step.rule_version}",
            )
            for index, step in enumerate(rule.path, start=1)
        )

        return tuple(findings)

    # ── the judgment ────────────────────────────────────────────────

    async def judge(self, symbol: str) -> CommitteeJudgment:
        """The answer, or the reason there is none. No model is asked.

        Three questions in order, never collapsed: is this meaningful,
        can we establish whether it is, and is the evidence good enough
        to answer. The third is the committee's own judgment and it is
        made against a stated rule rather than by weighing — which is
        what a model would be for, and there is nothing here to weigh.
        """

        asset = symbol.upper().strip()

        basis = self.basis(asset)

        if basis.applicability is Applicability.UNESTABLISHED:
            return abstain(
                asset, CONTRACT, AbstentionReason.APPLICABILITY_UNESTABLISHED, basis
            )

        if not basis.is_applicable:
            return abstain(
                asset, CONTRACT, AbstentionReason.NOT_ECONOMICALLY_APPLICABLE, basis
            )

        rule = self._issuance.rule(asset)

        findings = self.evidence(asset)

        if rule is None or not findings:
            return abstain(
                asset,
                CONTRACT,
                AbstentionReason.INSUFFICIENT_EVIDENCE,
                basis,
                because=(
                    "No mechanical issuance rule is held for this asset. That "
                    "is a statement about what this platform has read, not "
                    "about what the protocol does."
                ),
            )

        refusal = _cannot_answer(rule)

        if refusal is not None:
            return abstain(
                asset,
                CONTRACT,
                AbstentionReason.INSUFFICIENT_EVIDENCE,
                basis,
                because=refusal,
            )

        verdict = (
            Verdict.CONSENSUS_BOUND
            if rule.mutability is RuleMutability.PROTOCOL_FIXED
            else Verdict.GOVERNANCE_SET
        )

        return CommitteeJudgment(
            asset=asset,
            contract=CONTRACT,
            state=JudgmentState.JUDGED,
            basis=basis,
            verdict=verdict,
            # Counted from the evidence, and it cannot reach the verdict:
            # the verdict is a function of `mutability` alone, and no
            # count of parameters can move it.
            confidence=confidence_from(
                supporting=len(findings),
                across_captures=False,
            ),
            refs=tuple(finding.ref for finding in findings),
            because=(
                f"The rule is {rule.formula}, every parameter names the "
                f"surface it was read from, and {rule.mutability.because}."
            ),
            # When the committee concluded, never when the evidence was
            # observed. Taking the rule's reading time made two
            # convenings from one cached rule produce one record id, so
            # the record said the committee met once when it met twice —
            # and a count of judgments is the one thing #113 requires to
            # be honest.
            judged_at=datetime.now(UTC),
        )


def _cannot_answer(rule: MechanicalIssuance) -> str | None:
    """Why this rule cannot settle the committee's question, or None.

    The eligibility rule, stated rather than felt, and owned by this
    committee because what counts as good enough evidence for *who can
    change a rule* is not a framework question.

    **It deliberately does not read `EvidenceStanding`**, and that is the
    sharpest thing measured while building this committee. Every issuance
    rule on this platform stands at `CLAIMED`, because S1's corroboration
    vocabulary was built for vendor claims where a second independent
    source is real evidence. A chain's own issuance parameters have no
    second source and cannot acquire one — the chain *is* the authority —
    so requiring `ESTABLISHED` here would not raise the standard, it
    would make this committee permanently silent about the strongest
    evidence the platform holds. S4.5 already ruled on exactly this:
    **where a fact came from is a second axis, never a second standing.**

    So the clauses below are S5.1's Model C gates asked of a rule instead
    of a figure: is the authority primary, is the surface the asset's
    own, is every constant read rather than remembered, is the reading
    versioned, does the path re-run, and is the thing being asked about
    actually established. **A clause that cannot be evaluated fails**,
    which is Model C's standing rule and the reason "we did not check" is
    not a pass.

    One distinction this rests on, from S5.2: Bitcoin's issuance *rule*
    reproduces 89 of 89 daily intervals within the consensus bound while
    its historical *total* stays unresolved. The rule is right and the
    composition is unitemised — and this committee asks about the rule.
    """

    if rule.authority not in _PRIMARY:
        return (
            "This rule was not read from a primary surface, so it is "
            "somebody's description of the protocol's schedule rather than "
            "the schedule itself."
        )

    if not rule.provenance.surface_is_canonical:
        return (
            "The surface this rule was read from serves a figure only its "
            "operator computed, so it cannot establish what the protocol is "
            "running."
        )

    if not rule.parameters:
        return (
            "The mechanism is named and no parameter is read, so there is "
            "nothing to re-run and no rule to describe the governance of."
        )

    if not rule.parameters_are_all_read:
        return (
            "At least one parameter of this rule names no surface it was "
            "read from. A rule assembled partly from memory cannot be "
            "trusted to be the rule the protocol is running."
        )

    if not rule.provenance.rule_version:
        return (
            "This reading names no rule version, so a later reading could "
            "not tell a corrected rule from a changed protocol."
        )

    if not rule.is_projectable:
        return (
            "The rule is read and its path does not re-run here, so this "
            "platform cannot show that the rule it read is the rule the "
            "protocol is running."
        )

    if rule.mutability is RuleMutability.UNKNOWN:
        return (
            "The rule is read and what it would take to change it is not "
            "established — which is the committee's whole question, so it "
            "is left unanswered rather than guessed."
        )

    return None


#: Authorities that are the protocol speaking about itself. A rule read
#: anywhere else is a description of the schedule, not the schedule.
_PRIMARY = frozenset(
    {
        EvidenceAuthority.PRIMARY_OBSERVATION,
        EvidenceAuthority.PRIMARY_DERIVED,
    }
)
