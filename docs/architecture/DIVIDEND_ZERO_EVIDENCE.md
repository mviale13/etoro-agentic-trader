# A stated zero is evidence; an omission is not

**Status: built. Q1, the audit's §5 answer. No factor scoring,
completeness, band, threshold, denomination/FX, dual-class or
business-quality change. Stopped for review.**

`QUALITY_BOTTLENECK_AUDIT.md` measured the largest single blocker on
Quality coverage and found it was not an evidence gap in the world but
a field-choice in this adapter:

> Yahoo represents non-payment by **omitting** `dividendYield` — the
> field this platform read — while stating the zero explicitly in
> `trailingAnnualDividendRate` and `trailingAnnualDividendYield`,
> which it discarded.

So every non-payer arrived as *unread*, `quality-authority@1`
correctly refused to band a business on an unanswered question, and 19
companies were blocked by nothing else. This slice preserves the
provider's statement instead of converting it into absence.

---

## 1. Which field is authoritative, established from the payloads

Measured over the live corpus (2026-08-16, 66 payloads):

| Observation | Count |
|---|---|
| `dividendYield` served with a positive value (payers) | 34 |
| `dividendYield` served as `0` for a **company** | **0** — it never happens |
| `dividendYield` omitted while a trailing field states `0.0` | **29** |
| the two trailing fields disagreeing about the zero | **0** |

One appearance of `dividendYield: 0` exists corpus-wide and it is
**IB01.L, a fund** — the F1 specimen, whose company questions are not
asked at all. For companies the value is never served.

The rule, therefore:

- **A served `dividendYield` wins, unchanged.** Its scale is #133's
  open defect and is untouched here — this slice widens what is
  *read*, never how a figure is interpreted.
- **An omitted `dividendYield` becomes `0.0` only where the provider
  states that zero itself** — a trailing field explicitly present and
  equal to zero. That is a provider statement, not an inference from
  silence.
- **Everything else stays absent.** No trailing fields, or nulls, or a
  positive value in them → `None`. A payload that answers nothing is
  still unread.

`ValueProvider._dividend_yield`, and nothing else in the reading
changed.

## 2. Two guards the corpus forced

**A historical dividend does not contradict a current zero.** ADBE
serves `lastDividendValue: 0.0065` — a payment from 2005 — beside
`trailingAnnualDividendRate: 0.0`. It is a non-payer today, and a
guard that treated any historical trace as a contradiction would have
refused the statement it exists to read.

**Two spellings that disagree establish nothing.** Where one trailing
field says zero and the other is positive, the payload contains two
statements of one fact that contradict each other, and that is not a
statement of zero. Measured at 0 occurrences; kept as a structural
guard, not as a response to an observed case.

**A positive trailing value is never promoted.** The rate is an amount
per share; the trailing yield is backward-looking where `dividendYield`
is forward-looking. Neither is this domain concept's quantity, so only
the zero — which both spellings agree on — is consumed. The two new
crossings are registered ASSUMED as
`ValuationSnapshot.dividend_yield (stated zero)`, and their `because`
says exactly that.

## 3. Before → after, over the audit's corpus

The same 78-security book and the same live payloads as
`QUALITY_BOTTLENECK_AUDIT.md`, both arms through the real adapter;
only the dividend reading differs.

| | before | after |
|---|---|---|
| applicable | 67 | 67 |
| size-readable | 47 | 47 — untouched |
| **complete = authorised** | **28** | **47** |
| HIGH | 22 | 22 |
| MEDIUM | 5 | 13 |
| LOW | 1 | 12 |
| lost (previously complete, now not) | — | **0** |

**+19, exactly the audit's expectation**, and the composition is what
the audit named: every company whose size and earnings were already
readable and whose only missing answer was the dividend.

Newly complete solely because a stated zero became readable:
**ADBE, AMD, AMZN, BA, CLNE, DV, DXCM, FLYW, GRE.MC, INSE, IS7.DE,
LNTH, LUNR, MNST, NFLX, ORSTED.CO, RIVN, TSLA, UUUU.**

29 companies now hold a stated zero; the other 10 of them are still
incomplete for reasons this slice does not touch (dual-class or ADR
denominations — CPNG, DIDIY, MSTR, PLTR, SHOP, SRAD, SPCX, H2O.DE, SE,
ETOR). **After this repair, no company is blocked by the dividend
question alone.**

**HIGH is unchanged at 22, and that is the point.** A stated zero
earns no point, exactly as before — what changed is that the question
is *answered*, so completeness can be reached. The band composition
moves only into MEDIUM and LOW, which is what reading a real negative
answer looks like. It also makes the audit's §6 finding visible in the
corpus rather than in prose: TSLA, Amazon and Netflix are now banded,
and are structurally barred from HIGH by the dividend wall.

## 4. Invariants

| Check | Result |
|---|---|
| Quality authorised (live store) | **0/78** — unchanged; the store still predates C5/C6 |
| Recommendations | BUY 0 · **HOLD 78** · SELL 0 |
| Kernel deletion invariant | 135 deletions, **0 hardened** |
| Intra-Quality deletion invariant | 69 deletions, **0 direction moves** |
| Six blocking specimens | all **HOLD** |
| `provider-quality` fingerprint | `3adc0fd3fd9f` unchanged |
| `monetary-comparison` / `fx-translation` | `92a418fb4a78` / `e3a548db860c` unchanged |
| Bands, thresholds, `FACTORS`, completeness | untouched |

No live decision changes in this slice: the counterfactual above is
what the *next funded acquire* would produce, and the stored corpus
still carries no denominations, so the size factor stays unreadable
until then.

## 5. Non-goals honoured

No factor scoring change (a zero still earns no point); no
completeness change (3/3 still required); no band, threshold or
fingerprint-input change; nothing touched in denomination, FX or
dual-class handling; `dividendYield`'s scale defect (#133) left
exactly as it was, and deliberately — it is band-invariant while the
factor tests `> 0`, and repairing it is its own slice with its own
evidence.
