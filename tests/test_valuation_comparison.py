"""A comparison claim cannot exist without a benchmark that exists.

The boundary this file guards was drawn after the platform's one
actively false evidence sentence: *"Forward P/E below historical market
average"*, produced from a constant, presented as evidence, for eight
of nine live securities. The guards are structural — the types refuse
the shapes — with the produced sentences checked by equality against
the observation, not by a word blacklist.

Decision behaviour is deliberately out of scope here and protected by
its own pins: the bands, scores and gates of `pe-bands@1` and
`valuation-scores@1` are untouched legacy policy, fingerprinted in
`test_decision_rule_provenance.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.company_facts import CompanyFacts
from app.domain.decision_rules import PE_BANDS
from app.domain.finding import Sense
from app.domain.provenance import Provenance
from app.domain.valuation_comparison import (
    AbsentComparison,
    ComparisonRelation,
    ValuationBenchmark,
    ValuationComparison,
    ValuationObservation,
)
from app.services.value_signal_service import ValueSignalService

OBSERVATION = ValuationObservation(
    metric="forward_pe",
    label="Forward P/E",
    value=17.4,
)

READING = Provenance(
    source="Test fixture",
    observed_at=datetime(2026, 8, 16, tzinfo=UTC),
)


def _facts(pe: float | None) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Co",
        asset_type="stock",
        exchange="TEST",
        forward_pe=pe,
    )


# ── 1. the types refuse the shapes ──────────────────────────────────


def test_a_benchmark_cannot_be_a_bare_constant() -> None:
    """The mutation the whole slice exists for: hard-code 18, claim a
    benchmark. A benchmark demands a name, a reading and evidence, and
    a code constant has none of them."""

    with pytest.raises(ValueError, match="constant"):
        ValuationBenchmark(
            name="the pe-bands threshold",
            value=18.0,
            reading=READING,
            evidence=(),
        )

    with pytest.raises(ValueError, match="what it is"):
        ValuationBenchmark(name="  ", value=18.0, reading=READING, evidence=("E1",))


def test_a_comparison_cannot_exist_without_a_benchmark() -> None:
    with pytest.raises(TypeError, match="benchmark that exists"):
        ValuationComparison(
            observation=OBSERVATION,
            benchmark=None,  # type: ignore[arg-type]
            relation=ComparisonRelation.BELOW,
            rule=PE_BANDS,
            because="testing the refusal",
        )


def test_a_comparison_must_say_why_its_benchmark_is_relevant() -> None:
    benchmark = ValuationBenchmark(
        name="an evidenced benchmark",
        value=21.0,
        reading=READING,
        evidence=("E1",),
    )

    with pytest.raises(ValueError, match="why"):
        ValuationComparison(
            observation=OBSERVATION,
            benchmark=benchmark,
            relation=ComparisonRelation.BELOW,
            rule=PE_BANDS,
            because="   ",
        )


def test_a_legitimate_comparison_states_its_whole_chain() -> None:
    """The positive case, so the boundary is a gate and not a wall."""

    benchmark = ValuationBenchmark(
        name="an evidenced benchmark",
        value=21.0,
        reading=READING,
        evidence=("E1", "E2"),
    )

    comparison = ValuationComparison(
        observation=OBSERVATION,
        benchmark=benchmark,
        relation=ComparisonRelation.BELOW,
        rule=PE_BANDS,
        because="the benchmark covers the observation's own market",
    )

    assert "17.4" in comparison.stated
    assert "below" in comparison.stated
    assert "an evidenced benchmark" in comparison.stated
    assert PE_BANDS.identity in comparison.stated


def test_an_absent_comparison_is_the_observation_and_nothing_more() -> None:
    """No benchmark must never silently become a neutral comparison.

    The absence keeps its reason for surfaces that render gaps, and its
    stated form — the finding a committee may weigh — is the measured
    fact alone.
    """

    absent = AbsentComparison(
        observation=OBSERVATION,
        because="no benchmark is held",
    )

    assert absent.stated == OBSERVATION.stated
    assert absent.stated == "Forward P/E of 17.4×."

    for word in ("below", "within", "above", "average", "benchmark"):
        assert word not in absent.stated


def test_the_relation_vocabulary_is_descriptive_not_evaluative() -> None:
    """BELOW is not cheap. Interpretation is a layer that does not exist."""

    for relation in ComparisonRelation:
        for word in ("cheap", "expensive", "attractive", "favourable", "adverse"):
            assert word not in relation.stated.lower()


# ── 2. the evidence layer produces only what it holds ───────────────


@pytest.mark.parametrize(
    ("pe", "band"),
    [(9.6, "CHEAP"), (21.0, "FAIR"), (71.8, "EXPENSIVE")],
)
def test_a_banded_signal_states_the_observation_only(pe: float, band: str) -> None:
    """The finding is the observation, by equality — not by blacklist.

    Substituting any benchmark language into the finding breaks the
    equality with the observation's own stated form, which is what
    makes this the primary guard rather than a word list.
    """

    signal = ValueSignalService().build(_facts(pe))

    assert signal.valuation == band, "the legacy band must not move"

    assert signal.observation is not None
    assert isinstance(signal.comparison, AbsentComparison)

    assert len(signal.evidence) == 1

    finding = signal.evidence[0]

    assert finding.statement == signal.observation.stated
    assert finding.statement == f"Forward P/E of {pe:.1f}×."


@pytest.mark.parametrize("pe", [9.6, 21.0, 71.8])
def test_no_band_reads_favourable_or_adverse_any_more(pe: float) -> None:
    """The senses rode on the false comparison, and left with it.

    A favourable CHEAP finding asserted that an unsourced band argues
    for the security. With the claim withdrawn, the honest sense of a
    bare observation is neutral — the band itself still stands, as
    policy, underneath.
    """

    signal = ValueSignalService().build(_facts(pe))

    assert all(finding.sense is Sense.NEUTRAL for finding in signal.evidence)


def test_absence_of_a_multiple_is_not_an_absent_comparison() -> None:
    """Two different absences, kept apart.

    No P/E at all means there is no observation to compare; the signal
    reads UNKNOWN with no observation and no comparison, exactly as
    before this slice.
    """

    signal = ValueSignalService().build(_facts(None))

    assert signal.valuation == "UNKNOWN"
    assert signal.observation is None
    assert signal.comparison is None


def test_the_absence_names_the_constant_for_what_it_is() -> None:
    signal = ValueSignalService().build(_facts(12.0))

    assert isinstance(signal.comparison, AbsentComparison)
    assert "not a benchmark" in signal.comparison.because


# ── 3. the decision machine is untouched ────────────────────────────


def test_the_legacy_bands_and_confidences_are_unchanged() -> None:
    """The slice withdraws a claim; it must not move a decision.

    The full byte-identity proof runs over the live corpus outside the
    suite; this pins the mechanism: same inputs, same bands, same
    asserted confidences, same rule stamp.
    """

    service = ValueSignalService()

    assert service.build(_facts(17.9)).valuation == "CHEAP"
    assert service.build(_facts(18.0)).valuation == "FAIR"
    assert service.build(_facts(27.9)).valuation == "FAIR"
    assert service.build(_facts(28.0)).valuation == "EXPENSIVE"

    assert service.build(_facts(10.0)).confidence == 90
    assert service.build(_facts(20.0)).confidence == 80
    assert service.build(_facts(30.0)).confidence == 85

    stamped = service.build(_facts(10.0))

    assert stamped.rule is PE_BANDS


# ── 4. the old market Value committee obeys the same invariant ──────


def test_the_market_value_committee_no_longer_interprets() -> None:
    """Its own copy of the band survives; "attractive" does not.

    The votes and the 18/30 thresholds are untouched legacy policy.
    The rationale now names its basis as this committee's own fixed
    band rather than presenting an interpretation with no benchmark.
    """

    import ast
    import inspect

    from app.committee import value as module

    tree = ast.parse(inspect.getsource(module))

    # String literals only: the AST drops comments, so the module may
    # still *explain* the withdrawn words without being able to say them.
    literals = " ".join(
        node.value.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )

    for banned in ("attractive", "elevated", "reasonable"):
        assert banned not in literals

    assert "fixed band" in literals
    assert "not an evidenced comparison" in literals
