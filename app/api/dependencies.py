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


def get_brain_builder_service() -> BrainBuilderService:
    """The canonical Brain composition root, reached by the reasoning routes."""

    return BrainBuilderService()


def get_brain_snapshot_service() -> BrainSnapshotService:
    """The factual snapshot the dashboard is served from."""

    return BrainSnapshotService()
