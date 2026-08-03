"""One door to the eToro API, and what it records on the way through."""

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.brokers.etoro_client import EtoroClient, RateBudget
from app.config import Settings
from app.infrastructure.evidence import VersionedSnapshotStore

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)

PUBLISHED = {
    "ratelimit-limit": "60",
    "ratelimit-policy": "60;w=60",
    "ratelimit-remaining": "57",
    "ratelimit-reset": "43",
}


def settings() -> Settings:
    return Settings(
        etoro_api_key="test-api-key",
        etoro_user_key="test-user-key",
        trading_mode="demo",
    )


def client(tmp_path, handler) -> EtoroClient:
    return EtoroClient(
        settings(),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        evidence_store=VersionedSnapshotStore(root=tmp_path),
    )


def responder(status: int = 200, headers: dict[str, str] | None = None):
    def handle(request: httpx.Request) -> httpx.Response:
        handle.seen.append(request)  # type: ignore[attr-defined]

        return httpx.Response(
            status,
            json={"ok": True},
            headers=headers if headers is not None else PUBLISHED,
        )

    handle.seen = []  # type: ignore[attr-defined]

    return handle


def test_the_allowance_is_read_from_the_response_not_assumed() -> None:
    """
    eToro publishes 60/minute for reads and 20/minute for writes.

    Reading it off each response means the client is right about whichever
    tier it is actually being charged against, without the number being
    written down anywhere and going stale.
    """

    budget = RateBudget()
    budget.observe(PUBLISHED, now=NOW)

    assert budget.limit == 60
    assert budget.remaining == 57
    assert budget.resets_at == NOW + timedelta(seconds=43)


def test_an_unpublished_allowance_is_never_invented() -> None:
    """A limit nobody stated is not a limit to throttle against."""

    budget = RateBudget()
    budget.observe({}, now=NOW)

    assert budget.remaining is None
    assert budget.pause_needed(now=NOW) == 0.0


def test_a_spent_allowance_waits_for_the_window_to_turn_over() -> None:
    budget = RateBudget()
    budget.observe({**PUBLISHED, "ratelimit-remaining": "0"}, now=NOW)

    assert budget.pause_needed(now=NOW) == pytest.approx(43.0)
    assert budget.pause_needed(now=NOW + timedelta(seconds=43)) == 0.0


def test_every_response_is_archived_with_what_was_asked(tmp_path) -> None:
    handler = responder()

    asyncio.run(
        client(tmp_path, handler).get(
            "/api/v1/watchlists",
            endpoint="watchlists",
            params={"page": 2},
        )
    )

    saved = list(tmp_path.rglob("*.json"))

    assert len(saved) == 1
    assert "watchlists" in str(saved[0])

    import json

    document = json.loads(saved[0].read_text())

    assert document["payload"] == {"ok": True}
    # Named in the API inventory and previously unrecorded. A paginated
    # capture that does not say which page it holds is a corrupted archive.
    assert document["metadata"]["query_parameters"] == {"page": 2}
    assert document["metadata"]["request_path"] == "/api/v1/watchlists"
    assert document["metadata"]["response_headers"]["ratelimit-remaining"] == "57"


def test_a_refusal_is_evidence_too(tmp_path) -> None:
    """
    A 429 is the most useful reply the platform can get about its own
    budget. Discarding it would leave the question unanswerable afterwards.
    """

    api = client(tmp_path, responder(status=429))

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(api.get("/api/v1/watchlists", endpoint="watchlists"))

    saved = list(tmp_path.rglob("*.json"))

    assert len(saved) == 1

    import json

    assert json.loads(saved[0].read_text())["metadata"]["http_status"] == 429


def test_the_credentials_are_sent_and_each_call_is_identifiable(tmp_path) -> None:
    handler = responder()

    asyncio.run(client(tmp_path, handler).get("/api/v1/watchlists", endpoint="w"))

    request = handler.seen[0]  # type: ignore[attr-defined]

    assert request.headers["x-api-key"] == "test-api-key"
    assert request.headers["x-user-key"] == "test-user-key"
    assert request.headers["x-request-id"]
