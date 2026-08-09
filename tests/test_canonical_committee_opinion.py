"""The canonical committee opinion: a position, its grounds, and its rule.

The claims this slice makes, each one testable and each one a thing the
previous committee object could not do: a committee states where it
stands rather than what to do, points at findings instead of restating
them, never speaks outside its remit, distinguishes silence from
neutrality, and derives its confidence from counts nobody supplied.
"""

import pytest

from app.application.committees import opinion_builder
from app.application.committees.opinion_builder import Input, build
from app.domain.committee.opinion import (
    Confidence,
    ConfidenceLevel,
    Stance,
    Uncertainty,
    UncertaintyKind,
)
from app.domain.committee.panel import Panel
from app.domain.finding import Dimension, Finding, FindingLedger

REMIT = frozenset({Dimension.QUALITY, Dimension.VALUATION})


def ledger(*findings: Finding) -> FindingLedger:
    return FindingLedger.of(findings)


def opinion(*findings: Finding, **kwargs: object):
    return build(
        committee="Test Committee",
        remit=REMIT,
        ledger=ledger(*findings),
        **kwargs,  # type: ignore[arg-type]
    )


# ── the ledger a committee points into ──────────────────────────────


def test_a_finding_keeps_the_reading_that_produced_it() -> None:
    """The dimension is preserved at composition, never read off the words."""

    found = Finding.favourable("Returns are wide.", Dimension.QUALITY)

    assert found.dimension is Dimension.QUALITY

    # A finding composed without one says so, rather than being guessed at.
    assert Finding.favourable("Returns are wide.").dimension is (Dimension.UNATTRIBUTED)


def test_a_reference_is_stable_and_distinguishes_what_is_distinct() -> None:
    """
    Content-addressed, so a reference means the same thing across cycles.

    A positional index would silently come to point at a different
    finding the moment a signal changed the order it reported in.
    """

    wide = Finding.favourable("Returns are wide.", Dimension.QUALITY)

    assert wide.ref == Finding.favourable("Returns are wide.", Dimension.QUALITY).ref

    # The same sentence read adversely is a different observation.
    assert wide.ref != Finding.adverse("Returns are wide.", Dimension.QUALITY).ref

    # And the same sentence from a different reading is another.
    assert wide.ref != Finding.favourable("Returns are wide.", Dimension.RISK).ref


def test_the_ledger_resolves_what_it_holds_and_nothing_else() -> None:
    book = ledger(Finding.favourable("Returns are wide.", Dimension.QUALITY))

    assert book.statements_for(book.refs) == ("Returns are wide.",)

    # A stale address resolves to nothing rather than raising: one bad
    # reference must not take a whole dossier down.
    assert book.resolve("finding:deadbeef") is None
    assert book.statements_for(("finding:deadbeef",)) == ()


# ── the stance table ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("favourable", "adverse", "expected", "rule"),
    [
        (2, 0, Stance.STRONGLY_POSITIVE, opinion_builder.RULE_UNOPPOSED_FAVOURABLE),
        (0, 2, Stance.STRONGLY_NEGATIVE, opinion_builder.RULE_UNOPPOSED_ADVERSE),
        (2, 1, Stance.POSITIVE, opinion_builder.RULE_FAVOURABLE_MAJORITY),
        (1, 2, Stance.NEGATIVE, opinion_builder.RULE_ADVERSE_MAJORITY),
        (1, 1, Stance.NEUTRAL, opinion_builder.RULE_BALANCED),
        # One unopposed finding is positive, never *strongly*: a lone
        # observation is as easily a gap in reading as a one-sided case.
        (1, 0, Stance.POSITIVE, opinion_builder.RULE_FAVOURABLE_MAJORITY),
    ],
)
def test_the_stance_follows_the_counts_and_names_its_rule(
    favourable: int,
    adverse: int,
    expected: Stance,
    rule: str,
) -> None:
    found = [
        Finding.favourable(f"Good {index}.", Dimension.QUALITY)
        for index in range(favourable)
    ] + [
        Finding.adverse(f"Bad {index}.", Dimension.VALUATION)
        for index in range(adverse)
    ]

    taken = opinion(*found)

    assert taken.stance is expected
    assert taken.decided_by == rule


def test_polarity_is_never_invented() -> None:
    """
    A stance is a count of senses the signals recorded, nothing more.

    Neutral findings are observations, not arguments, and a committee
    shown only those has nothing to take a position on.
    """

    taken = opinion(
        Finding.neutral("It trades at 21 times earnings.", Dimension.VALUATION),
        Finding.neutral("It is a large-cap company.", Dimension.QUALITY),
    )

    assert taken.stance is None
    assert taken.decided_by == opinion_builder.RULE_NO_FINDINGS


# ── silence is not a position ───────────────────────────────────────


def test_an_abstention_is_not_a_neutral_stance() -> None:
    """The distinction this platform has paid for twice."""

    silent = opinion()
    balanced = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        Finding.adverse("It is dear.", Dimension.VALUATION),
    )

    assert silent.stance is None
    assert balanced.stance is Stance.NEUTRAL

    assert not silent.has_opinion
    assert balanced.has_opinion


def test_an_abstention_carries_no_confidence_at_all() -> None:
    """
    A committee that did not speak is not one that spoke unsurely.

    Reporting 0.0 here is what made an unmeasurable input look like an
    objection once it was averaged with real positions.
    """

    assert opinion().confidence is None


def test_an_abstention_says_why_in_words() -> None:
    caller = opinion(abstain_because="Nothing about MSFT was gathered.")

    assert caller.abstained_because == "Nothing about MSFT was gathered."

    # And a committee simply shown nothing says that, rather than nothing.
    assert "abstention, not a neutral view" in (opinion().abstained_because or "")


# ── remit ───────────────────────────────────────────────────────────


def test_a_committee_never_speaks_outside_its_remit() -> None:
    outside = Finding.adverse("It fell 61% from its high.", Dimension.RISK)

    taken = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        outside,
    )

    assert outside.ref not in taken.opposing
    assert taken.stance is Stance.POSITIVE


def test_the_remit_is_declared_on_the_opinion() -> None:
    """
    So a reader can tell *found nothing adverse* from *was shown nothing*.

    Without the declared remit the two are the same empty list.
    """

    assert opinion().remit == REMIT


# ── confidence ──────────────────────────────────────────────────────


def test_confidence_is_counted_never_supplied() -> None:
    taken = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        Finding.adverse("It is dear.", Dimension.VALUATION),
        inputs=(
            Input(name="business quality", value=1),
            Input(name="valuation", value=None, absent_because="Not read."),
        ),
    )

    assert taken.confidence is not None
    assert taken.confidence.inputs_measured == 1
    assert taken.confidence.inputs_asked == 2
    assert taken.confidence.supporting == 1
    assert taken.confidence.opposing == 1
    assert taken.confidence.completeness == 0.5


def test_confidence_states_its_counts_never_a_bare_band() -> None:
    """`Agreement` learned this first: a band alone is an interpretation."""

    stated = Confidence(
        inputs_measured=2,
        inputs_asked=2,
        supporting=3,
        opposing=1,
        unresolved=0,
    ).stated()

    assert "high" in stated
    assert "2 of 2 inputs measured" in stated
    assert "4 findings read" in stated


def test_an_unmeasurable_remit_is_not_a_remit_that_measured_nothing() -> None:
    """`0/0` reported as 0% would say the opposite of what it means."""

    assert (
        Confidence(
            inputs_measured=0,
            inputs_asked=0,
            supporting=1,
            opposing=0,
            unresolved=0,
        ).completeness
        is None
    )


def test_confidence_does_not_soften_a_negative_stance() -> None:
    """
    The defect that made a bearish view tentative by construction.

    A committee reading two clear adverse findings on fully measured
    inputs is not unsure. It is sure, and negative.
    """

    taken = opinion(
        Finding.adverse("Margins fell four quarters.", Dimension.QUALITY),
        Finding.adverse("It is priced for perfection.", Dimension.VALUATION),
        inputs=(
            Input(name="business quality", value=1),
            Input(name="valuation", value=1),
        ),
    )

    assert taken.stance is Stance.STRONGLY_NEGATIVE
    assert taken.confidence is not None
    assert taken.confidence.level is ConfidenceLevel.HIGH


# ── uncertainty ─────────────────────────────────────────────────────


def test_an_unmeasured_input_becomes_an_uncertainty_in_its_own_words() -> None:
    taken = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        inputs=(
            Input(
                name="valuation",
                value=None,
                absent_because="Valuation could not be read for MSFT.",
            ),
        ),
    )

    assert taken.uncertainty == (
        Uncertainty(
            kind=UncertaintyKind.MEASUREMENT_ABSENT,
            about="Valuation could not be read for MSFT.",
        ),
    )


def test_a_question_with_no_answer_is_never_reported_as_pending() -> None:
    """
    Sending an investor back to wait for a measurement that is not coming
    is the estimated figure's defect, told in the future tense.
    """

    resolvable = UncertaintyKind.MEASUREMENT_ABSENT.is_resolvable
    never = UncertaintyKind.OUTSIDE_KNOWLEDGE.is_resolvable

    assert resolvable
    assert not never

    # Nor is a disagreement between readings closed by reading again.
    assert not UncertaintyKind.EVIDENCE_CONFLICTING.is_resolvable


def test_one_absence_stated_by_two_layers_is_one_uncertainty() -> None:
    repeated = Uncertainty(
        kind=UncertaintyKind.MEASUREMENT_ABSENT,
        about="Valuation could not be read.",
    )

    taken = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        uncertainty=(repeated,),
        inputs=(
            Input(
                name="valuation",
                value=None,
                absent_because="Valuation could not be read.",
            ),
        ),
    )

    assert len(taken.uncertainty) == 1


# ── the panel ───────────────────────────────────────────────────────


def positive():
    return opinion(Finding.favourable("Returns are wide.", Dimension.QUALITY))


def negative():
    return opinion(Finding.adverse("It is priced for perfection.", Dimension.VALUATION))


def test_agreement_counts_concurrence_not_confidence() -> None:
    """
    The old figure rose and fell with how much had been read.

    Two committees flatly contradicting each other on well-read evidence
    outscored two agreeing on thin evidence, under a label that said
    "agreement".
    """

    assert Panel(opinions=(positive(), positive())).agreement_pct == 100
    assert Panel(opinions=(positive(), negative())).agreement_pct == 50


def test_an_abstention_is_not_counted_either_way() -> None:
    panel = Panel(opinions=(positive(), opinion()))

    assert len(panel.spoke) == 1
    assert len(panel.abstained) == 1
    assert panel.agreement_pct == 100
    assert panel.is_unanimous


def test_a_panel_nobody_spoke_on_reports_nothing_not_disagreement() -> None:
    panel = Panel(opinions=(opinion(), opinion()))

    assert panel.agreement_pct is None
    assert not panel.is_unanimous
    assert not panel.is_divided
    assert "Nothing here is disagreement" in panel.stated()


def test_a_difference_of_degree_is_not_a_division() -> None:
    """
    Strongly positive beside positive is concurrence, not an argument.

    Reporting it as division would tell an investor two committees
    disagreed when they agreed about direction and differed about force.
    """

    strong = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        Finding.favourable("It compounds capital.", Dimension.QUALITY),
    )

    panel = Panel(opinions=(strong, positive()))

    assert strong.stance is Stance.STRONGLY_POSITIVE
    assert panel.is_unanimous
    assert not panel.is_divided


def test_a_real_contradiction_is_reported_as_one() -> None:
    panel = Panel(opinions=(positive(), negative()))

    assert panel.is_divided
    assert not panel.is_unanimous
    assert "they disagree" in panel.stated()


def test_a_contested_opinion_says_so() -> None:
    """
    A positive stance reached over opposition is not the same finding as
    a positive stance with nothing against it.
    """

    contested = opinion(
        Finding.favourable("Returns are wide.", Dimension.QUALITY),
        Finding.favourable("It compounds capital.", Dimension.QUALITY),
        Finding.adverse("It is dear.", Dimension.VALUATION),
    )

    assert contested.stance is Stance.POSITIVE
    assert contested.is_contested
    assert not positive().is_contested
