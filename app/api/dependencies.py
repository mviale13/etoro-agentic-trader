"""Injectable seams for the API routes.

A handler that builds its services inline reaches for the network the moment
it is called, so the routing, validation, response shape and error handling
around it cannot be exercised without it. Declaring those services as FastAPI
dependencies moves construction to one place a test can override through
`app.dependency_overrides`: the route runs against a stub offline, and the
service behind it is tested on its own terms.

Only the network-coupled composition roots belong here. A route's own
serialization and its error branches stay in the route, now reachable.
"""

from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.brain.brain_snapshot_service import BrainSnapshotService
from app.application.brain.perception.market_perception import MarketPerception
from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.services.account_service import AccountService
from app.services.brief_service import BriefService
from app.services.dashboard_service import DashboardService


def get_brain_builder_service() -> BrainBuilderService:
    """The canonical Brain composition root, reached by the reasoning routes."""

    return BrainBuilderService()


def get_brain_snapshot_service() -> BrainSnapshotService:
    """The factual snapshot the dashboard is served from."""

    return BrainSnapshotService()


def get_account_service() -> AccountService:
    """The eToro account snapshot behind the portfolio view."""

    return AccountService(EtoroAccountBroker(Settings()))


def get_brief_service() -> BriefService:
    """The morning brief the today route serves."""

    return BriefService()


def get_market_perception() -> MarketPerception:
    """The one place a market snapshot is assembled, behind the market route."""

    return MarketPerception()


def get_dashboard_service() -> DashboardService:
    """The composite the dashboard route passes through."""

    return DashboardService()
