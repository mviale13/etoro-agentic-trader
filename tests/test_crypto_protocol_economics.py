"""What the systems behind a token earn, and what reaches the token.

The second half of the same boundary defect as the judged market facts.
`protocol` was served from the day the endpoint existed, parsed into a
view model whose entities carried **no facts field at all**, and then
referenced by no component — so an entity arrived named, with its
mapping basis, and completely silent about its economics. The general
dossier rendered all of it.

What the payload holds, and what an investor could not see: Hyperliquid
earns **$842.7k** of fees over the observed day and **$534.9k** of that
is reported as reaching holders — the two magnitudes behind the one
committee verdict on this platform that says a mechanism is evidenced.

These run over the committed claim-set builders rather than the acquired
cache: `data/cache/` is gitignored, and a test that reads it passes on
the developer's machine and fails under `git archive HEAD`. What is
pinned here is the wire contract the page composes from. The
architectural half — that no served section can silently stop reaching
the page again — is `test_crypto_dossier_reaches_the_page.py`.
"""

from __future__ import annotations

import inspect
from typing import Any

from app.api.models import protocol_adapter
from app.api.models.protocol_adapter import protocol_fundamentals_response
from app.domain.asset_class import AssetClass
from tests.test_protocol_fundamentals import BITCOIN, HYPE_CHAIN, HYPE_PROTOCOL, service

#: The two quantities the Value Capture question itself names — what
#: users pay, and what reaches holders.
QUESTIONED = ("fees", "holder_revenue")


def served(asset: str, *claims: Any) -> dict[str, Any]:
    """The protocol payload as the crypto route composes it."""

    outcome = service(*claims).established(asset, AssetClass.CRYPTO)

    assert outcome is not None, asset

    response = protocol_fundamentals_response(outcome)

    assert response is not None, asset

    return response.model_dump()


def facts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [fact for entity in payload["entities"] for fact in entity["facts"]]


# ── the economics travel, per entity ────────────────────────────────


def test_an_entity_carries_its_economics_and_not_only_its_name() -> None:
    """The defect, stated as a contract.

    An entity arrived named, with its mapping basis, and silent. The
    payload has always held the figures; nothing consumed them.
    """

    payload = served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN)

    assert payload["entities"]
    assert facts(payload), "entities with no economics is the defect itself"


def test_hype_keeps_the_venue_and_the_chain_apart() -> None:
    """The entity trap, held open.

    Two DefiLlama entities once shared the name *Hyperliquid* and were
    224× apart. The venue and the layer-1 it settles on are two economic
    systems, and each carries its own figures: the exchange earns three
    orders of magnitude more than its chain.
    """

    payload = served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN)

    assert len(payload["entities"]) == 2

    by_key = {entity["key"]: entity for entity in payload["entities"]}

    assert set(by_key) == {"hyperliquid-protocol", "hyperliquid-l1-chain"}

    venue = next(
        fact
        for fact in by_key["hyperliquid-protocol"]["facts"]
        if fact["metric"] == "fees"
    )
    chain = next(
        fact
        for fact in by_key["hyperliquid-l1-chain"]["facts"]
        if fact["metric"] == "fees"
    )

    assert venue["stated"] != chain["stated"]

    for entity in payload["entities"]:
        assert entity["measures"], entity["key"]
        assert entity["mapping_basis"], (
            "a shared name establishes nothing; the reason the entity's "
            "economics belong to this token must travel with it"
        )


def test_the_mapping_basis_names_the_source_of_the_link() -> None:
    """HYPE's is the strongest case, and it is the provider's sentence."""

    venue = next(
        entity
        for entity in served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN)["entities"]
        if entity["key"] == "hyperliquid-protocol"
    )

    assert "names HYPE" in venue["mapping_basis"]
    assert "not inferred from the shared name" in venue["mapping_basis"]


# ── each figure keeps what makes it checkable ───────────────────────


def test_a_served_figure_carries_its_window_source_freshness_and_standing() -> None:
    """A magnitude without its window is not a magnitude.

    $842.7k means nothing until it says *over 24 hours*, and it means
    less until it says who reported it and when.
    """

    for payload in (
        served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN),
        served("BTC", BITCOIN),
    ):
        for fact in facts(payload):
            assert fact["label"], fact["metric"]
            assert fact["family"] in {
                "capital",
                "activity",
                "value_generation",
                "holder_accrual",
            }, fact["family"]
            assert fact["availability_stated"], fact["metric"]

            if fact["stated"] is None:
                continue

            assert fact["standing_stated"], fact["metric"]
            assert fact["source"], fact["metric"]
            assert fact["age"], fact["metric"]


def test_a_flow_states_the_window_it_was_measured_over() -> None:
    """A level and a flow are different claims, and only one has a window."""

    for fact in facts(served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN)):
        if fact["stated"] and fact["family"] in {
            "value_generation",
            "holder_accrual",
        }:
            assert fact["window"], fact["metric"]


def test_the_provider_methodology_travels_where_it_is_supplied() -> None:
    """The mechanism itself, in the provider's own words.

    "99% of fees go to Assistance Fund for buying HYPE tokens" is what
    turns a number into an argument, and it is the provider's sentence
    rather than this platform's.
    """

    holder = [
        fact
        for fact in facts(served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN))
        if fact["metric"] == "holder_revenue" and fact["stated"]
    ]

    assert holder
    assert any(fact["provider_methodology"] for fact in holder)


def test_the_kinds_of_silence_stay_distinct() -> None:
    """*Not applicable* and a served figure are different facts, and a
    figure is served only where the reading is available.

    A question that does not apply to this kind of system is not a gap.
    Bitcoin's holder revenue is not missing — the provider defines no
    such mechanism for it, which under S2's sibling rule is evidence
    that none exists.
    """

    payload = served("BTC", BITCOIN)

    availabilities = {fact["availability"] for fact in facts(payload)}

    assert "available" in availabilities
    assert len(availabilities) > 1, "one word for every silence would hide the kinds"

    for fact in facts(payload):
        assert fact["availability_stated"], fact["metric"]

        if fact["availability"] != "available":
            assert fact["stated"] is None, fact["metric"]


# ── magnitude for a judgment, and only a real one ───────────────────


def test_the_questioned_quantities_are_held_for_an_answered_committee() -> None:
    """The composition the slice exists for.

    Where Value Capture answered, the two quantities its own question
    names — what users pay, and what reaches holders — are served for
    every mapped entity, so the verdict can be read beside what it was
    reached on.
    """

    payload = served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN)

    by_entity = {
        entity["key"]: {
            fact["metric"]: fact["stated"]
            for fact in entity["facts"]
            if fact["metric"] in QUESTIONED and fact["stated"]
        }
        for entity in payload["entities"]
    }

    # The venue answers both halves of the question: what users pay it,
    # and what reaches holders.
    assert set(by_entity["hyperliquid-protocol"]) == set(QUESTIONED)

    # And the chain contributes its own, so the two systems are never
    # read as one — whichever of the two quantities it publishes.
    assert by_entity["hyperliquid-l1-chain"]


def test_bitcoins_fee_figure_exists_and_belongs_to_no_verdict() -> None:
    """The rule that keeps a refusal a refusal.

    Bitcoin's fee figure is real, and its Value Capture Committee
    declines the question as the wrong instrument for a monetary asset.
    The page shows the magnitudes only where the posture is `answered`;
    what this pins is the half that makes the rule bite — a figure was
    available to misuse, and no holder-revenue figure exists to pair
    with it.
    """

    payload = served("BTC", BITCOIN)

    fees = next(fact for fact in facts(payload) if fact["metric"] == "fees")

    assert fees["stated"], "the figure exists — that is what makes the rule bite"

    holder = next(fact for fact in facts(payload) if fact["metric"] == "holder_revenue")

    assert holder["stated"] is None


# ── boundaries ──────────────────────────────────────────────────────


def test_the_adapter_forms_no_ratio_and_no_annualisation() -> None:
    """No fee yield, no multiple, no per-market-cap figure.

    HYPE is the case that makes this concrete: its market value is
    reported 50% apart by two credible sources, so a fees-over-market-cap
    figure would invent both a numerator convention and a denominator.
    """

    source = inspect.getsource(protocol_adapter)

    for banned in ("market_cap", "annualis", "annualiz", "yield", "multiple"):
        assert banned not in source, banned


def test_no_figure_crosses_the_wire_as_a_number() -> None:
    """The structural half of the same guarantee.

    Every protocol figure is served as the backend's own worded value.
    There is no number on the wire for a surface to divide by another,
    which is what makes "no valuation multiple" a property of the
    contract rather than a promise about the page.
    """

    for fact in facts(served("HYPE", HYPE_PROTOCOL, HYPE_CHAIN)):
        assert fact["stated"] is None or isinstance(fact["stated"], str)
        assert not isinstance(fact["stated"], (int, float))
