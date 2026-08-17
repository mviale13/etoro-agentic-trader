# Fifteen readings, fifteen successes — and a reason not to append them yet

**Status: acquired, BQ26. 15 of 15 readings succeeded, all three filers
quorate at 5 of 5 with zero divergence. No production append, no vocabulary
change, no threshold tuned. `data/statements` byte-identical. Stopped for
ruling.**

> **Reader stability is not in question.** Goldman, JPMorgan and American
> Express each produced five independent readings that agree to the cell:
> the same label, the same figure, the same address, the same marker
> relationship, the same native fingerprint. No reading was aborted, none
> was retried, and no stop condition fired.
>
> **The concept is acquired.** Appending would establish
> `REVENUE_NET_OF_INTEREST_EXPENSE` at majority for all three, and the
> quality bands would not move — **HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14**
> before and after, simulated on a copy.
>
> **And that is not the whole answer.** Appending would turn Goldman's and
> JPMorgan's `total_revenue` from a **reasoned refusal** into an
> **unsettled 5-against-5 tie**. Both read *not established* and the band
> is UNKNOWN either way, so nothing scores differently — but the sentence a
> reader gets is strictly worse, and the tie is not reader disagreement. It
> is two contracts answering two different questions.
>
> **Recommendation: do not append yet.** One slice first, and it is not a
> consensus rule.

---

## 1. #174 merged, contracts unchanged

Checked before the first call rather than after the last, and the harness
refuses to run if either differs:

| | live | expected | |
|---|---|---|---|
| `REVENUE_NET_OF_INTEREST_EXPENSE` | `3e077c247f109a37` | `3e077c247f109a37` | **OK** |
| `TOTAL_REVENUE` | `ea9df9c5adbc7f44` | `ea9df9c5adbc7f44` | **OK** |
| accepted forms | 5 / 14 | 5 / 14 | **OK** |
| store schema | 3 | 3 | **OK** |
| `registry_is_current(TOTAL_REVENUE)` | `True` | — | **OK** |

Gates on merged `main` before acquisition: 2,861 pass, ruff clean, mypy
clean. Production baseline md5 `5b5b1d1d57787769c4ddee8af7a21ad5`.

---

## 2–3. Calls attempted, and every reading

Through the ordinary BQ17-native path: `observe` was called with a target
of *n+1* so it took exactly one new reading, and each reading was validated
before the next was bought. Income statement only. Isolated three ways —
evidence root set before any app import, store passed explicitly, resolved
path asserted not to be production.

| | attempted | succeeded | aborted |
|---|---|---|---|
| **GS** | 5 | **5** | — |
| **JPM** | 5 | **5** | — |
| **AXP** | 5 | **5** | — |
| **total** | **15** | **15** | **0** |

Every reading, in order:

```text
GS   1–5  'Total net revenues' = 58,283  t0 r12 c3 · marker 13,559 r11 · net income 17,176
JPM  1–5  'Total net revenue' = 182,447  t0 r15 c3 · marker 95,443 r14 · net income $ 57,048
AXP  1–5  'Total revenues net of interest expense' = 72,229  t0 r17 c3 · marker 17,364 r16 · net income $ 10,833
```

**Byte-identical across each filer's five.** Same label, same printed
figure, same table, row and column, same marker row, same net income.

Each reading was checked against every stop condition §2 names — wrong
concept, both concepts from one cell, a lost anchor, an incompatible
fingerprint, whole-observation rejection, a materially different row — and
none fired. The expected specimens are validation expectations in the
harness only; nothing in extraction reads them.

---

## 4. Consensus, per company

Quorum unchanged at 5, and no special rule was invented for this concept.

| | readings | target concept | `total_revenue` | marker |
|---|---|---|---|---|
| **GS** | 5, **quorate** | **5× `Total net revenues` 58,283**, majority | 5× *no figure located*, majority | 5× 13,559, majority |
| **JPM** | 5, **quorate** | **5× `Total net revenue` 182,447**, majority | 5× *no figure located*, majority | 5× 95,443, majority |
| **AXP** | 5, **quorate** | **5× `Total revenues net of interest expense` 72,229**, majority | 5× *no figure located*, majority | 5× 17,364, majority |

**Majority consensus is established for the target concept in all three**,
on a single answer each — the strongest shape this platform's consensus can
report. And the familiar caveat holds: five readings of one document measure
**reader stability, not corroboration**.

## 5. Concept ownership

**15 of 15 assigned the target row to `REVENUE_NET_OF_INTEREST_EXPENSE`
and none to `TOTAL_REVENUE`.**

For GS and JPM this is BQ25's arbitration exercised ten times: the label is
in both vocabularies, and each time the marker one row above awarded the
cell to the new concept and declined the old one. For AXP it confirms the
non-overlap path, which needs no arbitration at all. One cell, one concept,
in every reading.

## 6. Native provenance

Every one of the fifteen carries both contracts, stamped at acquisition:

```text
produced_under[revenue_net_of_interest_expense] = 3e077c247f109a37
produced_under[total_revenue]                   = ea9df9c5adbc7f44
```

No manifest was authored and none was needed. No historical backfill: the
old readings carry no stamp for either concept and gained none.

## 7. Failed or aborted readings

**None.** No batch was stopped, no reading was refused, no extraction was
rejected, and no retry was attempted or required.

---

## 8. The simulated import

Applied through `StatementPromotion` on a **copy** of production; the real
store was opened read-only and its md5 compared before and after.

| | |
|---|---|
| would append | **15** (5 per filer) |
| duplicates | **0** |
| refusals / incompatible | **0** |
| unproven | **0** — all fifteen ruled `compatible` on their own native stamps |

### Which concepts would gain consensus

| | before | after |
|---|---|---|
| GS target | *not asked by any reading* | **located 58,283**, addressed 5/10, **majority** |
| JPM target | *not asked* | **located 182,447**, addressed 5/10, **majority** |
| AXP target | *not asked* | **located 72,229**, addressed 5/10, **majority** |
| GS / JPM marker | located, 5/5 | located, **10/10** |
| AXP `total_revenue` | absent, 5/5 majority | absent, **10/10 majority** |

`addressed_in=5/10` is the designed behaviour, not a defect: the consensus
counts over the observations that *addressed* a concept, because a claim no
reading was asked must never be presented.

### Whether existing `TOTAL_REVENUE` authority changes — **yes, and this is the finding**

| | before | after |
|---|---|---|
| **GS** | **REFUSED** — *constructed from net interest income*; addressed 5/5, **majority True** | **absent** — addressed 10/10, **majority False** |
| **JPM** | **REFUSED** — same standing; majority True | **absent**; **majority False** |
| **AXP** | absent, majority True | absent, majority True — **unchanged** |

No authority is *restored*: `total_revenue` is unestablished before and
after, and no band moves. What changes is the account. Measured, not
inferred:

```text
GS, before
  total_revenue: REFUSED — constructed from net interest income
  net margin says: … The statement prints "Net interest income" 13,559 at
  table 0, row 11, column 3, above "Total net revenues" 58,283 at table 0,
  row 12, column 3 and in the same column ("2025"). So the figure is a
  total after financing cost, not the gross total revenue this concept names…

GS, after
  total_revenue: absent
  net margin says: … Where the statement prints this figure is unsettled
  across 10 readings: 5× "Total net revenues" = 58,283 at table 0, row 12,
  column 3; 5× no figure located.
```

**A structural explanation is replaced by what reads as reader
disagreement — and it is not disagreement.** The old five were never asked
about the new concept; the new five correctly declined `total_revenue`
because arbitration awarded the row elsewhere. Pooling them makes two
different questions look like one question answered inconsistently.

This is BQ19's lesson in a new costume. There, *a stale absence votes*.
Here, **a stale positive votes** — against a fresh, better-reasoned absence.

**And BQ20 cannot fix it, correctly.** The new absences were produced under
`ea9df9c5adbc7f44`, which *does* accept `total net revenues`, so the
vocabulary explains nothing and absence supersession declines to withdraw
them. The new absences are not a vocabulary failure; they are an
*arbitration* outcome, and BQ20 has no vocabulary for that.

**Nor does the existing audit.** Measured on the live corpus: all ten old
GS and JPM readings rule **`active`**, `supersedes=False`. `statement_audit`
checks a stored anchor against the document — table, row, label, header, row
contents — and GS's anchor is still exactly what the filing prints. It has
no notion of *which concept* today's extractor would award that cell to.

## 9. Simulated quality impact

| | HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|
| before | 3 | 4 | 3 | 14 |
| **after 15 appended** | **3** | **4** | **3** | **14** |

**No change**, as expected. GS and JPM stay UNKNOWN, and would stay UNKNOWN
either way: the new concept has no Business Quality consumer, it is not a
profitability denominator, and one answered factor never bands. A perfect
5-of-5 consensus restores no band, which is the whole point of §7.

## 10. API and model usage

| | |
|---|---|
| calls | **15** — GS 5, JPM 5, AXP 5 · `gpt-5` · income statement only |
| successful observations | **15 of 15** |
| retries | **0** |
| other companies | **none.** BCS and NWG not acquired; no balance sheet, cash flow or narrative evidence |
| preserved at | `data/experiments/statement-observations/bq26/statements/`, md5 `8bd5604939fb8731d3bd2f9b386d2001` |
| production write | **none** — `data/statements` md5 `5b5b1d1d57787769c4ddee8af7a21ad5` before and after |

## 11. Gates

**2,861 pass** · ruff check clean · ruff format clean · mypy clean, 594
files · `git status --porcelain data/statements` empty.

No test changed. This slice adds evidence and a report; it changes no code.

---

## 12. Recommendation — **do not append yet**

Not because the acquisition failed. It is the cleanest acquisition in this
arc: 15 of 15, three filers, three labels, one quantity, zero divergence,
no retries. **The concept is proven stable and the specimens are durable
and compatible.**

The reason to hold is that appending buys one thing and spends another:

- **buys** the new concept at majority for three filers, changing no band;
- **spends** Goldman's and JPMorgan's `total_revenue` refusal, replacing a
  sentence that explains the document with one that reports a tie the
  document does not contain.

The second is a *presentation* regression on the very surface BQ23 was
built to make truthful, and it would be introduced knowingly. Invariant 1's
sibling applies: an unsettled tie is a weaker and less honest account than
a reasoned refusal, and this platform does not trade the second for the
first to gain a field.

### The one slice that should come first

**Concept-assignment supersession** — a stored positive loses its vote for
one concept where today's extractor would award its cell to a *different*
concept.

It is precedented in shape and new in axis. BQ15's rule already says *only
what today's parse can positively read may refute a reading*, and today's
parse positively reads GS's row 12 as `revenue_net_of_interest_expense`;
what the audit lacks is the *assignment* axis, having only the anchor axis.
It is derived on read like BQ20 and BQ23, writes nothing, needs no
re-reading, and would leave GS and JPM with a clean 5-of-5 target consensus
beside an `total_revenue` that is refused rather than tied.

**With that in place, appending these fifteen is unambiguously additive**,
and the append should be ruled then — on the same specimens, which need no
re-acquisition.

### If the ruling is to append now anyway

It is defensible, and the cost is exactly one thing: two companies' surfaces
lose a good sentence and gain a tie. No band moves, no figure is invented,
nothing is written that cannot be superseded later. **A narrower option
exists and is genuinely clean: append AXP's five alone** — its
`total_revenue` is an absence before and after, its wording strictly
improves (5 of 5 → 10 of 10), and it gains the concept with no loss at all.
Holding all three keeps the decision single, which is why it is the
recommendation rather than a split.

## Out of scope, and untouched

BCS and NWG **not acquired** — BQ24 recorded that their totals qualify on
the marker relationship alone with no reconcilable non-interest component,
and that needs its own semantic ruling · `FinancialModel.BANK` not
activated · no profitability use of the new concept · no synthesised gross
revenue · COF/FITB not re-read · DB/MUFG not repaired · HON and KO untouched
· no vocabulary change · BQ23 and BQ25 unchanged · **no consensus threshold
tuned and no special rule invented for this concept**.
