from app.domain.committee_member_performance import (
    CommitteeMemberPerformance,
)
from app.domain.committee_member_statistics import (
    CommitteeMemberStatistics,
)
from app.domain.committee_outcome import is_recommendation_successful
from app.domain.committee_performance import CommitteePerformance
from app.domain.committee_statistics import CommitteeStatistics
from app.domain.event import Event
from app.domain.event_type import EventType
from app.domain.market_regime import MarketRegimeType
from app.domain.regime_member_performance import RegimeMemberPerformance
from app.repositories.event_repository import EventRepository


class CommitteeAnalyticsService:
    """
    Provides historical analytics over committee recommendations,
    member performance, recommendation outcomes, and market-regime
    statistics using the event store.
    """

    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def statistics(self) -> CommitteeStatistics:
        events = self._recommendation_events()

        if not events:
            return CommitteeStatistics(
                recommendations=0,
                buy=0,
                hold=0,
                sell=0,
                average_confidence=0,
            )

        buy = sum(event.payload.get("recommendation") == "BUY" for event in events)
        hold = sum(event.payload.get("recommendation") == "HOLD" for event in events)
        sell = sum(event.payload.get("recommendation") == "SELL" for event in events)

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
        members: dict[str, list[dict[str, object]]] = {}

        for event in self._recommendation_events():
            for vote in self._votes(event):
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

    def performance(self) -> CommitteePerformance:
        recommendation_events = self._recommendation_events()
        outcome_events = self._outcome_events()

        successful = sum(
            event.payload.get("successful") is True for event in outcome_events
        )
        completed = len(outcome_events)

        accuracy = round((successful / completed) * 100) if completed else 0

        return CommitteePerformance(
            recommendations=len(recommendation_events),
            completed=completed,
            successful=successful,
            accuracy=accuracy,
        )

    def member_performance(
        self,
    ) -> list[CommitteeMemberPerformance]:
        recommendation_events = {
            self._recommendation_key(event): event
            for event in self._recommendation_events()
        }

        results: dict[str, dict[str, int]] = {}

        for outcome in self._outcome_events():
            recommendation = recommendation_events.get(self._outcome_key(outcome))

            if recommendation is None:
                continue

            return_pct = outcome.payload.get("return_pct")

            if not isinstance(return_pct, (int, float)):
                continue

            for vote in self._votes(recommendation):
                member = str(vote.get("member", "Unknown"))
                member_vote = vote.get("vote")

                if not isinstance(member_vote, str):
                    continue

                member_result = results.setdefault(
                    member,
                    {
                        "completed": 0,
                        "successful": 0,
                    },
                )

                member_result["completed"] += 1

                if is_recommendation_successful(
                    member_vote,
                    float(return_pct),
                ):
                    member_result["successful"] += 1

        performance: list[CommitteeMemberPerformance] = []

        for member, result in sorted(results.items()):
            completed = result["completed"]
            successful = result["successful"]

            accuracy = round((successful / completed) * 100) if completed else 0

            performance.append(
                CommitteeMemberPerformance(
                    member=member,
                    completed=completed,
                    successful=successful,
                    accuracy=accuracy,
                )
            )

        return performance

    def member_performance_by_regime(
        self,
    ) -> list[RegimeMemberPerformance]:
        recommendation_events = {
            self._recommendation_key(event): event
            for event in self._recommendation_events()
        }

        results: dict[
            tuple[str, MarketRegimeType],
            dict[str, int],
        ] = {}

        for outcome in self._outcome_events():
            recommendation = recommendation_events.get(self._outcome_key(outcome))

            if recommendation is None:
                continue

            return_pct = outcome.payload.get("return_pct")

            if not isinstance(return_pct, (int, float)):
                continue

            regime_value = recommendation.payload.get(
                "regime",
                MarketRegimeType.SIDEWAYS.value,
            )

            try:
                regime = MarketRegimeType(str(regime_value))
            except ValueError:
                regime = MarketRegimeType.SIDEWAYS

            for vote in self._votes(recommendation):
                member = str(vote.get("member", "Unknown"))
                member_vote = vote.get("vote")

                if not isinstance(member_vote, str):
                    continue

                key = (member, regime)

                result = results.setdefault(
                    key,
                    {
                        "completed": 0,
                        "successful": 0,
                    },
                )

                result["completed"] += 1

                if is_recommendation_successful(
                    member_vote,
                    float(return_pct),
                ):
                    result["successful"] += 1

        performance: list[RegimeMemberPerformance] = []

        for (member, regime), result in sorted(
            results.items(),
            key=lambda item: (
                item[0][0],
                item[0][1].value,
            ),
        ):
            completed = result["completed"]
            successful = result["successful"]

            accuracy = round((successful / completed) * 100) if completed else 0

            performance.append(
                RegimeMemberPerformance(
                    member=member,
                    regime=regime,
                    completed=completed,
                    successful=successful,
                    accuracy=accuracy,
                )
            )

        return performance

    def _recommendation_events(self) -> list[Event]:
        return [
            event
            for event in self._repository.load_all()
            if event.event_type == EventType.RECOMMENDATION_GENERATED
        ]

    def _outcome_events(self) -> list[Event]:
        return [
            event
            for event in self._repository.load_all()
            if event.event_type == EventType.RECOMMENDATION_OUTCOME_RECORDED
        ]

    @staticmethod
    def _votes(
        event: Event,
    ) -> list[dict[str, object]]:
        votes = event.payload.get("votes", [])

        if not isinstance(votes, list):
            return []

        return [vote for vote in votes if isinstance(vote, dict)]

    @staticmethod
    def _recommendation_key(
        event: Event,
    ) -> tuple[str | None, str]:
        return (
            event.symbol,
            event.timestamp.isoformat(),
        )

    @staticmethod
    def _outcome_key(
        event: Event,
    ) -> tuple[str | None, str]:
        timestamp = event.payload.get("recommendation_timestamp")

        return (
            event.symbol,
            str(timestamp),
        )
