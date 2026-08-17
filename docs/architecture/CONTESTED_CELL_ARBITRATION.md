# One printed cell, two vocabularies, and the statement decides

**Status: built and confirmed live, BQ25. The offline gate passed in full;
the paid confirmation succeeded on the first attempt for both filers. No
vocabulary edited, no schema bump, no production byte changed, no
production append. Stopped for ruling.**

> **The defect was an ordering one.** Distinctness ran *before* the
> structural predicates could say which concept a cell belongs to, so when
> one row was accepted by two vocabularies the concept that came earlier in
> `StatementConcept` claimed it and the other raised — **rejecting the
> whole observation**. Goldman and JPMorgan lost their net income and their
> net interest income to a collision about a third concept.
>
> **Enum order is not evidence.** The resolution stage is now lexical
> candidates → semantic qualification → uniqueness, and a lexical match is
> a *candidacy* rather than ownership.
>
> **Both filers read cleanly, first attempt.** GS resolved
> `Total net revenues` 58,283 to the new concept with its marker one row
> above; JPM resolved `Total net revenue` 182,447 the same way. Every other
> fact was retained, both fingerprints stamped natively, and the importer
> rules both compatible with no manifest.
>
> **BQ23 is untouched downstream.** Production's historical GS and JPM
> figures are still refused as `TOTAL_REVENUE`, and the corpus is still
> **HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14**.

---

## 1. The exact failure

One physical row, `Total net revenues` at Goldman's t0 r12 c3, accepted by
two vocabularies:

```text
matches_concept(TOTAL_REVENUE,                   "Total net revenues") → True
matches_concept(REVENUE_NET_OF_INTEREST_EXPENSE, "Total net revenues") → True
```

The old `_facts` resolved in this order:

1. parse `located` into a dict keyed by concept — rejects a duplicate
   *concept*, not a duplicate *cell*;
2. loop `concepts_of(statement)` **in enum order**;
3. per concept: `figure_at` → `matches_concept` → **`anchor.cell in cited`**
   → add to `cited`.

`TOTAL_REVENUE` precedes the new concept in the enumeration, so it reached
step 3 first, passed, and put r12 into `cited`. The new concept then found
its own cell already claimed and raised:

```text
The figure for 'revenue_net_of_interest_expense' cites a cell already read
as another concept, so one of the two is not what it was said to be.
```

`EvidenceNotApplicable` becomes `ExtractionRejected`, and `_validated`
discards the reading in full. **Two costs, and the second is the worse
one**: the winner was decided by enum position, and the loser took the
whole observation with it — net income and net interest income included.

BQ24 measured this live: GS and JPM produced **no observation at all**,
while **AXP succeeded**, because its label is in the new vocabulary and not
in `TOTAL_REVENUE`'s so no collision was possible. AXP remains the
non-overlap control here and no vocabulary was edited to make the
reproducer disappear — a test asserts the collision is still real.

---

## 2. The new candidate-resolution order

| | old | **new** |
|---|---|---|
| 1 | existence and agreement (`figure_at`) | existence and agreement |
| 2 | correspondence (`matches_concept`) | correspondence — **candidacy, not ownership** |
| 3 | **distinctness** | **semantic qualification**, where a concept declares one |
| 4 | row expansion | **distinctness**, over the arbitrated assignment |
| 5 | — | row expansion |

**The difference is that steps 3 and 4 changed places, and step 3 acquired
a meaning.** A lexical match now yields a *candidate set* per cell;
candidates are held until each concept's own structural requirement can be
asked of them; and uniqueness is enforced on the survivors rather than on
the claimants.

Everything else is unchanged. A label that answers no concept is still a
reading error and still rejects at step 2 — that is not a collision, and it
is the case every uncontested reading in the corpus takes. A cell with one
claimant skips arbitration entirely.

**The evidence a requirement reads is the *uncontested* anchors.** A figure
still under arbitration cannot be the thing that settles arbitration, so
`_arbitrate` builds `established` from candidates whose cell no one else
claims. The marker is always among them: `NET_INTEREST_INCOME` accepts one
label and shares it with nothing.

---

## 3. The formal rule

```text
survivors_for(contested, figure, established) =
    ( concept for concept in contested
      if refusal_for(concept, figure, established) is None )
```

and at the extractor:

```text
|survivors| = 1  →  that concept owns the cell; the others are declined,
                    each with the reason worded
|survivors| = 0  →  the cell answers none of them
|survivors| > 1  →  ambiguity: refuse the observation
```

**It decides by evidence or it does not decide.** Nothing in it reads a
name, a vocabulary size, a recency, a specificity or a position in an enum,
and a test asserts that reversing the input cannot move the answer. Every
shape §3 forbids is excluded by construction rather than by convention:

- *first matching predicate wins* — no; every candidate is asked.
- *newest concept wins* — no; the rule has no notion of age.
- *enum order wins* — no; `survivors_for` is order-symmetric.
- *more specific name wins* — no; names are never read.
- *financial-company concept wins* — no; no company or sector is knowable
  here.

**A concept that declares no requirement cannot be refuted**, so it always
survives — which means arbitration resolves only where *every* candidate
carries a discriminator. Pair one that does with one that does not and you
get two survivors and a refusal, which is correct: the platform holds
nothing that could tell them apart.

One consequence looks like a weakness and is not, so it has its own test:
the rule is *survives refutation*, not *has the better predicate*. A
concept nothing can refute wins a contest whose only other candidate the
statement refuted — because that is what the evidence says.

**A declined candidate is not an absence.** `_lost_to` words it apart: the
reading located the cell, this platform read it, and the structure says the
row answers something else. *The reading located no cell* would be false.

---

## 4–5. The controls

All pinned in `tests/test_contested_cell_arbitration.py`, over real
documents through the real extractor.

| control | expected | result |
|---|---|---|
| **GS** — shared label, marker above | new concept survives, `TOTAL_REVENUE` does not, observation otherwise valid | **exactly that**, and net income + net interest income retained |
| **JPM** — same shape | same | **same** |
| **AXP** — only the new vocabulary matches | unchanged successful extraction, qualification still passes | **unchanged**; `TOTAL_REVENUE` is an ordinary *"located no cell"* absence |
| **industrial** — same shared label, **no marker** | `TOTAL_REVENUE` survives, new concept does not | **exactly that** |
| **marker below** — same two rows, order reversed | no false assignment to the new concept | **`TOTAL_REVENUE` keeps the cell** |
| **unresolved collision** — a candidate with no discriminator | refusal, never enum-order selection | **refuses**, naming both and saying it holds no evidence that tells them apart |
| **one survivor from a refuted pair** | the survivor owns it | pinned, because it looks wrong and is right |

The unresolved-collision control had to be **constructed**: no two live
concepts both accept one label *and* lack a discriminator — the only real
overlap is the pair this slice exists for, and that pair always resolves.
So `GROSS_PROFIT` is given the shared form for the length of one test,
monkeypatched rather than mocked, and the extractor runs its real three
stages over a real document.

---

## 6. One cell, one final concept

**Unweakened.** Arbitration decides *who* owns a cell before uniqueness is
enforced; it never licenses two owners. Asserted on the fixtures and on
both live readings:

```text
GS  : 3 anchors, 3 distinct cells → HOLDS
JPM : 3 anchors, 3 distinct cells → HOLDS
```

The two concepts are not declared equivalent anywhere, and BQ24's test that
they are not aliases still stands.

---

## 7. Contracts and provenance

| | before | after |
|---|---|---|
| `TOTAL_REVENUE` fingerprint | `ea9df9c5adbc7f44` | **`ea9df9c5adbc7f44`** |
| its accepted forms | 14 | **14** |
| `REVENUE_NET_OF_INTEREST_EXPENSE` fingerprint | `3e077c247f109a37` | **`3e077c247f109a37`** |
| its accepted forms | 5 | **5** |
| store schema | 3 | **3** |
| `vocabulary_contracts.PUBLISHED` | unchanged | **unchanged** — no lineage update needed, and `registry_is_current(TOTAL_REVENUE)` is still `True` |
| `GOVERNED` requirements | `ABSENT_ABOVE` / `PRESENT_ABOVE` | **unchanged** |

**Nothing about producing-contract identity moved**, which is the point: an
arbitration stage is a resolution rule downstream of the vocabulary, not a
change to what any concept accepts. Confirmed explicitly, and pinned by a
test, so a future slice cannot fix an arbitration problem by quietly
editing a contract.

Both live readings carry native stamps for both concepts:

```text
produced_under[revenue_net_of_interest_expense] = 3e077c247f109a37
produced_under[total_revenue]                   = ea9df9c5adbc7f44
```

---

## 8. BQ23 downstream, and the aggregate

**Unchanged, and checked against production after the run:**

```text
GS  : production total_revenue located=False  refused=constructed from net interest income
JPM : production total_revenue located=False  refused=constructed from net interest income
```

| | HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|
| **production** | **3** | **4** | **3** | **14** |

The arbitration is not a backdoor to generic net margin. A correctly
assigned fact is still not a comparable quality factor, and nothing
consumes the new concept.

---

## 9. The offline gate — passed

| requirement | result |
|---|---|
| GS fixture resolves deterministically to the new concept | **yes** |
| JPM fixture resolves deterministically | **yes** |
| AXP remains valid | **yes** |
| industrial net-revenue control remains `TOTAL_REVENUE` | **yes** |
| unresolved collisions still refuse | **yes** |
| fingerprints unchanged | **yes**, both |
| production bytes unchanged | **md5 `5b5b1d1d…` before and after** |
| tests, ruff, mypy | **2,861 pass**, clean, clean |

---

## 10. The paid confirmation — 2 of 2, first attempt

Two calls, `gpt-5`, one reading each, income statement only, isolated three
ways before the first call. **No AXP re-read.**

### Goldman Sachs

```text
revenue_net_of_interest_expense  'Total net revenues' = 58,283   t0 r12 c3
net_interest_income              'Net interest income' = 13,559  t0 r11 c3
net_income                       'Net earnings' = 17,176         t0 r26 c3
total_revenue                    absent — "…this statement's own structure
                                 reads that row as revenue_net_of_interest_expense instead…"
```

### JPMorgan

```text
revenue_net_of_interest_expense  'Total net revenue' = 182,447   t0 r15 c3
net_interest_income              'Net interest income' = 95,443  t0 r14 c3
net_income                       'Net income' = $ 57,048         t0 r27 c3
total_revenue                    absent — same wording
```

| check | GS | JPM |
|---|---|---|
| whole observation accepted | **yes** | **yes** |
| shared row assigned only to the new concept | **yes** | **yes** |
| `TOTAL_REVENUE` not established from that row | **yes**, declined with the arbitration reason | **yes** |
| net income retained | **17,176** | **$ 57,048** |
| net interest income retained | **13,559** | **95,443** |
| structural relationship | r11 precedes r12, one table, one column — **holds** | r14 precedes r15 — **holds** |
| native provenance stamped | **both concepts** | **both concepts** |
| importer without manifest | **`compatible=1`** | **`compatible=1`** |

**Neither needed a retry**, and no retry was attempted.

---

## 11. API and model usage

| | |
|---|---|
| calls | **2** — GS and JPM, one each, `gpt-5`, income statement only |
| produced an observation | **2 of 2** |
| AXP | **not re-read**, as instructed |
| other companies | **none** |
| preserved at | `data/experiments/statement-observations/bq25/statements/`, md5 `c122e424ee18443e711552ef27df2135` |
| production write | **none** — `data/statements` md5 `5b5b1d1d57787769c4ddee8af7a21ad5` before and after |

## 12. Gates

**2,861 pass** (2,845 before, +16) · ruff check clean · ruff format clean ·
mypy clean, 594 files · `git status --porcelain data/statements` empty.

---

## 13. Recommendation

**A five-reading consensus is now justified, for these three filers, and
it is the natural next slice.**

The evidence for it is that arbitration is deterministic where it matters:
the two overlapping-label filers both resolved correctly on a single
unassisted reading, the assignment is decided by the filers' own
typesetting rather than by anything stochastic, and AXP already read
cleanly under BQ24 without arbitration being involved at all. Three filers,
three labels, one quantity, one outcome.

What a quorum would buy is what a quorum always buys — *reader stability*,
not corroboration: five readings of one document measure whether this
platform reads it the same way five times. The specific risk it would
measure here is a reading that omits the concept altogether or cites the
wrong row, neither of which a single reading can rule out.

**Scope, if it is funded:** 5 readings each for GS, JPM and AXP — 15 in
total, income statement only, isolated as before — followed by a separate
ruling on the production append. **Nothing else should be added to that
scope**, and in particular BCS and NWG should stay out: BQ24 recorded that
their totals would qualify on the marker relationship alone with **no
reconcilable non-interest component**, which is weaker evidence than these
three and deserves its own ruling first.

## Recorded, not solved

- **A rejected reading still loses every concept it found.** BQ24 flagged
  it and this slice removes the *cause* for the one collision that exists,
  not the failure mode: a two-survivor ambiguity, or any other
  `ExtractionRejected`, still discards the whole observation. Whether a
  partial observation should be storable remains open.
- **Arbitration is only as good as the discriminators.** Today exactly one
  pair of concepts carries mutually exclusive requirements. A third concept
  sharing a label with either, and declaring nothing, would make that cell
  permanently ambiguous — correctly, and silently as far as the vocabulary
  is concerned.
- **`_arbitrate` treats a contested cell's candidates as sharing one
  figure.** They do, because they cite the same cell and `figure_at` reads
  it from the document — but the code takes the first candidate's anchor
  rather than asserting the anchors are equal. Harmless and worth
  tightening if a third contested concept ever appears.

## Scope compliance

No shared vocabulary form deleted · `TOTAL_REVENUE` semantics unchanged ·
BQ23 unchanged · `FinancialModel.BANK` not activated · no bank
profitability logic · COF/FITB not repaired · no quality threshold changed ·
HON and KO untouched · **no backfill of the new concept** · no production
append · 2 model calls, the authorised scope.
