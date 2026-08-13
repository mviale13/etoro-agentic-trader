"""DA1's research step: where does Volkswagen's description actually fail?

**Research harness. Read-only. Delete when the ruling lands.**

*(DP1 has since repaired what this found. The harness still runs both
ways — pass the filer's declared name to see the partition after the
repair, omit it to see the defect — which is what keeps the measurement
checkable rather than historical.)*

DA1 was scoped on the premise that Volkswagen describes its passenger-car
business *only* at a parent altitude (`Konzernbereich Automobile`) and
never under the reportable segment's own label — so a hierarchical
ownership path would be needed to carry the description down.

This harness fetches the filer's own package, reads it exactly as the
platform does, and tests that premise against the document. It changes
nothing and asks no model: every step below is `namings()` and
`describes()` — production's own ownership machinery — run over
production's own reading of the document.

Run it with the repo's venv active:

    python -m tools.description_ownership

It performs one network fetch of the issuer's published package (~5.8MB)
and writes only into a temp directory.
"""

from __future__ import annotations

import pathlib
import tempfile

import httpx

from app.domain.prose_evidence import (
    NEARBY,
    EvidenceNotApplicable,
    _indexed,
    describes,
    namings,
    normalised,
)
from app.providers.esef_filings import read_package

#: The exact document the stored VOW3.DE observations were read from —
#: identifier and location copied from the knowledge file's own source
#: descriptor, so this reads the filing the consensus rests on.
PACKAGE = (
    "https://uploads.vw-mms.de/system/production/files/cws/041/941/file/"
    "00d8d2096bb900de99e1115b0bb6a000f60579c0/VWAG_JFB_Konzern-2025-12-31-DE.zip"
)

#: The filer's own name, as its knowledge entry's source declares it —
#: the evidence DP1's partition consults, and the only thing that may
#: withdraw a naming.
FILER = "Volkswagen AG"

#: The segments exactly as the consensus holds them.
SEGMENTS = (
    "Pkw und leichte Nutzfahrzeuge",
    "Nutzfahrzeuge",
    "Finanzdienstleistungen",
)

#: The filer's own structural statements, located by search over the
#: platform's own flattened reduction. Quoted here so the hierarchy
#: claim can be checked against the document rather than believed.
HIERARCHY = (
    "Seit dem Geschäftsjahr 2025 umfasst der Konzernbereich Automobile",
    "Der Konzernbereich Automobile umfasst dabei das Segment",
    "Der Konzernbereich Finanzdienstleistungen entspricht dem Segment",
)

#: Candidate descriptions of the 75.9% segment, printed under that
#: segment's own name in the filer's own text.
CANDIDATES = {
    "what the segment consolidates": (
        "Im Segment Pkw und leichte Nutzfahrzeuge werden im Wesentlichen die Pkw-Marken"
    ),
    "what the business actually does": (
        "Schwerpunkte der Geschäftstätigkeit sind die Entwicklung von "
        "Fahrzeugen, Motoren, Fahrzeugsoftware und -batterien, die "
        "Produktion und der Vertrieb von Pkw"
    ),
    "the parts business": "sowie das Geschäft mit Originalteilen",
    "the product portfolio": (
        "Das Produktportfolio erstreckt sich von Kleinwagen bis hin zu "
        "Fahrzeugen aus dem Luxussegment"
    ),
}


def text() -> str:
    """The untagged management-report prose, as E1 reads it."""

    cache = pathlib.Path(tempfile.gettempdir()) / "vw_esef_package.zip"

    if not cache.exists():
        response = httpx.get(PACKAGE, timeout=300.0, follow_redirects=True)
        response.raise_for_status()
        cache.write_bytes(response.content)

    return read_package(cache.read_bytes()).unstructured_text


def main() -> None:
    document = text()
    partition = namings(document, SEGMENTS)
    flat, _ = _indexed(document)

    print(f"document: {len(document):,} characters, {len(partition)} namings\n")

    print("── the filer's own hierarchy, verbatim ──\n")
    for probe in HIERARCHY:
        at = flat.find(normalised(probe))
        print(f"  [{at}] {probe}…\n")

    print("── does the segment describe itself at its own altitude? ──\n")
    for label, quoted in CANDIDATES.items():
        try:
            found = describes(
                document, partition, "Pkw und leichte Nutzfahrzeuge", quoted
            )
            print(
                f"  {label:<32} ACCEPTED under {found.under!r}, "
                f"{found.distance} chars from the naming"
            )
        except EvidenceNotApplicable as refused:
            print(f"  {label:<32} REFUSED  {refused}")

    print("\n── what interrupts the partition ──\n")
    opener = flat.find(normalised("Im Segment Pkw und leichte Nutzfahrzeuge werden"))
    closer = flat.find(normalised("Das Produktportfolio erstreckt sich"))

    interrupting = [
        naming
        for naming in partition
        if opener < naming.at <= closer and naming.segment != SEGMENTS[0]
    ]

    for naming in interrupting:
        print(f"  at {naming.at}: read as a naming of {naming.segment!r}")
        print(f"     …{flat[naming.at - 60 : naming.ends + 30]}…")

    print("\n── after DP1: the partition told who the filer is ──\n")
    repaired = namings(document, SEGMENTS, FILER)

    print(f"  namings: {len(partition)} -> {len(repaired)}\n")

    for label, quoted in CANDIDATES.items():
        try:
            found = describes(
                document, repaired, "Pkw und leichte Nutzfahrzeuge", quoted
            )
            print(f"  {label:<32} ACCEPTED at {found.distance} chars")
        except EvidenceNotApplicable as refused:
            print(f"  {label:<32} REFUSED  {str(refused)[:96]}")

    print(f"\n(the proximity bound is NEARBY = {NEARBY} characters, unchanged)")


if __name__ == "__main__":
    main()
