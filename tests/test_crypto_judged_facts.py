"""The token's judged market facts reach the surface built for tokens.

The defect this closes: `/crypto/{symbol}/dossier` has served a top-level
`facts` payload since the endpoint existed — thirteen judged rows and the
rejection ledger — and the crypto page's parser had no key for it. The
*general* dossier rendered the same evidence as `asset_profile`, so the
asset-class surface was the one hiding it. On HYPE that meant a market
value two sources put 50% apart, a circulating supply three sources put
4.5× apart, and a provider claim wrong by a factor of 1.5 million, none
of it visible on the token's own page.

These prove the wire contract the parser now consumes. The parser and the
section are TypeScript, and this repository has no JavaScript test
runner — adding one is a slice of its own — so their proof is
`npm run build` (which typechecks) plus the rendered page, and what is
pinned here is that the payload carries every state, unmutated, and that
an unjudged committee is serialisable beside it.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.api.models.asset_profile_adapter import asset_profile_response
from app.domain.token_fact_validation import judge
from app.domain.token_facts import TokenFactStanding
from tests.test_token_fact_validation import coingecko, tokeninsight, yahoo


def hype_profile() -> Any:
    """HYPE as the three sources actually reported it.

    The builders are the S1 acceptance case's own, committed with it:
    two internally coherent vendors 33–51% apart on what counts as
    circulating, and Yahoo's defective row on the way.
    """

    served = asset_profile_response(
        judge("HYPE", [tokeninsight(), coingecko(), yahoo()])
    )

    assert served is not None

    return served


def rows(profile: Any) -> list[Any]:
    return [row for group in profile.groups for row in group.rows]


def row_named(profile: Any, label: str) -> Any:
    found = next((row for row in rows(profile) if row.label == label), None)

    assert found is not None, label

    return found


# ── the HYPE regression: the conflict and the refusal ───────────────


def test_hype_shows_the_conflict_rather_than_a_value() -> None:
    """The acceptance case. Two credible sources, 50% apart, no number.

    The gate serves no market value at all here, and the reason it serves
    none is the finding. A surface that printed either vendor's figure —
    or worse, something between them — would be inventing a number nobody
    published.
    """

    market_value = row_named(hype_profile(), "Market value")

    assert market_value.standing == TokenFactStanding.CONFLICTED.value
    assert market_value.stated is None

    assert "sources disagree" in market_value.because
    assert "TokenInsight" in market_value.because
    assert "CoinGecko" in market_value.because

    # Both vendors' figures — the committed builders' own — appear only
    # inside the explanation of the disagreement, never as the row's
    # value.
    assert "18.3bn" in market_value.because
    assert "12.2bn" in market_value.because


def test_hype_keeps_the_refused_yahoo_claim_out_of_the_figures() -> None:
    """A rejected claim is evidence about a source, not a candidate value."""

    profile = hype_profile()

    refused = " ".join(item.statement for item in profile.rejected)

    assert "Yahoo Finance" in refused
    assert "8,105" in refused
    assert "was not accepted" in refused

    # And it is nowhere among the served figures.
    for row in rows(profile):
        assert "8,105" != (row.stated or "")
        assert row.source != "Yahoo Finance"


def test_the_rejection_ledger_is_structurally_apart_from_the_rows() -> None:
    """Two different kinds of thing, and the payload keeps them apart.

    A refused claim has no label, no standing, no source and no age — it
    is a sentence about why a provider was not believed. Nothing about
    the shape invites a surface to render it as a row.
    """

    profile = hype_profile()

    assert profile.rejected
    assert all(set(vars(item)) == {"statement"} for item in profile.rejected), (
        "a rejected claim carries only its sentence"
    )


# ── every state survives, unmutated ─────────────────────────────────


def test_each_standing_travels_with_its_own_sentence() -> None:
    """Whatever the gate judged is what the payload carries.

    The states are not ordered and none is a score: `claimed` is not a
    lesser `established`, and `absent` is not a zero. Each simply carries
    its own word and its own reason.
    """

    profile = hype_profile()

    served = {row.standing for row in rows(profile)}

    assert TokenFactStanding.CONFLICTED.value in served
    assert TokenFactStanding.CLAIMED.value in served
    assert TokenFactStanding.ESTABLISHED.value in served

    for row in rows(profile):
        assert row.standing_stated, row.label
        assert row.because, row.label

        # A value is served only where the gate served one; every other
        # state renders its reason instead of a number.
        if row.standing == TokenFactStanding.ABSENT.value:
            assert row.stated is None, row.label


def test_a_figure_is_never_recomposed_on_the_way_to_the_wire() -> None:
    """The adapter formats and groups; it judges nothing.

    Established rows keep their source and their age, so a reader can
    check the platform against the provider it names.
    """

    established = [
        row
        for row in rows(hype_profile())
        if row.standing == TokenFactStanding.ESTABLISHED.value
    ]

    assert established

    for row in established:
        assert row.stated
        assert row.source
        assert row.age


# ── the same evidence, on both surfaces ─────────────────────────────


@pytest.fixture
def client() -> TestClient:
    from app.api.main import app

    return TestClient(app)


def test_the_crypto_route_declares_the_facts_key(client: TestClient) -> None:
    """Under the hermetic root nothing has been acquired, so the honest
    answer is null — and the key is still declared, because a surface
    must be able to tell "no facts held" from "this backend predates the
    field"."""

    body = client.get("/crypto/BTC/dossier").json()

    assert "facts" in body


def test_both_routes_compose_the_same_adapter() -> None:
    """The defect, stated as a contract.

    Both routes serve `asset_profile_response` over the same stores — the
    crypto endpoint was never the problem, the parser was. Asserted over
    the route modules' own source rather than by calling them, because
    the general dossier reaches a broker and this must hold in an
    environment that has none.
    """

    from pathlib import Path

    routes = Path(__file__).resolve().parent.parent / "app" / "api" / "routes"

    for module in ("crypto_dossier.py", "executive.py"):
        source = (routes / module).read_text(encoding="utf-8")

        assert "asset_profile_response" in source, module


# ── the unjudged committee: no crash, and no invented verdict ───────


def test_an_unjudged_committee_serialises_without_a_verdict() -> None:
    """The latent crash, held shut at the wire.

    `UnjudgedCommittee` is deliberately its own type: *this committee has
    never run here* and *this committee ran and could not answer* are
    different facts. Its payload therefore carries no posture, no
    applicability and no evidence count — and the crypto parser required
    all three, so one unjudged committee threw and the whole page fell
    back to "Nothing is held for this asset".

    The guard is on the parser, which now reads them as absent. Nothing
    in the domain changed: what it says is already right.
    """

    from app.domain.committee_matrix import CommitteeIdentity, UnjudgedCommittee

    cell = UnjudgedCommittee(
        asset="DOGE",
        committee=CommitteeIdentity(
            key="value_capture",
            name="Value Capture Committee",
            version=1,
            fingerprint="abc123",
        ),
        question="Does this network generate evidenced fee activity?",
    ).as_dict()

    # The fields the parser must tolerate as absent.
    assert cell["posture"] is None
    assert "posture_stated" not in cell
    assert "applicability" not in cell
    assert "evidence_count" not in cell

    # And the sentence it renders instead — the domain's own, and not a
    # verdict of any kind.
    assert cell["answered"] is False
    assert cell["judgments_recorded"] == 0
    assert "recorded no judgment" in cell["stated"]

    verdicts = ("mechanism_evidenced", "no_mechanism_evidenced", "consensus_bound")

    assert not any(word in cell["stated"] for word in verdicts)


def test_every_committee_is_unjudged_on_an_empty_store() -> None:
    """How reachable the crash actually was.

    `data/judgments/` is gitignored — the records are a runtime artifact
    — so on a fresh clone *every* registered committee is unjudged for
    *every* asset. The old parser required four fields an unjudged cell
    does not send, threw on the first one, and the whole crypto dossier
    fell back to "Nothing is held for this asset". Not a ninth-asset
    hypothetical: the default state of a new checkout.
    """

    from app.services.committee_matrix_service import CommitteeMatrixService

    served = CommitteeMatrixService().for_asset("BTC").as_dict()

    cells = cast(list[dict[str, Any]], served["committees"])

    assert cells

    for cell in cells:
        assert cell["posture"] is None
        assert "posture_stated" not in cell

        # What the surface renders instead — and it is not a verdict.
        assert "recorded no judgment" in cell["stated"]


def test_a_judged_committee_still_sends_every_field_it_did() -> None:
    """The guard relaxes what the parser *requires*, never what a judged
    committee *sends*. Its presentation is untouched."""

    from app.domain.committee_matrix import CommitteeAssessment

    sent = set(CommitteeAssessment.__dataclass_fields__)

    for field in (
        "posture",
        "applicability",
        "evidence_count",
        "judgments_recorded",
        "verdict",
        "confidence",
        "refs",
    ):
        assert field in sent, field


def test_a_receipt_clock_reaches_the_wire_saying_so() -> None:
    """The qualifier must survive the adapter, not just the gate.

    This is where it was found to be lost. `_age` rebuilt a
    `Provenance` from a fact's source and moment alone, and the third
    field defaulted back to True — so a row whose clock is MOVRvest's
    receipt clock rendered *"TokenInsight, 28 minutes ago"*, which is
    the original defect restored one layer further out.

    The gate can only carry a fact honestly; every surface that unpacks
    one has to keep it that way.
    """

    from datetime import UTC, datetime

    from app.domain.provenance import Provenance

    received = datetime(2026, 8, 21, 6, 59, 42, tzinfo=UTC)

    outcome = judge(
        "HYPE",
        [
            tokeninsight(
                read=Provenance(
                    source="TokenInsight",
                    observed_at=received,
                    observation_stated=False,
                )
            )
        ],
    )

    profile = asset_profile_response(outcome)

    assert profile is not None

    aged = [
        row
        for group in profile.groups
        for row in group.rows
        if row.age is not None and row.source == "TokenInsight"
    ]

    assert aged, "no TokenInsight row carried an age at all"

    for row in aged:
        assert "received" in row.age, row.label
