# S5.2 — Cache integrity, and mechanical issuance evidence

**Status: built 2026-08-10. Nothing scored.** Supply Structure remains
`VISIBLE_NOT_SCORED`, the quality quorum remains 2, every crypto headline
remains UNKNOWN, and no decision threshold moved.

Two sub-slices: `S5.2a` gave the shared cache a schema contract, and
`S5.2b` acquired the three issuance rules primary state can actually
support.

---

## A. JsonCache integrity result

### Stores affected

Eleven, all under `data/cache/`. **The architectural boundary the ruling
worried about already exists**: `JsonCache` is never pointed anywhere
else, and the authoritative stores — knowledge, statements, decisions,
events, evidence snapshots — are separate classes with their own
contracts. A cache miss loses a materialisation of a provider response,
never provenance. No storage boundary work was needed.

### The contract

```text
CURRENT       the schema this reader asked for        → decode
MIGRATED      an older schema, registered migration   → migrate, decode
UNVERSIONED   written before the store declared one   → by declared policy
INCOMPATIBLE  a different schema, no migration        → cache miss
MALFORMED     unreadable, or version metadata is junk → cache miss
```

Owned by `JsonCache` rather than repeated per provider. Eleven copies of
four lines means the eleventh is the one that gets forgotten — which is
precisely how the defect arose.

Three properties worth stating:

- **A record from a newer schema is never migrated backwards.** Two
  processes on different versions share a directory more often than
  anyone plans for, and guessing which fields the newer one dropped is
  the same guess this class refuses everywhere else.
- **Migrations are sequential and explicit.** A store at 3 with a
  migration for 1 but not 2 cannot read a version-1 record at all. That
  is the honest answer; the alternative is inventing the missing step.
- **A migration may refuse one record** by returning None, so a store
  need not pretend every record can come forward.

### Compatibility policy

| Store | Schema | Pre-version records |
|---|---|---|
| `primary_supply` | 2 | **refused** — a version-1 record carries no provenance and the establishment gate reads provenance, so there is nothing to bring forward. It re-acquires, which is a keyless chain read |
| the other ten | 1 | **accepted, deliberately** — their shape is what schema 1 describes, so adopting the contract cost no live API call |

`accepts_unversioned` is a statement about schema 1 **only**. The first
draft let it wave records through at any schema, which would have
rebuilt the silent decode the class exists to stop; a test caught it. An
accepted pre-version record now faces the same migration chain an
explicit version-1 record would, so a store that bumps to 2 must write a
migration or re-acquire.

### Tests

Fourteen, one per invariant the ruling named, including: an incompatible
schema does not silently decode; a migration works only when registered;
`"schema": "two"` is malformed rather than unversioned; a store
declaring no schema behaves exactly as before; a rejected record
re-acquires under the store's existing spend rules and the read-only
door stays silent; and every provider declares what it does with
pre-version records.

### Remaining storage risk

None identified in `data/cache/`. The one residual observation: nothing
prevents a *new* store from declaring no schema. The guard is the test
that walks `app/providers` and asserts every `JsonCache` construction
passes one.

---

## B. Mechanical issuance corpus

| Asset | Mechanism | Parameters | All read? | Mutability | Path | Standing |
|---|---|---|---|---|---|---|
| **BTC** | Halving subsidy | tip height; subsidy derived | yes | **Protocol-fixed** | yes | CLAIMED |
| **ADA** | Reserve draw | ρ, τ, epoch length, reserves | **yes, all four** | Governance parameter | yes | CLAIMED |
| **SOL** | Tapering inflation | initial, taper, terminal, current | yes | Governance parameter | yes | CLAIMED |
| ARB · HYPE · 1INCH · TAO · ETH | — | — | — | — | — | **no entry** |

**No asset gets an entry it has not earned.** Arbitrum's supply arrives
because a contract releases an allocation, not because a rule creates
it. An entry saying so *in the shape of a rule* would be a placeholder,
and a placeholder on an investment surface is a claim.

Everything is CLAIMED. The layer is consumed by nothing and is guarded
by an import test.

---

## C. BTC residual reconciliation — **partially resolved, and the total stays claimed**

The research reported ~13.125 BTC. Measuring properly changed the
diagnosis twice.

**First: `blockchain.info/q/totalbc` is not a usable comparison.** It
reports a whole number of BTC (20,068,365.00000000) and **did not move
across six blocks** while height advanced. It is rounded and stale. The
"13.125 BTC" was largely an artefact of comparing a live height against
a frozen total.

**Second: against a precise figure, the residual is exactly constant.**
Blockchair publishes circulation to the satoshi at a stated height:

| Tip | Circulation (sat) | Rule (sat) | Residual (sat) |
|---|---|---|---|
| 961,886 | 2,006,836,791,655,096 | 2,006,839,687,500,000 | **2,895,844,904** |
| 961,887 | 2,006,837,104,155,096 | 2,006,840,000,000,000 | **2,895,844,904** |

Circulation rose by exactly 312,500,000 sat — one 3.125 BTC subsidy —
and the residual is **identical to the satoshi**. So:

- it is **not** a height mismatch
- it is **not** drift, and not per-block under-claiming accumulating now
- it is a **fixed historical difference of 28.95844904 BTC**, and *the
  rule is right about what each block pays*

**What is still unexplained is its composition.** It is larger than
nothing and *smaller than the genesis subsidy alone* (50 BTC), so it is
neither of the two obvious candidates — genesis exclusion or the BIP30
duplicate coinbases (100 BTC). It has not been itemised.

There is also an honest limit on the comparison itself: if the explorer
computes circulation from the same subsidy rule minus known losses, a
constant difference is exactly what that would produce, and this
platform cannot tell that apart from an independent count.

**Verdict: the emitted *total* stays below ESTABLISHED**, marked
`emitted_is_derived`, with both caveats attached. The *rule* and the
*forward path* are unaffected — a fixed historical constant does not
propagate into future issuance.

---

## D. ADA issuance path — fully primary-derived

Every parameter is read. Nothing is remembered, including the epoch
length.

| Parameter | Value | Read from |
|---|---|---|
| ρ monetary expansion | 0.003 | `/epoch_params → [0].monetary_expand_rate` |
| τ treasury growth | 0.2 | `/epoch_params → [0].treasury_growth_rate` |
| epoch length | 432,000 s | `/epoch_info → [0].end_time − start_time` |
| reserves | 6,196,427,118 ADA | `/totals → [0].reserves` |

`draw = reserves × ρ` each epoch; `τ` goes to the treasury and the rest
to stakers. Under the rule as observed:

| Horizon | Drawn from reserves | Reaching holders after τ |
|---|---|---|
| 1 year (73 epochs) | 1,220,340,830 ADA | **976,272,664 ADA** |
| 4 years (292 epochs) | 3,619,349,062 ADA | **2,895,479,249 ADA** |

**Only Cardano can separate the ruling's three supply concepts.** The
treasury share moves to a pot that is itself excluded from circulating
supply, so the supply *issued* and the supply *reaching holders* are
different numbers and are reported apart.

ρ and τ are protocol parameters Cardano's own governance can change, so
the rule is recorded as `GOVERNANCE_PARAMETER`. A reproducible
projection is not an immutable one.

---

## E. Dynamic-supply result — **uncapped is not unruled**

**Solana qualifies, and comfortably.** `getInflationGovernor` returns
the whole schedule in one keyless call: initial 8%, taper 15% a year,
terminal 1.5%; `getInflationRate` gives the current 3.705%. No constant
is remembered, so Model C gate 3 is satisfied by construction.

That answers the ruling's twelfth section directly: **an asset with no
maximum supply can have a better-published issuance rule than a capped
one.** Solana's is more completely served than Bitcoin's, whose
parameters no endpoint publishes at all.

Solana publishes a *rate* and no supply figure, so `emitted` is None
rather than zero — a zero would be a number nobody measured.

**Ethereum does not qualify.** Its burn is available from a secondary
source and validator issuance is not read, so net issuance cannot be
assembled from primary state. `max_supply_infinite` remains a useful
*positive* statement that no cap exists; it is not an issuance rule.

---

## F. Allocation-release gap — preserved, unchanged

| Asset | What is missing |
|---|---|
| **ARB** | which buckets hold the 33.9–87.2% of maximum outside the market, and when each releases. Two vendors are 419% apart on circulating |
| **HYPE** | the cadence for 412.5m allocated-but-unemitted tokens. The protocol publishes *who* (94,023 genesis addresses summing to exactly 1bn) and *how much*, and nothing about *when* |
| **1INCH** | any release schedule; no primary surface at all |
| **TAO** | the emission rule is not located in chain storage; `TotalIssuance` alone |

Recorded as `EVIDENCE_UNAVAILABLE_FROM_CURRENT_FREE_SOURCES`. **A 401 is
a statement about access, not disclosure.** Nothing here says these
protocols fail to publish a schedule — only that this platform cannot
reach one.

---

## G. Revised Supply Structure architecture

**Split it, along the line the corpus drew.** Two capabilities, not one
factor:

**Supply Policy Predictability** — mechanically issued assets.
*Is future issuance governed by an explicit and reproducible rule?*
Evidence exists for BTC, ADA, SOL.

**Allocation Release Visibility** — allocation-release assets.
*Is the future release of allocated supply observable and defined?*
Evidence exists for none.

Neither is required of every token, which is what the S3 capability
composition is for. Forcing them through one denominator is what
produced the ARB inversion.

---

## H. Scoring readiness

| Question | Verdict | Why |
|---|---|---|
| Supply Policy Predictability | **VISIBLE_NOT_SCORED** | three assets have reproducible rules and *mutability differs among them* — Bitcoin's is consensus, Cardano's and Solana's are governance parameters. Scoring them alike would flatten the difference; scoring them apart needs a corpus of more than one protocol-fixed asset |
| Allocation Release Visibility | **NOT_READY** | no evidence for any applicable asset, and a paid API is not the asset's failing |
| Supply Structure (the single question) | **VISIBLE_NOT_SCORED** | unchanged. The split above supersedes it as the eventual shape |
| Market robustness | SCORABLE_NOW | unchanged, still the only one |

**Quorum unchanged at 2, and unreached.** Every asset still has exactly
one scorable question, so no headline is emitted and no verdict moved.

---

## I. Recommendation

**Itemise the Bitcoin residual, or acquire a second precise circulation
source.** It is small, bounded, and it is the only thing standing
between the corpus's cleanest mechanical case and an established figure.
Two routes, in order of cost:

1. A second independent precise circulation figure. If two explorers
   that do not share a computation agree, the perimeter comparison
   becomes real and the ambiguity in section C dissolves.
2. Enumerate coinbase under-claims directly. Exact, and expensive: it
   means reading historical coinbase outputs, which no keyless endpoint
   serves in bulk.

Not recommended yet: a second protocol-fixed mechanical asset to make
mutability scorable. That is a real gap — one consensus-fixed asset is
not a corpus — but it is an argument for patience rather than
acquisition.

---

## Boundaries held

Nothing scored. Age stays retired; volume/mcap liquidity stays retired;
generic circulating/max stays retired. No market context, no valuation.
No decision threshold changed. Equity behaviour untouched. Every
projection carries its rule version, its starting state and the
mutability of the rule, and is worded *under the currently observed
issuance rule* rather than as a fact about the future.
