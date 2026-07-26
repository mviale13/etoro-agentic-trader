from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationSnapshot:
    forward_pe: float | None
    trailing_pe: float | None
    peg_ratio: float | None
    dividend_yield: float | None
