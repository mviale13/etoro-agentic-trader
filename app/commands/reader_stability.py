"""Measure how reproducibly this platform reads a filing.

The command is its own opt-in, exactly as `writer-compare` is: invoking
it is the request to spend N readings of a document on a measurement,
and it stores none of them.
"""

from __future__ import annotations

from app.renderers.reader_stability_renderer import ReaderStabilityRenderer
from app.services.reader_calibration import (
    DEFAULT_READINGS,
    ReaderCalibrationService,
    ReaderCalibrationUnavailable,
)


class ReaderStabilityCommand:
    async def run(self, symbol: str, readings: int = DEFAULT_READINGS) -> int:
        normalized = symbol.upper().strip()

        try:
            service = ReaderCalibrationService()
            stability = await service.calibrate(normalized, readings)
        except ReaderCalibrationUnavailable as unavailable:
            print(f"{normalized} — not calibrated")
            print()
            print(str(unavailable))
            return 1

        ReaderStabilityRenderer.render(stability)

        return 0


async def run(symbol: str, readings: int = DEFAULT_READINGS) -> int:
    return await ReaderStabilityCommand().run(symbol, readings)
