# S5.3 — What a supply policy tells an investor

**Status: measured 2026-08-10. No factor created. Nothing scored.**
Quality quorum stays 2, every crypto Asset Quality verdict stays UNKNOWN,
Supply Policy Predictability stays `VISIBLE_NOT_SCORED`, Allocation
Release Visibility stays `NOT_READY`.

The question: *what characteristics of a supply policy are actually
relevant to the long-term quality of the investment object?*

---

## The finding, first

**Predictability does not discriminate. Magnitude does. They are two
questions, and only one of them looks like quality — and it is not the
one that discriminates.**

All three mechanical assets are *equally* explicit and *equally*
projectable. Every parameter of every rule is read from the chain; every
rule projects. The only dimension separating them is mutability, and
there it is one asset against two.

Meanwhile their five-year supply expansion runs **2.73% to 14.51%** — a
factor of five.

A measure that cannot tell three assets apart is not a measure of those
assets.

---

## A. BTC / ADA / SOL policy comparison

| | **BTC** | **ADA** | **SOL** |
|---|---|---|---|
| Policy type | Halving subsidy | Reserve draw | Tapering inflation |
| Primary authority | consensus rule | protocol parameters | protocol parameters |
| Parameters | tip height (read); subsidy derived | ρ 0.003, τ 0.2, epoch 432,000 s, reserves — **all read** | initial 8%, taper 15%, terminal 1.5%, current 3.705% — **all read** |
| Remembered constants | 50 BTC, 210,000 blocks — cross-checked by reproduction | **none** | **none** |
| Mutability | **Protocol-fixed** | Governance parameter | Governance parameter |
| Reproducibility | yes | yes | yes |
| Forward path | yes | yes | yes, as a rate |
| Standing | CLAIMED | CLAIMED | CLAIMED |

**Rule explicitness is unanimous.** Every one of the eleven parameters
across the three rules is read from a chain surface. Nothing here
separates the assets.

**Mutability is the only separator, and it is thin.** Bitcoin's schedule
needs a consensus change; Cardano's and Solana's are parameters their own
governance can move. One protocol-fixed example is not a corpus, and
banding on it would rest the entire distinction on Bitcoin being the only
asset of its kind this platform reads.

Note the ruling's warning holds in both directions: governance
flexibility is not automatically a defect. Cardano's τ exists so the
treasury can be funded without a fork; that is a design, not a weakness.

---

## B. Forward supply measurement

Under the currently observed policy. MOVRvest's arithmetic from rules
read at block 961,892 / epoch 648 / epoch 1014, never a forecast.

| | 1 year | 3 years | 5 years |
|---|---|---|---|
| **BTC** | 164,362 BTC · **0.82%** | 384,211 BTC · **1.91%** | 548,573 BTC · **2.73%** |
| **ADA** drawn | 1.22bn · 3.14% | 2.99bn · 7.70% | 4.13bn · **10.64%** |
| **ADA** reaching holders | 0.98bn · 2.52% | 2.39bn · 6.16% | 3.30bn · **8.51%** |
| **SOL** | rate 3.15% · 3.70% | rate 2.28% · 9.83% | rate 1.64% · **14.51%** |

**Assumptions, stated because they are assumptions.** Bitcoin's horizons
assume the ten-minute block target — the block counts are exact, the
dates are not. Cardano's assume ρ and τ hold. Solana's compound the
published taper; its expansion needs no supply figure because the rate
*is* the expansion, which is how the projection avoids the one quantity
Solana does not publish.

Rule versions: `btc-halving-schedule/1`, `ada-reserve-draw/1`,
`sol-tapering-inflation/1`.

---

## C. Predictability vs magnitude — distinct conclusions

They rank the corpus differently, and one of them barely ranks it at all.

```text
by predictability   BTC ·  ADA = SOL          (only mutability separates)
by magnitude        BTC (2.73%) · ADA (10.64%) · SOL (14.51%)
```

The conclusions an investor would draw are not the same:

> *Predictability*: "All three publish a rule you can re-run. Bitcoin's
> needs a fork to change; the other two need a governance vote."

> *Magnitude*: "Over five years, Bitcoin creates 2.7% more coins,
> Cardano 8.5% more reaching holders, Solana 14.5% more."

Only the second distinguishes an investment case. Combining them into
one number would weigh a dimension the corpus is unanimous on against
one it spreads five-fold — and the unanimous dimension would contribute
nothing but noise.

---

## D. Architectural placement

| Concept | Belongs to | Why |
|---|---|---|
| Rule explicitness | **visible evidence only** | unanimous across the corpus; no discriminating power |
| Path predictability | **visible evidence only** | same |
| Rule mutability | **Asset Quality, eventually** | a genuine durable asset property, but n=1 for protocol-fixed |
| **Prospective supply expansion** | **a future Tokenomics layer — not Asset Quality** | see below |

**Magnitude is not a quality defect, and this platform already knows
why.** S3 established that the same fee figure means the security budget
on Bitcoin, a burn on Ethereum and a buyback on Hyperliquid — and that a
quantity whose meaning depends on where it flows cannot be scored until
the flow is established. **Issuance is the mirror image.** Solana's
14.51% pays validators who secure the chain; Cardano's τ share funds a
treasury; Bitcoin's 2.73% pays miners. The number is identical in kind
and opposite in meaning depending on destination.

This platform cannot yet trace where issuance goes — that is the
holder-value-accrual question, which is `VISIBLE_NOT_SCORED`. Scoring
magnitude before answering it would repeat exactly the error S3 was
written to prevent.

So: **prospective supply expansion is evidence today and belongs to
tokenomics tomorrow, not to Asset Quality.**

---

## E. BTC residual — mechanism evidenced, itemisation unresolved

A bounded investigation, and it changed the picture twice more.

**A second precise source exists.** Coin Metrics' community API is free
and keyless and publishes `SplyCur` to eight decimals.

**The three sources disagree with each other**, which settles what kind
of thing the residual is:

| Source | Character |
|---|---|
| rule from height | the consensus upper bound |
| Blockchair `circulation` | ~29 BTC *below* the rule, constant to the satoshi |
| Coin Metrics `SplyCur` | ~330 BTC *above* my height-matched rule, varying with the match |
| blockchain.info `totalbc` | whole BTC, and stale — **do not use** |

Coin Metrics exceeding the rule is impossible under consensus, so the
excess is a snapshot-convention offset in matching their daily timestamp
to a block height, not a supply claim. The disagreement is therefore
about *convention*, and the residual is not one ledger fact three parties
measured differently.

**But the flow is confirmed, decisively.** Across **89 consecutive daily
intervals** of Coin Metrics data:

- **89 of 89 are short** of a whole number of subsidies
- **0 of 89 exceed it** — not once
- largest single-day shortfall 0.0055 BTC; total 0.0177 BTC over 90 days

So the rule is a **strict upper bound on issuance, never violated**, and
under-claiming is continuous and tiny — about 0.073 BTC a year at this
pace. That is the same mechanism that produced the historical residual,
now *evidenced in the data* rather than speculated. It does not itemise
28.96 BTC: 0.073 a year over sixteen years is roughly 1 BTC, so the rest
came from larger historical events this platform cannot enumerate
without reading historical coinbase outputs in bulk, which no keyless
endpoint serves.

**Verdict, per the ruling's section 2 — and the two standings are now
genuinely different:**

| | Standing | Evidence |
|---|---|---|
| **Historical supply stock** | below ESTABLISHED, marked derived | residual unitemised; three sources use three conventions |
| **Issuance transition rule** | independently confirmed | 89 of 89 intervals within the bound, never exceeded; one Blockchair block-to-block step exactly one subsidy |

The stock does not block the rule. A fixed historical difference does not
propagate into future issuance.

---

## F. Allocation-release status — unchanged, and carefully worded

| Asset | Missing evidence |
|---|---|
| **ARB** | which balances hold the 419%-disputed difference, and when they release |
| **HYPE** | the cadence for 412.5m allocated-and-unemitted; genesis publishes who and how much, never when |
| **1INCH** | any release schedule; no primary surface |
| **TAO** | the emission rule was looked for in chain storage and not located |

`EVIDENCE_UNAVAILABLE_FROM_CURRENT_FREE_SOURCES`, not
`NO_SCHEDULE_EXISTS`. The `movrvest issuance ARB` surface says so in as
many words: *"a statement about what this platform can reach, not about
what the protocol discloses."*

---

## G. Scoring recommendation

| Candidate | Verdict | Why |
|---|---|---|
| Rule explicitness / path predictability | **VISIBLE_NOT_SCORED** | unanimous across every asset that has a rule; discriminates nothing |
| Rule mutability | **VISIBLE_NOT_SCORED** | a real asset property, and one protocol-fixed example is not a corpus |
| Prospective supply expansion | **OUTSIDE_ASSET_QUALITY** | its meaning depends on where issuance goes, which is unanswered. Belongs to a future tokenomics layer |
| Allocation Release Visibility | **NOT_READY** | no evidence for any applicable asset, and a paid API is not the asset's failing |

**Factor #2 has not been earned.** Crypto remains UNKNOWN, which the
ruling anticipated and permits.

---

## H. Recommendation

**The next evidence question is: where does newly issued supply go?**

It is the single question that unblocks the most, and the measurement
above is what identifies it. Magnitude is the only supply dimension with
discriminating power, and the only reason it cannot be scored is that
this platform cannot say whether 14.51% a year is a security budget or a
transfer. Answering the destination would:

- make prospective supply expansion interpretable, and so scorable
- feed the *same* answer into holder value accrual, which is
  `VISIBLE_NOT_SCORED` for exactly this reason
- apply to allocation-release assets too: where an unlock goes matters as
  much as when

Evidence exists to start: Cardano's τ already splits its draw between
treasury and stakers, from the chain. Bitcoin's subsidy goes to block
producers by consensus. Solana's governor names a `foundation` share
(currently 0.0).

Not recommended: acquiring a second protocol-fixed asset to make
mutability scorable. That gap is real and is an argument for patience.

---

## Also in this slice

The AST `_identifiers()` helper had been written three times. S5.3
touched all three files, so it is now `tests/reachability.py` and the
duplicates are gone — the ruling's section 14, taken at the moment it
allowed.

`movrvest issuance [SYMBOL]` renders the evidence without scoring it:
the mechanism, every parameter with the surface it was read from, what
could change the rule, and the path under the currently observed policy.
Allocation-release assets get the specific missing evidence named
instead.

## Boundaries held

Nothing scored. Quorum unchanged. No price, no valuation, no market
context, no FDV. Uncapped is not treated as adverse — Solana has the
best-published rule in the corpus. Governance mutability is not treated
as adverse. No decision threshold changed; equity behaviour untouched.
