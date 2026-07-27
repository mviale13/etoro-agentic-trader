from app.domain.committee_member_statistics import (
    CommitteeMemberStatistics,
)
from app.domain.committee_statistics import CommitteeStatistics
from app.domain.event_type import EventType
from app.repositories.event_repository import EventRepository


class CommitteeAnalyticsService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def statistics(self) -> CommitteeStatistics:
        events = [
            event
            for event in self._repository.load_all()
            if event.event_type == EventType.RECOMMENDATION_GENERATED
        ]

        if not events:
            return CommitteeStatistics(
                recommendations=0,
                buy=0,
                hold=0,
                sell=0,
                average_confidence=0,
            )

        buy = sum(event.payload["recommendation"] == "BUY" for event in events)
        hold = sum(event.payload["recommendation"] == "HOLD" for event in events)
        sell = sum(event.payload["recommendation"] == "SELL" for event in events)

        confidence_values = [
            value
            for event in events
            if isinstance(
                value := event.payload.get("confidence"),
                int,
            )
        ]

        average_confidence = (
            round(sum(confidence_values) / len(confidence_values))
            if confidence_values
            else 0
        )

        return CommitteeStatistics(
            recommendations=len(events),
            buy=buy,
            hold=hold,
            sell=sell,
            average_confidence=average_confidence,
        )

    def member_statistics(
        self,
    ) -> list[CommitteeMemberStatistics]:
        events = [
            event
            for event in self._repository.load_all()
            if event.event_type == EventType.RECOMMENDATION_GENERATED
        ]

        members: dict[str, list[dict[str, object]]] = {}

        for event in events:
            votes = event.payload.get("votes", [])

            if not isinstance(votes, list):
                continue

            for vote in votes:
                if not isinstance(vote, dict):
                    continue

                member = str(vote.get("member", "Unknown"))
                members.setdefault(member, []).append(vote)

        statistics: list[CommitteeMemberStatistics] = []

        for member, votes in sorted(members.items()):
            buy = sum(vote.get("vote") == "BUY" for vote in votes)
            hold = sum(vote.get("vote") == "HOLD" for vote in votes)
            sell = sum(vote.get("vote") == "SELL" for vote in votes)

            confidence_values = [
                value
                for vote in votes
                if isinstance(
                    value := vote.get("confidence"),
                    int,
                )
            ]

            average_confidence = (
                round(sum(confidence_values) / len(confidence_values))
                if confidence_values
                else 0
            )

            statistics.append(
                CommitteeMemberStatistics(
                    member=member,
                    recommendations=len(votes),
                    buy=buy,
                    hold=hold,
                    sell=sell,
                    average_confidence=average_confidence,
                )
            )

        return statistics
