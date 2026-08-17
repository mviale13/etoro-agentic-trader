# Does HON still need paid readings, and how many?

**Status: BQ17 audit, research only. No model call, no re-observation, no
production write, no code change. Stopped for ruling.**

> **Yes — five, and the number is forced rather than chosen.** The
> deterministic path is now provably correct: today's parser reads all
> three of HON's periods with their figures. What remains is acquisition,
> not discovery — the platform cannot call a figure established without a
> reading, and the quorum being replaced is five.
>
> **The audit also corrects the sequencing plan, in both directions.**
> Superseding alone strips HON of its grounded assessment entirely; and
> the intuitive fix — observe first, supersede after — is a **no-op**,
> because the stopping rule counts only authoritative readings and would
> find the quorum already full.

---

## 1. Why HON was queued

BQ28 found that HON's income statement was parsed with **the rowspan not
carried down**: an empty `colspan=3 rowspan=2` stub above the year row
shifted `2025/2024/2023` three columns left, so `row_figures` returned
**zero headed figures**. The parser was repaired, and HON was the only
company in the corpus affected.

The five readings were meant to test one hypothesis: **that a fresh
reading under the repaired parser records the prior-period figures, so
revenue and earnings growth become answerable and HON can band.**

The hypothesis still exists. What has changed is that DV2 made grounded
`BusinessQuality` authoritative in the decision layer, so the outcome now
propagates further than it would have then.

## 2. HON's current end-to-end path

| boundary | state |
|---|---|
| **filing** | 10-K 0000773840-26-000013, located; income statement 1 table, 26 rows printing a figure |
| **deterministic parse (today)** | `Net sales` → **2025: 37,442 · 2024: 34,717 · 2023: 33,009**; `Net income` → **2025: 4,772 · 2024: 5,740 · 2023: 5,672**. All three periods headed. |
| **stored readings** | **5, all income statement**, no balance-sheet or cash-flow readings at all |
| **statement audit** | all 5 `stale_provenance`, supersedes — *"the filer heads 37,442 with '2025' and the reading recorded 'Years Ended December 31,'"*. **HON is the only company in the corpus with any refuted reading.** |
| **FinancialUnderstanding** | quorate |
| **BusinessQuality** | **UNKNOWN**, 1 of 3 answered — profitability `strong`; both growth factors *"prints no earlier period this platform can date from"* |
| **score / basis** | `quality_score = None`; basis states the 1-of-3 arithmetic |
| **DecisionEvidence** | `security_evidenced = True`, `grounded_quality` carried |
| **decision gates** | INVESTIGATE via DV2's assessed-but-inconclusive branch, conviction withheld |
| **rendered wording** | *"Business quality was assessed from 10-K … and could not be concluded. 1 of 3 factors answered…"*, and under review conditions *"2 of 3 quality questions are still unanswerable"* |
| **journal** | 1 record (2026-08-17), `quality_score = None`, conviction 64 from the DV1 era — historical and immutable |

**The stored readings are not empty — they are single-period.**
Profitability answers because it needs only the current period. Growth
fails because it needs two.

## 3. HON against the controls

| | grounded state | score | evidenced | decision | wording |
|---|---|---|---|---|---|
| **AAPL** | MEDIUM, 1 favourable of 3 answered | 62 | yes | PREPARE 60 | *"quality conviction is not yet sufficient"* |
| **UNP** | MEDIUM, 1 favourable of 3 answered | 62 | yes | INVESTIGATE, conviction withheld | *"merits deeper research"* |
| **DIS** (HIGH control) | HIGH, 2 favourable of 3 | 80 | yes | PREPARE 74 | — |
| **KO** (UNKNOWN control) | UNKNOWN, **0 of 3** | none | yes | INVESTIGATE | total-revenue tie, a *different* cause |
| **HON** | UNKNOWN, **1 of 3** | none | yes | INVESTIGATE | assessed, could not conclude |

**HON's remaining uncertainty is extraction, and only extraction.**
Acquisition is done (the filing is held), grounding is sound (the parse
reads the figures), scoring is sound (AAPL/UNP/DIS band from the same
rules), propagation is sound (DV2 carries the object), gating is sound,
and the wording is sound. KO's failure is a different one — a contested
concept, already ruled on elsewhere — and the two must not be conflated.

## 4–5. What remains, and whether it needs a model

The facts are **deterministically visible**, and the outcome is
therefore predictable:

- revenue growth 2024→2025 = **+7.85%** → score 55 → `moderate` → 0 points
- earnings growth 2024→2025 = **−16.86%** → score 0 → `declining` → 0 points
- profitability already `strong` → 1 point

→ **1 favourable of 3 answered → 33% → MEDIUM → 62**, the same shape as
AAPL and UNP.

**That prediction is not a substitute for the readings.** This platform
establishes a figure by reading it and agreeing with itself at quorum;
computing the growth here and calling it established would be exactly
the estimated-figure invariant it exists to refuse. What the prediction
buys is a **precise pass criterion** — we know what a correct outcome
looks like before spending.

So the residual uncertainty is narrow and genuinely model-dependent:
**will five readings of a now-unambiguously-headed table record the
three periods, and agree?**

## 6–7. Five, and why five

All five criteria hold, and the count is not a matter of taste:

1. the unpaid path is correct — verified above with the figures;
2. the remaining question needs observation, because only a reading can
   establish a fact here;
3. it is product-relevant — HON moves from *cannot conclude* to a band
   that DV2 made authoritative in the decision layer;
4. it would be the first end-to-end proof that a parser repair reaches a
   band through fresh observation;
5. **`QUORUM = 5`, and the entire existing quorum is being withdrawn.**

One or three readings leave HON below quorum, which makes
`FinancialUnderstanding` non-quorate and `BusinessQuality` **None** — the
state measured in §8 below. Five is the *minimum* that restores a quorate
understanding, not a comfortable margin.

## 8. The protocol

**Order is forced, and the intuitive alternative is a no-op.**
`FinancialStatementService.observe` counts *authoritative* readings
against its target, with the reason written at the line: *"a superseded
reading has no vote, so letting it fill the count would mean an audited
statement could never be re-read."* So observing before superseding finds
five authoritative readings, considers the quorum full, and **takes zero
readings**. Supersede must come first.

```bash
movrvest statement-audit HON --supersede
```
```bash
movrvest observe-statements HON --statement income_statement
```

- **Readings**: 5 (the command stops at the quorum on the count, never on
  the content).
- **Held constant**: the filing (0000773840-26-000013, immutable), the
  statement kind, the reader model, the parser.
- **Compared**: the anchors each reading records — label, cell address,
  column header and printed figure — and then the derived consensus.
- **Pass**: ≥3 of 5 readings anchor `Net sales` and `Net income` at
  column headers `2025`, `2024`, `2023` with the figures in §2; the
  consensus settles both concepts; `BusinessQuality` reaches
  **MEDIUM 62** with earnings growth `declining` and revenue growth
  `moderate`.
- **Acceptable variance**: disagreement on rows this platform does not
  consume; a reading that records fewer than three periods, so long as
  the modal answer carries three.
- **Extraction instability**: readings disagree on the *cell address* for
  the same concept, or record different column headers for the same
  figure.
- **Scoring instability**: the consensus settles but the band does not
  match the deterministic prediction — which would mean the rule tables
  disagree with the arithmetic above.
- **Propagation defect**: HON bands and the decision layer still shows
  `quality_score = None`, or the review condition still says the quality
  questions are unanswerable.
- **Production protection**: run against a cloned evidence root
  (`MOVRVEST_EVIDENCE_ROOT`) first and compare, exactly as this audit
  did; promote to production only after the clone passes.
- **Estimated model calls**: 5 for production. Add 5 if the clone is
  rehearsed first — **10 total for the risk-free path**, and the extra
  five buy the guarantee below.

**The risk the ordering creates.** Between the supersede and the fifth
reading, HON holds no authoritative reading: `BusinessQuality` is None,
`security_evidenced` is False, and the decision reverts to *"No
security-level analysis is available for HON."* Measured, not predicted —
§10. That sentence is **truthful** in that state (HON has no provider row
either), but it is strictly less informative than what HON shows today.
**So the supersede must not be run unless the readings can follow
immediately.** Rehearsing on a clone first removes the exposure.

## 9. Funding readiness, non-chargeable

Read from configuration only; no probe was made.

- `MOVRVEST_READER_PROVIDER` and `MOVRVEST_READER_MODEL` are **empty**,
  which is *not* unconfigured: `_resolve_provider` falls back to
  `DEFAULT_PROVIDER = "openai"` and `DEFAULT_MODELS["openai"] = "gpt-5"`.
- `openai_api_key` is **set**. `anthropic_api_key` is **empty**.
- The 429s recorded in earlier reports were on the **Anthropic** path,
  which is not the path this would take.

So the reader resolves to **openai / gpt-5** on a credential that exists.
**Whether that account has balance is unknown and was deliberately not
tested**, since the only way to learn it is a chargeable call.

## 10. Deterministic defects found

**None in the code.** The parse, the audit, the consensus stopping rule,
the scoring, the propagation and the wording are all correct, and the
suite is green without a line changed.

One **sequencing hazard**, measured on a clone rather than assumed:
running `statement-audit HON --supersede` alone takes HON from

| | today | after supersede alone |
|---|---|---|
| grounded | UNKNOWN, 1 of 3, profitability strong | **None** |
| `security_evidenced` | True | **False** |
| rationale | *"assessed … could not be concluded"* | *"No security-level analysis is available for HON"* |

That is correct behaviour over a genuinely refuted quorum, not a bug —
but it is a regression in what the investor is shown, and it is why the
two steps are one slice.

## 11–12. Gates and production data

No code changed. `pytest -q` 3062 passed · ruff clean · `mypy app` clean
(598 files). Production `data/` byte-identical: every command that could
write ran against a cloned evidence root, and the one production-path
audit was run without `--supersede`.

## 13. Recommendation

**Spend — five readings, as one atomic slice, after a clone rehearsal.**

The deterministic work is finished and correct; what is left is the
acquisition the architecture requires before it will call a figure
established. The expected result is HON **MEDIUM 62**, and the value is
as much in the propagation proof as in HON itself.

Two conditions on funding it:

1. **Do not run the supersede unless the readings can follow in the same
   session.** The clone rehearsal is the cheap insurance.
2. **Confirm the OpenAI balance out-of-band** — this audit could not, and
   would not spend to find out.
