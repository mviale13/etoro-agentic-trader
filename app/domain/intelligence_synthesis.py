"""An analyst's reading of evidence this platform already holds.

The last layer of the crypto intelligence stack, and the only one that
asks a model anything. Its job is stated narrowly on purpose:

> **Which of these things matter together, why they matter, and what
> deserves attention next.**

It is **not an evidence producer**. Every acquisition slice before it
was about getting facts into the platform; this one adds no facts at
all. The model's universe is the findings it is handed — it has no web
access, no tools, no second call, and no way to discover an event. What
it contributes is the thing five slices of deterministic rules could not:
noticing that MicroStrategy selling, Marathon selling and dormant coins
moving are **one story about holder behaviour**, and saying so in a
sentence that still points at all three events.

**A theme is a synthesis object, never a canonical fact.** `Theme` is
free text the model chose, capped and carried beside the refs it groups.
Nothing stores it, nothing scores it, and no downstream layer may branch
on it — the moment a fixed theme vocabulary exists, something will
classify against it, and this platform will have acquired a taxonomy
nobody measured.

**Three outputs, and none of them is an action.** *What matters*, *why
it matters*, *what to watch*. The model is never asked what the investor
should do; that question belongs to the Artificial CIO and this layer
cannot reach it.

The trust model is the Executive Writer's, unchanged: the draft is
untrusted until validated, validation **fails closed**, and a rejected
draft leaves the deterministic brief standing rather than showing
half-checked prose.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.provenance import Provenance


class SynthesisStatus(StrEnum):
    """Whether there is a reading, and if not, why not.

    An absence is a state a surface prints, not a blank. The Executive
    Writer established this and the reason holds here: an investor
    seeing no synthesis needs to know whether the model was off, refused,
    or wrote something that failed grounding — those are three different
    facts about the platform.
    """

    #: A draft was produced and survived every validation rule.
    WRITTEN = "written"

    #: The synthesis layer is switched off. The deterministic brief is
    #: the canonical rendering and always was.
    DISABLED = "disabled"

    #: No provider could be built — no credentials, no SDK, an unknown
    #: provider name.
    UNCONFIGURED = "unconfigured"

    #: The model declined, timed out, or could not be reached.
    UNAVAILABLE = "unavailable"

    #: A draft came back and failed grounding. The most important of
    #: these: it means the guard worked.
    REJECTED = "rejected"

    #: There was too little to synthesise.
    THIN = "thin"

    @property
    def stated(self) -> str:
        return _STATUS[self]

    @property
    def is_written(self) -> bool:
        return self is SynthesisStatus.WRITTEN


_STATUS = {
    SynthesisStatus.WRITTEN: "Synthesised",
    SynthesisStatus.DISABLED: "Synthesis is off",
    SynthesisStatus.UNCONFIGURED: "No synthesis provider is configured",
    SynthesisStatus.UNAVAILABLE: "The synthesis model could not be reached",
    SynthesisStatus.REJECTED: "A synthesis was drafted and refused",
    SynthesisStatus.THIN: "Too little evidence to synthesise",
}


#: How long a theme label may be. A cap rather than a vocabulary: the
#: point of leaving it free text is that the corpus has not yet shown
#: which themes recur, and the point of the cap is that a long "theme"
#: is a sentence pretending to be a label.
MAX_THEME_WORDS = 5


@dataclass(frozen=True, slots=True)
class SynthesisItem:
    """One analytical statement, and the evidence it rests on.

    **Each item carries its own refs.** A single global reference set
    would let a four-sentence synthesis cite eleven findings and leave a
    reader unable to tell which sentence rested on which — which is
    indistinguishable from citing nothing.
    """

    stated: str

    #: Findings this statement rests on. Never empty: an item with no
    #: refs cannot be constructed, and the validator rejects a draft that
    #: produces one.
    refs: tuple[str, ...]

    #: The model's own name for what it grouped, where it grouped
    #: anything. Free text, capped, stored nowhere, and read by nothing
    #: that decides.
    theme: str | None = None


@dataclass(frozen=True, slots=True)
class IntelligenceSynthesis:
    """What matters, why, and what to watch — over supplied evidence only.

    Sits *beside* the deterministic brief and never replaces it. A
    surface renders this first because it is the answer, and the
    structured evidence beneath it because that is the proof.
    """

    symbol: str
    status: SynthesisStatus

    what_matters: tuple[SynthesisItem, ...] = ()
    why_it_matters: tuple[SynthesisItem, ...] = ()
    watch_next: tuple[SynthesisItem, ...] = ()

    #: The worded reason there is no synthesis. Present exactly when
    #: `status` is not WRITTEN — the Executive Writer's rule, kept: a
    #: narrative or the reason there is none, never both and never
    #: neither.
    absent_because: str | None = None

    model: str | None = None
    reading: Provenance | None = None

    @property
    def items(self) -> tuple[SynthesisItem, ...]:
        return self.what_matters + self.why_it_matters + self.watch_next

    @property
    def themes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.theme for item in self.items if item.theme))

    def grounded_in(self, known: set[str]) -> bool:
        """Whether every item points only at findings that were supplied.

        The same checkable property `CryptoIntelligenceSnapshot.grounded`
        is, applied to the layer that has a model in it — which is the
        layer that needs it most.
        """

        return all(item.refs and set(item.refs) <= known for item in self.items)


def absent(
    symbol: str,
    status: SynthesisStatus,
    because: str,
    at: datetime | None = None,
) -> IntelligenceSynthesis:
    """A synthesis that is not there, and says why."""

    return IntelligenceSynthesis(
        symbol=symbol,
        status=status,
        absent_because=because,
        reading=(
            Provenance(source="Intelligence Synthesist", observed_at=at)
            if at is not None
            else None
        ),
    )
