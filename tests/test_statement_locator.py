"""The acceptance criterion for statement location, case by case.

> Every authoritative financial statement must be selected because it
> belongs to the highest-quality structural run, not because its title
> matched first.

Each shape below is one the corpus actually produced, and each is
refused by the *same* rule rather than by a clause written for it.
"""

from app.domain.financial_statements import StatementKind
from app.providers.document_text import flatten
from app.providers.statement_locator import (
    LISTING_WIDEST,
    candidates,
    locate,
    resolve,
    runs,
)

#: A statement's own rows, wide enough to be a statement rather than a
#: listing — which is the only thing that separates the two.
ROWS = "\n".join(
    f"  <tr><td>Revenue and expense line item number {number}</td>"
    f"<td>{number * 137}</td><td>{number * 129}</td></tr>"
    for number in range(1, 21)
)


def statement(title: str) -> str:
    return f"<p>{title}</p>\n<table>\n{ROWS}\n</table>"


AUDITED = f"""\
<html><body>
{statement("Consolidated statements of income")}
<p>Consolidated statements of comprehensive income</p>
<p>Other comprehensive income was as follows.</p>
{statement("Consolidated balance sheets")}
{statement("Consolidated statements of cash flows")}
<p>Notes to consolidated financial statements</p>
<p>Note 1 — Basis of presentation.</p>
</body></html>
"""


def located(markup: str):
    return locate(markup, flatten(markup))


# ── the genuine audited sequence ─────────────────────────────────────


def test_the_audited_run_is_selected_and_every_statement_placed() -> None:
    found = located(AUDITED)

    assert found.run is not None
    assert found.run.substance == 3

    for kind in StatementKind:
        assert found.span(kind) is not None
        assert found.contenders[kind] == 1


def test_a_statement_closes_at_the_next_statement_the_filer_printed() -> None:
    """Even one this platform reads no concept from."""

    found = located(AUDITED)
    flat = flatten(AUDITED)

    span = found.span(StatementKind.INCOME_STATEMENT)

    assert span is not None
    assert "Other comprehensive income" not in flat.text[span[0] : span[1]]
    assert "Consolidated balance sheets" not in flat.text[span[0] : span[1]]


# ── a contents page ──────────────────────────────────────────────────


def test_a_contents_page_is_a_progression_of_nothing_and_loses() -> None:
    """Three statements in order, each a few characters wide."""

    with_contents = f"""\
<html><body>
<p>Consolidated statements of income 152</p>
<p>Consolidated balance sheets 154</p>
<p>Consolidated statements of cash flows 156</p>
{AUDITED}
</body></html>
"""

    found = located(with_contents)
    flat = flatten(with_contents)

    assert found.run is not None
    assert found.run.substance == 3

    span = found.span(StatementKind.INCOME_STATEMENT)

    assert span is not None
    # What was selected is a statement, not the entry pointing at it:
    # wide, and not followed by a page number.
    assert span[1] - span[0] >= LISTING_WIDEST
    assert "152" not in flat.text[span[0] : span[0] + 60]
    assert "Revenue and expense line item" in flat.text[span[0] : span[1]]


# ── an MD&A discussion ───────────────────────────────────────────────


def test_a_discussion_of_a_statement_is_isolated_and_loses() -> None:
    """The JPMorgan shape: a real, wide, block-beginning wrong answer."""

    discussed = f"""\
<html><body>
<p>CONSOLIDATED BALANCE SHEETS AND CASH FLOWS ANALYSIS</p>
<p>Consolidated balance sheets analysis</p>
<table>
{ROWS}
</table>
<p>{"Discussion of the significant changes between periods. " * 900}</p>
{AUDITED}
</body></html>
"""

    found = located(discussed)
    flat = flatten(discussed)

    assert found.run is not None
    assert found.run.substance == 3

    span = found.span(StatementKind.BALANCE_SHEET)

    assert span is not None
    assert "analysis" not in flat.text[span[0] : span[0] + 60].casefold()

    # The discussion was seen, considered, and rejected as a run — not
    # ignored by a rule about its wording.
    assert found.rejected
    assert all(losing.substance < 3 for losing in found.rejected)


# ── a pointer item ───────────────────────────────────────────────────


def test_a_pointer_item_holds_no_statement_title_and_is_no_candidate() -> None:
    """JPM's Item 8 is 370 characters naming pages 162–314."""

    pointer = """\
<html><body>
<p>Item 8. Financial Statements and Supplementary Data.</p>
<p>The Consolidated Financial Statements, together with the Notes
thereto and the report thereon of the independent registered public
accounting firm, appear on pages 162-314.</p>
</body></html>
"""

    found = located(pointer)

    assert found.run is None
    assert found.spans == {}
    assert found.unresolved_because is not None
    assert "not about the company" in found.unresolved_because


# ── a title in discussion but not in the audited run ─────────────────


def test_a_statement_absent_from_the_run_stays_absent() -> None:
    """Interpretation never outruns evidence: no fallback to the mention."""

    partial = f"""\
<html><body>
<p>Consolidated statements of cash flows analysis</p>
<table>
{ROWS}
</table>
<p>{"Cash flow commentary for the period. " * 1200}</p>
<html><body>
{statement("Consolidated statements of income")}
{statement("Consolidated balance sheets")}
<p>Notes to consolidated financial statements</p>
</body></html>
"""

    found = located(partial)

    assert found.run is not None
    assert found.span(StatementKind.INCOME_STATEMENT) is not None
    assert found.span(StatementKind.BALANCE_SHEET) is not None

    # The cash flow title exists in this document, begins a block, and
    # is wide. It is not in the audited run, so it is not located.
    assert found.span(StatementKind.CASH_FLOW_STATEMENT) is None
    assert found.contenders[StatementKind.CASH_FLOW_STATEMENT] == 0


# ── what it refuses to decide ────────────────────────────────────────


def test_two_indistinguishable_runs_settle_nothing() -> None:
    """Choosing between them by position would be a heuristic."""

    twice = f"""\
<html><body>
{statement("Consolidated statements of income")}
{statement("Consolidated balance sheets")}
{statement("Consolidated statements of cash flows")}
<p>Notes to consolidated financial statements</p>
<p>{"Filler between the two blocks. " * 3000}</p>
{statement("Consolidated statements of income")}
{statement("Consolidated balance sheets")}
{statement("Consolidated statements of cash flows")}
<p>Notes to consolidated financial statements</p>
</body></html>
"""

    flat = flatten(twice)
    accepted = tuple(c for c in candidates(twice, flat) if c.is_heading)
    selected, because = resolve(runs(accepted, flat.text))

    assert selected is None
    assert because is not None
    assert "structurally indistinguishable" in because


def test_a_title_inside_a_sentence_is_never_a_candidate() -> None:
    """The auditor's report names every statement it audited."""

    flat = flatten(AUDITED)
    audited_mention = """\
<html><body>
<p>We have audited the consolidated balance sheets of Example Corp and
the related consolidated statements of income for the year then
ended.</p>
</body></html>
"""

    mentions = candidates(audited_mention, flatten(audited_mention))

    assert mentions
    assert all(not mention.is_heading for mention in mentions)

    # And the real document still resolves, so the rule is not simply
    # rejecting everything.
    assert locate(AUDITED, flat).run is not None
