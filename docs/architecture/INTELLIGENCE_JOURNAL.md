# The Intelligence Journal — what this platform knew, and when

**Status: built 2026-08-10. Decision-neutral, deterministic, no model.**
No recommendation threshold moved, no quality factor changed, no quorum
touched, equity untouched. Nothing here scores, decides, or reaches a
committee.

```bash
movrvest intelligence-journal BTC --evidence   # the record, and the reading of it
movrvest acquire                               # what writes to it
```

---

## The problem it closes

Every layer before this answers a question about *now*. To a
point-in-time system these five sentences are the same sentence:

```text
ETF flows are positive today.
ETF flows have been positive for three weeks.
ETF flows turned positive today after three negative weeks.
ETF flows were positive but are weakening.
Nothing materially changed.
```

An investor treats them completely differently, and a decision layer
cannot consume intelligence that cannot tell them apart.

---

## A. The model

```text
JournalEntry     one finding as one capture read it — immutable, forever
Capture          one acquisition of one asset, whole
ObservationStatus  OBSERVED · UNAVAILABLE · NOT_APPLICABLE
ChangeNature     WORLD_MOVED · SOURCE_REVISED · READING_CHANGED · UNDETERMINED
TemporalStatus   FIRST_OBSERVED · STILL_PRESENT · CHANGED · INCREASED ·
                 DECREASED · DISAPPEARED · UNAVAILABLE
ObservationSpan  count · first · last · largest_gap
TemporalFact     what the record says about one key, with its entry ids
```

An entry carries the asset, the capture id, when **we** looked, the
finding key, its family and claim type, its status, the sentence, the
value **where one genuinely exists**, the source, and **when the source
says its figure is from**. That last field does more work than any
other; see §D.

**Qualitative findings get no invented number.** A regulatory suspension
has no value, so it is compared by wording and reported as `CHANGED`
with no direction. Encoding it numerically would make it comparable with
a fee reading and mean nothing.

**Storage is JSON Lines, one file per asset, opened in append mode and
never in write mode.** There is no code path that can rewrite a line,
because a store that *could* would eventually be asked to. **Schema
rides on the line, not the file** — every other store here versions the
file, which works when a file is rewritten whole; this one never is, so
a schema-1 line must stay readable beside a schema-2 line forever.

---

## B. Observation and change detection are separate

`record` writes and knows nothing about change. `project` reads and
states what the record says, and says nothing about what it means.

`positive on 3 consecutive captures` is what the projection may
produce. `ETF demand has persisted` is downstream. `bullish
institutional demand is strengthening` is not anywhere in this codebase.

Asserted by test: no `TemporalStatus.stated` string contains *bullish*,
*bearish*, *strong*, *weak*, *demand*, *positive* or *negative*.

---

## C. "For three weeks" — the rule the layer is judged on

Three captures across twenty-one days are not three weeks of
observation. `ObservationSpan` carries the count, the first, the last
and the **largest gap**, and every sentence is worded from them:

> *"Observed on 3 captures spanning 21 day(s), the longest gap between
> them 14 day(s)."*

A run is counted in **captures**, never in time:

> *"Unchanged across the last 3 capture(s)."*

The surface leads with a **Coverage** section before any finding,
because a reader who does not know the platform looked three times
cannot judge a claim built on three observations. Where the largest gap
is two days or more it says so explicitly: *"Anything between them was
not observed."*

Tested directly: the wording contains `on 3 captures`, `spanning 21
day(s)` and `the longest gap between them 14 day(s)`, and contains
neither `for three weeks` nor `for 21 days`.

---

## D. The world changed, our evidence changed, our reading changed

Conflating these would be the worst defect this layer could ship, and
the distinction is structural rather than advisory. It rests on the
**source's own timestamp**, not ours:

| | Test | Meaning |
|---|---|---|
| `WORLD_MOVED` | the source's date advanced | a new figure for a new moment |
| `SOURCE_REVISED` | the source's date is unchanged, the figure is not | the source revised itself |
| `READING_CHANGED` | either side is not `OBSERVED` | **not an economic event** |
| `UNDETERMINED` | the source dates nothing | said rather than guessed |

An unavailable reading **is never compared with a value** — including
with another unavailable reading, so two outages are not a stable
observation. This is what stops a provider outage from arriving as
*"holdings fell to zero"*, which would be a lie assembled entirely out
of true parts.

---

## E. The ten acceptance demonstrations

Each is a named test over controlled captures. A temporal layer measured
against a moving corpus proves nothing, because the thing under test is
what happens *between* two readings.

| # | Demonstrated | Result |
|---|---|---|
| 1 | unchanged evidence is not a new development | 3 identical captures → one `STILL_PRESENT`, `run_length=3` |
| 2 | a genuine measured change is detected | `$128m → $540m` → `INCREASED`, `WORLD_MOVED`, previous value carried |
| 3 | new is distinguishable from changed | `flow.30d` `INCREASED` beside `holdings` `FIRST_OBSERVED` in one projection |
| 4 | unavailable ≠ a negative observation | outage → `UNAVAILABLE`, no value either side, *"a fact about the reading and not about the asset"* |
| 5 | a provider failure is not an economic event | `READING_CHANGED`; never `DECREASED` |
| 6 | history is unchanged by later runs | the first line survives byte for byte; a correction is a **new entry naming what it corrects** |
| 7 | synthesis can cite a grounded temporal fact | `H1` findings carry journal entry ids; demonstrated live below |
| 8 | deleting the observations removes the claim | file unlinked → `history() == ()` and **no `H` finding exists** — unavailable, not reconstructable |
| 9 | sparse observation is not continuous monitoring | wording carries count + largest gap; duration-only phrasing asserted absent |
| 10 | nothing decides | import-graph test: no Asset Quality, no `ExecutiveDecision`, no `CommitteeOpinion`, no model |

Plus: a `NOT_APPLICABLE` finding produces no temporal fact at all (HYPE
has no US spot ETF, which is not a gap); one unreadable line does not
cost the record; and replaying an identical capture appends nothing
while looking again an hour later is a second capture — because the
platform did look twice, and §5 says the count of looks is the fact
every temporal claim is built from.

---

## F. Measured on live evidence

Four controlled captures over the real BTC snapshot: unchanged at +7
days, a genuine move at +14, then the flow surface broken six hours
later.

**The genuine move, as of capture 3:**

```
[increased] nature=world_moved
Over the last 30 published days those funds took $540m net, positive on 21
of them. The previous reading, on 3 August, was $128m. Compared with the
capture before it, the source reported a later reading. Observed on 3
captures spanning 14 day(s), the longest gap between them 7 day(s).
```

**The outage, at capture 4** — two facts, both honest, neither economic:

```
[unavailable ] SoSoValue could not be read — ConnectionError  This platform
               could not read it in the latest capture, which is a fact about
               the reading and not about the asset.     nature=reading_changed
[disappeared ] …took $540m net… — last seen 10 August, and not produced by
               the latest capture.
```

Note what did **not** happen: no `DECREASED`, no zero, no development.

**Synthesis citing the record (acceptance 7), live.** The temporal
finding supplied:

```
[H1] (Journal — higher than the previous reading, from 3 recorded
      observation(s): 20260727T120000-f1a932c5:flow.30d,
      20260803T120000-0d5a692f:flow.30d, 20260810T120000-bb3167bc:flow.30d)
```

What the model wrote from it:

> *"Spot BTC ETF flows strengthened: 7 August saw $99m net, the 30-day net
> rose from $128m to $540m with 21 positive days, after earlier
> offsetting days and five straight inflow sessions."* — `refs=('C4',
> 'H1', 'C5')`

**Code established the history; the model explained it.** The sentence
is a temporal claim the platform could not previously make, it points at
the journal entries that support it, and it says nothing about coverage
the platform did not have.

---

## G. What the architecture can now truthfully say

Before this slice, MOVRvest could say what was true at a moment. It can
now say, **with evidence a reader can check**:

- **that something is new** — first observed, on this capture;
- **that something has held** — unchanged across N captures, with the
  span and the largest gap stated;
- **that something moved, and in which direction** — where a
  measurement exists on both sides, with the previous figure quoted;
- **that something changed without a direction** — where the finding is
  qualitative, refusing an invented number;
- **that a change was the world, or the source correcting itself** —
  from the source's own timestamp;
- **that it stopped being able to look** — distinct from anything the
  asset did;
- **that a question stopped being produced** — distinct again from
  being unreadable;
- **and how much it is entitled to claim** — because every one of the
  above is worded from a count of captures rather than a duration.

Equally important, the things it still **cannot** say, by construction:

- it cannot say a condition was continuous between two captures;
- it cannot say what any of it means for an investment case;
- it cannot say a change is good or bad, and no status carries a
  direction of sentiment;
- and it cannot reconstruct a temporal claim whose observations are
  gone — the claim becomes unavailable, which is the honest state.

---

## Boundaries held

- **No decision contract.** §J of the synthesis report stays parked and
  unimplemented, exactly as ruled.
- **The journal asks no model**, and no synthesis prose is ever stored
  as history — asserted over the parse tree.
- **Asset Quality and the decision layer are unreachable** from all four
  journal modules.
- **No scoring**, no committee, no portfolio reasoning, no
  recommendation.
- **Slice 3's invariants are untouched**: one call per asset, grounded
  findings only, no tools or retrieval, per-item refs, no verdict field,
  worded absence on failure, and removing evidence still removes the
  model's ability to recover it.
- Equity behaviour unchanged.
