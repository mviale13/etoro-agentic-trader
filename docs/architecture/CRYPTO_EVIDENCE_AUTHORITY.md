# S4.5 — Crypto evidence authority: what primary state can settle

**Status: measured and built 2026-08-10 (`5d694a7`, merged locally as `fc17e38`). No score, threshold, band,
factor or decision changed. `ESTABLISHED` was not weakened, and nothing
in S1–S4 was re-judged.**

The S4 readiness report ended on a blocker: crypto Asset Quality is
constrained by **evidence authority**, not by a shortage of candidate
metrics. Eleven of twelve investment questions read *claimed* because
there is one source, not because the figures are thin.

So this slice asked the ruling's question and measured it:

> Is independently reproducible computation from canonical primary state
> epistemically equivalent to cross-provider corroboration?

**The measured answer is: sometimes, and the conditions are checkable.**
Two of the four surfaces cleared every bar; one cleared none of them and
looked identical from the outside; and one produced a figure that was
canonical, deterministic and wrong by a factor of 850 million.

> **Provenance.** This slice reached GitHub only on 2026-08-10, inside the squash commit [`4cb9516`](https://github.com/mviale13/etoro-agentic-trader/commit/4cb9516) that merged [PR #103](https://github.com/mviale13/etoro-agentic-trader/pull/103). Its own merge commit carries a `(#NNN)` suffix that matches no pull request: the number was written by hand and never existed. The per-slice history is preserved on the `history/crypto-s3-to-s4.6` branch; the commit hashes above are the authority, not the suffix.


---

## The two findings that decide the ruling

### 1. Canonical inputs, deterministic method, catastrophically wrong

Ethereum's blob base fee is computed from `excessBlobGas` and a protocol
constant. Using the constant this platform knew (EIP-7691's 5,007,716):

```text
computed   4,222,810,848,427,812 wei
the node               4,973,775 wei      eth_blobBaseFee
```

**Wrong by a factor of ~850 million**, from a canonical input, by a
computation that looked perfectly deterministic. The constant had
changed at a fork this platform does not track; the value that
reproduces the node's own answer is ~11,684,671, which was recovered by
bisection rather than known.

Nothing about the shape of that computation would have signalled the
error. It is the sharpest available demonstration that **primary is not
a synonym for true** — and it is why the burn figure this platform
computes is the base-fee component only, which needs no constant at all.

### 2. A protocol's own field that does not mean what it says

Hyperliquid's `info` API publishes `totalSupply = 999,044,028.59`. It
**includes 412,513,565 tokens that do not exist yet**. The reconciliation
found it, and it reconciles exactly:

```text
totalSupply            999,044,028.5858
− nonCirculatingUserBalances   287,507,716.9363   (4 named addresses)
− futureEmissions              412,513,564.9696
= 299,022,746.6799
  circulatingSupply reported   299,022,746.6799   ← to the last decimal
```

Copying the field would have been wrong by 412 million. Checking the
field against its own components is what turned a read number into an
understood one.

---

## A. The evidence-authority model

**Two axes, never one.** `EvidenceStanding` keeps meaning *MOVRvest
considers this sufficiently grounded for canonical use*. A new
`EvidenceAuthority` says what kind of thing it is, and — the practical
payoff — **what would have to happen for it to establish**.

| authority | what it is | what would corroborate it |
|---|---|---|
| `PRIMARY_OBSERVATION` | read from the protocol's own state or API — the subject *is* the source | a second independent access path agreeing |
| `PRIMARY_DERIVED` | MOVRvest's deterministic computation over primary observations | the recorded rule + inputs + a second run — **the ruling below** |
| `SECONDARY_COMPUTATION` | a third party's deterministic computation over canonical state, not reproducible here | either a second party computing it, or gaining the access — which *moves the class* rather than corroborating |
| `SECONDARY_AGGREGATE` | a vendor's figure over a perimeter it chose | a second independent vendor — S1's rule, unchanged |
| `PROVIDER_SCOPED_AGGREGATE` | a figure whose **universe is the vendor's definition** | **nothing.** No source-independent value exists |
| `ATTRIBUTED_OPINION` | another party's judgment under their name | nothing, and nothing should |

The axis is enforced apart from standing by test: the two enums share no
member value, `evidence_authority.py` cannot import `EvidenceStanding`,
and no reasoning path can import either.

**The reproducibility contract** (`PrimaryComputation`) carries what a
stranger needs: surface, network, entity, block or time window, units,
formula, **rule version**, observation time and raw input references. Two
properties, and the difference between them is the slice in miniature:

- `is_repeatable` — the record is complete enough to run the recorded
  method again.
- `is_independently_reproducible` — *and* the surface is canonical and
  the authority primary. Bitcoin's fee total is repeatable and **not**
  independently reproducible: asking the same explorer twice is not
  checking it.

---

## B. The three-chain experiment

| | fact | surface | canonical | authority | independently reproducible |
|---|---|---|---|---|---|
| **ETH** | base-fee burn over 300 blocks | execution JSON-RPC | ✅ | `PRIMARY_DERIVED` | **yes** |
| **HYPE** | circulating supply; Assistance Fund | protocol's own API | ✅ | `PRIMARY_OBSERVATION` | **yes** |
| **ADA** | four ledger supply concepts | ledger totals | ✅ | `PRIMARY_OBSERVATION` | **yes** |
| **BTC** | fees in one block | explorer API | ❌ | `SECONDARY_COMPUTATION` | **no** |

### Ethereum — computable here, and the comparison is a perimeter finding

```text
window   blocks 25,723,806–25,724,105 (300 blocks, exactly 3600 s)
formula  Σ baseFeePerGas × gasUsed ÷ 1e18
result   0.871034 ETH burned  =  20.90 ETH/day at that rate
```

Seven batched requests read an hour of Ethereum. Against DefiLlama:

| | 24h | |
|---|---|---|
| DefiLlama holder revenue (base + blob) | **$32,159** | a full day |
| MOVRvest base-fee only, scaled | **$40,261** | one hour, scaled |

1.25× apart — and **not a disagreement**. Different windows and
different perimeters: mine excludes blob fees and covers a busy hour.
A perimeter difference is evidence about the perimeters.

### Bitcoin — the contrast, and it is a property of the ledger

A Bitcoin block **carries no fee figure**. Recovering one needs the value
of every transaction input, which needs an indexed node. mempool.space
publishes `extras.totalFees` (0.0321 BTC for the block read); that is
their arithmetic, and this platform cannot re-run it.

And the failure mode is live: **blockchain.info's published
`total_fees_btc` was `-44,687,500,000` when this was measured** — a
negative fee total, served without complaint. That is what an
unreproducible figure looks like when it fails.

So the same economic question — *what did users pay to use the network* —
is primary-computable on Ethereum and not on Bitcoin, and the difference
is the shape of the two ledgers rather than the effort spent.

---

## C. HYPE value accrual — mechanism and amount, separated

| | evidence | authority | standing |
|---|---|---|---|
| **The Assistance Fund exists and holds HYPE** | address `0xfefe…fe`; holds **46,311,782.58 HYPE** by the protocol's own `spotClearinghouseState`; **listed by name** in the token's own `nonCirculatingUserBalances` at the identical figure | `PRIMARY_OBSERVATION` | CLAIMED |
| **99% of fees go to it** | DefiLlama's sentence, and nothing else | `SECONDARY_AGGREGATE` | CLAIMED |
| **$534.9k reached holders in 24h** | DefiLlama's figure | `SECONDARY_AGGREGATE` | CLAIMED |

**The mechanism's existence is now evidenced from the protocol itself**,
by two independent readings of its own state that agree to the decimal —
and this is *not* another website repeating DefiLlama. What remains
DefiLlama's alone is the *fee split* and the *daily amount*.

The object records what it does not establish: how much reached the fund
over any interval (a balance at a moment conflates arrivals, spending and
price), that the split is 99%, and that any of it is worth anything.

**The measurable next step, if the owner wants the amount:** the fund's
balance is a level, so *dated readings of it* make the accumulation
measurable by difference — the same technique the supply-drift
measurement already uses. One reading cannot; two can. No new
integration is needed.

---

## D. Supply methodology — and the S1 conflict is now explained

**Circulating supply is not a primitive chain fact.** Measured, not
asserted.

### Cardano settles it definitionally

The ledger publishes **four** quantities, epoch 648:

```text
circulation  36,550,320,207.15 ADA
reward          797,735,740.88
treasury      1,450,053,248.59
supply       38,803,572,882.17   ( = circulation + reward + treasury )
```

Now the three vendors S1 marked CONFLICTED:

| vendor | reported | equals the ledger's | error |
|---|---|---|---|
| **TokenInsight** | 38,803,572,882 | **`supply`** | **0.000%** |
| **CoinGecko** | 37,353,519,634 | `circulation + reward` | 0.015% |
| **Yahoo** *(rejected in S1)* | 36,550,320,128 | **`circulation`** | **0.0000%** |

**All three were right about different quantities.** The conflict was
semantic, not a data failure — and the reading S1 *rejected* matches the
ledger's own `circulation` to four decimal places. Nothing about ADA's
supply needed a better vendor; it needed the ledger's vocabulary.

### The four corpus assets

| | primary observable | primary computable | policy-dependent | status |
|---|---|---|---|---|
| **ADA** | ✅ four named quantities | ✅ | ✅ *which one is "circulating"* | **resolved definitionally** — no vendor need be preferred |
| **HYPE** | ✅ protocol publishes it | ✅ reconciles exactly | ✅ **four excluded addresses**, plus unemitted tokens inside `totalSupply` | **protocol's own policy**, and a **third number**: 299.0m against TI's 336.7m and CG's 222.4m |
| **ARB** | ✅ `totalSupply()` = **9,999,998,977.63**, identical from two independent RPC endpoints | ✅ for *total* | ✅ for circulating — the token is fully minted, so the entire question is which wallets to exclude | **total settled, circulating unresolved** |
| **TAO** | ❌ not reached | — | — | **unresolved**: no keyless canonical surface found (taostats requires a key) |

**No provider was named a winner**, per the ruling — enforced by a test
that forbids a vendor name in the primary-source module.

The vocabulary this points to, for a later ruling: distinguish
`on_chain_supply` (a primitive, where one exists) from
`reported_circulating_supply` (a policy, whoever's). HYPE demonstrates
that even the protocol's own answer is the second kind.

---

## E. Provider-defined aggregates — a permanent ceiling, not a gap

`PROVIDER_SCOPED_AGGREGATE` is recommended for total market
capitalisation, category aggregates, rankings and breadth.

For these, cross-provider corroboration is **category-inapplicable**: a
second vendor computing "the total" computes a *different total* over a
different universe. Chasing convergence would manufacture a consensus
about a question with no source-independent answer.

`can_be_corroborated` returns False for this class and for attributed
opinions, so a surface can distinguish *nobody has checked this yet* from
*nothing could*. The correct representation is the one S4 already
adopted: **"CoinGecko's universe total capitalisation"**, never "the
total crypto market capitalisation" — permanently attributed, and that
is not a deficiency.

---

## F. Revised S5 readiness

| question | applies | best authority available | can primary establish it? | second source still needed? |
|---|---|---|---|---|
| Market robustness | 8/8 | secondary aggregate | ❌ — market value needs a price, and price is a market fact | **no** — already established for 6/8 |
| Liquidity | 8/8 | provider-scoped | ❌ — venue volume is each vendor's universe | **unchanged**: NOT_READY, and S4 rightly left it alone |
| Supply / dilution | 8/8 | **primary observation** | ✅ **ADA, HYPE, ARB** — with the concept named | **no**, once the *concept* is ruled |
| Monetary scarcity | 1/8 | primary (cap established) | ⚠️ issuance schedule not read | yes, for the schedule |
| Network adoption | 7/8 | none | ⚠️ tx counts are chain-computable, not yet read | no — an access question |
| Network security | 6/8 | **primary derived (ETH)** | ✅ ETH; ❌ BTC (secondary computation) | chain-dependent |
| Protocol usage | 2/8 | secondary aggregate | ❌ not attempted | yes |
| Economic activity | 6/8 | **primary derived (ETH)** | ✅ ETH; ⚠️ others unread | chain-dependent |
| Protocol capture | 2/8 | secondary aggregate | ⚠️ HYPE plausibly, via fund-balance deltas | probably not |
| Token-holder value accrual | 6/8 | **primary observation for the *mechanism*** | ✅ mechanism (HYPE); ❌ amount from one reading | for the amount, yes |
| Resilience / evidence maturity | 8/8 | none | ❌ | out of Asset Quality by S3's ruling |

**What changed:** *supply and dilution* moved from PARTIAL-blocked-by-
conflict to **answerable once a concept is named** — the biggest single
movement, and it came from the ledger rather than from a vendor.
*Token-holder value accrual* split: its **mechanism** is now
primary-evidenced for HYPE while its **amount** is not.

**What did not change:** liquidity and market robustness are market
facts and no amount of chain access improves them.

---

## G. Recommendation — the ruling first, then a narrow S5

**S5 is not yet ready, and the missing piece is one decision rather than
more code.**

### The recommended model: **C, with a gate**

Model A (primary is just another claimant) is refuted by the ADA result:
the ledger did not add a fourth opinion, it explained the other three.

Model B (canonical primary establishes alone) is refuted by the blob
constant: a canonical, deterministic computation was wrong by 850
million ×, and nothing in its shape said so.

**Model C — primary establishes, secondary validates the perimeter —
survives both**, provided establishment is gated on properties this
platform can check rather than on the word "on-chain":

1. **identity** — the entity is confirmed by the source itself (HYPE
   found by name in the protocol's own metadata, never a stored id);
2. **semantics** — the figure reconciles against its own components, or
   its definition is published (the check that caught `totalSupply`);
3. **computation** — no undocumented protocol constant, or the constant
   is read from the source rather than remembered (the blob lesson);
4. **independent reproducibility** — canonical surface, recorded rule,
   recorded inputs;
5. **perimeter comparison** — a secondary source is consulted and a
   *difference is reported rather than reconciled*.

Under that gate, ETH's burn, ADA's four quantities and HYPE's supply and
fund would establish. Bitcoin's fee total would not, and should not.

### Recommended next slice (smallest that unblocks S5)

**S4.6 — apply the gate to the supply question only.** It is the one
place primary evidence resolves a live conflict rather than adding a
figure:

- name the concepts (`on_chain_supply` vs `reported_circulating_supply`);
- run the five-step gate over ADA, HYPE and ARB;
- let the S1 conflicts *dissolve* where the ledger explains them, and
  stand where it does not (TAO);
- change no score.

Then S5 designs Asset Quality over a corpus where at least one economic
question is genuinely established, consuming `QuestionCoverage` per
archetype.

**The S4 boundary is restated for S5 and unchanged:** market context —
relative return, breadth, dominance, category momentum, market volume —
**does not enter Asset Quality**. A good asset does not become low
quality because the market had a bad Tuesday. Evidence maturity likewise
stays outside, and calendar age stays deleted.

---

## What was built, and what it cannot do

`movrvest primary [BTC|ETH|ADA|HYPE]` runs the experiment: it reads
canonical state and prints each figure with its authority, its window,
its formula, its rule version, its inputs and both reproducibility
verdicts.

It is in the family of `movrvest reader-stability` and
`movrvest statement-shape`: **a measurement of this platform, not of an
asset**. It costs a fetch, asks no model, **stores nothing**, and decides
nothing. Enforced by test — the module may not name a cache, and no
reasoning path may import any of it.

Every figure it produces is `CLAIMED`. Being canonical earned a fact its
authority label and nothing else; the standing rule is the owner's to
move.

1738 tests, ruff, mypy green. The hermetic guard now blocks the wire on
all four new surfaces — every one of them keyless, which is exactly why
a credential guard would not have stopped a single call.
