from fastapi import APIRouter

from app.api.models.committee_member_statistics import (
    CommitteeMemberStatisticsResponse,
)
from app.api.models.committee_statistics import (
    CommitteeStatisticsResponse,
)
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)

router = APIRouter(
    prefix="/committee",
    tags=["committee"],
)


@router.get(
    "/statistics",
    response_model=CommitteeStatisticsResponse,
)
async def get_committee_statistics() -> CommitteeStatisticsResponse:
    statistics = CommitteeAnalyticsService(
        JsonEventRepository(),
    ).statistics()

    return CommitteeStatisticsResponse(
        recommendations=statistics.recommendations,
        buy=statistics.buy,
        hold=statistics.hold,
        sell=statistics.sell,
        average_confidence=statistics.average_confidence,
    )


@router.get(
    "/members",
    response_model=list[CommitteeMemberStatisticsResponse],
)
async def get_committee_members() -> list[CommitteeMemberStatisticsResponse]:
    members = CommitteeAnalyticsService(
        JsonEventRepository(),
    ).member_statistics()

    return [
        CommitteeMemberStatisticsResponse(
            member=item.member,
            recommendations=item.recommendations,
            buy=item.buy,
            hold=item.hold,
            sell=item.sell,
            average_confidence=item.average_confidence,
        )
        for item in members
    ]
