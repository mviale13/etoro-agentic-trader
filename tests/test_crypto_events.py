"""Crypto Intelligence slice 2: current events and market narratives.

One test per acceptance criterion, plus one per defect the live corpus
found while this was being built. The second group is the more valuable
of the two — every one of them was a plausible-looking behaviour that
only failed against real copy:

- `"23,093 BTC"` read as twenty-three thousand **billion**, because the
  magnitude table matched `b` inside `BTC`.
- `"since China's 2021 ban"` read as two thousand and twenty-one billion.
- *"AUSTRAC suspended Cryptolink's VASP registration"* filed as an
  **opinion**, because the first decomposition rule required a digit
  before a sentence could be a fact.
- four **bitcoin** ETF stories attached to **Ethereum's** ETF event, on
  four shared words and no shared subject.
- DefiLlama's loss amounts read as millions, printing COLDCARD's $115m
  as `$115,000,000.0m`.

**Nothing here reads the network or the live store.** Every case runs on
markup and payloads recorded on 2026-08-10, pushed through the real
parsers and the real service.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.asset_class import AssetClass
from app.domain.crypto_event import (
    CryptoEvent,
    EventFact,
    EventFamily,
    EventFeed,
    EventFeedHealth,
    EventStatus,
    Interpretation,
    SourceReport,
    SourceTier,
    anchors_in,
    decompose,
    identity_of,
)
from app.domain.crypto_intelligence import DriverSupport
from app.providers.coin_insight_provider import (
    CoinInsightProvider,
    family_of,
    is_price_commentary,
)
from app.providers.etf_flow_provider import EtfFlowProvider, EtfFlowReading
from app.providers.press_corroboration_provider import PressItem, corroborate
from app.services.crypto_event_service import CryptoEventService, merge
from tests.reachability import reachable

NOW = datetime(2026, 8, 10, 16, 0, tzinfo=UTC)
READ = datetime(2026, 8, 10, 12, 40, tzinfo=UTC)


# ── recorded markup ─────────────────────────────────────────────────


def _entry(
    identifier: str,
    headline: str,
    body: str,
    when: str | None,
    sources: tuple[str, ...] = ("Elfa AI",),
) -> str:
    """One timeline entry in the surface's own shape, as recorded."""

    stamp = (
        f'<div data-rel-time="{when}" class="gecko-timeline-entry-title"> x </div>'
        if when
        else ""
    )

    icons = "".join(f'<span data-tooltip="{name}"></span>' for name in sources)

    return (
        '<div class="gecko-timeline-entry-wrapper">'
        f'<div class="gecko-timeline-entry" data-url="https://www.coingecko.com/'
        f'en/coins/bitcoin/insights/{identifier}" '
        f'data-insight-source-id="{identifier}">{stamp}'
        '<div class="gecko-timeline-entry-content">'
        '<div class="gecko-insight">'
        f'<span class="tw-font-semibold"> {headline}: </span>'
        f'<span class="tw-font-normal"> {body} </span>'
        f"</div>{icons}"
        f'<div class="tw-text-xs"> {len(sources)} sources </div>'
        "</div></div></div>"
    )


#: The Bitcoin timeline as it read on 2026-08-10, trimmed to the entries
#: the tests turn on. The second section is dated on the *section* and
#: carries no per-entry stamp, which is the shape that made a whole day
#: of events undated in the first draft.
BTC_PAGE = (
    '<div data-date="2026-08-10" class="gecko-timeline-primary"><div>Today</div>'
    + _entry(
        "102229428",
        "Marathon Sells 23,093 BTC in First Half 2026",
        "Marathon (MARA) sold 23,093 BTC, valued at approximately $1.6 billion, "
        "during the first half of 2026. The company now holds about 35,577 BTC.",
        "2026-08-10T15:51:00Z",
    )
    + _entry(
        "102229424",
        "AUSTRAC Suspends Cryptolink Bitcoin ATM Registration",
        "Australia's financial watchdog AUSTRAC suspended Cryptolink's VASP "
        "registration for three months.",
        "2026-08-10T14:51:41Z",
    )
    + _entry(
        "102229430",
        "H100 Group Increases Bitcoin Holdings to 3,506 BTC",
        "H100 Group acquired 2,455.7 BTC through company acquisitions, raising "
        "its total Bitcoin holdings to approximately 3,506 BTC.",
        "2026-08-10T13:52:00Z",
        sources=("Elfa AI", "PANews (EN)"),
    )
    + _entry(
        "102229431",
        "Bitcoin Price Holds Key $118,000 Support",
        "Bitcoin's price consolidated near $118,400, with buyers defending the "
        "$118,000 area.",
        "2026-08-10T12:00:00Z",
    )
    + '</div><div data-date="2026-08-09" class="gecko-timeline-primary">'
    "<div>Yesterday</div>"
    + _entry(
        "102229400",
        "Bitcoin Mining Difficulty Drops 19% from Peak",
        "Bitcoin mining difficulty declined by 19% from its peak. This "
        "highlights economic pressures on miners.",
        None,
    )
    + "</div>"
)

#: One incident, exactly as the register returns it.
COLDCARD = {
    "date": int(datetime(2026, 7, 31, tzinfo=UTC).timestamp()),
    "name": "COLDCARD",
    "classification": "Infrastructure",
    "technique": "Non-Random Private Key Generation",
    "amount": 115_000_000,
    "chain": ["Bitcoin"],
    "source": "https://example.invalid/coldcard",
    "returnedFunds": None,
}


class _Page:
    """The insight provider with the network replaced by recorded markup."""

    def __init__(self, page: str) -> None:
        self.page = page

    def __call__(self, url: str) -> str:
        return self.page


def _insights(page: str = BTC_PAGE) -> CoinInsightProvider:
    provider = CoinInsightProvider(detail_budget=0)

    provider._fetch = _Page(page)  # type: ignore[method-assign, assignment]

    return provider


# ── A: the source measurement is recorded, not assumed ──────────────


def test_the_narrative_surface_is_web_only_and_says_so() -> None:
    """§5. The measurement lives in the module that depends on it.

    Not decoration: the ruling asked for the terms of this surface
    before anything was built on it, and a reader who finds the parser
    later needs to know it is parsing a page rather than calling an API.
    """

    text = (
        __import__("pathlib")
        .Path("app/providers/coin_insight_provider.py")
        .read_text(encoding="utf-8")
    )

    assert "API accessible?    NO" in text
    assert "401" in text and "PRO API" in text


# ── B: the canonical model ──────────────────────────────────────────


def test_a_number_is_normalised_the_same_however_it_is_written() -> None:
    """Three spellings of one figure are one anchor, or two accounts of
    one event never recognise each other."""

    assert anchors_in("$1.6 billion") == anchors_in("$1.6bn")
    assert anchors_in("$1.6bn") == anchors_in("$1,600,000,000")


def test_a_ticker_is_not_a_magnitude() -> None:
    """The `b`-inside-`BTC` defect, caught against live copy.

    Twenty-three thousand BTC became twenty-three thousand *billion*,
    which is not a rounding error — it is an anchor no other account of
    the same event could ever match.
    """

    assert anchors_in("Marathon sold 23,093 BTC") == ("23093",)


def test_a_year_is_not_a_quantity() -> None:
    """`2021 ban` must not become an anchor, and `2021bn` must."""

    assert anchors_in("the largest drop since China's 2021 ban") == ()
    assert anchors_in("during the first half of 2026") == ()

    # Still a quantity where something marks it as one.
    assert anchors_in("$2,026 per coin") == ("2026",)


def test_a_hedged_sentence_is_attributed_and_a_plain_one_is_not() -> None:
    """§2, and the rule that decides it.

    The marker separates them, not the number. Both halves are asserted
    because the first draft got the second one wrong.
    """

    facts, readings = decompose(
        "AUSTRAC suspended Cryptolink's VASP registration for three months. "
        "This indicates growing regulatory pressure on Bitcoin access.",
        "CoinGecko",
    )

    assert [fact.stated for fact in facts] == [
        "AUSTRAC suspended Cryptolink's VASP registration for three months."
    ]

    assert len(readings) == 1
    assert readings[0].source == "CoinGecko"


def test_a_graded_sentence_is_an_interpretation_even_with_a_figure() -> None:
    """*"$245m indicates sustained demand"* is somebody's reading."""

    facts, readings = decompose(
        "Ethereum spot ETFs recorded $245 million in net inflows last week. "
        "This indicates sustained institutional demand for ETH.",
        "CoinGecko",
    )

    assert len(facts) == 1
    assert facts[0].anchors == ("245000000",)

    assert len(readings) == 1
    assert not readings[0].is_causal


def test_a_causal_sentence_is_marked_and_never_settled() -> None:
    """§12. The platform keeps it, labels it, and does not resolve it."""

    _, readings = decompose(
        "ETF inflows are supporting Bitcoin's price, driven by institutional demand.",
        "CoinGecko",
    )

    assert [item.is_causal for item in readings] == [True]


def test_the_ruling_s_own_sentence_decomposes() -> None:
    """§G's acceptance case, on the exact wording the ruling used."""

    facts, readings = decompose(
        "US spot Bitcoin ETFs recorded $128 million of net inflows. "
        "Institutional interest remains strong and ETF demand is supporting "
        "the price.",
        "A provider",
    )

    assert [fact.anchors for fact in facts] == [("128000000",)]

    assert len(readings) == 1
    assert readings[0].is_causal
    assert readings[0].source == "A provider"


# ── the parse, and its failure modes ────────────────────────────────


def test_the_timeline_parses_into_dated_events() -> None:
    events, health = _insights().events("BTC", NOW)

    assert health.reached

    headlines = {event.headline for event in events}

    assert "Marathon Sells 23,093 BTC in First Half 2026" in headlines

    marathon = next(e for e in events if e.headline.startswith("Marathon"))

    assert marathon.at == datetime(2026, 8, 10, 15, 51, tzinfo=UTC)
    assert marathon.family is EventFamily.INSTITUTIONAL_ADOPTION


def test_an_entry_dated_only_by_its_section_is_not_left_undated() -> None:
    """The *Yesterday* trap.

    Entries under the second date heading carry no per-entry stamp. A
    parse reading only the entry attribute leaves them undated — and
    undated is never current, so a whole day of events drops silently
    out of every brief while the page still looks fine.
    """

    events, _ = _insights().events("BTC", NOW)

    difficulty = next(e for e in events if "Difficulty" in e.headline)

    assert difficulty.at == datetime(2026, 8, 9, tzinfo=UTC)


def test_price_commentary_is_declined_and_counted() -> None:
    """§1: developments, not a price feed.

    Price commentary is a worse reading of something this platform
    already measures itself. It is refused — and *counted*, so the
    refusal is visible rather than a quiet gap.
    """

    assert is_price_commentary("Bitcoin Price Holds Key $118,000 Support", "")

    events, health = _insights().events("BTC", NOW)

    assert not [e for e in events if "Price Holds" in e.headline]

    assert health.entries_declined == 1
    assert not health.is_degraded


def test_a_broken_page_reports_itself_rather_than_returning_nothing() -> None:
    """The failure mode of a parser against a page that changed is zero
    events and no error. That must not look like a quiet day."""

    events, health = _insights(
        '<div class="gecko-timeline-entry-wrapper">x</div>'
    ).events("BTC", NOW)

    assert not events
    assert health.reached
    assert health.is_degraded
    assert "page shape may have changed" in health.stated


def test_an_unmapped_asset_is_not_a_failed_read() -> None:
    events, health = _insights().events("DOGE", NOW)

    assert not events
    assert not health.reached
    assert "not mapped" in (health.because or "")


def test_the_family_rules_place_the_live_corpus() -> None:
    """The classifications measured over the live timeline."""

    assert family_of("Coinsbuy Wallet Drain Affects Ethereum", "") is (
        EventFamily.SECURITY
    )
    assert family_of("AUSTRAC Suspends Cryptolink Registration", "") is (
        EventFamily.REGULATORY
    )
    assert family_of("Ethereum Spot ETFs See $245M Net Inflows", "") is (
        EventFamily.CAPITAL_FLOW
    )
    assert family_of("MicroStrategy Sells 1,690 BTC for Stock Buybacks", "") is (
        EventFamily.INSTITUTIONAL_ADOPTION
    )

    # "supply" bare captured staking; only its compounds are tokenomics.
    assert family_of("Ethereum Sees Record Staked Supply", "") is (
        EventFamily.NETWORK_OPERATION
    )

    # An entry the words do not place is declined, not filed under a
    # family that happens to sort last.
    assert family_of("Cardano Foundation CTO to Resign August 31", "") is None


# ── H: deduplication across sources ─────────────────────────────────


def _event(
    headline: str,
    source: str,
    tier: SourceTier = SourceTier.AGGREGATOR,
    family: EventFamily = EventFamily.INSTITUTIONAL_ADOPTION,
    when: datetime = READ,
    fact: str | None = None,
) -> CryptoEvent:
    body = fact or headline

    return CryptoEvent(
        identity=identity_of(("BTC",), family, headline, when),
        symbols=("BTC",),
        family=family,
        headline=headline,
        occurred_at=when,
        published_at=when,
        observed_at=READ,
        reports=(SourceReport(source=source, tier=tier, text=body),),
        facts=(EventFact(stated=body, anchors=anchors_in(body)),),
    )


def test_two_accounts_of_one_event_collapse_into_one() -> None:
    """§9, on the case the live corpus supplied.

    Two outlets, two headlines, one development — and the figure they
    share is what proves it, because they share almost no words.
    """

    merged = merge(
        [
            _event("H100 Group Increases Bitcoin Holdings to 3,506 BTC", "CoinGecko"),
            _event(
                "Adam Back-backed H100 more than triples bitcoin holdings to 3,506 BTC",
                "The Block",
                tier=SourceTier.SECONDARY,
            ),
        ]
    )

    assert len(merged) == 1

    assert set(merged[0].sources) == {"CoinGecko", "The Block"}

    # The closest account's wording is kept.
    assert merged[0].tier is SourceTier.SECONDARY


def test_two_different_events_do_not_collapse() -> None:
    """The other half, and the one that matters: a dedup rule that
    merges too eagerly loses developments silently."""

    merged = merge(
        [
            _event("H100 Group Increases Bitcoin Holdings to 3,506 BTC", "CoinGecko"),
            _event("MicroStrategy Sells 1,690 BTC for Buybacks", "CoinGecko"),
        ]
    )

    assert len(merged) == 2


def test_a_merge_keeps_both_readings_and_averages_neither() -> None:
    left = _event("H100 raises holdings to 3,506 BTC", "CoinGecko")

    right = CryptoEvent(
        identity=left.identity,
        symbols=("BTC",),
        family=left.family,
        headline=left.headline,
        occurred_at=READ,
        published_at=READ,
        observed_at=READ,
        reports=(
            SourceReport(source="The Block", tier=SourceTier.SECONDARY, text="x"),
        ),
        interpretations=(
            Interpretation(stated="This is bullish.", source="The Block"),
        ),
    )

    merged = merge([left, right])

    assert len(merged) == 1
    assert len(merged[0].interpretations) == 1
    assert merged[0].interpretations[0].source == "The Block"


# ── corroboration: a witness, never a discoverer ────────────────────


def test_the_press_corroborates_an_event_it_names() -> None:
    event = _event("H100 Group Increases Bitcoin Holdings to 3,506 BTC", "CoinGecko")

    witnessed = corroborate(
        event,
        (
            PressItem(
                source="The Block",
                title="Adam Back-backed H100 more than triples bitcoin holdings "
                "to 3,506 BTC",
                url="https://example.invalid/h100",
                published_at=READ,
            ),
        ),
    )

    assert "The Block" in witnessed.sources
    assert witnessed.facts[0].is_corroborated


def test_the_press_cannot_corroborate_an_event_about_another_asset() -> None:
    """The bitcoin-onto-Ethereum defect, from the first live run.

    Four bitcoin ETF stories attached themselves to Ethereum's ETF event
    on four shared words — *spot*, *ETFs*, *inflows*, *week* — and no
    shared subject. A headline that never names the asset is not
    corroboration for it however well its words line up.
    """

    ethereum = CryptoEvent(
        identity="ETH|capital_flow|2026-08-10|245000000",
        symbols=("ETH",),
        family=EventFamily.CAPITAL_FLOW,
        headline="Ethereum Spot ETFs See $245 Million Net Inflows Last Week",
        occurred_at=READ,
        published_at=READ,
        observed_at=READ,
        reports=(
            SourceReport(source="CoinGecko", tier=SourceTier.AGGREGATOR, text="x"),
        ),
    )

    witnessed = corroborate(
        ethereum,
        (
            PressItem(
                source="CoinDesk",
                title="Spot bitcoin ETFs post net inflows across all five "
                "sessions last week",
                url=None,
                published_at=READ,
            ),
        ),
    )

    assert witnessed.sources == ("CoinGecko",)


def test_a_small_number_is_not_enough_to_identify_an_event() -> None:
    """*"between August 3-9"* yields the anchors `3` and `9`.

    A headline is very likely to contain a small number for reasons of
    its own, so matching on one would attach unrelated stories to an
    event. A percentage is exempt: "19%" is specific in a way "3" is not.
    """

    from app.providers.press_corroboration_provider import distinctive

    assert distinctive({"3", "9", "1690", "19%"}) == {"1690", "19%"}


def test_a_press_item_never_introduces_an_event() -> None:
    """The rule that keeps this from being a news feed.

    `corroborate` takes an event and returns an event. There is no path
    by which a headline becomes a development on its own.
    """

    event = _event("H100 Group Increases Bitcoin Holdings to 3,506 BTC", "CoinGecko")

    witnessed = corroborate(
        event,
        (
            PressItem(
                source="CoinDesk",
                title="Bitcoin miner Bitdeer's shares sink 15% despite revenue growth",
                url=None,
                published_at=READ,
            ),
        ),
    )

    assert witnessed.sources == ("CoinGecko",)
    assert witnessed.headline == event.headline


# ── I: freshness ────────────────────────────────────────────────────


class _Feed:
    """An event service serving recorded events, never a network."""

    def __init__(self, events: tuple[CryptoEvent, ...]) -> None:
        self._events = events

    def established(self, symbol: str, now: datetime | None = None) -> EventFeed:
        return EventFeed(
            events=CryptoEventService._live(self._events, now),
            health=(EventFeedHealth(source="recorded", reached=True),),
        )


def test_a_stale_event_leaves_the_brief_rather_than_being_ranked_last() -> None:
    """§10, and its negative half.

    A fortnight-old headline is not kept because nothing newer exists.
    Ranking it last would still surface it once the list was short,
    which is exactly what the ruling forbids.
    """

    old = _event(
        "Something that happened a long time ago",
        "CoinGecko",
        when=NOW - timedelta(days=30),
    )

    fresh = _event("Something that happened today", "CoinGecko", when=NOW)

    assert CryptoEventService._live((old, fresh), NOW) == (fresh,)

    # And with nothing fresh at all, the answer is nothing.
    assert CryptoEventService._live((old,), NOW) == ()


def test_an_empty_event_set_is_stated_rather_than_blank() -> None:
    from app.commands.intelligence_brief import _events
    from app.domain.crypto_intelligence import CryptoIntelligenceSnapshot

    snapshot = CryptoIntelligenceSnapshot(symbol="BTC", as_of=NOW)

    assert "No material current event identified" in _events(snapshot, False)[0]


# ── K: materiality is ranked, never scored ──────────────────────────


def test_a_security_incident_outranks_an_adoption_headline() -> None:
    incident = _event(
        "An exploit",
        "DefiLlama",
        tier=SourceTier.PRIMARY,
        family=EventFamily.SECURITY,
        when=NOW - timedelta(days=2),
    )

    adoption = _event("A company bought some", "CoinGecko", when=NOW)

    assert CryptoEventService._live((adoption, incident), NOW)[0] is incident


def test_rank_is_a_tuple_of_ordinals_and_not_a_score() -> None:
    """§11: *avoid numerical scoring if simple ranked rules are
    sufficient*. The rank is ordinal terms, read in order."""

    rank = _event("x", "CoinGecko").rank(NOW)

    assert isinstance(rank, tuple)
    assert all(isinstance(term, int) for term in rank)


# ── C: flow distribution ────────────────────────────────────────────


def test_the_flow_shape_separates_concentrated_from_persistent() -> None:
    """§13, on the two live windows that motivated it.

    BTC's $128m net arrived across sessions whose largest single day of
    *selling* was $445m — three and a half times the month's whole net
    total. ETH's $540m arrived on 21 of 30 days with no session above
    $92m. Slice 1 printed both as a total and a day count, and they read
    as the same thing.
    """

    btc = EtfFlowReading(
        symbol="BTC",
        group="us-btc-spot",
        source="SoSoValue",
        as_of=datetime(2026, 8, 7, tzinfo=UTC).date(),
        observed_at=READ,
        flow_30d=127_718_020.0,
        inflow_days_30d=18,
        days_counted_30d=30,
        largest_inflow_day=265_686_935.0,
        largest_outflow_day=-444_505_600.0,
        current_streak=5,
    )

    eth = EtfFlowReading(
        symbol="ETH",
        group="us-eth-spot",
        source="SoSoValue",
        as_of=datetime(2026, 8, 7, tzinfo=UTC).date(),
        observed_at=READ,
        flow_30d=539_615_811.0,
        inflow_days_30d=21,
        days_counted_30d=30,
        largest_inflow_day=92_150_884.0,
        largest_outflow_day=-70_617_894.0,
        current_streak=4,
    )

    assert btc.shape == "concentrated"
    assert eth.shape == "persistent"

    assert btc.concentration is not None and btc.concentration > 3
    assert eth.concentration is not None and eth.concentration < 0.2


def test_a_streak_is_broken_by_a_flat_day() -> None:
    """A day on which nothing moved did not continue the run."""

    assert (
        EtfFlowProvider._rolling(
            [{"totalNetInflow": v} for v in (10.0, 5.0, 0.0, 3.0, 2.0, 1.0)]
        )["current_streak"]
        == 2
    )


def test_a_stored_schema_1_reading_migrates_without_inventing_dispersion() -> None:
    """S5.2's rule, applied. The daily series was never stored, so the
    three figures are absent rather than zero — a zero would say the
    biggest day was nothing."""

    from app.providers.etf_flow_provider import _to_schema_2

    migrated = _to_schema_2({"symbol": "BTC", "flow_30d": 1.0})

    assert migrated["largest_inflow_day"] is None
    assert migrated["current_streak"] is None


# ── D/E/F: the brief, and §12's guard on causality ──────────────────


def _snapshot(events: tuple[CryptoEvent, ...] = (), flows: object | None = None):  # type: ignore[no-untyped-def]
    from app.services.crypto_intelligence_service import CryptoIntelligenceService
    from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
    from tests.test_crypto_intelligence import (
        _Claims,
        _Flows,
        _Market,
        _NoFacts,
        _NoSupply,
    )

    service = CryptoIntelligenceService(
        facts=_NoFacts(),  # type: ignore[arg-type]
        market=_Market(),  # type: ignore[arg-type]
        protocol=ProtocolFundamentalsService(sources=(_Claims(),)),
        supply=_NoSupply(),  # type: ignore[arg-type]
        flows=flows or _Flows(),  # type: ignore[arg-type]
        events=_Feed(events),  # type: ignore[arg-type]
    )

    outcome = service.snapshot("BTC", AssetClass.CRYPTO, now=NOW)

    assert outcome is not None

    return outcome


def test_events_reach_the_brief_as_claims_and_as_drivers() -> None:
    incident = _event(
        "COLDCARD: $115m lost to Non-Random Private Key Generation",
        "DefiLlama",
        tier=SourceTier.PRIMARY,
        family=EventFamily.SECURITY,
        when=NOW - timedelta(days=2),
    )

    snapshot = _snapshot((incident,))

    assert incident.identity in {claim.ref for claim in snapshot.claims}

    assert any(incident.identity in driver.claims for driver in snapshot.headwinds)


def test_a_coincidence_is_worded_as_one() -> None:
    """§12. *"while"*, never *"because"*."""

    snapshot = _snapshot()

    coincident = [
        driver
        for driver in snapshot.drivers
        if driver.support is DriverSupport.COINCIDENT
    ]

    assert coincident

    assert "while" in coincident[0].stated
    assert "because" not in coincident[0].stated.lower()


def test_a_source_s_causal_claim_is_carried_as_the_source_s() -> None:
    event = CryptoEvent(
        identity="BTC|capital_flow|2026-08-10|1",
        symbols=("BTC",),
        family=EventFamily.CAPITAL_FLOW,
        headline="Flows rose",
        occurred_at=NOW,
        published_at=NOW,
        observed_at=READ,
        reports=(
            SourceReport(source="A provider", tier=SourceTier.AGGREGATOR, text="x"),
        ),
        interpretations=(
            Interpretation(
                stated="ETF demand is supporting the price.",
                source="A provider",
                is_causal=True,
            ),
        ),
    )

    snapshot = _snapshot((event,))

    attributed = [
        driver
        for driver in snapshot.drivers
        if driver.support is DriverSupport.ATTRIBUTED_BY_SOURCE
    ]

    assert attributed
    assert attributed[0].stated.startswith("A provider:")

    assert snapshot.causal_claims
    assert snapshot.causal_claims[0].source == "A provider"


def test_a_concentrated_month_is_not_reported_as_a_tailwind() -> None:
    """The slice-1 defect the handoff named, fixed at the driver too.

    Fixing only the sentence left the brief contradicting itself: the
    claim said *"offsetting flows rather than accumulation"* while the
    driver beside it still called the same month *"a net source of
    demand"* and filed it under tailwinds.
    """

    class _Concentrated:
        @staticmethod
        def flows(symbol: str) -> EtfFlowReading | None:
            return EtfFlowReading(
                symbol="BTC",
                group="us-btc-spot",
                source="SoSoValue",
                as_of=datetime(2026, 8, 7, tzinfo=UTC).date(),
                observed_at=READ,
                daily_net_flow=98_845_326.9,
                total_net_assets=79_497_427_558.3,
                flow_30d=127_718_020.0,
                inflow_days_30d=18,
                days_counted_30d=30,
                largest_inflow_day=265_686_935.0,
                largest_outflow_day=-444_505_600.0,
            )

        @staticmethod
        def treasuries(symbol: str) -> None:
            return None

    snapshot = _snapshot(flows=_Concentrated())

    flow = snapshot.claim("flow.30d")

    assert flow is not None
    assert "offsetting flows rather than accumulation" in flow.stated

    assert not [driver for driver in snapshot.tailwinds if "flow.30d" in driver.claims]


def test_watch_next_never_invents_a_date() -> None:
    """§16. Where nothing scheduled is known, the item is a measurable
    condition on evidence already held — and says how it is measured."""

    snapshot = _snapshot()

    assert snapshot.watch_next
    assert len(snapshot.watch_next) <= 3

    for item in snapshot.watch_next:
        assert not item.is_scheduled
        assert item.measured_by
        assert item.because


def test_the_snapshot_is_grounded_in_what_it_holds() -> None:
    """Drivers, watch items and narratives all resolve to held refs."""

    incident = _event(
        "An exploit",
        "DefiLlama",
        tier=SourceTier.PRIMARY,
        family=EventFamily.SECURITY,
        when=NOW,
    )

    assert _snapshot((incident,)).grounded


# ── the boundaries the ruling fixed ─────────────────────────────────


def test_the_event_layer_cannot_reach_asset_quality() -> None:
    """§18, in both directions and structurally."""

    for module in (
        "app/domain/crypto_event.py",
        "app/services/crypto_event_service.py",
        "app/providers/coin_insight_provider.py",
        "app/providers/primary_event_provider.py",
        "app/providers/press_corroboration_provider.py",
        "app/commands/crypto_events.py",
    ):
        code = reachable(module)

        for forbidden in ("crypto_quality", "quality_signal", "asset_quality"):
            assert forbidden not in code, (module, forbidden)


def test_the_event_layer_cannot_reach_the_decision_layer() -> None:
    """§18. No recommendation, no threshold, no verdict."""

    for module in (
        "app/domain/crypto_event.py",
        "app/services/crypto_event_service.py",
        "app/services/crypto_intelligence_service.py",
        "app/commands/crypto_events.py",
    ):
        code = reachable(module)

        for forbidden in (
            "InvestmentDecision",
            "Recommendation",
            "DecisionSynthesis",
            "CommitteeOpinion",
        ):
            assert forbidden not in code, (module, forbidden)


def test_no_model_is_asked_anywhere_in_the_slice() -> None:
    """§17. The deterministic floor is the implementation, not a
    fallback behind a flag."""

    for module in (
        "app/services/crypto_event_service.py",
        "app/services/crypto_intelligence_service.py",
        "app/commands/crypto_events.py",
        "app/commands/intelligence_brief.py",
    ):
        code = reachable(module, with_literals=True)

        for forbidden in (
            "openai",
            "anthropic",
            "NarrativeProvider",
            "ExecutiveWriter",
            "prompt",
        ):
            assert forbidden not in code, (module, forbidden)


def test_nothing_branches_on_a_ticker() -> None:
    """§8 and the slice-1 rule it inherits: evidence decides.

    The incident register is asked with a chain map, the release feed
    with a repository map, and the timeline with the provider's own
    identifiers. None of them is a rule about a symbol — hand the same
    code a different asset with the same evidence and it behaves the
    same way.
    """

    events, _ = _insights().events("ETH", NOW)

    # The identical Bitcoin markup, read under another symbol, produces
    # the identical events attributed to that symbol.
    assert events
    assert all(event.symbols == ("ETH",) for event in events)


def test_a_register_entry_is_one_fact_with_its_units_intact() -> None:
    """DefiLlama publishes whole dollars. Read as millions once, and
    COLDCARD's $115m printed as `$115,000,000.0m`."""

    from app.providers.primary_event_provider import PrimaryEventProvider

    event = PrimaryEventProvider()._incident("BTC", COLDCARD)

    assert event is not None
    assert "$115m" in event.headline
    assert event.family is EventFamily.SECURITY
    assert event.status is EventStatus.ONGOING
    assert event.entity == "COLDCARD"
    assert event.tier is SourceTier.PRIMARY


def test_an_asset_with_no_release_feed_is_not_reported_as_a_gap() -> None:
    """Hyperliquid publishes none. That is a fact about the protocol,
    not a failed read — the same distinction the flow acquisition makes
    for a token with no fund vehicle."""

    from app.providers.primary_event_provider import PrimaryEventProvider

    _, health = PrimaryEventProvider().releases("HYPE")

    assert not health.reached
    assert "not a failed read" in (health.because or "")
