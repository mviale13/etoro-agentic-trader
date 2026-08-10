# Crypto Intelligence, slice 3 — the LLM synthesis

**Status: built 2026-08-10. Decision-neutral, off by default.** No
recommendation threshold moved, no quality factor changed, no quorum
touched, equity untouched. The model produces no evidence and can reach
no decision.

```bash
MOVRVEST_INTELLIGENCE_SYNTHESIS=on movrvest crypto-intelligence BTC --evidence
```

---

## A. The contract

**One call per asset**, over the snapshot slice 2 assembled. No tools,
no web access, no second pass, no retrieval. The model's universe is a
list of numbered findings.

**In** — `NarrativeFinding(id, statement, source)`, the Executive
Writer's own object, grouped by prefix so a citation says what kind of
thing it points at:

| | |
|---|---|
| `C` | a live claim — measured or reported, with its relevance band |
| `E` | a development, with how many sources carried it and its tier |
| `A` | an attributed reading, carrying its author, flagged if causal |
| `R` | relative market context, MOVRvest's interval-safe arithmetic |
| `F` | durable foundation — context, not news |
| `T` | an unresolved tension |
| `W` | a deterministic open question |

BTC supplies 22 findings; ETH 24; HYPE 21.

**Out** — three sections, each item carrying **its own refs**:

```json
{"what_matters":   [{"stated": "...", "theme": "...", "refs": ["E3","E5","C7"]}],
 "why_it_matters": [{"stated": "...", "theme": "...", "refs": ["C6","F1"]}],
 "watch_next":     [{"stated": "...", "theme": "...", "refs": ["W2","C5"]}]}
```

There is **no recommendation field to fill**. The model is not asked
what to do, and the schema gives it nowhere to say.

`IntelligenceSynthesis` carries the three sections, a `SynthesisStatus`
(`WRITTEN` / `DISABLED` / `UNCONFIGURED` / `UNAVAILABLE` / `REJECTED` /
`THIN`), the worded `absent_because`, the model name, and provenance.
`grounded_in(known)` is a checked property, not a promise.

**§16 — the seam is reused, not rebuilt.** Same `NarrativeProvider`,
same `DraftRequest`/`Draft`, same `NarrativeFinding`, same
`build_provider`, same fail-closed philosophy, same worded absence, same
flag convention. A different prompt and schema were expected; a second
trust architecture was not. The synthesis service resolves its own
provider through the shared builder — the knowledge reader's pattern —
rather than importing the writer's resolver, which would have put
`ExecutiveDecision` one import from a module that must never reach it.
The **on switch** is separate (`MOVRVEST_INTELLIGENCE_SYNTHESIS`)
because wording a decision and reading an intelligence packet are
different jobs; the **provider and model** are the writer's, because
which model this platform talks to is one decision.

---

## B. The grounding validator

Every rule refuses one specific way a plausible sentence can be wrong.

| Rule | Rejects | Live example |
|---|---|---|
| **references** | a ref not supplied | `Z9` |
| **figures** | a number in no finding — including a **rounded** or **recomputed** one | model wrote `5.61m` where evidence said `5,610,842` |
| **entities** | a name in no finding | `Coinbase`, `CoinDesk`, `AI’s` |
| **guarded concepts** | domain knowledge the evidence never stated | `proof of stake`, `21 million`, `the merge`, `maximum supply` |
| **causality** | a causal verb with no attributed cause behind it, or one that drops its author | `drove`, `lifted`, `sent` |
| **actions** | a verdict aimed at the reader, or advice this platform never gives | `Investors should buy`, `MONITOR`, `position sizing` |
| **shape** | empty statements, no refs, over-long items, too many items, a theme that is a sentence | |

**§15 — it fails closed, and the whole draft fails together.** No
sentence is quietly deleted and the remainder shown as checked; that
would tell an investor what remains was verified *and that nothing was
removed*, and the second half would be false. This is the Executive
Writer's contract unchanged.

### What calibrating it against real drafts cost

The first validator was **wrong in both directions**, and the second
error is the instructive one.

**Too strict** — it refused correct writing:

- `hold` refused *"these funds already hold 1,223,634 BTC"*. **A verb is
  not a verdict.** Now only a directive (`investors should hold`) or a
  capitalised verdict (`HOLD`) is refused.
- Checking every capitalised word refused *"Operational signals are
  cautious"*, *"Divergent institutional actions…"*, *"Because perps fees
  are…"*. **The start of a sentence is where capitalisation means
  nothing.**
- Exact matching refused `ETF` against `ETFs`, `Aug` against `7 August`,
  `staking` against `record staked supply`, and `AI’s` against `Elfa
  AI`. Stemming and a possessive rule fixed all four.
- `0.09pp` did not match `0.09 percentage points`. Fixed in
  `anchors_in`, which both slices now share.
- `sent ` matched inside **absent** and **present**, refusing a correct
  sentence about absent evidence for asserting a cause. Causal verbs are
  now matched on word boundaries.

**Too loose** — and this one was found by the failure demonstration
itself. Exempting the first word of a sentence let **`"Coinbase led the
buying."`** straight through. The subject position is exactly where a
model puts a name it invented.

The resolution is **measured, not argued**. Across nine live drafts,
every sentence-initial rejection was ordinary English (*Operational,
Divergent, Short-term, Substantial, Analysts, Scale, Additional, Flat*)
and a fabricated name in that position appeared **zero times**. So the
first word is challenged only when it is *shaped* like a name — an
acronym, an internal capital, a digit, or the head of a capitalised
phrase — while mid-sentence stays strict.

**The honest limit, stated because it is real**: a fabricated
single-word plain-capitalised name in subject position is not caught by
the entity rule. Mid-sentence it is, and any figure it carries still is.
The alternative was a validator refusing most correct drafts, which
fails closed into showing the investor nothing at all.

**Acceptance rate after calibration: 9 of 12 live drafts**, and all
three rejections were defensible catches — a causal verb, a guarded
concept, and a figure written without its unit.

---

## C. BTC — real output

```
BTC — current intelligence
  Monetary network · read 2026-08-10 17:13 UTC

  What matters now
    · Price and relative move — BTC's performance is modest and slightly ahead of
      the market: +0.2% over 24h, +3.9% over 7d, +1.1% over 30d, and it outpaced
      crypto by 0.09 percentage points over 24h.            [C1, C2, C3, R1]
    · ETFs: scale and flows — US spot BTC ETF flows are positive but offsetting:
      $99m net on 7 August; last 30 days net $128m, positive on 18 days, with a
      -$445m sell day outweighing; ETFs hold 1,223,634 BTC — 6.1% worth $79.5bn.
                                                            [C4, C5, C6]
    · Institutions repositioning — Institutional actions diverge: Marathon sold
      23,093 BTC; H100 Group increased to 3,506 BTC; MicroStrategy sold 1,690 BTC
      for stock buybacks; Elfa AI states proceeds near ~$108.6M.
                                                            [E3, E4, E5, A1]
    · Network and operational risk — Network/operational signals are mixed: $139k
      fees in a day; a COLDCARD security incident remains ongoing; AUSTRAC
      suspended Cryptolink Bitcoin ATM registration.        [E1, E2, C8]

  Why it matters
    · Ownership concentration vs supply — ETF and public-company exposure is large
      versus a capped supply: ETFs hold 1,223,634 BTC — 6.1% worth $79.5bn, while
      179 public companies hold 1,282,501 BTC, within a system emitting 95.6% of
      21,000,000.                                           [C6, C7, F2]
    · Flows and price context — Offsetting ETF flows alongside modest price gains
      suggest no clear accumulation trend in this window.   [C5, C3]

  Watch next
    · Whether ETF flows regain persistent positive breadth rather than netting out
      across offsetting sessions.                           [W2, C5]
    · Whether the COLDCARD incident is resolved.            [W1, E1]

  ── then the full deterministic brief beneath ──
```

**What the LLM added, concretely.** The deterministic layer produced
*nine atomic events*, five of them shown as separate bullets. The
synthesis produced **four themes**, and the third one is the whole
point: Marathon selling, MicroStrategy selling and H100 buying are three
events the deterministic layer can only list, and *"institutional
actions diverge"* is a reading of them — while still pointing at
`E3, E4, E5`. It also **connected the flow dispersion to the price
context** without asserting cause, and **kept the tension** rather than
resolving it. That is what an analyst reading the list would say and
what a rule cannot.

---

## D. ETH — a different synthesis from different evidence

```
  What matters now
    · ETFs signal demand — US spot ETH ETFs have seen consistent net inflows
      recently, including $50m on 7 August, four straight inflow sessions, and a
      press-reported $245 Million last week; sources interpret this as sustained
      institutional demand that may support price discovery. [C4, C5, E3, A2, A3]
    · Concentration in treasuries — those funds report 5,610,842 ETH — 4.6% of
      supply, worth $10.7bn, while 33 public companies report 7,818,592 ETH.
                                                             [C6, C7]
    · Support vs. risks — Signals diverge: on-chain accumulation and record staked
      supply are reported, yet a wallet-drain incident raises security concerns,
      and a large holder exit drew attention.        [E4, A4, E1, A1, E5, A5]

  Why it matters
    · Flows versus scale — If ETF demand persists, attributed by sources as
      supporting price discovery, that could matter given Ethereum's $232.3bn
      market significance and its rule-governed issuance rather than a cap.
                                                             [A2, A3, F1, F2, F3]
```

**§5 preserved without being asked twice.** *"sources interpret this
as…"* and *"attributed by sources as supporting price discovery"* — the
attribution survived synthesis, which is exactly the sentence the
validator would have refused had the model written *"inflows supported
price discovery"* instead.

**No BTC template.** ETH's themes are ETF persistence, treasury
concentration, and a flow-versus-security tension; BTC's were price,
flows, institutional divergence and operational risk. Neither shares a
theme name with the other, and nothing in the prompt mentions either
symbol.

---

## E. HYPE — synthesis with no ETF or fund concepts

```
  What matters now
    · Revenue and buybacks — Hyperliquid's fee engine is sizable and channels value
      to HYPE: $843k fees/day with $535k reaching holders, and 99% of perps fees
      earmarked for HYPE buybacks; $10.9bn open interest, though revenue leadership
      is disputed by alternative readings.  [C4, C6, C8, E2, E3, A1, A3, A4]
    · Flows and participation — Demand signals are mixed: HYPE Spot ETFs logged
      $2.84M net inflows; three new wallets withdrew 165,425 HYPE from FalconX; yet
      Hyperliquid investors are dwarfed by Binance traders.  [E1, E5, A6, A7, E4]
    · Price-performance tension — -0.2% over 24h, +3.9% over 7d, -18.0% over 30d,
      underperforming the crypto market and Perpetuals, despite activity reaching
      the token and disputed circulating-supply figures. [C1, C2, C3, R1, R2, T1, T2]
```

**No MOVRvest ETF concept appears and nothing says one is missing.** The
`HYPE Spot ETFs` line is an *attributed event* — a source published it,
slice 2 recorded it as such, and the synthesis reports it as reported.
The buyback language is admissible only because DefiLlama's own
methodology sentence supplies it; strip that finding and the guarded
concept rule refuses it.

**§9 held under pressure**: *"revenue leadership is disputed"* and
*"despite activity reaching the token"* are two tensions the model kept
rather than resolving into a direction.

---

## F. Failure case — every rejection path, and the fallback

Deliberately invalid generations, pushed through the real service:

```
fabricated entity   → rejected: names 'Coinbase', which appears in no supplied finding
invented figure     → rejected: contains the figure '312000000', which appears in no
                                supplied finding. The synthesist may not calculate,
                                and may not round.
unsupported cause   → rejected: asserts a cause ('drove') where no supplied finding
                                contains an attributed causal reading
a recommendation    → rejected: told the reader to 'buy'. This layer says what
                                matters, never what to do.
```

Each renders as one line above an otherwise complete brief:

```
  MOVRvest reading — A synthesis was drafted and refused: A what_matters
  statement names 'Coinbase', which appears in no supplied finding.

  What changed
    · BTC returned +0.2% over 24 hours. …
```

**§14: the deterministic brief is unchanged underneath, every time** —
flag off, no credentials, model unreachable, model declined, empty
draft, unparseable draft, failed grounding, too little evidence. Eight
paths, eight worded absences, one test each.

---

## G. No external knowledge — the deliberately starved fixture

BTC's synthesis was run with **the entire durable foundation removed**:
the 21,000,000 maximum, the market significance, the economic system.
22 findings became 19.

| Term | Present in output? |
|---|---|
| `21,000,000` / `21 million` / `21m` | **absent** |
| `halving` | **absent** |
| `scarcity` | **absent** |
| `fixed supply` / `maximum` | **absent** |

**The validator accepted the draft** — the model stayed inside the
starved evidence rather than filling the gap from what it certainly
knows. What it wrote instead was about what remained:

> *"Divergent institutional actions — sales by Marathon and
> MicroStrategy versus accumulation by H100 Group — indicate rotation
> rather than uniform positioning."*

And where a model *does* reach, the rule fires: `proof of stake`, `21
million` and `the merge` are each refused by a different rule, which is
why there are three.

---

## H. Against the CoinGecko benchmark

The provider summary that motivated this work, beside the same asset's
brief:

| | CoinGecko | MOVRvest |
|---|---|---|
| **Selectivity** | 8 entries, chronological, price commentary included | 4 themes over 9 ranked events; price commentary refused as not-an-event |
| **Traceability** | a paragraph; sources named per entry | every statement cites finding ids; every finding names its source, tier and epistemic type |
| **Fact vs opinion** | *"ETF demand is supporting price"* stated flat | the flow is `REPORTED`, the price state `MEASURED`, *supporting* stays `ATTRIBUTED` with its author |
| **Dispersion** | *"$128m net"* | *"$128m net, positive on 18 of 30, largest selling day −$445m — offsetting flows rather than accumulation"* |
| **Conflicting signals** | one narrative | tensions preserved and named |
| **Length** | comparable | comparable |
| **Freshness** | minutes | minutes, and stale items leave |

The one thing CoinGecko still does better: **breadth of discovery**. It
sees stories MOVRvest's press rule deliberately declines to introduce.

---

## I. Product assessment — an Artificial CIO, or a better summary engine?

**Between the two, and closer to the first than at any previous slice —
but not there yet, and the gap is nameable.**

What is genuinely CIO-shaped now:

- It **selects**. Nine events become four themes, ranked by materiality
  rather than recency, and the reader is told which two or three things
  matter.
- It **connects across evidence families**, which no rule did: fund
  flows against a supply path, an exploit against participation, three
  holders' actions into one observation about positioning.
- It **holds tension** instead of resolving it — the single behaviour
  that most distinguishes an analyst from a sentiment score.
- It is **checkable end to end**. Every sentence points at findings;
  every finding points at a source with an epistemic type; a fabricated
  figure or name cannot survive.

What still separates it from an Artificial CIO:

- **It has no view.** It says what matters and why; it does not say what
  that means for *this portfolio*, at *this* cost basis, against *this*
  policy. That is deliberate and correct for now, and it is also the
  thing an investor actually wants next.
- **It does not weigh.** *"Signals are mixed"* is honest and is where
  the layer stops. A CIO says which side of mixed it lands on and what
  would change its mind.
- **It cannot see history.** Every brief is written fresh; nothing
  compares today's reading to last week's, so *"this is new"* and *"this
  has been true for a month"* read identically.
- **Its evidence is still mostly secondary.** Slice 2 measured that
  honestly, and no amount of synthesis quality changes what the sources
  are.

So: **the best summary engine this platform could build over its own
evidence, and the first layer that reads like an analyst rather than a
report generator.** Calling it an Artificial CIO would require the
portfolio.

---

## J. Recommendation — the minimum contract for the CIO

**Do not implement. This is the specification for when you rule.**

The bridge should be **evidence, not a score, and not this prose.**
`ASSESSMENT_CONVERGENCE.md` already describes the shape: convergence by
**projection**, never merger. Concretely, the minimum contract is four
things:

1. **Project claims into `Finding`s, not synthesis into a view.** An
   `IntelligenceClaim` is already ref-addressable and carries a
   `ClaimType`; a `Finding` carries `Sense` and `Dimension`. The bridge
   is a projection function over `MEASURED` and `REPORTED` claims only.
   **`ATTRIBUTED` and `INFERRED` claims must not project** — a
   recommendation must never move on somebody's opinion, and the LLM
   synthesis must not project *at all*, because it is a reading of
   evidence and not evidence.

2. **A new `Dimension` — current conditions — and nothing else changes.**
   Existing dimensions stay weighted as they are, so the addition can be
   measured against the decision journal before it is trusted.

3. **One committee consumes it, with an explicit remit.** The natural
   home is a Risk or Timing remit stating a position over *referenced*
   findings, exactly as `CommitteeOpinion` already does. It may
   `abstain`, and on current evidence it usually should.

4. **A standing that admits.** Every crypto intelligence claim is
   `CLAIMED`. Under the platform's own rules that is not enough to
   warrant a decision, so the honest first contract lets current
   conditions **raise or lower confidence and never flip a verdict** —
   the `FactOrigin` bridge `ASSESSMENT_CONVERGENCE.md` describes.

And one thing to build first, before any of it: **a history.** The
decision layer will want *"flows have been positive for three weeks"*,
and nothing stores yesterday's snapshot. An append-only intelligence
journal is a smaller slice than the coupling and it is a precondition
for it being worth anything.

---

## Boundaries held

- **Asset Quality** unreachable from all three synthesis modules.
- **The decision layer** unreachable — no `ExecutiveDecision`,
  `InvestmentDecision`, `Recommendation`, `DecisionSynthesis`,
  `CommitteeOpinion` or `InvestmentThesis`. Asserted over the parse
  tree.
- **No new evidence source.** The model reads what slices 1 and 2
  acquired.
- **No scoring.** No confidence, sentiment or strength number exists to
  produce, and an invented one is refused as an unsupported figure.
- **Off by default.** The deterministic brief is canonical.
- Equity behaviour unchanged.
