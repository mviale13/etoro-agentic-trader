"""Both providers carry the same contract over their own wire."""

from types import SimpleNamespace

import pytest

from app.providers.anthropic_narrative_provider import AnthropicNarrativeProvider
from app.providers.narrative_provider import DraftRequest, NarrativeDeclined
from app.providers.openai_narrative_provider import OpenAINarrativeProvider
from app.renderers.executive_writer import SYSTEM_PROMPT, narrative_schema


def request() -> DraftRequest:
    return DraftRequest(
        system_prompt=SYSTEM_PROMPT,
        user_prompt="Security: MSFT",
        schema=narrative_schema(),
        max_tokens=8000,
    )


# ------------------------------------------------------------------
# Anthropic — the first implementation of the seam.
# ------------------------------------------------------------------


class AnthropicStubMessages:
    def __init__(self, response) -> None:
        self._response = response
        self.last_kwargs: dict = {}

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class AnthropicStubClient:
    def __init__(self, response) -> None:
        self.messages = AnthropicStubMessages(response)


def anthropic_response(
    text: str,
    stop_reason: str = "end_turn",
    usage=None,
):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=text)],
        usage=usage,
    )


@pytest.mark.anyio
async def test_anthropic_sends_the_schema_as_structured_output() -> None:
    client = AnthropicStubClient(anthropic_response('{"headline": "x"}'))
    provider = AnthropicNarrativeProvider(client=client, model="claude-opus-5")  # type: ignore[arg-type]

    draft = await provider.draft(request())

    assert draft.text == '{"headline": "x"}'
    assert draft.model == "claude-opus-5"

    sent = client.messages.last_kwargs
    assert sent["model"] == "claude-opus-5"
    assert sent["system"] == SYSTEM_PROMPT
    assert sent["max_tokens"] == 8000
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert sent["output_config"]["format"]["schema"] == narrative_schema()


@pytest.mark.anyio
async def test_anthropic_maps_a_refusal_to_a_decline() -> None:
    client = AnthropicStubClient(anthropic_response("", stop_reason="refusal"))
    provider = AnthropicNarrativeProvider(client=client, model="claude-opus-5")  # type: ignore[arg-type]

    with pytest.raises(NarrativeDeclined, match="declined"):
        await provider.draft(request())


@pytest.mark.anyio
async def test_anthropic_reports_the_usage_the_api_reported() -> None:
    client = AnthropicStubClient(
        anthropic_response(
            "{}",
            usage=SimpleNamespace(input_tokens=1200, output_tokens=340),
        )
    )
    provider = AnthropicNarrativeProvider(client=client, model="claude-opus-5")  # type: ignore[arg-type]

    draft = await provider.draft(request())

    assert draft.usage is not None
    assert draft.usage.input_tokens == 1200
    assert draft.usage.output_tokens == 340


@pytest.mark.anyio
async def test_anthropic_reports_no_usage_as_absent_not_zero() -> None:
    client = AnthropicStubClient(anthropic_response("{}"))
    provider = AnthropicNarrativeProvider(client=client, model="claude-opus-5")  # type: ignore[arg-type]

    draft = await provider.draft(request())

    assert draft.usage is None


# ------------------------------------------------------------------
# OpenAI — the same contract through strict structured outputs.
# ------------------------------------------------------------------


class OpenAIStubCompletions:
    def __init__(self, response) -> None:
        self._response = response
        self.last_kwargs: dict = {}

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class OpenAIStubClient:
    def __init__(self, response) -> None:
        self.chat = SimpleNamespace(completions=OpenAIStubCompletions(response))


def openai_response(
    text: str | None,
    refusal: str | None = None,
    usage=None,
):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text, refusal=refusal),
            )
        ],
        usage=usage,
    )


@pytest.mark.anyio
async def test_openai_sends_the_same_schema_strictly() -> None:
    client = OpenAIStubClient(openai_response('{"headline": "x"}'))
    provider = OpenAINarrativeProvider(client=client, model="gpt-5")  # type: ignore[arg-type]

    draft = await provider.draft(request())

    assert draft.text == '{"headline": "x"}'
    assert draft.model == "gpt-5"

    sent = client.chat.completions.last_kwargs
    assert sent["model"] == "gpt-5"
    assert sent["max_completion_tokens"] == 8000
    # Wording a finished case is formatting, not deep reasoning — and
    # default-effort reasoning starves the draft budget (measured).
    assert sent["reasoning_effort"] == "low"
    assert sent["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}

    contract = sent["response_format"]
    assert contract["type"] == "json_schema"
    assert contract["json_schema"]["strict"] is True
    # The identical schema the Anthropic provider sends: one contract,
    # two wires.
    assert contract["json_schema"]["schema"] == narrative_schema()


@pytest.mark.anyio
async def test_openai_maps_a_refusal_to_a_decline() -> None:
    client = OpenAIStubClient(openai_response(None, refusal="I cannot write this."))
    provider = OpenAINarrativeProvider(client=client, model="gpt-5")  # type: ignore[arg-type]

    with pytest.raises(NarrativeDeclined, match="declined"):
        await provider.draft(request())


@pytest.mark.anyio
async def test_openai_reports_the_usage_the_api_reported() -> None:
    client = OpenAIStubClient(
        openai_response(
            "{}",
            usage=SimpleNamespace(prompt_tokens=1500, completion_tokens=420),
        )
    )
    provider = OpenAINarrativeProvider(client=client, model="gpt-5")  # type: ignore[arg-type]

    draft = await provider.draft(request())

    assert draft.usage is not None
    assert draft.usage.input_tokens == 1500
    assert draft.usage.output_tokens == 420


@pytest.mark.anyio
async def test_openai_reports_no_usage_as_absent_not_zero() -> None:
    client = OpenAIStubClient(openai_response("{}"))
    provider = OpenAINarrativeProvider(client=client, model="gpt-5")  # type: ignore[arg-type]

    draft = await provider.draft(request())

    assert draft.usage is None
