"""Compose the Artificial CIO's digital-asset answer from stored doors.

Read-only, like every consumption door on this platform: the bridge
projects recorded judgments, the assessment reads stored evidence, and
the CIO's rule is a deterministic function of both. Opening this door
fetches nothing, asks no model, records no judgment and writes no
journal event — the decision is a projection, recomputed on every read.
"""

from __future__ import annotations

from app.cio.digital_asset_decision import (
    DigitalAssetDecision,
    decide_digital_asset,
)
from app.services.decision_bridge_service import DecisionBridgeService
from app.services.investor_assessment_service import InvestorAssessmentService


class DigitalAssetDecisionService:
    """One canonical answer per digital asset, from what is already held."""

    def __init__(
        self,
        bridge: DecisionBridgeService | None = None,
        assessment: InvestorAssessmentService | None = None,
    ) -> None:
        self._bridge = bridge or DecisionBridgeService()
        self._assessment = assessment or InvestorAssessmentService()

    def decide(self, symbol: str) -> DigitalAssetDecision:
        asset = symbol.upper().strip()

        return decide_digital_asset(
            self._bridge.considerations(asset),
            self._assessment.for_asset(asset),
        )
