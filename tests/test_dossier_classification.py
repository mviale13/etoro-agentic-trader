"""Industry and the earned playbook reach the dossier apart, and honestly.

EF1, the visibility half of the convergence ruling: the investor sees
where the market files a company (the provider's industry — context)
beside the investment playbook this platform actually established from
the company's own filing — without either substituting for the other,
and without an absence ever dressed as a classification.

Three rules pinned here:

- **Both coexist and neither overwrites the other.** "Semiconductors"
  beside "Industrial" is two answers to two questions, and an apparent
  mismatch is information rather than a defect.
- **Absence is not a classification.** The earned playbook has three
  states — established, refused, unavailable — each carrying the owning
  layer's own sentence, and no state ever serves "General Corporate".
- **Visibility is not routing.** The classification available to the
  dossier cannot move the executive decision: the decision fields are
  identical whatever the grounded route concluded, proven at the wire.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from fastapi.testclient import TestClient

from app.api.dependencies import get_brain_builder_service
from app.api.main import app
from app.api.routes.executive import (
    _classification,
    _earned_playbook,
    _industry_context,
)
from app.domain.asset_class import AssetClass
from app.domain.business_understanding import BusinessUnderstanding
from app.domain.dossier_definition import definition_for
from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot
from app.services.company_understanding_service import (
    CompanyUnderstanding,
    CompanyUnderstandingService,
)
from app.services.understanding_engine import understand
from tests.test_api_routes import StubBrainBuilder, make_brain
from tests.test_playbook_mapping import (
    bank_shape,
    consensus,
    diversified_shape,
    manufacturer_shape,
    segment,
    unexplained_shape,
)

EQUITY = definition_for(AssetClass.STOCK)


def snapshot_with(
    industry: str | None,
    sector: str | None,
    read: bool = True,
) -> ValuationSnapshot:
    """A stored provider profile, or the never-acquired absence."""

    return ValuationSnapshot(
        forward_pe=24.0 if read else None,
        trailing_pe=None,
        peg_ratio=None,
        dividend_yield=None,
        industry=industry,
        sector=sector,
        reading=(
            Provenance(
                source="Yahoo Finance",
                observed_at=datetime(2026, 8, 9, 8, 24, tzinfo=UTC),
            )
            if read
            else None
        ),
    )


def understood(business: BusinessUnderstanding) -> CompanyUnderstanding:
    """An understanding whose business half is present."""

    return CompanyUnderstanding(
        symbol=business.symbol,
        business=business,
        business_absent_because=None,
        financial=None,
        financial_absent_because="No financial statement has been read.",
    )


def not_understood(because: str) -> CompanyUnderstanding:
    """The store door's absence, carried with its reason."""

    return CompanyUnderstanding(
        symbol="ANY",
        business=None,
        business_absent_because=because,
        financial=None,
        financial_absent_because="No financial statement has been read.",
    )


# ── the acceptance corpus: both concepts, apart ─────────────────────


def test_industry_and_earned_playbook_coexist_without_overwriting() -> None:
    """NVDA's acceptance: Semiconductors beside Industrial, both true.

    The industry route's playbook for NVDA is "Semiconductor"; the
    grounded route's is Industrial. Before EF1 the dossier showed only
    the first, presented as the classification. Now the provider's own
    industry string and the earned playbook each render in their own
    half, with their own provenance.
    """

    industry = _industry_context(snapshot_with("Semiconductors", "Technology"))
    playbook = _earned_playbook(understood(understand(manufacturer_shape())))

    assert industry.label == "Semiconductors"
    assert industry.industry == "Semiconductors"
    assert industry.sector == "Technology"
    assert industry.read is not None
    assert industry.read.source == "Yahoo Finance"
    assert "where it operates" in industry.stated
    assert "not a conclusion from its filing" in industry.stated

    assert playbook.state == "established"
    assert playbook.playbook == "Industrial"
    assert playbook.label == "Industrial"
    assert playbook.stated.startswith("Manufacturer")

    # Neither half mentions the other's answer: no substitution.
    assert "Industrial" not in industry.stated
    assert "Semiconductor" not in playbook.stated


def test_a_diversified_conclusion_renders_beside_its_industry() -> None:
    """DIS's acceptance shape: provider industry kept, Diversified earned."""

    industry = _industry_context(
        snapshot_with("Entertainment", "Communication Services")
    )
    playbook = _earned_playbook(understood(understand(diversified_shape())))

    assert industry.label == "Entertainment"
    assert playbook.state == "established"
    assert playbook.playbook == "Diversified Business"


def test_a_bank_reads_bank_while_the_provider_reports_no_industry() -> None:
    """BNP.PA's acceptance: the two absences and the conclusion held apart.

    The provider profile was read and names no industry — the provider's
    own answer, dated. The filing concluded a bank. Before EF1 this
    security rendered "Not classified" under a sentence asserting the
    grounded route established nothing.
    """

    industry = _industry_context(snapshot_with(None, None))
    playbook = _earned_playbook(understood(understand(bank_shape())))

    assert industry.label == "None reported"
    assert industry.industry is None
    assert industry.read is not None
    assert industry.stated == (
        "The data provider reports no industry for this security."
    )

    assert playbook.state == "established"
    assert playbook.playbook == "Bank"
    assert "balance sheet that is the business" in playbook.stated


def test_a_refused_grounding_is_a_refusal_and_never_a_default() -> None:
    """VOW3.DE's acceptance: no archetype is manufactured to fill the field.

    The grounded route's own refusal travels verbatim, and the playbook
    field carries no name at all — not Industrial, not Automotive, not
    General Corporate.
    """

    playbook = _earned_playbook(understood(understand(unexplained_shape())))

    assert playbook.state == "refused"
    assert playbook.playbook is None
    assert playbook.label == "Not established"

    # The engine's own sentence, not a rewording of it.
    business = understand(unexplained_shape())
    assert playbook.stated == business.characteristics.undecided_because


def test_below_quorum_is_refused_with_the_count_stated() -> None:
    """Three readings are not a consensus, and the sentence says so."""

    same = (segment("Only", share=0.95),)

    playbook = _earned_playbook(understood(understand(consensus(same, same, same))))

    assert playbook.state == "refused"
    assert playbook.playbook is None
    assert "3 observations" in playbook.stated
    assert "below the quorum of 5" in playbook.stated


def test_knowledge_unavailable_carries_the_store_doors_own_sentence() -> None:
    """A filing not held under the current reading contract says so.

    BNP.PA, DIS, NVDA and CAT hold observations from an older reading
    contract, which the store deliberately restores as absent. The
    dossier carries that absence in the store's own words rather than
    resurrecting archived knowledge through a side door.
    """

    absent = (
        "No filing has been read for BNP.PA. Reading one is an explicit "
        "spend, and no surface takes it — `movrvest observe` does."
    )

    playbook = _earned_playbook(not_understood(absent))

    assert playbook.state == "unavailable"
    assert playbook.playbook is None
    assert playbook.label == "Not established"
    assert playbook.stated == absent


def test_an_unacquired_profile_is_a_different_absence_from_none_reported() -> None:
    """Never read and read-but-empty must not share a sentence."""

    unread = _industry_context(snapshot_with(None, None, read=False))
    empty = _industry_context(snapshot_with(None, None))

    assert unread.label == "Not acquired"
    assert unread.read is None
    assert "No provider profile has been acquired" in unread.stated

    assert empty.label == "None reported"
    assert empty.read is not None

    assert unread.stated != empty.stated


def test_no_state_ever_serves_general_corporate_as_a_classification() -> None:
    """Absence is not a classification, and the fake fallback is gone."""

    states = [
        _earned_playbook(understood(understand(manufacturer_shape()))),
        _earned_playbook(understood(understand(diversified_shape()))),
        _earned_playbook(understood(understand(bank_shape()))),
        _earned_playbook(understood(understand(unexplained_shape()))),
        _earned_playbook(not_understood("No filing has been read.")),
        _earned_playbook(None),
    ]

    for state in states:
        assert state.playbook != "General Corporate"
        assert state.label != "General Corporate"
        assert "General Corporate" not in state.stated


def test_classification_is_not_composed_for_a_subject_without_filings() -> None:
    """A token and a fund are not companies wearing a missing label."""

    for asset_class in (AssetClass.CRYPTO, AssetClass.ETF, AssetClass.COMMODITY):
        definition = definition_for(asset_class)

        assert _classification("BTC", definition, None) is None, asset_class


# ── visibility is not routing: the wire-level proof ─────────────────


def dossier_body(client: TestClient, symbol: str) -> dict[str, object]:
    response = client.get(f"/executive/{symbol}/dossier")

    assert response.status_code == 200

    return cast(dict[str, object], response.json())


#: Everything the executive decision consists of at the wire. The
#: comparison deliberately excludes what is not the decision: the
#: classification and understanding sections themselves (the thing
#: changing), the synthesis (which explains the case beside whatever
#: understanding exists), and decided_at/trend/conviction_change (the
#: journal remembers each request, so a second call has one more review
#: behind it whatever the classification says).
DECISION_FIELDS = (
    "decision_state",
    "conviction",
    "conviction_label",
    "committee_agreement",
    "rationale",
    "action",
    "playbook",
    "summary",
    "expected_holding_period",
    "catalysts",
    "invalidation_conditions",
    "next_trigger",
    "security_evidenced",
    "evidence_weighed",
    "strengths",
    "risks",
    "missing_evidence",
    "scores",
    "context_strengths",
    "context_risks",
    "committees",
)


def test_the_classification_available_to_the_dossier_cannot_move_the_decision(
    monkeypatch,
) -> None:
    """EF1's architectural boundary, proven behaviourally at the route.

    Two dossiers over the identical brain — one where the grounded route
    holds nothing, one where it authoritatively establishes Bank. Every
    decision field is byte-identical; only the classification (and the
    sections that display understanding) may differ. The displayed
    archetype reroutes no analyst, no score, no committee and no
    conviction.
    """

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    try:
        with TestClient(app) as client:
            monkeypatch.setattr(
                CompanyUnderstandingService,
                "understanding",
                lambda self, symbol: not_understood(
                    "No filing has been read for MSFT."
                ),
            )

            without_archetype = dossier_body(client, "MSFT")

            monkeypatch.setattr(
                CompanyUnderstandingService,
                "understanding",
                lambda self, symbol: understood(understand(bank_shape())),
            )

            with_bank = dossier_body(client, "MSFT")
    finally:
        app.dependency_overrides.clear()

    first = cast(dict[str, object], without_archetype["classification"])
    second = cast(dict[str, object], with_bank["classification"])

    # The classification genuinely changed between the two requests…
    assert cast(dict[str, object], first["playbook"])["state"] == "unavailable"
    assert cast(dict[str, object], second["playbook"])["state"] == "established"
    assert cast(dict[str, object], second["playbook"])["playbook"] == "Bank"

    # …and the decision did not, field by field.
    for field in DECISION_FIELDS:
        assert without_archetype[field] == with_bank[field], field


def test_the_dossier_serves_both_concepts_with_their_sentences(
    monkeypatch,
) -> None:
    """The wire shape: label + sentence for each half, states declared.

    Under the hermetic root nothing has been acquired, so both halves
    arrive in their honest empty states — each carrying the backend's
    own words, which is what the page renders instead of inventing
    fallback prose.
    """

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    try:
        with TestClient(app) as client:
            body = dossier_body(client, "MSFT")
    finally:
        app.dependency_overrides.clear()

    classification = cast(dict[str, object], body["classification"])
    industry = cast(dict[str, object], classification["industry"])
    playbook = cast(dict[str, object], classification["playbook"])

    assert industry["label"] == "Not acquired"
    assert industry["industry"] is None
    assert industry["read"] is None
    assert "No provider profile has been acquired" in cast(str, industry["stated"])

    assert playbook["state"] == "unavailable"
    assert playbook["playbook"] is None
    assert "No filing has been read for MSFT" in cast(str, playbook["stated"])

    assert cast(str, classification["distinction"])
