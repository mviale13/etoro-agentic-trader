"""One case through every provider; only measured differences reported."""

import json

import pytest

from app.domain.token_usage import TokenUsage
from app.providers.model_prices import cost_usd
from app.providers.narrative_provider import Draft, DraftRequest
from app.renderers.executive_writer import ExecutiveWriter
from app.services.writer_comparison_service import WriterComparisonService
from tests.test_executive_writer import (
    make_decision,
    make_evidence,
    make_findings,
    make_opinions,
    make_thesis,
    valid_payload,
)


class MeasuredStubProvider:
    """A provider with a fixed draft, model and usage report."""

    def __init__(
        self,
        name: str,
        model: str,
        text: str,
        usage: TokenUsage | None,
    ) -> None:
        self.name = name
        self.model = model
        self._text = text
        self._usage = usage

    async def draft(self, request: DraftRequest) -> Draft:
        return Draft(text=self._text, model=self.model, usage=self._usage)


REPORTED_USAGE = TokenUsage(input_tokens=1000, output_tokens=2000)


def good_provider(
    name: str = "Anthropic",
    model: str = "claude-opus-5",
    usage: TokenUsage | None = REPORTED_USAGE,
) -> MeasuredStubProvider:
    return MeasuredStubProvider(
        name=name,
        model=model,
        text=json.dumps(valid_payload(make_findings())),
        usage=usage,
    )


def bad_provider(name: str = "OpenAI", model: str = "gpt-5") -> MeasuredStubProvider:
    payload = valid_payload(make_findings())
    payload["recommendation"] = "RECOMMEND"

    return MeasuredStubProvider(
        name=name,
        model=model,
        text=json.dumps(payload),
        usage=TokenUsage(input_tokens=900, output_tokens=100),
    )


async def compare(*providers) -> tuple:
    comparison = await WriterComparisonService(
        writers=tuple(ExecutiveWriter(provider=item) for item in providers),
    ).compare(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    return comparison.runs


@pytest.mark.anyio
async def test_both_providers_word_the_identical_decision() -> None:
    runs = await compare(good_provider(), good_provider(name="OpenAI", model="gpt-5"))

    assert [run.provider for run in runs] == ["Anthropic", "OpenAI"]
    assert all(run.narrative is not None for run in runs)

    # The one decision, echoed by both — the comparison is language,
    # never judgment.
    assert all(run.narrative.recommendation == "PREPARE" for run in runs)  # type: ignore[union-attr]


@pytest.mark.anyio
async def test_latency_is_measured_and_cost_is_priced_from_reported_usage() -> None:
    runs = await compare(good_provider())
    run = runs[0]

    assert run.latency_seconds is not None
    assert run.latency_seconds >= 0.0

    assert run.usage == TokenUsage(input_tokens=1000, output_tokens=2000)

    # 1,000 in at $5/MTok + 2,000 out at $25/MTok.
    assert run.cost_usd == pytest.approx(0.055)


@pytest.mark.anyio
async def test_a_model_absent_from_the_price_table_has_an_absent_cost() -> None:
    runs = await compare(good_provider(model="claude-experimental"))

    assert runs[0].usage is not None
    assert runs[0].cost_usd is None


@pytest.mark.anyio
async def test_unreported_usage_is_an_absent_cost_not_a_zero() -> None:
    runs = await compare(good_provider(usage=None))

    assert runs[0].usage is None
    assert runs[0].cost_usd is None


@pytest.mark.anyio
async def test_a_rejected_draft_is_reported_beside_the_accepted_one() -> None:
    runs = await compare(good_provider(), bad_provider())

    accepted, rejected = runs

    assert accepted.narrative is not None

    assert rejected.narrative is None
    assert "different recommendation" in (rejected.absent_reason or "")
    # The attempt was real, so its duration is reported; the usage
    # report did not survive the failure path.
    assert rejected.latency_seconds is not None
    assert rejected.usage is None
    assert rejected.cost_usd is None


@pytest.mark.anyio
async def test_a_provider_that_cannot_be_built_is_a_worded_run(monkeypatch) -> None:
    from app.config import Settings

    # Silence every credential source: the environment, `.env`, and both
    # modules that read them. A patch that misses one does not fail this
    # test — it builds a real client and calls a real model.
    for module in (
        "app.services.executive_writer_service",
        "app.services.narrative_providers",
    ):
        monkeypatch.setattr(
            f"{module}.get_settings",
            lambda: Settings(_env_file=None),
        )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MOVRVEST_WRITER_PROVIDER", raising=False)

    comparison = await WriterComparisonService(providers=("openai",)).compare(
        symbol="MSFT",
        decision=make_decision(),
        thesis=make_thesis(),
        evidence=make_evidence(),
        opinions=make_opinions(),
    )

    run = comparison.runs[0]

    assert run.provider == "OpenAI"
    assert run.narrative is None
    assert "OpenAI credentials" in (run.absent_reason or "")
    # Nothing ran, so there is no duration to report.
    assert run.latency_seconds is None


def test_cost_arithmetic_prices_the_reported_tokens() -> None:
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)

    assert cost_usd("claude-opus-5", usage) == pytest.approx(30.00)
    assert cost_usd("gpt-5", usage) == pytest.approx(11.25)
    assert cost_usd("unpriced-model", usage) is None
    assert cost_usd("claude-opus-5", None) is None
