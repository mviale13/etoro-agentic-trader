# Grounded Business Quality: what it already says, and what is actually dark

**Status: research/observation report. No implementation. Two
operational blockers reported rather than designed around. Stopped for
ruling.**

BQ1 asked to restore the grounded Business Quality path, re-observe
seven specimens, and inspect what investment intelligence it produces.

**The first finding replaced the brief's premise: grounded Business
Quality is not dark, and the schema mismatch is not what stops it.**
It answers today, from filing evidence, for eight of the
twenty-four companies whose statements the platform holds — AAPL, JPM
and PG among them. What the schema mismatch blocks is a *different*
route: business understanding, archetype and playbook. The audit that
prompted this slice conflated the two, and this report separates them.

---

## 1. The failure, established precisely

**Two evidence streams, two stores, two schemas — and only one is
broken.**

| Stream | Store | Reader wants | Stored | Readable |
|---|---|---|---|---|
| narrative knowledge (segments, descriptions, ownership) | `data/knowledge`, 33 companies, 75 observations | **14** | **11 (31 companies), 12 (2)** | **0 of 75** |
| financial statements (income, balance, cash flow) | `data/statements`, 24 companies | **3** | **3** | **all** |

Corrections to the bottleneck audit's account, both measured:

- The knowledge corpus is **schema 11 and 12**, not uniformly 12.
  `PREVIOUS_SCHEMA_VERSION` and `RELABELED_SCHEMA_VERSION` are both
  `None`, so `_restore` returns `()` for any version other than 14 —
  the gate is structural, exactly as described, and no code defect
  contributes.
- **Grounded Business Quality does not read that store at all.**
  `quality_of(symbol, understanding.financial, model)` consumes
  `FinancialUnderstanding` — the statement stream, which is schema 3
  and current. The "0 of 80" the audit reported is
  `movrvest playbook-coverage`, which measures the *narrative* route.
  Both numbers are real; they are answers to different questions.

**A second measurement that changes the cost of any re-read.** Of the
33 companies in the knowledge corpus, **24 hold a single observation**
and only **9 ever reached the quorum of 5** (BNP.PA, CAT, DIS, JPM,
META, NFLX, NVDA, UMI.BR, VOW3.DE — one of them twice). A restoration
is therefore not "33 companies × 5 readings": for 24 of them the
platform never had quorate narrative knowledge under *any* schema.

## 2. Operational blocker — funded observation is unavailable

`movrvest observe AAPL` and `movrvest archetype JPM`, both live:

```
OpenAI could not complete the request: Error code: 429 —
'You have no credits remaining.'  type: insufficient_quota,
code: credit_balance_exhausted
```

The reader is *configured* correctly (`openai`, `gpt-5`, key present,
164 chars) and fails only on billing. No schema-14 observation of any
specimen was possible, and none was attempted beyond the one call that
established the blocker. **Nothing was redesigned around it, and no
migration fabricating schema-14 evidence from schema-11/12 records was
built.**

**A second blocker, independent of funding: Nestlé cannot be observed
at all.** It is absent from both stores under every identifier
(`NESN`, `NESN.SW`, `NESN.ZU`), and it is **not in
`EUROPEAN_ISSUERS`** — the registry of 30-odd European filers whose
reports the platform can fetch. Swiss issuers are absent from that
list entirely. So the seventh specimen is blocked by acquisition
coverage, not by credits: funding alone would not produce it.

## 3. What the existing intelligence actually says — measured today

`quality_of` over all 24 companies with statements. This required no
funding and no re-observation; it is what the platform holds.

| Band | Count | Companies |
|---|---|---|
| HIGH (80) | 3 | DIS, GS, TRV |
| MEDIUM (62) | 4 | AAPL, CB, JPM, PG |
| LOW (40) | 1 | MET |
| UNKNOWN | 16 | 7 with nothing answered, 9 with one factor |

The three questions, each answered from checked filing cells:
**profitability** (*How profitable is this business on the revenue it
earns?*), **revenue growth** (*Is what this business earns growing?*),
**earnings growth** (*Is what this business keeps growing?*), with two
dimensions deliberately excluded and documented (cash generation,
leverage).

### The specimens

**AAPL — MEDIUM (62), 1 of 3 favourable.** Profitability *excellent*
(gross 46.9%, operating 32.0%, net 26.9%, all from cells in the
2025 10-K's consolidated statements); revenue growth *moderate*
(+6.4%, 416,161 against 391,035); earnings growth *moderate* (+19.5%).
Nothing missing.

**JPM — MEDIUM (62), 1 of 3 favourable.** Profitability *excellent*
on net margin 31.3% ($57,048 over $182,447); revenue growth **weak**
(+2.8%); earnings growth **declining** (−2.4%, $57,048 against
$58,471). Gross and operating margin are recorded as *gaps* with the
filing's own reason: a bank prints neither line — the Financial Domain
Boundary appearing in the output rather than as a silent zero.

**PG — MEDIUM (62), 1 of 3 favourable.** Profitability *strong*
(operating 22.7%, net 18.5%); revenue growth *weak* (+3.3%); earnings
growth *weak* (+0.5%). Gross margin gapped for the same structural
reason.

**TSLA — UNKNOWN, 1 of 3 answered.** Profitability *weak* (gross
18.0%, operating 4.6%, net 4.1%). Both growth questions are
`not_answerable_from_established_facts`, with a precise reason: *the
row "Total revenues" prints no earlier period this platform can date
from the filer's own column headers*. A comparative column exists in
the filing; the locator cannot date it. **This is the one place a
small, real defect may sit** — see §6.

**GOOG — no statement observations and no readable narrative
knowledge.** Its stored knowledge file is schema 11 with a single
observation. Nothing to report; nothing was invented.

**VOW3.DE — the structural specimen, and the news is good.** It has no
statement observations, so grounded quality returns nothing. But the
stored schema-12 record (forensic read of the JSON, not a migration)
shows the Volkswagen structure **intact and correctly attributed**:
three segments — *Pkw und leichte Nutzfahrzeuge*, *Nutzfahrzeuge*,
*Finanzdienstleistungen* — each carrying a revenue share as a checked
cell pair against the group total (244,484 / 321,913 = **75.9%**,
the exact figure the DP1 attribution repair was measured on).
Descriptions are `null`, each with an `undescribed_because` recording
that the reader found no describing words in the text it reads. So
identity and size survived the repaired attribution boundary; the
description claim is separately absent, which is Invariant 4 behaving
as designed.

**JPM's 5/5, reconciled.** The previously measured 5/5 filing
knowledge is real and still on disk: five observations, each reading
the same three segments (CCB, CIB, AWM) with revenue shares as checked
cells and descriptions carrying `ownership: "proximity"`, a quoted
span, and four `revenue_models` (services, transaction, financial
spread, asset-management fees). It is unreadable **only** because
schema 12 predates DP1's ownership partition — the change that cannot
pool. Meanwhile JPM's *statement* evidence is fully readable, which is
why the platform can already grade JPM's profitability and growth
while knowing nothing, today, about its segments.

## 4. Product evaluation — is this better than cap + EPS + dividend?

**Yes, and the comparison is sharpest exactly where the legacy ruler
is most confident.**

| | legacy three-factor ruler | grounded Business Quality |
|---|---|---|
| JPM | large-cap ✓, positive EPS ✓, pays a dividend ✓ → **HIGH** | **MEDIUM**: excellent margin, **+2.8% revenue, −2.4% earnings** — a business whose earnings are shrinking |
| AAPL | HIGH | MEDIUM: excellent margin, moderate on both growth axes |
| PG | HIGH | MEDIUM: strong margin, weak growth (+3.3% / +0.5%) |
| TSLA | MEDIUM at best (pays nothing) | UNKNOWN — and says *why*: the growth rows cannot be dated |

The legacy ruler cannot express *"earnings are declining"* about
anything: it has no question that could produce that sentence. Three
of the four specimens it would call HIGH are MEDIUM here, each for a
reason quoted from the filing with the cell that produced it. And the
grounded route's failures are *legible* — TSLA's UNKNOWN names the
missing evidence, where the legacy ruler's UNKNOWN names only its own
incompleteness.

The honest limits, equally measured: the grounded route today says
nothing about **16 of 24** companies; its band is a share of three
correlated financial-statement questions, not a judgment of business
quality; and its HIGH population (DIS, GS, TRV) is not obviously a
better investment set than its MEDIUM one (AAPL, JPM, PG) — a
three-question ruler over two years of one statement cannot separate
those, and should not be read as if it could.

## 5. Comparing the specimens — what discriminates, what is missing

**Questions that genuinely discriminate.** All three do, and they
diverge from each other, which is the useful part: DIS (weak revenue,
strong earnings), GS (moderate, strong), JPM (weak, declining), MET
(moderate, declining), TRV (moderate, strong). Revenue growth and
earnings growth are **not** redundant — the gap between them is
operating leverage, and the corpus shows it in both directions.
Profitability discriminates across the full verdict range
(excellent / strong / weak) and is the only question answerable for
almost everyone.

**Where the answer is evidence-poor despite abundant filings — and it
is structural, not scarcity.** Of the 16 UNKNOWNs, **seven answer
nothing at all** (BCS, C, DB, KO, MTB, MUFG, RF) and nine answer
exactly one. The population is dominated by banks: they print no gross
profit and no operating income, so two of the three profitability
measures are unavailable by the nature of the statement, and several
print comparatives the locator cannot date. These filings are large
and complete; the platform's questions simply do not fit them.
`FinancialModel.BANK` exists for precisely this and **cannot be
selected**, because `model_for` derives it from the business playbook
— which is the route the schema mismatch has darkened. The two
blockers therefore compound: the narrative outage is what keeps every
bank on the generic question set.

**Dimensions the existing system never asks.** Cash generation and
leverage are excluded *with reasons on the record*. Beyond those: no
capital efficiency (ROIC), no competitive position, no revenue
durability or recurring share, and — most striking — **no use of the
narrative evidence at all**. The knowledge stream measures segment
concentration and revenue models; VW's 75.9% single-segment
concentration and JPM's four revenue models are exactly the kind of
fact a quality judgment wants, and `quality_of` receives only
`understanding.financial`. The two halves of `CompanyUnderstanding`
never meet.

**Do different archetypes need different questions?** **Measured yes,
twice.** Banks cannot answer gross margin at all — not a gap in our
reading but a fact about their statements — and insurers (ALL, CB,
MET, TRV) answer a different subset again. A single generic question
set applied to all 24 is why 16 are UNKNOWN. The platform already
holds the vocabulary for this (`FinancialModel`, and the ruling that
what a company *is* and how it is *read financially* are two
classifications); what it lacks is a route to select it that does not
depend on the dark narrative path.

## 6. The one candidate defect — reported, not fixed

TSLA answers profitability from its income statement but neither
growth question, because *"the row prints no earlier period this
platform can date from the filer's own column headers"*. Tesla's 10-K
does print comparative columns. Whether this is a locator limitation
worth repairing, or a filing whose header shape genuinely defeats
dating, needs its own measurement over the corpus — the same
population (9 UNKNOWNs answering exactly one question) is where any
gain would land. **Not touched here**, since BQ1 forbids redesign and
this is not preventing the path from operating as designed.

## 7. What Business Quality v2 should mean — from the measurements

Recommended for ruling, in the order the evidence supports:

1. **Restore funding, then re-observe narrowly.** Both quality routes
   need the same operational unblock, and the narrative one needs
   nothing else. The cheapest informative set is the two companies
   that already prove the pipeline end-to-end — **JPM and VOW3.DE**
   (5 readings each at quorum) — because they are the only specimens
   whose schema-12 evidence shows what a successful reading looks
   like.
2. **Let the two halves meet.** The single largest product gain
   available without new questions is passing the narrative
   understanding into the quality judgment: segment concentration and
   revenue-model diversity are measured, checkable, and unread.
   VW's 75.9% concentration is a quality fact today going nowhere.
3. **Make the question set archetype-dependent — the corpus insists.**
   Sixteen UNKNOWNs, seven of them total silences, are a generic
   question set meeting bank and insurer statements. This is not a
   scoring change; it is asking answerable questions.
4. **Do not merge the two rulers, and do not map grounded answers onto
   the 0/1/2 factors.** They answer different questions from different
   evidence with different failure modes, and the legacy ruler's
   HIGH/MEDIUM/LOW is not a scale the grounded verdicts belong on.
   What the corpus shows is that grounded quality is *more informative
   and less complete* — those are the two facts a v2 has to carry
   together.

Nothing in this slice changed the decision path, the legacy ruler, the
bands, completeness, or any fingerprinted rule. No new Business
Quality question was invented, and no output was tuned toward what a
famous company "should" score.
