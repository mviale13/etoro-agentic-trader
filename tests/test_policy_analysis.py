from app.domain.policy_analysis import (
    AllocationDifference,
    PolicyAnalysis,
)


def test_allocation_returns_none_for_unknown_asset():
    analysis = PolicyAnalysis(
        allocations=(
            AllocationDifference(
                asset="stocks",
                current=60,
                target=60,
                difference=0,
            ),
        ),
        compliant=True,
    )

    assert analysis.allocation("crypto") is None


def test_largest_deviation_returns_none_when_empty():
    analysis = PolicyAnalysis(
        allocations=(),
        compliant=True,
    )

    assert analysis.largest_deviation() is None
