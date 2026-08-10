# S2 — Protocol fundamentals: the economics behind a token

**Status: built and merged, 2026-08-10. No score, threshold, band or
decision rule changed. Every S1 conflict stands untouched.**

The second canonical evidence family. What follows is the S2 report the
ruling asked for: the corpus, the HYPE deep read, the entity-mapping
report, the circulating-supply investigation, the architecture
verification, and a recommendation on what comes next.

---

## 1. The entity finding — the one that justifies the whole discipline

DefiLlama publishes two entities under the name *Hyperliquid*:

| | fees / day | TVL |
|---|---|---|
| **Hyperliquid** — the venue (`parent#hyperliquid`: perps + spot + HLP) | **$842,720** | **$6.26bn** |
| **Hyperliquid L1** — the chain it settles on | **$3,769** | **$1.20bn** |

**224× apart on fees, 5.2× on capital.** Same name, same token, same
provider. Reading either as "HYPE's economics" without saying which is
a misstatement by two orders of magnitude — and PR #100's own report
quoted the *chain's* $1.21bn TVL as HYPE's, which this slice corrects.

So a security maps to named entities; each states what it measures and
why it is attached; each fact names its entity. HYPE has two, shown
apart. Nothing collapses them.

A second, smaller instance of the same trap: 1inch's DEX volume. The
provider's DEX list holds *1inch Aqua*, a different product. Rather
than map the aggregator to another business's book, DEX volume is
**declined** for 1inch — an aggregator routes trades and runs no book,
so the question is not thin evidence about it, it is not a question
about it.

---

## 2. Protocol fundamentals corpus

Nine entities across eight securities. `✓` available, `n/a` not
applicable, `—` not available free. Every value is a **provider claim**
(see §6), dated, attributed, and consumed by nothing.

| security | entity | kind | TVL | fees/day | protocol rev | holder rev | DEX vol | OI |
|---|---|---|---|---|---|---|---|---|
| HYPE | Hyperliquid | protocol | $6.26bn | $842.7k | $534.9k | $534.9k | $38.7m | $10.87bn |
| HYPE | Hyperliquid L1 | chain | $1.20bn | $3.8k | $3.8k | $3.8k | n/a | n/a |
| ETH | Ethereum | chain | $41.99bn | $175.2k | $32.2k | $32.2k | n/a | n/a |
| SOL | Solana | chain | $4.86bn | $650.7k | $59.3k | $59.3k | n/a | n/a |
| BTC | Bitcoin | chain | $3.56bn | $139.0k | — | **n/a** | n/a | n/a |
| ARB | Arbitrum | chain | $1.20bn | $6.9k | $6.8k | — | n/a | n/a |
| ADA | Cardano | chain | $70.4m | $782 | $156 | — | n/a | n/a |
| TAO | Bittensor | chain | $45.0m | — | — | — | n/a | n/a |
| 1INCH | 1inch | protocol | **n/a** | $1.8k | $329 | — | **n/a** | **n/a** |

**Trends available free** (acquired, not yet surfaced): `change_1d` per
metric; the provider also publishes 7d/30d/1y totals and its own
`annualized1y`, which is *provider*-derived and would be carried as
such, never as MOVRvest arithmetic.

**Unresolved semantics, recorded:** the provider's cumulative fields
for open interest (`total1y` = a sum of daily levels) are meaningless
and are not read — only the level and its changes. Bitcoin's
`annualized1y` ≠ its `total1y`, so that field is a provider derivation
rather than a sum, wherever it is eventually used.

**Coverage is not a score.** BTC shows four of six as inapplicable or
unavailable and is *not* incomplete: a chain has no order book, and the
provider's own methodology for Bitcoin defines fees and revenue and
says nothing about holder revenue — evidence that the mechanism does
not exist, not that a figure is missing.

---

## 3. HYPE deep read

**What the entity is:** `parent#hyperliquid`, an aggregate of three
child protocols — Hyperliquid Perps ($815.3k/day fees), Hyperliquid
Spot Orderbook ($22.1k), Hyperliquid HLP ($5.4k). The children sum to
the parent exactly (815,257 + 22,060 + 5,403 = **842,720** ✓), which is
a checkable relation, not a coincidence. It is *not* the chain.

**The figures** (DefiLlama, 24-hour windows unless stated):

- TVL **$6.26bn** — level
- Fees **$842.7k**, change +35.0% on the day
- Protocol revenue **$534.9k**
- Holder revenue **$534.9k** — identical to protocol revenue
- Spot DEX volume **$38.7m**
- Open interest **$10.87bn** — level

**The mechanism, in the source's own words** (carried verbatim, because
this sentence *is* the value-accrual evidence):

> Hyperliquid Perps: 99% of fees go to Assistance Fund for buying HYPE
> tokens, excluding builders fees. Hyperliquid Spot Orderbook: 99% of
> fees go to Assistance Fund for buying HYPE tokens, excluding unit
> protocol fees. Hyperliquid HLP: No revenue.

And on protocol retention: *"Protocol doesn't keep any fees."*

**Derived arithmetic: none today.** A run rate over $534.9k/day would
be ~$195m/year — the figure PR #100 flagged — and this platform does
**not** compute it, because `annualise` refuses anything that is not
established, and with one protocol source nothing is. When a second
source corroborates, the figure appears labelled *"MOVRvest's
arithmetic over one observation"* with the caveat *"a run rate is what
one day implies if it repeats. It is not a year that happened"*
attached wherever it is shown.

**Caveats recorded:** holder revenue equalling protocol revenue is the
provider's model of a buyback, not a distribution — the tokens are
bought, not paid out, and what that is worth to a holder is an
interpretation nobody is authorised to make yet. The perps *volume*
that generates most of these fees is behind the provider's paywall;
only its open interest is free.

---

## 4. Entity mapping report

| security | entity | mapping | confidence |
|---|---|---|---|
| ETH, SOL, ADA, BTC | the chain | native gas/staking asset | **straightforward** |
| HYPE | Hyperliquid (venue) | the venue's own fee methodology *names the token* — the source states the link | **straightforward, source-stated** |
| HYPE | Hyperliquid L1 (chain) | native asset of the chain | **straightforward, and separate** |
| 1INCH | 1inch (protocol) | governance token with a recorded fee split | **straightforward** |
| **ARB** | Arbitrum (chain) | governance token — **but the chain's gas is paid in ETH**, so its fees are not revenue to ARB holders by any mechanism the provider records | **ambiguous — flagged `mapping_settled=False`** |
| **TAO** | Bittensor (chain) | native asset — but whether on-chain capital is meaningful evidence for a network of this kind is an archetype question | **ambiguous — flagged `mapping_settled=False`** |

An ambiguous mapping is acquired and shown with its caveat rendered in
amber; nothing may reason from it as though the economic link were
established. A security with no mapped entity (any token outside the
table) measures nothing and says so — a shared name does not establish
an economic system.

---

## 5. Circulating-supply methodology investigation

Provider values, same day:

| | TokenInsight | CoinGecko | Yahoo | max | pattern |
|---|---|---|---|---|---|
| **HYPE** | 336,685,219 | 222,445,714 | 1,500,000,000 | 1bn | TI/CG **51% apart**, both live; CG also reports total supply 955.3m ≠ max 1bn |
| **ARB** | 1,275,000,000 | 6,614,056,381 | — | 10bn | TI is a **round number** — the documented initial float |
| **ADA** | 38,803,572,882 | 37,353,519,634 | 36,550,320,128 | 45bn | three sources, three counts, all within 6% |
| **TAO** | 8,644,817 | 9,597,491 | — | 21m | 11% apart, TI consistently lower on an emitting asset |

**What the evidence supports today:**

- **ARB — stale, not methodological.** TokenInsight's figure is exactly
  1,275,000,000: a round launch-float number, not a measurement that
  moved. High confidence.
- **HYPE — methodological.** Both sources are live and internally
  coherent, and the gap (114.2m) is far too large and too stable to be
  timing. Which buckets count — foundation, assistance fund, unvested —
  is the question, and neither source publishes a per-token
  reconciliation through the free API.
- **ADA and TAO — unresolved.** Consistent with either slow updating or
  a definitional difference; the evidence does not choose.

**No methodology documentation was retrievable through the free API
surfaces** — neither provider exposes a per-token supply reconciliation
or definition endpoint. Anything more would be reading their published
documentation pages, which is a separate investigation.

**No rule is proposed, per the ruling.** But S1 handed us a decisive
and nearly free test: the stores now hold *dated* claims per source. A
stale figure does not move. Re-reading the same four tokens over a week
and diffing each source against itself separates staleness from
methodology **by measurement rather than by argument** — and needs no
new integration. That is the recommended first step of any supply
ruling.

Meanwhile the honest state holds: HYPE, ARB, ADA and TAO circulating
supply remain CONFLICTED, and the market values that depend on them
remain CONFLICTED for HYPE and ARB.

---

## 6. Why every protocol fact is a CLAIM, not ESTABLISHED

The ruling's §2 says a token's market cap may be CONFLICTED while its
protocol revenue is ESTABLISHED — and that independence is exactly what
the architecture delivers: the two families never block each other.

What the figures do *not* yet have is a second source. S1's rule —
**agreement inside one provider is not corroboration** — applies
uniformly, or "established" would mean two different things on one
page. So every protocol figure today is an attributed, dated CLAIM,
shown in full, consumed by nothing.

Three ways this could change, for the owner to rule on later:

1. a second protocol-data source joins the pool (the seam exists and is
   tested) and the two corroborate;
2. the owner rules that a primary computation over public chain data
   with published methodology is a different epistemic class from a
   secondary market aggregate — defensible, and a real decision rather
   than a default;
3. the provider's own children/parent sum (verified exact for HYPE)
   becomes a recognised internal check that can lift a figure.

I did not take any of the three unilaterally.

---

## 7. Architecture verification

- **Separate canonical family** — `protocol_fundamentals.py` and
  `protocol_entities.py`, sharing only the standing vocabulary
  (`EvidenceStanding`, now the platform's one definition of
  "established"; `TokenFactStanding` is an alias, so the S1 contract
  reads unchanged).
- **No provider types past the adapter** — enforced by test: neither
  canonical module may contain `app.providers` or `requests`.
- **A second protocol provider joins unchanged** — tested at the
  service seam with a source nobody wrote a line for.
- **No score, playbook, committee or the CIO can import any of it** —
  enforced by an import-graph test over thirteen reasoning paths, the
  same guard the third-party rating carries. A slice that wants
  protocol economics in a score has to argue with that test first.
- **Judged on read** — a rule improved later re-judges stored claims
  with no reacquisition.
- 1653 tests, ruff, mypy, `npm run build` green; HYPE and BTC dossiers
  verified in the browser.

Acquisition: ~30 keyless DefiLlama calls per cycle, reported in
`movrvest acquire` as its own line.

---

## 8. Recommended next slice

**S3 (archetypes) remains correct, and S2 strengthened the case for
it.** The corpus now shows the same metric meaning different things by
asset kind — Bitcoin's fees go to miners, Ethereum's are burned,
Hyperliquid's buy the token — and *that* distinction is applicability,
which is precisely what S3 formalises. Doing S5 first would mean
scoring facts whose relevance per archetype has not been decided.

Two smaller candidates the owner may want to sequence before S3:

- **The supply-drift measurement** (§5) — a week of dated re-reads,
  almost free, and it unblocks four CONFLICTED facts that currently
  suppress three quality verdicts.
- **A second protocol source**, which would let protocol facts
  establish rather than merely claim.

Both are optional; neither changes S3's correctness as the next
structural step.
