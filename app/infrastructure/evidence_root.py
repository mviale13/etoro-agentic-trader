"""Where evidence lives on disk, asked once instead of assumed seventeen times.

Every store and cache on this platform used to name its own path as a
string literal relative to the process's working directory —
`data/cache/protocol_facts`, `data/judgments`, `data/journal`. Seventeen
of them, each correct in production and each an undeclared input
everywhere else.

**That is the whole shape of the gitignored-cache trap, and it happened
five times.** A test constructs an analytical service with no arguments,
the service defaults its evidence door to one of those literals, and the
answer depends on whatever the developer happened to have acquired. It
passes locally, fails on a clean checkout, and — measured on this
repository — a cache edited by hand flips Cardano's supply-governance
verdict from `governance_set` to `consensus_bound` with the caller
having declared no evidence at all.

So the root is asked for rather than assumed. One function, one
environment variable, and every default path built from it:

```python
JsonCache(evidence_path("cache", "issuance_rules"), schema=SCHEMA)
```

The test suite points `MOVRVEST_EVIDENCE_ROOT` at a temporary directory,
which makes ambient developer state unreadable **and unwritable** by
accident — the second half matters, because running the suite was
observed creating `data/cache/fx` in the developer's own tree.

**This is not a cache switch.** Caching stays exactly as it was and
production reads exactly what it read before. What changes is that the
location is a declared input with one owner, so it can be redirected in
one place and audited in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

#: The environment variable that relocates every evidence store.
#:
#: Set by the test suite to a temporary directory. Unset in production,
#: where the default below is what this platform has always used.
ROOT_ENV = "MOVRVEST_EVIDENCE_ROOT"

#: Where evidence lives when nobody says otherwise.
DEFAULT_ROOT = "data"


def evidence_root() -> Path:
    """The directory every evidence store hangs from.

    Read on each call rather than captured at import, because the test
    suite redirects it per test and a value frozen at import time would
    silently ignore the redirection — which is the same class of bug
    this module exists to remove.
    """

    return Path(os.environ.get(ROOT_ENV) or DEFAULT_ROOT)


def evidence_path(*parts: str) -> Path:
    """A path beneath the evidence root.

    `evidence_path("cache", "quotes")` is `data/cache/quotes` in
    production and something disposable under test. Callers pass path
    *segments* rather than a joined string so nothing has to know the
    separator or the root.
    """

    return evidence_root().joinpath(*parts)
