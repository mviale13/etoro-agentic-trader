from app.application.brain.perception.market_perception import MarketPerception
from app.application.change_feed.market_change_service import MarketChangeService
from app.application.market import MarketSnapshotArchive
from app.renderers.market_renderer import MarketRenderer


async def run(
    *,
    perception: MarketPerception | None = None,
    archive: MarketSnapshotArchive | None = None,
) -> int:
    # The one path that turns quotes into a canonical observation, records
    # it, and reads the sentiment index. `movrvest market` used to fetch and
    # discard on a path of its own, so running it never advanced the archive
    # and could never say what moved. Perception and archive share one
    # instance so the reading just filed is the one compared against.
    archive = archive or MarketSnapshotArchive()
    perception = perception or MarketPerception(archive=archive)

    try:
        snapshot = await perception.execute()
    except Exception as exc:
        print(f"MOVRvest market snapshot failed: {exc}")
        return 1

    # The two most recently recorded observations, newest first — the same
    # pair the dashboard change feed compares. One observation is not a
    # movement, and a fresh clone honestly has only one.
    recorded = archive.recent(2)

    if len(recorded) >= 2:
        current, previous = recorded[0], recorded[1]
        changes = MarketChangeService().changes(previous, current)
        previous_at = previous.timestamp
    else:
        changes = ()
        previous_at = None

    MarketRenderer.render(snapshot, changes=changes, previous_at=previous_at)
    return 0
