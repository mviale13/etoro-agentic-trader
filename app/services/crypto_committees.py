"""Which committees exist. A list, and deliberately not more than one.

Earned by a failure rather than anticipated. With one committee, both
`movrvest judge` and `movrvest judgment-history` named `CONTRACT`
directly and were correct. With two, the history surface would have
printed Fee Capture's record and stopped — and a reader would have
concluded that the Supply Governance Committee had never judged
anything, which is a false statement assembled out of true parts.

So this module exists to answer two questions and no others: *which
committees are there*, and *which contract wrote this record*. It is a
tuple and a lookup.

**What it deliberately is not.** No priority, no ordering that means
anything, no weighting, no registration protocol, no plugin discovery,
no way to ask which committee matters more. Those would be the layer
above committees, and the whole point of stopping here is that the layer
above is supposed to be decided from the two-committee matrix rather
than sketched before it.

The order below is alphabetical by key, which is a rendering decision
and carries no meaning. A caller that needed a meaningful order would be
a caller doing something this platform has not earned.
"""

from __future__ import annotations

from app.domain.committee_protocol import Committee, CommitteeContract
from app.services.supply_governance_committee import (
    CONTRACT as SUPPLY_GOVERNANCE,
)
from app.services.supply_governance_committee import (
    SupplyGovernanceCommittee,
)
from app.services.value_capture_committee import CONTRACT as VALUE_CAPTURE
from app.services.value_capture_committee import ValueCaptureCommittee

#: Every committee's contract. Constants, so a surface can name a
#: committee without constructing one.
CONTRACTS: tuple[CommitteeContract, ...] = (SUPPLY_GOVERNANCE, VALUE_CAPTURE)


def committees() -> tuple[Committee, ...]:
    """Every committee, freshly built.

    A function rather than a module-level tuple because constructing a
    committee opens stores, and importing this module must not.
    """

    return (SupplyGovernanceCommittee(), ValueCaptureCommittee())


def contract_for(key: str) -> CommitteeContract | None:
    """The contract filed under this key, where one is still live.

    `None` is a real answer and the caller must handle it: a record
    written by a committee that has since been removed is still a record,
    and history reads it by key without needing the code that wrote it.
    """

    for contract in CONTRACTS:
        if contract.key == key:
            return contract

    return None
