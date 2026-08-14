"""No section the backend serves may disappear at the page boundary.

**This defect has now been found twice, in the same file, three days
apart.** `facts` — the judged market figures and the rejection ledger —
was served from the day the endpoint existed and the parser had no key
for it. `protocol` — what the systems behind a token earn and what
reaches holders — was parsed into a view model whose entities carried no
`facts` field, and then referenced by no component at all. Both times
the *general* dossier rendered the same evidence, so the surface built
for tokens was the one hiding it, and both times every gate was green:
the payload was correct, the types compiled, and the page was simply
silent.

So the guard is architectural rather than about either section. Two
halves, and it takes both to close the class:

1. **Every top-level key the route serves is read by the parser.**
   Catches `facts`: a key nothing consumes.
2. **Every field the parser produces is referenced by the page.**
   Catches `protocol`: a field consumed into a view model and rendered
   by nothing.

The parser and the page are TypeScript and this repository has no
JavaScript test runner, so these read the sources. That is weaker than
executing them and it is the strongest check available here — and it is
the check that would have failed on both defects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app

WEB = Path(__file__).resolve().parent.parent / "apps" / "web" / "movrvest-web"
PARSER = WEB / "lib" / "api" / "crypto-dossier.ts"
PAGE = WEB / "app" / "crypto" / "[symbol]" / "page.tsx"

#: Served for the page's own addressing rather than as an analytical
#: section, so it needs no section of its own.
NOT_A_SECTION = {"symbol"}


@pytest.fixture
def served() -> dict[str, object]:
    """The payload's own shape, taken from the route rather than a list."""

    with TestClient(app) as client:
        body = client.get("/crypto/BTC/dossier").json()

    assert isinstance(body, dict)

    return body


def test_every_served_section_is_read_by_the_parser(
    served: dict[str, object],
) -> None:
    """Half one: a key the backend sends and nothing consumes.

    This is what hid the judged market facts. The route composed
    `"facts"`, the parser's only occurrences of the word were nested
    inside events and journal, and the section vanished with every gate
    green.
    """

    source = PARSER.read_text(encoding="utf-8")

    # Scoped to `parseDossier` deliberately. `record.facts` also appears
    # inside the journal parser, so a file-wide search reports the
    # top-level key as read while the section is being dropped — which
    # is precisely how the first defect stayed invisible.
    composition = source[source.index("function parseDossier") :]

    for key in served:
        if key in NOT_A_SECTION:
            continue

        assert re.search(rf"\brecord\.{re.escape(key)}\b", composition), (
            f"the crypto dossier serves {key!r} and parseDossier never reads "
            "it — the payload would arrive and vanish"
        )


def test_every_parsed_section_is_referenced_by_the_page() -> None:
    """Half two: a field parsed into the view model and rendered by nothing.

    This is what hid the protocol economics. `protocol` was parsed,
    typed, and `Sections` never passed it to any component — so the
    fields existed, the build passed, and an investor saw nothing.
    """

    parser = PARSER.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")

    model = re.search(
        r"export interface CryptoDossier \{(.*?)\n\}",
        parser,
        re.DOTALL,
    )

    assert model is not None, "CryptoDossier interface not found"

    fields = re.findall(r"^\s{2}(\w+)\??:", model.group(1), re.MULTILINE)

    assert len(fields) > 5, fields

    for field in fields:
        assert f"dossier.{field}" in page, (
            f"the crypto dossier parses {field!r} and the page never "
            "references it — parsed, typed, and rendered by nothing"
        )


def test_the_protocol_entity_carries_its_economics_through_the_parser() -> None:
    """The narrower half of the same defect, pinned.

    `protocol` was *parsed* — its entities arrived named, with their
    mapping basis — and every figure those entities hold was dropped on
    the way. A section can be present and still say nothing.
    """

    parser = PARSER.read_text(encoding="utf-8")

    entity = re.search(
        r"export interface ProtocolEntityView \{(.*?)\n\}",
        parser,
        re.DOTALL,
    )

    assert entity is not None

    assert "facts" in entity.group(1), (
        "an entity without its facts is a name with no economics"
    )

    for field in ("family", "window", "availability", "provider_methodology"):
        assert field in parser, field


def test_no_ratio_between_a_protocol_figure_and_a_market_figure_is_formed() -> None:
    """The boundary this slice was given, held on both sides.

    Fees over market value is a valuation multiple. This platform holds
    a market value for HYPE that two sources put 50% apart, so forming
    one would be inventing a denominator as well as a conclusion.

    Nothing on the page divides, annualises or extrapolates a protocol
    figure — the arithmetic operators are absent from both the section
    and the composition that puts magnitudes beside the judgment.
    """

    parser = PARSER.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")

    fact = re.search(
        r"export interface ProtocolFactView \{(.*?)\n\}",
        parser,
        re.DOTALL,
    )

    assert fact is not None

    # The structural half, and the one that makes the guarantee hold
    # however the section is later edited: a protocol figure crosses the
    # boundary as the backend's own *worded* value. There is no number
    # here to divide by anything.
    assert "number" not in fact.group(1), (
        "a numeric protocol figure would make a valuation multiple one "
        "keystroke away; the backend words every value instead"
    )

    for coercion in ("parseFloat", "parseInt", "Number("):
        assert coercion not in page, (
            f"{coercion} would turn a worded figure back into arithmetic"
        )

    # And the naming half: no section on this page claims a multiple.
    for banned in ("annualis", "annualiz", "fdvRatio", "feeYield", "perMarketCap"):
        assert banned not in page, banned
