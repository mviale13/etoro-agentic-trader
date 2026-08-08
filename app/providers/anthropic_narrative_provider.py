"""Anthropic as a narrative provider — the first implementation of the seam."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.token_usage import TokenUsage
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic


class AnthropicNarrativeProvider:
    """
    Carry a draft request to Claude and hand back what it wrote.

    This is exactly the wire call the Executive Writer used to make
    itself, moved behind the provider seam: structured output enforced
    through `output_config`'s JSON schema, a safety decline surfaced as
    `NarrativeDeclined`, and the reported token usage carried through.
    Nothing here judges the draft.
    """

    name = "Anthropic"

    def __init__(
        self,
        client: AsyncAnthropic,
        model: str,
    ) -> None:
        self._client = client
        self.model = model

    async def draft(self, request: DraftRequest) -> Draft:
        from anthropic import AnthropicError

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens,
                system=request.system_prompt,
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": request.schema,
                    }
                },
                messages=[
                    {
                        "role": "user",
                        "content": request.user_prompt,
                    }
                ],
            )
        except AnthropicError as failed:
            # An outage, an exhausted balance, a rate limit. Wrapped so
            # it travels the seam as the worded absence every caller
            # already carries to its surface, exactly as the OpenAI
            # provider wraps its own.
            raise NarrativeDeclined(
                f"{self.name} could not complete the request: {failed}"
            ) from failed

        if response.stop_reason == "refusal":
            raise NarrativeDeclined(
                "The writing model declined the request, so no narrative was produced."
            )

        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )

        return Draft(
            text=text,
            model=self.model,
            usage=self._usage_of(response),
        )

    @staticmethod
    def _usage_of(response: object) -> TokenUsage | None:
        """The usage the API reported, or None where it reported none."""

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)

        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
