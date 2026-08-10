# Crypto Investment Intelligence — the measurement before the model

**Status: measured, 2026-08-10. No threshold, band, factor or decision
rule was changed. This document is the evidence for the next ruling,
not the ruling.**

Everything here was measured against the eight-token corpus (BTC, ETH,
SOL, ADA, ARB, 1INCH, HYPE, TAO) using the stores as they stand after
PR #99 and ~30 keyless free API calls (CoinGecko, DefiLlama; TokenInsight
re-read from the stored payloads at zero spend; CoinMarketCap **not**
probed — it requires a registered key this platform does not hold, and
no account was created for the measurement).

The contracts frozen by the owner all held through the measurement, and
one of them earned its escape clause: §9 records the one architectural
defect the measurement demonstrates, exactly of the kind the ruling
anticipated.

---

## 1. Corpus matrix — what produced each verdict

Factor anatomy after PR #99. Every input names its source and standing;
`·` is *not measured*, and the reason is beside it.

| | scale | liquidity | issuance | age | verdict |
|---|---|---|---|---|---|
| **BTC** | +1 — $1,308.7bn (TI, established, Yahoo-corroborated) | 0 — 0.96% turnover (Yahoo vol, sibling-corroborated) | +1 — 95.6% issued (TI, established) | · unmeasurable | **MEDIUM (68)** |
| **ETH** | +1 — $232.3bn (established, corroborated) | 0 — 1.73% | · no stated cap | · | **MEDIUM (62)** |
| **SOL** | +1 — $44.7bn (established, corroborated) | +1 — 2.54% | · no stated cap | · | **HIGH (74)** |
| **ADA** | 0 — $7.7bn (established, corroborated) | +1 — 5.28% | 0 — 86.2% issued | · | **MEDIUM (68)** |
| **ARB** | −1 — "$102m" (TI, established by self-arithmetic — **see §2: impeached**) | · Yahoo had nothing to corroborate | −1 — "12.8% issued" (**impeached**) | · | **LOW (55)** |
| **1INCH** | −1 — $119m (established, corroborated) | +1 — 3.41% | +1 — 94.2% issued | · | **MEDIUM (68)** |
| **HYPE** | +1 — $18.4bn (TI, established — **see §2: now contested**) | · Yahoo mcap rejected → volume forfeited | −1 — 33.7% issued, FDV 3.0× | · | **LOW (55)** |
| **TAO** | 0 — $1.8bn (TI, established by self-arithmetic) | · nothing to corroborate | −1 — 41.2% issued | · | **LOW (55)** |

Rejections retained: HYPE ×3 (Yahoo mcap $8,105, circulating 1.5bn,
inception 2020), ADA ×2 (Yahoo circulating count, inception), every
other token ×1 (inception, semantic).

### Why each verdict is what it is — and whether it makes sense

**BTC is MEDIUM** because 2 of 3 measured factors earned, and 0.667 <
0.75. Mechanically correct; analytically **not a sensible account of
Bitcoin**. The factor table has no way to express anything that makes
BTC what it is: sixteen years of survival (deleted with the fabricated
age field, rightly, but nothing honest replaced it), the deepest
liquidity in the asset class (its 0.96% turnover reads *neutral* on a
band calibrated for something else — §8), 56.7% of the entire market's
capitalisation, or a monetary thesis the model cannot even name. BTC is
MEDIUM because the questionnaire is short, not because the evidence is.

**HYPE is LOW** because dilution is real (one earned, one adverse, two
unmeasurable → ratio 0). Half-sensible: the 33.7% issuance and FDV at
3.0× market value is a true, material fact an investor should see.
But the model is structurally blind to the other half of HYPE's case,
which is now *measurable for free*: **$843k/day protocol fees, $535k/day
revenue, 100% of it flowing to holders (~$195m/yr against the market
value), on a chain holding $1.21bn TVL** (§3). LOW is the right output
of a model that cannot see value capture; whether it is the right
verdict is precisely the question the quality-model ruling must answer.

**ARB is LOW** — and this one is the measurement's alarm. Its
established inputs are themselves impeached by the second source (§2):
TokenInsight's circulating supply is 1,275,000,000 — *exactly the
March-2023 launch float* — making its $102m market value a
self-consistent staleness error 4.2× below CoinGecko's $530m, and its
"12.8% issued" wrong against CG's 66%. The verdict might survive
re-judgment ($530m is still small; dilution still real at 34%
remaining), but today it stands partly on false facts that passed the
gate because arithmetic coherence cannot catch a vendor agreeing with
its own stale inputs.

**TAO is LOW** on a neutral scale and adverse issuance. Thin rather
than wrong — and its supply figures sit at an 11.3% cross-source gap,
just past the corroboration tolerance, for methodology reasons (§2).
The model sees nothing of what TAO is (an AI/DePIN network with $35–89m
daily volume and near-zero DeFi footprint), and does not claim to.

**Overall: the outputs follow the current factor table mechanically and
faithfully.** The gate improved the inputs; the table itself cannot
express crypto quality. That is the finding the owner predicted, now
measured.

---

## 2. Cross-source measurement — even market cap is not one fact

Same day, three sources, the corpus:

| | CG mcap | TI mcap | Δ | CG circulating | TI circulating | verdict |
|---|---|---|---|---|---|---|
| BTC | $1,310.2bn | $1,307.6bn | 0.2% | 20,068,243 | 20,068,225 | three-source agreement |
| ETH | $232.8bn | $232.2bn | 0.3% | identical | identical | agreement |
| SOL | $44.8bn | $44.8bn | 0.2% | ~identical | ~identical | agreement |
| ADA | $7.4bn | $7.7bn | 3.4% | 37.35bn | 38.80bn | inside tolerance |
| **ARB** | **$530m** | **$102m** | **422%** | **6.614bn** | **1.275bn** | **TI stale at TGE float** |
| 1INCH | $119m | $119m | 0.8% | ~identical | ~identical | agreement (but rank: CG #233 vs TI #116) |
| **HYPE** | **$12.15bn** | **$18.25bn** | **33%** | **222.4m** | **336.7m** | **circulating-methodology conflict** |
| **TAO** | $1.96bn | $1.76bn | 11.3% | 9.60m | 8.64m | just past tolerance; emission methodology |

Three findings, each load-bearing:

1. **Where methodology is unambiguous, corroboration works perfectly.**
   BTC/ETH/SOL agree across three vendors to within 0.3%. The
   architecture's establishment concept is sound.
2. **Internal arithmetic cannot catch self-consistent staleness.** TI's
   ARB row reproduces its own price × circulating exactly — because the
   vendor computes one from the other. The triad check catches
   transcription and unit catastrophes (the $8,105 class); it cannot
   catch a frozen supply feed. **Only a second independent source can**,
   and for ARB and TAO, Yahoo had nothing to offer.
3. **"Circulating supply" is not one concept.** For HYPE, both vendors
   are internally coherent and 33% apart, because they count different
   buckets (CG excludes ~114m tokens TI counts — assistance-fund /
   non-circulating treatment). Under a two-credible-source gate, HYPE's
   market value is honestly **CONFLICTED** until a methodology is
   chosen and named. `SEMANTICS_UNCLEAR` is a real standing need, not
   a bureaucratic one. (Also: **rank is vendor-relative** — 1INCH is
   #116 or #233 depending on the listing universe — and must stay an
   attributed claim forever.)

---

## 3. Provider capability matrix

Legend per the ruling: `FREE` = FREE_API_AVAILABLE (verified on the
corpus), `PAID` = observed paywall, `N/AP` = not applicable, `N/AV` =
not available, `SEM?` = semantics unclear, `UNVER` = plausible per
published plan docs but **unverified — no key held, no account created**.

| candidate fact | Yahoo | TokenInsight | CoinGecko | CoinMarketCap | DefiLlama |
|---|---|---|---|---|---|
| price | FREE (quotes: authority today) | FREE | FREE | UNVER | N/AV |
| price history | FREE (authority) | N/AV on probed endpoint | FREE (separate endpoint, unprobed) | UNVER | N/AV |
| market cap | FREE — **wrong 3/8, silently** | FREE — **stale 1/8 (ARB)** | FREE — agreed on all majors | UNVER | N/AV |
| rank | N/AV | FREE (SEM?: universe-relative) | FREE (SEM?: same) | UNVER | N/AV |
| circulating supply | FREE — wrong for HYPE | FREE — stale for ARB | FREE | UNVER | N/AV |
| total supply | N/AV | **N/AV (endpoint lacks it)** | **FREE — fills the gap** | UNVER | N/AV |
| max supply | FREE | FREE | FREE | UNVER | N/AV |
| FDV | N/AV | FREE | FREE | UNVER | N/AV |
| genesis / project start | FREE — **fabricated 2/8, rejected 8/8 on semantics** | N/AV | FREE for 2/8 only (BTC, ETH) | UNVER | N/AV |
| 24h volume | FREE (SEM?: universe undefined) | FREE (tracked spot — narrow, defined) | FREE (broader tracked universe) | UNVER | N/AP |
| DEX volume | N/AV | N/AV | N/AV per-asset | UNVER | FREE (per protocol; 1inch ✓; HL spot slug unresolved) |
| perp volume / open interest | N/AV | N/AV | N/AV | UNVER (likely N/AV free) | **PAID (402 observed)** |
| TVL (chain & protocol) | N/AV | N/AV | N/AV | N/AV | **FREE — all 7 corpus entities** |
| protocol fees / revenue / holders revenue | N/AV | N/AV | N/AV | N/AV | **FREE — verified (HYPE, 1INCH, 5 chains)** |
| total crypto mcap / volume / dominance | N/AV | N/AV | **FREE — one call** | UNVER | N/AV |
| category performance / breadth | N/AV | N/AV | **FREE — 749 categories with mcap/vol/Δ** | UNVER | partial (protocol categories) |
| trending / attention | N/AV | N/AV | FREE (SEM?: attention only) | UNVER | N/AV |
| funding / liquidations / unlocks | N/AV | N/AV | N/AV | UNVER (unlikely free) | PAID or N/AV |
| stablecoin metrics | N/AP for corpus | N/AP | N/AP | N/AP | FREE (no corpus consumer today) |
| third-party rating | N/AV | FREE (opinion — stays isolated) | N/AV | N/AV | N/AV |

Operational facts measured on the way: CoinGecko keyless tier
rate-limits at roughly six calls/minute (429s observed mid-probe; a
free demo key — registered by the owner, not by this platform — lifts
it to production cadence). DefiLlama is keyless and generous.
TokenInsight's coin payload also carries a `tickers` array (venue
breadth candidate, unmeasured) and platform/contract identifiers.

**Proposed authority roles** (for the ruling, not enacted): Yahoo —
quotes and price history, everywhere; cross-source voice for token
facts, never authority. TokenInsight — token-fact claimant one of two,
plus the isolated rating. CoinGecko — token-fact claimant two of two,
total supply, market intelligence authority (global, categories).
DefiLlama — protocol/network fundamentals authority (TVL, fees,
revenue, holder revenue; DEX volume). CoinMarketCap — deferred until a
key exists; candidate third corroborator, nothing more.

---

## 4. Three evidence domains — confirmed, three

The measurement says yes: these are three families with different
subjects, different entities, different failure modes, and different
consumers. They must not share a schema.

- **A. Crypto Asset Facts** — about *the token*. Exists (PR #99).
  Entity: the symbol. Failure mode: vendor staleness and supply
  methodology (§2).
- **B. Protocol / Network Fundamentals** — about *the economic system
  behind the token, where one exists*. Entity: a chain or protocol
  (Hyperliquid L1; 1inch the aggregator; Ethereum the chain), which is
  **not the symbol** — the mapping token→entity is a hand-verified
  identity map exactly like `TOKEN_IDS`, and BTC maps to a chain whose
  TVL is *not a BTC-quality question* (§6). Verified free evidence:
  TVL for all seven corpus entities; fees/revenue/holders-revenue.
  Failure mode: applicability confusion — the domain §6 exists to
  discipline.
- **C. Crypto Market Intelligence** — about *the environment*. Entity:
  the market and its categories. One CoinGecko call held total mcap
  $2.31tn, 24h volume $38.7bn, BTC dominance 56.7%, ETH 10.1%, mcap
  Δ24h +0.56%; a second held 749 categories with mcap/volume/Δ. Failure
  mode: regime observations leaking into per-asset quality — the
  boundary the ruling already names, kept structural by the separate
  domain.

An asset score that quietly absorbed a market-regime observation would
repeat the account-conditions defect this platform has now fixed three
times on the equity side. Three domains is the structural prevention.

---

## 5. Crypto archetypes — the corpus classifies cleanly, on evidence we hold

Hypotheses tested against the corpus, with the grounding evidence that
is actually available free:

| token | archetype (hypothesis) | grounding evidence measured |
|---|---|---|
| BTC | **Monetary / store-of-value** | CG categories noisy here (tags it "Smart Contract Platform" *first*, plus junk like "FTX Holdings") — a rule must demand positive specific tags, e.g. PoW + L1 + dominance share; Llama: chain, no meaningful protocol economy |
| ETH | **Base-layer network** | CG: Smart Contract Platform + L1; Llama: chain, $41.9bn TVL, fee economy |
| SOL | **Base-layer network** | same shape ($4.9bn TVL, $651k/day fees) |
| ADA | **Base-layer network** | same tags; near-zero fee economy ($782/day) — a *finding within* the archetype, not a different archetype |
| ARB | **Scaling / infrastructure** | CG: Arbitrum+Ethereum ecosystems; Llama: L2 chain, $1.2bn TVL, fees paid down to L1 |
| 1INCH | **Protocol token** | CG: DEX/DeFi/AMM tags; Llama: protocol with volume+fees, no chain |
| HYPE | **Exchange-native protocol token with its own chain** | CG: DEX + Smart Contract Platform (both true); Llama: *both* a chain ($1.21bn TVL) and a fee-generating protocol — the hybrid is real, not a classification failure |
| TAO | **Other / AI network** (honest bucket today) | CG: AI + L1 + DePIN; Llama: chain with negligible TVL — the DeFi lens measures nothing meaningful here |

Mechanism: **reuse the playbook machinery, no second taxonomy.**
`PlaybookSelector` already branches on `AssetClass.CRYPTO` before
industry; the branch selects among crypto `PlaybookKind`s the same way
BANK/REIT are selected for companies, each playbook declaring what it
asks and what it declines with reasons. Selection evidence: CG category
tags (positive, specific, junk-tolerant rules) + Llama entity shape
(chain / protocol / both / neither) — both acquirable, both checkable.
UNKNOWN stays UNKNOWN; nothing is promoted by heuristics.

The requirement that matters: **absence because inapplicable, never as
missing evidence.** BTC without TVL is not a gap; a stablecoin (none
held today) must not inherit HYPE's model; TAO's empty DeFi footprint
is a declined question, not a zero.

---

## 6. Applicability matrix — candidate questions × archetypes

`ASK` / `DECL` (not applicable, declined with reason) / `UNAV`
(applicable, evidence currently unavailable or unfunded).

| question | Monetary (BTC) | Base-layer (ETH/SOL/ADA) | Scaling (ARB) | Protocol (1INCH) | Exch-native (HYPE) | Other (TAO) |
|---|---|---|---|---|---|---|
| Market scale | ASK | ASK | ASK | ASK | ASK | ASK |
| Market liquidity | ASK — **after §8's venue rule** | ASK | ASK | ASK | **UNAV** — relevant venue is perp-native; free spot data misstates it | ASK |
| Supply / dilution schedule | ASK (the one place BTC's 21m cap is the question) | DECL where uncapped (ETH/SOL) — *by design, not missing* | ASK | ASK | ASK | ASK |
| Observed market history | UNAV — held series too short to establish (§7) | UNAV | UNAV | UNAV | UNAV | UNAV |
| Network activity (fees, usage) | ASK (miner-fee economy) | ASK | ASK | DECL (protocol, not network) | ASK (its chain) | ASK, weakly grounded |
| TVL | **DECL — not a BTC-quality question** | ASK | ASK | DECL (aggregators hold ~nothing) | ASK | DECL |
| Value capture (fees→holders) | DECL (no fee-to-holder mechanism) | UNAV (burn semantics need care) | UNAV | ASK | **ASK — measured: $535k/day, 100% to holders** | UNAV |
| Dominance / monetary share | ASK (56.7% measured) | DECL | DECL | DECL | DECL | DECL |
| Security / decentralisation | UNAV (future domain) | UNAV | UNAV | UNAV | UNAV | UNAV |

---

## 7. Age, treated carefully

The five concepts are not interchangeable, and the measurement leaves
four of them unestablishable today:

- **Project age**: CG `genesis_date` exists for exactly 2 of 8 (BTC,
  ETH) — nulls for the rest. Not a factor's evidence base. Stays
  unknown; the gate's semantic rejection of Yahoo's field stands.
- **Token trading age**: no source with established semantics.
- **Observed market history**: establishable *by this platform* as the
  length of the price series it actually holds — but the quote path
  retains roughly one year, so today it can establish only "at least
  one year" for everyone, which distinguishes nothing. `UNAV` until
  history depth is deliberately acquired, and then it is
  `observed_market_history`, never "age".
- **Survival through cycles / evidence maturity**: derivable only from
  the above once it exists.

**No replacement factor is proposed.** BTC does not become HIGH by
inventing one; that instruction is honored.

---

## 8. Liquidity semantics — `volume/mcap` is not one measure

Three volume universes, same day, over CoinGecko's market value:

| | Yahoo vol → turnover | TI spot → turnover | CG vol → turnover |
|---|---|---|---|
| BTC | $12.6bn → 0.96% | $3.7bn → 0.28% | $14.2bn → 1.08% |
| ETH | $4.0bn → 1.73% | $1.3bn → 0.54% | $5.1bn → 2.20% |
| SOL | $1.1bn → 2.54% | $440m → 0.98% | $1.2bn → 2.62% |
| ADA | $392m → 5.28% | $59m → 0.80% | $208m → 2.80% |
| ARB | — | $10m → 1.98% | $36m → 6.70% |
| 1INCH | $4m → 3.41% | $2m → 1.53% | $7m → 6.11% |
| **HYPE** | — (rejected) | **$12m → 0.10%** | **$163m → 1.34%** |
| TAO | — | $35m → 1.79% | $89m → 4.52% |

The same token's turnover differs by up to **13×** by vendor universe;
ADA is "very liquid" or "borderline illiquid" depending on who counts.
The current LIQUID/ILLIQUID bands were calibrated on Yahoo's universe
and are *only* meaningful against it — which is why PR #99 froze them.

HYPE is the decisive case: its tracked **spot** turnover (0.10%) reads
adverse while the asset's own venue — a perpetuals book throwing off
**$843k/day in fees** — is invisible to every free volume feed
(DefiLlama's derivatives summary: 402, paid). For a perp-native asset,
spot turnover materially misstates the relevant market.

**Verdict:** `24h volume / market cap` is not a universal crypto
liquidity measure. It is a per-universe measure that must name its
universe, and for exchange-native archetypes the relevant universe is
not free.

**Minimum next rule (recommended, not enacted):** the liquidity factor
declares its venue universe as part of its semantics; for archetypes
whose relevant market is perp/DEX-native it is `UNAV` (declined with
that reason) rather than measured against the wrong universe — until
either the paid derivatives feed is funded or protocol fee flow is
accepted as the activity evidence under the value-capture dimension
instead.

---

## 9. Provider extensibility — the boundary holds, and one seam must evolve

What holds, verified by inspection and the existing tests: provider
payloads terminate at adapters (`NativeTokenClaims` is the only thing
that leaves a provider); standings and their semantics are consumed by
dossier and assembly through `TokenMarketFacts` alone; scoring reads
`CompanyFacts` and nothing upstream; re-judgment over stored claims
needs no reacquisition. Adding a source changes none of those.

**The defect the measurement demonstrates** — per the ruling's own
escape clause: `judge(symbol, native, generalist)` is a *two-slot*
signature with hardcoded roles. It cannot express the two findings that
matter most in §2: ARB (a second full claimant refuting the first's
self-consistent staleness) and HYPE (two coherent claimants in genuine
methodological conflict). Today's gate literally has no argument
position for CoinGecko's claims. The fix is shape, not semantics:

    fact request → provider capabilities → candidate claims (a pool,
    each claim tagged with source + semantics) → validation →
    corroboration → established / conflicted / claimed

with establishment rules, standings, tolerances and re-runnability
unchanged. Dossier rendering, scoring, canonical fact meaning and
decision logic are untouched by construction — they already consume
only the outcome objects.

---

## 10. Candidate Crypto Quality model — dimensions, not yet factors

For each dimension: the investor question, applicability, the evidence
measured, and whether a band could *responsibly* be set today. No code,
no thresholds.

**Market robustness** — *"Can a position be entered and left, in an
asset the market takes seriously?"* Applies to all archetypes. Evidence
in hand: established market value (multi-source after slice S1), rank
as attributed context, venue-scoped turnover (§8), venue breadth (TI
`tickers`, unmeasured). Corpus coverage: 8/8 for scale; turnover
blocked on the §8 rule. **Bands: scale yes (the existing ones);
turnover no — not before the venue rule.**

**Tokenomics / supply quality** — *"Who gets diluted, by what schedule,
and how much of the eventual asset already trades?"* Applies where a
schedule exists; **declined** for uncapped assets rather than absent.
Evidence: issued share and FDV/mcap (established, 6/8), unlock
schedules (no free source found — `UNAV`), concentration (`UNAV`).
Corpus coverage: strong. **Bands: measurable from the corpus spread
(12.8%–95.6% issued, FDV 1.0×–7.8×), but only after S1 resolves the
circulating-methodology conflicts — banding contested inputs would
launder the conflict.**

**Adoption / usage** — *"Is the economic system behind this token
actually used?"* Applies per archetype (§6). Evidence measured free:
TVL (7/7 entities), chain fees (5 chains; note the spread —
SOL $651k/day, ETH $168k, BTC $139k, ARB $6.9k, ADA $782), DEX volume
(1INCH $12.8m/day). Semantic flags: ETH's chain-fee figure wants
verification before establishment (`SEM?`); TVL double-counting rules
are DefiLlama's, adopted knowingly. **Bands: not yet — one day of
observation is a reading, not a distribution. Needs the S2 acquisition
running long enough to hold a corpus of observations.**

**Economic quality / value capture** — *"Does the token participate in
what the protocol earns?"* Applies to protocol/exchange-native
archetypes; declined for monetary assets. Evidence measured: fees,
revenue, **holders revenue** (HYPE: $535k/day, 100% of revenue — the
single most investment-relevant new fact this measurement produced;
~$195m/yr against a $12–18bn market value is a computable multiple).
**Bands: premature — but the *facts* are establishable now, and worth
showing attributed on the dossier long before they score.**

**Network / security quality** — future domain. Nothing free measured
here beyond consensus tags (PoW/PoS). `UNAV` throughout; do not build.

---

## 11. CryptoMarketSnapshot — the smallest useful market object

Everything below was populated by two free CoinGecko calls during the
measurement:

    CryptoMarketSnapshot
      total_market_cap            $2.31tn      (established, CG /global)
      total_market_cap_change_24h +0.56%
      total_volume_24h            $38.7bn
      btc_dominance               56.7%
      eth_dominance               10.1%
      category_performance        749 rows: name, mcap, Δ24h, volume
      relevant_categories         the categories the held tokens map to
      trending                    attention only, attributed (symbols
                                  measured today were meme assets —
                                  useful as a regime tell, never quality)
      reading                     Provenance per call

Purpose, verbatim from the ruling: *"Is HYPE weakening, or is the
crypto market weakening?"* — answerable by placing HYPE's own dated
observations beside its category's and the market's, all established,
with interpretation deferred to an analytical layer that names its
rules. Fear & Greed remains an attributed external measure (the
existing provider already treats it so). Funding/liquidations/
positioning: no free source verified; the fields wait.

Population: CoinGecko free with an owner-registered demo key (the
keyless tier's ~6 calls/min is enough for a daily acquire batch, but
with no headroom); CMC as a later corroborator if a key ever exists.

---

## 12. Recommended slices, smallest first

**S1 — Multi-source claims pool.** Generalize the gate's input from
two slots to a claims pool; add a CoinGecko claims adapter (owner
registers the free key). Re-judge the stored corpus. Expected outcomes,
already known from this measurement: ARB's stale establishment falls to
CONFLICTED (honest UNKNOWN downstream), HYPE's market value becomes
CONFLICTED pending a named circulating-supply methodology, total supply
fills from the second source, majors gain three-source corroboration.
Trust slice; no scoring, no dossier changes beyond standings doing
their existing jobs. *This is the slice the ARB finding makes urgent —
the platform is currently serving one established figure it now knows
to be false.*

**S2 — Protocol fundamentals acquisition (domain B).** Hand-verified
token→entity map (the `TOKEN_IDS` discipline); acquire TVL, fees,
revenue, holders revenue per mapped entity from DefiLlama in the
normal batch; show on the crypto dossier as attributed, dated facts
**consumed by nothing** (the TokenInsight-rating discipline). HYPE's
dossier finally carries its economic case; BTC's declines the section
as inapplicable, with the reason.

**S3 — Crypto archetypes through the playbook machinery.** Grounded
selection (CG category tags + Llama entity shape), crypto playbooks
declaring ASK/DECLINE per §6, absences become declines. No scoring
changes; this is the applicability slice.

**S4 — CryptoMarketSnapshot (domain C).** Two-call acquisition, market
page and dossier context, attributed. Answers "asset or market?"
descriptively, no regime model.

**S5 — The quality-model ruling.** Only now: per-archetype dimensions
from §10, bands measured over the by-then-accumulated observations,
scores consuming the stable `ScoreBasis` contract. Decision layer
untouched until after this.

Age stays out until history depth is deliberately acquired and
`observed_market_history` earns a factor on its own evidence.

---

## Probe artifacts

Payloads and scripts from this measurement (session scratchpad):
`tokeninsight_coins.json`, `coingecko_probe.json`,
`defillama_probe.json`, `corpus_factor_matrix.json`, and the probe
scripts. ~30 keyless calls total; TokenInsight re-read from stored
payloads at zero credit spend; no account was created anywhere.
