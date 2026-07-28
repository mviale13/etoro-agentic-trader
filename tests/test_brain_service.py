import inspect

from app.services.brain_service import BrainService


def test_brain_service_build_is_async() -> None:
    assert inspect.iscoroutinefunction(
        BrainService.build,
    )
