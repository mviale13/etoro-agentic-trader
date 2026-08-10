# S4.6 — Crypto supply semantics: what each number counts

**Status: built 2026-08-10 (`b236a41`, merged locally as `2a493f0`). No score, threshold, band,
factor or decision rule changed. `judge()` is untouched, so every
standing a score reads is exactly what it was.**

The rule this slice installs:

> **Two numbers only conflict if they claim to represent the same
> thing.**

Crypto supply is an accounting vocabulary, not one fact. Three vendors
were each reporting a different Cardano ledger quantity, correctly, and
this platform recorded the result as a data-quality failure because they
shared a label.

> **Provenance.** This slice reached GitHub only on 2026-08-10, inside the squash commit [`4cb9516`](https://github.com/mviale13/etoro-agentic-trader/commit/4cb9516) that merged [PR #103](https://github.com/mviale13/etoro-agentic-trader/pull/103). Its own merge commit carries a `(#NNN)` suffix that matches no pull request: the number was written by hand and never existed. The per-slice history is preserved on the `history/crypto-s3-to-s4.6` branch; the commit hashes above are the authority, not the suffix.


---

## A. The vocabulary

Five concepts. Each is here because the corpus forced it.

| concept | what it counts | why it exists |
|---|---|---|
| `MAX_SUPPLY` | the most that can ever exist | four corpus assets have a protocol-enforced cap and two have none — inferring one from issuance policy would invent a constraint |
| `EMITTED_SUPPLY` | tokens that exist today | the closest thing to a primitive, and the quantity a chain can usually answer without a policy |
| `FUTURE_EMISSIONS` | tokens the protocol will issue and has not | **Hyperliquid's own `totalSupply` counts 412m of them** |
| `EXCLUDED_BALANCE` | a balance some methodology removes | a circulating figure is a subtraction, and the thing subtracted is a choice |
| `CIRCULATING_ESTIMATE` | what one party holds to be available | never *the* circulating supply — always somebody's, including the protocol's |

Beside every figure sits a **`SupplyMethodology`**: who defined it, what
it includes and excludes, a version, and one load-bearing flag —
`disclosed`. **An undisclosed methodology is not a different
methodology.** Not knowing what a vendor excluded is a gap in this
platform; if it counted as evidence of a different definition, any two
numbers could avoid conflicting by being equally unexplained.

Comparison is by `concept + methodology + version`. That is the whole
rule, and it produces three verdicts: **corroborated**, **coexist**,
**conflicted**.

---

## B. ADA — the conflict dissolves, and nobody was chosen

The ledger publishes four quantities. The three vendors were each
reporting one:

| source | reported | equals the ledger's | error | verdict now |
|---|---|---|---|---|
| **TokenInsight** | 38,803,572,882 | **`supply`** — everything issued | **0.000%** | **corroborates the chain** |
| **CoinGecko** | 37,353,519,634 | `circulation + reward` | 0.015% | **coexists** |
| **Yahoo** *(S1 rejected this)* | 36,550,320,128 | **`circulation`** | **0.0000%** | **corroborates the chain** |

TokenInsight was never publishing a circulating estimate at all — it was
publishing emitted supply under the wrong label. CoinGecko counts
rewards; the ledger's own circulation does not. Both are right, and the
difference between them is now reported as *information*, not as a
contradiction.

**No provider was preferred.** A test forbids a vendor name in the
comparison logic.

**One conflict survives, and it is real:** CoinGecko's `total_supply`
for ADA is 45,000,000,000 — Cardano's protocol *maximum*, published
under a label its own documentation defines as coins created minus
burned. The ledger says 38.80bn. Primary evidence impeaching a vendor
figure is the correct outcome, and the same thing happens to TAO below.

---

## C. HYPE — decomposed, and still methodology-dependent

The protocol's own accounting, reconciled rather than copied:

```text
totalSupply                        999,044,028.5858
− futureEmissions                  412,513,564.9696   ← tokens that do not exist yet
= emitted supply                   586,530,463.6162

− 0x43e9…a251 (a foundation)       241,194,257.8481
− 0xfefe…fefe (Assistance Fund)     46,311,782.5847
− the zero address                       1,673.7868
− the burn address                           2.7167
= circulatingSupply                299,022,746.6799   ← reconciles to the last decimal
```

Each exclusion is kept as its own `EXCLUDED_BALANCE`. The result is
**not** declared the true circulating supply: it is *emitted supply
after the four exclusions the protocol names*, and the methodology says
so.

| source | circulating estimate | methodology |
|---|---|---|
| Hyperliquid (protocol) | **299,022,747** | published, four named addresses |
| TokenInsight | 336,685,219 | **not published** |
| CoinGecko | 222,445,714 | **not published** |
| Yahoo *(rejected in S1)* | 1,500,000,000 | **not published** |

**All six pairs conflict**, and the reason is stated: two of the parties
publish no exclusion set, so this platform cannot say they measure
something else. S4.6 succeeds without inventing a figure.

**The Assistance Fund appears here only as a balance.** Its
value-accrual role — fees buying HYPE — lives in the protocol-economics
family and the two never meet: a test forbids the words *fees*,
*protocol revenue* and *holder revenue* anywhere in the supply layer.

---

## D. ARB — evidence of staleness, not a precedence rule

| | |
|---|---|
| chain `totalSupply()` | **9,999,998,977.63**, identical from two independent RPC endpoints |
| CoinGecko total supply | 10,000,000,000 → **corroborated** (0.00001%) |
| TokenInsight circulating | **1,275,000,000 exactly** |
| CoinGecko circulating | 6,614,056,381 |

The two circulating figures **still conflict**. What the mapping records
is the evidence and its limit: 1,275,000,000 is the documented float at
launch and lands on a round number to seven significant figures, which a
measured quantity does not usually do — *consistent with a frozen input,
and not proof of one*. The decisive test is whether it moves across
dated readings, and the store holds one reading per source per day.

**No rule was created that makes an older or smaller provider lose.**
Time alone does not establish truth.

---

## E. TAO — resolved further than expected

S4.5 reported no keyless canonical surface. There is one: **Bittensor's
own Subtensor RPC answers over plain JSON-RPC without a key.**

```text
storage key  twox128("SubtensorModule") ++ twox128("TotalIssuance")
             0x658faa385070e074c85bf6b568cf055557c875e4cff74148e4628f264b974c80
TotalIssuance  11,218,142.119340581 TAO
```

XXH64 is implemented in the adapter rather than imported — a dependency
for forty lines of arithmetic that CI would have to install — and is
checked against the algorithm's published vectors by test. **A wrong key
returns null, not a wrong number**, which is the failure mode this
platform can live with.

What it settles and what it does not:

- **Emitted supply is now primary**: 11.22m TAO.
- **CoinGecko's `total_supply` of 21,000,000 is the protocol maximum**,
  and the chain contradicts it. A real conflict, found by primary
  evidence.
- **Circulating remains unresolved.** TokenInsight says 8.64m and
  CoinGecko 9.60m, both below emitted, neither publishing what it
  excludes. Most TAO is staked, and whether staked TAO circulates is a
  policy the chain has no opinion about. `UNRESOLVED`, with the demand
  named.

---

## F. Claims-pool re-judgment

| | S1 standing (unchanged) | S4.6 circulating comparisons |
|---|---|---|
| **BTC** | established | 3 corroborated |
| **ETH** | established | 3 corroborated |
| **SOL** | established | 3 corroborated |
| **1INCH** | established | 3 corroborated |
| **ADA** | conflicted | **1 corroborated, 2 coexist — dissolved** |
| **ARB** | conflicted | 1 conflicted — stands |
| **HYPE** | conflicted | 6 conflicted — stands |
| **TAO** | conflicted | 1 conflicted — stands, emitted now primary |

**The re-judgment is reported, not written into the store — and that was
a deliberate refusal.** `CompanyFactsService` reads
`established_value("circulating_supply")` and the crypto quality signal
reads that, so promoting ADA's standing would move its issuance factor.
Acceptance 11 forbids a score change, so the semantic layer explains the
conflict and `judge()` keeps its verdict.

**That is the one decision I did not take, and it is the owner's:**
whether a vendor figure mapped to a ledger concept by measurement should
establish in the token-facts pool. It would change ADA's factor and
nothing else in the corpus.

---

## G. Investor-facing rendering

A **Supply** section on the token dossier, grouped by what each number
counts rather than by who published it, with the methodology under every
figure and the provenance under that.

**ADA** reads: *"The circulating-supply estimates for ADA either agree
or count different, stated quantities. One figure below still disagrees
with the chain, and it is not about what circulates."* Then a **Different
numbers, both correct** block explaining that CoinGecko counts rewards
and the ledger's circulation does not — and a **Genuine disagreements**
block for the 45bn.

**HYPE** reads: *"Circulating-supply estimates for HYPE differ, and at
least one party does not publish which token buckets it excludes."* The
emitted/future split is shown as two figures, and the four excluded
balances are listed with their addresses.

Also `movrvest supply [SYMBOL]`, and a corpus table of facts, agreements,
coexistences and conflicts.

Verified rendered for ADA, HYPE and BTC, plus AAPL to confirm an equity
is sent no supply section at all.

---

## H. S5 readiness

| question | evidence | semantic coverage | standing | authority | ready? |
|---|---|---|---|---|---|
| **Supply structure** | emitted supply | ADA, HYPE, ARB, TAO **primary**; BTC/ETH/SOL/1INCH vendor-only | claimed | primary observation / derived | **READY for 4 of 8** |
| **Maximum supply** | protocol cap | 6 of 8 have one; ETH and SOL have none, correctly | established (vendors agree) | protocol constant | **READY** |
| **Future issuance** | unissued supply | **HYPE only** — no other protocol publishes it here | claimed | primary | **PARTIAL** |
| **Circulating methodology** | exclusion sets | ADA disclosed for all three; HYPE disclosed for one of four; ARB and TAO for none | mixed | mixed | **PARTIAL** |
| **Unlock / emission cadence** | schedules | **nothing** — no source read publishes one | absent | — | **NOT_READY** |
| Protocol economics | fees, revenue | single-source | claimed | secondary aggregate | **NOT_READY**, unchanged |
| Token-holder accrual — mechanism | fund + methodology | HYPE primary | claimed | primary observation | **PARTIAL** |
| Token-holder accrual — amount | daily flow | single-source | claimed | secondary aggregate | **NOT_READY**, unchanged |
| Liquidity | venue volume | vendor-scoped | claimed | provider-scoped | **NOT_READY**, untouched by design |
| Market robustness | market value | 6 of 8 established | established | secondary aggregate | **READY** |

### Recommendation: **S5 can begin, narrowly.**

The supply question is the first economic question with a real answer,
and the answer is a *structure* rather than a ratio. So:

1. **Do not score `circulating / max`.** ADA proves the numerator is
   ambiguous and HYPE proves it is contested. A supply reading that
   consumed one vendor's estimate would be scoring a definition.
2. **Score what is established**: emitted supply against the protocol
   maximum, where both are primary or corroborated — four assets today,
   and the other four say why not.
3. **Carry the methodology into the output.** A dilution reading whose
   denominator is somebody's policy must name whose.
4. **Rule on the promotion question in F first** if ADA's factor should
   move.

**Still blocking a full Asset Quality model, unchanged:** protocol
economics remain single-source CLAIMED. That is S4.5's Model C ruling,
still the owner's to take.

---

## What did not move

- **`judge()` untouched**; every S1 standing stands.
- **No dilution word anywhere** — a test forbids *dilution*, *dilutive*,
  *attractive*, *favourable*, *adverse*, *tokenomics* and
  *supply pressure* in the layer.
- **Nothing consumes it**: the import-graph guard covers the supply
  modules across thirteen reasoning paths.
- **Equity untouched**, checked on identifiers rather than on prose.
- **The Assistance Fund's two roles stay apart**, by test.
- The crypto quality bands are asserted at their current values.

1760 tests, ruff, mypy and `npm run build` green.
