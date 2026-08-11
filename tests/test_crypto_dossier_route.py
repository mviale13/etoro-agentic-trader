"""The crypto dossier endpoint: a read, and one that changes with the asset.

**Nothing here reads the acquired stores.** `tests/conftest.py` points
the evidence root at a temp directory, so these run against an empty
store and measure the *route's* contract: what it composes, what it
refuses, and what it must never carry. The analytical content is each
layer's own suite.

The one test that is not a structural guard is
`test_the_dossier_changes_its_analytical_character`, and it is the
product property this slice exists to establish: five assets whose
dossiers differ only in numbers would be a product warning, not a
success.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.domain.crypto_archetype import ASSIGNMENTS
from tests.reachability import reachable

#: The owner's visual forcing set: a monetary network, a smart-contract
#: network, a multi-entity exchange network, an application protocol,
#: and one asset whose archetype was never established.
FORCING_SET = ("BTC", "ETH", "HYPE", "1INCH", "TAO")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _keys(node: object) -> set[str]:
    """Every key anywhere in a payload, however deeply nested."""

    if isinstance(node, dict):
        found = set(node)

        for value in node.values():
            found |= _keys(value)

        return found

    if isinstance(node, list):
        found: set[str] = set()

        for item in node:
            found |= _keys(item)

        return found

    return set()


def test_every_forcing_set_asset_is_served(client: TestClient) -> None:
    """All five compose against an empty store, with every section present.

    A section that raised on absent evidence would make the page
    unopenable on a fresh clone, which is the state the repository is
    committed in. Absence is a null section with a reason, never an
    exception.
    """

    for symbol in FORCING_SET:
        response = client.get(f"/crypto/{symbol}/dossier")

        assert response.status_code == 200, symbol

        body = response.json()

        for section in (
            "playbook",
            "assessment",
            "quality",
            "committees",
            "supply",
            "market",
            "facts",
            "intelligence",
            "journal",
            "issuance",
            "protocol",
        ):
            assert section in body, (symbol, section)


def test_a_security_this_platform_does_not_read_is_refused(
    client: TestClient,
) -> None:
    """404 rather than an empty dossier.

    Nine absent sections say *we looked and found nothing*. The truth
    for an unread security is that nobody looked, and the two are
    opposite claims about the same blank page.
    """

    response = client.get("/crypto/AAPL/dossier")

    assert response.status_code == 404
    assert "not a digital asset" in response.json()["detail"]


def test_the_dossier_changes_its_analytical_character(client: TestClient) -> None:
    """The product property, asserted rather than hoped for.

    Five dossiers identical except for their numbers would mean the
    surface had flattened the domain back into one shape.

    **Asserted on which questions, never on how many**, and the first
    run of this test is why: BTC and 1INCH are both asked 9 and refused
    10, and they are not remotely the same asset — BTC is asked about
    monetary scarcity and adoption, 1INCH about protocol capture and
    holder accrual. A surface that showed *"9 questions asked"* would
    make a monetary network and a fee-charging application look
    identical, which is the product warning this slice was told to
    watch for, arriving in a count.
    """

    asked: dict[str, frozenset[str]] = {}
    undetermined: dict[str, int] = {}
    refused: dict[str, int] = {}

    for symbol in FORCING_SET:
        questions = client.get(f"/crypto/{symbol}/dossier").json()["playbook"][
            "questions"
        ]

        asked[symbol] = frozenset(
            item["key"] for item in questions if item["applicability"] == "ask"
        )
        refused[symbol] = sum(
            1
            for item in questions
            if item["applicability"] == "not_applicable_for_archetype"
        )
        undetermined[symbol] = sum(
            1 for item in questions if item["applicability"] == "undetermined"
        )

    # Four established archetypes, four genuinely different question sets.
    established = [asked[symbol] for symbol in ("BTC", "ETH", "HYPE", "1INCH")]

    assert len(set(established)) == len(established), asked

    # The pair the count could not tell apart.
    assert len(asked["BTC"]) == len(asked["1INCH"])
    assert asked["BTC"] != asked["1INCH"]

    # And the unestablished one is a different *kind* of answer, not a
    # thinner version of the others: nothing is refused for it, because
    # not knowing what an asset is cannot be a form of knowing about it.
    assert refused["TAO"] == 0
    assert undetermined["TAO"] > len(asked["TAO"])

    for symbol in ("BTC", "ETH", "HYPE", "1INCH"):
        assert undetermined[symbol] == 0, symbol


def test_the_payload_carries_no_aggregate(client: TestClient) -> None:
    """No score, no agreement, no ranking — checked over the whole body.

    The refusals `/committees/{symbol}` states, held across nine more
    families. A crypto asset reads UNKNOWN on quality by design, and a
    surface that shipped a number beside that would be overturning S5
    in a formatter.

    Searched over the serialised payload rather than the response model,
    because the next aggregate would arrive as a key rather than a
    field.
    """

    for symbol in FORCING_SET:
        body = client.get(f"/crypto/{symbol}/dossier").json()

        keys = _keys(body)

        for forbidden in (
            "overall",
            "aggregate",
            "agreement",
            "conviction",
            "score",
            "rank",
            "weight",
            "recommendation",
        ):
            assert forbidden not in keys, (symbol, forbidden)


def test_unknown_is_never_served_as_a_zero(client: TestClient) -> None:
    """`UNKNOWN` is not a low band, and its reason always travels with it.

    A client that received a null band and no sentence would have to
    invent one, and the only sentence available to invent is the wrong
    one — that the asset was judged and judged poorly.
    """

    for symbol in FORCING_SET:
        quality = client.get(f"/crypto/{symbol}/dossier").json()["quality"]

        assert quality["quality"] == "UNKNOWN"
        assert quality["because"]
        assert quality["earned"] == 0

        # And every question says how it participated, in the domain's
        # own words — so "not applicable" can never render as a zero row
        # beside a scored one.
        for answer in quality["answers"]:
            assert answer["participation_stated"]


def test_serving_a_dossier_convenes_and_acquires_nothing() -> None:
    """Opening a page may not fetch, ask a model, or judge.

    The rule every knowledge surface here already lives by, restated for
    the one that reads nine layers at once — this is the surface with
    the most opportunities to break it.
    """

    code = reachable("app/api/routes/crypto_dossier.py")

    for forbidden in ("judge", "acquire", "observe", "draft", "fetch", "record"):
        assert forbidden not in code, forbidden


def test_the_corpus_is_served_from_the_assignments(client: TestClient) -> None:
    """A switcher a frontend cannot get out of step with.

    Kept on the server so an asset added to the corpus appears without
    a frontend change, and one removed disappears rather than 404ing
    from a menu that still lists it.
    """

    assets = client.get("/crypto/corpus").json()["assets"]

    assert {item["symbol"] for item in assets} == set(ASSIGNMENTS)
    assert set(FORCING_SET) <= {item["symbol"] for item in assets}

    unestablished = [item for item in assets if not item["established"]]

    assert [item["symbol"] for item in unestablished] == ["TAO"]


def test_the_assessment_travels_with_its_licensors(client: TestClient) -> None:
    """#119's guarantee survives the wire.

    Every reason a figure matters carries the question that owns it and
    the sentence licensing it for this asset — so the frontend has
    nothing to author, and the withheld case arrives as a sentence
    rather than as an empty field the client would have to explain.
    """

    body = client.get("/crypto/BTC/dossier").json()

    for statement in body["assessment"]["statements"]:
        for meaning in statement["why_it_matters"]:
            assert meaning["question"]
            assert meaning["stated"]
            assert meaning["licensed_by"]

        assert "why_it_matters" in statement
        assert "interpretation_withheld" in statement


def test_the_response_is_json_serialisable(client: TestClient) -> None:
    """Composed of plain data, so no section can smuggle a live object."""

    for symbol in FORCING_SET:
        json.dumps(client.get(f"/crypto/{symbol}/dossier").json())
