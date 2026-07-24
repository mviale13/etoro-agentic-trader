from dataclasses import dataclass


@dataclass
class Signal:
    action: str
    confidence: float
    fast: float | None
    slow: float | None


def moving_average_signal(
    closes: list[float],
    fast_period: int = 10,
    slow_period: int = 30,
) -> Signal:
    if fast_period >= slow_period:
        raise ValueError("fast_period must be less than slow_period")
    if len(closes) < slow_period:
        return Signal("hold", 0.0, None, None)

    fast = sum(closes[-fast_period:]) / fast_period
    slow = sum(closes[-slow_period:]) / slow_period
    distance = abs(fast - slow) / slow if slow else 0
    confidence = min(0.85, 0.5 + distance * 10)
    return Signal("buy" if fast > slow else "exit", confidence, fast, slow)
