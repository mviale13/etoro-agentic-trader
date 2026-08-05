"""Keep the suite hermetic: no test may read the developer's own `.env`.

The Executive Writer reads its flag, provider, model and keys from the
process environment first and `.env` second. On a developer machine that
`.env` legitimately carries a live key and the flag turned on — which
must never turn a unit test into a live model call. Every test therefore
starts with the writer's configuration silenced on both sources; a test
that wants the writer on says so explicitly with `monkeypatch.setenv`,
which still wins over the silenced fallback.
"""

from __future__ import annotations

import pytest

WRITER_ENVIRONMENT = (
    "MOVRVEST_EXECUTIVE_WRITER",
    "MOVRVEST_WRITER_PROVIDER",
    "MOVRVEST_WRITER_MODEL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
)


@pytest.fixture(autouse=True)
def hermetic_writer_configuration(monkeypatch):
    from app.config import Settings

    monkeypatch.setattr(
        "app.services.executive_writer_service.get_settings",
        lambda: Settings(_env_file=None),
    )

    for name in WRITER_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
