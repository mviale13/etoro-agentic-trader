"""Acquire leadership events explicitly and serve stored evidence on read."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.domain.leadership_event import (
    ExecutiveRole,
    LeadershipEvent,
    LeadershipEventFeed,
    LeadershipEventKind,
    LeadershipFeedHealth,
    RegulatoryEventSource,
)
from app.domain.primary_source import SourceAuthority
from app.infrastructure.cache.json_cache import JsonCache
from app.infrastructure.evidence_root import evidence_path
from app.providers.sec_leadership_provider import SecLeadershipProvider


class LeadershipEventService:
    """The stored door and the explicit acquisition door for one company."""

    SCHEMA = 1

    def __init__(
        self,
        provider: SecLeadershipProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or SecLeadershipProvider()
        self._cache = cache or JsonCache(
            evidence_path("cache", "leadership_events"),
            schema=self.SCHEMA,
        )
        self._acquires = acquires

    @classmethod
    def stored(cls, cache: JsonCache | None = None) -> LeadershipEventService:
        """A read-only service that can never reach the SEC."""

        return cls(cache=cache, acquires=False)

    def established(self, symbol: str) -> LeadershipEventFeed:
        """What an earlier explicit acquisition stored, and nothing else."""

        entry = self._cache.read(_cache_key(symbol))

        return _decode(entry.value) if entry is not None else LeadershipEventFeed()

    def acquire(
        self,
        symbol: str,
        now: datetime | None = None,
    ) -> LeadershipEventFeed:
        """Read recent Item 5.02 filings once and store the resulting feed."""

        if not self._acquires:
            return self.established(symbol)

        feed = self._provider.events(symbol.upper().strip(), now or datetime.now(UTC))

        self._cache.write(_cache_key(symbol), _encode(feed))

        return feed


def _cache_key(symbol: str) -> str:
    return f"leadership.{symbol.upper().strip()}"


def _encode(feed: LeadershipEventFeed) -> dict[str, Any]:
    return {
        "events": [
            {
                "identity": event.identity,
                "symbol": event.symbol,
                "company": event.company,
                "role": event.role.value,
                "person": event.person,
                "kind": event.kind.value,
                "occurred_on": event.occurred_on.isoformat(),
                "effective_on": (
                    event.effective_on.isoformat() if event.effective_on else None
                ),
                "facts": list(event.facts),
                "source": {
                    "regulator": event.source.regulator,
                    "form": event.source.form,
                    "item": event.source.item,
                    "accession": event.source.accession,
                    "filed_on": event.source.filed_on.isoformat(),
                    "url": event.source.url,
                    "authority": event.source.authority.value,
                },
            }
            for event in feed.events
        ],
        "health": {
            "source": feed.health.source,
            "reached": feed.health.reached,
            "reports_seen": feed.health.reports_seen,
            "reports_read": feed.health.reports_read,
            "events_kept": feed.health.events_kept,
            "declined": list(feed.health.declined),
            "unreadable": list(feed.health.unreadable),
            "because": feed.health.because,
        },
    }


def _decode(row: Any) -> LeadershipEventFeed:
    if not isinstance(row, dict):
        return LeadershipEventFeed()

    events: list[LeadershipEvent] = []

    for item in row.get("events") or []:
        event = _decode_event(item)

        if event is not None:
            events.append(event)

    health_row = row.get("health")

    if not isinstance(health_row, dict):
        return LeadershipEventFeed(events=tuple(events))

    health = LeadershipFeedHealth(
        source=str(health_row.get("source") or "SEC EDGAR"),
        reached=bool(health_row.get("reached")),
        reports_seen=int(health_row.get("reports_seen") or 0),
        reports_read=int(health_row.get("reports_read") or 0),
        events_kept=int(health_row.get("events_kept") or 0),
        declined=tuple(str(item) for item in health_row.get("declined") or ()),
        unreadable=tuple(str(item) for item in health_row.get("unreadable") or ()),
        because=(
            str(health_row["because"])
            if health_row.get("because") is not None
            else None
        ),
    )

    return LeadershipEventFeed(events=tuple(events), health=health)


def _decode_event(row: Any) -> LeadershipEvent | None:
    if not isinstance(row, dict) or not isinstance(row.get("source"), dict):
        return None

    source = row["source"]

    try:
        return LeadershipEvent(
            identity=str(row["identity"]),
            symbol=str(row["symbol"]),
            company=str(row["company"]),
            role=ExecutiveRole(row["role"]),
            person=str(row["person"]),
            kind=LeadershipEventKind(row["kind"]),
            occurred_on=date.fromisoformat(str(row["occurred_on"])),
            effective_on=(
                date.fromisoformat(str(row["effective_on"]))
                if row.get("effective_on")
                else None
            ),
            source=RegulatoryEventSource(
                regulator=str(source["regulator"]),
                form=str(source["form"]),
                item=str(source["item"]),
                accession=str(source["accession"]),
                filed_on=date.fromisoformat(str(source["filed_on"])),
                url=str(source["url"]),
                authority=SourceAuthority(source["authority"]),
            ),
            facts=tuple(str(fact) for fact in row.get("facts") or ()),
        )
    except (KeyError, TypeError, ValueError):
        return None
