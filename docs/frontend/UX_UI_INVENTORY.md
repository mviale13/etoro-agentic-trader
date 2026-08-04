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

## 5. What was NOT changed

No source files were modified for this inventory. The next action is to review
this document, then execute Slice 1. Per the working agreement, start a new
session at each slice boundary.
