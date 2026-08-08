"""Which financial questions a playbook asks, and which it refuses to.

The layer the owner's ruling created, and the sentence that motivates
it: *a bank is not a highly levered industrial — leverage is the
business model*. A rule table built for one cannot be pointed at the
other, and the fix is not a threshold that knows about banks. It is
moving the decision about **which questions are meaningful** to the
thing that already knows what kind of company this is.

```text
canonical facts                    ← universal, filing-grade, never scored
      ↓
playbook selects the questions     ← this module
      ↓
playbook supplies the rule         ← by naming the analyst that owns it
      ↓
analyst answers, or declines       ← app/services/financial_questions.py
```

**The analyst no longer decides what matters for a bank.** It executes
a question it was handed, against facts it did not read, with a rule
table it does not own — and where the contract cannot be satisfied it
says so rather than reaching for something else.

Three outcomes, and the last two are never collapsed:

- `ANSWERED` — the facts were there and the rule ran.
- `NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS` — a meaningful question whose
  filing-grade fact this platform has not established. A gap in
  evidence.
- `NOT_APPLICABLE_FOR_PLAYBOOK` — a question that should not be asked
  of this kind of company at all. A statement about the question.

Collapsing them would destroy the distinction the whole slice exists to
make. "We could not measure JPMorgan's leverage" and "the industrial
leverage question is the wrong question for a bank" are opposite claims
about the same blank space, and only one of them is a reason to go and
acquire more evidence.

**No thresholds live here.** A question names the analyst whose rule
table interprets it, and that analyst keeps owning it — so a playbook
asserting ownership of a question never becomes a second copy of its
numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.financial_understanding import FinancialMeasure
from app.domain.playbook import PlaybookKind
from app.domain.research_plan import AnalystKey
from app.domain.tabular_evidence import ReportedFigure


class FinancialQuestionKey(StrEnum):
    """A stable name for one financial question, across every playbook.

    Named for the *economic question*, never for the metric that
    currently answers it. "Leverage" survives a playbook that measures
    it with a regulatory capital ratio instead of a balance-sheet
    quotient; "liabilities to equity" would not, and renaming a question
    later would break every stored answer that referred to it.
    """

    PROFITABILITY = "profitability"
    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    LEVERAGE = "leverage"
    CASH_GENERATION = "cash_generation"


class AnswerState(StrEnum):
    """What became of one question."""

    ANSWERED = "answered"
    NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS = "not_answerable_from_established_facts"
    NOT_APPLICABLE_FOR_PLAYBOOK = "not_applicable_for_playbook"


@dataclass(frozen=True, slots=True)
class FinancialQuestion:
    """One question, the facts it needs, and who owns the rule for it."""

    key: FinancialQuestionKey

    #: The question in words, as an investor would ask it.
    asks: str

    #: The canonical measures this question consults, in the order it
    #: consults them. A question is answered from the ones that are
    #: established and reports the rest as gaps, with its confidence
    #: falling accordingly — the behaviour the analysts have always had.
    #: Only where *none* of them is established is the question
    #: unanswerable, because there is then nothing to answer it with.
    requires: tuple[FinancialMeasure, ...]

    #: The analyst whose rule table interprets it. Named rather than
    #: copied — this is what keeps a playbook from becoming a second
    #: place the thresholds live.
    interpreted_by: AnalystKey

    #: What that rule table calls each required measure, where the two
    #: vocabularies differ. Empty where they agree.
    #:
    #: The one entry this needs today is the whole point of the slice:
    #: the generic leverage question hands `liabilities_to_equity` to a
    #: rule table whose thresholds were written for `debt_to_equity`.
    #: Stating that here makes the substitution visible in the contract
    #: rather than hidden in a scorer — and being visible is what let
    #: the BANK playbook refuse it.
    scored_as: dict[FinancialMeasure, str] = field(default_factory=dict)

    def rule_key(self, measure: FinancialMeasure) -> str:
        """The observation key the owning rule table scores this under."""

        return self.scored_as.get(measure, measure.value)


#: Every financial question this platform knows how to ask.
QUESTIONS: dict[FinancialQuestionKey, FinancialQuestion] = {
    FinancialQuestionKey.PROFITABILITY: FinancialQuestion(
        key=FinancialQuestionKey.PROFITABILITY,
        asks="How profitable is this business on the revenue it earns?",
        requires=(
            FinancialMeasure.GROSS_MARGIN,
            FinancialMeasure.OPERATING_MARGIN,
            FinancialMeasure.NET_MARGIN,
        ),
        interpreted_by=AnalystKey.PROFITABILITY,
    ),
    FinancialQuestionKey.REVENUE_GROWTH: FinancialQuestion(
        key=FinancialQuestionKey.REVENUE_GROWTH,
        asks="Is what this business earns growing?",
        requires=(FinancialMeasure.REVENUE_GROWTH,),
        interpreted_by=AnalystKey.GROWTH,
    ),
    FinancialQuestionKey.EARNINGS_GROWTH: FinancialQuestion(
        key=FinancialQuestionKey.EARNINGS_GROWTH,
        asks="Is what this business keeps growing?",
        requires=(FinancialMeasure.EARNINGS_GROWTH,),
        interpreted_by=AnalystKey.GROWTH,
    ),
    FinancialQuestionKey.LEVERAGE: FinancialQuestion(
        key=FinancialQuestionKey.LEVERAGE,
        asks="How much of this business is financed by other people's money?",
        requires=(FinancialMeasure.LIABILITIES_TO_EQUITY,),
        interpreted_by=AnalystKey.BALANCE_SHEET,
        scored_as={FinancialMeasure.LIABILITIES_TO_EQUITY: "debt_to_equity"},
    ),
    FinancialQuestionKey.CASH_GENERATION: FinancialQuestion(
        key=FinancialQuestionKey.CASH_GENERATION,
        asks="Does this business generate cash from what it does?",
        requires=(FinancialMeasure.OPERATING_CASH_FLOW,),
        interpreted_by=AnalystKey.CASH_FLOW,
    ),
}


@dataclass(frozen=True, slots=True)
class QuestionDecline:
    """A question this playbook holds to be the wrong question, and why.

    A sibling of `PlaybookExclusion`, one level finer. That one declines
    a whole analyst; this declines a single question, so a playbook can
    run the balance-sheet analyst and still refuse its leverage rule.
    """

    question: FinancialQuestionKey
    reason: str


@dataclass(frozen=True, slots=True)
class PlaybookQuestions:
    """The financial questions one playbook owns.

    Three powers, and a playbook may use any of them: which questions
    are asked, which are refused, and — `narrowed` — which established
    facts answer a question it does ask.

    The third is not a convenience. A bank's income statement prints no
    gross profit and no operating income, so a profitability question
    that kept consulting them would report the same two gaps for every
    bank forever, and a permanent gap is noise rather than a finding.
    Narrowing states that a bank's profitability question is about net
    margin — which is a claim about banks, and therefore the playbook's
    to make.
    """

    asks: tuple[FinancialQuestionKey, ...]
    declines: tuple[QuestionDecline, ...] = ()

    #: Which measures answer a question here, where fewer than the
    #: question's own list. Never more: a playbook may narrow what
    #: answers a question and may not invent inputs for it.
    narrowed: dict[FinancialQuestionKey, tuple[FinancialMeasure, ...]] = field(
        default_factory=dict
    )

    def declined(self, key: FinancialQuestionKey) -> QuestionDecline | None:
        for decline in self.declines:
            if decline.question is key:
                return decline

        return None

    def consults(self, question: FinancialQuestion) -> tuple[FinancialMeasure, ...]:
        """The measures that answer this question under this playbook."""

        narrowed = self.narrowed.get(question.key)

        if narrowed is None:
            return question.requires

        return tuple(measure for measure in question.requires if measure in narrowed)


#: What every playbook asks unless it says otherwise. The behaviour the
#: platform had before playbooks owned questions, kept exactly, so that
#: nothing outside a playbook that declares its own set changes.
GENERIC = PlaybookQuestions(asks=tuple(FinancialQuestionKey))


#: Playbooks that own their financial questions explicitly.
#:
#: One entry, deliberately. A playbook enters here when a real case
#: shows the generic set answering the wrong question for it — never
#: because a taxonomy of playbooks would look more complete filled in.
OWNED: dict[PlaybookKind, PlaybookQuestions] = {
    PlaybookKind.BANK: PlaybookQuestions(
        asks=(
            FinancialQuestionKey.PROFITABILITY,
            FinancialQuestionKey.REVENUE_GROWTH,
            FinancialQuestionKey.EARNINGS_GROWTH,
            FinancialQuestionKey.LEVERAGE,
            FinancialQuestionKey.CASH_GENERATION,
        ),
        narrowed={
            # A bank's income statement prints neither a gross profit
            # line nor an operating income line — measured on JPMorgan,
            # 5 of 5 readings. Its profitability question is about what
            # it keeps on what it earns.
            FinancialQuestionKey.PROFITABILITY: (FinancialMeasure.NET_MARGIN,),
        },
        declines=(
            QuestionDecline(
                question=FinancialQuestionKey.LEVERAGE,
                reason=(
                    "A deposit-taking bank cannot be assessed with the "
                    "industrial leverage threshold. Its balance sheet is its "
                    "business rather than a support for it, and the "
                    "liabilities that make it look levered are the deposits "
                    "it exists to take. What a bank's leverage question needs "
                    "is regulatory capital, which this platform has not "
                    "established."
                ),
            ),
            QuestionDecline(
                question=FinancialQuestionKey.CASH_GENERATION,
                reason=(
                    "A bank's operating cash flow is dominated by deposit and "
                    "lending flows, so its sign does not measure cash "
                    "generation the way it does for an industrial. The figure "
                    "is established and reported; the industrial rule for "
                    "reading it is not applied."
                ),
            ),
        ),
    ),
}


def questions_for(playbook: PlaybookKind) -> PlaybookQuestions:
    """The questions this playbook asks, generic unless it owns its own."""

    return OWNED.get(playbook, GENERIC)


@dataclass(frozen=True, slots=True)
class QuestionAnswer:
    """What one question came to for one company, and on what evidence.

    Carries the canonical facts' own evidence rather than a restatement
    of it: the `basis` figures are the cells this platform read out of
    the filing, and they travel from `FinancialUnderstanding` through
    here unchanged. An answer whose provenance stopped at this layer
    would be a score with nothing behind it.
    """

    question: FinancialQuestionKey
    playbook: PlaybookKind
    state: AnswerState

    #: The rule table's own verdict word, where one ran.
    verdict: str | None = None
    score: int | None = None
    confidence: float | None = None

    #: How the answer is evidenced, one line per measure consumed.
    evidence: tuple[str, ...] = ()

    #: Measures this question consults that are not established, in the
    #: canonical layer's own words. An answer with gaps is a partial
    #: answer and says so through its confidence; it is never silently
    #: presented as complete.
    gaps: tuple[str, ...] = ()

    #: The checked cells beneath it, inherited from the canonical facts.
    basis: tuple[ReportedFigure, ...] = ()

    #: Why there is no answer — the consensus's own wording for a gap in
    #: evidence, the playbook's own wording for a refused question.
    because: str | None = None

    @property
    def is_answered(self) -> bool:
        return self.state is AnswerState.ANSWERED

    @property
    def asks(self) -> str:
        return QUESTIONS[self.question].asks
