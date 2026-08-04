"""Compatibility import for the application-layer LearningEngine.

New code should import LearningEngine from app.application.learning.
LearningService remains as a temporary alias for existing callers.
"""

from app.application.learning import LearningEngine

LearningService = LearningEngine

__all__ = ["LearningService"]
