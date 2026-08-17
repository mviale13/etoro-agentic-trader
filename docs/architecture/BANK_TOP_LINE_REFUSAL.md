# An established top line with no comparable ruler, and a withdrawal that cannot fall through

**Status: BQ20, built. Accepted owner ruling on BQ19's finding. No model
call, no acquisition, no production data mutation, and no band, factor,
threshold, recipe, vocabulary, schema or decision moved.**

Two halves of one seam. `_quality_value` promised that a grounded
assessment governs outright *including when it bands `UNKNOWN`* — and
BQ19 measured two live cases the promise did not reach.

> **The platform now says what it read and what it cannot judge.** For
> AXP, GS and JPM the consolidated top line is established, and the
> quality basis states — in the domain's own words, carried to the
> dossier verbatim — that the figure was read, that it is struck after
> financing cost, that every threshold here compares a margin against
> gross revenue, that no comparable ruler for such a denominator has
> been established, and that therefore no verdict and no band is
> claimed.
>
> **And a withdrawal is no longer an absence.** Where an audit withdrew
> every statement reading a company has, the provider's three proxies
> are refused. Reproduced with the strongest provider recommendation
> there is: before this slice C and MTB scored **quality 80** from it;
> they now score nothing, and the basis says the readings were audited
> away and that re-observation is what restores authority.
>
> **Neutrality is measured, not argued.** Every decision-bearing field
> of all 24 companies — five scores, conviction, rank, recommendation,
> action, `security_evidenced` and the quality derivation — is
> **byte-identical** to `main`, captured through the live API on both
> sides.

---

## 1. The owner ruling, as given

1. `REVENUE_NET_OF_INTEREST_EXPENSE` is a legitimate established
   quantity.
2. It is **not** economically comparable to gross `TOTAL_REVENUE` under
   the existing corporate profitability thresholds.
3. Do not add it to `RECIPES` or feed it into the existing profitability
   or revenue-growth ruler.
4. Do not invent bank thresholds or a bank quality score. The current
   corpus does not earn one.
5. Where the quantity is established, say explicitly that the platform
   read the top line and has no comparable profitability ruler for a
   denominator struck after financing cost.
6. A statement whose authoritative readings were all withdrawn must not
   fall through to provider quality. *Never read* and *read, then
   withdrawn by audit* are different states.

Every one of the six is satisfied structurally rather than by
convention, and §6 names the guard for each.

## 2. Why "no, and say so" is a product improvement

Before this slice an investor opening Goldman Sachs read:

> *1 of 3 factors answered — fewer than 2, so no band is claimed. That
> is a limit of the established evidence, not a finding about the
> company.*

Which is true, and reads exactly like a company whose filing this
platform failed to open. It is the same sentence MUFG gets, whose
located statement stops before its bottom line, and the same sentence
Barclays gets, whose top line this platform cannot read at all. **Three
completely different epistemic states, one wording** — and the one an
investor most needs to distinguish is the one where waiting will not
help, because there is nothing left to acquire.

After:

> *… It is not a complete measure of business quality. This platform
> read the company's consolidated top line — "Total net revenues" =
> 58,283 under "2025" (Consolidated Statements of Earnings, table 0,
> row 12, column 3) — and it is struck after financing cost: the
> statement prints a net interest income subtotal above it, so interest
> expense is already deducted from the total. Every profitability
> threshold this platform applies compares a margin against gross
> revenue, and no comparable ruler for a top line struck after financing
> cost has been established. So no margin is computed from it, no
> profitability verdict is reached and no quality band is claimed. That
> is a limit of this platform's rulers, not a finding about the company.*

That is a **different kind of absence**, and the difference is
actionable: it tells the reader the evidence is in hand and the
judgment is not, which is a statement about MOVRvest's rulers that no
amount of further reading would change. It is also the only honest
alternative to the two things the ruling forbids — scoring the figure
against a corporate threshold, which BQ21 measured makes six of seven
banks *excellent* while zero of four insurers are, and inventing a bank
threshold seven companies cannot ground.

The alternative was not "nothing". It was silence that looked like
ignorance.

## 3. Deliverable A — the semantic refusal

### The discriminator is structural, and both halves are load-bearing

`_incomparable_top_line` (`app/services/financial_engine.py`) fires on
exactly one shape:

```text
TOTAL_REVENUE is NOT established   AND   REVENUE_NET_OF_INTEREST_EXPENSE IS
```

- **The first half keeps the corporate ruler untouched.** Where a filer
  prints a gross total, that total governs and there is nothing to
  refuse. AAPL, UNP, DIS, TRV, HON and PG carry no refusal and their
  basis gains no sentence.
- **The second half is why this is a statement about evidence.** The
  concept carries its own structural requirement — the filer printed a
  net interest income subtotal above the row (BQ23's `GOVERNED`, read
  with the opposite polarity) — so a label alone reaches nothing.

**No label is matched, no sentence is read, and no figure is combined
with another.** An AST guard asserts the derivation's body contains no
arithmetic operator at all.

### Who it fires for, and why not the others

| | `TOTAL_REVENUE` | net-of-interest total | refusal worded |
|---|---|---|---|
| **AXP** | absent — its label was never a `TOTAL_REVENUE` form | **established** `Total revenues net of interest expense` 72,229 | **yes** |
| **GS** | **refused** by BQ23, `NET_OF_FINANCING_COST` | **established** `Total net revenues` 58,283 | **yes** |
| **JPM** | **refused** by BQ23 | **established** `Total net revenue` 182,447 | **yes** |
| BCS, NWG | absent | **printed and not established** — the concept post-dates their readings | no |
| COF, FITB, RF, MTB, MUFG, DB, KO | absent | not printed | no |
| the banded eight | **established** | — | no |

AXP and GS reach the same wording by different routes — one a plain
absence, one a structural refusal — which is the point: the reader is
owed the same statement in both, because the same thing is true of both.

### It takes part in no arithmetic

`assess()` computes the band from `answers` alone. Proved by handing it
the same answers twice, with and without a refusal, and comparing the
band, the score, `favourable`, `answered`, every factor and
`stated()` — identical for AAPL, GS and KO. A caller **cannot** move a
verdict by supplying one.

`IncomparableTopLine` has five fields — `label`, `printed`, `basis`,
`source`, `support` — and no `int` or `float` anywhere in them. There is
nowhere for a score, a band or a threshold to live, and a test asserts
the field set.

### Evidence travels with the figure

The checked cell first and the rest of its row behind it, each cell
once, every one carrying the filer's row label, column header, printed
text and cell address; the filing as an investor would cite it; and the
narrowest agreement beneath it (5 of 5 for all three). A refusal rests
on evidence as firmly as an established measure does.

### Where it is authored, and where it is only rendered

| layer | what it does |
|---|---|
| `financial_engine.measure` | derives the carrier from the income consensus |
| `FinancialUnderstanding.incomparable_top_line` | holds it; **no measure reads it** |
| `business_quality_service.quality_of` | passes it to `assess`, unconsulted |
| `BusinessQuality.incomparable_top_line` | carries it past no arithmetic |
| `_grounded_quality_basis` | **renders `refused.stated()`** into the basis and as the first evidence line |
| `_score` → dossier | copies `basis.basis` and `basis.evidence` verbatim |

**Communication renders the domain's sentence and composes none.** A
test asserts the exact string appears in both the basis and the evidence
tuple, and the live `/executive/GS/dossier` was fetched and read.

### The refusal is first in the evidence list

Because it is the *reason* the factors below are unavailable, not one
more absence beside them — the presentation-ownership lesson from #126
applied at the point where it would otherwise recur.

## 4. Deliverable B — total withdrawal cannot fall through

### The defect, reproduced

BQ19 measured it and this slice reproduces it before closing it: a
synthetic `CompanyRecommendation` whose quality signal reads `HIGH` —
the provider proxy at its strongest, worth **80** — handed in beside C
and MTB, whose every income-statement reading BQ15's audit withdrew.

| | before | after |
|---|---|---|
| `_quality_value(provider=80, grounded=None)` | **80** | **None** |
| rules stamped | `provider-quality` | **none** |
| basis | *"No security-level analysis was gathered"* | the withdrawal, named |

`_quality_value`'s docstring promised a grounded `UNKNOWN` governs
outright. Total withdrawal produces no grounded object at all, so the
promise — written about a *band* — never reached the case, and the
provider route re-opened underneath it. Not *too little was established
to say*, but *what was established has been taken away*.

### The distinction is a member, never a sentence

`CompanyUnderstandingService._financial` already drew the three-way
distinction **in prose**, correctly, in branches nothing downstream
could read. `FinancialEvidenceStanding` is the structured form of those
same branches, returned from the branch that words the reason so the two
can never disagree:

| member | condition |
|---|---|
| `ESTABLISHED` | `measure()` produced an understanding |
| `WITHDRAWN_BY_AUDIT` | readings held, **none authoritative** |
| `NEVER_READ` | nothing stored |
| `UNMEASURABLE` | authoritative readings held, `measure()` refused them (two filings) |

**The gate reads the member.** A test hands `NEVER_READ` in *carrying the
withdrawal prose* and asserts the provider still scores 80 and the
sentence does not appear; the mirror hands `WITHDRAWN_BY_AUDIT` in with
**no sentence at all** and asserts the block still fires. Prose
matching would fail one of the two.

### Two sentences, two owners

The basis quotes the composing service's account of *what happened to
the evidence* and adds this layer's account of *what it did about it*:

> *C's income statement has been read, and an offline audit of the
> filing withdrew all 5 of those readings: the figures were taken from
> cells the filer heads differently. The readings are still stored and
> none of them is counted. Reading the statement again is what restores
> authority, and is an explicit spend — `movrvest observe-statements`
> takes it. **No business quality is scored from them: a withdrawn
> reading is stored history rather than a current assessment, and the
> provider's proxies are not consulted in its place.***

Re-authoring the first half here would put one claim in two voices, so
the re-observation clause belongs to whichever voice already carries
it — asserted by a test that counts *"explicit spend"* exactly once.

### Withdrawn readings are not an assessment and not current evidence

`security_evidenced` counts a provider row or a grounded assessment. A
withdrawn reading is neither, and the live dossier confirms it: C and
MTB render `security_evidenced: false`, `conviction: null`, quality
`null`.

### `UNMEASURABLE` is deliberately not gated

Nothing was audited away there, and no company in the corpus is
currently in that state — so the provider route is left exactly as it
was rather than changed on an unreachable shape. Recorded, not fixed.

## 5. Controls — all pinned

Captured through the live API on `main` and on this branch, and
`diff`ed:

| control | required | observed |
|---|---|---|
| GS | UNKNOWN, 1/3 | **UNKNOWN, score None, 1/3** |
| JPM | UNKNOWN, 1/3 | **UNKNOWN, score None, 1/3** |
| AXP | UNKNOWN, 1/3 | **UNKNOWN, score None, 1/3** |
| HON | MEDIUM 62, 3/3 | **MEDIUM 62, 3/3** |
| AAPL | MEDIUM 62 | **MEDIUM 62, 3/3** |
| UNP | MEDIUM 62 | **MEDIUM 62, 3/3** |
| DIS | HIGH 80 | **HIGH 80, 3/3** |
| KO | UNKNOWN, 0/3 | **UNKNOWN, score None, 0/3** |
| TRV, ALL | remain HIGH | **HIGH, HIGH** |
| aggregate | 3 · 5 · 3 · 13 | **HIGH 3 · MEDIUM 5 · LOW 3 · UNKNOWN 13** |
| `REVENUE_NET_OF_INTEREST_EXPENSE` in any recipe | absent | **absent from all 9** |
| live decision / conviction / band / factor count / threshold | none moves | **0 movements across 24 companies** |
| `data/statements` | byte-identical | **`a148e451aa5ee82a3732dcfa4569f284`** — what BQ18 left |

### Negative controls

| control | result |
|---|---|
| never-read + provider quality | **score 80, `provider-quality` stamped** — unchanged |
| fully withdrawn + provider quality | **blocked, score None, no rule** |
| grounded UNKNOWN + provider quality | **grounded governs, score None** |
| established gross `TOTAL_REVENUE` | **corporate ruler unchanged**, no refusal, no extra sentence |
| unestablished / never-asked net-of-interest claim (BCS, NWG) | **no wording produced** |
| the default parameter (no standing passed) | **behaves exactly as before it existed** |
| RF — income withdrawn, balance sheet survives | **grounded UNKNOWN 0/3, still governs** |

### The decision-neutrality measurement

For each of the 24: `quality`, `evidence`, `valuation`, `safety`,
`portfolio_fit`, `conviction`, `rank`, `recommendation`, `action`,
`security_evidenced` and the serialised quality `derivation`, fetched
from `/executive/{symbol}/dossier` on both revisions.

```text
diff baseline.jsonl branch.jsonl  →  no output
```

The reason nothing moved where the fallback was blocked: **neither C nor
MTB holds a provider row.** Of the 24, only AAPL, DIS, PG and TSLA do.
The defect was latent, exactly as BQ19 measured — and the block is what
stops the next `movrvest acquire` from arming it.

## 6. Where each clause of the ruling is enforced

| ruling | guard |
|---|---|
| 1 — legitimate established quantity | the consensus is untouched; `refused.support` carries 5 of 5 |
| 2, 3 — not comparable, not in `RECIPES` | `test_the_quantity_still_reaches_no_measure_and_no_threshold`, plus BQ24's existing grep of the six scoring modules — which still passes, because the concept is named in none of them |
| 4 — no bank threshold or score | `IncomparableTopLine` has no numeric field; the derivation contains no arithmetic operator |
| 5 — say it explicitly | `test_the_refusal_states_all_five_things_the_ruling_requires`, clause by clause |
| 6 — withdrawal ≠ never read | `FinancialEvidenceStanding`, and the two-way prose test |

## 7. Scope compliance

No model or API call · no acquisition · no re-observation of C, MTB, RF,
BCS, DB, KO or NWG · no `NET_INCOME` vocabulary widening · no KO
tie-breaking and no absence weakened · no MUFG locator work · no parser,
extraction, consensus, vocabulary, schema, fingerprint, recipe, factor,
threshold, band, playbook, financial-model, decision-weight or portfolio
change · no missing bank total constructed · no production data mutation
(`git status --porcelain data/` empty).

Gates: **3,078 tests pass** (3,062 + 16 new), `ruff check` clean,
`ruff format --check` clean, `mypy app` clean over 598 files — and the
commit verified in isolation from `git archive HEAD`, not only the
working tree.

## 8. Recorded, not solved

- **`UNMEASURABLE` is not gated.** A company observed across two filings
  holds authoritative readings and yields no understanding, so the
  provider route stands there. No company in the corpus is in that
  state; gating it would be a change on an unreachable shape.
- **The refusal is worded per company and the ruler is missing for a
  class.** Six companies print the quantity and three currently
  establish it; the other three will produce the same sentence the
  moment they are read. Nothing yet says *this class of business has no
  ruler here*, and saying it would need the bank threshold work the
  ruling declines.
- **`security_evidenced` still counts a provider row.** Correct today —
  a provider row is evidence — but it means a withdrawn-statement
  company with a provider row reads as evidenced on the strength of the
  provider alone. The quality score is blocked; the flag is not.
- **BQ19's remaining eleven UNKNOWNs are untouched.** Four print no top
  line, three have an unreadable bottom line, one is truncated, one is a
  contested cell, and three need re-observation that BQ19 measured buys
  no band.
