# Handoff — 2026-08-12

Everything is committed and green. Nothing is open. Start a fresh window
here.

## State

`main` carries the Fund Analytical Boundary (F1) on top of `2375f34`
(merge of #120). Gates at F1: ruff clean, mypy clean (567 files),
**2121 tests passing**, frontend builds, HEAD verified in isolation.

**F1, briefly**: a fund cannot receive evaluative meaning from a
company question its playbook does not ask — IB01.L no longer scores
"Business quality LOW (40)" from a structural dividend zero. The fix
was membership (`has_no_company` gains ETF; the boundary's six
consumers already existed) plus one conflated flag split. The TER the
provider already returned is retained as `fund_cost` (a dated fact, no
score). **F2 is not started**; its question is *"what am I actually
buying when I own this fund?"* and its ground is
`docs/architecture/FUND_EVIDENCE_RESEARCH.md`.

**E1, briefly** (2026-08-13): a wordless named segment is now asked
against the untagged prose of its own package — the shape Volkswagen's
management report ships in — under the same span and ownership
contracts, recorded with provenance naming the untagged text.
Knowledge **schema 12**: the schema-11 corpus reads as absent until
re-observed (`movrvest observe`, per symbol; JPM and VOW3.DE are
already re-read). The `normalised`/`_indexed` accent mismatch is
fixed — German and French quoted spans ground now. **E2 (attributed
category corroboration) and the dossier-fidelity slices are NOT
started**; their grounds are `EVIDENCE_PROPORTIONALITY.md` and
`EQUITY_DOSSIER_FIDELITY.md`.

**ED1, briefly** (2026-08-13): `EconomicRelationship` inside Business
Understanding — the filer's own stated dependence of one business on
another, quantifiers intact, consensus over asked readings, schema 13
with a cross-schema read that keeps the 12-corpus valid,
decision-neutral by test, rendered on the equity dossier's segments.
⛔ **BLOCKED on OpenAI credits for live acceptance** (re-confirmed
2026-08-13: three fresh 429 `credit_balance_exhausted`). Once Marcos
funds the account, run **`movrvest observe VOW3.DE --to 10`**,
**`movrvest observe CAT --to 10`**, **`movrvest observe DIS --to 10`**
— `--to` is required: the schema-12 corpus counts toward the quorum
under ED1's cross-schema read, so a plain `observe` stops on the count
and takes no asked readings. Five asked readings each; the consensus
and dossier then render whatever the readings establish, with no
further code change. CAT's verdict is genuinely open. DIS must stay
empty (the control). **Trap: `observe` exits 0 and prints the stored
consensus even when every reading attempt 429'd — read the log, not
the exit code.**

Merged since the last handoff, in order:

| PR | What |
|---|---|
| `#113` | Judgment history — a number moving is not a conclusion moving |
| `#114` | The committee protocol, discovered rather than designed |
| `#115` | Committee #2, chosen by measurement, and the matrix it makes |
| `#116` | The committee portfolio — everything beside, nothing combined |
| `#117` | Investor Assessment — the strongest useful statement |
| `#118` | Hermetic evidence execution |
| `#119` | Zero Fake Meaning — economic role-awareness in Investor Assessment |
| `#120` | The Crypto Dossier — the first investor-usable crypto surface |

## Where the work is

The judgment arc is now five layers deep and each one is
decision-neutral:

```text
Evidence → Finding → Temporal Finding → Synthesis        (knowledge)
Eligible findings → Committee → Judgment                 (judgment)
Judgment → append-only history → transitions             (memory)
Every registered committee's latest judgment, side by side (matrix)
Evidence + judgments → what can usefully be said          (assessment)
```

**Everything above the assessment layer is explicitly parked**: the
Artificial CIO recommendation layer, committee aggregation, weighting,
agreement percentages, an overall crypto score, thesis, portfolio
coupling and any favourable/adverse mapping. The owner's standing
instruction is to observe good assessments across the corpus *first* and
choose the next abstraction from evidence. Do not start any of it
without a new ruling.

**Asset Quality stays off.** Crypto quality is UNKNOWN for every asset,
quorum 2, declined three times. Do not try to earn factor #2.

## What to read first

1. `.claude/…/memory/MEMORY.md` — the first nine lines are the crypto
   arc in order, newest first.
2. `docs/architecture/CRYPTO_DOSSIER_UI.md` — the newest surface, and
   `docs/architecture/INVESTOR_ASSESSMENT.md` — the layer beneath it
   (its §6, Zero Fake Meaning, is Invariant 10).
3. `docs/architecture/HERMETIC_EVIDENCE.md` — read before writing any
   test that touches evidence.
4. `CLAUDE.md` — current through `#120`.

## Six rules this arc established, in the order they cost the most

1. **A number moving is not a conclusion moving.** Three axes on every
   transition — the answer, the observation count, the evidence — and
   evidence moving under a steady answer is the *ordinary* case. Proved
   live: HYPE's evidence was byte-identical across three judgments while
   the answer moved twice.
2. **The framework may know Committee X answered Y with verdict Z; it may
   never know what Z means.** One line broke it (`posture_of` read
   `MECHANISM_EVIDENCED` and decided it meant presence). The extraction
   was a *relocation* — the logic was already generic, only the
   vocabulary was not.
3. **An analytical call must declare an evidence set, not just a
   subject.** `judge("ADA")` resolved its own evidence from a path
   literal, and a poisoned cache flipped the verdict with the caller
   declaring nothing. This was the root cause of five separate
   clean-checkout failures.
4. **`CONFLICTED` is a fact about two readings; "we cannot tell you
   anything" is a fact about the investor's question.** Internal
   epistemic vocabulary is not an investment conclusion, and a
   difference between sources is only material when it changes what can
   responsibly be said.
5. **A prose failure is a presentation failure.** HYPE lost a complete
   `mechanism_evidenced` because the drafted sentence used the word
   *buy*. Structural checks now finish before prose is read; the
   validator is untouched.
6. **`EvidenceStanding` is a corroboration axis, not a gate a committee
   may borrow.** Every issuance rule stands at `CLAIMED` because a
   chain's own parameters have no second source — requiring
   `ESTABLISHED` silenced all three answerable assets.
7. **A grounded fact may travel upward without its economic
   interpretation travelling with it** — Invariant 10, Zero Fake
   Meaning. One sentence keyed by *quantity* rather than by asset
   (*"it bounds how far the holder's share can be diluted"*) is true of
   a network asset and inverted for a claim on a reserve. The executive
   layer must not invent the missing half; it quotes the contract that
   owns the question, or states that the interpretation is not
   established.
8. **A declaration that no code path can reach is not a rule.**
   `DECLINED` documented itself as the place an archetype refuses a
   question *no lens can refuse*, and `applicability_for` returned
   `ASK` before reaching it — so **13 of 13 entries were unreachable**
   and could only re-word refusals that would have happened anyway.
   Dormant since S3, found only by asking the table to do the one thing
   it claimed.

## Traps

- **`git archive HEAD` in isolation, every time.** The gitignored-cache
  trap fired **five times**. `#118` fixed the *cause* — the evidence
  root is now one owner and the suite redirects it — so a test can no
  longer read your machine by accident. Keep running the isolation check
  anyway; it is the only thing that caught occurrences 4 and 5.
- **A module that explains what it refuses fails a text search for the
  thing it refuses.** Use `reachable()` from `tests/reachability.py`, or
  prefer a behavioural test. Seven occurrences so far.
- **Resolve a path at construction, never in a signature.** Ruff's B008
  caught three stores freezing the evidence root at import — the same
  class of bug the slice was fixing.
- **A `git commit --amend` after a hook-aborted commit silently amends
  the previous merged commit.** Check `git log` after any amend. If the
  hooks reformat, run `ruff format .` yourself first, then `git add -A`.
- **`data/` is gitignored except `data/knowledge/`.** A fresh clone has
  no evidence and honestly says so; every crypto surface is empty until
  acquisition has run.

## What is live and what it costs

Two explicit spends, and nothing else fetches or asks a model:

```bash
movrvest acquire            # provider stores, events, one journal capture
movrvest judge [SYMBOL]     # runs both committees, appends judgment events
```

Read-only surfaces:

```bash
movrvest assessment ETH               # what can usefully be said
movrvest committees BTC               # every committee, side by side
movrvest committees [SYMBOL]          # every committee's conclusion
movrvest judgment-history BTC --evidence
movrvest crypto-intelligence BTC --evidence
```

The investor-facing surface is `GET /crypto/{symbol}/dossier` (#120),
rendered by the web app — ~19ms of stored doors, no model, no fetch. The
equity dossier at `/executive/{symbol}/dossier` is a different
composition (a *decision*, ~12s of brain pipeline) and the two do not
share an endpoint.

Two model seams are off by default and share the writer's provider
config: `MOVRVEST_INTELLIGENCE_SYNTHESIS` and
`MOVRVEST_COMMITTEE_JUDGMENT`. With the latter off, Fee Capture records
`execution_unavailable` — which is a real judgment event, not a failure.
Supply Governance has no model seam at all and always answers.

## The two-committee matrix, as last recorded

```text
asset   Supply Governance        Value Capture
1INCH   known_not_applicable     no_mechanism_evidenced
ADA     governance_set           (last run with the judge off)
ARB     evidence_insufficient    no_mechanism_evidenced
BTC     consensus_bound          known_not_applicable
ETH     evidence_insufficient    mechanism_evidenced
HYPE    evidence_insufficient    mechanism_evidenced
SOL     governance_set           mechanism_evidenced
TAO     applicability_unknown    applicability_unknown
```

**BTC and 1INCH swap sides** — the clearest evidence the two committees
are not one question asked twice.

## Recorded debt, deliberately unsolved

- **No shared notion of "acquired for committee N."** `movrvest acquire`
  fills neither committee's evidence door. The acquisition orchestrator
  is its own slice and nothing so far proved it inseparable.
- **`Confidence` saturates** — 8, 9 and 11 findings all read
  `MULTIPLE_OBSERVATIONS`. Two committees are not enough to design its
  replacement.
- **Historical judgments are auditable, not reproducible.** The digest
  says the evidence moved; it cannot say what it said.
- **`MATERIAL_SPREAD` (25%) is provisional** and is not a definition of
  investor materiality.
- **`max_supply: null` and "field absent" are indistinguishable** in the
  provider, so *"ETH has no cap"* is not currently supportable.
- **Asset Quality's absolute bands** still force a value across a
  threshold this platform would now express as a range.

## Open, unchanged, not mine to take

Two rulings from the S-sequence remain open and are recorded in
`memory/movrvest-crypto-sequence.md`. Neither blocks anything above.
