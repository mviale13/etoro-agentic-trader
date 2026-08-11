"""Turn what is held into the strongest thing that can responsibly be said.

Deterministic, read-only, no model. It reads two things — the supply
evidence and the recorded committee judgments — and produces sentences.
It convenes nothing and fetches nothing.

**Three layers stay separate and this is the third.** The evidence layer
keeps every reading with its provenance and may hold figures that
disagree. The committee layer keeps what each committee concluded about
its own remit, in its own vocabulary. This layer decides what is *useful
to tell an investor*, and it is the only one of the three allowed to
decide that a disagreement does not matter.

**It never reinterprets a verdict.** A committee's answer is quoted, not
translated: the sentence a reader sees for a structural judgment is the
committee's own `verdict_stated`, and the reason is the committee's own
`because`. What this layer adds is the decision to *say it at all*, and
what to say when the committee said nothing useful.

**And it never invents a figure.** Two sources 2% apart produce a bound
naming both, never a midpoint. Averaging disagreeing sources into a
number nobody published is the plausible-figure failure Invariant 1
exists to prevent.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.committee_matrix import CommitteeAssessment
from app.domain.investor_assessment import (
    InvestorAssessment,
    InvestorStatement,
    ObservedValue,
    StatementShape,
)
from app.domain.judgment_history import JudgmentPosture
from app.domain.supply_semantics import (
    Comparison,
    SupplyConcept,
    SupplyFact,
    SupplyPicture,
)
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.supply_semantics_service import SupplySemanticsService

#: How far two readings may differ and still be reported as a bound
#: rather than as a material uncertainty.
#:
#: **Not a quality threshold and not a band.** It is the point at which
#: the *difference itself* changes what can responsibly be said: below
#: it, an investor who reads "8.6–9.6 million" knows everything the
#: readings support; above it, the spread is the story and quoting a
#: range would imply the truth lies inside it when one reading may
#: simply be wrong. Set from the corpus — Bittensor's estimates span
#: 9.9% and bound a real answer; Hyperliquid's span 78% and one of them
#: exceeds the protocol maximum.
#: **Provisional, and explicitly not a definition of investor
#: materiality.** One constant currently decides this for every quantity,
#: and the corpus has already shown that what a spread *means* depends on
#: context: Bittensor's two circulating readings 9.9% apart form a useful
#: bound, while Hyperliquid's much larger span matters partly because one
#: reading exceeds the protocol maximum — a fact about the *kind* of
#: disagreement rather than its size.
#:
#: Future materiality may belong to the quantity or the question rather
#: than to one global evidence threshold. No decision is taken here, and
#: nothing downstream should treat this number as a general answer.
MATERIAL_SPREAD = 0.25

#: The investor's words for the quantities this layer reports. Internal
#: concept names never reach a reader.
_SUBJECTS = {
    SupplyConcept.MAX_SUPPLY: "Maximum supply",
    SupplyConcept.EMITTED_SUPPLY: "Tokens in existence",
    SupplyConcept.CIRCULATING_ESTIMATE: "Circulating supply",
}

_WHY = {
    SupplyConcept.MAX_SUPPLY: ("It bounds how far the holder's share can be diluted."),
    SupplyConcept.EMITTED_SUPPLY: (
        "It is how many tokens exist today, whoever holds them."
    ),
    SupplyConcept.CIRCULATING_ESTIMATE: (
        "It is what the market can currently trade, and it is an "
        "estimate under somebody's definition rather than a protocol fact."
    ),
}


class InvestorAssessmentService:
    """The strongest useful statements about one asset."""

    def __init__(
        self,
        supply: SupplySemanticsService | None = None,
        matrix: CommitteeMatrixService | None = None,
    ) -> None:
        self._supply = supply or SupplySemanticsService()
        self._matrix = matrix or CommitteeMatrixService()

    def for_asset(self, symbol: str) -> InvestorAssessment:
        asset = symbol.upper().strip()

        statements: list[InvestorStatement] = []
        silent: list[str] = []

        reading = self._supply.established(asset, AssetClass.CRYPTO)

        if reading is not None:
            statements.extend(_quantities(reading))

        for subject in _SUBJECTS.values():
            if not any(item.subject == subject for item in statements):
                silent.append(subject)

        for cell in self._matrix.for_asset(asset).assessments:
            statement = _from_committee(cell)

            if statement is None:
                silent.append(_committee_subject(cell))

                continue

            statements.append(statement)

        return InvestorAssessment(
            asset=asset,
            statements=tuple(statements),
            silent_about=tuple(silent),
        )


# ── quantities: precise, bounded, or materially uncertain ───────────


def _quantities(reading: SupplyPicture) -> list[InvestorStatement]:
    """One statement per quantity, as strong as its readings allow."""

    statements: list[InvestorStatement] = []

    for concept, subject in _SUBJECTS.items():
        facts = [
            fact
            for fact in reading.facts
            if fact.concept is concept and fact.value is not None
        ]

        if not facts:
            continue

        statements.append(_about(concept, subject, facts, reading))

    return [_guarded(item, reading) for item in statements]


def _guarded(
    statement: InvestorStatement,
    reading: SupplyPicture,
) -> InvestorStatement:
    """Qualify a figure this platform has measured a reason to distrust.

    One guard, and it exists because the corpus produced a sentence that
    was faithful to the evidence and irresponsible to print: *"Tokens in
    existence is 21.00 million"* for Bittensor, where the same vendor
    also puts the maximum at 21 million.

    S5 measured that a vendor's `total_supply` **is** the protocol
    maximum for 83 of 145 capped assets in the top 250, and the chain
    impeached it for ADA and TAO. So an emitted figure exactly equal to
    the maximum is not evidence that everything has been issued — it is
    equally consistent with the vendor having restated the cap.

    Exact equality is a reason to qualify and not to reject: Arbitrum
    genuinely is fully emitted. So the figure stands and the statement
    says what else it could be, which is the difference between
    reporting a number and vouching for it.
    """

    if statement.subject != _SUBJECTS[SupplyConcept.EMITTED_SUPPLY]:
        return statement

    caps = [
        fact.value
        for fact in reading.facts
        if fact.concept is SupplyConcept.MAX_SUPPLY and fact.value is not None
    ]

    emitted = [value.value for value in statement.observed]

    if not caps or not emitted or max(caps) != max(emitted):
        return statement

    return InvestorStatement(
        subject=statement.subject,
        shape=StatementShape.QUALIFIED,
        stated=statement.stated,
        qualification=(
            "This figure is exactly the maximum supply, which is equally "
            "consistent with every token having been issued and with the "
            "source restating the cap — a substitution measured across 83 "
            "of 145 capped assets. No chain reading is held here to tell "
            "the two apart."
        ),
        why_it_matters=statement.why_it_matters,
        observed=statement.observed,
        refs=statement.refs,
    )


def _about(
    concept: SupplyConcept,
    subject: str,
    facts: list[SupplyFact],
    reading: SupplyPicture,
) -> InvestorStatement:
    values = [fact.value for fact in facts if fact.value is not None]

    low, high = min(values), max(values)

    observed = tuple(
        ObservedValue(
            value=fact.value,
            unit=fact.unit,
            source=fact.source,
            observed_at=fact.observed_at,
        )
        for fact in facts
        if fact.value is not None
    )

    refs = tuple(sorted({fact.source for fact in facts}))

    spread = (high - low) / high if high else 0.0

    # One reading, or several that agree closely enough to be one
    # answer. The tolerance is the evidence layer's own.
    if spread <= 0.0005:
        return InvestorStatement(
            subject=subject,
            shape=StatementShape.PRECISE,
            stated=(
                f"{subject} is {_amount(high)}"
                + (
                    f", agreed by {len(observed)} sources."
                    if len(observed) > 1
                    else f", from {observed[0].source}."
                )
            ),
            why_it_matters=_WHY[concept],
            observed=observed,
            refs=refs,
        )

    # Readings that differ, and the difference does not change what can
    # responsibly be said. **The bound is the answer**, and no midpoint
    # is computed.
    if spread < MATERIAL_SPREAD:
        return InvestorStatement(
            subject=subject,
            shape=StatementShape.RANGE,
            stated=(
                f"{subject} is approximately {_amount(low)} to "
                f"{_amount(high)} across {len(observed)} available "
                "estimates."
            ),
            qualification=(
                "The estimates differ by "
                f"{spread:.1%}; no single figure is published by all of "
                "them and none is computed here."
            ),
            why_it_matters=_WHY[concept],
            observed=observed,
            refs=refs,
        )

    # The spread is the story. Where the evidence layer has already said
    # *why* the readings differ, that reason is quoted rather than
    # restated — it knows things this layer does not.
    return InvestorStatement(
        subject=subject,
        shape=StatementShape.UNCERTAIN,
        stated=(
            f"{subject} cannot be stated as a single figure: available "
            f"estimates run from {_amount(low)} to {_amount(high)}, a "
            f"spread of {spread:.0%}."
        ),
        uncertainty=_why_they_differ(concept, reading)
        or (
            "The estimates are far enough apart that quoting a range "
            "would imply the answer lies inside it, and this platform "
            "cannot establish that it does."
        ),
        why_it_matters=_WHY[concept],
        observed=observed,
        refs=refs,
    )


def _why_they_differ(concept: SupplyConcept, reading: SupplyPicture) -> str | None:
    """The evidence layer's own account of a disagreement, where it has one."""

    for comparison in reading.comparisons:
        if comparison.left.concept is not concept:
            continue

        if comparison.verdict is Comparison.CONFLICTED:
            return comparison.because

    return None


# ── committee judgments: quoted, never translated ───────────────────


def _committee_subject(cell: CommitteeAssessment) -> str:
    return cell.committee.name.replace(" Committee", "")


def _from_committee(cell: CommitteeAssessment) -> InvestorStatement | None:
    """One committee's conclusion, worded for an investor.

    Returns `None` where the committee genuinely has nothing useful to
    say — which is not the same as it having no verdict. Three of the
    four unanswered postures still carry a useful statement:

    - *the question does not apply here* is a **structural fact about
      the asset** and one of the more useful things this layer can say;
    - *the committee did not run* is a fact about this platform, said
      plainly rather than dressed as an absence of evidence;
    - *the evidence could not answer it* names what is missing.

    Only an unestablished applicability leaves nothing — this platform
    cannot say whether the question even applies, so it says so and
    files the subject as one it is silent about.
    """

    subject = _committee_subject(cell)

    refs = (cell.committee.key, *cell.refs)

    if cell.posture is JudgmentPosture.ANSWERED and cell.answer:
        # The committee's own sentence, quoted. This layer adds the
        # decision to say it and nothing else.
        return InvestorStatement(
            subject=subject,
            # A committee's answer describes how something works, so it
            # is structural. It becomes *qualified* in exactly one
            # derivable case: the committee answered and its drafted
            # explanation was refused, so the answer stands while the
            # reasoning beside it is the committee's own fallback.
            # Inferring a qualification from the verdict's wording would
            # be this layer reading committee semantics, which PR #114
            # forbids.
            shape=(
                StatementShape.QUALIFIED
                if cell.wording_refused
                else StatementShape.STRUCTURAL
            ),
            stated=f"{cell.answer.capitalize()}.",
            qualification=(
                f"{cell.because} The committee's drafted explanation was "
                "refused by this platform's own checks, so the account "
                "above is its own."
                if cell.wording_refused
                else cell.because
            ),
            why_it_matters=cell.question,
            refs=refs,
        )

    if cell.posture is JudgmentPosture.KNOWN_NOT_APPLICABLE:
        return InvestorStatement(
            subject=subject,
            shape=StatementShape.STRUCTURAL,
            stated=(
                "This question is the wrong instrument for this asset, so "
                "it is left unanswered rather than answered."
            ),
            qualification=cell.because,
            why_it_matters=cell.question,
            refs=refs,
        )

    if cell.posture is JudgmentPosture.EVIDENCE_INSUFFICIENT:
        return InvestorStatement(
            subject=subject,
            shape=StatementShape.INSUFFICIENT,
            stated="This platform holds too little to answer this question.",
            uncertainty=cell.because,
            why_it_matters=cell.question,
            refs=refs,
        )

    if cell.posture is JudgmentPosture.EXECUTION_UNAVAILABLE:
        return InvestorStatement(
            subject=subject,
            shape=StatementShape.INSUFFICIENT,
            stated=(
                "This committee did not run, so there is no answer either "
                "way — a fact about this platform rather than the asset."
            ),
            uncertainty=cell.unavailable_because,
            why_it_matters=cell.question,
            refs=refs,
        )

    return None


def _amount(value: float) -> str:
    """A figure as published, never rounded into a different number."""

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f} billion"

    if value >= 1_000_000:
        return f"{value / 1_000_000:,.2f} million"

    return f"{value:,.0f}"
