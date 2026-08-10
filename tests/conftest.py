"""Keep the suite hermetic: no test may read the developer's own `.env`.

Two seams in this platform put a prompt to a model — the Executive Writer
and the knowledge reader — and both read their flag, provider, model and
keys from the process environment first and `.env` second. On a developer
machine that `.env` legitimately carries a live key, which must never
turn a unit test into a live model call. Every test therefore starts with
both configurations silenced on both sources; a test that wants one of
them on says so explicitly with `monkeypatch.setenv`, which still wins
over the silenced fallback.

**The failure mode this exists for is a passing test.** A test that
asserts "no credentials, so it did not run" and whose silencing misses
one source does not go red — it builds a real client, calls a real model
and passes, having spent money. It was caught here twice: once when
credential reading moved into `narrative_providers`, and once when the
knowledge reader became the pipeline's default and a signal test that had
never touched the network began reading a 10-K.

So `SETTINGS_READERS` names every module that can reach a credential, and
adding one means adding it here. The cost of forgetting is invisible.

**A keyless provider needs the same guard for a different reason.** The
crypto market endpoints answer without a credential, so silencing a key
does nothing for them — and the acquisition cycle calls them
unconditionally rather than only for a crypto security. A test that
reached them would not fail: it would pass, eight HTTP calls and ninety
seconds later, having spent a shared rate limit. It was caught exactly
that way, by running the committed tree in isolation where no cache
stood in the way. `NETWORK_SEAMS` blocks the wire itself, so a test that
reaches for it goes red with the fix in the message.
"""

from __future__ import annotations

import pytest

#: Every module that resolves configuration into a live client. Each is
#: patched to a `Settings` that has never seen `.env`.
SETTINGS_READERS = (
    "app.services.executive_writer_service",
    "app.services.company_knowledge_reader",
    "app.services.narrative_providers",
    # Not a model, but the same failure mode: a metered third-party
    # key whose allowance a test could quietly spend.
    "app.providers.token_insight_provider",
    "app.providers.token_facts_provider",
    "app.providers.coingecko_facts_provider",
)

#: Every variable that could turn a reading or a drafting on, or hand it
#: a credential, from the process environment.
MODEL_ENVIRONMENT = (
    "MOVRVEST_EXECUTIVE_WRITER",
    "MOVRVEST_WRITER_PROVIDER",
    "MOVRVEST_WRITER_MODEL",
    "MOVRVEST_READER_PROVIDER",
    "MOVRVEST_READER_MODEL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "TOKENINSIGHT_API_KEY",
    "COINGECKO_API_KEY",
)


#: Every method that puts a request on the wire without needing a key.
#:
#: Each is the one place its provider touches the network, so blocking it
#: blocks the provider without pretending to know its internals. A test
#: that wants a provider's behaviour passes a stub reader; a test that
#: wants the parsing passes a recorded payload. Neither needs this.
NETWORK_SEAMS = ("app.providers.coingecko_market_provider.CoinGeckoMarketProvider",)


@pytest.fixture(autouse=True)
def hermetic_model_configuration(monkeypatch):
    from app.config import Settings

    for module in SETTINGS_READERS:
        monkeypatch.setattr(
            f"{module}.get_settings",
            lambda: Settings(_env_file=None),
        )

    for name in MODEL_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)

    def _refuse(*args, **kwargs):
        raise AssertionError(
            "A test reached a live provider. Pass a stub reader or a "
            "recorded claim set instead — see tests/conftest.py."
        )

    for seam in NETWORK_SEAMS:
        monkeypatch.setattr(f"{seam}._request", _refuse)

        # A blocked call still paced itself first: the batch sleeps
        # between requests to stay under a rate limit, and eight of those
        # turned a four-second suite into ninety-six. Refusing the wire
        # and leaving the wait in place is a guard that works and costs
        # more than the calls it prevented.
        monkeypatch.setattr(f"{seam}.PACE", 0.0)
        monkeypatch.setattr(f"{seam}.RATE_LIMIT_PAUSE", 0.0)
