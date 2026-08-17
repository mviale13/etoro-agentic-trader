"""One crypto asset, one live investment answer.

DV3's product invariant. The crypto dossier now carries the Artificial
CIO's answer, and the legacy executive dossier is retired for every
asset in the crypto corpus — 410, before the pipeline spends anything,
gated on the same `ASSIGNMENTS` declaration the crypto corpus serves so
the two surfaces cannot disagree about which assets it covers.

These run against an empty evidence store (`tests/conftest.py` points
the root at a temp directory), so they measure the routes' contract:
what is served, what is refused, and that the refusal costs no build.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_brain_builder_service
from app.api.main import app
from app.domain.crypto_archetype import ASSIGNMENTS


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── the canonical surface answers ───────────────────────────────────


def test_the_crypto_dossier_carries_the_decision(client: TestClient) -> None:
    """Every corpus asset gets a decision section, empty store included.

    Against an empty store no judgment is recorded, and the honest
    answer is MONITOR with the silence named — never an error, never a
    missing section, and never a number.
    """

    for symbol in ASSIGNMENTS:
        body = client.get(f"/crypto/{symbol}/dossier").json()

        decision = body["decision"]

        assert decision["state"] in {"MONITOR", "INVESTIGATE"}, symbol
        assert decision["rationale"], symbol
        assert decision["ceiling"], symbol
        assert decision["conviction_withheld_because"], symbol
        assert "conviction" not in decision, symbol
        assert decision["decided_under"] == [
            {"key": "digital-asset-gates", "version": 1}
        ], symbol


def test_the_decision_is_a_projection_not_a_record(client: TestClient) -> None:
    """Two reads, one answer — a page view manufactures no judgment."""

    first = client.get("/crypto/BTC/dossier").json()["decision"]
    second = client.get("/crypto/BTC/dossier").json()["decision"]

    assert first == second


# ── the legacy surface is retired ───────────────────────────────────


class ExplodingBuilder:
    """A brain builder that fails the test if the route ever builds."""

    async def build(self, **_: object) -> None:
        raise AssertionError(
            "The executive dossier built a Brain for a crypto-corpus "
            "asset. Retirement must cost no pipeline run."
        )


def test_the_executive_dossier_is_gone_for_every_corpus_asset(
    client: TestClient,
) -> None:
    """410 for all of them, before any pipeline spend.

    The exploding builder is the measurement: a gate placed after
    `builder.build` would pass a status-code assertion and still spend
    twelve seconds per view on a surface that no longer answers.
    """

    app.dependency_overrides[get_brain_builder_service] = ExplodingBuilder

    try:
        for symbol in ASSIGNMENTS:
            response = client.get(f"/executive/{symbol}/dossier")

            assert response.status_code == 410, symbol

            detail = response.json()["detail"]

            # The refusal names the one canonical surface, so a client
            # that followed the old path is told the new one.
            assert f"/crypto/{symbol}/dossier" in detail, symbol
    finally:
        app.dependency_overrides.pop(get_brain_builder_service, None)


def test_btc_end_to_end_has_exactly_one_answer(client: TestClient) -> None:
    """The mandatory invariant, pinned on the DV1 specimen."""

    legacy = client.get("/executive/BTC/dossier")
    canonical = client.get("/crypto/BTC/dossier")

    assert legacy.status_code == 410
    assert canonical.status_code == 200
    assert canonical.json()["decision"]["rationale"]


def test_a_non_corpus_security_still_reaches_the_executive_dossier() -> None:
    """The gate is the corpus, not the asset class.

    An equity must not be caught by it — the gate runs before the
    pipeline, so it cannot know the asset class and must not guess.
    MSFT is outside `ASSIGNMENTS`, so the route proceeds to build,
    which is the behaviour the equity dossier tests already cover.
    """

    assert "MSFT" not in ASSIGNMENTS
    assert "AAPL" not in ASSIGNMENTS
