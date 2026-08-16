# Financial-model selection independence — measured, and declined

**Status: research report, BQ2. No implementation. The brief's premise
was falsified by the first measurement, so the report answers the
question it was asked and then the question the corpus substituted for
it. Stopped for ruling.**

BQ2 asked whether `FinancialModel.BANK` can be selected from financial
evidence alone, so that an absent narrative understanding stops making
strong statement evidence unreadable. The measurement says the
dependency is real, is correctly ruled, and **is not blocking
anything**:

> **Selecting `BANK` for every interest-based filing in the corpus
> changes 0 bands, 0 scores and 0 answered questions in grounded
> Business Quality.** Sixteen companies read UNKNOWN today and sixteen
> read UNKNOWN after. Not one of them becomes answerable.

BQ1 reported that `FinancialModel.BANK` "exists for precisely this and
cannot be selected", and that "the two blockers therefore compound: the
narrative outage is what keeps every bank on the generic question set."
The first half is true. **The second half is wrong**, and this report
corrects it: `BANK` and `GENERIC` ask grounded Business Quality the same
three questions, and `BANK`'s only power over them subtracts inputs. The
narrative outage is not why banks are silent.

What the corpus put in its place is a smaller, real and general defect,
measured below: for 22 of 24 companies this platform explains a missing
profitability measure by naming a line the filer has demonstrably never
printed in five readings — sending an investor to acquire evidence that
does not exist.

Everything here is offline, over the tracked `data/statements` corpus
(24 companies, every quorum 5 of 5), through `CompanyUnderstandingService`,
`quality_of` and `answer_questions`. No filing was fetched, no model was
asked, no credit was spent. `data/cache` is gitignored and absent, so
nothing here read one.

---

## 1. The current model-selection dependency graph

Traced from the code, not from documentation.

```text
CompanyKnowledgeConsensus  (data/knowledge, schema 14 wanted, 11/12 stored)
        ↓  understand()
BusinessUnderstanding
        ↓  select_grounded()          app/services/playbook_mapping.py
PlaybookSelection → PlaybookKind
        ↓  model_for()                app/domain/financial_question.py:241
FinancialModelSelection → FinancialModel
        ↓  questions_for()
PlaybookQuestions  (asks / declines / narrowed)
        ↓  answer_questions()         app/services/financial_questions.py
QuestionAnswer × 5
        ↓  assess()
BusinessQuality → band, score
```

**`model_for` has exactly one live caller in the whole repository**:
`app/commands/financials.py:74`, the `movrvest financials` CLI. Nothing
else resolves a financial model at all.

`IMPLIED_BY_PLAYBOOK` has one entry — `PlaybookKind.BANK → BANK` — so
`model_for` returns `BANK` for one playbook and `GENERIC` for all
others. `FinancialModelSelection.diverged` is `False` everywhere and
nothing sets it.

### The dependency does not reach Business Quality at all

`app/application/workspace/executive_pipeline.py:166`:

```python
workspace.quality = quality_of(
    symbol,
    self.understanding.understanding(symbol).financial,
)
```

No model is passed. `quality_of`'s third parameter defaults to
`GENERIC`, so **every company in the live pipeline is already assessed
under `GENERIC` regardless of what any narrative route concludes.** An
independent selection route would change nothing until this call site
were edited too — which is a separate change with its own product
story.

### The narrative route, measured rather than assumed

Over the 24 statement companies, `CompanyUnderstandingService` returns
`business = None` for **24 of 24**. Only 5 of the 24 have a knowledge
file at all (AAPL, DIS, JPM, PG, TSLA) and none is readable under
schema 14. Over the whole 33-company knowledge corpus,
`select_grounded` yields **0 grounded playbook selections**.

So the dependency graph above is, today, severed at its first arrow for
every company whose statements this platform holds. That is the fact
BQ2's premise rests on, and it is correct.

### What `BANK` actually is, as a contract

`OWNED[FinancialModel.BANK]` differs from `GENERIC` in exactly three
ways:

| Power | What `BANK` does |
|---|---|
| `asks` | identical — all five `FinancialQuestionKey` members |
| `narrowed` | profitability consults `NET_MARGIN` **only** (drops gross and operating margin) |
| `declines` | `LEVERAGE` and `CASH_GENERATION`, each with a reason and an acquisition demand |

`QUALITY_QUESTIONS` — what grounded Business Quality reads — is
profitability, revenue growth, earnings growth. **`BANK`'s two declines
are on the two questions Business Quality does not consult.** Its only
reachable power over quality is a narrowing, and a narrowing can only
remove inputs.

That is the whole mechanical explanation of §4's zero.

---

## 2. Financial-semantic classification of all 24 statement companies

Derived only from `StatementLanguage` over the stored consensus —
positive printed lines, never name, ticker, sector or industry. This
independently reproduces `FINANCIAL_LANGUAGE_EVIDENCE.md` exactly: every
claim 5 of 5, in both directions.

| Symbol | `net_interest_income` | `premium_revenue` | Established language | Model this evidence could support |
|---|---|---|---|---|
| AXP | `Net interest income` 17,364 | — | **interest based** | interest-based language; **not** `BANK` |
| BCS | `Net interest income` 14,501 | — | **interest based** | interest-based language; **not** `BANK` |
| C | `Net interest income` 59,792 | — | **interest based** | interest-based language; **not** `BANK` |
| COF | `Net interest income` 42,878 | — | **interest based** | interest-based language; **not** `BANK` |
| DB | `Net interest income` 15,673 | — | **interest based** | interest-based language; **not** `BANK` |
| FITB | `Net Interest Income` 5,982 | — | **interest based** | interest-based language; **not** `BANK` |
| GS | `Net interest income` 13,559 | — | **interest based** | interest-based language; **not** `BANK` |
| JPM | `Net interest income` 95,443 | — | **interest based** | interest-based language; **not** `BANK` |
| MTB | `Net interest income` 6,948 | — | **interest based** | interest-based language; **not** `BANK` |
| MUFG | `Net interest income` 3,684,254 | — | **interest based** | interest-based language; **not** `BANK` |
| NWG | `Net interest income` 12,829 | — | **interest based** | interest-based language; **not** `BANK` |
| RF | `Net interest income` 4,991 | — | **interest based** | interest-based language; **not** `BANK` |
| CB | — | `Net premiums earned` 53,014 | **insurance based** | insurance language; no model exists |
| MET | — | `Premiums` 49,779 | **insurance based** | insurance language; no model exists |
| TRV | — | `Premiums` 43,914 | **insurance based** | insurance language; no model exists |
| ALL | — | — | **neither established** | **insufficient** |
| AAPL | — | — | **neither established** | insufficient (see below) |
| DIS | — | — | **neither established** | insufficient |
| HON | — | — | **neither established** | insufficient |
| KO | — | — | **neither established** | insufficient |
| PG | — | — | **neither established** | insufficient |
| TSLA | — | — | **neither established** | insufficient |
| UNP | — | — | **neither established** | insufficient |
| WMT | — | — | **neither established** | insufficient |

**Conflicting models: zero.** No filing in the corpus prints both
markers, so `StatementLanguage.BOTH` stays unexercised.

**The last column is the load-bearing one.** Twelve filings establish
interest-based *language*. None of them establishes `BANK`, because
`BANK` is not a description of a statement — it is a contract that
declines two questions *for reasons about deposit funding and
regulatory capital*, and no line above mentions either. That is
`FINANCIAL_DOMAIN_BOUNDARY.md` §4, and this measurement re-derives it
rather than assuming it.

**"Insufficient" is the honest label for `NEITHER`, and ALL proves
why.** Allstate is an insurer whose premium line this platform did not
locate, so it lands in the same bucket as Apple and Coca-Cola. Any rule
reading `NEITHER` as evidence of a generic operating company would be
reading an insurer as one. The bucket is an absence of evidence, and
`StatementLanguage` already words it that way.

---

## 3. Ambiguous and conflicting specimens

No two-marker conflict exists, so the ambiguity is all on one side.

**GS and AXP are the specimens the brief predicted.** The brief's
guard — *we must not solve JPM by turning insurers or diversified
financial companies into banks* — is not tested by the insurers, which
a marker rule leaves alone. It is tested by the two interest-based
filings whose business is not deposit-taking lending, and a
marker rule **cannot tell them from JPMorgan**: all three print one
line, `Net interest income`, at 5 of 5, and nothing else on the face of
the statement separates them.

The one quantity that might have separated them is not computable:

| Symbol | NII / total revenue |
|---|---|
| JPM | 95,443 / 182,447 = **52.3%** |
| GS | 13,559 / 58,283 = **23.3%** |
| the other ten | `total_revenue` **not located** — not computable |

**A magnitude refinement is unevaluable on 10 of the 12 filings it
would have to judge**, which is S5.1's rule arriving from a new
direction: *a gate that cannot be evaluated fails.* A refinement that
silently passed those ten would be a threshold that never ran.

**The measured false positives are outside this corpus and already on
the record.** `BANK_PRUDENTIAL_EVIDENCE.md` establishes that AGNC, NLY
and ARCC "are interest-spread businesses — a mortgage REIT earns almost
nothing but net interest, and would read `INTEREST_BASED` the moment
this platform reads its income statement", and that none of them
mentions CET1 or the LCR "because none is a prudentially-regulated
bank." So the rule's false-positive population has been measured; it is
simply not represented in these 24. **A corpus containing no
counterexample is not a corpus that refutes one.**

**MUFG is a second ambiguity, of a different kind.** It establishes
`Net interest income` = 3,684,254 at 5/5 and **nothing else at all** —
no total revenue, no net income, no gross profit, no operating income.
Its language reads `interest based` on a single located line. The
`_was_read` guard passes (`located_facts` is non-empty), so the
statement counts as read. One marker with no corroborating figure
anywhere on the same statement is the weakest evidentiary state a
positive language claim can be in, and today nothing distinguishes it
from JPMorgan's, which sits beside a located revenue and a located net
income.

**ALL is the third.** An insurer reading `NEITHER` is a false negative
already present in the corpus, and it means the buckets are not three
classes of company — they are two positive findings and one absence.

---

## 4. BQ coverage: before → counterfactual after

The counterfactual applied: `BANK` for the 12 interest-based filings,
`GENERIC` for the other 12. Compared against today's all-`GENERIC`
baseline, per company, on the full `BusinessQuality` object and on the
`ScoreBasis` the dossier and the decision actually receive.

| | today | counterfactual |
|---|---|---|
| HIGH | 3 — DIS, GS, TRV | **3 — DIS, GS, TRV** |
| MEDIUM | 4 — AAPL, CB, JPM, PG | **4 — AAPL, CB, JPM, PG** |
| LOW | 1 — MET | **1 — MET** |
| UNKNOWN | 16 | **16** |
| companies answering 0 questions | 7 — BCS, C, DB, KO, MTB, MUFG, RF | **7 — the same seven** |
| companies answering 1 question | 9 | **9 — the same nine** |
| **bands changed** | | **0 of 24** |
| **scores changed** | | **0 of 24** |
| **answered-question counts changed** | | **0 of 24** |

**Which questions become readable: none.** Not one `QuestionAnswer`
moves from `NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS` to `ANSWERED`
anywhere in the corpus, under either model, for any of the three
quality questions.

**Resulting HIGH / MEDIUM / LOW: 3 / 4 / 1, unchanged.**

### What does change: ten refusal sentences, and they are the finding

`ScoreBasis` — the object carrying quality to the dossier and to
`DecisionEvidence` — differs for **10 of 24** companies, in wording
only. Citigroup is the clearest specimen:

> **today** — *"Gross margin needs gross_profit, which is not
> established: the reading located no cell holding the company's gross
> profit … (5 of 5 observations.)"*
>
> **under `BANK`** — *"Net margin needs net_income, which is not
> established: the reading located no cell holding the company's net
> income … (5 of 5 observations.)"*

Both are true. Only the second is **actionable**: Citigroup prints a net
income line and this platform failed to locate it, so the sentence names
evidence that can be acquired. The first names gross profit, which a bank
does not print, so it sends the reader after a line that does not exist —
an acquisition demand phrased against a document that will never satisfy
it.

That is a real product gain. §7 shows it is not a model-selection gain.

### The one place `BANK` is strictly worse

Selecting `BANK` for **WMT** — which no marker rule would do, but which
any shape-based or absence-based rule might — moves it from 1 answered
factor to 0. Walmart establishes operating margin and not net margin, so
`BANK`'s narrowing deletes the one profitability answer it had. Band is
UNKNOWN either way; the platform simply knows less.

### Outside Business Quality, `BANK` does have an effect

`BANK` declines `LEVERAGE` and `CASH_GENERATION`. Over the 12
interest-based filings that converts **4 answered leverage verdicts**
(AXP, GS, JPM, RF — each `weak`) and **8 leverage gaps** into
`NOT_APPLICABLE_FOR_PLAYBOOK` with a named demand (CET1, Tier 1, the
regulatory leverage ratio). Business Quality excludes leverage
deliberately, so none of this reaches a band; it is visible only in
`movrvest financials`.

**A side observation, recorded and not acted on**: the generic leverage
rule returns `weak` for **9 of 9** companies whose liabilities-to-equity
is established, from 2.61× (CB) to 25.22× (MET) — Apple at 3.87× included.
Over this corpus that question discriminates nothing. It is out of BQ2's
scope and belongs to whoever next opens the balance-sheet analyst.

---

## 5. JPM before → after, causally

**Before.** MEDIUM, 62. Profitability *excellent* — net margin 31.3%,
`"Net income" $57,048` over `"Total net revenue" 182,447` under `"2025"`,
table 0 of the consolidated statements of income. Revenue growth *weak*
(+2.8%). Earnings growth *declining* (−2.4%). One favourable of three
answered → 33% → MEDIUM → 62. Profitability carries two gaps: gross
margin and operating margin, each 5 of 5 unlocated.

**After, under an independently selected `BANK`.** MEDIUM, 62. Same
three verdicts, same figures, same cells, same arithmetic, same band,
same score. Two things change and neither is a number:

1. the two gap sentences disappear, because `BANK` narrows
   profitability to net margin;
2. the answer's `confidence` rises from **0.333 to 1.0** — one of three
   consulted measures established, against one of one.

**Neither reaches an investor.** `QualityFactor` carries no confidence
field, so the 1.0 is dropped by `assess()`. `QualityFactor.gaps` is
consumed nowhere outside its own construction — the evidence builder
reads `factor.evidence` and `factor.because`, and JPM's profitability is
*answered*, so its `because` is `None`. JPM's `ScoreBasis` is
**byte-identical** under both models.

**So the exact causal explanation for JPM is: nothing changes.** The
platform's reading of JPMorgan is not currently limited by its financial
model. It is limited by having three questions, two of which JPMorgan
answers unfavourably.

The confidence figure is worth one sentence of its own, because it is
the only true statement `BANK` adds anywhere: this platform currently
records 33% confidence in JPMorgan's profitability because it is missing
two lines a bank never prints. That is a misstatement of its own
certainty. It is invisible today, and it would become a defect the
moment any surface rendered confidence.

---

## 6. Does the independence law survive?

The law has three clauses. They fare differently, and the third is the
one that fails.

### Clause 1 — *selection may be established independently from financial-statement semantics*

**Survives, for language. Fails, for `BANK`.**

The corpus establishes financial *language* independently, at 5 of 5
across 24 companies with no false positive in either direction —
reproduced here from the store. What it does not establish is
`FinancialModel.BANK`, and the reason is not a missing threshold. `BANK`
declines two questions on grounds of deposit funding and regulatory
capital; selecting it from an interest subtotal asserts both from
evidence that mentions neither, and would tell an investor that a
company's leverage awaits a CET1 ratio it may not be required to hold.
That is Invariant 10 — *an established number is authority to report
the number, not authority to invent what the number means*.

The law survives clause 1 only if what is selected independently is
renamed to what the evidence establishes. This platform already has
that name and already computes it: `StatementLanguage`.

### Clause 2 — *absence of narrative knowledge must not make strong financial evidence unreadable*

**Survives, and is already satisfied — the premise it guards against is
false.**

Measured: 0 of 24 companies have any readable narrative understanding,
and grounded Business Quality still reads all 24 statement corpora,
answers 33 of the 72 quality questions it asks, and bands 8 companies.
Narrative absence does not make
financial evidence unreadable today. It makes the `movrvest financials`
CLI fall back to a `GENERIC` model, which for the three quality
questions is the same question set.

### Clause 3 — *if both routes exist and disagree, authority should withdraw*

**Unexercisable, and structurally unrepresentable.**

*Unexercisable*: 0 of 24 companies have both routes, so the corpus
contains no specimen on which the clause could be tested — and it
cannot be constructed offline, because a narrative route needs a funded
schema-14 observation.

*Unrepresentable*, which matters more. `FinancialModel` has two members
and no third state for *withdrawn*. `questions_for` falls back to
`GENERIC` for any model it does not own. So a withdrawal expressed as
`GENERIC` would be **indistinguishable from a positive generic
selection** — exactly the collapse `AnswerState` exists to prevent one
layer down, where *"we could not measure it"* and *"that is the wrong
question"* are kept apart by construction. And the collapse is already
present: `quality_of` defaults to `GENERIC`, so *no model established*
and *generic established* are the same value at the only live call
site.

Making clause 3 real therefore requires a new enum member or an
`Optional[FinancialModelSelection]` threaded through `questions_for`,
`answer_questions` and `quality_of` — a taxonomy change and a seam
change, which Constitution §23–24 places behind the owner.

### Verdict

**The independence law survives as law and has nothing to run on.** It
is a correct statement about how two routes should relate. Today one
route is dark, the other cannot reach the conclusion the law is about,
the disagreement clause has no representation in the type system, and
the arbitration it would perform would change no band, no score and no
answered question for any company this platform holds.

---

## 7. The smallest implementation slice

**Recommendation: do not implement independent financial-model
selection.** It has a measured product value of zero bands, zero scores
and zero newly answerable questions, and it would spend a taxonomy
change and a seam change from a frozen architecture to buy them.

The dependency on narrative classification is **not necessary** — it is
inert. Nothing is waiting on it. `FINANCIAL_DOMAIN_BOUNDARY.md` should
stand unchanged, and `model_for` should keep its single caller.

### What the corpus substituted, and what it is worth

The one real defect BQ2 found is the refusal wording in §4, and the
measurement says it is **larger than banks and not reachable by a
model boundary**:

> **22 of 24 companies** carry at least one profitability gap naming a
> measure whose statement concept is **5 of 5 unlocated** — a line this
> platform has looked for five times and never found.

The population is not the banks. It includes every insurer (ALL, CB,
MET, TRV), the railway (UNP), the industrial (HON), the beverage
company (KO) and Procter & Gamble. `FinancialModel.BANK` reaches **at
most 12 of the 22**, and would reach them by asserting prudential
status this platform cannot evidence.

The general shape of the defect is not about what kind of company it is
at all. It is this: **`FinancialUnderstanding` already knows, at 5 of 5,
that the filer's statement establishes nothing for a concept — and the
answer layer still words that as an acquisition demand.** Concept
location across the corpus:

| Concept | located |
|---|---|
| `net_income` | 18 of 24 |
| `total_revenue` | 12 of 24 |
| `net_interest_income` | 12 of 24 |
| `operating_income` | 6 of 24 |
| `premium_revenue` | 3 of 24 |
| `gross_profit` | **3 of 24** |

### The candidate slice, described and not built

Not proposed for the freeze exemption — described so the owner can rule
on it, and deliberately smaller than anything BQ2 was scoped to build.

**Word a 5-of-5 unlocated concept as the filer's silence rather than as
this platform's demand.** The distinction already exists one layer down
(`AnswerState` separates a gap in evidence from a wrong question) and
the input already exists (`Agreement` on the consensus fact records
5/5). What is missing is that the profitability answer's gap sentence
does not consult it.

Three properties that make it small:

- **It adds no concept, no question, no threshold, no model and no
  taxonomy member.** It changes how one existing absence is worded.
- **It is arithmetic-neutral by construction** — the sentence is
  attached to a factor that already contributes nothing and already
  stays out of the denominator. A test asserting the decision corpus is
  byte-identical would be the gate.
- **It is model-independent**, which is why it reaches 22 companies
  where a bank model reaches 12.

**What it deliberately does not do**: claim the filer does not print
the line. This platform has read one region of one filing five times;
that supports *"no such line was located in the statement this platform
read, in five readings"* and not *"this company prints no gross
profit"*. `movrvest statement-shape` already owns that stronger
distinction, and the wording should borrow its discipline rather than
its conclusion.

### Also recorded, not proposed

1. **`quality_of` defaults to `GENERIC` and the pipeline passes no
   model.** *No model established* and *generic established* are one
   value. Harmless today because the two ask the same three questions;
   it is the seam clause 3 would have to fix first.
2. **JPMorgan's profitability confidence is 0.333 for want of two lines
   a bank does not print**, and is dropped before any surface. A defect
   in waiting, not one in flight.
3. **The generic leverage rule returns `weak` for 9 of 9 established
   companies**, 2.61× to 25.22×. It discriminates nothing over this
   corpus and belongs to the balance-sheet analyst's next slice.
4. **MUFG's language rests on one located line with no corroborating
   figure on the same statement.** `_was_read` passes on
   `located_facts` being non-empty, so one marker and nothing else is
   currently a sufficient basis for a positive language claim.
5. **`total_revenue` is located for 12 of 24 and is the single largest
   proximate blocker** of grounded quality — it gates net margin and
   revenue growth both. Whether that is label coverage or a locator
   limit cannot be settled offline: the store holds located cells only,
   so the rows a reading rejected are not enumerable from this
   checkout. KO is the sharpest specimen — its income-statement table
   was demonstrably read (gross profit at table 0 row 3, operating
   income at row 6) and no revenue row was located above them.

---

## Scope compliance

No implementation. The legacy Quality ruler was not touched. No schema
was migrated and narrative schema 11/12 was not restored. No API credit
was spent and no model call was attempted. No Swiss acquisition. No
Business Quality question was invented, no financial threshold changed,
no narrative concentration integrated into scoring, and no financial
concept added. No output was tuned toward a known company: every claim
above is a figure read back from `data/statements` or a diff between two
executions of existing code, and each is reproducible offline.

**Gates at the time of writing** (Python 3.12 venv, fresh install):
`ruff` clean; `mypy app` clean on 586 files once `types-PyYAML` is
installed (the sole error is a missing stub, not a typing defect);
`pytest` **2633 passed, 7 failed, 1 error** — every failure is a crypto
route test unable to reach `mempool.space` through the cloud
environment's egress proxy (403 on the tunnel), and 88 proxy errors are
the only cause. `tests/test_financial_questions.py`,
`tests/test_business_quality.py` and `tests/test_score_derivation.py`
pass, 64 of 64. **No source file was modified by this slice.**
