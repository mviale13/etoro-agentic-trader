"""The Value Capture Committee — evidence in code, judgment by the judge.

Three responsibilities, kept apart on purpose.

**Code assembles the evidence, and code does every calculation.** §8:
the committee interprets established facts and does not become another
calculator. So the share of fees reaching holders, the presence of a
named mechanism, the sibling-definition state and any temporal
corroboration are all settled here, in Python, before the judge sees a
word. What arrives is a list of sentences with refs.

**Code also establishes confidence.** §7 asks that confidence cannot
secretly decide the verdict; the strongest available guarantee is that
different things produce them. `confidence_from` counts independent
supporting observations and never sees the verdict; the judge chooses
the verdict and never sees the count.

**The judge chooses the verdict, and the validator refuses anything
ungrounded.** The Executive Writer's philosophy, third application: the
draft is untrusted until checked, validation fails closed, and a
rejected judgment leaves an honest absence rather than a plausible
sentence.

**Nothing about the portfolio is in scope.** §9: no position size, no
cash, no concentration, no other holding, no preference, no existing
recommendation, no `ExecutiveDecision`, no previous verdict. The
question under test is whether grounded evidence can safely become
bounded judgment *before* portfolio state is allowed to touch it, and
an import test asserts none of it is reachable.
"""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from typing import Any

from app.config import get_settings
from app.domain.asset_class import AssetClass
from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    CommitteeJudgment,
    EligibleFinding,
    JudgmentState,
    Remit,
    Verdict,
    abstain,
    confidence_from,
    is_eligible,
    unavailable,
)
from app.domain.crypto_archetype import (
    ArchetypeConfidence,
    TokenArchetype,
    archetype_for,
)
from app.domain.crypto_intelligence import ClaimType, CryptoIntelligenceSnapshot
from app.domain.protocol_fundamentals import ProtocolMetric
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)
from app.services.intelligence_journal_service import IntelligenceJournalService
from app.services.narrative_providers import build_provider
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService

#: The flag that lets a committee judge at all. Off by default, as every
#: model seam on this platform is.
FLAG = "MOVRVEST_COMMITTEE_JUDGMENT"

PROVIDER_ENV = "MOVRVEST_WRITER_PROVIDER"
MODEL_ENV = "MOVRVEST_WRITER_MODEL"

DEFAULT_PROVIDER = "openai"
DEFAULT_MODELS = {"anthropic": "claude-opus-5", "openai": "gpt-5-nano"}

JUDGMENT_TIMEOUT = 90.0
MAX_DRAFT_TOKENS = 6000

#: How long the judge's one sentence may be. A judgment is an answer,
#: not an essay.
MAX_BECAUSE_WORDS = 45

#: Language that would take the judgment outside its remit. Refused
#: rather than requested — the third time this platform applies that
#: lesson, and the reason is unchanged: asked politely not to, a model
#: eventually does.
OUT_OF_REMIT = (
    "buy",
    "sell",
    "hold",
    "recommend",
    "overweight",
    "underweight",
    "allocate",
    "position",
    "portfolio",
    "investment case",
    "conviction",
    "undervalued",
    "overvalued",
    "bullish",
    "bearish",
    "target price",
    "good investment",
    "attractive",
    "unattractive",
    "opportunity",
)

SYSTEM_PROMPT = """\
You are one committee of MOVRvest, an investment platform. You have been
assigned exactly one question and you answer only that question.

Your question: does this network generate evidenced fee activity, and
does an evidenced mechanism capture some of it for the token or its
holders?

You are given established facts. Every calculation has already been
performed; you do not compute anything.

Rules:
- Answer only the assigned question. You have no view on whether the
  asset is a good investment, what anyone should do about it, or how it
  compares with anything else, and you must not imply one.
- Choose "mechanism_evidenced" or "no_mechanism_evidenced". If neither
  is supportable from the supplied facts, choose "abstain".
- Neither answer is favourable or adverse. You are reporting whether a
  mechanism is evidenced, not whether that is good. Do not say a
  mechanism is strong, weak, healthy, meaningful or insufficient.
- Do not judge whether an amount or a share is large enough to matter.
  This platform has not established any threshold, and you must not
  invent one.
- A figure with no stated mechanism is weaker evidence than a figure
  with one. Weigh that; it is the judgment you are here to make.
- Cite the ids of the facts your answer rests on.
- Give one sentence of reasoning, at most 45 words, using only the
  supplied facts. Do not introduce a number, a name or a mechanism that
  is not in them.
- Never write buy, sell, hold, recommend, portfolio, conviction,
  bullish, bearish, undervalued, overvalued, or any word suggesting an
  action or an overall view of the asset.
- Do not describe your own confidence. That is established elsewhere
  from the evidence, not by you.
"""


class JudgmentRejected(Exception):
    """A draft failed validation, with the reason worded."""


class ValueCaptureCommittee:
    """One question, one asset, one answer — or an honest absence."""

    REMIT = Remit.VALUE_CAPTURE

    def __init__(
        self,
        protocol: ProtocolFundamentalsService | None = None,
        journal: IntelligenceJournalService | None = None,
        provider: NarrativeProvider | None = None,
    ) -> None:
        self._protocol = protocol or ProtocolFundamentalsService()
        self._journal = journal or IntelligenceJournalService()
        self._provider = provider

    @staticmethod
    def enabled() -> bool:
        flag = os.environ.get(FLAG) or get_settings().movrvest_committee_judgment

        return flag.strip().lower() in {"on", "1", "true"}

    # ── the evidence, established in code ───────────────────────────

    def evidence(
        self,
        symbol: str,
        snapshot: CryptoIntelligenceSnapshot | None = None,
    ) -> tuple[EligibleFinding, ...]:
        """Everything the committee is allowed to see. Nothing else reaches it.

        Assembled from the protocol family and the journal — never from
        the synthesis, and never from an `ATTRIBUTED` or `INFERRED`
        claim. `EligibleFinding` refuses those at construction, so the
        rule holds even if this method is wrong.
        """

        asset = symbol.upper().strip()

        facts = self._protocol.established(asset, AssetClass.CRYPTO)

        if facts is None or not facts.entities:
            return ()

        findings: list[EligibleFinding] = []

        for entity in facts.entities:
            fee = facts.fact(ProtocolMetric.FEES, entity.key)
            holder = facts.fact(ProtocolMetric.HOLDER_REVENUE, entity.key)

            if fee is not None and fee.value is not None:
                findings.append(
                    EligibleFinding(
                        ref=f"F.{entity.key}",
                        stated=(
                            f"{entity.name}: users paid {_money(fee.value)} in "
                            "fees over a day."
                        ),
                        claim_type=ClaimType.REPORTED,
                        established_by=f"Protocol fundamentals — {fee.source}",
                    )
                )

            if holder is not None and holder.value is not None:
                mechanism = (
                    f" The mechanism is stated: {holder.provider_methodology}"
                    if holder.provider_methodology
                    else " No mechanism is stated."
                )

                findings.append(
                    EligibleFinding(
                        ref=f"H.{entity.key}",
                        stated=(
                            f"{entity.name}: {_money(holder.value)} reached "
                            f"token holders over the same day.{mechanism}"
                        ),
                        claim_type=ClaimType.REPORTED,
                        established_by=f"Protocol fundamentals — {holder.source}",
                    )
                )

                # §8: the share is arithmetic, so code performs it and
                # the judge reads it. A model asked to divide would be a
                # calculator, and an unchecked one.
                if fee is not None and fee.value:
                    findings.append(
                        EligibleFinding(
                            ref=f"S.{entity.key}",
                            stated=(
                                f"{entity.name}: that is "
                                f"{holder.value / fee.value:.0%} of the fees "
                                "paid over the same day."
                            ),
                            claim_type=ClaimType.MEASURED,
                            established_by=(
                                "MOVRvest arithmetic over two checked figures"
                            ),
                        )
                    )

            elif holder is not None and fee is not None:
                # Defined and empty, which is not the same as undefined.
                # S2's sibling rule: a source that publishes this metric
                # for comparable entities and none here is saying there
                # is no mechanism, not failing to say a number. The
                # distinction is carried by the fact object — `None`
                # means the metric was never defined for this entity,
                # and a fact with no value means it was.
                findings.append(
                    EligibleFinding(
                        ref=f"N.{entity.key}",
                        stated=(
                            f"{entity.name}: the source defines a "
                            "holder-revenue figure for comparable entities "
                            "and publishes none here, which is evidence that "
                            "no such mechanism exists rather than a missing "
                            "number."
                        ),
                        claim_type=ClaimType.REPORTED,
                        established_by="Protocol fundamentals — sibling rule",
                    )
                )

        findings.extend(self._temporal(asset))

        return tuple(findings)

    def _temporal(self, asset: str) -> list[EligibleFinding]:
        """Deterministic projections over the record, traceable to it.

        Eligible because code established them, and only where the
        journal entries behind them are carried — §3 requires the
        provenance to survive the projection.
        """

        findings: list[EligibleFinding] = []

        for fact in self._journal.history(asset):
            if not fact.key.startswith("network."):
                continue

            if not fact.entry_ids:
                continue

            findings.append(
                EligibleFinding(
                    ref=f"T.{fact.key}",
                    stated=fact.stated,
                    claim_type=ClaimType.MEASURED,
                    established_by="Intelligence journal — deterministic projection",
                    observations=fact.entry_ids,
                )
            )

        return findings

    # ── the judgment ────────────────────────────────────────────────

    def applicability(self, symbol: str) -> tuple[Applicability, str]:
        """Whether this question is economically meaningful here, and why.

        **The committee's own rule, in economic terms**, reading the
        archetype layer as evidence rather than delegating to it. The
        distinction is this method's whole reason to exist:
        `TokenArchetype` was built to decide which questions an Asset
        Quality layer asks, and a committee that simply forwarded to it
        would be a generic crypto-quality judgment wearing a narrow
        remit — and would change meaning silently the next time that
        taxonomy was edited for another purpose.

        Two clauses and one refusal:

        - a token whose established economic role is **monetary** does
          not rest on capturing network fees. Its fees are the budget
          that secures it, which is S5.3's finding restated — the same
          figure is a security budget or a transfer depending on where
          it goes. Asking whether Bitcoin captures its fees for holders
          is the wrong instrument, and answering it adversely would be a
          category error dressed as a finding.
        - every other **established** role in this corpus is one where
          capture is part of what the token is.
        - and where the role is not established at all, neither clause
          applies and the committee says exactly that.

        This is a coupling, and it is named: it reads one fact from S3
        and owns the rule applied to it.
        """

        assignment = archetype_for(symbol)

        if assignment.confidence is ArchetypeConfidence.UNESTABLISHED:
            return (
                Applicability.UNESTABLISHED,
                "No economic role is established for this asset, so this "
                "platform cannot say whether capturing network activity is "
                "part of what the token is.",
            )

        if assignment.archetype is TokenArchetype.MONETARY_NETWORK:
            return (
                Applicability.NOT_ECONOMICALLY_APPLICABLE,
                "This asset's established economic role is monetary: the fees "
                "its users pay are the budget that secures the network rather "
                "than a flow the token is entitled to. Asking whether they are "
                "captured for holders is the wrong instrument, so the question "
                "is left unanswered rather than answered adversely.",
            )

        return (
            Applicability.APPLICABLE,
            f"This asset's established economic role — "
            f"{assignment.definition.name} — is one where activity accruing "
            "to the token is part of what the token is, so whether it does is "
            "a meaningful question.",
        )

    async def judge(self, symbol: str) -> CommitteeJudgment:
        asset = symbol.upper().strip()

        # Three questions, in order, never collapsed: is this
        # economically meaningful, can we establish whether it is, and
        # do we have the evidence. Collapsing the first two makes
        # Bitcoin look adverse for lacking mechanics it was never meant
        # to have, and makes Bittensor — whose problem is entirely
        # different — look identical to it.
        applies, because = self.applicability(asset)

        if applies is Applicability.UNESTABLISHED:
            return abstain(
                asset,
                self.REMIT,
                AbstentionReason.APPLICABILITY_UNESTABLISHED,
                because,
            )

        if not applies.is_applicable:
            return abstain(
                asset,
                self.REMIT,
                AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
                because,
            )

        findings = self.evidence(asset)

        if not findings:
            return abstain(
                asset,
                self.REMIT,
                AbstentionReason.INSUFFICIENT_EVIDENCE,
                "No eligible fee or capture evidence is held for this asset.",
            )

        if not self.enabled():
            return unavailable(
                asset,
                self.REMIT,
                "Committee judgment is off, so no verdict was reached. The "
                "eligible evidence below is unchanged and stands on its own.",
            )

        provider = self._provider

        if provider is None:
            resolved = resolve_provider()

            if isinstance(resolved, str):
                return unavailable(asset, self.REMIT, resolved)

            provider = resolved

        try:
            payload, model = await self._draft(provider, asset, findings)
        except NarrativeDeclined as declined:
            return unavailable(asset, self.REMIT, str(declined))
        except JudgmentRejected as rejection:
            return unavailable(
                asset, self.REMIT, f"A judgment was drafted and refused: {rejection}"
            )
        except Exception:
            return unavailable(
                asset,
                self.REMIT,
                "The judging model could not be reached, so no verdict exists.",
            )

        try:
            return self._validated(asset, payload, findings, model)
        except JudgmentRejected as rejection:
            return unavailable(
                asset, self.REMIT, f"A judgment was drafted and refused: {rejection}"
            )

    async def _draft(
        self,
        provider: NarrativeProvider,
        asset: str,
        findings: tuple[EligibleFinding, ...],
    ) -> tuple[dict[str, Any], str]:
        request = DraftRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt(asset, findings),
            schema=judgment_schema(),
            max_tokens=MAX_DRAFT_TOKENS,
        )

        draft = await provider.draft(request)

        if not draft.text.strip():
            raise JudgmentRejected("the committee returned an empty draft")

        try:
            return json.loads(draft.text), draft.model
        except json.JSONDecodeError as error:
            raise JudgmentRejected(
                "the committee returned unparseable output"
            ) from error

    def _validated(
        self,
        asset: str,
        payload: dict[str, Any],
        findings: tuple[EligibleFinding, ...],
        model: str,
    ) -> CommitteeJudgment:
        answer = str(payload.get("verdict") or "").strip().lower()

        # An abstention chosen by the judge is still an abstention, and
        # is reported as one rather than as a failure.
        if answer == "abstain":
            return abstain(asset, self.REMIT, AbstentionReason.INSUFFICIENT_EVIDENCE)

        try:
            verdict = Verdict(answer)
        except ValueError as error:
            raise JudgmentRejected(
                f"the committee returned {answer!r}, which is not an answer to "
                "its question"
            ) from error

        refs = tuple(payload.get("refs") or ())

        known = {finding.ref for finding in findings}

        if not refs:
            raise JudgmentRejected("the verdict cited no evidence")

        unknown = [ref for ref in refs if ref not in known]

        if unknown:
            raise JudgmentRejected(
                f"the verdict cited evidence that was not supplied "
                f"({', '.join(unknown)})"
            )

        because = (payload.get("because") or "").strip()

        _check_sentence(because, findings)

        supporting = [finding for finding in findings if finding.ref in refs]

        return CommitteeJudgment(
            asset=asset,
            remit=self.REMIT,
            state=JudgmentState.JUDGED,
            verdict=verdict,
            # Counted, not chosen. The judge never saw this and it never
            # saw the verdict.
            confidence=confidence_from(
                supporting=len(supporting),
                across_captures=any(
                    len(finding.observations) > 1 for finding in supporting
                ),
            ),
            refs=refs,
            because=because,
            judged_at=datetime.now(UTC),
            model=model,
        )


# ── the contract ────────────────────────────────────────────────────


def judgment_schema() -> dict[str, Any]:
    """What the judge may return, and there is nothing else it can say.

    Three fields. No score, no recommendation, no confidence — the
    schema is the fence, and a model cannot answer a question it is
    given no room to answer.
    """

    return {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["mechanism_evidenced", "no_mechanism_evidenced", "abstain"],
            },
            "refs": {"type": "array", "items": {"type": "string"}},
            "because": {"type": "string"},
        },
        "required": ["verdict", "refs", "because"],
        "additionalProperties": False,
    }


def user_prompt(asset: str, findings: tuple[EligibleFinding, ...]) -> str:
    lines = [
        f"Asset: {asset}",
        "",
        "Established facts — the only facts you may use:",
    ]

    lines.extend(
        f"[{finding.ref}] ({finding.established_by}) {finding.stated}"
        for finding in findings
    )

    lines += [
        "",
        "Answer the committee's question: does this network's measured "
        "economic activity reach the token's holders?",
    ]

    return "\n".join(lines)


def _check_sentence(
    because: str,
    findings: tuple[EligibleFinding, ...],
) -> None:
    """Refuse a sentence that leaves the remit or the evidence."""

    if not because:
        raise JudgmentRejected("the verdict carried no reasoning")

    if len(because.split()) > MAX_BECAUSE_WORDS:
        raise JudgmentRejected(
            f"the reasoning ran to {len(because.split())} words, over the "
            f"{MAX_BECAUSE_WORDS}-word limit"
        )

    spoken = because.lower()

    for phrase in OUT_OF_REMIT:
        if re.search(rf"(?<![\w-]){re.escape(phrase)}\b", spoken):
            raise JudgmentRejected(
                f"the reasoning used {phrase!r}, which is outside this "
                "committee's question"
            )

    supplied = " ".join(finding.stated for finding in findings)

    # Reuse the event layer's normaliser: a figure the judge wrote must
    # be a figure the evidence gave it, in whatever form.
    from app.domain.crypto_event import anchors_in

    allowed = set(anchors_in(supplied))

    for anchor in anchors_in(because):
        if anchor not in allowed:
            raise JudgmentRejected(
                f"the reasoning contains the figure {anchor!r}, which appears "
                "in no supplied fact"
            )

    words = {word.lower() for word in re.findall(r"[A-Za-z][\w'’-]*", supplied)}

    for token in re.findall(r"[A-Za-z][\w'’-]*", because):
        if not token[:1].isupper():
            continue

        if token.lower() in words or token.lower() in _ORDINARY:
            continue

        raise JudgmentRejected(
            f"the reasoning names {token!r}, which appears in no supplied fact"
        )


#: Ordinary words that may open a sentence. The synthesist's lesson,
#: applied at a smaller scale: capitalisation is not a proper noun.
_ORDINARY = {
    "a",
    "an",
    "the",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "and",
    "or",
    "but",
    "no",
    "not",
    "none",
    "both",
    "each",
    "every",
    "all",
    "one",
    "two",
    "three",
    "there",
    "then",
    "when",
    "where",
    "whether",
    "while",
    "although",
    "however",
    "because",
    "since",
    "with",
    "without",
    "over",
    "under",
    "of",
    "on",
    "to",
    "in",
    "for",
    "from",
    "by",
    "at",
    "as",
    "users",
    "fees",
    "holders",
    "token",
    "tokens",
    "network",
    "activity",
    "economic",
    "measured",
    "reported",
    "source",
    "mechanism",
    "share",
    "day",
    "daily",
    "evidence",
    "figures",
    "figure",
    "several",
    "most",
    "some",
    "only",
    "also",
    "here",
    "neither",
    "nothing",
    "they",
    "their",
    "is",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "does",
    "do",
    "did",
    "reaches",
    "reach",
    "reached",
    "paid",
    "pays",
    "published",
    "publishes",
    "defined",
    "defines",
    "stated",
    "states",
    "supported",
    "supports",
}


def resolve_provider() -> NarrativeProvider | str:
    """The configured judge, or the sentence a surface should show."""

    settings = get_settings()

    name = (
        (
            os.environ.get(PROVIDER_ENV)
            or settings.movrvest_writer_provider
            or DEFAULT_PROVIDER
        )
        .strip()
        .lower()
    )

    if name not in DEFAULT_MODELS:
        return (
            f"The committee does not know the provider {name!r}, so no "
            "judgment was reached."
        )

    override = (os.environ.get(MODEL_ENV) or settings.movrvest_writer_model).strip()

    return build_provider(
        name=name,
        model=override or DEFAULT_MODELS[name],
        timeout=JUDGMENT_TIMEOUT,
        purpose="The Value Capture Committee",
    )


def _money(value: float) -> str:
    sign = "-" if value < 0 else ""

    size = abs(value)

    if size >= 1_000_000_000:
        return f"{sign}${size / 1_000_000_000:,.1f}bn"

    if size >= 1_000_000:
        return f"{sign}${size / 1_000_000:,.0f}m"

    if size >= 1_000:
        return f"{sign}${size / 1_000:,.0f}k"

    return f"{sign}${size:,.0f}"


def eligible_only(claims: Any) -> tuple[Any, ...]:
    """Filter any claim collection to what a committee may see.

    Exported so a caller can apply the rule without knowing it — the
    eligibility boundary should be hard to get wrong from outside.
    """

    return tuple(claim for claim in claims if is_eligible(claim.claim_type))
