"""OpenAI as a narrative provider, held to the same contract as Anthropic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from app.domain.token_usage import TokenUsage
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined

if TYPE_CHECKING:
    from openai import AsyncOpenAI


class OpenAINarrativeProvider:
    """
    Carry a draft request to an OpenAI model and hand back what it wrote.

    The same JSON schema the Anthropic provider sends through
    `output_config` is enforced here through OpenAI's strict structured
    outputs, so both providers are held to one contract and their drafts
    pass through one validator. A refusal is surfaced as
    `NarrativeDeclined`, exactly as the Anthropic provider surfaces its
    decline. Nothing here judges the draft.
    """

    name = "OpenAI"

    #: Wording a finished case is formatting, not deep reasoning, and the
    #: GPT-5 models spend reasoning tokens out of the same completion
    #: budget the draft needs. Measured on a trivial prompt: default
    #: effort burned 2,112 reasoning tokens where "low" spent 192 — and
    #: on a full dossier the default starved the draft to empty.
    REASONING_EFFORT: Final = "low"

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
    ) -> None:
        self._client = client
        self.model = model

    async def draft(self, request: DraftRequest) -> Draft:
        from openai import OpenAIError
        from openai.types.chat import (
            ChatCompletionMessageParam,
            ChatCompletionSystemMessageParam,
            ChatCompletionUserMessageParam,
        )
        from openai.types.shared_params import ResponseFormatJSONSchema
        from openai.types.shared_params.response_format_json_schema import (
            JSONSchema,
        )

        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=request.system_prompt,
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=request.user_prompt,
            ),
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                # The reasoning-model parameter name; `max_tokens` is not
                # accepted by current OpenAI models.
                max_completion_tokens=request.max_tokens,
                reasoning_effort=self.REASONING_EFFORT,
                messages=messages,
                response_format=ResponseFormatJSONSchema(
                    type="json_schema",
                    json_schema=JSONSchema(
                        name="executive_narrative",
                        strict=True,
                        schema=request.schema,
                    ),
                ),
            )
        except OpenAIError as failed:
            # An outage, an exhausted balance, a rate limit. Wrapped so
            # it travels the seam as the worded absence every caller
            # already carries to its surface — measured twice as a raw
            # traceback ending a run against this platform's own absence
            # discipline, once in an observe run and once on the first
            # statement reading.
            raise NarrativeDeclined(
                f"{self.name} could not complete the request: {failed}"
            ) from failed

        choice = response.choices[0]

        if getattr(choice.message, "refusal", None):
            raise NarrativeDeclined(
                "The writing model declined the request, so no narrative was produced."
            )

        return Draft(
            text=choice.message.content or "",
            model=self.model,
            usage=self._usage_of(response),
        )

    @staticmethod
    def _usage_of(response: object) -> TokenUsage | None:
        """The usage the API reported, or None where it reported none."""

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)

        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
