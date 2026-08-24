"""What happened on one explicit company-knowledge acquisition attempt.

**Two dimensions, never collapsed into one availability boolean.** A
consumer asking about a company needs both, and they answer different
questions:

1. **Usable knowledge** — the latest restorable
   `CompanyKnowledgeConsensus`, if any. Owned by the knowledge store,
   unchanged by this module.
2. **The latest acquisition outcome** — the typed result of the latest
   explicit attempt, with its time and a safe reason. Owned here.

The measurement that earned it (`SECURITY_SPECIFIC_EVIDENCE_SUFFICIENCY.md`):
`CompanyKnowledgeService.established()` — the read-only door every
decision path uses — can return only `AVAILABLE_CACHED` or
`UNAVAILABLE`. `PROVIDER_ERROR`, `INVALID_EXTRACTION` and
`DOCUMENT_REFUSED` are computed at acquisition and **discarded**, and a
search of the whole evidence root found no stored occurrence of any of
them. So at the point of decision, *a filing whose section was
structurally refused* and *a company nobody has ever looked at* were the
same fact.

The pairs this makes expressible, none of which a single flag can hold:

- provider error **with** last year's knowledge — usable knowledge
  exists, and the latest attempt failed transiently;
- document refusal **with** older knowledge — usable knowledge exists,
  and the latest attempt was refused structurally;
- invalid extraction — earlier grounded observations are untouched;
- no knowledge and **no recorded attempt** — never recorded, which is
  neither a provider error nor a refusal.

**A read-only page request is not an acquisition attempt** and appends
nothing.

**`KnowledgeState` is not overloaded.** `observe()` legitimately returns
`AVAILABLE_ACQUIRED` when some observations were taken and a later
extraction was refused — the knowledge is real and the run ended in a
refusal, and no single state can say both. `ended_in_refusal` carries
the second half beside the state rather than inventing a seventh member
that would be a lie in the other direction.

Nothing here is decision-bearing. This slice persists facts; the slice
after it decides what typed breadth and persisted outcome authority do
about `evidence_score`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.domain.knowledge_state import KnowledgeState

#: What a canonical MOVRvest symbol may look like as a journal filename.
#: Alphanumeric first, then alphanumerics, dots and hyphens — which
#: admits `NESN.ZU`, `VOW3.DE`, `NOVO-B.CO` and `1INCH`, and refuses
#: every path-shaping input (`../DIS`, `A/B`, a lone whitespace) at the
#: type rather than at the filesystem. Validation, not encoding: two
#: distinct symbols are never rewritten onto one filename, because
#: nothing is rewritten at all.
SAFE_SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")


@dataclass(frozen=True, slots=True)
class KnowledgeAcquisitionEvent:
    """One terminal outcome of one explicit acquisition attempt.

    Appended after the outcome is known and never before, so a hard
    kill leaves no manufactured terminal event. Immutable: no event
    overwrites or deletes a previous outcome, and two identical
    attempts are two events, because *this platform tried twice* is a
    fact only an unclipped record can support.
    """

    symbol: str
    attempted_at: datetime

    #: The existing vocabulary, reused rather than re-declared.
    state: KnowledgeState

    #: The document this attempt resolved, where it got that far. None
    #: where source resolution itself failed — which is exactly the
    #: difference between *we could not find a filing* and *we found one
    #: and could not read it*.
    source_key: str | None = None

    #: The document's own publication date, where the source stated one.
    source_published: str = ""

    #: Why, in safe domain wording. **Never a raw exception message**:
    #: a provider failure contributes its exception *class* and nothing
    #: else, because the message may carry an API key, a signed URL, an
    #: account identifier or a fragment of the document itself. A
    #: document refusal may be quoted, because its wording comes from a
    #: typed carrier this platform composed.
    because: str = ""

    #: Whether usable knowledge existed *after* the attempt — the first
    #: dimension, recorded beside the second rather than folded into it.
    knowledge_usable: bool = False

    #: The document the usable knowledge belongs to, where known. May
    #: differ from `source_key`: last year's filing still describes the
    #: business when today's lookup fails.
    usable_source_key: str | None = None

    #: How many observations stood after the attempt.
    observations_after: int = 0

    #: Whether the attempt ended in an extraction refusal. Independent
    #: of `state`, and the reason this is a separate object rather than
    #: a seventh `KnowledgeState`: `observe()` can end with real
    #: acquired knowledge *and* a refusal, and both are true.
    ended_in_refusal: bool = False

    def __post_init__(self) -> None:
        # Normalized once, here, so every consumer downstream — the
        # store's filename, the history's identity check — reads one
        # canonical spelling rather than each normalizing its own way.
        object.__setattr__(self, "symbol", self.symbol.upper().strip())

        if not self.symbol:
            raise ValueError("an acquisition event names the symbol it attempted")

        if not SAFE_SYMBOL.fullmatch(self.symbol):
            raise ValueError(f"{self.symbol!r} is not a canonical MOVRvest symbol")

        if self.attempted_at.tzinfo is None:
            raise ValueError("an acquisition event is stamped in an aware timezone")

        # The two dimensions must agree with each other. Usable
        # knowledge is a claim about the store, and it is checkable:
        # it implies stored observations and the document they belong
        # to, and its absence implies neither survives on the event.
        if self.knowledge_usable and self.observations_after <= 0:
            raise ValueError("usable knowledge implies at least one stored observation")

        if self.knowledge_usable and self.usable_source_key is None:
            raise ValueError("usable knowledge implies the document it was read from")

        if not self.knowledge_usable and (
            self.usable_source_key is not None or self.observations_after > 0
        ):
            raise ValueError(
                "unusable knowledge cannot carry a usable source key or "
                "restorable observations"
            )

        if self.state.is_available and not self.knowledge_usable:
            raise ValueError(
                "an available outcome without usable knowledge is a "
                "contradiction, not a state"
            )

        if self.ended_in_refusal and not self.because.strip():
            raise ValueError("a refusal-ended attempt carries its safe reason")

        if self.state is KnowledgeState.DOCUMENT_REFUSED and not self.because.strip():
            raise ValueError("a document refusal carries its safe typed reason")

    @property
    def had_prior_knowledge(self) -> bool:
        """Usable knowledge beside an outcome that acquired none.

        The pair the measurement said could not be expressed: a
        transient failure or a structural refusal standing beside
        knowledge that still serves.
        """

        return self.knowledge_usable and not self.state.is_available


@dataclass(frozen=True, slots=True)
class KnowledgeOutcomeHistory:
    """One read of one symbol's outcome journal.

    The read contract, following the identity stream's precedent
    (#216): what decoded, what did not, and **whether a complete claim
    about the lifecycle is available at all**. Unknown schemas and
    malformed records are counted apart and never pooled with readable
    history — reading a line whose shape this reader does not
    understand would be the silent cross-schema pooling the knowledge
    store's own contract forbids.

    **A corrupt or unsupported outcome history does not erase usable
    company knowledge.** It prevents a complete claim about the
    acquisition lifecycle; it says nothing about the company. The two
    live in different stores for that reason.
    """

    symbol: str
    events: tuple[KnowledgeAcquisitionEvent, ...] = ()
    unreadable_records: int = 0
    unsupported_schemas: tuple[tuple[str, int], ...] = ()

    @property
    def is_complete(self) -> bool:
        return self.unreadable_records == 0 and not self.unsupported_schemas

    @property
    def skipped(self) -> int:
        return self.unreadable_records + sum(
            count for _, count in self.unsupported_schemas
        )

    @property
    def latest(self) -> KnowledgeAcquisitionEvent | None:
        """The newest terminal event, **only where the history is complete**.

        A latest-outcome claim rests on having seen every outcome. With
        a line missing, the newest *readable* event may not be the
        newest event, and returning it would be a claim this reader
        cannot support.
        """

        if not self.is_complete:
            return None

        return self.events[-1] if self.events else None

    @property
    def attempts(self) -> int:
        """Readable attempts. Never presented as *every* attempt."""

        return len(self.events)
