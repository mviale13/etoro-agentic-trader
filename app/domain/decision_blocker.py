"""What stands between a case and its next state, named by the gate itself.

The measured defect: the homepage listed *"Top opportunities the CIO
evaluated"* — MSFT waiting, GRE.MC in research, AMD and UUUU rejected —
in one ranked table, with a *"What is missing"* column reading an em
dash for AMD. AMD is not missing anything. It is stopped, by this
platform's own risk policy, at 71.8% annualised volatility.

Two rules this object exists to keep:

**The blocker is the branch that fired, never a re-reading of the
outcome.** `ArtificialCIO._determine_state` already knows which gate
stopped a case — it returns that gate's own sentence as the rationale —
and this is that knowledge given a type instead of being inferred back
out of a state string by a surface. Nothing downstream classifies.

**A gate is not a verdict on the business.** A risk ruling says the
security's own price record is violent; it says nothing about whether
the company is any good, and AMD's own analysts read growth as strong
on the same evidence. So a blocker that is not about the business
carries the analyst verdicts that survive it, and says in words what it
does *not* claim. That is Invariant 10 applied to a gate: the
measurement is established, its meaning beyond the gate is not, and the
layer receiving it must not invent the missing half.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BlockerKind(StrEnum):
    """What kind of thing is standing in the way.

    One member per branch of the two decision cascades, and no member
    without a branch. `IDENTITY_REFUSAL` is deliberately **absent**:
    neither cascade stops on identity today — a refused vendor listing
    removes measurements upstream, and the crypto path that produces
    those refusals never reaches a measurement gate — so declaring it
    would be #119's defect exactly, where 13 of 13 refusal entries were
    unreachable and the table read as though it worked.
    """

    #: Nothing stands in the way: every gate this platform applies was
    #: cleared. Rendered in words, never as an em dash.
    NONE = "none"

    #: Not enough has been read yet. What is short is nameable, and a
    #: later cycle could supply it.
    MISSING_EVIDENCE = "missing_evidence"

    #: The security's own price record is too violent for policy, or its
    #: risk could not be measured at all and no case progresses without
    #: one.
    RISK_GATE = "risk_gate"

    #: What the security costs, against what this platform's bands call
    #: attractive — or the absence of any reading of it.
    VALUATION_GATE = "valuation_gate"

    #: The business itself, as measured. The one kind that *is* a
    #: statement about the company.
    QUALITY_GATE = "quality_gate"

    #: How this security would sit in this account, under the investor's
    #: own policy.
    PORTFOLIO_FIT_GATE = "portfolio_fit_gate"

    #: A hard policy gate refused the case outright.
    POLICY_GATE = "policy_gate"

    #: This platform cannot take the case further, whatever the evidence
    #: says. A limit of MOVRvest, never a finding about the asset —
    #: every digital asset is here, and the crypto path's own ceiling
    #: sentence is what it carries.
    PLATFORM_LIMIT = "platform_limit"

    @property
    def blocks(self) -> bool:
        return self is not BlockerKind.NONE


#: What a gate that is not about the business does not claim about it.
#:
#: Worded here, once, and only attached where the gate that fired was
#: something other than quality: a risk ruling, a valuation band and a
#: portfolio-fit measure are all silent about whether the company is any
#: good.
def _does_not_say(kind: BlockerKind, symbol: str) -> str:
    if kind in (
        BlockerKind.RISK_GATE,
        BlockerKind.VALUATION_GATE,
        BlockerKind.PORTFOLIO_FIT_GATE,
    ):
        return (
            f"This is a {_NAMES[kind]} ruling. It does not say "
            f"{symbol} is a weak business."
        )

    return ""


_NAMES = {
    BlockerKind.RISK_GATE: "risk",
    BlockerKind.VALUATION_GATE: "valuation",
    BlockerKind.PORTFOLIO_FIT_GATE: "portfolio-fit",
}


@dataclass(frozen=True, slots=True)
class DecisionBlocker:
    """One blocker, with the reading beneath it and what it does not say."""

    kind: BlockerKind

    #: What blocks progress, in the investor's language, carrying the
    #: figures the gate compared. Worded by the cascade that stopped,
    #: never composed by a surface.
    stated: str

    #: The fundamental analysts' favourable verdicts, quoted verbatim
    #: and in the order the ledger reported them. Selected by *kind* —
    #: an analyst's own verdict — and never by strength, because this
    #: platform does not measure how strong a finding is and an ordering
    #: nobody measured must not be published as one.
    despite: tuple[str, ...] = ()

    #: What this ruling does not claim. Empty where the gate is itself a
    #: statement about the business, because there the sentence would be
    #: false.
    does_not_say: str = ""

    @classmethod
    def none(cls) -> DecisionBlocker:
        return cls(
            kind=BlockerKind.NONE,
            stated=(
                "Nothing blocks progress: every gate this platform applies was cleared."
            ),
        )

    @classmethod
    def of(
        cls,
        kind: BlockerKind,
        stated: str,
        symbol: str,
        despite: tuple[str, ...] = (),
    ) -> DecisionBlocker:
        """A blocker with its disclosure attached, decided by the kind."""

        return cls(
            kind=kind,
            stated=stated,
            despite=despite if kind is not BlockerKind.QUALITY_GATE else (),
            does_not_say=_does_not_say(kind, symbol),
        )

    @property
    def blocks(self) -> bool:
        return self.kind.blocks
