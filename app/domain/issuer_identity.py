"""Which legal entity a symbol denoted, and when.

`provider_identity` asks whether two providers describing a symbol *now*
are describing the same instrument. This asks the other question its own
docstring names and does not answer: symbols are *"reassigned over
time"*, so the same registry, the same symbol and two different moments
can denote two different companies.

The failure that earned this module was measured rather than imagined.
Paramount Global was acquired and delisted; the SEC reassigned the
ticker `PARA`; and a harvest keyed on that ticker returned **seven Item
5.02 filings belonging to Banzai International**. Nothing downstream
could see it. A leadership timeline, a development feed or a filing
history is precisely the evidence where a wrong issuer looks entirely
plausible — the dates are real, the officers are real, the regulator
received all of it, and none of it is about the company the investor
asked about.

Invariant 2, on its third recorded occasion: *identity is enforced
before the reading, and a perfectly grounded, exactly cited reading of a
genuine filing is still wrong when the filing is another company's.*

## What this is, and what it is not

It records **a dated claim** — this symbol resolved to this issuer, at
this registry, on this date — and compares two of them. It resolves
nothing, ranks nothing and prefers nothing: where two dated claims
disagree, the disagreement is raised, never settled by taking whichever
was read most recently. Preferring the newer one is exactly how a
reassignment becomes a silent substitution.

It is deliberately **not** a security master and invents no canonical
identifier. The registry's own number is the identity; this only says
whether two readings agree about it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

#: Where an EDGAR document's address states the filer's own number:
#: `.../Archives/edgar/data/4962/000000496226000080/axp-20251231.htm`.
#:
#: Read from the location rather than stored in a new field, and that is
#: the whole reason no record had to be rewritten to gain this guarantee:
#: every source this platform has ever held already carries the issuer's
#: registry number inside the address it was fetched from.
_EDGAR_CIK = re.compile(r"/edgar/data/(\d+)/", re.I)


class IssuerReassigned(Exception):
    """A symbol now denotes a different issuer than the evidence held.

    Raised rather than resolved. The two readings are both honest and
    the platform cannot tell which one the investor meant, so it refuses
    to serve either as though it were the other.
    """


@dataclass(frozen=True, slots=True)
class IssuerIdentity:
    """One dated claim that a symbol denoted one issuer at one registry.

    Every field is load-bearing. The registry, because a number means
    nothing without the register that issued it. The date, because this
    is a claim about a moment and not a standing fact. And the name,
    because it is what makes a refusal readable to a person — *"PARA now
    resolves to Banzai International"* is a sentence; a pair of integers
    is not.
    """

    symbol: str

    #: The register that issued the number — "SEC EDGAR".
    registry: str

    #: The register's own identifier for the issuer, as printed. A
    #: string, because a registry number is an identifier rather than a
    #: quantity: nothing here adds, compares or orders it.
    issuer_id: str

    #: The issuer's name as that register states it.
    name: str

    #: When this claim was observed to hold. A filing's own date for
    #: held evidence; today's date for a resolution being made now.
    observed_on: date

    def stated(self) -> str:
        return (
            f"{self.symbol} denoted {self.name} "
            f"({self.registry} {self.issuer_id}) as of {self.observed_on.isoformat()}"
        )


def issuer_id_in(location: str) -> str | None:
    """The issuer number an EDGAR document's own address states.

    `None` where the address is not one this can read — a document from
    another register, or a location shaped differently. Absent is absent:
    an address this cannot parse yields no claim rather than a guess,
    and a guarded call with no claim on one side is unguarded and says
    so rather than passing.
    """

    found = _EDGAR_CIK.search(location)

    # Leading zeros are presentation. EDGAR prints the same filer as
    # `4962` in an archive path and `0000004962` in an accession, and
    # two spellings of one number must not read as two issuers.
    return str(int(found.group(1))) if found else None


def reconcile(
    held: IssuerIdentity | None,
    resolved: IssuerIdentity,
) -> None:
    """Refuse where a symbol's issuer has changed under held evidence.

    Returns nothing and raises on conflict, because there is no third
    outcome worth expressing: either the two readings agree about the
    issuer or the platform must stop.

    **Nothing is checked where nothing is held.** A company read for the
    first time has no prior claim to disagree with, and inventing a
    refusal there would block every new company to catch a reassignment
    that cannot have happened yet. That is a real limit and it is stated
    rather than hidden: this guard catches a symbol changing hands
    *between* two readings, and cannot catch a symbol that was already
    pointing at the wrong issuer the first time it was read.
    """

    if held is None:
        return

    if held.registry != resolved.registry:
        # Two registers can legitimately number the same company
        # differently. Comparing across them would raise on every
        # provider change, which is noise rather than a finding.
        return

    if held.issuer_id == resolved.issuer_id:
        return

    raise IssuerReassigned(
        f"{resolved.symbol} does not denote the same issuer it did when this "
        f"platform last read evidence for it. Held: {held.stated()}. "
        f"Resolved now: {resolved.stated()}. A ticker is reassigned when a "
        "company is acquired or delisted, so the two readings are both "
        "honest and describe different companies — and this platform cannot "
        "tell which one was meant. Nothing is served for this symbol until "
        "the identity is settled; serving either would attribute one "
        "company's filings to another."
    )
