# MOVRvest Frontend — UX/UI Inventory

**Status:** Required first deliverable of the UX/UI Alignment mission. This is an
evidence-based audit produced *before* any refactoring. Every claim below was
verified against the code on branch `main` (clean, green). No frontend code was
changed to produce it.

**Scope of confidence.** Route data-sources, mocks/fallbacks, dead code,
reachability, and frontend-calculation locations were verified directly. A full
field-by-field "backend fields ignored" audit was done for the highest-value
surfaces (Executive Workspace, Dossier) and is marked *pending* where a page's
full body was not yet line-read. That gap is stated, not hidden — per the
product's own honesty rule.

---

## 0. Headline findings

1. **An entire dead dashboard.** All 18 components under
   `components/dashboard/` have **zero live consumers**. They are the previous
   generation of the UI. Alongside them: 3 dead API clients
   (`lib/api/movrvest.ts`, `lib/doctor-api.ts`, `lib/explanation-api.ts`) and
   two stray backups (`app/page.tsx.backup`, `app/globals.css.backup`).

2. **The homepage's primary CTA leads to a placeholder.** Every "review case"
   link on the Executive Workspace points at `/dossiers/{symbol}`
   (`lib/api/executive-workspace.ts:273`), and `/dossiers/[symbol]` renders
   `WorkspacePlaceholder` — a dead end. The backend endpoint that would fill it,
   `GET /executive/{symbol}`, **already exists** (`app/api/routes/executive.py:152`).

3. **A route renders fabricated data as if real.** `/briefs/[symbol]` renders a
   hardcoded `microsoftExecutiveBrief` mock (`app/briefs/[symbol]/page.tsx:2`)
   for *any* symbol. This is the fabricated MSFT brief. It is behind the
   well-built `components/brief/*` stack, which is wired only to this mock.

4. **The frontend calculates investment meaning.** Despite disciplined JSON
   parsing, `lib/api/executive-workspace.ts` derives **portfolio risk band**
   (`riskLevel()`, line 309) and **concentration/diversification**
   (`diversification()`, line 321) in TypeScript from raw numbers. These are
   backend judgments, not presentation banding. A second instance:
   `ExecutiveWorkspaceBriefing.tsx:140` recomputes liquidity % from
   `cash / equity` even though the backend already provides `liquidity_pct`.

5. **A whole frontend reasoning engine exists, wired only to a mock.**
   `lib/acio/` (ontology + `PortfolioReasoner` + `PortfolioEvidenceBuilder`) is
   consumed **only** by `lib/investor/mockAnalysis.ts` → onboarding
   `AnalysisResultsStep`. It is a TypeScript re-implementation of investment
   reasoning that the backend now owns.

6. **Navigation does not match the product's information model.** Primary nav is
   `Executive Workspace / Portfolio / Research / Markets / Brain / Settings`.
   The mission's model wants `Overview / Portfolio / Decisions / Research /
   Markets / Track Record / Investor Policy`. `Brain` is promoted to primary nav
   (mission says it should be a diagnostic route). `Decisions`, `Track Record`
   are absent. `Investor Policy` exists as `/strategy` but is **not linked from
   nav**; `/investor` (Artificial CIO) is likewise an orphan.

---

## 1. Route inventory

Reachability legend: **Nav** = in primary sidebar; **Link** = reachable via an
in-app link; **Orphan** = reachable only by typing the URL.

| Route | Reach | Purpose today | Data source | Mocks / fallbacks | Frontend calc | Recommended action |
|---|---|---|---|---|---|---|
| `/` | Nav | Executive Workspace (Overview) | `getExecutiveWorkspace()` → `GET /brain/` + `GET /executive/portfolio` | On fetch failure renders `executiveWorkspaceMock` (labeled `placeholder` via PageIntegrity) | `riskLevel()`, `diversification()` in the API layer; liquidity % recomputed in briefing | **Phase 2.** Keep the labeled-fallback pattern; move risk/diversification/liquidity to backend. Fix the CTA (see `/dossiers`). |
| `/portfolio` | Nav | Portfolio condition & risk decomposition | `lib/api/portfolio.ts` (`GET /portfolio`) | none found | bar widths only (`investedWidth`); scores arrive from backend (`ExecutivePortfolioAssessment` notes it *used to* derive them) | **Phase 4.** Field-level audit pending; verify no proxy risk ladder remains. |
| `/research` | Nav | Decision funnel / candidates | `getResearchPipeline()` (`lib/api/research.ts`) | none found | `Math.max` over conviction for ranking only; explicit "never render unmeasured as zero" discipline present | **Phase 4.** Verify reviewed-vs-unevidenced split is visible. |
| `/markets` | Nav | Market context | `lib/api/market.ts` (`GET /market`) | none found | `* 100` formatting only | **Phase 5.** Add explicit "market does not gate decisions" statement; ensure neutral averages don't hide opposing moves. |
| `/brain` | Nav | — | none | `WorkspacePlaceholder` | — | **Demote from primary nav** to a diagnostics route. |
| `/settings` | Nav | — | none | `WorkspacePlaceholder` | — | Placeholder; low priority. |
| `/investor` | Orphan | Artificial CIO view | `getArtificialCio()` (`lib/api/artificial-cio.ts`) | "local fallback data" path (page line ~221) | pending | Candidate to become the **Decisions** surface; currently unreachable. |
| `/strategy` | Link* | Investor Policy form | `lib/strategy-api.ts` | none found | none obvious | Promote to nav as **Investor Policy**. *Only linked from the dead `InvestmentPolicyCard`, so effectively orphaned. |
| `/dossiers/[symbol]` | Link | Investment dossier | none | `WorkspacePlaceholder` | — | **Phase 3, highest value.** Wire to real `GET /executive/{symbol}`; do **not** reuse the MSFT mock. Contract gap — see §3. |
| `/briefs/[symbol]` | Orphan | Executive brief | **hardcoded `microsoftExecutiveBrief` mock** | entire page is mock | n/a | **Phase 1.** Remove fabricated route or repoint the `brief/*` components at real data. |
| `/events/[slug]` | Orphan | — | none | `WorkspacePlaceholder` | — | Placeholder; decide keep/remove. |

---

## 2. Component inventory

### Dead (zero live consumers) — remove after confirming
- **`components/dashboard/` — all 18 cards:** `AdvisorCard`, `BrainCard`,
  `ChangesCard`, `CommitteeWeightsCard`, `DoctorCard`, `ExecutiveBriefCard`,
  `ExplainCard`, `Header`, `InvestmentPolicyCard`, `InvestorDNACard`,
  `NextActionCard`, `OpportunityCard`, `PortfolioCard`, `PortfolioHealthCard`,
  `ReflectionCard`, `ObservationCard`. (Previous-generation dashboard.)
- **Dead API clients:** `lib/api/movrvest.ts`, `lib/doctor-api.ts`,
  `lib/explanation-api.ts`.
- **Stray files:** `app/page.tsx.backup`, `app/globals.css.backup`.
- The many 1-consumer `lib/*-api.ts` clients are consumed by the dead dashboard
  cards; they die with them (`committee-weights-api`, `investor-dna-api`,
  `observation-api`, `portfolio-health-api`, `reflection-api`, `brain-api`).
  Verify each consumer is itself dead before deleting.

### Components containing business calculation (move to backend)
- `lib/api/executive-workspace.ts` — `riskLevel()`, `diversification()`,
  `convictionLevel()` banding thresholds.
- `components/executive/ExecutiveWorkspaceBriefing.tsx:140` — liquidity %.
- `lib/acio/reasoning/*` — full reasoning engine (see below).

### Components using mock fallback
- `app/briefs/[symbol]/page.tsx` — `microsoftExecutiveBrief`.
- `components/investor/onboarding/steps/AnalysisResultsStep.tsx` →
  `lib/investor/mockAnalysis.ts` → `lib/acio/*`.
- `lib/api/executive-workspace.ts` — `executiveWorkspaceMock` (labeled fallback).

### Reasoning engine wired only to a mock — `lib/acio/`
`ontology/{company,investor,macro,market,portfolio}.ts`,
`reasoning/PortfolioReasoner.ts`, `reasoning/PortfolioEvidenceBuilder.ts`,
`knowledge/types.ts`. Only reachable path is onboarding via `mockInvestorAnalysis`.
This is the single largest violation of "the frontend must not calculate
investment meaning." Decide: retire the onboarding mock analysis, or back it with
a real backend endpoint. Do not extend it.

### Duplicate concepts rendered inconsistently
- **Two `ObservationCard`s** (`components/dashboard/` vs
  `components/investor/onboarding/cards/`).
- **Three dashboards:** `components/dashboard/*` (dead),
  `components/executive/*` (live homepage), `components/investor/dashboard/InvestorDashboard.tsx`.
- **Executive brief rendered two ways:** `components/brief/*` (mock-fed) vs
  `components/executive/ExecutiveWorkspaceBriefing.tsx` (live). Consolidating on
  one is the path to the shared `DecisionCard`.

### Reusable, keep (live)
- `components/system-integrity/*` (`PageIntegrity`, `BackendStatusDot`,
  `SystemIntegrityLegend`) — already the honesty backbone; extend, don't replace.
- `components/ui/*` (`Card`, `StatusPill`, `StatusDot`, `ProgressRing`).
- `components/executive/*`, `components/portfolio/ExecutivePortfolioAssessment.tsx`.
- `components/brief/*` (good structure, wrong data source — repoint, don't rebuild).

---

## 3. Contract inventory (highest-value gaps)

| Surface | Frontend needs | Backend provides today | Gap owner |
|---|---|---|---|
| **Dossier** `/dossiers/{symbol}` | Five-question case: what changed, why, portfolio room, decision, evidence weighed, committee opinions, provenance, missing evidence | `GET /executive/{symbol}` → `ExecutiveBriefResponse`: `symbol, headline, summary, confidence, portfolio_health, priorities[], investment_cases[]` where each case is only `symbol, recommendation, confidence, conviction, summary, previous_decisions` | **Backend.** The single-symbol endpoint is *thinner* than the per-case payload the list endpoint already returns (`/executive/portfolio` cases carry `risk_level, why_now, risks, expected_holding_period, committee_agreement`). No evidence/provenance/committee structure is exposed anywhere yet. |
| **Overview risk/diversification** | Portfolio risk band, concentration room | Raw `invested_usd`, `total_value`, `positions` | **Backend** should own the band; frontend currently derives it. |
| **Decisions inbox** | Consolidated Artificial CIO judgments with state grouping | `/executive/portfolio` cases + `/investor` (Artificial CIO) exist but aren't consolidated into one surface | **Frontend** consolidation; backend contract likely sufficient. |
| **Track Record** | Decisions recorded, mature outcomes, hit rate when measurable | `recommendation_timeline` router exists; maturity/outcome exposure unverified | Audit pending. |

---

## 4. Proposed migration sequence (small, verifiable slices)

Ordered by trust-risk first, then value. Each slice ends green
(`ruff` / `mypy` / `pytest` / `npm run build`) and committed.

**Slice 1 — Delete the dead generation (truthfulness, zero behavior change).**
Remove `components/dashboard/*`, the 3 dead API clients, the two `.backup`
files, and any now-orphaned 1-consumer `lib/*-api.ts`. Pure subtraction; verify
`npm run build` and grep for stragglers first.

**Slice 2 — Remove fabricated data surfaces.** Delete or repoint
`/briefs/[symbol]` off `microsoftExecutiveBrief`. Decide the fate of
`lib/acio/*` + `mockAnalysis` (retire onboarding mock, or gate it behind a real
endpoint). No fabricated brief reachable after this slice.

**Slice 3 — De-calculate the Overview.** Move `riskLevel`, `diversification`,
liquidity % to the backend; render backend-provided bands. Add an explicit
`EvidenceStatus` for any value the backend cannot yet supply. Call out the
backend contract change explicitly (do not paper over it in TS).

**Slice 4 — The real Dossier (needs backend contract work first).** Expand
`GET /executive/{symbol}` to carry evidence weighed, committee opinions,
strengths/risks, provenance, and missing-evidence markers; then wire
`/dossiers/{symbol}` to it using the existing `components/brief/*` stack. Fix the
homepage CTA target. This is the mission's five-question case.

**Slice 5 — Navigation & consolidation.** Reshape nav toward the product model
(`Overview / Portfolio / Decisions / Research / Markets / Track Record /
Investor Policy`), promote `/strategy` and a Decisions surface, demote `/brain`
to diagnostics. Introduce the shared `DecisionCard` once the brief/executive
duplication is resolved.

**Slices 6+ — Portfolio, Research, Markets, Track Record** per the mission's
per-screen responsibilities (§ Portfolio/Research/Markets/Track Record).

---

## 5. Execution log

The inventory above is the point-in-time audit that preceded the migration.
Executed since, all on `feature/ux-slice-1-remove-dead-dashboard`, each slice
pure subtraction with all four gates green and the commit verified in
isolation via `git archive HEAD`:

- **Slice 1** (`787456b`) — dead dashboard generation: 16 cards, 10
  dead/orphaned API clients, 2 backups. 28 files, −1,409 lines.
- **Slice 1b** (`22346e4`) — 17 stray *tracked* files outside `movrvest-web/`
  discovered during commit verification: `apps/web/movrvest-web-old/`,
  root-level `lib/` (including a surviving frontend `ClaimEngine.ts`),
  `mocks/`, `types/`, fragments under `apps/web/components/`, and a
  `".coverage 2"` iCloud conflict artifact. None buildable — no
  tsconfig/package.json exists outside `movrvest-web`.
- **Slice 2.1** (`81257fd`) — reachable fabricated data: `/briefs/[symbol]` +
  `microsoftExecutiveBrief` + the orphaned `components/brief/*` stack
  (recoverable at `3551ab1` for the Dossier slice), and `/investor`, whose
  client fabricated per-field defaults ("78%", "27 days", "Moderate" risk
  tolerance) even on successful backend responses under a green "Connected"
  banner — worse than the labeled-fallback pattern this inventory recorded.
- **Slice 2.2** (`952711b`) — the frontend reasoning engine: `lib/acio/*`,
  `lib/investor/*`, and the unreachable onboarding prototype (28 files).
  Inspection proved no caller to migrate: zero external references, no
  dynamic imports, no mounting route.

- **Overview contract slice** (`86eb81c`, PR #9) — the first two-sided slice.
  Backend: `app/renderers/brief_language.py` puts the brief's numbers into
  words once (`health_label`, `conviction_label`, `urgency_band`); both
  `/executive` routes serve `portfolio_health_label`, `urgency_band`,
  `conviction_label`. Frontend: `riskLevel()`, `diversification()`,
  `healthLabel()`, `convictionLevel()`, `urgencyBand()` and the liquidity
  recompute deleted; the Risk row renders the Brain's own `risk.level`
  ("Not measured" when null); "Diversification" became the measured
  "Largest position"; labels are validated against the rendered vocabulary
  and fail loudly on unknown words. The labeled demo fallback is resolved:
  `lib/mocks/executive-workspace.ts` deleted, an unreachable backend renders
  an explicit unavailable state with no figures at all. Verified live in
  both states.

- **Dossier slice** (`930c08f`, PR #10) — `GET /executive/{symbol}/dossier`
  composes `ExecutiveDecision`, `InvestmentThesis`, `DecisionEvidence`,
  `CommitteeOpinion` and `Provenance`; nothing derived at the API layer.
  `/dossiers/[symbol]` replaces its placeholder with the five-question case:
  recorded history only, recommendation + rationale, investor context kept
  apart from security evidence, scores with "Not measured" nulls, committee
  opinions with abstentions marked (never rendered as opposition), and
  domain-worded provenance. The homepage's "review case" CTA now lands on a
  real page. Verified live in three states (evidenced, unevidenced, backend
  down).

- **Nav + DecisionCard slice** (`148a92e`, PR #11) — navigation maps the
  product: Overview (renamed from "Executive Workspace" everywhere),
  Portfolio, Research, Markets, Investor Policy, Settings; Brain demoted to
  an unadvertised diagnostics route. `components/decisions/DecisionCard.tsx`
  is the one presentation of a decision's identity (security, state,
  conviction in the backend's words, recorded history, "Review case"),
  adopted by the Overview's cases and the Research pipeline; the research
  contract gained `conviction_label`. Promoting `/strategy` surfaced and
  fixed two defects: it read `NEXT_PUBLIC_API_URL` (every other client reads
  `MOVRVEST_API_URL`) and it crashed with a 500 when the backend was away —
  it now joins the shared layout and fails honestly.

- **Portfolio slice** (`e4b7613`, PR #12) — the screen leads with the
  measured story before any raw rows. Backend: `CapacityAnalyst` (beside
  `RiskAnalyst`) measures room to act against the stated policy — funding
  room in points and dollars, single-position headroom served *signed* (a
  holding over its limit is a measured breach, not a zero), crypto-ceiling
  room unmeasured while any of the account is unclassified, reason named.
  `/brain/` serves the assessment plus the holdings the snapshot already
  carried, each with the snapshot's own weight (null on a valueless
  account, never zero). Frontend: `CapacityToAct` renders the three terms
  in the Brain's figures; `HoldingsTable` renders last, as evidence, with
  unresolved instruments keeping their reported identity; the aside's
  "next portfolio slice" promise retired. Verified live in both states —
  the real account exercised the honest paths on its own (an unresolved
  `#1238` row, a 0.2%-unclassified crypto absence with its reason).

- **Research slice** (`70847f8`, PR #13) — the funnel now names what it
  previously only counted. `SecurityPerception.perceive()` records which
  candidates a fundamentals request was actually spent on; the Brain
  carries `attempted_candidates` as a fact; the research service derives
  the "reviewed" count *and* two named groups from that one record —
  `unevidenced` (request spent, nothing came back, deliberately not
  judged) and `not_reviewed` (outside the budget, nobody looked). The
  route stops reconstructing "reviewed" by arithmetic. The page renders
  both groups with symbol, name and source watchlist; the strict parser
  requires the new fields and fails loudly against an older backend.
  Verified live in three states, including a genuine old-contract backend
  refusing to partially render.

- **Markets slice** (`d778bbb`, PR #14) — the market's role stated and
  checkable (the CIO reads no market mood; market context reaches a
  decision only as measured per-security evidence), and unusual movement
  measured rather than eyeballed: `MarketQuote` derives its own ordinary
  day from its own volatility and today's move as a multiple of it;
  `/market/` serves `typical_daily_move_pct` / `move_ratio` / `unusual`
  (null when history unreadable — unknown, not calm). Page: "Unusual
  today" names the instruments whose day was unusual *for them*, a
  "vs typical day" table column, and the informs-not-gates statement.
  Live data made the case: SPY +1.8% flagged at 2.2× its day; WTI −6.4%
  not flagged (1.9× of oil's wild ordinary day).

- **Track Record slice** (`b81d246`, PR #15) — the domain already knew
  how to be honest (no scoring of MONITOR/INVESTIGATE or flat moves, no
  hit rate below ten calls, unscored carried with reasons) but only the
  CLI read it. `GET /track-record/` now serves outcomes (provenance on
  every row), counts, `hit_rate` (null with the minimum stated beside
  the absence) and unscored reasons counted; the verdict is worded once
  in the route. `/track-record` joined the primary nav — the mission's
  product model is now fully present. Verified live on the real
  journal: 99 recorded, 0 old enough to measure, no hit rate, three age
  reasons counted — the mission's exact honest-maturity example.

- **Closeout** (PR #16) — the `/events/[slug]` placeholder removed: an
  orphan reachable only by typed URL, rendering an invented title from
  its own slug under a promise no backend concept backs. The tracked
  `.coverage` artifact untracked and ignored. `PROJECT_STATE.md` updated:
  the mission recorded as complete, and its stale claim that no
  beta/correlation is measured corrected (`MarketSensitivity` measures
  both; the market still gates nothing, now stated on `/markets`).

The mission's screens are all shipped. Still open: a future Decisions
inbox surface once the contract earns it.

---

# After the mission: the crypto dossier (PR #120, 2026-08-11)

One surface added since closeout, outside the mission's scope and under
its rules
([`../architecture/CRYPTO_DOSSIER_UI.md`](../architecture/CRYPTO_DOSSIER_UI.md)):

- **`/crypto/[symbol]`** (`app/crypto/[symbol]/page.tsx`) — the
  digital-asset dossier, served by `GET /crypto/{symbol}/dossier`. A
  token is not a company with different labels: the audit that earned
  the page found `/executive/BTC/dossier` leading with conviction,
  agreement and safety — none of it from crypto evidence — while six
  crypto layers had reached the CLI and stopped.
- **The frontend calculates nothing analytical**, enforced three times:
  adapters carry the domain's sentence beside every state, the parser
  *requires* it, and the page renders the refusal where the backend
  declines to interpret. No fallback prose turns a measurement into
  economic meaning.
- **The page changes with the asset** — 9/12/15/9/4 questions asked
  across the corpus — but a count is never the differentiator (BTC and
  1INCH have identical counts and are not remotely the same asset):
  questions are named, grouped by applicability, and the groups are
  separated rather than sorted. `UNKNOWN` is never a zero,
  `NOT_APPLICABLE` is never adverse, and no state is colour-coded.
- The equity dossier at `/dossiers/[symbol]` banners a link to the
  digital-asset dossier for crypto symbols; the two compositions do not
  share an endpoint (~19ms of stored doors against ~12s of brain
  pipeline).

---

# EF1: the classification an investor can trust (2026-08-13)

The equity dossier's playbook card was the industry route wearing a
classification heading — a held bank read *"Not classified"* under a
static sentence asserting the platform knew nothing, while the grounded
route had concluded Bank
([`../architecture/EQUITY_DOSSIER_FIDELITY.md`](../architecture/EQUITY_DOSSIER_FIDELITY.md)
§7). What changed on the surface:

- **`/dossiers/[symbol]` gains a Classification section** rendering the
  backend's `classification` object: Industry (the provider's category,
  dated, or its worded absence — two absences, two sentences) beside
  Investment playbook (established / refused / unavailable, each
  carrying the owning layer's sentence verbatim). The section closes
  with the backend's one-sentence distinction between the concepts.
- **The analyst-coverage card is re-headed** by the definition's new
  `analysis_heading` ("How this security is analysed"), so "General
  Corporate" reads as the analysis frame it is, never as an earned
  classification.
- **The parser refuses what it does not know**: every `stated` sentence
  is required, and an earned-playbook state outside
  established/refused/unavailable throws rather than defaulting — the
  fallback-prose door stays shut. No pill and no colour grades the
  states; an honest absence is not ranked below a conclusion.
- Rendered-page verification (not status codes): VOW3.DE shows Auto
  Manufacturers beside the engine's verbatim 33%-coverage refusal; JPM
  shows "Not acquired" beside an established Diversified Business — the
  two concepts demonstrably independent on one card.

---

# F3: why the recommendation changed (2026-08-13)

The dossier's *What changed* section stated a run length and called it
stability. VOW3.DE read "Stable — 6 consecutive reviews since
2026-08-09" over a record holding eight state changes, three of them on
that very date
([`../architecture/EQUITY_DOSSIER_FIDELITY.md`](../architecture/EQUITY_DOSSIER_FIDELITY.md)
§9). What changed on the surface:

- **`/dossiers/[symbol]` gains "Every recorded change"** under *What
  changed*: each transition with its states and convictions either side,
  the rationale the CIO recorded **at the time**, and the scores that
  differed — most recent first.
- **The trend sentence no longer dates a calm that did not hold.** Where
  the record contains changes it counts them; where the run is the whole
  record, "Stable — N consecutive reviews since DATE" is kept.
- **The parser requires every backend sentence** (`stated`, `rationale`)
  and computes no delta. A score that stopped being measurable renders
  the domain's own words — never a fall, never a zero.
- **Absences render as absences**: a first review says it has nothing to
  have changed from; an unchanged case says so; a transition whose
  scores predate the journal says what cannot be said.
- Rendered-page verification: VOW3.DE shows the three 9 August moves
  with *"Business quality could no longer be measured (it was 62)"*, and
  JPM — which never changed — keeps its honest "Stable".

### One page container, fluid — `PageMain`

Raised from product use, twice: the token-supply answer read as a
narrow column on a 1,990px display. It was not the tokenomics view's
fault. The app carried **four different answers to the width question
across ten containers** — `max-w-[1600px]` on five pages,
`w-[90%] max-w-[1700px]` on Research, `max-w-5xl` (1,024px) on the
crypto dossier, `max-w-4xl` (896px) on Investor Policy, and
`max-w-6xl` inside `WorkspacePlaceholder` — so the same screen
rendered a crypto dossier at 944px of content and the portfolio beside
it at 1,520px.

`components/layout/PageMain.tsx` is now the only one. Measured on a
1,990px viewport:

| surface | before | after |
|---|---|---|
| `/crypto/[symbol]` | 944px — **47% of the display** | 1,607px — **81%** |
| `/strategy` | 816px | 1,607px |
| Brain, Settings | 1,072px | 1,607px |
| `/research` | 1,560px | 1,607px |
| home, portfolio, markets, dossiers, track-record | 1,520px | 1,607px |

**Fluid means gutters, not a percentage.** `w-[90%]` grows its own
margins with the display — which is why Research, the one page already
written in the percentage idiom, rendered *narrower* than the
fixed-1,600px pages on a wide screen. Constant padding spends every
pixel the navigation leaves on content. The single `max-w-[2400px]` is
an ultrawide guard, not a layout width: it engages past roughly a
2,700px viewport, so 1,440px, 1,990px and 2,560px are all entirely
fluid.

**Widening a container is safe only because prose caps itself.**
Reading measure lives on the content — `max-w-2xl` and its siblings
appear 16 times in the crypto dossier alone — so no paragraph became a
200-character line. Where content had no natural measure the fix was to
show *more*, not *wider*: the policy form's three grids take a third
column past `2xl`, and Investor Policy went from two sections visible
to three while its inputs got **narrower**, 780px → 520px.

**The lesson the slice earned: a guard that only watches where the last
stray was found is not a guard.** The first source guard walked `app/`
and passed — while `WorkspacePlaceholder`, a *component*, held a tenth
`<main>` that Brain and Settings both rendered through. Widened to walk
`components/` too, and mutation-checked three ways: a page reclaiming
its own `<main>`, a component doing the same, and the container
reverting to a fixed 1,600px. All three fail the suite.

### The crypto Overview explains the situation; the other tabs prove it

Measured from product use: *"much better than the old dossier, but it
still feels like a well-organized evidence report rather than a CIO
product. The main problem is hierarchy, not styling."* Desktop
**2,495px**, mobile **4,085px**, a **1,362px** Key Facts block
dominating the page, and the conclusion abstract and repeated.

**The sentences moved to the backend, because the frontend may not
author them.** A hero line reading *"momentum is supportive, but
MOVRvest cannot establish the issuance rule"* is economic
interpretation, and Invariant 10 forbids this side inventing it. So
`app/api/models/crypto_brief_adapter.py` composes the brief — current
view, what blocks progress, what would change it, and the one-line
setup — by **quoting** the layer that owns each finding: a `Driver`
from the intelligence snapshot, an `UnresolvedQuestion` from the
committee that raised it, a material uncertainty from the assessment, a
`WatchItem` from the intelligence layer. It adds headings, an order and
one connective, and a test asserts every emitted clause appears
verbatim in its source sentence.

**It is Communication and not the CIO, and the guard said so first.**
Written under `app/cio/`, it was rejected by the crypto intelligence
layer's own import test: nothing in `app/cio/` may import
`crypto_intelligence`, because what is *happening* must never reach
what is *decided*. The guard was right and the placement was wrong.
This layer reads a decision already made and explains it.

| | before | after |
|---|---|---|
| desktop Overview | 2,495px | **1,572px** (target 1,300–1,700) |
| mobile Overview | 4,085px | **2,812px** (target < 2,600) |
| metrics visible by default | 16 | **6** |
| `INVESTIGATE` rendered | 2× | **1×** |
| "No capital action is suggested" | 2× | **1×** |
| source-disagreement essays open by default | 2 (343 and 414 chars) | **0** |
| grid row heights | 1,362px / 1,362px | 589px / 736px |

**Three defects the corpus forced, all found on the first live run.**

1. **One splitter may not be pointed at two sentence shapes.** A
   decision sentence qualifies itself — *"No mechanical issuance rule is
   held. That is a statement about what this platform has read…"* — so a
   full stop or colon separates claim from support. A driver's colon
   carries a **category**: *"Token economics: Hyperliquid Reports Strong
   Revenue…"*. Splitting it left the brief asserting *"Token economics"*
   as a finding, and TAO rendered that non-sentence **twice in one
   block**. Drivers and watch items are now quoted whole, and even for
   decision sentences the colon cuts only before a lowercase
   continuation — a capitalised right-hand side is a title.
2. **A side degrades to fewer clauses and never vanishes.** ETH's second
   supportive clause could not be safely lowercased, and refusing the
   whole side left its setup **opening on a blocker** while the block
   below still listed what supported the case.
3. **Case is never repaired.** Joining quoted clauses needs the second
   lowercased, and lowercasing one that opens on a proper noun corrupts
   it. The joiner lowercases only openers on an explicit closed-class
   list and otherwise emits **two intact sentences** — ADA reads *"The
   asset has moved +36% over a month. Committee judgment is off…"*
   rather than *"…but Committee judgment is off"*.

**Two things the brief asked for are not held, and are named as
absent.** There is no high, no low and no baseline volume anywhere in
the payload — the only "all-time" figures in the corpus are event
headlines about *open interest*, a different quantity — so *position
within the recent measured range* and *volume relative to normal* are
stated as absences. No conditional scenario is worded for the same
reason: *"continuation would be better supported if…"* is a forecast
and no layer beneath this one establishes one.

**Exposure has three states, not two.** A recorded share, an asset the
completed cycle did not contain (**HYPE is not among the 14 holdings**),
and no readable cycle at all. The middle is a finding and reads *"Not
held"*; the last is silence. Neither renders as 0%.

**`BLOCK_LIMIT` is 2, measured not chosen**: at three the mobile
Overview ran 3,239px and the brief alone was 1,021px. A capped block
says how many findings it holds back.

**Mobile lands at 2,812px against a 2,600px target** — 8% over, and
recorded rather than hidden. The remaining ~210px costs either a
metric's provenance line, one of the three developments, or the
exposure receipt wording; all three were judged worth more than the
target.
