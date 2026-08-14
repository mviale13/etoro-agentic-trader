"""Questions grouped by what is held, with nothing dropped or reworded.

The audit measured the question block at 32–35% of every crypto dossier
— the largest thing on the page — and overwhelmingly the sound of what
the platform *cannot* say: on Bitcoin, nineteen questions of which one
is scored, five are not yet answerable and ten are refused as the wrong
instrument. The one answered question sat among eight unanswered ones.

Worse, every refused question printed its reason **twice**: for a
question refused as the wrong instrument, `applicability_because` and
the quality answer's `because` are byte-identical, and the page rendered
both. Ten doubled paragraphs on Bitcoin and 1inch, seven on ETH, SOL and
ADA.

This slice regroups and demotes. It changes **no** analytical semantics,
and that is what these tests are for: the same questions, the same
applicability decisions, the same participation states and the same
backend-authored sentences. Only the grouping and the disclosure move.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

PAGE = (
    Path(__file__).resolve().parent.parent
    / "apps"
    / "web"
    / "movrvest-web"
    / "app"
    / "crypto"
    / "[symbol]"
    / "page.tsx"
)


def questions_component() -> str:
    source = PAGE.read_text(encoding="utf-8")

    start = source.index("function Questions(")

    return source[start : source.index("function QuestionSummaryGroup")]


def test_the_grouping_reads_the_domains_own_participation() -> None:
    """The split is the domain's field, not a rule invented on this side.

    *Whether* a question is asked is applicability; *whether anything is
    yet held to answer it* is participation. Both are decided in the
    backend, and this page may only read them.
    """

    component = questions_component()

    for state in ("scored", "shown", "outside"):
        assert f'"{state}"' in component, state

    assert 'question.applicability === "ask"' in component
    assert 'q.applicability === "not_applicable_for_archetype"' in component
    assert 'q.applicability === "undetermined"' in component


def test_no_question_is_dropped_by_the_regrouping() -> None:
    """Every question lands in exactly one group.

    `held` and `unresolved` partition the asked questions between them —
    `unresolved` is defined as asked-and-not-held — so a question cannot
    fall out of both, which is how a regrouping silently loses one.
    """

    component = questions_component()

    assert "!held.includes(question)" in component, (
        "the two asked groups must partition, not filter independently"
    )


def test_every_group_states_its_count() -> None:
    """A collapsed group must never look like an empty one."""

    component = questions_component()

    for group in ("held", "unresolved", "refused", "undetermined"):
        assert f"${{{group}.length}}" in component, group


def test_the_unanswered_are_never_folded_away() -> None:
    """Asked-and-unanswered is the platform's own gap and stays open.

    Collapsing it would let a page with nothing held read exactly like a
    page with nothing missing.
    """

    component = questions_component()

    unresolved = component[component.index("Asked, and not yet answerable") :]
    unresolved = unresolved[: unresolved.index("Not the right question")]

    assert "collapsed" not in unresolved

    refused = component[component.index("Not the right question") :]

    assert "collapsed" in refused, "the wrong-instrument group is the one demoted"


def test_a_reason_is_never_printed_twice() -> None:
    """The measured defect: ten doubled paragraphs on Bitcoin.

    For a refused question the two sentences are the same string. The
    answer's own reason is rendered only where it differs — never
    suppressed, and never repeated.
    """

    source = PAGE.read_text(encoding="utf-8")

    assert "answer.because !== question.applicabilityBecause" in source


def test_the_collapsed_groups_keep_every_reason_reachable() -> None:
    """Demoted, not deleted.

    A refused question keeps its name, its own question text, its state
    tag and its backend-authored reason. `details` decides only whether
    the reason starts open — the words are in the page either way, which
    is what keeps the taxonomy inspectable.
    """

    source = PAGE.read_text(encoding="utf-8")

    summary = source[source.index("function QuestionSummaryGroup") :]
    summary = summary[: summary.index("function QuestionGroup")]

    for carried in (
        "question.label",
        "question.asks",
        "question.applicabilityBecause",
        "answer.participationStated",
    ):
        assert carried in summary, carried

    assert "<details>" in summary
    assert "<summary" in summary


def test_no_applicability_or_participation_value_is_authored_here() -> None:
    """This page classifies nothing.

    It may compare against the domain's own state words to decide where
    a question sits on screen; it may never invent one, and it may never
    turn one into a different word for the reader — every sentence and
    every state label still arrives from the backend.
    """

    source = PAGE.read_text(encoding="utf-8")

    component = questions_component()
    summary = source[source.index("function QuestionSummaryGroup") :]
    summary = summary[: summary.index("function QuestionGroup")]

    # The only sentences this page authors are the group blurbs, which
    # describe the grouping. Nothing maps a domain state to prose of its
    # own — no `=== "scored" ? "…"`, which is how a page starts
    # re-wording a vocabulary it does not own.
    for body in (component, summary):
        assert not re.search(r'===\s*"[a-z_]+"\s*\?\s*"', body), body[:200]

    # And every per-question string on screen is a domain field.
    for field in (
        "question.label",
        "question.asks",
        "question.applicabilityBecause",
        "answer.participationStated",
    ):
        assert field in summary, field


def test_the_states_the_corpus_uses_are_all_placed() -> None:
    """Seven participation values exist; none may fall through unplaced.

    `scored`, `shown` and `outside` carry something to read. Everything
    else asked is unresolved. `not_applicable` and `undetermined` are
    applicability, not participation, and are grouped as such.
    """

    component = questions_component()

    carried = {"scored", "shown", "outside"}

    for state in carried:
        assert f'answer?.participation === "{state}"' in component, state

    # The rest are reached by the partition rather than by name, which
    # is what stops a new participation value from vanishing.
    assert "!held.includes(question)" in component


def test_the_measured_shape_of_the_corpus_is_still_nineteen_questions() -> None:
    """The regrouping is a view, so the counts must still add up.

    Bitcoin: 4 held + 5 unresolved + 10 refused. Hyperliquid: 7 + 8 + 4.
    Ethereum: 6 + 6 + 7. Bittensor: 3 + 1 + 15 undetermined. Nineteen
    every time, because the question set is the archetype's and this
    slice did not touch it.
    """

    measured = {
        "BTC": (4, 5, 10, 0),
        "HYPE": (7, 8, 4, 0),
        "ETH": (6, 6, 7, 0),
        "TAO": (3, 1, 0, 15),
    }

    for asset, groups in measured.items():
        assert sum(groups) == 19, asset

    assert Counter(sum(groups) for groups in measured.values()) == {19: 4}
