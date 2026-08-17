# HON, five readings: predicted and observed

**Status: BQ18, executed. Clone rehearsed, production executed. 10 model
calls, 10 successful, 0 failed, 0 retries. One tracked file mutated.**

> **Predicted before observation, observed after: identical.** HON's
> grounded Business Quality moved **UNKNOWN 1/3 → MEDIUM 62, coverage
> 3/3**, with revenue growth `moderate`, earnings growth `declining` and
> profitability `strong` — exactly the deterministic expectation BQ17
> recorded before a single model call was made.
>
> **Extraction was perfectly repeatable**: all five readings, on both
> roots, returned the same three periods, the same figures and the same
> cell addresses. `5 of 5 agree` on every concept.

---

## 1. Provider and model actually used

**OpenAI · gpt-5**, resolved through `_resolve_provider`'s default
(`MOVRVEST_READER_*` empty is *not* unconfigured). Confirmed by
construction before spending, which makes no network call. Timeout 180s
per reading; five readings completed in **43 seconds** on the clone and
**42 seconds** on production.

## 2. Clone supersede

Exactly the audited quorum, and nothing else:

- 5 stored HON income readings → **0 authoritative, 5 withdrawn** (still
  stored, as designed)
- `financial.quorate` → None · `BusinessQuality` → **None** ·
  `security_evidenced` → **False** · wording reverts to *"No
  security-level analysis is available for HON"*
- **Blast radius: one file.** `HON.0000773840-26-000013.json` changed;
  the knowledge, cache and events stores were **byte-identical** to
  production.

This is the intermediate state BQ17 predicted, reproduced exactly — and
the reason the two steps had to be one session.

## 3. The five clone observations

| # | status | periods | Net sales | Net income |
|---|---|---|---|---|
| 1 | acquired | 2025 / 2024 / 2023 | 37,442 / 34,717 / 33,009 | 4,772 / 5,740 / 5,672 |
| 2 | acquired | identical | identical | identical |
| 3 | acquired | identical | identical | identical |
| 4 | acquired | identical | identical | identical |
| 5 | acquired | identical | identical | identical |

No abstention, no extraction failure, no retry, no selective discard.
Consensus: **`located: 5 of 5 agree`** on every concept — including the
five correctly reported **absent** (`gross_profit`, `operating_income`,
`revenue_net_of_interest_expense`, `net_interest_income`,
`premium_revenue`), each with the refusing contract's own sentence.

Cell addresses agreed to the column: `t0 r5 c3/c9/c15` for Net sales,
`t0 r21 c3/c9/c15` for Net income.

## 4–5. Clone result and propagation

```
band=MEDIUM score=62  coverage=3/3  favourable=1
  profitability    answered  strong     1 point
  revenue_growth   answered  moderate   0 points
  earnings_growth  answered  declining  0 points
```

- `security_evidenced` **restored to True**
- `DecisionEvidence.quality_score` = **62**, `grounded_quality` carried
  (band MEDIUM)
- score basis is **grounded**: *"1 favourable of 3 answered → 33% →
  MEDIUM → 62 … from 10-K 0000773840-26-000013"*, rules
  `['quality-grounded@1']`
- investor wording follows the same object: *"The opportunity merits
  deeper research before a thesis can be prepared"*, with the review
  condition naming the **market** gap only
- **no provider override**: HON has no provider row at all, and the
  string *"Quality data is unavailable"* appears nowhere

The clone passed all seven acceptance gates, so production proceeded.

## 6–7. Production execution

Same operation, **no code, prompt or configuration change between clone
and production**. Supersede at 22:52:07, observation complete 22:52:49.

All five production readings are byte-equivalent to the clone's: periods
`2025 / 2024 / 2023`, values `37,442 / 34,717 / 33,009` and
`4,772 / 5,740 / 5,672`, `5 of 5 agree`.

## 8. Production before → after

| | before | after |
|---|---|---|
| authoritative readings | 5 | **5** (the fresh ones) |
| refuted / withdrawn | 0 | **5** (still stored) |
| periods represented | `Years Ended December 31,` only | **2025 / 2024 / 2023** |
| profitability | answered, `strong` | answered, `strong` |
| revenue growth | not answerable | **answered, `moderate`** |
| earnings growth | not answerable | **answered, `declining`** |
| BusinessQuality | **UNKNOWN** | **MEDIUM** |
| coverage | 1/3 | **3/3** |
| score | none | **62** |
| `security_evidenced` | True | True |
| quality basis | *"1 of 3 factors answered — fewer than 2, so no band is claimed"* | *"1 favourable of 3 answered → 33% → MEDIUM → 62"* |
| investor wording | *"Business quality was assessed … and could not be concluded"* | *"The opportunity merits deeper research before a thesis can be prepared"* |

Conviction remains **withheld** — HON cites no supporting reason, which
is DV2's rule and correct: it has filing evidence and no market analysis.

## 9. Predicted versus observed

| | predicted (BQ17, pre-observation) | observed |
|---|---|---|
| revenue growth | +7.85% → `moderate` | **`moderate`** |
| earnings growth | −16.86% → `declining` | **`declining`** |
| profitability | `strong` | **`strong`** |
| factors passed | 1 of 3 | **1 of 3** |
| band | MEDIUM | **MEDIUM** |
| score | 62 | **62** |

**Exact match on every term.** Nothing was tuned, injected or retried to
reach it.

## 10. Extraction consistency

Perfect across ten readings on two roots: same three periods, same six
figures, same six cell addresses, same five absences with the same
reasons. The single discriminating fact between the old and new quorum is
the **period header** — `'Years Ended December 31,'` against
`'2025'/'2024'/'2023'` — which is precisely the rowspan defect BQ28
repaired, and precisely what made growth unanswerable.

## 11. Spend

| | |
|---|---|
| attempted | **10** (5 clone + 5 production) |
| successful | **10** |
| failed | **0** |
| retries | **0** |
| provider / model | OpenAI · gpt-5 |

No unrelated model call was made. Both `statement-audit` runs and every
verification are deterministic and model-free.

## 12. Production data mutations

**One tracked file:**

```
M data/statements/HON.0000773840-26-000013.json
```

Fingerprints before → after:

| store | before | after |
|---|---|---|
| `statements` | `02d6490d…` | `a148e451…` |
| `knowledge` | `1951d79c…` | **unchanged** |
| `events` | `2ff3b1e5…` | **unchanged** |
| `cache` | `245c479b…` | changed — the SEC filing fetch cache, **gitignored** (`.gitignore:28`) |

Corpus-wide, exactly one company moved: **HON, UNKNOWN → MEDIUM**. The
band tally went `HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14` →
`HIGH 3 · MEDIUM 5 · LOW 3 · UNKNOWN 13`. AAPL, UNP, DIS, GS, JPM and KO
are all unchanged.

## 13. Divergence

**None between prediction, clone and production.**

Two corpus pins moved with the evidence and were re-pinned — neither is a
code defect, and both are the deliberate act those pins exist to force:

- `test_the_production_bands_are_exactly_what_bq23_left` — the tally,
  moved by exactly one company;
- `test_the_concept_appears_only_where_it_was_natively_asked` —
  `{GS, JPM, AXP}` gains `HON`, because a reading produced today carries
  today's vocabulary contract. **The test's own `asked == stamped`
  assertion passed for HON**, which is BQ16/BQ17's per-concept provenance
  working as designed rather than an exception being made for it.

No code changed. `pytest -q` 3062 passed · ruff check + format clean ·
`mypy app` clean (598 files).

## 14. Recommendation for the next BQ step

**The HON question is closed.** The parser repair is now proven
end-to-end: a deterministic defect was found, repaired, its stale
evidence withdrawn, and fresh evidence acquired that propagates through
grounded quality to the decision layer and the investor wording — with
the outcome predicted before the spend and matched exactly.

The natural next target is the **remaining UNKNOWN 13**, and BQ18 gives a
method for choosing among them rather than guessing: BQ17's audit
distinguished acquisition, extraction, grounding, scoring, propagation,
gating and wording failures, and HON's turned out to be extraction alone.
**KO is the nearest specimen** — 0 of 3, blocked by a contested
`total_revenue` rather than a parse — and its cause is already ruled on
elsewhere, so the honest next question is whether any of the remaining
thirteen share HON's shape. That is a free audit, not a spend.
