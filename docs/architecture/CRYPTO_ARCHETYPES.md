# S3 — Crypto archetypes, applicability and investment questions

**Status: built 2026-08-10 (`0fbc7ee`, merged locally as `1054b9e`). No score, threshold, band or
decision rule changed. Every S1 conflict and every S2 claim stands
exactly as it did.**

The ruling's question, and the one this slice answers:

> Which investor questions legitimately apply to this economic object,
> and what evidence would answer them?

What follows is the S3 report — the archetype result, the question
matrix, the mechanism map, the evidence coverage, and the four
recommendations the ruling asked to be returned before S4.

> **Provenance.** This slice reached GitHub only on 2026-08-10, inside the squash commit [`4cb9516`](https://github.com/mviale13/etoro-agentic-trader/commit/4cb9516) that merged [PR #103](https://github.com/mviale13/etoro-agentic-trader/pull/103). Its own merge commit carries a `(#NNN)` suffix that matches no pull request: the number was written by hand and never existed. The per-slice history is preserved on the `history/crypto-s3-to-s4.6` branch; the commit hashes above are the authority, not the suffix.


---

## The finding, in one table

The same figure, from the same provider, on the same day:

| | fees/day | what the source says happens to them | what that is evidence *about* |
|---|---|---|---|
| **Bitcoin** | $139,032 | *"Gas fees paid by users"* — and the source defines **no holder mechanism at all** | the network's **security budget**. Not revenue |
| **Ethereum** | $175,154 | *"Amount of ETH burned — base fees plus blob fees"* | **value accrual by supply reduction** |
| **Hyperliquid** | $842,720 | *"99% of fees go to Assistance Fund for buying HYPE tokens"* | **value accrual by buyback**, and the source names the token |

Three fee figures within a factor of 6, meaning three unrelated things.
A model that scored them on one scale would rank a cost of defence
against a buyback. **That is what applicability is for**, and it is why
S5 could not have come first.

---

## A. Archetype result

Eight securities, six archetypes used, one deliberate `UNKNOWN`.

| security | archetype | confidence | grounded on | alternative considered | capabilities it composes |
|---|---|---|---|---|---|
| **BTC** | Monetary network | Structural | one **chain** entity; capped supply 21m at 95.6% issued, established across three sources; the source defines fees and protocol revenue and **defines no holder mechanism** | Smart-contract network — rejected: its $3.56bn of on-chain capital is 0.3% of market value, and a monetary case does not rest on what is built on the chain | market asset, monetary network |
| **ETH** | Smart-contract network | Structural | one **chain**; complete fee family defined; *"Amount of ETH burned"* names the asset; $41.99bn capital committed | Monetary network — rejected: **no stated maximum supply**, so the scarcity question cannot even be asked of it | market asset, smart-contract network, token value capture |
| **SOL** | Smart-contract network | Structural | one **chain**; complete fee family; *"Transaction base fees paid by users were burned"*; $4.86bn committed | Monetary network — rejected: no cap, and a fee economy an order of magnitude above Bitcoin's | as ETH |
| **ADA** | Smart-contract network | Structural | one **chain**; fees + protocol revenue defined; $70.4m committed; 45bn cap at 86.2% issued | Monetary network — rejected: a cap is its only monetary signal, and a chain is read on what it does | as ETH |
| **ARB** | Scaling network | **Reasoned** | one **chain**; S2 records that its gas is paid **in ETH** and flags the mapping unsettled for that reason; no holder mechanism defined | Smart-contract network — rejected: it *is* one and not only one; dropping the settlement and operator questions drops where its token's case is decided | market asset, smart-contract network, **scaling infrastructure**, token value capture |
| **HYPE** | Exchange network | Structural | **two** entities, a venue and a chain, 224× apart on fees; the venue publishes DEX volume and open interest, which only a book has; its fee methodology **names the token** | Application protocol — rejected: drops the chain ($1.20bn). Smart-contract network — rejected: drops the venue, where 99.6% of fees are earned | market asset, smart-contract network, **venue economics**, protocol economics, token value capture |
| **1INCH** | Application protocol | Structural | one **protocol** entity; S2 declined TVL, DEX volume and open interest with stated reasons; fees reported with **no methodology at all** | Exchange network — rejected: the provider's DEX list holds *1inch Aqua*, a different product, and a shared name is not an identity | market asset, protocol economics, token value capture |
| **TAO** | **Not classified** | Unestablished | one **chain**, mapping flagged unsettled by S2; the source defines **capital held and nothing else** — no fee methodology, so its silence about fees is a gap rather than a finding; 21m cap at 41.2% issued, sources 11.3% apart | Smart-contract network — rejected: no fee evidence and $45.0m of capital. Monetary network — rejected: a cap alone would classify every capped token as money | market asset only |

**TAO is the acceptance case for criterion 1.** A vendor category would
classify it instantly. This platform holds no category field for it at
all, holds TokenInsight's grade and six dimension labels for it, and
uses none of them — the refusal is printed on the dossier under *"Held
here and not used to classify"*. `UNKNOWN` is the honest answer, and the
15 questions it leaves **undetermined** are a statement about what has
been read here, never about the asset.

Every assignment also carries a `does_not_establish` list, because a
kind is not a verdict: *"an exchange network"* does not mean a good one,
and HYPE's entry says in as many words that the mechanism is evidenced
and the judgment is not made.

---

## B. Investment-question matrix

19 questions × 8 securities. `ASK` = applies and something **established**
answers it; `ask?` = applies and nothing established answers it yet;
`n/a` = the wrong question for this kind of asset; `—` = no archetype, so
applicability is unknown.

| question | BTC | ETH | SOL | ADA | ARB | HYPE | 1INCH | TAO |
|---|---|---|---|---|---|---|---|---|
| Market robustness | ASK | ASK | ASK | ASK | ask? | ask? | ASK | ASK |
| Liquidity | ask? | ask? | ask? | ask? | ask? | ask? | ask? | ask? |
| Supply and dilution | ASK | ASK | ASK | ASK | ASK | ASK | ASK | ASK |
| Evidence maturity | ask? | ask? | ask? | ask? | ask? | ask? | ask? | ask? |
| Monetary scarcity | **ASK** | n/a | n/a | n/a | n/a | n/a | n/a | — |
| Monetary adoption | ask? | n/a | n/a | n/a | n/a | n/a | n/a | — |
| Network security | ask? | ask? | ask? | ask? | ask? | ask? | n/a | — |
| Decentralisation | ask? | ask? | ask? | ask? | ask? | ask? | n/a | — |
| Usage | ask? | ask? | ask? | ask? | ask? | ask? | ask? | — |
| Economic activity | **n/a** | ask? | ask? | ask? | ask? | ask? | ask? | — |
| Capital committed | n/a | ask? | ask? | ask? | ask? | ask? | n/a | — |
| Ecosystem adoption | n/a | ask? | ask? | ask? | ask? | ask? | n/a | — |
| Settlement dependency | n/a | n/a | n/a | n/a | **ask?** | n/a | n/a | — |
| Operator economics | n/a | n/a | n/a | n/a | **ask?** | n/a | n/a | — |
| Venue activity | n/a | n/a | n/a | n/a | n/a | **ask?** | **n/a** | — |
| Competitive position | n/a | n/a | n/a | n/a | n/a | ask? | n/a | — |
| Protocol value capture | **n/a** | n/a | n/a | n/a | n/a | ask? | ask? | — |
| **Token-holder value accrual** | **n/a** | ask? | ask? | ask? | ask? | **ask?** | ask? | — |
| Token economic rights | n/a | ask? | ask? | ask? | ask? | ask? | ask? | — |

Every cell carries its reason. The three that matter most:

- **BTC / token-holder value accrual = n/a.** *"A monetary asset's
  return is not a distribution, and asking whether one arrives would
  mark it down for being what it is. This is the same error as judging a
  bank on the industrial leverage threshold: the answer would be
  none, the number would be real, and the question would be the wrong
  instrument."*
- **HYPE / token-holder value accrual = ask?** — applies, and the
  evidence is a single provider's uncorroborated claim. Applying and
  being answerable are different states and are shown as different
  states.
- **1INCH / venue activity = n/a**, worded so the Aqua trap cannot
  reopen: *"the provider's DEX list does hold a similarly-named product;
  reading that as this protocol's activity would attribute another
  business's volume on the strength of a shared name."*

**A declined question carries no evidence at all** — not in the API, not
in the domain. The service never gathers figures for a refused question,
so nothing downstream can ever read *"Bitcoin's economic activity:
$139.0k/day"* off a question this platform holds to be the wrong one.

---

## C. Mechanism map — why "fees" cannot be scored identically

`usage → fees → protocol capture → holder accrual`, one chain per
economic entity and never one per security. Every mechanism is
**recognised from the provider's own wording**, never declared here; the
sentence is the evidence and the label is a convenience over it.

### BTC — Bitcoin (chain) → `no mechanism here`

```
usage              not available free   (no source publishes chain transaction activity)
fees                       $139,032/d   "Gas fees paid by users"
protocol capture   not available free
holder accrual       NOT APPLICABLE     the source defines the rest of the family and defines no
                                        holder mechanism — under S2's sibling rule that is evidence
                                        there is none, not a figure missing today
```

The fee figure exists, and it is **not revenue**. It answers *network
security* — one half of what the network's defence is paid with. What it
does **not** establish, and the demand says so on the page: *"who
receives those payments; the source records what users pay and not where
it goes."* The platform declines to assert the miners from its own
knowledge.

### ETH — Ethereum (chain) → `burned`

```
usage              not available free
fees                       $175,154/d   "Total ETH gas fees (base fees + priority fees) plus blob
                                         fees … paid by users"
protocol capture            $32,159/d   "Amount of ETH burned — base fees plus blob fees (both are
                                         permanently burned, accruing to no proposer)"
holder accrual              $32,159/d   "Amount of ETH burned — base fees plus blob fees"
```

The identical figure appears at two stages and means two things, which
the source's own wording separates. **Protocol capture is declined for a
smart-contract network** — *"a chain has no treasury that retains what
its users pay; where fees are removed from supply instead, nothing is
retained by anyone, and the removal is read at the accrual question."*
The burn is accrual, not retention.

### HYPE — two entities, read apart

```
Hyperliquid (venue)                       →  buys the token
usage                   $38,730,237/d    "Include spot trading fees and unit protocol fees…"
fees                       $842,720/d    "Hyperliquid Perps: Include perps trading fees…"
protocol capture           $534,851/d    "…99% of fees go to Assistance Fund for buying HYPE
                                           tokens…  Hyperliquid HLP: No revenue."
holder accrual             $534,851/d    "…99% of fees go to Assistance Fund for buying HYPE
                                           tokens…  Hyperliquid HLP: Fees going to governance
                                           token holders"

Hyperliquid L1 (chain)                    →  mechanism not recorded
fees                         $3,769/d    "Gas fees paid by users"
protocol capture             $3,769/d    "Burned coins"
holder accrual               $3,769/d    (no methodology published)
```

**S3 establishes that the accrual question applies to HYPE and that a
mechanism is documented. It concludes nothing about whether the accrual
is strong.** The dossier says so where the classification is made.

The recogniser's ordering is load-bearing and tested: Hyperliquid's
sentence contains *both* "buying HYPE tokens" and "going to governance
token holders", and the buyback clause covers 99% of the fees and names
the asset, so it is recognised first. The full sentence is shown either
way.

### The rest, and one provider inconsistency worth recording

| security | entity | mechanism | why |
|---|---|---|---|
| SOL | Solana (chain) | **burned** | *"Transaction base fees paid by users were burned"* |
| ADA | Cardano (chain) | **no mechanism here** | fees + protocol revenue defined (*"Burned coins"*), **holder revenue not defined** |
| ARB | Arbitrum (chain) | **no mechanism here** | same shape; and S2 records the gas is paid **in ETH**, so burning another network's asset is not accrual to this one |
| 1INCH | 1inch (protocol) | **nothing read** | figures published with **no methodology**, so the amount is known and its meaning is not |
| TAO | Bittensor (chain) | **nothing read** | only capital is published |

**The inconsistency:** DefiLlama labels a burn as *holder revenue* for
Ethereum and Solana and does **not** for Cardano and Arbitrum, while
recording *"Burned coins"* as protocol revenue for both. ADA's accrual
question therefore stands open **on a provider inconsistency, not on a
property of the chain** — which is stated in ADA's assignment rather
than smoothed over. It is a candidate for the second protocol source to
resolve.

---

## D. Evidence coverage

Over the questions that apply to each security:

| | asked | established | claimed | conflicted | absent | declined | undetermined |
|---|---|---|---|---|---|---|---|
| **BTC** | 9 | 3 | 2 | 0 | 4 | 10 | 0 |
| **ETH** | 12 | 2 | 5 | 0 | 5 | 7 | 0 |
| **SOL** | 12 | 2 | 5 | 0 | 5 | 7 | 0 |
| **ADA** | 12 | 2 | 4 | 1 | 6 | 7 | 0 |
| **ARB** | 14 | 1 | 5 | 2 | 8 | 5 | 0 |
| **HYPE** | 15 | 1 | 9 | 2 | 5 | 4 | 0 |
| **1INCH** | 9 | 2 | 3 | 0 | 4 | 10 | 0 |
| **TAO** | 4 | 2 | 1 | 1 | 1 | 0 | **15** |

Four readings of this table:

1. **Only the market questions establish.** Every economic question in
   the corpus rests on a single uncorroborated provider — which is S2's
   standing rule applied uniformly, not a new limitation. Criterion 9
   holds by test: no protocol figure reaches `ESTABLISHED` through this
   layer.
2. **Liquidity establishes for nobody**, and this was a surprise worth
   recording. Volume is vendor-scoped by S1's own rule — TokenInsight's
   spot aggregate and CoinGecko's market aggregate measure different
   universes and are never pooled — so *"could a position be left?"* is
   asked of all eight and answered from claims in all eight.
3. **HYPE is the best-evidenced token in the corpus and its case is
   still not answerable** — 9 claims, 1 established, 2 conflicts. That is
   the honest state, and it is far more informative than the LOW band the
   factor table currently produces.
4. **ARB has the most absent evidence of any classified asset** (8 of
   14), which follows from its archetype rather than from bad luck: the
   settlement and operator questions its kind demands have no free
   source at all.

The **acquisition roadmap** falls straight out of the unmet demands,
counted across the corpus:

| demanded by | unmet | what it would unlock |
|---|---|---|
| Evidence maturity ×4 demands | 8 assets each | observed history, drawdowns, recovery, incidents — see F |
| Liquidity: order-book depth | 8 | the one question every asset asks and none answers |
| Supply: vesting/unlock schedule | 8 | turns dilution from a ratio into a timetable |
| Usage: transactions, distinct users | 7 | the *first* of the four questions, currently unevidenced for every chain |
| Network security ×3 | 6 | issuance to block producers, who receives fees, cost to attack |
| Decentralisation ×3 | 6 | entirely unread today |

None of it is acquired in S3. Naming it is the deliverable.

---

## E. Architecture recommendation — **hybrid, and the corpus forced it**

**Capability composition, with archetypes as names for capability sets.**
Not because it is elegant: because HYPE broke the alternative.

- **Simple archetypes are insufficient.** An exchange that runs its own
  chain needs the network questions *and* the venue questions. Written as
  one flat archetype, six questions would be duplicated from the
  smart-contract set, and the next combination would duplicate them
  again.
- **Capabilities alone are insufficient.** An investor is owed the
  sentence *"BTC is read as a monetary network"*, and a bare set of
  lenses does not say it.
- **The hybrid is what the equity side already does, plus one degree.**
  `PlaybookKind` → `FinancialModel` → `PlaybookQuestions` is exactly this
  shape with a **single-member** middle layer. JPMorgan is a bank or an
  industrial and never both; HYPE is a venue **and** a chain, and S2
  proved it with two entities. So the crypto middle layer is a *set*, and
  that is the only structural difference.

**It does not conflict with the existing playbook architecture — it
reuses it.** What carried over unchanged: the three-outcome discipline
(a statement about the question vs a statement about our evidence), the
`QuestionDecline` shape with its worded reason, `narrowed`'s lesson that
a permanent gap is noise, the demands-name-facts-never-verdicts rule,
and `EvidenceStanding` for the evidence half. What could not carry over
is `FinancialQuestion.interpreted_by`: it names the analyst that owns a
rule table, and **S3 has no analyst and no rule table by design**. That
absence is the ruling's "no scoring" boundary made structural.

Six capabilities, and each is earned — a test asserts that every one of
them asks at least one question no other asks:

```
MARKET_ASSET            every tradable token          (4 questions)
MONETARY_NETWORK        BTC                           (+4)
SMART_CONTRACT_NETWORK  ETH SOL ADA ARB HYPE          (+6)
SCALING_INFRASTRUCTURE  ARB                           (+2)
VENUE_ECONOMICS         HYPE                          (+2)
PROTOCOL_ECONOMICS      HYPE 1INCH                    (+3)
TOKEN_VALUE_CAPTURE     everything except BTC         (+2)
```

`SPECIALISED_NETWORK` was drafted for TAO and deleted: it would have
renamed an absence. The archetype count stayed at six because a seventh
would have changed no question.

**Falsifiable against S2.** Each capability declares the kind of entity
it needs, and a test asserts every corpus assignment is supported by its
mapped entities — a security read through the venue lens must have a
venue mapped to it. The archetype table cannot drift from the entity
table without failing.

---

## F. Evidence maturity / resilience — **outside Asset Quality**

The owner's preference is confirmed by the corpus, on three grounds.

1. **It would be a permanent zero, which is noise rather than a
   finding.** All four of its demands are unmet for all eight assets.
   The equity side already learned this from the bank's gross-margin
   gap — a measurement that can never arrive is not a dimension, it is
   a column of blanks.
2. **It measures this platform's evidence, not the asset.** Bitcoin's
   sixteen years are a fact about the world; what this platform has
   *observed* is a few weeks of market history. Scoring the first would
   be borrowing an authority nothing here earned — and that is precisely
   how the fabricated age field failed before PR #99 removed it.
3. **Calendar age is not resilience, and the question is built so it
   cannot become it.** `project_age` is deliberately not among its
   demands, and a test asserts it. What it demands is *observed
   behaviour*: history through a full cycle, drawdowns and what recovery
   followed, operating history, security incidents.

**Recommendation:** keep it as an **asked question** carrying its
acquisition demands — which is what S3 shipped — and, when it eventually
scores, make it a **qualifier on the whole reading** rather than a point
inside Asset Quality. "We are confident *about* this asset" and "this
asset is *good*" are different sentences, and a single number cannot say
both. The proposed home is beside the Evidence score the dossier already
carries, not inside quality.

**Not settled by this slice:** whether the price history the platform
already archives is deep enough to answer the drawdown demand. That is a
measurement, and it belongs with S4's market work rather than here.

---

## G. Recommended S4 boundary — `CryptoMarketSnapshot`

The boundary this slice preserved, and the one S4 must not cross:

```text
Asset / protocol understanding        Market environment
────────────────────────────────      ─────────────────────────────
what this thing IS                    what the market is DOING
archetype, applicability,             fear & greed, BTC dominance,
mechanism, evidence standing          trending, market-wide volume,
                                      category momentum, liquidations,
                                      funding regime
per security                          per market, or per security
                                      *relative to* the market
changes when the system changes       changes hourly
```

**Belongs in `CryptoMarketSnapshot`:** market-wide sentiment (the
fear & greed provider already exists and is unwired to this),
BTC dominance, aggregate market capitalisation and volume, category and
sector momentum, liquidation and funding-rate regime, trending lists.
Every one is a fact about the *environment*.

**Must not enter it:** anything in section B's matrix. No market-context
reading may change which questions a token is asked — HYPE's
value-accrual question applies in a bull market and a bear one, and a
fear index has no view on Bitcoin's issuance schedule.

**The one seam to be careful with:** volume and liquidity appear on both
sides. The token's own liquidity (section B) is evidence about the
asset; market-wide volume is environment. They must not be joined by
arithmetic — S1 already established that even *one* asset's volume is
vendor-scoped and must name its venue universe.

**S4 should also stay out of scoring**, on the same argument that
justified S3 before S5: what a market regime is *worth* to a decision is
S5's question.

---

## What did not move

Verified by test, not by assertion.

- **No score, threshold, band or decision rule changed.** The four
  crypto quality bands are asserted at their current values, so a slice
  that moves one has to do it deliberately.
- **Nothing consumes any of this.** An import-graph test over fifteen
  reasoning paths — analysts, the Brain, the committees, the Executive,
  the CIO, both quality services, the playbook selector, and the equity
  financial-question layer — forbids all four new modules. A slice that
  wants applicability inside a score argues with that test first.
- **Applicability never consults a figure.** `applicability_for` takes an
  archetype and a question; there is no parameter a value could arrive
  through. The whole layer is run against empty stores and every
  applicability is byte-identical, and no question anywhere becomes
  inapplicable for want of data.
- **Equity playbooks are untouched.** `financial_question.py` contains no
  reference to crypto; `playbook.py` knows nothing of archetypes.
- **The supply conflicts survive.** HYPE's supply question reads
  answerable on an established cap while its circulating count stays
  CONFLICTED, and the conflict is shown beside the answer rather than
  absorbed into it.
- **No S2 claim was promoted.** Every protocol figure remains a single
  provider's dated, attributed claim.

1687 tests, ruff, mypy and `npm run build` green. HYPE, BTC, TAO, 1INCH
and AAPL dossiers verified in the browser — the last of them to confirm
an equity is sent no crypto section at all, rather than an empty one.

---

## Where it is visible

- `movrvest crypto-playbook SYMBOL` — one security in full.
- `movrvest crypto-playbook` — the corpus matrix and the evidence
  counts above, which is the roadmap view.
- The token dossier, section **"Which questions this asset is asked"** —
  the archetype and its basis, the questions with their evidence, the
  declines with their reasons, and each entity's value chain.

## Open, and deliberately not closed here

- **A second protocol source** would let economic figures establish
  rather than claim, and would settle the ADA/ARB labelling
  inconsistency in §C.
- **The supply-drift measurement** (S2 §5) continues to accumulate dated
  claims. S3 forced no polling and resolved nothing.
- **Whether a primary computation over public chain data is a different
  epistemic class** from a secondary market aggregate — still the
  owner's ruling to make, still not taken unilaterally.
