"""The Executive Writer: language only, grounded or absent."""

from datetime import UTC, datetime

import pytest

from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.thesis.investment_thesis import InvestmentThesis
from app.providers.narrative_provider import (
    Draft,
    DraftRequest,
    NarrativeDeclined,
)
from app.renderers.executive_writer import (
    ExecutiveWriter,
    NarrativeRejected,
    build_findings,
    narrative_from_payload,
    narrative_schema,
)
from app.services.executive_writer_service import (
    FLAG,
    MODEL_ENV,
    PROVIDER_ENV,
    ExecutiveWriterService,
)


def make_decision(state: DecisionState = DecisionState.PREPARE) -> ExecutiveDecision:
    return ExecutiveDecision(
        symbol="MSFT",
        state=state,
        conviction=72,
        rationale="Quality and evidence gates cleared; valuation has not.",
        evidence_weighed=(
            "Strong profitability.",
            "Valuation reads expensive.",
        ),
        missing_evidence=("No price target is measured.",),
        context_risks=("Cash concentration.",),
        decided_at=datetime(2026, 8, 5, tzinfo=UTC),
    )


def make_thesis() -> InvestmentThesis:
    return InvestmentThesis(
        symbol="MSFT",
        recommendation="PREPARE",
        confidence=0.62,
        conviction=72,
        summary="A quality business held back by its price.",
        strengths=("Strong profitability.",),
        risks=("Valuation reads expensive.",),
        catalysts=("Reports earnings in 6 days (Aug 11).",),
        invalidation_conditions=("Margins compress two quarters running.",),
        expected_holding_period="3-5 years",
        created_at=datetime(2026, 8, 5, tzinfo=UTC),
        evidence_weighed=("Strong profitability.",),
        context_strengths=("Healthy liquidity.",),
        context_risks=("Cash concentration.",),
        previous_decisions="PREPARE on August 4.",
    )


def make_evidence() -> DecisionEvidence:
    return DecisionEvidence(
        symbol="MSFT",
        evidence_score=70,
        quality_score=80,
        security_evidenced=True,
    )


def make_opinions() -> tuple[CommitteeOpinion, ...]:
    return (
        CommitteeOpinion(
            committee="Quality",
            recommendation=Recommendation.BUY,
            confidence=74.0,
            summary="Profitability is broad and persistent.",
            evidence=(),
        ),
        CommitteeOpinion(
            committee="Risk",
            recommendation=Recommendation.HOLD,
            confidence=None,
            summary="Portfolio risk could not be fully measured.",
            evidence=(),
        ),
    )


def make_findings():
    return build_findings(
        make_decision(),
        make_thesis(),
        make_evidence(),
        make_opinions(),
    )


def valid_payload(findings) -> dict:
    first = findings[0].id

    return {
        "headline": "Quality worth waiting on.",
        "recommendation": "PREPARE",
        "sections": [
            {
                "section": "executive_summary",
                "text": "The case clears quality and evidence gates.",
                "finding_ids": [first],
            }
        ],
    }


def test_a_dated_catalyst_reaches_the_writer_as_its_own_finding() -> None:
    """
    "Why now" is entitled to rest on a date, and to be told it is only a date.

    The catalyst used to arrive among the thesis statements, where it was
    the market's mood under every symbol. It now arrives as a scheduled
    event about this security, sourced as an event rather than a view — the
    writer may say the report is coming, never what it will say.
    """

    findings = make_findings()

    scheduled = next(f for f in findings if f.id.startswith("W"))

    assert scheduled.statement == "Scheduled: Reports earnings in 6 days (Aug 11)."
    assert "not a view on its outcome" in scheduled.source

    # Once, not twice: it is no longer restated among the thesis findings.
    assert sum("Reports earnings" in f.statement for f in findings) == 1


def test_findings_word_the_canonical_objects_with_stable_ids() -> None:
    findings = make_findings()
    ids = [finding.id for finding in findings]

    assert ids[0] == "D1"
    assert "E1" in ids and "M1" in ids and "C1" in ids

    # An abstention is worded as an abstention, never as opposition.
    abstained = next(f for f in findings if "Risk committee" in f.statement)
    assert "abstained" in abstained.statement
    assert "not opposition" in abstained.statement


def test_a_grounded_draft_becomes_a_narrative() -> None:
    findings = make_findings()

    narrative = narrative_from_payload(
        valid_payload(findings),
        symbol="MSFT",
        decision_state="PREPARE",
        findings=findings,
        model="claude-opus-5",
    )

    assert narrative.recommendation == "PREPARE"
    assert narrative.sections[0].finding_ids == (findings[0].id,)
    assert "Executive Writer" in narrative.reading.source


def test_the_writer_may_never_change_the_recommendation() -> None:
    findings = make_findings()
    payload = valid_payload(findings)
    payload["recommendation"] = "RECOMMEND"

    with pytest.raises(NarrativeRejected, match="different recommendation"):
        narrative_from_payload(
            payload,
            symbol="MSFT",
            decision_state="PREPARE",
            findings=findings,
            model="claude-opus-5",
        )


def test_a_citation_to_a_nonexistent_finding_rejects_the_draft() -> None:
    findings = make_findings()
    payload = valid_payload(findings)
    payload["sections"][0]["finding_ids"] = ["Z9"]

    with pytest.raises(NarrativeRejected, match="do not exist"):
        narrative_from_payload(
            payload,
            symbol="MSFT",
            decision_state="PREPARE",
            findings=findings,
            model="claude-opus-5",
        )


def test_a_section_citing_nothing_rejects_the_draft() -> None:
    findings = make_findings()
    payload = valid_payload(findings)
    payload["sections"][0]["finding_ids"] = []

    with pytest.raises(NarrativeRejected, match="cites no findings"):
        narrative_from_payload(
            payload,
            symbol="MSFT",
            decision_state="PREPARE",
            findings=findings,
            model="claude-opus-5",
        )


def test_an_unknown_section_rejects_the_draft() -> None:
    findings = make_findings()
    payload = valid_payload(findings)
    payload["sections"][0]["section"] = "price_target"

    with pytest.raises(NarrativeRejected, match="unknown or repeated"):
        narrative_from_payload(
            payload,
            symbol="MSFT",
            decision_state="PREPARE",
            findings=findings,
            model="claude-opus-5",
        )


class StubProvider:
    """A provider that returns a canned draft and remembers the request."""

    name = "Stub"

    def __init__(
        self,
        text: str,
        model: str = "claude-opus-5",
        declines: bool = False,
    ) -> None:
        self.model = model
        self._text = text
        self._declines = declines
        self.last_request: DraftRequest | None = None

    async def draft(self, request: DraftRequest) -> Draft:
        self.last_request = request

        if self._declines:
            raise NarrativeDeclined(
                "The writing model declined the request, so no narrative was produced."
            )

        return Draft(text=self._text, model=self.model, usage=None)


@pytest.mark.anyio
async def test_the_writer_calls_the_provider_and_validates_the_draft() -> None:
    import json

    findings = make_findings()
    provider = StubProvider(json.dumps(valid_payload(findings)))

    writer = ExecutiveWriter(provider=provider)

    narrative = await writer.write(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert narrative.headline == "Quality worth waiting on."
    # The narrative names the model the provider actually used.
    assert narrative.model == "claude-opus-5"

    sent = provider.last_request
    assert sent is not None
    assert "communication specialist" in sent.system_prompt
    assert "[D1]" in sent.user_prompt
    # The grounding contract rides on one shared schema, whichever
    # provider carries it.
    assert sent.schema == narrative_schema()


@pytest.mark.anyio
async def test_an_empty_draft_states_its_own_absence() -> None:
    """A budget-starved draft is empty, and the absence says so rather
    than blaming the parser."""

    writer = ExecutiveWriter(provider=StubProvider(""))

    with pytest.raises(NarrativeRejected, match="empty draft"):
        await writer.write(
            symbol="MSFT",
            decision=make_decision(),
            thesis=make_thesis(),
            evidence=make_evidence(),
            opinions=make_opinions(),
        )


@pytest.mark.anyio
async def test_a_declined_request_is_an_absence_not_a_narrative() -> None:
    writer = ExecutiveWriter(provider=StubProvider("", declines=True))

    with pytest.raises(NarrativeRejected, match="declined"):
        await writer.write(
            symbol="MSFT",
            decision=make_decision(),
            thesis=make_thesis(),
            evidence=make_evidence(),
            opinions=make_opinions(),
        )


@pytest.mark.anyio
async def test_the_flag_off_is_an_honest_absence(monkeypatch) -> None:
    monkeypatch.delenv(FLAG, raising=False)

    outcome = await ExecutiveWriterService().narrate(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert outcome.narrative is None
    assert outcome.absent_reason is not None
    assert "off" in outcome.absent_reason


@pytest.fixture
def no_env_file(monkeypatch):
    """Keys live in `.env` as well as the environment; a test asserting
    their absence must silence both sources, not just the one
    `monkeypatch.delenv` reaches."""

    from app.config import Settings

    monkeypatch.setattr(
        "app.services.executive_writer_service.get_settings",
        lambda: Settings(_env_file=None),
    )


@pytest.mark.anyio
async def test_flag_on_without_credentials_states_why(monkeypatch, no_env_file) -> None:
    """The default provider is OpenAI; its missing key is named."""

    monkeypatch.setenv(FLAG, "on")
    monkeypatch.delenv(PROVIDER_ENV, raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    outcome = await ExecutiveWriterService().narrate(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert outcome.narrative is None
    assert "OpenAI credentials" in (outcome.absent_reason or "")


@pytest.mark.anyio
async def test_anthropic_selected_without_credentials_states_why(
    monkeypatch, no_env_file
) -> None:
    monkeypatch.setenv(FLAG, "on")
    monkeypatch.setenv(PROVIDER_ENV, "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    outcome = await ExecutiveWriterService().narrate(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert outcome.narrative is None
    assert "Anthropic credentials" in (outcome.absent_reason or "")


@pytest.mark.anyio
async def test_an_unknown_provider_is_a_worded_absence(monkeypatch) -> None:
    """Never a silent fallback: swapping models is configuration, stated."""

    monkeypatch.setenv(FLAG, "on")
    monkeypatch.setenv(PROVIDER_ENV, "mystery")

    outcome = await ExecutiveWriterService().narrate(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert outcome.narrative is None
    assert "does not know the provider" in (outcome.absent_reason or "")


def test_the_model_override_pins_only_the_configured_provider(monkeypatch) -> None:
    """One env names one model; the other provider keeps its own default."""

    from app.services.executive_writer_service import resolve_provider

    monkeypatch.delenv(PROVIDER_ENV, raising=False)  # default: openai
    monkeypatch.setenv(MODEL_ENV, "gpt-5-mini")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    openai_provider = resolve_provider("openai")
    anthropic_provider = resolve_provider("anthropic")

    assert not isinstance(openai_provider, str)
    assert not isinstance(anthropic_provider, str)
    assert openai_provider.model == "gpt-5-mini"
    assert anthropic_provider.model == "claude-opus-5"


@pytest.mark.anyio
async def test_a_rejected_draft_surfaces_its_reason(monkeypatch) -> None:
    import json

    monkeypatch.setenv(FLAG, "on")

    findings = make_findings()
    payload = valid_payload(findings)
    payload["recommendation"] = "RECOMMEND"

    writer = ExecutiveWriter(provider=StubProvider(json.dumps(payload)))

    outcome = await ExecutiveWriterService(writer=writer).narrate(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert outcome.narrative is None
    assert "different recommendation" in (outcome.absent_reason or "")
