# Read-only is a property of the graph, and evidence moves whole or not at all

**Status: built, BQ16. Two boundaries: read-only surfaces made
structurally incapable of acquisition, and an append-only promotion
operator for observations the pipeline already produced. No model call,
no credit spent, nothing re-observed. Production `data/statements`
untouched — promotion was proven against copies only.**

---

## Part A — read-only purity

### 1. The accidental acquisition path, exactly

`movrvest financials ALL`, 2026-08-16, one command documented *"Read-only
and free … never observes"*:

```text
FinancialsCommand.run
  └─ PlaybookSelectionService.select("ALL")
       ├─ CompanyKnowledgeService.knowledge()          ← the ACQUIRING door
       │    └─ resolve → EDGAR fetch → gpt-5 reading   → data/knowledge/ALL…json
       │                                                 (22:10:38Z, one paid call)
       └─ grounded refused (1 reading < quorum 5)
            └─ _fallback → WatchlistService.find_symbol
                 └─ EtoroClient.get("/api/v1/watchlists")   ← the BROKER door
                      → data/evidence/etoro/…/watchlists/…  (22:10:49Z, 22:11:22Z)
```

Two doors, not one — and they fire differently. The model spend happened
**once**, because `knowledge()` acquires only for a document with no
stored reading. The watchlist fetch fired **on every invocation**: the
grounded route stayed refused (one narrative reading is below quorum), so
every render of `financials` fell back through the broker. Two archived
watchlist payloads, thirty-three seconds apart, are the two runs.

**Why a read surface wanted playbook selection at all**: only to derive
the governing `FinancialModel` via `model_for(playbook)` — one enum and
one sentence. It bought that enum with a filing read and a broker fetch.

**A non-acquiring selection door already existed** — the dossier's
earned-playbook section runs `select_grounded` over the established
(store-only) understanding, with three honest states and no industry
fallback. `financials` simply did not use it.

### 2. The audit — every surface that claims to be read-only

Every command and route describing itself as read-only / free / stored /
"asks no model" / "stores nothing", classified by what its dependency
graph can actually reach:

| Surface | Claim | Class |
|---|---|---|
| `financials` (before this slice) | "Read-only and free … never observes" | **CAN ACQUIRE — CONTRACT DEFECT** (repaired here) |
| `GET /crypto/{symbol}/dossier` | "**And it acquires nothing.** Every service is opened at its read-only…" | **CAN ACQUIRE — CONTRACT DEFECT** (recorded, not repaired) |
| `assessment`, `committees`, `committee-judgment`, `considerations`, `judgment-history`, `intelligence-journal`, `supply`, `crypto-events`, `crypto-market`, `crypto-playbook`, `crypto-quality`, `translations` | read-only / stored | **PURE READ** — store doors only |
| `statement-shape`, `statement-audit`, `primary` | "costs a fetch, asks no model, stores nothing" | **CAN ACQUIRE — INTENTIONAL** (the fetch is the declared function) |
| `issuance` | "Read-only, scores nothing" | **CAN ACQUIRE — INTENTIONAL**, wording ambiguous: it fetches chain state, which "read-only" does not advertise the way `primary`'s "costs a fetch" does |
| `knowledge`, `statements`, `understanding`, `archetype`, `playbook`, `observe`, `observe-statements`, `acquire` | none claimed | **CAN ACQUIRE — INTENTIONAL** (the platform's declared acquisition family) |
| dossier / research pages (`CompanyUnderstandingService`, `CompanyFactsService`, `CompanyResearchService`) | a page view acquires nothing | **PURE READ** — `established()` and `stored()` doors, already guarded by raising stubs |

**The crypto dossier finding is the root cause of main's red CI.** Line
153 constructs the raw `IssuanceRuleProvider()` — fetch-on-call for
BTC/ETH/ADA/SOL — where `CachedIssuanceProvider` exists and is used
elsewhere. The seven pre-existing test failures are those fetches timing
out against `api.blockchair.com`. Scope guard says crypto stays
untouched, so this is **classified and recorded**: the same defect class
as `financials`, one line, waiting for its own slice.

### 3. The repair — dependency construction, not flags

`app/services/stored_playbook_selection.py`: the grounded route over
`CompanyKnowledgeService.established()` — the same canonical
`select_grounded` rule, reached through the read-only door — and **no
fallback route at all**, because the industry route's inputs (broker
watchlist, provider profile) arrive by acquisition. Where nothing
grounded is established, the generic model governs and the sentence says
exactly why, and what the operator's alternatives are (`movrvest
playbook` for the full selector, `--model` for explicit inspection).

`FinancialsCommand` now constructs `StoredPlaybookSelection`. No flag
anywhere; the acquiring selector is simply not in the graph.

**One rendered difference, stated rather than hidden**: an on-book
company with no grounded playbook whose Yahoo industry says "bank" was
previously governed BANK via the acquired fallback; the read surface now
governs GENERIC with the absence worded. BQ2 measured model selection
inert for bands and scores; what changes is which questions the
`financials` screen asks, and `--model bank` remains the explicit way to
inspect the other language.

### 4. The pin — `tests/test_read_only_purity.py`

- **Structural**: the module ASTs of `stored_playbook_selection` and
  `financials` are walked for **call-position** attribute names —
  `knowledge`, `select`, `fetch`, `observe`, `statements`, `extract`,
  `resolve`, `find_symbol` all forbidden (`established` asserted
  present); acquiring modules forbidden from their import lists. A
  future dependency that reintroduces an acquiring fallback fails here
  before it runs.
- **Behavioural**: every acquiring door monkeypatched to raise
  (`knowledge`, `statements`, `observe`, watchlist `get`/`find_symbol`,
  `EtoroClient.get`, `PrimarySourceResolver.resolve`), **credentials
  deliberately present** — the boundary must hold because acquisition is
  unreachable, never because a key was missing — and the command run
  with evidence absent (renders the absence, exit 1) and present (full
  render, exit 0). Both complete; no trap springs.

## Part B — genuine observation promotion

### 5. Inventory, and the durable copy

**All 23 paid statement observations survive**, every one a genuine
`FinancialStatementObservation` — schema 3, `read by gpt-5`, its own
`PrimarySource` and dated `Provenance`, dated anchors with 3-cell rows.
None reconstructed from prose; none fabricated.

| Run | Company | Filing | Observations | Read at (UTC) |
|---|---|---|---|---|
| bq11 (BQ11+BQ12) | KO | `0001628280-26-010047` | **5** | 20:43–21:05 |
| bq13 | ALL | `0000899051-26-000031` | **5** | 21:23–21:24 |
| bq13 | TSLA | `0001628280-26-003952` | **5** | 21:23–21:24 |
| bq13 | WMT | `0000104169-26-000055` | **5** | 21:23–21:25 |
| bq8 (probes) | ALL, KO, TSLA | same filings | **1 each** | 20:04–20:05 |

Copied byte-unchanged from `/tmp` to
**`data/experiments/statement-observations/{bq8,bq11,bq13}/statements/`**
— inside the repository, tracked by git, outside every store any service
reads (`evidence_path("statements")` is `data/statements`). MD5 before
and after, identical all seven:

```text
89c0527c6d0e08b4bc3821837915dc70  bq8/ALL     ed75bb47915cbc9a2f905b9de230238b  bq8/KO
d5b3348ce04e14e32277d37b61c4655d  bq8/TSLA    9b0a6322e8efc945f12437a3401827ad  bq11/KO
0aab292d178eef82aa3861c312e384fd  bq13/ALL    bf36e53e20ffda7268477167c3cea9e4  bq13/TSLA
1fc1318fb6a78ef5e4ac40c6c6dd9920  bq13/WMT
```

Reproducible without a model call? **No** — an LLM reading cannot be
regenerated offline, which is exactly why the artifacts are now durable.
Enough provenance to append after supersession? **Yes** — measured in §8
by appending them.

**The accidental ALL narrative reading** (`data/knowledge/ALL.…json`,
md5 `ae494c05f2261830f0879bf502a7cd11`, schema 14, 4 segments,
relationships asked, 22:10:38Z): a **distinct, valid observation** in a
different stream — not a duplicate of any statement observation and not
comparable with one. Quorum-relevant: it is 1 of 5 toward ALL's
narrative quorum, the corpus's first schema-14 reading. **Kept.** A valid
observation does not become false evidence because the acquisition was
accidental; the audit trail stands — it was acquired in violation of a
read-only contract, BQ15 §10, and Part A is why it cannot recur.

### 6. Same schema is not same contract — the amended gate

The first cut of the importer gated on `STATEMENT_SCHEMA_VERSION`, and
BQ16's own measurement refuted it: schema 3 contains observations
produced under materially different semantic contracts, because
`6c96ea0` widened `CONCEPT_LABELS` under no bump — exactly as `301cfdf`
repaired the parser under one. **The missing identity is the vocabulary
contract**: the schema says what a reading was shown and asked; nothing
says which labels it was permitted to accept.

**The contract identity built**: a deterministic **per-concept
vocabulary fingerprint** — sha256 over the concept and its normalised,
sorted accepted forms (`concept_vocabulary_fingerprint`, in the module
that owns `CONCEPT_LABELS`). Per concept, not per vocabulary, because
vocabulary moves one concept at a time: the *only* change in the whole
schema-3 era is `TOTAL_REVENUE` (`ba55a427097938f3` before `6c96ea0`,
`3cdbddd6a1fcf0e6` today, derived from the historical blob itself);
every other concept is byte-identical across the era. Git commits were
rejected as the identity — unrelated code changes would manufacture
false incompatibility — and model name and timestamp identify nothing
about interpretation. Two honest limits are stated in the docstring:
`TOTAL_EQUITY`'s `names_its_own_equity` rule is code, not a constant;
and parse behaviour is not fingerprinted, because an anchor is checkable
against the immutable document (the statement audit's approach) — the
vocabulary is the one axis neither in the schema nor checkable from the
record.

**The reconciled evidence sets.** BQ16's 20-observation simulation =
bq13's 15 + the bq11 artifact's 5 — and that artifact holds **both**
BQ11's single reading (obs 0, 20:43Z) and BQ12's four (obs 1–4,
21:04–21:05Z): one file, one producing contract, two experiment names.
Nothing was withheld; the directory name obscured that BQ12 was already
in both the simulation and the recommendation.

**The full compatibility table** — ruled without reading any Business
Quality outcome:

| Obs | Experiment | Read at (UTC) | Filing | Tree | Vocabulary | Compatible with main? | Ruling |
|---|---|---|---|---|---|---|---|
| ALL ×1 | BQ8 | 16 Aug 20:04:36 | `0000899051…031` | pre-`6c96ea0` (research/funded-recovery-baseline) | pre-widening | **PROVEN COMPATIBLE** — located labels accepted today; absences name only unchanged concepts | promote |
| KO ×1 | BQ8 | 16 Aug 20:05:02 | `0001628280…047` | same | pre-widening | **PROVEN INCOMPATIBLE** — records *no figure for `total_revenue`* under the pre-widening vocabulary | refuse |
| TSLA ×1 | BQ8 | 16 Aug 20:04:11 | `0001628280…952` | same | pre-widening | **PROVEN COMPATIBLE** — same grounds as BQ8 ALL | promote |
| KO ×1 | BQ11 | 16 Aug 20:43:23 | `0001628280…047` | widened working tree, committed as `6c96ea0` | today's | **PROVEN COMPATIBLE** | promote |
| KO ×4 | BQ12 | 16 Aug 21:04–21:05 | same | main `10f4904` | today's | **PROVEN COMPATIBLE** | promote |
| ALL ×5 | BQ13 | 16 Aug 21:23–21:24 | `0000899051…031` | main `6d2fecc` | today's | **PROVEN COMPATIBLE** | promote |
| TSLA ×5 | BQ13 | 16 Aug 21:23–21:24 | `0001628280…952` | same | today's | **PROVEN COMPATIBLE** | promote |
| WMT ×5 | BQ13 | 16 Aug 21:23–21:25 | `0000104169…055` | same | today's | **PROVEN COMPATIBLE** | promote |

Nothing lands in COMPATIBILITY UNPROVEN: the evidence base is unusually
strong, and it is evidence, not memory. **A located anchor proves its
producing vocabulary accepted its label** — `matches_concept` gates
extraction — so every bq11/bq12/bq13 observation proves its own
contract through the anchors it carries; BQ8's own report is the
*measured* proof its vocabulary
refused that label (its negative control §5); and
`git diff 9ed6d7d..HEAD` shows exactly one `CONCEPT_LABELS` change in
the era, so every other concept's absence claims are era-invariant.

**BQ11 and BQ12 receive the identical ruling, structurally.** Their five
observations live in one artifact under one manifest entry; eligibility
is a function of (observation, ruled contract, today's contract) and the
module is AST-pinned unable to read a band, a score or a consensus — so
withholding BQ12 for leaving KO tied is not merely forbidden, it is
inexpressible. Pinned twice more in tests: two same-contract readings
whose figures point opposite ways receive the same ruling, and the
eligibility module names no analytical concept.

**Why BQ8's KO reading is incompatible, precisely**: before `6c96ea0`,
`Net Operating Revenues` could not establish `TOTAL_REVENUE`; after it,
that exact label can. BQ8-KO's *"no figure located for total_revenue"*
was a true claim under its contract and is not a claim today's contract
would make of the same filing — measured: pooled, it turns the honest
5-vs-5 tie into a 6-of-11 settled absence. Its located facts
(`Gross Profit`, `Operating Income`) are fine; an observation travels
whole or not at all, so the observation is refused.

### 6b. The manifest, and how the importer refuses

The historical observations cannot retroactively carry a fingerprint
they never had. The narrowest honest mechanism is the brief's own: a
**promotion manifest** beside the artifacts
(`promotion-manifest.json`), recording per artifact its **sha256**, the
**per-concept fingerprints of the producing vocabulary**, and the
**evidence** for that ruling (commits, the anchor proof, BQ8's negative
control). The manifest is an operator ruling *about* the bytes, tied to
them by hash — never a retro-stamp on the record.

`movrvest statement-import` now rules **per observation**, worst answer
first, and the dry run prints every ruling:

| Ruling | When | Default |
|---|---|---|
| **duplicate** | equal in every field to a target observation | skipped |
| **incompatible** | a located label today's vocabulary refuses (provable from the record alone), or an absence whose ruled producing fingerprint differs from today's for that concept | refused, worded |
| **compatibility unproven** | no manifest, no entry, or a fingerprint missing for an absent concept | **refused — not knowing is not knowing** |
| **compatible** | every located label accepted today, every absence ruled produced under today's vocabulary | appendable |
| *(artifact-level)* refused | malformed, wrong schema, or **hash ≠ manifest** (the artifact changed after its ruling) | refused whole |

An arbitrary same-schema store now imports **nothing**: deserialization
is admission to inspection, never to a consensus.

### 7–8. The complete, non-selective simulation

Every surviving artifact through the same rule — bq8, bq11, bq13, no
experiment chosen or skipped — against a copy of production carrying
BQ15's supersession. Production untouched, `git status` clean.

**Appended: 22.** bq8-ALL (1), bq8-TSLA (1), bq11-KO (5), bq13
ALL/TSLA/WMT (15). **Refused: 1** — bq8-KO, *"the reading records no
figure for total_revenue under a vocabulary that differs from today's
for that concept."* Duplicates: 0. Unproven: 0. Re-applying appends 0.

| | active | answered | band |
|---|---|---|---|
| ALL | 5 → **11** | 0 → 3 | UNKNOWN → **HIGH 80** — revenue 6/6 agreement across BQ8 and BQ13 readings |
| TSLA | 0 → **6** | 0 → 3 | UNKNOWN → **LOW 40** — 6/6 |
| WMT | 5 → **10** | 0 → 2 | UNKNOWN → **LOW 40** |
| KO | 5 → **10** | 0 → 0 | UNKNOWN → **UNKNOWN** — `total_revenue` an honest 5-vs-5, `by_majority=False`; gross profit and operating income 10/10 |
| other 20 | unchanged | unchanged | unchanged |

**KO is UNKNOWN and UNKNOWN is accepted.** The tie is the true state of
ten authoritative readings under one contract; the incompatible eleventh
that would have "settled" it is exactly what the gate exists to refuse.

Aggregate: **HIGH 4 · MEDIUM 4 · LOW 3 · UNKNOWN 13** (from 3 · 4 · 1 ·
16).

### 9. Model readings avoided

**22 promoted without a model call.** Re-earning the same evidence
through `observe-statements` would cost 20 readings (four quorums), and
the two BQ8 probes would cost 2 more to reproduce.

### 10. The exact production write recommended next

Three commands, after the ruling — **not executed in BQ16**:

```bash
movrvest statement-import data/experiments/statement-observations/bq13/statements --apply
movrvest statement-import data/experiments/statement-observations/bq11/statements --apply
movrvest statement-import data/experiments/statement-observations/bq8/statements --apply
```

Order is immaterial; each is idempotent. Expected, measured on the
copy: 22 appended, bq8-KO refused with its reason printed, ALL → HIGH
80, TSLA → LOW 40, WMT → LOW 40, KO → UNKNOWN with the tie on the
record, bands HIGH 4 · MEDIUM 4 · LOW 3 · UNKNOWN 13, zero other
companies moved.

## Recorded, not solved

- **The crypto dossier's issuance fetch** (§2) — one line, the declared
  contract's one violation, and the cause of main's red CI. Its own
  slice.
- **`issuance`'s "Read-only" wording** understates a chain fetch.
- **KO's tie** waits on the vocabulary limb BQ14 deferred; promotion
  cannot and does not touch it.
- **The behavioural purity test covers `financials`**, the defective
  surface; the pure-read commands in §2 were classified by graph
  inspection, not each executed under traps.
- **New observations still do not carry their producing fingerprints.**
  The manifest solves transport for the historical corpus honestly; the
  durable fix — stamping the vocabulary fingerprints on the observation
  at acquisition, the `located_among` precedent again — belongs to the
  acquisition path and is deliberately not smuggled into an importer
  slice. Until it lands, every future isolated experiment needs a
  manifest authored from repository evidence, exactly as these three
  were.
- **The manifest's trust boundary is the operator**, the same boundary
  `--supersede` and `--apply` already stand on. The importer verifies
  what a manifest can be checked for — hashes against bytes,
  fingerprints against today's vocabulary — and takes the producing
  fingerprints as the operator's evidence-backed testimony, which is
  what the brief's "evidence-backed compatibility ruling" is.

## Scope compliance

No LLM call · no credit spent · nothing re-observed · statement facts,
supersession semantics, quorum, agreement, Business Quality, vocabulary
and schema all untouched · HON, Citigroup, financial-company question
semantics untouched · no crypto analytical logic changed (one crypto
defect *classified*) · no UI · PR #145 untouched · production
`data/statements` byte-identical — promotion proven against copies only.
