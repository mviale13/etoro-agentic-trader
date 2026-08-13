# Would the CIO decide differently on the earned classification? — measured, nothing built

**Status: research only, measured 2026-08-13 on the live pipeline with
a disposable harness (`tools/decision_convergence.py` — two in-process
patches, no journal, no store writes, no runtime consumer). Nothing
here reroutes production.** Ruled after the Equity Dossier Fidelity
measurement; ED1's live acceptance remains credit-blocked and ED1's
relationships played no part here (decision-neutral by its own ruling).

The research question:

> If the Artificial CIO consumed the classification/playbook MOVRvest
> has actually earned from Business Understanding, rather than the
> legacy industry route, which investment questions, assessments and
> decisions would change — and are those changes better supported?

The finding, in one sentence: **route B changes what three companies
are *called* and which analysts are *asked*, and changes not one
score, committee stance, conviction point or decision anywhere in the
corpus — because the grounded intelligence that matters to decisions
(statement-grounded quality) already flows through a
playbook-independent seam, and the one place the financial model would
genuinely diverge (a grounded bank) has no statements at quorum for
the model to consume.**

---

## 1. Method

Route A: the production pipeline exactly as it runs (industry
`ResearchStrategyFactory`, pipeline `quality_of` at its default
model). Route B: identical evidence, portfolio state and pipeline,
with two harness patches — the factory answers with the grounded
playbook, and `quality_of` receives `model_for(grounded_kind)`.
`ExecutivePipeline(journal=None)`: no decision history written.

Corpus and classification provenance:

- JPM, VOW3.DE — grounded route read through the store's own door
  (schema-13-current entries).
- BNP.PA, DIS, NVDA, CAT — the store's current protocol restores
  nothing (their entries are schema-11 archives awaiting the funded
  re-observation), so route B's classification was derived from the
  archived readings, **labelled as such**: for these EDGAR /
  single-document filers the text shown was bit-identical across
  11→12, so their segment, size and description claims are the
  platform's own established readings. A measurement may consume a
  labelled archive; production consumes only the store door, and does
  not change here.

## 2. The matrix

| | JPM | BNP.PA (held) | DIS | NVDA | CAT | VOW3.DE |
|---|---|---|---|---|---|---|
| Current classification | *(no card — off book)* | **unclassified** | general_corporate | semiconductor | *(no card — off book)* | general_corporate |
| Grounded classification | diversified | **bank** | diversified | industrial | diversified | refused (33% coverage) |
| Analysts asked A→B | 4→4 | **4→3 (cash_flow dropped)** | 4→4 | 4→4 | 4→4 | unchanged |
| Financial model A→B | generic→generic | **generic→bank** | generic→generic | generic→generic | generic→generic | unchanged |
| Model questions | awaits statements | **bank set — awaits statements** (5 generic ⇄ bank set, all unanswerable either way: no quorum) | 3 of 5 answered — identical | awaits statements | awaits statements | unchanged |
| Evidence gained | none | **an honest next-evidence pointer**: the bank's questions now name the bank's statements | none | none | none | none |
| Evidence lost | none | none — the dropped cash-flow analyst produced no findings over BNP's null provider fundamentals | none | none | none | none |
| Assessments changed | none | none | none | none | none | none |
| Scores (Q/V/S/E) | identical | identical (62/…) | identical (80/…) | identical (80/…) | identical | identical |
| Committee consequence | identical | identical (IC strongly_positive on 3; RC positive on 1) | identical | identical | identical | identical |
| Conviction A→B | 64→64 | 71→71 | 76→76 | 73→73 | 64→64 | 77→77 |
| Decision A→B | INVESTIGATE→INVESTIGATE | PREPARE→PREPARE | RECOMMEND→RECOMMEND | RECOMMEND→RECOMMEND | INVESTIGATE→INVESTIGATE | RECOMMEND→RECOMMEND |
| Interpretation | degenerate (no market evidence off book) | **the critical case — see §3** | pure relabel | pure relabel | degenerate off book | routes identical by construction |

Reason classification for every difference found: BNP.PA — *stops
asking an inappropriate generic question* (a bank's cash-flow analyst)
and *asks a more economically appropriate question set* (BANK's),
which is **unanswered because evidence is missing** — the exact
category the ruling names as a possible improvement without any score
moving. DIS/NVDA — *changed applicability of nothing*: same analysts,
same model, same questions; a label. Nowhere did a score change from
different applicability, nowhere did committee evidence change,
nowhere did conviction or the decision state move.

## 3. BANK, the critical test — measured honestly

BNP.PA under route B stops being "unclassified", drops the cash-flow
analyst its own bank playbook already declares inapplicable, and
selects `FinancialModel.BANK`. And then: **no statements at quorum, so
every bank question awaits the bank's own statements** — exactly as
every generic question already did. The comparison the ruling asked
for resolves as: *better question, unanswered because evidence is
missing* — versus, today, *the same absence under generic questions*.
Nothing is answered either way; what improves is what the platform
would honestly say it is waiting for.

Two standing boundaries cap what convergence could deliver even after
statements arrive: the pipeline's own comment records that the
financial model is deliberately not resolved in the decision path
("a company reaches the default"), and `FINANCIAL_DOMAIN_BOUNDARY.md`
holds that BANK's deeper demands (CET1, LCR) are unreachable until a
Prudential Understanding layer exists. The bank case justifies
*visibility* convergence today and would justify decision-path
convergence only when a grounded bank has statements at quorum — a
state no corpus company is in.

## 4. The five answers

1. **Is production making materially different decisions because it
   does not consume grounded understanding?** No — measured, not
   assumed: zero changes in scores, committees, conviction or decision
   across six companies. The decisive reason is architectural and
   already shipped: grounded (statement-based) quality reaches the
   score through `quality_of`, which is playbook-independent, and
   provider signals drive the rest identically in both routes.
2. **Where the result changes, better / different / worse?** BNP.PA:
   better-supported (appropriate question set, honest waiting state,
   nothing lost — the dropped analyst had nothing to say). DIS, NVDA:
   merely different at decision level — but the *label* difference is
   exactly the investor-facing defect the fidelity audit ranked first
   (a held bank rendered "Not classified" under a false sentence).
3. **Does BANK justify convergence now?** Decision-path: no — no
   answerable bank question exists (no statements at quorum), so
   convergence would change declarations, not answers. Visibility: yes
   — the earned *Bank* classification and its honest question set are
   established intelligence the investor cannot currently see.
4. **What stays stranded even after grounded selection?** The
   financial question states themselves (answered / awaiting —
   CLI-only today), the statements domain for every company below
   quorum, ED1 relationships (decision-neutral by ruling), and the
   schema-11 archive corpus until the funded re-observation restores
   it through the store door.
5. **The smallest justified investor-facing slice** — and the §23
   sentence completes only for display, not rerouting: *after this
   change, the investor can see the classification MOVRvest actually
   earned and the financial questions that follow from it — a held
   bank reads Bank, with its bank questions honestly awaiting the
   bank's own statements — which they cannot reliably do today,
   because the dossier's card asserts the platform knows nothing where
   it knows Bank at eleven readings.* That is the fidelity audit's
   slice 1 (+4), unchanged by this measurement. **For decision-path
   convergence the sentence does not complete from measured
   consequences — recommended: no production decision change now.**
   Re-measure when any grounded bank reaches statement quorum; that is
   the trigger condition this experiment leaves behind.

## 5. Traps recorded

- The pipeline's `quality_of` call ignores `model_for` by documented
  design; any future convergence slice must decide that coupling
  explicitly rather than inherit it silently.
- The convergence corpus is hostage to the knowledge store's protocol:
  under schema 13 only re-observed companies restore, so a measurement
  (or a future selector) that reads the store door sees a *thinner*
  corpus than the platform has actually read. Fund the re-observation
  before re-running.
- JPM and CAT produce degenerate decision comparisons off the book —
  classification-level convergence measures fine; decision-level needs
  book membership.
