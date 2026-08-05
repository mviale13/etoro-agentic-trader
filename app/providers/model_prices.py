"""Published model prices, stated with the date they were read.

A cost line on a comparison multiplies two numbers: token counts the
provider reported for the call, and a price the provider published for
the model. The counts are measured; the price is a quotation, and it
goes stale the day either provider changes its price page. That is why
the table carries the date it was read, why every consumer states that
date beside the cost, and why a model absent from the table produces an
absent cost rather than a guessed one.
"""

from __future__ import annotations

from datetime import date

from app.domain.token_usage import TokenUsage

#: When these prices were read off the providers' published price pages.
PRICES_STATED_ON = date(2026, 8, 5)

#: USD per million tokens, (input, output), as published.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.00, 25.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "gpt-5": (1.25, 10.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
}


def cost_usd(model: str, usage: TokenUsage | None) -> float | None:
    """
    What the call cost at the stated prices, or None where it cannot be said.

    None when the provider reported no usage, or when the model is not
    in the table — both are absences to report, not zeros to assume.
    """

    if usage is None:
        return None

    prices = PRICES_PER_MTOK.get(model)

    if prices is None:
        return None

    input_price, output_price = prices

    return (
        usage.input_tokens * input_price + usage.output_tokens * output_price
    ) / 1_000_000
