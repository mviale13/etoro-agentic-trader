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

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app.domain.market_magnitude import MarketCapMagnitude

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
    # Added by CI1, and the two of them are the same omission twice:
    # this list is named per class, so a chain surface written after it
    # is unguarded until somebody remembers. `ArbitrumRpc` and
    # `SubtensorRpc` sit in the same module as the four above and were
    # never added, and `tests/test_hermetic_boundary.py` now enumerates
    # the module rather than trusting the memory.
    "app.providers.primary_sources.ArbitrumRpc",
    "app.providers.primary_sources.SubtensorRpc",
    # The S5.2 issuance reader, and the leak CI1 was opened for. It is
    # a whole provider rather than a chain adapter, which is why it was
    # missed: the crypto dossier constructed it inline, so eight tests
    # of a *payload's shape* asked mempool.space whether it was up.
    "app.providers.issuance_rule_provider.IssuanceRuleProvider",
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
    "app.providers.primary_sources.ArbitrumRpc": ("_post",),
    "app.providers.primary_sources.SubtensorRpc": ("_post",),
    # Two, because this one speaks both: a REST get for Bitcoin's tip
    # and blockchair's stats, a JSON-RPC post for Solana's inflation.
    # Naming only the first would have left Solana's schedule live.
    "app.providers.issuance_rule_provider.IssuanceRuleProvider": ("_get", "_rpc"),
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
def hermetic_route_acquisition():
    """Routes compose their evidence from stored doors, as a page must.

    The wire is already blocked below, so a route that reached for it
    would go red rather than slow — but red is the wrong answer when
    the thing under test is a payload's shape. This supplies the same
    reading the rest of the crypto dossier already uses: a stored door
    onto the temp evidence root, which holds nothing, so the route
    renders the honest absence its siblings render.

    Declared here rather than in three test files because the default
    belongs with the other hermetic defaults. A test that genuinely
    wants an acquiring provider overrides it back, visibly.
    """

    from app.api.dependencies import get_issuance_rule_provider
    from app.api.main import app
    from app.providers.cached_issuance_provider import CachedIssuanceRuleProvider

    # A nullary callable, deliberately: FastAPI inspects an override's
    # signature to build its dependency, and `stored` takes an optional
    # cache — which it tries to resolve as a request field and refuses.
    # The lambda also defers construction to request time, so the cache
    # is rooted at the temp evidence directory rather than at whatever
    # the root was when this fixture ran.
    app.dependency_overrides[get_issuance_rule_provider] = lambda: (
        CachedIssuanceRuleProvider.stored()
    )

    yield

    app.dependency_overrides.pop(get_issuance_rule_provider, None)


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


def admissible_market_cap(amount: float) -> MarketCapMagnitude:
    """A market capitalisation the size factor is allowed to compare.

    Most quality tests are about the band arithmetic — three factors
    make HIGH, two make MEDIUM — and not about whether a magnitude may
    be compared with a threshold at all. Since
    `market-cap-input-eligibility@1` refuses every live magnitude
    (nothing is VERIFIED and no denomination is established), those
    tests supply one that clears the gate, so they keep testing the
    ruler rather than the gate.

    Clearing the gate means clearing every term of its conjunction,
    identity included: this helper carries an undisputed (assumed)
    cross-provider identity, because eligibility is
    identity AND magnitude AND denomination AND comparison authority
    and a helper that skipped one term would be testing a gate that
    does not exist.

    A test that means to exercise the *gate* passes a bare
    `market_cap=` float instead, which is what every live security
    carries.
    """

    from app.domain.market_magnitude import MarketCapMagnitude
    from app.domain.provider_translation import TranslationWarrant

    return MarketCapMagnitude.measured(
        amount,
        warrant=TranslationWarrant.VERIFIED,
        currency="USD",
        currency_is_assumed=False,
        identity=assumed_identity(),
    )


def assumed_identity(symbol: str = "TEST"):
    """An undisputed cross-provider join, for tests about other terms.

    ASSUMED, not ESTABLISHED — the honest live state of every join on
    this platform (#134) — which the identity term of the eligibility
    conjunction passes. A test about the identity term itself builds
    its own UNRESOLVED specimen instead.
    """

    from app.domain.provider_identity import (
        CrossProviderIdentity,
        IdentityStanding,
        ProviderIdentityClaim,
    )

    return CrossProviderIdentity(
        symbol=symbol,
        claims=(ProviderIdentityClaim(provider="eToro", symbol=symbol),),
        standing=IdentityStanding.ASSUMED,
        because="test fixture: joined on symbol equality alone",
    )
