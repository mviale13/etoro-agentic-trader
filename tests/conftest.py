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
    "app.services.intelligence_synthesis_service",
    "app.services.value_capture_committee",
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
    "MOVRVEST_INTELLIGENCE_SYNTHESIS",
    "MOVRVEST_COMMITTEE_JUDGMENT",
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
NETWORK_SEAMS = (
    "app.providers.coingecko_market_provider.CoinGeckoMarketProvider",
    # The S4.5 primary surfaces. Keyless every one of them, which is
    # exactly why they need this: a credential guard would not have
    # stopped a single call.
    "app.providers.primary_sources.EthereumRpc",
    "app.providers.primary_sources.HyperliquidInfo",
    "app.providers.primary_sources.CardanoLedger",
    "app.providers.primary_sources.BitcoinExplorer",
)

#: What each seam's wire method is called. Named per seam because these
#: adapters speak different protocols — JSON-RPC posts, REST gets — and
#: a guard that assumed one name would silently protect nothing.
SEAM_METHODS = {
    "app.providers.coingecko_market_provider.CoinGeckoMarketProvider": ("_request",),
    "app.providers.primary_sources.EthereumRpc": ("_post",),
    "app.providers.primary_sources.HyperliquidInfo": ("_post",),
    "app.providers.primary_sources.CardanoLedger": ("_get",),
    "app.providers.primary_sources.BitcoinExplorer": ("_get",),
}


@pytest.fixture(autouse=True)
def hermetic_evidence_root(monkeypatch, tmp_path_factory):
    """No test may read — or write — the developer's own evidence.

    The third dimension of the same guarantee, and the one this file was
    missing. Credentials were silenced and the wire was blocked, and a
    test could still open `data/cache/protocol_facts` and answer from
    whatever the developer happened to have acquired.

    **That is not hypothetical and it is not rare: it happened five
    separate times across the crypto work.** Each occurrence looked like
    a test-writing mistake and was the same architectural one — an
    analytical service defaulting its evidence door to a path literal,
    so the call declared a *subject* and never an *evidence set*. The
    suite went green, `git archive HEAD` went red, and in one measured
    case a hand-edited cache flipped a committee verdict while the
    caller passed no evidence at all.

    Pointing the root at a fresh temporary directory makes the whole
    class impossible: a test that forgets to supply fixtures reads an
    empty store and says so, rather than reading a machine. A test that
    genuinely wants the acquired evidence sets the variable back
    itself — deliberately, and visibly in the test.

    The writing half matters too. Running the suite was observed
    creating `data/cache/fx` in the developer's own tree, so tests were
    mutating the state they were accidentally reading.
    """

    from app.infrastructure.evidence_root import ROOT_ENV

    monkeypatch.setenv(ROOT_ENV, str(tmp_path_factory.mktemp("evidence")))


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
        for method in SEAM_METHODS[seam]:
            monkeypatch.setattr(f"{seam}.{method}", _refuse)

        # A blocked call still paced itself first: the batch sleeps
        # between requests to stay under a rate limit, and eight of those
        # turned a four-second suite into ninety-six. Refusing the wire
        # and leaving the wait in place is a guard that works and costs
        # more than the calls it prevented.
        monkeypatch.setattr(f"{seam}.PACE", 0.0, raising=False)
        monkeypatch.setattr(f"{seam}.RATE_LIMIT_PAUSE", 0.0, raising=False)
