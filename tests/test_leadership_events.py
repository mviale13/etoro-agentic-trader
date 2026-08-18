"""Equity leadership events: regulator-filed facts, decision-neutral."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from app import cli
from app.domain.leadership_event import (
    ExecutiveRole,
    LeadershipEventFeed,
    LeadershipEventKind,
    LeadershipFeedHealth,
)
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.edgar_filings import CurrentReportReference, EdgarFilings
from app.providers.sec_leadership_provider import (
    SecLeadershipProvider,
    parse_leadership_events,
)
from app.services.leadership_event_service import LeadershipEventService
from tests.reachability import reachable

ADBE_CEO = CurrentReportReference(
    symbol="ADBE",
    company="ADOBE INC.",
    form="8-K",
    filed_on=date(2026, 3, 12),
    accession="0000796343-26-000048",
    url=(
        "https://www.sec.gov/Archives/edgar/data/796343/"
        "000079634326000048/adbe-20260309.htm"
    ),
    items=("2.02", "5.02", "7.01", "9.01"),
)

ADBE_CFO = CurrentReportReference(
    symbol="ADBE",
    company="ADOBE INC.",
    form="8-K",
    filed_on=date(2026, 6, 11),
    accession="0000796343-26-000109",
    url=(
        "https://www.sec.gov/Archives/edgar/data/796343/"
        "000079634326000109/adbe-20260608.htm"
    ),
    items=("2.02", "5.02", "9.01"),
)

CEO_ITEM = """\
Item 5.02 Departure of Directors or Certain Officers; Election of Directors;
Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.
On March 9, 2026, Shantanu Narayen notified Adobe of his decision to transition
from his role as Adobe's Chief Executive Officer. Adobe is conducting a search
for Mr. Narayen's successor. Mr. Narayen will remain as Adobe's Chief Executive
Officer until his successor is appointed. Mr. Narayen will remain as Chair of
Adobe's Board of Directors.
"""

CFO_ITEM = """\
Item 5.02 Departure of Directors or Certain Officers; Election of Directors;
Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.
On June 8, 2026, Daniel Durn notified the Company of his decision to resign as
Chief Financial Officer and Executive Vice President, Finance, Technology,
Security and Operations, effective June 15, 2026. On June 11, 2026, Steven Day
was appointed to serve as the Company's interim Chief Financial Officer,
effective immediately upon Mr. Durn's departure. Mr. Day joined the Company in
2006.
"""


def test_adobe_ceo_search_is_one_open_transition_with_its_qualifying_facts() -> None:
    (event,) = parse_leadership_events(ADBE_CEO, CEO_ITEM)

    assert event.kind is LeadershipEventKind.SUCCESSION_SEARCH
    assert event.role is ExecutiveRole.CHIEF_EXECUTIVE
    assert event.person == "Shantanu Narayen"
    assert event.occurred_on == date(2026, 3, 9)
    assert event.effective_on is None
    assert event.kind.names_no_permanent_successor

    assert len(event.facts) == 4
    assert "conducting a search" in event.facts[1]
    assert "until his successor is appointed" in event.facts[2]
    assert "Chair" in event.facts[3]

    assert event.source.accession == "0000796343-26-000048"
    assert event.identity.endswith("chief_executive|succession_search|shantanu-narayen")


def test_adobe_cfo_filing_keeps_departure_and_interim_appointment_apart() -> None:
    events = parse_leadership_events(ADBE_CFO, CFO_ITEM)

    assert [event.kind for event in events] == [
        LeadershipEventKind.DEPARTURE,
        LeadershipEventKind.INTERIM_APPOINTMENT,
    ]
    assert [event.person for event in events] == ["Daniel Durn", "Steven Day"]
    assert all(event.role is ExecutiveRole.CHIEF_FINANCIAL for event in events)

    departure, interim = events

    assert departure.effective_on == date(2026, 6, 15)
    # "Immediately upon Mr. Durn's departure" is conditional.  The parser
    # does not silently borrow the preceding event's effective date.
    assert interim.effective_on is None
    assert interim.kind.names_no_permanent_successor
    assert interim.facts == (interim.facts[0],)
    assert departure.facts == (departure.facts[0],)


def test_compensation_in_the_same_sec_item_is_not_a_leadership_event() -> None:
    compensation = """\
Item 5.02 Departure of Directors or Certain Officers; Election of Directors;
Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.
On April 15, 2026, the Compensation Committee approved an amended award for
the Company's Chief Executive Officer.
"""

    assert parse_leadership_events(ADBE_CEO, compensation) == ()


def test_a_planned_transition_is_not_called_a_search_without_search_evidence() -> None:
    transition = """\
Item 5.02 Departure of Directors or Certain Officers.
On April 2, 2026, Jane Example notified the Company of her decision to
transition from her role as Chief Executive Officer to Executive Chair.
"""

    (event,) = parse_leadership_events(ADBE_CEO, transition)

    assert event.kind is LeadershipEventKind.PLANNED_TRANSITION
    assert "search" not in " ".join(event.facts).casefold()


def test_an_active_voice_board_appointment_is_still_a_named_event() -> None:
    appointment = """\
Item 5.02 Departure of Directors or Certain Officers.
On April 8, 2026, the Board appointed Jane Example to serve as Chief Financial
Officer, effective immediately.
"""

    (event,) = parse_leadership_events(ADBE_CFO, appointment)

    assert event.kind is LeadershipEventKind.APPOINTMENT
    assert event.person == "Jane Example"
    assert event.effective_on == date(2026, 4, 8)


def test_a_person_role_and_transition_action_are_all_required() -> None:
    no_person = "The Company is conducting a search for a Chief Executive Officer."
    no_role = "Jane Example notified the Company of her decision to resign."
    no_action = "Jane Example is the Company's Chief Executive Officer."

    assert parse_leadership_events(ADBE_CEO, no_person) == ()
    assert parse_leadership_events(ADBE_CEO, no_role) == ()
    assert parse_leadership_events(ADBE_CEO, no_action) == ()


def test_the_item_locator_prefers_the_filed_body_over_the_contents_entry() -> None:
    document = f"""\
<html><body>
<p>Item 5.02 Executive changes</p><p>Item 7.01 Regulation FD</p>
<p>{CEO_ITEM}</p>
<p>Item 7.01 Regulation FD Disclosure.</p><p>Another exhibit was furnished.</p>
</body></html>
"""

    item = EdgarFilings.current_item(document, "5.02")

    assert "Shantanu Narayen" in item
    assert "Another exhibit" not in item


class _JsonResponse:
    def __init__(self, value: object) -> None:
        self._value = value

    def json(self) -> object:
        return self._value


def test_the_sec_index_selects_item_502_before_any_document_is_read() -> None:
    submissions = {
        "name": "ADOBE INC.",
        "filings": {
            "recent": {
                "form": ["8-K", "8-K", "10-K"],
                "filingDate": ["2026-06-11", "2026-03-12", "2026-01-12"],
                "accessionNumber": [
                    "0000796343-26-000109",
                    "0000796343-26-000048",
                    "0000796343-26-000003",
                ],
                "primaryDocument": [
                    "adbe-20260608.htm",
                    "adbe-20260309.htm",
                    "adbe-20251128.htm",
                ],
                "items": ["2.02,5.02,9.01", "2.02,5.02,7.01,9.01", ""],
            }
        },
    }
    filings = EdgarFilings()
    filings._cik = lambda ticker: 796343  # type: ignore[method-assign]
    filings._get = lambda url: _JsonResponse(submissions)  # type: ignore[method-assign]

    reports = filings.current_reports("adbe", "5.02", date(2026, 1, 1))

    assert [report.accession for report in reports] == [
        "0000796343-26-000109",
        "0000796343-26-000048",
    ]
    assert all(report.symbol == "ADBE" for report in reports)


class _Filings:
    def current_reports(
        self,
        symbol: str,
        item: str,
        since: date,
    ) -> tuple[CurrentReportReference, ...]:
        assert symbol == "ADBE"
        assert item == "5.02"
        assert since == date(2025, 2, 13)

        return (ADBE_CFO, ADBE_CEO)

    def read_current_item(self, report: CurrentReportReference, item: str) -> str:
        assert item == "5.02"

        return CFO_ITEM if report is ADBE_CFO else CEO_ITEM


def test_provider_reports_health_and_orders_the_newest_event_first() -> None:
    feed = SecLeadershipProvider(_Filings()).events(
        "ADBE", datetime(2026, 8, 17, tzinfo=UTC)
    )

    assert feed.is_read
    assert feed.health.reports_seen == 2
    assert feed.health.reports_read == 2
    assert feed.health.events_kept == 3
    assert feed.health.declined == ()
    assert feed.events[0].person == "Steven Day"
    assert feed.events[-1].person == "Shantanu Narayen"


class _Provider:
    def __init__(self, feed: LeadershipEventFeed) -> None:
        self.feed = feed
        self.calls = 0

    def events(self, symbol: str, now: datetime) -> LeadershipEventFeed:
        self.calls += 1

        return self.feed


def test_the_read_only_door_serves_storage_and_never_calls_the_provider(
    tmp_path: Path,
) -> None:
    cache = JsonCache(tmp_path, schema=1)
    acquired = SecLeadershipProvider(_Filings()).events(
        "ADBE", datetime(2026, 8, 17, tzinfo=UTC)
    )
    provider = _Provider(acquired)
    writer = LeadershipEventService(provider=provider, cache=cache)

    writer.acquire("ADBE", datetime(2026, 8, 17, tzinfo=UTC))

    reader_provider = _Provider(
        LeadershipEventFeed(health=LeadershipFeedHealth(source="wrong", reached=False))
    )
    reader = LeadershipEventService(
        provider=reader_provider,
        cache=cache,
        acquires=False,
    )
    held = reader.established("adbe")

    assert provider.calls == 1
    assert reader_provider.calls == 0
    assert [event.identity for event in held.events] == [
        event.identity for event in acquired.events
    ]
    assert held.health.stated == acquired.health.stated


def test_the_slice_cannot_reach_quality_decisions_or_a_model() -> None:
    for module in (
        "app/domain/leadership_event.py",
        "app/providers/sec_leadership_provider.py",
        "app/services/leadership_event_service.py",
        "app/commands/leadership.py",
    ):
        code = reachable(module, with_literals=True)

        for forbidden in (
            "quality_signal",
            "investmentdecision",
            "recommendation",
            "committeeopinion",
            "openai",
            "anthropic",
            "prompt",
        ):
            assert forbidden not in code, (module, forbidden)


def test_the_cli_separates_reading_from_explicit_acquisition() -> None:
    parser = cli.build_parser()

    read = parser.parse_args(["leadership", "ADBE", "--evidence"])
    acquire = parser.parse_args(["acquire-leadership", "ADBE"])

    assert (read.command, read.symbol, read.evidence) == (
        "leadership",
        "ADBE",
        True,
    )
    assert (acquire.command, acquire.symbol, acquire.evidence) == (
        "acquire-leadership",
        "ADBE",
        False,
    )
