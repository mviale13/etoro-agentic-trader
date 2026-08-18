"""Acquire or inspect regulator-filed executive leadership changes."""

from __future__ import annotations

from app.domain.leadership_event import LeadershipEvent
from app.services.leadership_event_service import LeadershipEventService


class LeadershipCommand:
    def __init__(self, service: LeadershipEventService | None = None) -> None:
        self._service = service

    def run(
        self,
        symbol: str,
        evidence: bool = False,
        acquire: bool = False,
    ) -> int:
        normalized = symbol.upper().strip()
        service = self._service or (
            LeadershipEventService() if acquire else LeadershipEventService.stored()
        )
        feed = (
            service.acquire(normalized) if acquire else service.established(normalized)
        )

        print(f"{normalized} — leadership developments")
        print()

        if not feed.is_read:
            print(
                "  No regulator-filed leadership reading is held. "
                "`movrvest acquire-leadership SYMBOL` reads SEC Item 5.02 "
                "as an explicit spend."
            )
        elif not feed.events:
            print(
                "  The SEC surface was read and no covered executive transition "
                "was stated in the recent Item 5.02 reports."
            )
        else:
            print(
                "  Events only — no management-quality or investment conclusion "
                "is made here."
            )
            print()

            for event in feed.events:
                _render(event, evidence)

        print()
        print(f"  Surface: {feed.health.stated}")

        if evidence:
            for reason in feed.health.declined:
                print(f"    declined: {reason}")

            for reason in feed.health.unreadable:
                print(f"    unreadable: {reason}")

        return 0 if feed.is_read else 1


def _render(event: LeadershipEvent, evidence: bool) -> None:
    effective = (
        f" · effective {event.effective_on.isoformat()}"
        if event.effective_on is not None
        else ""
    )
    open_transition = (
        " · this event names no permanent successor"
        if event.kind.names_no_permanent_successor
        else ""
    )

    print(f"  · [{event.kind.stated}] {event.role.stated} — {event.person}")
    print(
        f"      occurred {event.occurred_on.isoformat()} · "
        f"filed {event.source.filed_on.isoformat()}{effective}{open_transition}"
    )

    for fact in event.facts:
        print(f"      fact: {fact}")

    if evidence:
        print(
            f"      source: {event.source.form} Item {event.source.item} "
            f"{event.source.accession} — {event.source.url}"
        )
        print(f"      identity: {event.identity}")

    print()


async def run(
    symbol: str,
    evidence: bool = False,
    acquire: bool = False,
) -> int:
    return LeadershipCommand().run(symbol, evidence=evidence, acquire=acquire)
