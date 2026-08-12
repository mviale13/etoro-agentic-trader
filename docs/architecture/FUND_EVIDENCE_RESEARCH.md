# Can fund evidence be acquired? — research, and the F1 slice it earned

**Status: measured 2026-08-12 at `f3ea1e7`; §3's defects F1–F8 were
then ruled on and built as the Fund Analytical Boundary (F1, same
day — see §9). Everything else remains research, not a mandate**
(Constitution §23–24). It records
what the platform currently knows about the funds it can see, every
place `AssetClass.ETF` falls through generic equity logic, and which
trustworthy free sources were *measured* to answer the investor-relevant
fund questions. The next fund slice, if one earns its product story,
stands on this ground.

Method: the corpus was read from the platform's own stores and live
surfaces (no code changed, no model asked); every source claim below was
probed with a real request on 2026-08-12, and a figure quoted here was
read from the response, not assumed.

---

## 1. The corpus: what "fund" means to MOVRvest today

**One typed fund is visible.** Sweeping every stored eToro watchlist
capture (98 instruments with asset types): exactly one instrument
carries asset type 6 —

| | |
|---|---|
| Symbol | `IB01.L` (eToro id 1442, LSE) |
| Name | iShares $ Treasury Bond 0-1yr UCITS ETF |
| Status | **Watched, not held** (absent from the 17 live positions) |

Four more ETFs are visible as **market-strip instruments** — SPY, QQQ,
IWM, GLD in `YahooMarketProvider.DEFAULT_INSTRUMENTS` — priced daily as
market context, never evaluated as securities.

Two watchlist symbols that *look* like funds were checked and are not:
`IS7.DE` is InTiCa Systems SE and `H2O.DE` is Enapter AG (both typed 5,
correctly). And one identity worry dissolved under measurement: eToro's
`SPCX` ("Space Exploration Technologies Corp", typed 5, **held**) was
suspected of colliding with a US ETF that historically owned that
ticker — but Yahoo's `SPCX` quote now names *Space Exploration
Technologies Corp* too (38 price observations, a recent listing).
Identity is consistent today. It was checked because Invariant 2 says a
ticker is not an identity; it stays consistent only as long as both
sides keep naming the same thing.

**The corpus is thin.** One UCITS fund on a watchlist and four US market
instruments. Any fund architecture designed now would be designed from
almost no corpus — the same situation the crypto sequence refused at S1,
and the reason this document measures sources rather than proposing
layers.

---

## 2. What the platform holds for IB01.L today

Every store, inventoried:

| Store | Content |
|---|---|
| `quotes` | price 121.40 USD, +0.02%, realized volatility **0.33%**, max drawdown **0.03%**, beta 0.0008, correlation 0.03 (vs SPY, 246 obs) — all genuinely meaningful for a T-bill fund |
| `fundamentals` | **every company field null** except `dividend_yield: 0.0` and volume 285,346 |
| `earnings`, `ratings`, `sentiment`, `token_facts` | no entry (correct — see §3, honest handlers) |
| `knowledge`, `statements` | no entry |

The live dossier (`GET /executive/IB01.L/dossier`, measured 2026-08-12):
decision INVESTIGATE, conviction 69, quality score **40 "Business
quality" (LOW)**, valuation UNKNOWN, safety 80, Investment Committee
abstains ("shown no finding in its remit"), Risk Committee strongly
positive on the volatility and drawdown readings. The playbook is
**Fund** — real, selected from identity, running zero analysts.

So today the platform knows a fund's *price behaviour* well and its
*fundhood* not at all: no cost, no holdings, no benchmark, no AUM, no
distribution policy, no structure.

---

## 3. The fall-through inventory

Measured on the live surfaces, each with its owner. The honest handlers
are listed too, because the repair surface is smaller than it looks —
the *structure* (playbook, calendar, committees) is right, and the leaks
are in the scores and the wording around it.

### Defects (a fund asked an equity question, or a fake meaning)

**F1 — "Business quality: LOW (40)" from a structural zero.**
`QualitySignalService` (`app/services/quality_signal_service.py`) counts
three factors: market cap, EPS, dividend. For IB01.L only
`dividend_yield` is non-null — Yahoo's `0.0` — so the fund reads *one
factor available, zero points, LOW → 40*. But IB01 is the
**Accumulating** share class (issuer factsheet, §5): it *cannot*
distribute, by design. A structural property of the share class is read
as a payout fact, and it is the **single value** that converts an honest
UNKNOWN (`if not counted`) into "LOW business quality" for a US Treasury
fund. This is the provider-hygiene trap — *a zero read as a measurement*
— live on the only fund in the book.

**F2 — the promising wording, un-repaired for funds.** The dossier's
blocker reads *"Valuation data is unavailable for IB01.L"* and its
review condition *"Measuring it is what would let this case progress."*
A fund has no earnings; the measurement can never come. This is exactly
the defect `ArtificialCIO._unassessable_quality` fixed for crypto — but
the guard is `asset_class.has_no_company`, which is `(CRYPTO,
COMMODITY)` only. A fund *does* have fundamentals in the provider's
sense (`has_company_fundamentals` is deliberately True), so it falls to
the generic company wording. The crypto sentence's own docstring
describes the fund case without covering it.

**F3 — the dossier invites a spend that would resolve nothing.**
`definition_for(AssetClass.ETF)` returns the GENERAL definition with
`filings_apply=True`, so the dossier renders *"No filing has been read
for IB01.L. Reading one is an explicit spend, and no surface takes it —
`movrvest observe` does."* Measured: **IB01 is absent from both EDGAR
ticker files** (`company_tickers.json`, 10,398 entries;
`company_tickers_mf.json`, 28,420 rows), so the invited observe would
find no primary source. The absence is acquisition-shaped ("not yet")
where the truth is capability-shaped ("not with these readers").
`DossierKind.GENERAL`'s docstring already names a fund dossier as a
future specialization — the definition is deliberate; the *sentence it
produces* is still wrong for this asset class.

**F4 — a fund's scores wear company vocabulary.**
`score_labels_for(None)` (the GENERAL dossier's labels) titles the
quality score **"Business quality"** — the same label as a stock. The
crypto dossier earned "Asset quality" (PR #98) precisely because a token
is not a business; a fund is not one either.

**F5 — "a fund publishes no annual report to read" is false about the
world.** `PlaybookCoverageService._never_read` charges a fund with
`NO_PRIMARY_SOURCE`, worded *"a fund publishes no annual report to
read."* The iShares umbrella publishes an audited annual report; US
ETFs file NPORT-P monthly and GLD files an actual 10-K (§6). The code
comment above `_FILES_NOTHING` is more careful ("a fund whose accounts
describe the wrapper") — the investor-visible sentence asserts
nonexistence. The honest charge is that the platform's readers target
company filings, a fact about this platform.

**F6 — two surfaces state opposite absences about one subject.** The
coverage surface says a fund's filing can *never* be read (F5); the
dossier says it has *not yet* been read (F3). Never and not-yet, side by
side, about the same security. Whichever wording a fund slice chooses,
it must choose once.

**F7 — the provider call already answers fund questions, and the
platform drops them.** `ValueProvider`'s `.info` call returned, live,
for IB01.L: `quoteType: "ETF"`, `netExpenseRatio: 0.07`,
`navPrice: 121.3958`, `ytdReturn: 2.06`, `threeYearAverageReturn:
0.046`, `fundFamily: "BlackRock Asset Management Ireland - ETF"`,
`legalType: "Exchange Traded Fund"`. `CompanyFacts` has no slot for any
of them, so the stored record is nulls plus the misleading zero of F1.
**The platform is already paying for the fund's cost of ownership on
every acquisition and throwing it away** — while the Fund playbook
lists "Cost of ownership" as priority #3 of 3.

**F8 — "No dividend." presented as an observation.** In
`evidence_weighed` on the live dossier. For an accumulating share class
this is structurally guaranteed, and reads as an adverse-shaped payout
fact to an investor comparing income funds.

### Honest handlers (recorded so nobody re-fixes them)

- **The Fund playbook** (`PlaybookKind.FUND`): selected from identity
  (`AssetClass.ETF` outranks industry — the token lesson applied), runs
  zero analysts, excludes all four fundamentals analysts each with a
  correct reason, and names the right priorities: *what it holds,
  observed volatility and drawdown, cost of ownership*. The platform can
  currently answer only the middle one.
- **The earnings calendar** filters to `AssetClass.STOCK` in both
  directions (holdings and watchlists) — a fund is never asked for an
  earnings date.
- **Risk measurement** is fully meaningful: volatility, drawdown, beta
  from the fund's own price record.
- **Committees**: the Investment Committee abstains explicitly rather
  than opining; the Risk Committee speaks to real measurements.

---

## 4. The investor questions for a fund

Derived from the Fund playbook's own priorities plus what a careful
investor asks a wrapper. Q1–Q3 are the playbook's three priorities in
its own order.

| # | Question |
|---|---|
| Q1 | What does it hold — what exposure does this wrapper actually deliver? |
| Q2 | What does ownership cost (TER / expense ratio)? |
| Q3 | What does it track, and how closely (benchmark, tracking difference)? |
| Q4 | How big is it, and how liquid (AUM, volume)? |
| Q5 | Does it distribute or accumulate? |
| Q6 | What is the wrapper (UCITS / '40 Act / trust; domicile; replication; securities lending)? |
| Q7 | Identity — which fund is this ticker, exactly (share class included)? |

---

## 5. The sources, measured

Every row below is a real probe from 2026-08-12, not a catalogue claim.

### Yahoo Finance `.info` (already called by the platform, free)

| | IB01.L (UCITS) | SPY (US) |
|---|---|---|
| `quoteType` | `"ETF"` ✓ | `"ETF"` ✓ |
| Expense ratio | **0.07 ✓** (`netExpenseRatio`) | 0.0945 ✓ |
| NAV | 121.3958 ✓ | 772.98 ✓ |
| AUM (`totalAssets`) | **absent** | $795.3bn ✓ |
| Category | null | "Large Blend" ✓ |
| Top holdings / sector weights | **empty** | top-10 + sectors ✓ |
| `ytdReturn` / 3y avg | ✓ / ✓ | ✓ / ✓ |
| `fundFamily`, `legalType` | ✓ | ✓ |
| Inception date | **wrong** — 2024-11-27 vs the issuer's 20-Feb-2019, six years off | 1993 ✓ (not independently checked) |

Two hygiene findings, both of the known Yahoo shape (*answers wrongly
without failing*): the inception date above, and **two AUM figures in
one SPY response** — `totalAssets` $795bn beside the annual-report
`fund_operations` figure $496bn, neither dated on the field. An AUM
must carry its as-of or two true figures will read as a conflict
(S4.6's rule, mapped onto funds).

### The issuer's own literature (iShares `gls-download`, keyless, free)

The product *website* is bot-gated (the screener JSON, the product page
and the holdings-CSV ajax all returned 403/500/error-HTML to plain
clients, measured repeatedly — one failure arrived as a **3,440-byte
gzip-compressed HTML error page behind a `.csv` name**, which a naive
reader would store as holdings). The *literature path* is not gated:

`https://www.ishares.com/gls-download/literature/fact-sheet/ib01-…-en-gb.pdf`
→ HTTP 200, 254KB PDF, text extracts cleanly (pypdf, 11.5k chars). It
answers, with the issuer's own authority:

- **ISIN IE00BGSF1X88**; share class launch **20-Feb-2019**; currency USD
- **Use of income: Accumulating** — the fact that retires F1/F8
- **TER 0.07%** — agreeing with Yahoo's `netExpenseRatio` to the basis point (two independent sources; a real corroboration, unlike two copies of one feed)
- Net assets: share class **$19,278.58M**, fund $26,816.77M — dated
- Benchmark: **ICE U.S. Treasury Short Bond Index**; domicile Ireland
- **32 holdings**, weighted maturity 0.33y, effective duration 0.32y
- Performance vs benchmark side by side → **tracking difference is
  computable from the issuer's own table** (1Y: 5.04% vs 5.07% = −3bp)

### SEC EDGAR (keyless with a User-Agent, free) — US funds only

- `company_tickers.json` / `company_tickers_mf.json`: SPY → CIK 884394;
  QQQ → both files; IWM/IVV → series ids under the iShares Trust
  umbrella CIK 1100663 (a fund ticker resolves to a *series*, not a
  company — identity for US funds is series-shaped); GLD → CIK 1222333.
  **IB01: absent from both** — a UCITS fund does not exist for EDGAR.
- **NPORT-P** (monthly portfolio, XML): SPY's latest parsed live —
  **503 holdings with names and `pctVal` weights, `netAssets`
  $651.59bn, reporting period 2026-03-31**. Regulator-grade,
  checkable-address evidence of exactly the platform's kind. Two traps
  measured: the `xslFormNPORT-P_X01/` URL serves a rendered view (9.3MB,
  no parseable tags) — the raw `primary_doc.xml` beside it parses; and
  the disclosure **lags** (~quarter-end + filing delay), so NPORT
  answers *"what did it hold at period end"*, never *"what does it hold
  today"*.
- **485BPOS / N-CEN** present in every US fund's form list (fees,
  operations) — named, not parsed in this research.
- **GLD files 10-K and 10-Q** — a commodity trust, not an investment
  company. The one fund-shaped instrument whose primary document the
  platform's *existing* filing reader could genuinely read.

### OpenFIGI mapping (keyless POST, rate-limited, free)

`ID_ISIN IE00BGSF1X88` → ticker `IB01`, venues LN/SW/…, securityType
ETP, one shareClassFIGI across venues. A working identity-corroboration
route for UCITS funds, where EDGAR cannot serve.

### Measured and not usable

- **iShares product/screener/holdings web endpoints**: bot-gated (403 /
  500 / error HTML) for plain clients. Line-by-line UCITS holdings have
  **no keyless route measured here**; for IB01 specifically the
  factsheet's count + maturity breakdown answers Q1 at investor
  granularity (32 T-bills, 0.33y), but that generosity is this fund's,
  not the asset class's.
- **SSGA holdings XLSX** (301 into a maze), **Invesco QQQ holdings CSV**
  (406): issuer downloads for US funds are brittle — and unnecessary
  while NPORT-P answers with regulator authority.
- **justETF, Morningstar, TipRanks**: scrape-shaped or paid; no keyless
  contract. Not measured further.

---

## 6. The evidence matrix

READY means: measured today, free, keyless, with identity attributable
to the fund (not a vendor's restatement). The two corpus populations
differ, so they are scored apart.

| Question | IB01.L (UCITS, the watched fund) | SPY/QQQ/IWM (US strip) |
|---|---|---|
| Q1 holdings / exposure | **PARTIAL** — count, maturity ladder, duration from issuer PDF; line-by-line bot-gated | **READY** — NPORT-P, 503 names + weights, lagged and dated |
| Q2 cost (TER) | **READY, corroborated** — issuer PDF 0.07% = Yahoo `netExpenseRatio` 0.07 | **READY** — Yahoo 0.0945% (+ 485BPOS as primary, unparsed) |
| Q3 benchmark + tracking | **READY** — index named and tracking difference computable from the issuer's own table | READY for benchmark via prospectus; tracking computable from returns |
| Q4 AUM + liquidity | **READY with dating discipline** — issuer PDF dated; Yahoo absent | READY — but three figures measured apart ($795bn / $652bn / $496bn on three windows); an undated AUM is a defect |
| Q5 accumulating / distributing | **READY** — issuer PDF; retires the dividend-zero fake meaning | READY (US ETFs distribute; Yahoo yield present) |
| Q6 wrapper / domicile / lending | **READY (coarse)** — UCITS, Ireland, legalType from PDF+Yahoo; lending detail is annual-report prose | PARTIAL — N-CEN named, unparsed |
| Q7 identity | **READY** — ISIN from issuer + OpenFIGI corroboration | READY — EDGAR CIK/series (series-shaped, not company-shaped) |

Reading of the matrix: **every question the Fund playbook already
names is answerable free for the one fund the investor actually
watches** — Q2, Q3, Q4, Q5 and Q7 outright, Q1 at investor granularity
— and the richest single move is F7: the platform *already receives*
the cost, the NAV, the fund family and the ETF-ness on the provider
call it makes today, and stores none of them.

## 7. What would become better for the investor (the gate, not a plan)

Named per the Constitution, decided by the owner, in no order:

1. **A fund stops being scored a LOW-quality business on a structural
   zero** (F1/F8 + Q5) — a wrong answer currently shipping, which the
   Constitution classes with defects.
2. **A fund case states this platform's limit instead of promising a
   measurement** (F2/F3/F5/F6) — the same honesty the crypto case
   already earned, wording only, no new evidence needed.
3. **The investor sees what ownership costs** (Q2/F7) — one field the
   platform already fetches, corroborated by the issuer to the basis
   point.

Everything beyond that — a fund dossier kind, holdings acquisition, a
tracking layer — is architecture, is frozen, and waits for a product
story and a corpus larger than one watched fund.

## 8. Traps recorded for whoever builds

- A bot-gate can serve a **gzip HTML error page under a `.csv` name**;
  a store that accepts it holds poison that parses as a small file. A
  fund acquirer needs the `EventFeedHealth` discipline: *nothing* and
  *nothing because the surface changed* must not look the same.
- **Yahoo's `fundInceptionDate` was wrong by six years** for IB01.L.
  Nothing that cheap corroborates it; the issuer's PDF does.
- **An AUM without an as-of is not a figure** — three true SPY AUMs
  span 60% across three undated windows.
- **A US fund ticker is a series, not a company** — IWM's identity
  lives inside CIK 1100663 among hundreds of NPORT-P filings; naive
  CIK-level reading attributes another series' portfolio to the ticker.
  Identity before reading (Invariant 2), series-scoped.
- **NPORT's XSL view looks like the filing and parses as nothing** —
  read `primary_doc.xml`, not the `xslFormNPORT-P_X01/` rendering.
- eToro's type 6 is the only fund classifier the platform has, and it
  marks 1 instrument in 98. Yahoo's `quoteType: "ETF"` — already in the
  response — is the free second witness if identity ever needs one.

---

## 9. The F1 slice: the Fund Analytical Boundary (built 2026-08-12)

The CTO's ruling on §3, built the same day the matrix was accepted. The
invariant: **a Fund cannot receive evaluative meaning from a
company-specific question its playbook does not ask.** Acceptance case
IB01.L, verified on the live dossier JSON and the rendered page.

**The structural change that was actually necessary — and it is
smaller than §3 suggested.** The capability boundary already existed:
six consumers — score labels, the value signal, missing-evidence
suppression, the committee's outside-knowledge uncertainty, the CIO's
honest wording, the writer's skip — were all keyed on
`AssetClass.has_no_company`, whose own docstring ("no business behind
it") already described a fund. The defect was **membership**: the
property predates the fund playbook and listed only crypto and
commodity. Adding `ETF` repaired F2, F4 and most of F1 through seams
that already existed. Around that one change:

- `CompanyFactsService` had conflated two decisions in one flag
  (`is_token = has_no_company`). Split: company fields key on the
  capability boundary, token-shaped fields keep their original
  membership exactly — a fund reads neither a dividend nor a
  `circulating_supply` (F1, F8, and the not-a-token half of F7).
- `QualitySignalService` gained the same optional `asset_class` the
  value signal already had, and refuses the whole factor set for a
  no-company asset — so no field the provider might someday answer
  (a fund's `marketCap` is AUM-shaped) can score it. `ValueSignal`
  gained the `basis` field `QualitySignal` already had, for the same
  failure: the builder explained a fund's UNKNOWN as figures that
  "could not be read", which will never read.
- The fund's dossier definition carries its own filings absence —
  *"Company filing knowledge is not part of the fund playbook … a
  limit of this platform's coverage of funds, not missing evidence
  about the fund"* — and the coverage blocker was reworded to the same
  boundary for every no-company noun, retiring the world-claim
  *"publishes no annual report"* (F3, F5, F6). Per the #98 precedent
  the dossier's filings sections are **absent, not sent**, and the
  reason travels on the definition.
- `expense_ratio` is retained from the `.info` call already being made
  (Yahoo reports percent; stored as a decimal ratio), reaches
  `CompanyFacts` for ETF only, and surfaces as `fund_cost` on the
  dossier — composed at the route like the token rating, so "it
  reaches no score" is a fact about the code. Store schema 2 with an
  identity migration. Live: *"Owning this fund costs 0.07% of assets
  per year"*, corroborated by the issuer to the basis point (§5).
- One contradiction found during verification and fixed at the same
  boundary: the Investment Committee declared a fund's business
  quality both *outside its knowledge* ("can ever answer") and an
  *absent measurement* ("could not be read"). The unanswerable
  questions are no longer inputs at all — for any no-company asset.

**Deliberately not done** (outcome 8): no Fund Quality, no holdings
ingestion, no N-PORT support, no benchmark/tracking/AUM scoring, no
wrapper taxonomy, no fund dossier kind — `DossierKind.GENERAL` still
serves the fund, and the fund dossier remains a named future
specialization. §5's matrix is the ground F2 would stand on; the next
research question is *"what am I actually buying when I own this
fund?"*

Regression suite: `tests/test_fund_analytical_boundary.py` (16 tests,
including: a zero dividend cannot recreate LOW for a fund even with
every company field populated; an unavailable company valuation cannot
become the fund's next thing needed; the boundary membership is
exactly three classes and UNKNOWN stays out; the honest behaviours —
identity-selected playbook, exclusions, earnings-calendar silence —
are pinned).
