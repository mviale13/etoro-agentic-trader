# BQ2 brief — Financial-model selection independence

**The owner's brief for the BQ2 research slice, recorded verbatim so a
fresh session can execute it without prior context. Research only.**

Do not redesign Business Quality. Investigate one measured blocker from
BQ1: financial grounded quality can answer from current statement
evidence, but `FinancialModel.BANK` cannot be selected when the
narrative understanding/playbook route is unavailable.

Determine whether financial-model selection can be earned from the
financial evidence itself, using semantics already represented in the
repository, rather than requiring narrative classification.

## Start with the existing domain

Trace: `FinancialModel`; `model_for`; BANK vs GENERIC; the existing
semantic statement concepts; how `NET_INTEREST_INCOME`,
`PREMIUM_REVENUE`, deposits or other domain-specific concepts are
represented; and every current dependency on archetype / playbook /
narrative understanding.

**Do not add new financial concepts initially.**

## Measure the 24-company statement corpus

For every company with readable `FinancialUnderstanding`, determine
whether its existing statement evidence independently supports: BANK;
GENERIC; conflicting models; or insufficient evidence.

**Do not infer from company name, ticker, sector, Yahoo industry or
general knowledge.** Use only semantics already established from
checked financial-statement evidence.

## Try to falsify the obvious rule

It was previously observed that `NET_INTEREST_INCOME` is characteristic
of banks and `PREMIUM_REVENUE` of insurers. **Do not simply encode
`NET_INTEREST_INCOME present => BANK`.** Test it against the corpus and
the domain semantics.

Look particularly at: **JPM, GS, MET, CB, TRV**, and ordinary
industrial/technology companies.

**We must not solve JPM by turning insurers or diversified financial
companies into banks.**

## Independence law to test

> Financial-model selection may be established independently from
> financial-statement semantics. Narrative/playbook classification may
> corroborate or disagree with it, but absence of narrative knowledge
> must not make strong financial evidence unreadable.
>
> If both routes exist and disagree, authority should withdraw rather
> than one silently overriding the other.

Test this against the current architecture **before** implementing it.

## Product impact — counterfactually measured

- how many of the current 16 UNKNOWN grounded-quality companies become
  answerable if financial-model selection is independent;
- which questions become readable;
- resulting HIGH / MEDIUM / LOW;
- exact causal explanation for JPM;
- false-positive candidates.

**Correctness matters much more than coverage.**

## Scope guard — do not

- touch the legacy Quality ruler;
- restore narrative schema 11/12;
- build a schema migration;
- spend API credits;
- add Swiss acquisition;
- invent Business Quality questions;
- integrate narrative concentration into scoring;
- change financial thresholds;
- tune results to known companies.

Research first. If the corpus demonstrates a small existing-semantic
boundary that safely removes the narrative dependency, **describe the
implementation slice and stop for ruling**. Otherwise report why the
dependency is actually necessary.

## Deliverable

Report:

1. current model-selection dependency graph;
2. financial-semantic classification of all 24 statement companies;
3. ambiguous/conflicting specimens;
4. BQ coverage before → counterfactual after;
5. JPM before → after;
6. whether the independence law survives;
7. smallest implementation slice, if justified.

**No implementation. Stop for ruling.**

---

## Operating notes for the executing session

These are environment facts measured on 2026-08-16, not part of the
owner's brief:

- **No broker or model-provider credentials exist in a cloud
  checkout.** Anything touching eToro or an LLM will fail; that is
  expected and is not a defect to repair. The owner's OpenAI balance is
  exhausted — **do not attempt model calls.**
- `data/statements` (24 companies) and `data/knowledge` (33) **are
  tracked in git**, so the corpus is present. `data/cache` is
  gitignored and absent, so anything reading it reads empty.
- The whole measurement is **offline**, through existing services:

  ```python
  from app.services.company_understanding_service import CompanyUnderstandingService
  from app.services.business_quality_service import quality_of

  service = CompanyUnderstandingService()
  graded = quality_of(
      symbol, service.understanding(symbol).financial
  )  # model= is the crux
  ```

  `quality_of`'s third parameter is `model: FinancialModel`, defaulting
  to `GENERIC` — passing `BANK` changes which questions are asked, and
  that is exactly the lever BQ2 is measuring.
- Setup in a fresh clone:
  `python -m venv .venv && source .venv/bin/activate && pip install -e . && pip install pytest ruff mypy`.
  Gates: `python -m pytest -q`, `python -m ruff check .`, `python -m mypy app`.
- **BQ1's measured baseline** (`BUSINESS_QUALITY_OBSERVATION.md`):
  grounded quality answers for 8 of 24 today — HIGH DIS/GS/TRV, MEDIUM
  AAPL/CB/JPM/PG, LOW MET, 16 UNKNOWN of which 7 answer nothing at all
  (BCS, C, DB, KO, MTB, MUFG, RF) and 9 answer one question (ALL, AXP,
  COF, FITB, HON, NWG, TSLA, UNP, WMT). JPM reads MEDIUM: net margin
  31.3% excellent, revenue +2.8% weak, earnings −2.4% declining, with
  gross and operating margin recorded as gaps because a bank prints
  neither line.
- Verify HEAD in isolation before trusting the commit
  (`git archive HEAD | tar -x -C /tmp/headcheck`, then mypy + pytest
  there) — pre-commit leaves untracked files in place and has shipped a
  commit that imported files it did not contain.
