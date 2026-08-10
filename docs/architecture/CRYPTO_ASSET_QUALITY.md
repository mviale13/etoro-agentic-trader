# Crypto Asset Quality (S5)

**Status: accepted, built, and consumed.** Replaces the four-factor crypto
quality signal outright. Measured against the eight-asset corpus and, where
eight was too few, against CoinGecko's 250 largest assets read on 2026-08-10.
Built as `77ef4d8`; merged 2026-08-10 as
[PR #103](https://github.com/mviale13/etoro-agentic-trader/pull/103),
squash `4cb9516`.

> **Provenance.** That squash is larger than this slice. S3, S4, S4.5 and
> S4.6 had been merged only into a local `main` and never pushed, so the
> squash of PR #103 carried all five slices to GitHub at once. Their own
> merge commits name pull requests `#103`–`#106` that never existed; the
> real numbering stops at `#102`, and GitHub then assigned `#103` to this
> slice. The per-slice history is preserved on the
> `history/crypto-s3-to-s4.6` branch. An identifier that looks plausible
> is not evidence that the event happened — the same rule the evidence
> layers live by, applied to the repository.

---

## What the score means

> **How strong is this economic object on durable, asset-specific
> characteristics — independent of today's market mood, and independent of
> whether it currently looks cheap?**

What it does not answer, each parked somewhere else:

| Question | Where it belongs |
|---|---|
| Is it going up? Is crypto risk-on? | S4 market context, and a future regime model |
| Is it attractively valued? | A crypto valuation model that does not exist |
| Should it be bought now? | The Artificial CIO |
| How much evidence does MOVRvest hold? | Coverage and confidence, reported beside it |
| How long has it existed? | A future Evidence Maturity / Resilience layer |

---

## The four vocabularies

S3 kept three apart. S5 adds the fourth and keeps all four apart, because
collapsing any two is how a dashboard starts lying.

```text
applicability  ← the archetype alone.  Does the question apply at all?
readiness      ← the question alone.   Can the evidence contract carry a
                                        score, for anyone?
standing       ← the evidence.         Can this asset's figure be trusted?
verdict        ← only where all three allow it.
```

**Readiness takes no symbol and no figure.** `readiness_for(question)` has
one parameter, guarded by a test. A function that could see an asset would
let a well-covered one make a question scorable that stays unscorable
everywhere else, and *this platform cannot judge this yet* would quietly
become *this asset does badly here*.

The four states the ruling asked for come out of `applicability × readiness`:

| Participation | Meaning |
|---|---|
| `SCORED` | Applies, scorable, answered from established evidence |
| `SCORABLE_UNANSWERED` | Applies and is scorable; this asset's evidence does not reach the standing |
| `SHOWN` | Applies; evidence is displayed with its standing and counted by nothing |
| `UNANSWERABLE` | Applies; nothing answers it. An acquisition demand |
| `OUTSIDE` | Applies; its answer is not part of quality. Only a ruling moves it |
| `NOT_APPLICABLE` | The wrong question for this kind of asset |
| `UNDETERMINED` | No archetype established, so applicability is unknown |

`OUTSIDE` exists because `NOT_READY` promises a future score. Evidence
maturity must never earn one, and saying so needed its own word.

---

## The question model

Nineteen questions. **One is scorable.** That number is the finding, not a
gap in the module.

| Question | Readiness | Why |
|---|---|---|
| Market robustness | **SCORABLE_NOW** | Market capitalisation reaches ESTABLISHED for 6 of 8 |
| Supply and dilution | VISIBLE_NOT_SCORED | Emitted supply corroborates for 1 of 8 |
| Monetary scarcity | VISIBLE_NOT_SCORED | A three-part question with one part evidenced |
| Economic activity | VISIBLE_NOT_SCORED | Fees held for 6 of 8, every one single-source |
| Capital committed | VISIBLE_NOT_SCORED | TVL held for 7 of 8, one provider's aggregate |
| Venue activity | VISIBLE_NOT_SCORED | Book and open interest read, single-source |
| Protocol value capture | VISIBLE_NOT_SCORED | Retained share read, single-source |
| Token-holder value accrual | VISIBLE_NOT_SCORED | Mechanism settled, amount claimed |
| Evidence maturity | **OUTSIDE_ASSET_QUALITY** | A property of the observation, not the asset |
| Liquidity | NOT_READY | The inherited measure is refuted (below) |
| Usage, monetary adoption, network security, decentralisation, ecosystem adoption, settlement dependency, operator economics, competitive position, token economic rights | NOT_READY | Unbound demands — the acquisition roadmap |

---

## The one rule

`market-significance-floor@1`, on the established market capitalisation.

| Band | Floor | Points | What clearing it means |
|---|---|---|---|
| robust | $10bn | 2 | markets deep enough that no single venue or holder defines the price |
| adequate | $500m | 1 | several independent markets, and a large holder still matters |
| fragile | — | 0 | one venue's withdrawal is a material part of the market |

**Measured basis.** CoinGecko's 250 largest, 2026-08-10: the page spans
$115m to $1,307bn, median $307m. $10bn is its 95th percentile (measured
$8.998bn at rank 13) and 11 of 250 clear it; $500m is cleared by 99 of 250.
Both sit in sparse parts of a heavily skewed distribution, which is why the
rule holds still — **a uniform 30% market fall re-bands 18 of 250 assets
(7.2%), a 50% fall 35 (14.0%)**. That is the answer to the objection that
market capitalisation moves every morning: a *level* under a floor test does
not, and no *change* appears anywhere in the model.

The inherited thresholds were $10bn and $1bn. The upper survives the
measurement; the lower does not, because $1bn calls 74% of the 250 largest
assets fragile and *extremely small* is the fragility the question is about.

The question saturates deliberately. Bitcoin at $1,307bn is not twenty-nine
times sounder than Solana at $45bn, and a rule that scored it that way would
be reporting size as quality.

---

## Three measurements that decided the design

### 1. Volume over market capitalisation is not a liquidity measure

Over the 250 largest assets, turnover ranks **Bitcoin 158th of 233 and 1inch
52nd** — while Bitcoin trades $14.8bn a day and 1inch $7m. A 2,100-fold
difference in what could actually be sold, inverted into a quality point. The
top of the turnover list is meme and stablecoin rotation: CYS 46.7% ($193m
cap), KAITO 21.9%, FDUSD 19.7%, WIF 15.4%.

Absolute volume is honest and vendor-scoped, so it never establishes.
Order-book depth is not acquired. **Liquidity is NOT_READY**, and the
question stays open rather than being answered by something else.

### 2. A vendor's `total_supply` is the protocol maximum for most capped assets

CoinGecko reports `total_supply` exactly equal to `max_supply` for **83 of
the 145 capped assets** in the 250 largest. Where a chain reading exists to
test it, it was wrong twice in three:

| Asset | Vendor "total" | Chain | Real emitted share |
|---|---|---|---|
| ADA | 45,000,000,000 | 38,803,572,882 | 86.2%, not 100% |
| TAO | 21,000,000 | 11,218,159 | 53.4%, not 100% |
| ARB | 10,000,000,000 | 9,999,998,978 | 100% — confirmed |

So the vendor field cannot stand in for emitted supply, and a chain reading
is a single source.

### 3. Two sources agreeing to the last bit are one source

TokenInsight's Cardano circulating figure is `38803572882.17353` and the
Cardano ledger's own `supply` is `38803572882.17353` — **bit-identical
IEEE-754 doubles**. Independent measurement of a continuous quantity does not
produce that. TokenInsight is republishing the ledger, so it cannot
corroborate it.

The distinction matters and is not universal: `max_supply` agreeing exactly
across vendors (21,000,000; 1,500,000,000) is a *declared protocol constant*
and the expected shape. Exact agreement is replication only for a **measured**
quantity. S1's rule gains a sibling: agreement inside one provider is not
corroboration, and neither is identity to the last digit across two.

---

## What is shown and never scored

`VISIBLE_NOT_SCORED` is the ruling's acceptance case, and Hyperliquid is why.
Every line carries its standing — that is the whole permission structure: a
claim may be shown *because* it is labelled a claim, and the moment the label
came off it would have to be scored or hidden.

```
Token-holder value accrual
  The share of fees that reaches holders: $534,851 — DefiLlama, provider claim.
  DefiLlama defines it: 99% of fees go to Assistance Fund for buying HYPE
  tokens… (provider claim).
```

The question applies, the mechanism is settled, the amount is a claim. A
platform that showed only the first would look ignorant; one that scored the
third would be wrong.

The emitted share is reported as **the emitted share of a protocol maximum**,
never as dilution. The ratio says how much of a cap has been issued; what the
rest arriving does to a holder depends on when it arrives and to whom, and
neither is read. Where no schedule is held the model says so, in the place a
schedule would have gone.

---

## The headline and its quorum

`MINIMUM_SCORED = 2`, inherited unchanged from the factor quorum the crypto
signal already enforced and from `MINIMUM_ANSWERED` on the company side. One
question is scorable, so **no crypto asset carries a quality band today.**

The reason is stated as a fact about the platform, never about the asset:

> No quality band is emitted. Of the 9 questions this asset is asked, 1 can be
> scored at all, and a band requires 2. That is a statement about this
> platform's evidence, not about the asset.

Score is over what was *answered*; coverage is reported beside it. Missing
evidence never becomes negative evidence — an unanswered question is absent
from the denominator, so nothing was available to have been lost.

**Confidence is computed from coverage alone.** No band, no figure and no
verdict enters it, guarded by a test over the function's own AST. Its
denominator is everything *in scope*, including questions an unestablished
archetype left undetermined — measured before that was so, Bittensor came out
the best-covered security in the corpus because four questions were asked of
it instead of nineteen. Not knowing what an asset is is not a form of knowing
about it.

---

## Retired

| Factor | Verdict | Replaced by |
|---|---|---|
| Scale ($10bn / $1bn on a provider field) | Rebuilt | Market robustness, established input only, floor re-measured |
| Liquidity (24h volume / market cap) | **Retired** | Nothing. The question is NOT_READY |
| Issuance (`circulating_supply` / `max_supply`) | **Retired** | Supply structure, on named S4.6 concepts, shown not scored |
| Age (years traded) | **Retired** | Nothing. A future Evidence Maturity layer |

`CryptoQualitySignalService` is deleted. The equity path
(`QualitySignalService`) is untouched — asset-class applicability carries the
difference, and a test asserts the company signal knows nothing about any of
this.

`CompanyFacts.circulating_supply` is not read by the model and is not
repaired. Equities keep it.

---

## Boundaries, held structurally

- **No market context.** The model cannot reach `crypto_market`, a peer
  group, a relative return, breadth, dominance, sentiment or a regime. An
  asset's quality must not change because the market moved this morning.
- **No valuation.** Fully-diluted valuation, capitalisation over revenue and
  capitalisation over capital committed are all computable from facts the
  platform holds, and all answer *what price am I paying*. None is reachable.
- **No third-party rating.** The model joins the list of things that may not
  import TokenInsight's grade.
- **No authority-as-standing.** A rule gates on `EvidenceStanding.ESTABLISHED`
  and never on `EvidenceAuthority`. Where a figure came from explains why a
  standing applies; a primary reading is not thereby scorable.
- **A page view acquires nothing.** `established()` reads the stores and
  stops, guarded by stubs that raise on any acquisition.

The S2, S3 and S4.6 import guards each said *S5 decides what these facts are
worth*. S5 decided, so each **narrowed to this one module** rather than
disappearing — and each gained a positive assertion in place of what it lost:
no protocol metric is scorable, applicability cannot be reached through a
score, and no supply figure earns a point.

---

## Corpus outcome, 2026-08-10

| Asset | Archetype | Old | New | Market robustness | Answered / scorable of in-scope | Confidence |
|---|---|---|---|---|---|---|
| BTC | Monetary network | MEDIUM 68 | UNKNOWN | robust ($1,308.7bn) | 1 / 1 of 9 | 19 |
| ETH | Smart-contract network | MEDIUM 62 | UNKNOWN | robust ($232.3bn) | 1 / 1 of 12 | 17 |
| SOL | Smart-contract network | **HIGH 74** | UNKNOWN | robust ($44.7bn) | 1 / 1 of 12 | 17 |
| ADA | Smart-contract network | MEDIUM 62 | UNKNOWN | adequate ($7.7bn) | 1 / 1 of 12 | 17 |
| TAO | *unclassified* | UNKNOWN 20 | UNKNOWN | adequate ($1.8bn) | 1 / 1 of 19 | 14 |
| 1INCH | Application protocol | MEDIUM 68 | UNKNOWN | fragile ($119m) | 1 / 1 of 9 | 19 |
| ARB | Scaling network | UNKNOWN 20 | UNKNOWN | *conflicted* | 0 / 1 of 14 | 10 |
| HYPE | Exchange network | UNKNOWN 20 | UNKNOWN | *conflicted* | 0 / 1 of 15 | 10 |

SOL's HIGH was two provider readings — market capitalisation and a turnover
ratio — and no third. Bitcoin's MEDIUM rested partly on being ranked *less
liquid* than 1inch. Neither survives its own measurement.

---

## Consequence the owner should rule on

`quality_score is None` routes a security to `DecisionState.INVESTIGATE`. No
decision threshold changed and no rule was touched, but with every crypto
asset at UNKNOWN, **the whole asset class stops at research again** — the
state the four-factor signal was built to escape.

That is a true report of what the evidence supports, and whether the platform
should prefer an honest silence to a two-factor band is the owner's call, not
this slice's.

## Parked, explicitly

- **Crypto valuation** — `market_cap / holder_revenue`, `FDV / revenue`,
  `market_cap / TVL`. Interesting, and a different question.
- **Market regime and timing** — S4 acquires the ingredients and classifies
  nothing.
- **Positioning and derivatives** — open interest is read and unscored.
- **Evidence Maturity / Resilience** — *how much real-world evidence stands
  behind this assessment*, never *old token, good token*.
- **Token unlock and supply pressure** — needs a schedule this platform does
  not read.
