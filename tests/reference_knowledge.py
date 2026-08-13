"""The committed JPM observations, read the way a test may read them.

Two tests decide investment questions against a real quorate consensus
rather than a synthetic one, and JPM's committed entry in
`data/knowledge/` is that reference. They reached it through
`JsonCompanyKnowledgeStore()` — whose directory defaults to the path
literal `data/knowledge` — which is the shape `HERMETIC_EVIDENCE.md`
exists to end: the call declared a *subject* and never an *evidence
set*, so the suite was answering from whichever readings the developer's
tree happened to hold, and `tests/conftest.py`'s hermetic root could not
see it to redirect it.

This declares the evidence instead. The committed file is read from the
repository by path, restamped to the current protocol inside a
temporary directory that lives and dies with the call, and served from
there — so the fixture is explicit, the developer's tree is only ever
read, and a schema bump changes one constant here rather than breaking
two suites.

**Why restamping is sound rather than convenient.** The version stamps
a protocol, and the protocol that moved at 14 is the ownership
partition: the filer's own name run into a segment's name no longer
opens that segment's region. That rule is measured to fire **zero
times** on this document — its identity words (*JPMorgan*, *Chase*,
*Co*) never precede a naming of `Consumer & Community Banking`,
`Commercial & Investment Bank` or `Asset & Wealth Management` — so
every description in this entry is owned by exactly the segment it was
owned by when it was read. Nothing is reinterpreted, and the claim is
checkable: `test_the_reference_entry_is_partition_stable` asserts it
rather than trusting this paragraph.

A company whose readings the partition *would* move must not be
restamped. It must be read again.
"""

from __future__ import annotations

import json
import tempfile
from functools import cache
from pathlib import Path

from app.domain.company_knowledge import CompanyKnowledgeObservation
from app.repositories.company_knowledge_store import (
    KNOWLEDGE_SCHEMA_VERSION,
    JsonCompanyKnowledgeStore,
)

#: The repository's own knowledge directory, named once. Not an evidence
#: root: this is a committed fixture read by path, never a store the
#: platform acquires into.
COMMITTED = Path(__file__).resolve().parent.parent / "data" / "knowledge"

REFERENCE_SYMBOL = "JPM"


@cache
def reference_observations(
    symbol: str = REFERENCE_SYMBOL,
) -> tuple[CompanyKnowledgeObservation, ...]:
    """The committed observations for this company, at the current protocol.

    The restamped copy lives inside a temporary directory that is
    removed before this returns, so the committed file is only ever
    read and nothing outside the repository survives the call.
    """

    entries = [
        path
        for path in COMMITTED.glob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("symbol") == symbol
    ]

    assert entries, f"{symbol} is the committed reference fixture and is missing"

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)

        for path in entries:
            stored = json.loads(path.read_text(encoding="utf-8"))
            stored["schema_version"] = KNOWLEDGE_SCHEMA_VERSION
            (root / path.name).write_text(json.dumps(stored), encoding="utf-8")

        observations = JsonCompanyKnowledgeStore(directory=root).latest(symbol)

    assert observations, f"the committed {symbol} knowledge did not restore"

    return observations
