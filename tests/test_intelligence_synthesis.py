"""Crypto Intelligence slice 3: the LLM synthesis, and the validator that
is the slice.

The tests are mostly about **rejection**, because the model is the only
untrusted component this platform has ever had inside a rendered
surface. Two groups:

- one per rule the ruling named — unknown references, unsupported
  figures, unsupported entities, unsupported causality, action words;
- one per **false positive the first live drafts exposed**, which is the
  more instructive group. A validator that rejects correct writing is
  not strict, it is broken, and each of these was a plausible rule that
  failed against real output:
  - `hold` refused *"these funds already hold 1,223,634 BTC"* — a verb
    is not a verdict;
  - capitalisation refused *"Operational signals are cautious"* and
    *"Because perps fees are…"* — the start of a sentence is where
    capitalisation means nothing;
  - exact word matching refused `ETF` against evidence saying `ETFs`,
    and `Aug` against `7 August`;
  - `0.09pp` did not match evidence saying `0.09 percentage points`.

**No test calls a model.** Every draft here is a recorded or
hand-written payload pushed through the real validator, and
`tests/conftest.py` refuses a live client besides.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from app.domain.crypto_event import (
    CryptoEvent,
    EventFamily,
    EventFeed,
    SourceReport,
    SourceTier,
    anchors_in,
)
from app.domain.executive_narrative import NarrativeFinding
from app.domain.intelligence_synthesis import (
    IntelligenceSynthesis,
    SynthesisStatus,
)
from app.domain.provenance import Provenance
from app.providers.etf_flow_provider import EtfFlowReading
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined
from app.renderers.intelligence_synthesist import (
    GUARDED_CONCEPTS,
    IntelligenceSynthesist,
    SynthesisRejected,
    build_findings,
    synthesis_from_payload,
    synthesis_schema,
    user_prompt,
)
from app.services.intelligence_synthesis_service import IntelligenceSynthesisService
from tests.reachability import reachable

NOW = datetime(2026, 8, 10, 16, 0, tzinfo=UTC)


# ── the evidence a synthesis is allowed to see ──────────────────────

FINDINGS = (
    NarrativeFinding(
        id="C1",
        statement=(
            "Over the last 30 published days those funds took $128m net, "
            "positive on 18 of them; the largest single day of buying was "
            "$266m and the largest day of selling -$445m."
        ),
        source="Measured here — MOVRvest",
    ),
    NarrativeFinding(
        id="C2",
        statement="Those funds hold 1,223,634 BTC — 6.1% of the supply.",
        source="Reported — SoSoValue",
    ),
    NarrativeFinding(
        id="C3",
        statement="BTC returned +1.1% over 30 days.",
        source="Reported — CoinGecko",
    ),
    NarrativeFinding(
        id="E1",
        statement=(
            "Institutional participation: MicroStrategy Sells 1,690 BTC for "
            "Stock Buybacks — reported by 8 sources"
        ),
        source="Development, press report, 10 August",
    ),
    NarrativeFinding(
        id="R1",
        statement=(
            "BTC returned 0.09 percentage points more than the crypto market "
            "over 24 hours."
        ),
        source="MOVRvest arithmetic over two aligned intervals",
    ),
    NarrativeFinding(
        id="A1",
        statement=(
            "CoinGecko Insights states: “This indicates sustained "
            "institutional demand, potentially supporting price discovery.”"
        ),
        source=(
            "Attributed interpretation — a causal claim by its author, not "
            "established here"
        ),
    ),
)


def _item(stated: str, refs: tuple[str, ...] = ("C1",), theme: str = "Flows") -> dict:
    return {"stated": stated, "theme": theme, "refs": list(refs)}


def _payload(
    what: list[dict] | None = None,
    why: list[dict] | None = None,
    watch: list[dict] | None = None,
) -> dict:
    return {
        "what_matters": (
            [_item("Fund flows netted $128m over 30 days.")] if what is None else what
        ),
        "why_it_matters": (
            [_item("It is an identifiable channel of demand.", ("C1", "C2"))]
            if why is None
            else why
        ),
        "watch_next": (
            [_item("Whether flows stay positive.", ("C1",))] if watch is None else watch
        ),
    }


def _validate(payload: dict, causal_allowed: bool = False):  # type: ignore[no-untyped-def]
    return synthesis_from_payload(
        payload, findings=FINDINGS, causal_allowed=causal_allowed
    )


# ── A: the contract ─────────────────────────────────────────────────


def test_the_schema_asks_for_exactly_three_sections() -> None:
    schema = synthesis_schema()

    assert set(schema["required"]) == {
        "what_matters",
        "why_it_matters",
        "watch_next",
    }

    item = schema["properties"]["what_matters"]["items"]

    assert set(item["required"]) == {"stated", "theme", "refs"}

    # No recommendation field exists to fill. The model is not asked.
    assert "recommendation" not in schema["properties"]


def test_a_valid_draft_is_accepted_with_its_refs_intact() -> None:
    what, why, watch = _validate(_payload())

    assert len(what) == 1 and len(why) == 1 and len(watch) == 1

    assert why[0].refs == ("C1", "C2")
    assert what[0].theme == "Flows"


def test_the_prompt_supplies_findings_and_nothing_else() -> None:
    prompt = user_prompt("BTC", FINDINGS)

    for finding in FINDINGS:
        assert f"[{finding.id}]" in prompt

    assert "no sources beyond" not in prompt  # that belongs to the system side
    assert "Do not invent a future date" in prompt


# ── B: every rejection rule ─────────────────────────────────────────


def test_an_unknown_reference_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="not supplied"):
        _validate(_payload(what=[_item("Flows were positive.", ("Z9",))]))


def test_a_statement_with_no_reference_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="cites no findings"):
        _validate(_payload(what=[_item("Flows were positive.", ())]))


def test_an_unsupported_figure_is_rejected() -> None:
    """§4. A number that is in no finding does not exist."""

    with pytest.raises(SynthesisRejected, match="figure"):
        _validate(_payload(what=[_item("ETFs took $312m over the month.")]))


def test_a_rounded_figure_is_rejected() -> None:
    """The live catch. The model wrote 5.61m where the evidence said
    5,610,842 — readable, plausible, and a number nobody measured."""

    with pytest.raises(SynthesisRejected, match="may not round"):
        _validate(_payload(what=[_item("Those funds hold 1.22m BTC.", ("C2",))]))


def test_arithmetic_the_model_performed_is_rejected() -> None:
    """§4: the model must not calculate. $266m minus $445m is a figure
    this platform never published."""

    with pytest.raises(SynthesisRejected, match="may not calculate"):
        _validate(_payload(what=[_item("The two largest days net to -$179m.")]))


def test_an_unsupported_entity_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="Coinbase"):
        _validate(
            _payload(what=[_item("Flows through Coinbase were positive.", ("C1",))])
        )


def test_an_action_word_is_rejected() -> None:
    """§3. The layer says what matters, never what to do."""

    with pytest.raises(SynthesisRejected, match="never what to do"):
        _validate(_payload(why=[_item("Investors should buy the dip.", ("C1",))]))


def test_a_verdict_in_capitals_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="verdict"):
        _validate(_payload(why=[_item("The evidence supports MONITOR.", ("C1",))]))


def test_advice_this_platform_never_gives_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="no size, price or quantity"):
        _validate(_payload(why=[_item("This should inform position sizing.", ("C1",))]))


def test_a_causal_claim_is_rejected_where_no_source_asserts_one() -> None:
    """§4 and §12. The evidence contains no attributed cause, so no
    sentence may assert one."""

    with pytest.raises(SynthesisRejected, match="asserts a cause"):
        _validate(
            _payload(what=[_item("Inflows drove the 30-day gain.", ("C1", "C3"))]),
            causal_allowed=False,
        )


def test_a_causal_claim_must_name_its_source_even_when_one_exists() -> None:
    """§5. The attribution is part of the evidence.

    *"ETF inflows supported the price"* is refused; *"CoinGecko Insights
    attributes support to ETF inflows"* is not. The difference is
    whether the sentence keeps its author.
    """

    with pytest.raises(SynthesisRejected, match="naming the source"):
        _validate(
            _payload(what=[_item("Inflows supported the price.", ("A1",))]),
            causal_allowed=True,
        )

    accepted, _, _ = _validate(
        _payload(
            what=[
                _item(
                    "CoinGecko Insights attributes support for price "
                    "discovery to sustained demand.",
                    ("A1",),
                )
            ]
        ),
        causal_allowed=True,
    )

    assert accepted[0].refs == ("A1",)


def test_a_statement_longer_than_the_limit_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="word limit|over the"):
        _validate(_payload(what=[_item("flows " * 60)]))


def test_a_theme_that_is_a_sentence_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="a label, not a sentence"):
        _validate(
            _payload(
                what=[
                    {
                        "stated": "Flows netted $128m.",
                        "theme": "this is a very long theme that is really "
                        "a whole sentence pretending",
                        "refs": ["C1"],
                    }
                ]
            )
        )


# ── §18: no external knowledge ──────────────────────────────────────


def test_the_model_may_not_supply_a_fact_the_evidence_omitted() -> None:
    """§18, on the ruling's own three examples.

    The model certainly knows Bitcoin's cap, Ethereum's consensus and
    Hyperliquid's buyback. None of the three is in `FINDINGS`, so none
    of the three may be written — and each is caught by a different
    rule, which is why there are three rules.
    """

    for sentence in (
        "Against a fixed 21 million cap, flows matter more.",
        "Ethereum's move to proof of stake changes the supply path.",
        "The next halving will slow new supply.",
    ):
        with pytest.raises(SynthesisRejected, match="own knowledge|figure"):
            _validate(_payload(why=[_item(sentence, ("C1",))]))


def test_a_guarded_concept_is_allowed_once_the_evidence_states_it() -> None:
    """The other half: guarded is not forbidden.

    A concept the evidence *does* mention may be used freely — the rule
    is about the model's own knowledge, not about the vocabulary.
    """

    supplied = FINDINGS + (
        NarrativeFinding(
            id="F1",
            statement=(
                "Supply: 95.6% of a protocol maximum of 21,000,000 tokens "
                "has been emitted."
            ),
            source="Durable understanding — context, not news",
        ),
    )

    what, _, _ = synthesis_from_payload(
        _payload(
            what=[
                _item(
                    "With 95.6% of the protocol maximum of 21,000,000 "
                    "emitted, flows meet a slow new-supply path.",
                    ("F1", "C1"),
                )
            ]
        ),
        findings=supplied,
        causal_allowed=False,
    )

    assert what[0].refs == ("F1", "C1")


def test_every_guarded_concept_is_a_thing_a_model_knows() -> None:
    """A guard list is only useful if it names the actual failure mode."""

    assert "halving" in GUARDED_CONCEPTS
    assert "proof of stake" in GUARDED_CONCEPTS
    assert "buyback" in GUARDED_CONCEPTS


# ── the false positives the live drafts exposed ─────────────────────


def test_a_verb_is_not_a_verdict() -> None:
    """*"these funds already hold 1,223,634 BTC"* is a description.

    The first validator refused it, and refusing correct writing is not
    strictness — it is a rule that cannot tell a verb from a verdict.
    """

    what, _, _ = _validate(
        _payload(
            what=[_item("Those funds hold 1,223,634 BTC — 6.1%.", ("C2",))],
            watch=[_item("Whether fee revenue holds.", ("C1",))],
        )
    )

    assert "hold" in what[0].stated


def test_a_fabricated_name_is_caught_wherever_it_is_shaped_like_one() -> None:
    """Sentence-initial names are challenged by *shape*, and the reason
    is measured: across nine live drafts every sentence-initial
    rejection was ordinary English and none was a name."""

    for sentence in (
        "Flows through Coinbase were positive.",  # mid-sentence: strict
        "CoinDesk reported the largest day.",  # internal capital
        "AUSTRAC issued a second notice.",  # acronym — unsupplied here
        "Grayscale Trust added to the total.",  # capitalised phrase
    ):
        with pytest.raises(SynthesisRejected, match="own knowledge"):
            _validate(_payload(what=[_item(sentence, ("C1",))]))


def test_an_ordinary_first_word_is_not_challenged() -> None:
    """The other side of the same rule, and the one the live drafts
    kept losing to."""

    for opener in ("Analysts", "Scale", "Additional", "Flat", "Substantial"):
        what, _, _ = _validate(
            _payload(what=[_item(f"{opener} readings remain unresolved.", ("C1",))])
        )

        assert what


def test_a_capitalised_word_at_the_start_of_a_sentence_is_not_a_name() -> None:
    """*"Operational signals are cautious"*, *"Because perps fees are…"*,
    *"Divergent institutional actions…"* — all refused by the first
    rule, all ordinary English."""

    what, _, _ = _validate(
        _payload(
            what=[
                _item("Operational signals are mixed. Divergent flows persist."),
                _item("Concentrated selling offsets the month.", ("C1",)),
            ]
        )
    )

    assert len(what) == 2


def test_a_plural_in_the_evidence_admits_its_singular() -> None:
    """The evidence says `Buybacks`; the model writes `Buyback`. One word."""

    what, _, _ = _validate(
        _payload(what=[_item("The MicroStrategy Buyback is one event.", ("E1",))])
    )

    assert what


def test_a_month_may_be_abbreviated() -> None:
    """Evidence prints `10 August`; a model writes `Aug`."""

    what, _, _ = _validate(
        _payload(what=[_item("The sale was reported in Aug.", ("E1",))])
    )

    assert what


def test_a_causal_verb_is_matched_on_word_boundaries() -> None:
    """`sent` lives inside `absent` and `present`.

    Matched as a bare substring it refused a correct sentence about
    *absent* evidence for asserting a cause — and a guard that fires on
    the wrong sentence teaches a reader to distrust the guard.
    """

    what, _, _ = _validate(
        _payload(
            what=[
                _item(
                    "Corroboration is absent for most figures, and no "
                    "present reading settles it.",
                    ("C1",),
                )
            ]
        )
    )

    assert what

    with pytest.raises(SynthesisRejected, match="asserts a cause"):
        _validate(_payload(what=[_item("Inflows sent BTC higher.", ("C1",))]))


def test_percentage_points_and_pp_are_one_figure() -> None:
    """`0.09 percentage points` and `0.09pp` are the same measurement,
    and a validator that disagreed rejected a model quoting it exactly."""

    assert anchors_in("0.09 percentage points") == anchors_in("0.09pp")

    what, _, _ = _validate(
        _payload(what=[_item("BTC outpaced the market by 0.09pp.", ("R1",))])
    )

    assert what


# ── §15: fail closed ────────────────────────────────────────────────


def test_one_bad_statement_rejects_the_whole_draft() -> None:
    """§15, and the Executive Writer's contract unchanged.

    Deleting the offending sentence and showing the rest would tell an
    investor that what remains was checked *and that nothing was
    removed*. The second half would be false.
    """

    with pytest.raises(SynthesisRejected):
        _validate(
            _payload(
                what=[
                    _item("Fund flows netted $128m over 30 days."),
                    _item("Flows through Coinbase were positive.", ("C1",)),
                ]
            )
        )


def test_an_empty_section_is_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="no what_matters"):
        _validate(_payload(what=[]))


def test_too_many_statements_are_rejected() -> None:
    with pytest.raises(SynthesisRejected, match="over the limit"):
        _validate(_payload(what=[_item("Flows netted $128m.") for _ in range(6)]))


# ── §14: the deterministic fallback, every path ─────────────────────


class _DispersedFlows:
    """BTC's real 30-day window, distribution included.

    Slice 2's fixture carried the total and the day count and nothing
    else — exactly the shape the previous ruling called insufficient — so
    the synthesis fixture cannot reuse it, or the test that the model is
    *given* dispersion would pass against evidence that has none.
    """

    @staticmethod
    def flows(symbol: str) -> EtfFlowReading | None:
        if symbol.upper() != "BTC":
            return None

        return EtfFlowReading(
            symbol="BTC",
            group="us-btc-spot",
            source="SoSoValue",
            as_of=datetime(2026, 8, 7, tzinfo=UTC).date(),
            observed_at=NOW,
            daily_net_flow=98_845_326.9,
            total_net_assets=79_497_427_558.3,
            token_holdings=1_223_633.4,
            share_of_supply=0.06097325,
            flow_30d=127_718_020.0,
            inflow_days_30d=18,
            days_counted_30d=30,
            largest_inflow_day=265_686_935.0,
            largest_outflow_day=-444_505_600.0,
            current_streak=5,
        )

    @staticmethod
    def treasuries(symbol: str) -> None:
        return None


class _Provider:
    """A narrative provider that returns whatever it was handed."""

    name = "Test"
    model = "test-model"

    def __init__(self, text: str = "", error: Exception | None = None) -> None:
        self._text = text
        self._error = error

    async def draft(self, request: DraftRequest) -> Draft:
        if self._error is not None:
            raise self._error

        return Draft(text=self._text, model=self.model, usage=None)


def _snapshot():  # type: ignore[no-untyped-def]
    from app.domain.asset_class import AssetClass
    from app.services.crypto_intelligence_service import CryptoIntelligenceService
    from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
    from tests.test_crypto_intelligence import (
        _Claims,
        _Market,
        _NoFacts,
        _NoSupply,
    )

    event = CryptoEvent(
        identity="BTC|security|2026-08-10|115000000",
        symbols=("BTC",),
        family=EventFamily.SECURITY,
        headline="COLDCARD: $115m lost to Non-Random Private Key Generation",
        occurred_at=NOW,
        published_at=NOW,
        observed_at=NOW,
        reports=(SourceReport(source="DefiLlama", tier=SourceTier.PRIMARY, text="x"),),
    )

    class _Feed:
        @staticmethod
        def established(symbol: str, now: datetime | None = None) -> EventFeed:
            return EventFeed(events=(event,))

    outcome = CryptoIntelligenceService(
        facts=_NoFacts(),  # type: ignore[arg-type]
        market=_Market(),  # type: ignore[arg-type]
        protocol=ProtocolFundamentalsService(sources=(_Claims(),)),
        supply=_NoSupply(),  # type: ignore[arg-type]
        flows=_DispersedFlows(),  # type: ignore[arg-type]
        events=_Feed(),  # type: ignore[arg-type]
    ).snapshot("BTC", AssetClass.CRYPTO, now=NOW)

    assert outcome is not None

    return outcome


def _synthesise(provider: object) -> IntelligenceSynthesis:
    service = IntelligenceSynthesisService(
        synthesist=IntelligenceSynthesist(provider=provider)  # type: ignore[arg-type]
    )

    return asyncio.run(service.synthesise(_snapshot()))


def test_synthesis_is_off_by_default_and_says_so(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    outcome = asyncio.run(IntelligenceSynthesisService().synthesise(_snapshot()))

    assert outcome.status is SynthesisStatus.DISABLED
    assert outcome.absent_because
    assert not outcome.what_matters


def test_an_invalid_generation_falls_back_and_names_the_reason(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """§F. The guard fires and the deterministic brief stands."""

    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    import json

    bad = json.dumps(
        _payload(what=[_item("Flows through Coinbase reached $999m.", ("C1",))])
    )

    outcome = _synthesise(_Provider(text=bad))

    assert outcome.status is SynthesisStatus.REJECTED
    assert "refused" in (outcome.absent_because or "")
    assert not outcome.items


def test_a_provider_outage_falls_back(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    outcome = _synthesise(_Provider(error=RuntimeError("no route to host")))

    assert outcome.status is SynthesisStatus.UNAVAILABLE
    assert not outcome.items


def test_a_declined_request_falls_back(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    outcome = _synthesise(_Provider(error=NarrativeDeclined("the model declined")))

    assert outcome.status is SynthesisStatus.REJECTED


def test_an_empty_draft_falls_back(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    assert _synthesise(_Provider(text="")).status is SynthesisStatus.REJECTED


def test_unparseable_output_falls_back(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    assert _synthesise(_Provider(text="not json")).status is SynthesisStatus.REJECTED


def test_a_written_synthesis_is_grounded_in_what_was_supplied(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    import json

    snapshot = _snapshot()

    findings = build_findings(snapshot)

    refs = [findings[0].id, findings[1].id]

    good = json.dumps(
        {
            "what_matters": [
                {
                    "stated": "Two readings point the same way.",
                    "theme": "Flows",
                    "refs": refs,
                }
            ],
            "why_it_matters": [
                {
                    "stated": "It is an identifiable channel.",
                    "theme": "Demand",
                    "refs": refs[:1],
                }
            ],
            "watch_next": [
                {
                    "stated": "Whether it persists.",
                    "theme": "Persistence",
                    "refs": refs[:1],
                }
            ],
        }
    )

    outcome = _synthesise(_Provider(text=good))

    assert outcome.status is SynthesisStatus.WRITTEN
    assert outcome.grounded_in({finding.id for finding in findings})
    assert outcome.themes


# ── §10: the flow distribution reaches the model ────────────────────


def test_the_model_is_given_dispersion_and_not_only_a_total() -> None:
    """§10, a hard input requirement.

    *"positive net flow"* alone must not be able to produce *"strong ETF
    tailwind"* — so the finding the model reads carries the count of
    positive sessions and both extremes, not just the sum.
    """

    findings = build_findings(_snapshot())

    flow = next(f for f in findings if "published days" in f.statement)

    for fragment in ("18 of them", "266m", "445m"):
        assert fragment in flow.statement


# ── §23: adversarial evidence ───────────────────────────────────────


def test_a_figure_that_appears_only_in_a_narrative_is_still_supplied() -> None:
    """An attributed sentence is evidence *that the source said it*, so
    its figures are quotable — with the attribution intact."""

    supplied = FINDINGS + (
        NarrativeFinding(
            id="A2",
            statement='Elfa AI states: "Proceeds were about $108.6M."',
            source="Attributed interpretation — its author's view",
        ),
    )

    what, _, _ = synthesis_from_payload(
        _payload(what=[_item("Elfa AI states proceeds near $108.6M.", ("A2",))]),
        findings=supplied,
        causal_allowed=False,
    )

    assert what


def test_opposing_evidence_does_not_have_to_collapse_into_one_view() -> None:
    """§9. *Signals are mixed* is a permitted conclusion."""

    what, _, _ = _validate(
        _payload(
            what=[
                _item(
                    "Signals are mixed: flows netted $128m while a "
                    "-$445m session offset the month.",
                    ("C1",),
                )
            ]
        )
    )

    assert "mixed" in what[0].stated


# ── the boundaries ──────────────────────────────────────────────────


def test_the_synthesis_layer_cannot_reach_asset_quality() -> None:
    for module in (
        "app/domain/intelligence_synthesis.py",
        "app/renderers/intelligence_synthesist.py",
        "app/services/intelligence_synthesis_service.py",
    ):
        code = reachable(module)

        for forbidden in ("crypto_quality", "quality_signal", "asset_quality"):
            assert forbidden not in code, (module, forbidden)


def test_the_synthesis_layer_cannot_reach_the_decision_layer() -> None:
    """§3 and §18 of the ruling, structurally: no recommendation can be
    read, echoed or changed from here."""

    for module in (
        "app/domain/intelligence_synthesis.py",
        "app/renderers/intelligence_synthesist.py",
        "app/services/intelligence_synthesis_service.py",
    ):
        code = reachable(module)

        for forbidden in (
            "ExecutiveDecision",
            "InvestmentDecision",
            "Recommendation",
            "DecisionSynthesis",
            "CommitteeOpinion",
            "InvestmentThesis",
        ):
            assert forbidden not in code, (module, forbidden)


def test_the_synthesist_reuses_the_writer_seam_rather_than_a_new_one() -> None:
    """§16. A different prompt and schema were expected; a second LLM
    trust architecture was not."""

    code = reachable("app/renderers/intelligence_synthesist.py")

    # `reachable` folds its output, so the guard compares folded names.
    assert "narrativeprovider" in code
    assert "draftrequest" in code
    assert "narrativefinding" in code

    service = reachable("app/services/intelligence_synthesis_service.py")

    assert "build_provider" in service

    # And no parallel client anywhere in the slice.
    for forbidden in ("openai", "anthropic", "AsyncOpenAI", "httpx"):
        assert forbidden not in code, forbidden


def test_the_absence_is_always_worded() -> None:
    """A synthesis or the reason there is none, never both and never
    neither — the Executive Writer's rule, kept."""

    for status in SynthesisStatus:
        if status.is_written:
            continue

        assert status.stated


def test_provenance_names_the_model_that_wrote_it(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_INTELLIGENCE_SYNTHESIS", "on")

    import json

    findings = build_findings(_snapshot())

    good = json.dumps(
        {
            key: [
                {
                    "stated": "A grounded statement.",
                    "theme": "Theme",
                    "refs": [findings[0].id],
                }
            ]
            for key in ("what_matters", "why_it_matters", "watch_next")
        }
    )

    outcome = _synthesise(_Provider(text=good))

    assert outcome.model == "test-model"
    assert isinstance(outcome.reading, Provenance)
    assert "test-model" in outcome.reading.source
