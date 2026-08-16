# Quality authority: where the 0 of 78 actually comes from

**Status: research audit. No threshold, band, scoring or acquisition
change. Measured over the live book and live payloads, 2026-08-16.
Stopped for ruling.**

The question, as set: why is Quality authorised for 0 of 78, and what
is the *smallest* evidence improvement that would let MOVRvest form
useful, defensible investment opinions about real companies — without
weakening authority?

Method: every applicable Quality factor, measured per security under
two lenses — **the store today** (why 0/78 now) and **the
counterfactual after one funded `movrvest acquire`** (today's live
payloads pushed through the current, unchanged gates) — because the
first lens alone cannot distinguish staleness from structure.

---

## 1. The model being measured

`provider-quality@1` + `quality-authority@1`: three factors, one point
each — **market significance** (comparable magnitude ≥ USD 10bn),
**earnings** (`eps > 0`), **dividend** (`dividend_yield > 0`) — banded
HIGH 3 / MEDIUM 2 / LOW 0, and banded *at all* only when every
applicable factor was read. A fund, commodity or token is not asked
(11 of the 78; crypto has its own S5 gate, permanently UNKNOWN today).

The evidence each factor requires is sharply asymmetric:

| Factor | Requires | Gates on the way in |
|---|---|---|
| size | `marketCap` + established denomination + identity + (FX translation when foreign) | four crossings (#134/#136/#142–#144) |
| earnings | `trailingEps` (or `forwardEps`) present | **none** — a bare ASSUMED crossing |
| dividend | `dividendYield` present | **none** — a bare ASSUMED crossing, with #133's ×100 scale defect live (band-invariant, since the factor only tests > 0) |

"How many fail validation" has a structural answer before a numeric
one: **for two of three factors, zero can fail validation because no
validation exists.** All of the authority machinery built since #133
guards one factor of three.

## 2. Why it is 0 of 78 *today* — one sentence, then the numbers

Every stored fundamentals record predates the C5/C6 boundaries, so no
record carries an established denomination (0 of 77), the size factor
is unreadable for every company, and completeness fails corpus-wide
before any other factor matters.

Store contents, measured: market cap present 72/77 · **denomination
0/77** · vendor identity claim 0/77 · eps present 35/77 · dividend
present 35/77. The store is also *partial* in ways the payloads are
not — AAPL, GOOG, PG and META hold no stored eps at all (rate-limited
Aug-08/09 payloads) — so today's lens overstates even the eps gap.

## 3. The funnel — after one funded acquire, current code unchanged

67 quality-applicable companies; live payloads through the live gates:

```
78 securities
→ 67 quality-applicable                        (11 funds/commodities/crypto: not asked)
→ evidence available (all three provider fields served)   35
→ evidence established (size's four crossings pass)       47 of 67 have a readable size
→ all three factors readable (complete)                   28
→ Quality complete = Quality authorised                   28   (HIGH 22 · MEDIUM 5 · LOW 1)
```

Per factor, the 67 companies:

| Factor | Readable | Blocked | Blocked by |
|---|---|---|---|
| size | **47** (34 USD, 13 via C6 FX) | 20 | 15 denomination-unreconciled (dual-class/ADR) · 4 no cap in payload · 1 identity-unresolved (SE) |
| earnings | **63** (49 positive, 14 negative) | 4 | AZN, CYD (entered the book, never acquired), NESN.ZU (empty vendor payload), UDMY |
| dividend | **34** (every one a payer) | 33 | see §4 — the provider *never serves* `dividendYield: 0` |

So the first funded acquire — no code, machinery already merged —
moves Quality authority **0 → 28 of 67**, and twenty-two of those
would band HIGH (AAPL, MSFT, NVDA, JNJ, PG, MCD, SBUX, BP.L, AIR.PA,
BNP.PA, VIE.PA, VWS.CO, …). Nothing about that number is a policy
change; it is the C5/C6 restoration running as designed.

## 4. The top three blockers by population (post-acquire residual: 39)

**Blocker 1 — the dividend factor cannot read non-payment: 33
affected, and for 19 it is the *only* blocker.** Measured: of 63
companies whose payload carries any dividend information, the 34
payers get `dividendYield > 0` and the 29 non-payers get **no
`dividendYield` field at all** — the value `0` never appears in that
field, corpus-wide. Yahoo represents "pays nothing" by *omission* in
the field we read — and by an **explicit `0.0`** in two fields we
discard: TSLA, AMZN and ADBE all serve
`trailingAnnualDividendRate: 0.0` and
`trailingAnnualDividendYield: 0.0`. The platform reads the one
dividend field the provider omits for non-payers, and throws away the
fields where the provider states the zero. Under `quality-authority@1`
this is fatal by design: absence ≠ measured zero (correctly — F1's
lesson), so every non-payer is *incomplete* rather than MEDIUM, and
TSLA cannot be banded at all. **This is a factor fed by the wrong
field, not an evidence gap in the world** — the classification the
brief calls "blocked because our factor itself is poorly designed."

**Blocker 2 — dual-class/ADR caps cannot establish a denomination: 15
affected** (GOOG, META, VOW3.DE, NOVO-B.CO, SHOP, PLTR, MSTR, SPCX,
DIDIY, SRAD, …). The #142 finding standing exactly where it was left:
`cap = price × sharesOutstanding` fails for structural reasons
(ratios 1.02–2.43), the amendment removed the circular count that
papered over it, and no second corroboration route exists. This is a
genuine evidence problem — the caps span share classes the single
listed count does not — and its repair (per-class counts, or a
filing-grade share figure) is real acquisition work.

**Blocker 3 — securities the platform holds no payload for: 4–5**
(AZN and CYD entered the book after the last acquisition; NESN.ZU is
the book's Nestlé entry and returns an empty vendor payload; UDMY
serves no cap; SE is identity-blocked pending #145's ruling). Small
in count, but it contains the book's only Nestlé.

**Genuinely economically indeterminate: 0.** Every incomplete company
traces to evidence, structure or factor design — none to an economy
that cannot be assessed.

## 5. The product question — one fix, largest honest gain

> If we fixed only one evidence/acquisition problem next, which one
> would cause the largest increase in economically meaningful Quality
> coverage without weakening authority?

**The dividend factor's zero-evidence repair.** Read the provider's
explicitly-stated zero (`trailingAnnualDividendRate` /
`trailingAnnualDividendYield`) instead of inferring anything from the
absence of `dividendYield`. It is:

- **the largest single increment**: +19 companies complete
  (28 → 47 of 67, 70%) — every size-and-earnings-readable non-payer:
  TSLA, AMZN, ADBE, AMD, NFLX, MNST, BA, ORSTED.CO, GRE.MC, …;
- **authority-strengthening, not weakening**: it consumes *more*
  provider evidence, an explicit statement rather than an inferred
  silence — no invented semantics (#133's rule), no absence read as a
  zero (F1's rule), completeness untouched;
- **already precedented**: it is the statement-shape distinction ("a
  printed zero versus a line never located") applied to a provider
  payload.

For comparison, the same question asked of the other blockers:
the dual-class route would add at most 15 (and the hardest evidence
work); the never-acquired 5 add 5. A funded acquire adds 28 but is
operation, not repair.

One honesty note carried with the recommendation: the repair widens
coverage of the *current* question set. Whether that set asks the
right questions is §6, and the answer there does not change this
answer — it bounds what the +19 means.

## 6. Are these three the right questions?

**Measured answer: they are three convenient provider fields, not
three independent dimensions of business quality.** The completeness
requirement (3/3, `quality-authority@1`) is sound and untouched — but
what it demands completeness *of* is: is the cap over USD 10bn, is
trailing eps positive, does it pay a dividend. #129 already named the
composite: *large-cap dividend-paying value investing*. This corpus
makes the consequences concrete:

- **HIGH is structurally reserved for payers.** All 22 post-acquire
  HIGHs pay dividends — definitionally, since HIGH needs 3/3.
  Amazon, Alphabet (post-repair) and TSLA cap at MEDIUM forever. A
  quality model in which Amazon cannot be a HIGH-quality business is
  answering a narrower question than its name claims.
- **eps > 0 is a bar, not a measure** — 14 companies read "negative
  earnings, adverse" with no notion of stage, cyclicality or cash
  generation (RIVN and DAL get the same adverse finding).
- **Size is significance, not quality** — and it is the only factor
  the entire authority arc guards.

The platform already owns the better answer, and it is the one
LICENSED quality rule it has: **grounded business quality (#81)** —
factors measured from filings over established business understanding.
Its coverage today, measured: **0 of 80 read.** Not because filings
were never read — 33 companies hold knowledge files, JPM's at 5/5
unanimity — but because every stored observation is **schema 12** and
the reader is on **schema 14** (DP1's ownership partition cannot
pool), so the entire filing corpus awaits a funded re-observation
(~33 companies × quorum 5). The grounded route is the "right
questions" answer, and it is dark for exactly one reason: the re-read
was never funded.

## 7. The specimens — why MOVRvest cannot yet form a Quality opinion

| Specimen | Today | After one funded acquire | What still blocks, and its class |
|---|---|---|---|
| **AAPL** | UNKNOWN — stored record predates the boundaries (no denomination; not even eps stored in the Aug-09 partial) | **HIGH 3/3** (USD cap reconciles; eps 8.72; yield 0.35) | nothing — pure staleness |
| **PG** | UNKNOWN — same | **HIGH 3/3** (eps 6.62; yield 3.01) | nothing — pure staleness |
| **GOOG** | UNKNOWN | still UNKNOWN — eps 19.93 and dividend 0.26 readable, but the dual-class cap fails the identity at 2.21× → denomination refused → size unreadable | blocker 2: structural, needs a multi-class corroboration route |
| **TSLA** | UNKNOWN | still UNKNOWN — size and eps readable; `dividendYield` absent (non-payer; the explicit `0.0` sits in fields we discard) | blocker 1: factor design; after the repair, complete at MEDIUM 2/3 — and capped there by the dividend wall (§6) |
| **VOW3.DE** | UNKNOWN | still UNKNOWN — eps 10.43 and dividend 7.14 readable (7.14 is #133's percent-points scale, live); dual-class cap fails at 2.43× | blocker 2 — and, once established EUR, C6's FX route is already waiting |
| **Nestlé as booked (NESN.ZU)** | UNKNOWN | still UNKNOWN — the book's entry returns an *empty* vendor payload: no cap, no eps, no dividend | blocker 3: the book names a listing the vendor serves nothing for; NESN.SW (which reconciles CHF and would translate under C6) is no longer the book's entry |
| **JPM** | — | — | **not in the book at all** (no watchlist names it), so provider Quality is never asked; and its filing knowledge — the platform's deepest, 5/5 anchors — is schema-12, unreadable since DP1. Both quality routes are dark for the best-understood bank the platform ever read |

(SE, measured in passing: identity-unresolved — the only security the
#143 amendment's gate blocks live, pending #145's ruling. SPCX:
unreconciled denomination *and* negative eps *and* absent dividend.)

## 8. Recommended next vertical slice — for ruling, not implemented

1. **Operate the machinery that is already merged: one funded
   `movrvest acquire`.** 0 → 28 authorised (22 HIGH), through gates
   that are all in place. No code. Everything below is measured
   against this baseline, not against zero.
2. **The dividend zero-evidence repair** (the §5 answer): read the
   provider's explicit `trailingAnnualDividendRate`/`Yield` zeros;
   28 → 47 of 67 complete. Small slice: one provider field mapping,
   one registered crossing, factor unchanged, completeness unchanged.
3. **Rule separately, as their own slices, in whichever order the
   product demands**:
   - the **dual-class/ADR denomination route** (blocker 2, 15 names —
     the book's GOOG, META, VOW3.DE heart);
   - **funding the schema-14 re-observation** of the 33-company
     knowledge corpus, which is what stands the LICENSED grounded
     quality (§6) back up — the actual answer to "are these the right
     questions", and the only path on which a JPM-class opinion can
     ever rest on filings rather than on three provider fields.

Nothing here touches thresholds, bands, scoring, completeness, or any
fingerprinted rule.
