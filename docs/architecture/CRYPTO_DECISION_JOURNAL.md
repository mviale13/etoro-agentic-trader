# What MOVRvest judged about a digital asset, at each recorded point

**Status: DV6, built. Closes the journal gap DV3 opened and DV4 and DV5
left recorded. No model call, no acquisition, no production write.
Stopped for ruling.**

> **The read side converged across DV3–DV5. The canonical crypto decision
> was still never written down**, so the platform could say what it thinks
> about BTC today and nothing about what it thought last week under the
> evidence that existed then.
>
> It is journalled now — through the same journal, carrying the rule that
> decided it and the exact committee records it rests on, and **appended
> only when something has actually moved**.

---

## 1. The gap

`ExecutivePipeline._digital_asset` carried an explicit refusal, written in
DV4:

> *Deliberately not journalled. A decision derived from recorded judgments
> is a projection, recomputed on every read — writing it back would create
> a second history of the same judgments.*

That was true of a writer that appended once a day whether or not anything
changed. It is no longer true, and the reason is §4.

## 2. The journal as it stood

- **Persisted**: an `Event` of type `EXECUTIVE_DECISION_RECORDED` carrying
  `state`, `conviction`, `rationale` and (since #127) the five scores.
- **Written**: in `ExecutivePipeline.execute`, only when a `journal` is
  supplied — the portfolio, brief, dossier and research routes supply one;
  a test or what-if evaluation does not.
- **Deduplicated**: once per symbol, per day, per state.
- **Read**: `DecisionHistory` → the change feed (state changes only,
  quoting the recorded rationale verbatim), `DecisionCourse` and
  `DecisionTrend` on the dossier, and `ConvictionChange` on the thesis.
- **Numeric conviction**: already `int | None` since DV2, and
  `conviction_change_against` already refuses to subtract against an
  absence. **No consumer assumed a number.**
- **Company strengths/risks**: never stored on a record at all, so there
  was nothing to fabricate.
- **Judgment ids**: available on `InvestmentConsideration.judgment_id` and
  stable (`20260811T122514-e730d6ad`), but reaching no decision object.

**The schema could represent a digital-asset decision without lying** —
what it could not do was say *which rule decided it* or *what it rested
on*, and those are the two facts that make a crypto record auditable.

## 3. What is persisted now

Two optional keys, written only where the decision carries them, so **no
existing record shape changes**:

| key | meaning |
|---|---|
| `decided_under` | the rules' `key@version` identities — `["digital-asset-gates@1"]` |
| `evidence_records` | the exact committee judgment ids, sorted |

`DecisionRecord` gained the matching fields, both defaulting to empty.
**Empty means the record predates the stamp, never that no rule applied** —
which is exactly what distinguishes a retired-path record from a canonical
one, with no stored byte rewritten.

References, never copies: a judgment is immutable and already stored under
its own id, so duplicating its payload would create a second copy that
could drift.

## 4. Change semantics — checked, not assumed

The existing rule is a *convention about how often to write*: a decision
reached from scores has no stable identity behind it, so the day is the
finest resolution at which two of them can honestly be called the same.
**That rule is untouched.**

A decision that names the records it rests on can do better, and the
discriminator is a structural property of the decision — *does it carry
evidence references* — not the asset class. Such a decision is compared
against the **last one recorded**, on three terms:

| what moved | recorded? |
|---|---|
| the posture | **yes** |
| the judgment ids beneath a steady posture | **yes** — #113's *evidence moved under a steady answer*, the ordinary case, and the one a day-and-state rule silently drops |
| the rule version | **yes** — otherwise upgrading to `@2` would leave the last record looking as though it had been decided under a rule that did not exist yet |
| nothing | **no** |

So a page view can append only when something actually moved. **Measured
live: two consecutive full runs over BTC, ETH and SOL wrote three records
and then nothing.** That is what makes DV4's objection obsolete rather
than overruled.

## 5–9. The specimens, written and read back

| | recorded |
|---|---|
| **BTC** | INVESTIGATE · no conviction · `digital-asset-gates@1` · 2 judgment ids · Supply Governance's conclusion preserved, Value Capture's wrong-instrument finding travelling as evidence weighed and never as a risk |
| **ETH** | INVESTIGATE · no conviction · the evidenced mechanism preserved · the issuance gap still an open question under its owner's name |
| **TAO** | **MONITOR, recorded as a decision** — `judged=True`, both committees' applicability findings preserved. A history that dropped it would report *we have never judged this* about an asset whose committees both ran |
| **ARB** | INVESTIGATE · the 81% circulating-supply spread recorded as what research would settle, never as a risk |

Live agreement at write time: for BTC, ETH and SOL the stored state,
rationale and references are identical to the live canonical decision.

## 10–11. History is never recomputed

A synthetic sequence records MONITOR (no applicable question established)
and then INVESTIGATE (one established, from a changed judgment set). Two
entries exist, and **the first entry's state, rationale, conviction,
provenance and references are byte-identical after the second is
written** — asserted as a frozen tuple, and again after a later decision
worded the same asset entirely differently.

## 12. The history that already exists

Production holds **45 crypto decision records** from the retired path
across eight assets — BTC 17, ETH 9, SOL 9, HYPE 5, TAO 3, and one each
for 1INCH, ADA and ARB. They carry numeric convictions from 28 to 75,
rationales such as *"A cryptocurrency has no business quality or valuation
to assess"*, and states — PREPARE, REJECT — that `digital-asset-gates@1`
can never produce.

**Nothing is rewritten or migrated.** They coexist and are distinguishable
by provenance: a legacy record names no rule, a canonical one names
`digital-asset-gates@1`. The change feed still renders their original
rationales verbatim, which is #113's law rather than an oversight.

One honest residue, recorded: `DecisionTrend` says *"INVESTIGATE across
the last 9 reviews"* over a run that now spans both paths. The statement
is true — the recorded state was INVESTIGATE nine times — and it claims
nothing about which rule reached each one.

## 13. Test protection

DV5 found that crypto corpus assertions can silently skip against the
empty evidence root. **Every test here writes to a `tmp_path` repository
and reads none of the acquired store**, so none can pass by exercising
zero specimens — and `test_the_acceptance_suite_exercised_every_specimen`
asserts the corpus is non-empty, names its four members, and fails unless
every one of them was actually written and read back. No
`if fixture exists` guard appears anywhere in the module.

## 14. Regression

**0 movements** on DV2's six-equity panel and **0** across all fourteen
portfolio holdings. The equity dedup rule is pinned directly: same day,
same state, different wording still yields one record. Funds are
untouched — they never reach the crypto path.

## 15–16. Gates

`pytest -q` 3037 passed · ruff check + format clean · `mypy app` clean
(597 files) · `npm run build` + `tsc --noEmit` clean · production `data/`
byte-identical (every write went to a cloned evidence root).
