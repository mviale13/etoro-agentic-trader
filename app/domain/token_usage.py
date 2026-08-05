"""What one model call reported spending."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """
    Token counts as the provider reported them — reported, never estimated.

    Both figures come off the provider's own response. Where a provider
    reports nothing, the caller carries None rather than an approximation:
    a token count on a cost line reads as a measurement, and estimating
    one would put an invented number under a real price.
    """

    input_tokens: int
    output_tokens: int
