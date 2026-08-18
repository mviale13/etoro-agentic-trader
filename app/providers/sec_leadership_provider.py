"""Executive leadership changes filed under SEC Form 8-K Item 5.02.

The submissions index supplies the selection: only filings the regulator
itself labels Item 5.02 are fetched.  The filed item is then narrowed to
sentences that name both an executive office and a transition action.
That second condition matters because Item 5.02 also contains director
elections and compensation changes, neither of which establishes a
leadership-continuity event.

No model is asked.  The vocabulary is intentionally small and measured on
the first acceptance case: Adobe's open CEO search, its later CFO departure,
and the interim CFO appointment filed beside it.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, date, datetime, timedelta

from app.domain.leadership_event import (
    ExecutiveRole,
    LeadershipEvent,
    LeadershipEventFeed,
    LeadershipEventKind,
    LeadershipFeedHealth,
    RegulatoryEventSource,
)
from app.providers.edgar_filings import (
    CurrentReportReference,
    EdgarFilings,
    FilingUnavailable,
)

SOURCE = "SEC EDGAR"
ITEM = "5.02"
LOOKBACK_DAYS = 550

_SENTENCE = re.compile(
    r"(?<!Mr\.)(?<!Ms\.)(?<!Dr\.)(?<!Mrs\.)(?<=[.!?])\s+(?=[A-Z0-9])"
)
_DATE = r"[A-Z][a-z]+\s+\d{1,2},\s+\d{4}"

_PERSON_ACTION = re.compile(
    rf"(?:On\s+{_DATE},\s+)?"
    r"(?P<person>[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+"
    r"(?:\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+){1,4})\s+"
    r"(?:notified|informed|has\s+notified|has\s+informed|"
    r"was\s+appointed|has\s+been\s+appointed|will\s+be\s+appointed|"
    r"was\s+named|has\s+been\s+named|will\s+be\s+named|"
    r"resigned|has\s+resigned|retired|has\s+retired|will\s+retire|"
    r"is\s+retiring|departed|will\s+depart)",
)

_PERSON_AFTER_APPOINTMENT = re.compile(
    r"(?i:appointed|named|elected)\s+"
    r"(?P<person>[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+"
    r"(?:\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+){1,4})\s+"
    r"(?:to\s+serve\s+as|as)\b",
)

_ROLE_PATTERNS = (
    (
        ExecutiveRole.CHIEF_EXECUTIVE,
        re.compile(r"(?i)\b(?:chief\s+executive\s+officer|CEO)\b"),
    ),
    (
        ExecutiveRole.CHIEF_FINANCIAL,
        re.compile(r"(?i)\b(?:chief\s+financial\s+officer|CFO)\b"),
    ),
    (
        ExecutiveRole.CHIEF_OPERATING,
        re.compile(r"(?i)\b(?:chief\s+operating\s+officer|COO)\b"),
    ),
    (
        ExecutiveRole.PRESIDENT,
        # A CFO who is also an Executive Vice President is captured by the
        # more specific role above before this fallback is considered.
        re.compile(r"(?i)\bpresident\b"),
    ),
)

_DEPARTURE = (
    "decision to resign",
    "has resigned",
    "resigned as",
    "decision to retire",
    "will retire",
    "is retiring",
    "has retired",
    "departed",
    "will depart",
    "termination of",
    "was terminated",
)


class SecLeadershipProvider:
    """Read the covered leadership events in recent SEC current reports."""

    def __init__(self, filings: EdgarFilings | None = None) -> None:
        self._filings = filings or EdgarFilings()

    def events(
        self,
        symbol: str,
        now: datetime | None = None,
    ) -> LeadershipEventFeed:
        moment = now or datetime.now(UTC)
        since = moment.date() - timedelta(days=LOOKBACK_DAYS)

        try:
            reports = self._filings.current_reports(symbol, ITEM, since)
        except FilingUnavailable as unavailable:
            return LeadershipEventFeed(
                health=LeadershipFeedHealth(
                    source=SOURCE,
                    reached=False,
                    because=str(unavailable),
                )
            )

        events: list[LeadershipEvent] = []
        declined: list[str] = []
        unreadable: list[str] = []
        reports_read = 0

        for report in reports:
            try:
                text = self._filings.read_current_item(report, ITEM)
            except Exception:
                unreadable.append(
                    f"{report.accession}: the filed Item {ITEM} could not be read"
                )
                continue

            reports_read += 1

            if not text:
                unreadable.append(
                    f"{report.accession}: the filed Item {ITEM} could not be located"
                )
                continue

            parsed = parse_leadership_events(report, text)

            if not parsed:
                declined.append(
                    f"{report.accession}: no covered executive transition was stated"
                )
                continue

            events.extend(parsed)

        # A permanent appointment filed after a search is shown first, so a
        # reader sees the newest state without any event being overwritten.
        events.sort(
            key=lambda event: (
                event.occurred_on,
                event.source.filed_on,
                event.identity,
            ),
            reverse=True,
        )

        return LeadershipEventFeed(
            events=tuple(events),
            health=LeadershipFeedHealth(
                source=SOURCE,
                reached=True,
                reports_seen=len(reports),
                reports_read=reports_read,
                events_kept=len(events),
                declined=tuple(declined),
                unreadable=tuple(unreadable),
            ),
        )


def parse_leadership_events(
    report: CurrentReportReference,
    text: str,
) -> tuple[LeadershipEvent, ...]:
    """The executive transitions plainly stated in one filed Item 5.02.

    Classification is conjunctive: a sentence must name a covered role,
    carry a transition action, and name the person taking that action.
    Missing any one of the three leaves it out.  That is how compensation
    arrangements and director elections remain Item 5.02 facts without
    becoming leadership-continuity events.
    """

    sentences = tuple(
        sentence.strip()
        for sentence in _SENTENCE.split(_plain(text))
        if sentence.strip() and not sentence.lstrip().casefold().startswith("item 5.02")
    )

    triggers: list[tuple[int, str, ExecutiveRole, LeadershipEventKind, str]] = []

    for index, sentence in enumerate(sentences):
        role = _role_of(sentence)
        kind = _kind_of(sentence)
        person = _person_in(sentence)

        if role is None or kind is None or person is None:
            continue

        triggers.append((index, sentence, role, kind, person))

    events: list[LeadershipEvent] = []

    for position, (index, sentence, role, kind, person) in enumerate(triggers):
        next_trigger = (
            triggers[position + 1][0]
            if position + 1 < len(triggers)
            else len(sentences)
        )
        facts = [sentence]

        # Keep the filed sentences that qualify the action -- an open search,
        # remaining in office until the successor arrives, staying as chair.
        # Stop at the next separately-classified action so two executives do
        # not borrow one another's evidence.
        for related in sentences[index + 1 : min(next_trigger, index + 4)]:
            folded = related.casefold()

            if any(
                marker in folded
                for marker in (
                    "successor",
                    "conducting a search",
                    "search committee",
                    "will remain",
                    "continue to serve",
                    "board of directors",
                )
            ):
                facts.append(related)

        kind = _qualified_kind(kind, facts)
        occurred = _leading_date(sentence) or report.filed_on
        effective = _effective_date(sentence, occurred)
        identity = "|".join(
            (
                report.accession,
                role.value,
                kind.value,
                _key(person),
            )
        )

        events.append(
            LeadershipEvent(
                identity=identity,
                symbol=report.symbol,
                company=report.company,
                role=role,
                person=person,
                kind=kind,
                occurred_on=occurred,
                effective_on=effective,
                source=RegulatoryEventSource(
                    regulator=SOURCE,
                    form=report.form,
                    item=ITEM,
                    accession=report.accession,
                    filed_on=report.filed_on,
                    url=report.url,
                ),
                facts=tuple(facts),
            )
        )

    return tuple(events)


def _role_of(sentence: str) -> ExecutiveRole | None:
    for role, pattern in _ROLE_PATTERNS:
        if pattern.search(sentence):
            return role

    return None


def _kind_of(sentence: str) -> LeadershipEventKind | None:
    folded = sentence.casefold()

    appointment = any(word in folded for word in ("appointed", "named", "elected"))

    if appointment and "interim" in folded:
        return LeadershipEventKind.INTERIM_APPOINTMENT

    if "decision to transition" in folded or "transition from" in folded:
        return LeadershipEventKind.PLANNED_TRANSITION

    if appointment:
        return LeadershipEventKind.APPOINTMENT

    if any(marker in folded for marker in _DEPARTURE):
        return LeadershipEventKind.DEPARTURE

    return None


def _qualified_kind(
    kind: LeadershipEventKind,
    facts: list[str],
) -> LeadershipEventKind:
    """A planned transition is a search only when the filing says so."""

    if kind is not LeadershipEventKind.PLANNED_TRANSITION:
        return kind

    folded = " ".join(facts).casefold()

    if "successor" in folded or "conducting a search" in folded:
        return LeadershipEventKind.SUCCESSION_SEARCH

    return kind


def _person_in(sentence: str) -> str | None:
    match = _PERSON_ACTION.search(sentence) or _PERSON_AFTER_APPOINTMENT.search(
        sentence
    )

    return match.group("person").strip() if match else None


def _leading_date(sentence: str) -> date | None:
    match = re.match(rf"On\s+(?P<date>{_DATE}),", sentence)

    return _parsed_date(match.group("date")) if match else None


def _effective_date(sentence: str, occurred_on: date) -> date | None:
    if re.search(r"(?i)effective\s+immediately(?!\s+upon)", sentence):
        return occurred_on

    match = re.search(rf"(?i)effective\s+(?:on\s+)?(?P<date>{_DATE})", sentence)

    return _parsed_date(match.group("date")) if match else None


def _parsed_date(value: str) -> date | None:
    for shape in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, shape).date()
        except ValueError:
            continue

    return None


def _plain(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def _key(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).casefold()

    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
