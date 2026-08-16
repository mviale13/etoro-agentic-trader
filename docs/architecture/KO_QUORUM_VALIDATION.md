# KO crosses the quorum: the whole authority chain, validated

**Status: funded validation complete. Four additional readings spent —
the exact budget. Production evidence byte-identical. No semantic
change of any kind. Stopped for ruling.**

BQ11 earned one vocabulary label offline and proved with a single
reading that KO's evidence becomes semantically answerable. It could
not produce a band, because one reading is not a quorum. BQ12 spends
the remaining authority to find out whether the *existing* consensus
contract turns that evidence into an authorised answer.

**It does. KO bands MEDIUM (62), on 2 of 3 questions, with every rule
unchanged.**

---

## 1. Paid readings used

**Four** — observations 2, 3, 4 and 5, all KO, all against the same
cached 10-K `0001628280-26-010047`, all `gpt-5`. Combined with BQ11's
single reading, KO reaches the quorum of five exactly. **No other
company was observed.**

## 2. Per-reading results

Every reading returned the identical anchor and the identical
deterministic expansion:

| Reading | Anchor | Label | Header | Dated cells |
|---|---|---|---|---|
| 1 (BQ11) | 47,941 | `Net Operating Revenues` | `2025` | 47,941 · 47,061 · 45,754 |
| 2 | 47,941 | `Net Operating Revenues` | `2025` | identical |
| 3 | 47,941 | `Net Operating Revenues` | `2025` | identical |
| 4 | 47,941 | `Net Operating Revenues` | `2025` | identical |
| 5 | 47,941 | `Net Operating Revenues` | `2025` | identical |

**Zero disagreement across all five.** The run aborted on any
divergence by construction — a guard compared every reading's anchor,
label and full row tuple after each observation and would have stopped
before spending the next.

**LLM recognition versus deterministic expansion, kept apart:** the
model contributed exactly one thing per reading — *which row is the
company's total revenue*. Every historical value and every period label
came from `row_figures` reading the filing's own table. The model is
credited with none of the three dated cells.

## 3. Consensus progression

| After reading | Observations | Quorate | Band |
|---|---|---|---|
| 1 | 1/5 | no | none — below quorum |
| 2 | 2/5 | no | none |
| 3 | 3/5 | no | none |
| 4 | 4/5 | no | none |
| **5** | **5/5** | **yes** | **MEDIUM** |

Established measures were stable from the first reading onward — gross
margin 0.6163, operating margin 0.2871, revenue growth 0.0187 — and did
not move as readings accumulated. **Nothing about the evidence changed
at reading five; only the authority to use it did.**

## 4. Quorum semantics, stated exactly

- **Required quorum: 5.**
- **Agreeing observations: 5 of 5.**
- **They are five readings of ONE filing**, not five filings, five
  periods or five sources.
- **What the contract grants them:** the quorum measures *reader
  stability on one document* — how far repeated readings of the same
  text agree — which is what `movrvest reader-stability` exists to
  report. It is **not** a claim that five independent sources
  corroborate the figure, and the architecture does not treat it as
  one.

**This is the question the brief asked me to stop on, and it does not
fire.** The consensus does not represent repeated readings as stronger
evidence than reader agreement: it counts readings, words them as
readings, and grants exactly the authority its own semantics describe.
The band therefore rests on a legitimate claim — *this platform read
one filing five times and read it the same way each time* — and on the
document's own arithmetic beneath that.

## 5. Evidence that repetition was not misrepresented

Measured over every investor-facing sentence KO's quality now produces
— the derivation, all factor evidence, all gaps, all refusal wording:

| Phrase | Occurrences |
|---|---|
| `readings of one filing` | **3** |
| `observations` | **0** |
| `independent` | **0** |
| `corroborat…` | **0** |
| `sources` | **0** |

BQ4's distinction survives the whole chain intact. Nothing anywhere
calls five readings of one document five observations, and nothing
claims corroboration.

## 6. Business Quality, before → after

**Before** (production, five *stale* readings under the old
vocabulary):

| | |
|---|---|
| answered | **0 of 3** |
| profitability | not answerable — `total_revenue` unlocated |
| revenue growth | not answerable — `total_revenue` unlocated |
| earnings growth | not answerable — `net_income` unlocated |
| score / band | — / **UNKNOWN** |

**After** (five fresh readings, unchanged rules):

| | |
|---|---|
| answered | **2 of 3** |
| profitability | **ANSWERED — excellent** (gross margin 61.6%, operating margin 28.7%), net margin gapped |
| revenue growth | **ANSWERED — weak** (+1.9%) |
| earnings growth | still not answerable — `net_income` unlocated |
| score / band | **62** / **MEDIUM** |

**The causal chain, per change:**

1. BQ11 accepted `Net Operating Revenues` → `total_revenue` 47,941
   establishes.
2. `total_revenue` is the **denominator** of both gross and operating
   margin → profitability becomes answerable, verdict *excellent*, one
   favourable point.
3. `total_revenue`'s deterministic row expansion supplies 2024's 47,061
   → revenue growth computes at +1.9%, verdict *weak*, no point.
4. Two answered questions meet `MINIMUM_ANSWERED = 2` → a band is
   authorised.
5. One favourable of two answered = 50% → **MEDIUM → 62** under the
   unchanged ruler.

**Earnings growth remains unanswered**, exactly as intended:
`NET_INCOME` was not widened, so KO's `Consolidated Net Income` is
still outside the vocabulary. The experiment proved the 2-of-3 rule
rather than making KO answer everything.

**The band is reported, not celebrated.** MEDIUM is the honest output
of one favourable factor out of two answered; it says Coca-Cola's
margins are excellent and its revenue growth is weak, on two of three
questions. That the result is non-UNKNOWN is not what makes the
experiment a success — that it is *authorised* is.

## 7. Final state

**KO: MEDIUM (62), 2 of 3 answered, quorate 5/5.**

## 8. Falsification — none fired

| Condition | Result |
|---|---|
| differing current values across identical-source readings | **no** — all five identical |
| historical periods/values disagreeing | **no** — identical row tuples |
| a revenue component promoted to `TOTAL_REVENUE` | **no** — only `Net Operating Revenues` |
| ambiguous row identity | **no** — same label, same anchor, every reading |
| a value on the wrong period | **no** — headers read from the filing's own header row |
| authority from changed thresholds/completeness | **no** — nothing was changed |
| production evidence modified | **no** — see §9 |
| repetition presented as independent filings | **no** — see §5 |
| a band before the contract allows | **no** — none until 5/5 |

## 9. Production-store invariance

`data/statements/KO.…json` MD5 **`aad67e5c57a3385fb5dbaf37a9341ec0`**
before and after. `git status --porcelain data/` empty. Every
observation was written to the isolated root `/tmp/bq11`, carrying
BQ11's artifact forward so attribution stays intact across both slices.

## 10. Next recommended slice

**One: `NET_INCOME` vocabulary, under BQ11's arithmetic standard.**

KO is the natural specimen and the evidence is already in hand: its
statement prints `Consolidated Net Income`, and the same
filing-arithmetic test that earned `Net Operating Revenues` can be
applied to it — a bottom line stands in a determinable relation to the
lines above it, where a component does not. It would complete KO's
third question and, more importantly, test whether the arithmetic
standard generalises beyond one concept.

It should be run exactly as BQ11 was: **offline falsification across
all 24 companies first**, with the adversarial population being the
income-like components (`Net income (loss) from equity method
investments`, `Other income`, `Total interest income`), and paid
readings only if the offline stage earns them.

**Not recommended yet:** AXP, FITB, UNP, the comparative cohort,
Citigroup, HON. Each is a separate attribution, and BQ12's whole value
is that KO's chain is now attributable end to end.

## Scope compliance

No `CONCEPT_LABELS` change · no `CONCEPT_WORDS` change · no extraction
change · no consensus/quorum change · no Business Quality, threshold or
completeness change · no financial-model change · `NET_INCOME`
untouched · no other company observed · crypto, UI, HON, the
six-company question-contract problem and PR #145 all untouched.
