"""The Executive Writer: language only, grounded or absent."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.thesis.investment_thesis import InvestmentThesis
from app.renderers.executive_writer import (
    ExecutiveWriter,
    NarrativeRejected,
    build_findings,
    narrative_from_payload,
)
from app.services.executive_writer_service import (
    FLAG,
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
        catalysts=("Next earnings report.",),
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


class StubMessages:
    def __init__(self, response) -> None:
        self._response = response
        self.last_kwargs: dict = {}

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class StubClient:
    def __init__(self, response) -> None:
        self.messages = StubMessages(response)


def stub_response(text: str, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=text)],
    )


@pytest.mark.anyio
async def test_the_writer_calls_the_model_and_validates_the_draft() -> None:
    import json

    findings = make_findings()
    client = StubClient(stub_response(json.dumps(valid_payload(findings))))

    writer = ExecutiveWriter(client=client, model="claude-opus-5")  # type: ignore[arg-type]

    narrative = await writer.write(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert narrative.headline == "Quality worth waiting on."

    sent = client.messages.last_kwargs
    assert sent["model"] == "claude-opus-5"
    assert "communication specialist" in sent["system"]
    # The grounding contract rides on structured output.
    assert sent["output_config"]["format"]["type"] == "json_schema"


@pytest.mark.anyio
async def test_a_declined_request_is_an_absence_not_a_narrative() -> None:
    client = StubClient(stub_response("", stop_reason="refusal"))
    writer = ExecutiveWriter(client=client, model="claude-opus-5")  # type: ignore[arg-type]

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


@pytest.mark.anyio
async def test_flag_on_without_credentials_states_why(monkeypatch) -> None:
    monkeypatch.setenv(FLAG, "on")
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
    assert "credentials" in (outcome.absent_reason or "")


@pytest.mark.anyio
async def test_a_rejected_draft_surfaces_its_reason(monkeypatch) -> None:
    import json

    monkeypatch.setenv(FLAG, "on")

    findings = make_findings()
    payload = valid_payload(findings)
    payload["recommendation"] = "RECOMMEND"

    client = StubClient(stub_response(json.dumps(payload)))
    writer = ExecutiveWriter(client=client, model="claude-opus-5")  # type: ignore[arg-type]

    outcome = await ExecutiveWriterService(writer=writer).narrate(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    assert outcome.narrative is None
    assert "different recommendation" in (outcome.absent_reason or "")
