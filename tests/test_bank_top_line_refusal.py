"""An established bank top line with no comparable ruler, and a withdrawal
that cannot fall through to a provider proxy.

Two halves of one ruling, and they meet at the same seam. `_quality_value`
promised that a grounded assessment governs outright *including when it bands
UNKNOWN* — and both halves are cases the promise did not reach:

- **A** the statements establish a consolidated total struck after financing
  cost, no threshold here can read it, and the factors it would have answered
  render as though the filer had printed nothing;
- **B** every reading of every statement held was withdrawn by an audit, so
  there is no band to govern with, and the provider's three proxies re-open
  underneath a company whose evidence was taken away.

Everything below runs on held evidence. No model, no fetch, no write.
"""

from __future__ import annotations

import collections
import pathlib

from app.application.executive.decision_evidence_builder import DecisionEvidenceBuilder
from app.domain.business_quality import BusinessQuality, QualityBand
from app.domain.financial_statements import StatementConcept, StatementKind
from app.domain.financial_understanding import (
    FinancialEvidenceStanding,
    IncomparableTopLine,
)
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services.business_quality_service import quality_of
from app.services.company_understanding_service import CompanyUnderstandingService
from app.services.financial_engine import measure
from app.services.financial_statement_service import FinancialStatementService

PRODUCTION = "data/statements"

#: The three companies whose filers strike the consolidated total after
#: financing cost and whose readings already establish it. Named rather
#: than discovered, so a fourth arriving is a visible act.
STRUCK_AFTER_FINANCING = ("AXP", "GS", "JPM")

#: The two whose every statement reading an audit withdrew. RF is not
#: here: its balance sheet survived, so it still reaches a grounded
#: UNKNOWN and is a control rather than a specimen.
FULLY_WITHDRAWN = ("C", "MTB")


def _symbols() -> list[str]:
    return sorted(
        {path.name.split(".")[0] for path in pathlib.Path(PRODUCTION).glob("*.json")}
    )


def _service() -> FinancialStatementService:
    return FinancialStatementService(JsonFinancialStatementStore(PRODUCTION))


def _graded(symbol: str) -> BusinessQuality | None:
    service = _service()

    held = service.established(symbol)

    if not held:
        return None

    return quality_of(symbol, measure(symbol, held))


# ── a provider recommendation that would score 80 ───────────────────────


class _QualitySignal:
    """The provider proxy at its strongest: large, profitable, paying."""

    quality = "HIGH"
    basis = "Provider proxy: large, profitable, dividend-paying."
    evidence = ()
    rule = None
    contributions = ()


class _Signals:
    quality = _QualitySignal()


class _Provider:
    symbol = "TEST"
    signals = _Signals()


def _provider() -> object:
    return _Provider()


# ── A: the semantic refusal ─────────────────────────────────────────────


def test_exactly_the_three_specimens_carry_an_incomparable_top_line() -> None:
    """The predicate is structural, and it fires nowhere else.

    Both halves are load-bearing and both are checked here: no gross
    total established, and a total struck after financing cost that is.
    A company printing the label without the structure reaches nothing,
    which is what keeps this a statement about evidence.
    """

    carrying = [
        symbol
        for symbol in _symbols()
        if (graded := _graded(symbol)) is not None
        and graded.incomparable_top_line is not None
    ]

    assert carrying == list(STRUCK_AFTER_FINANCING)

    service = _service()

    for symbol in carrying:
        income = service.established(symbol)[StatementKind.INCOME_STATEMENT]

        gross = income.fact(StatementConcept.TOTAL_REVENUE)
        struck = income.fact(StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE)

        # The gross total is not established — refused for GS and JPM,
        # never labelled for AXP — and the struck one is.
        assert gross is None or not gross.is_located, symbol
        assert struck is not None and struck.is_located, symbol


def test_the_three_stay_unknown_one_of_three_with_no_score() -> None:
    """The refusal is worded and changes no arithmetic whatsoever."""

    for symbol in STRUCK_AFTER_FINANCING:
        graded = _graded(symbol)

        assert graded is not None, symbol
        assert graded.band is QualityBand.UNKNOWN, symbol
        assert graded.score is None, symbol
        assert graded.answered == 1, symbol

        answered = [factor.question.value for factor in graded.factors if factor.counts]

        # Earnings growth alone, from a dated net income row. The two
        # questions that need a denominator stay unanswerable, in their
        # own layer's words.
        assert answered == ["earnings_growth"], symbol


def test_the_refusal_states_all_five_things_the_ruling_requires() -> None:
    """Domain-owned wording, and every clause the owner named is in it."""

    for symbol in STRUCK_AFTER_FINANCING:
        graded = _graded(symbol)

        assert graded is not None
        refused = graded.incomparable_top_line
        assert refused is not None

        stated = refused.stated()

        # 1 — the top line was established, quoted with its own label.
        assert refused.label in stated, symbol
        assert refused.printed in stated, symbol

        # 2 — it is struck after financing cost.
        assert "struck after financing cost" in stated

        # 3 — the existing ruler compares against gross revenue.
        assert "compares a margin against gross revenue" in stated

        # 4 — no comparable ruler has been established.
        assert "no comparable ruler" in stated

        # 5 — therefore no verdict and no band.
        assert "no profitability verdict" in stated
        assert "no quality band is claimed" in stated

        # And it is a limit of this platform, never a finding about the
        # company — the sentence every absence here has to end on.
        assert "not a finding about the company" in stated


def test_the_evidence_coordinates_and_source_travel_with_the_figure() -> None:
    """A refused figure is checkable against the filing or it is a claim."""

    for symbol in STRUCK_AFTER_FINANCING:
        graded = _graded(symbol)

        assert graded is not None
        refused = graded.incomparable_top_line
        assert refused is not None

        # The checked cell first, then the rest of its row, each cell
        # once. The filer's label, header, printed text and address all
        # ride along.
        assert refused.basis, symbol
        assert refused.basis[0].label == refused.label
        assert refused.basis[0].printed == refused.printed

        addresses = [figure.cell for figure in refused.basis]
        assert len(addresses) == len(set(addresses)), symbol

        assert "SEC EDGAR" in refused.source, symbol

        # Its width, at the narrowest — a refusal rests on evidence as
        # firmly as an established measure does.
        assert refused.support is not None
        assert refused.support.readings >= 5, symbol

        assert refused.basis[0].stated() in refused.stated()


def test_the_reason_reaches_the_investor_facing_basis_verbatim() -> None:
    """Communication renders the domain's sentence and composes none."""

    for symbol in STRUCK_AFTER_FINANCING:
        graded = _graded(symbol)

        assert graded is not None
        refused = graded.incomparable_top_line
        assert refused is not None

        basis = DecisionEvidenceBuilder._quality_basis(None, graded)

        assert refused.stated() in basis.basis, symbol
        assert refused.stated() in basis.evidence, symbol

        # Still an explained absence, so still no rule and no number.
        assert basis.rules == ()
        assert basis.derivation is None
        assert DecisionEvidenceBuilder._quality_value(None, graded) is None


def test_a_banded_company_carries_no_refusal_and_no_extra_sentence() -> None:
    """The corporate ruler is untouched where a gross total was read."""

    for symbol in ("AAPL", "UNP", "DIS", "TRV", "HON", "PG"):
        graded = _graded(symbol)

        assert graded is not None, symbol
        assert graded.incomparable_top_line is None, symbol

        basis = DecisionEvidenceBuilder._quality_basis(None, graded)

        assert "no comparable ruler" not in basis.basis, symbol


def test_the_wording_needs_an_established_figure_and_not_a_label() -> None:
    """The negative control the ruling asks for, constructed directly.

    A company that prints the label and establishes nothing — BCS and
    NWG both do — reaches no wording at all. Proved from the corpus
    rather than from a fixture, because a fixture would be asserting
    that this test's own construction is right.
    """

    for symbol in ("BCS", "NWG"):
        graded = _graded(symbol)

        assert graded is not None, symbol

        income = _service().established(symbol)[StatementKind.INCOME_STATEMENT]
        struck = income.fact(StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE)

        # The concept post-dates their readings, so it was never asked.
        # Not established, therefore not worded.
        assert struck is None or not struck.is_located, symbol
        assert graded.incomparable_top_line is None, symbol


def test_the_refusal_takes_part_in_no_arithmetic() -> None:
    """Supplying one cannot move a band, a count or a score.

    `assess` computes from `answers` alone. Asserted by handing the same
    answers to it twice, once with a refusal and once without, and
    comparing everything the decision layer reads.
    """

    from app.domain.business_quality import assess
    from app.domain.financial_question import FinancialModel
    from app.services.financial_questions import answer_questions

    service = _service()

    for symbol in ("AAPL", "GS", "KO"):
        understanding = measure(symbol, service.established(symbol))

        answers = answer_questions(FinancialModel.GENERIC, understanding)

        without = assess(symbol, answers, "test fixture")
        with_one = assess(
            symbol,
            answers,
            "test fixture",
            incomparable_top_line=IncomparableTopLine(
                label="Total net revenues",
                printed="58,283",
            ),
        )

        assert with_one.band is without.band, symbol
        assert with_one.score == without.score, symbol
        assert with_one.favourable == without.favourable, symbol
        assert with_one.answered == without.answered, symbol
        assert with_one.factors == without.factors, symbol
        assert with_one.stated() == without.stated()


# ── B: total withdrawal cannot fall through ─────────────────────────────


def test_the_standing_tells_the_three_states_apart_on_the_live_corpus() -> None:
    """Structured, and it agrees with what the store holds."""

    service = _service()
    understanding = CompanyUnderstandingService(statements=service)

    standings = {
        symbol: understanding.understanding(symbol).financial_standing
        for symbol in _symbols()
    }

    withdrawn = [
        symbol
        for symbol, standing in standings.items()
        if standing is FinancialEvidenceStanding.WITHDRAWN_BY_AUDIT
    ]

    assert withdrawn == list(FULLY_WITHDRAWN)

    for symbol, standing in standings.items():
        if symbol in FULLY_WITHDRAWN:
            # Readings held, none authoritative.
            assert service.withdrawn(symbol), symbol
            assert not service.established(symbol), symbol
            continue

        assert standing is FinancialEvidenceStanding.ESTABLISHED, symbol
        assert service.established(symbol), symbol

    # Nothing in this corpus has never been read, so the never-read
    # branch is exercised by a symbol the store does not hold.
    absent = understanding.understanding("NOSUCHTICKER")

    assert absent.financial_standing is FinancialEvidenceStanding.NEVER_READ
    assert absent.financial is None


def test_a_withdrawal_blocks_the_provider_proxy_that_would_score_eighty() -> None:
    """BQ19's measured defect, reproduced and closed.

    The provider recommendation here is the strongest one there is — it
    would score 80 — and it is handed in beside a company whose every
    statement reading an audit withdrew.
    """

    understanding = CompanyUnderstandingService(statements=_service())

    for symbol in FULLY_WITHDRAWN:
        held = understanding.understanding(symbol)

        assert held.financial is None, symbol
        assert quality_of(symbol, held.financial) is None, symbol

        # Before this slice, this returned 80.
        assert (
            DecisionEvidenceBuilder._quality_value(
                _provider(),  # type: ignore[arg-type]
                None,
                held.financial_standing,
            )
            is None
        ), symbol

        basis = DecisionEvidenceBuilder._quality_basis(
            _provider(),  # type: ignore[arg-type]
            None,
            held.financial_standing,
            held.financial_absent_because,
        )

        # No ruler ran, so no rule is stamped and no number is derived.
        assert basis.rules == (), symbol
        assert basis.derivation is None, symbol

        # The composing service's account, carried rather than composed.
        assert held.financial_absent_because is not None
        assert held.financial_absent_because in basis.basis, symbol

        # And this layer's own account of what it did about it.
        assert "No business quality is scored from them" in basis.basis
        assert "stored history rather than a current assessment" in basis.basis
        assert "proxies are not consulted" in basis.basis

        # Re-observation is named exactly once, by whichever voice owns it.
        assert basis.basis.count("explicit spend") == 1, symbol

        # The provider's own sentence never appears — a blocked route
        # does not get to explain itself.
        assert _QualitySignal.basis not in basis.basis, symbol


def test_a_never_read_company_keeps_the_provider_route_exactly() -> None:
    """The fallback this slice must not break."""

    score = DecisionEvidenceBuilder._quality_value(
        _provider(),  # type: ignore[arg-type]
        None,
        FinancialEvidenceStanding.NEVER_READ,
    )

    assert score == 80

    basis = DecisionEvidenceBuilder._quality_basis(
        _provider(),  # type: ignore[arg-type]
        None,
        FinancialEvidenceStanding.NEVER_READ,
    )

    assert [rule.key for rule in basis.rules] == ["provider-quality"]

    # And the default reaches the same place, so a caller that passes no
    # standing at all behaves as it did before this parameter existed.
    assert DecisionEvidenceBuilder._quality_value(_provider(), None) == 80  # type: ignore[arg-type]
    assert DecisionEvidenceBuilder._quality_basis(_provider(), None).rules  # type: ignore[arg-type]


def test_the_gate_reads_the_member_and_never_the_sentence() -> None:
    """Withdrawal is detected structurally, and a test can prove it.

    The withdrawal *prose* is handed in beside a `NEVER_READ` standing.
    A gate that matched words would block the provider here; a gate that
    reads the member cannot, and must not even echo the sentence.
    """

    prose = (
        "MTB's income statement has been read, and an offline audit of the "
        "filing withdrew all 5 of those readings"
    )

    assert (
        DecisionEvidenceBuilder._quality_value(
            _provider(),  # type: ignore[arg-type]
            None,
            FinancialEvidenceStanding.NEVER_READ,
        )
        == 80
    )

    basis = DecisionEvidenceBuilder._quality_basis(
        _provider(),  # type: ignore[arg-type]
        None,
        FinancialEvidenceStanding.NEVER_READ,
        prose,
    )

    assert "withdrew all 5" not in basis.basis

    # The mirror: the withdrawal standing blocks even with no sentence
    # at all, because the standing is what decides.
    assert (
        DecisionEvidenceBuilder._quality_value(
            _provider(),  # type: ignore[arg-type]
            None,
            FinancialEvidenceStanding.WITHDRAWN_BY_AUDIT,
        )
        is None
    )

    bare = DecisionEvidenceBuilder._quality_basis(
        _provider(),  # type: ignore[arg-type]
        None,
        FinancialEvidenceStanding.WITHDRAWN_BY_AUDIT,
    )

    assert "withdrawn by an offline audit" in bare.basis
    assert bare.rules == ()


def test_a_grounded_unknown_still_governs_and_rf_is_unchanged() -> None:
    """The guarantee this slice extends, re-asserted where it already held."""

    understanding = CompanyUnderstandingService(statements=_service())

    held = understanding.understanding("RF")

    # RF's income readings were withdrawn and its balance sheet was not,
    # so it has an understanding and a grounded UNKNOWN — which governs.
    assert held.financial_standing is FinancialEvidenceStanding.ESTABLISHED

    graded = _graded("RF")

    assert graded is not None
    assert graded.band is QualityBand.UNKNOWN
    assert graded.answered == 0

    assert (
        DecisionEvidenceBuilder._quality_value(
            _provider(),  # type: ignore[arg-type]
            graded,
            held.financial_standing,
        )
        is None
    )


def test_a_withdrawal_alone_is_not_current_security_evidence() -> None:
    """Stored history is not an assessment.

    `security_evidenced` counts a provider row or a grounded assessment.
    A withdrawn reading is neither, so a company holding only withdrawn
    readings and no provider row is reported as unevidenced.
    """

    understanding = CompanyUnderstandingService(statements=_service())

    for symbol in FULLY_WITHDRAWN:
        held = understanding.understanding(symbol)

        quality = quality_of(symbol, held.financial)

        assert quality is None, symbol

        # The expression the builder evaluates, with no provider row.
        assert (None is not None or quality is not None) is False


# ── the corpus, and what must not move ──────────────────────────────────


def test_no_band_moved_anywhere_in_the_corpus() -> None:
    """The whole slice is wording and a blocked fallback. Nothing scores."""

    service = _service()

    tally: collections.Counter[str] = collections.Counter()
    coverage = {}

    for symbol in _symbols():
        graded = _graded(symbol)

        tally[graded.band.value if graded is not None else "UNKNOWN"] += 1

        if graded is not None:
            coverage[symbol] = (graded.band.value, graded.score, graded.answered)

    assert dict(tally) == {"HIGH": 3, "MEDIUM": 5, "LOW": 3, "UNKNOWN": 13}

    # The owner's control set, pinned by value rather than by band count.
    assert coverage["GS"] == ("UNKNOWN", None, 1)
    assert coverage["JPM"] == ("UNKNOWN", None, 1)
    assert coverage["AXP"] == ("UNKNOWN", None, 1)
    assert coverage["HON"] == ("MEDIUM", 62, 3)
    assert coverage["AAPL"] == ("MEDIUM", 62, 3)
    assert coverage["UNP"] == ("MEDIUM", 62, 3)
    assert coverage["DIS"] == ("HIGH", 80, 3)
    assert coverage["KO"] == ("UNKNOWN", None, 0)
    assert coverage["TRV"][0] == "HIGH"
    assert coverage["ALL"][0] == "HIGH"

    del service


def test_the_quantity_still_reaches_no_measure_and_no_threshold() -> None:
    """BQ24's guard, restated over what this slice added.

    The concept is now *named* in one more place — the engine that
    derives the worded refusal — and must still be consumed by no
    recipe, and named in none of the layers that score. The existing
    guard in `test_revenue_net_of_interest_concept.py` covers the
    scoring layers; this covers the new carrier and the engine.
    """

    import ast

    from app.services.financial_engine import RECIPES

    concept = StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE

    for name, recipe in RECIPES.items():
        assert concept not in recipe.concepts, name

    # The carrier holds no number this platform could compare. Every
    # field is a string, evidence, or the width beneath it — there is
    # nowhere for a score, a band or a threshold to live.
    fields = {
        field.name: field.type
        for field in IncomparableTopLine.__dataclass_fields__.values()
    }

    assert set(fields) == {"label", "printed", "basis", "source", "support"}
    assert "int" not in "".join(str(annotation) for annotation in fields.values())
    assert "float" not in "".join(str(annotation) for annotation in fields.values())

    # And the module that derives it performs no arithmetic on the
    # figure: the derivation function's body contains no arithmetic
    # operator at all. Its `X | None` return annotation is a `BitOr` and
    # is skipped by walking the body rather than the whole node — a
    # union is a type, not a computation.
    source = pathlib.Path("app/services/financial_engine.py").read_text()

    derivation = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_incomparable_top_line"
    )

    arithmetic = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Pow, ast.Mod)

    for statement in derivation.body:
        for node in ast.walk(statement):
            assert not (
                isinstance(node, ast.BinOp) and isinstance(node.op, arithmetic)
            ), ast.unparse(node)
