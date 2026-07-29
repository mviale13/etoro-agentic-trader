"""Compatibility import for the application-layer InvestmentBrain.

New code should import InvestmentBrain from app.application.brain.
BrainService remains as a temporary alias for existing callers.
"""

from app.application.brain import InvestmentBrain

BrainService = InvestmentBrain

__all__ = ["BrainService"]
