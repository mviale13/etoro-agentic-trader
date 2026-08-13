# Handoff — 2026-08-13

Everything is committed and green. One thing is blocked (funding, not
code), several things await CTO rulings. Start a fresh window here.

## State

`main` is at `f80912f`. Gates: ruff, ruff format, mypy (567 files),
**2150 tests**, frontend builds, HEAD verified in isolation at the ED1
merge (`e5f5ff1`).

Merged since the crypto arc closed at `#120`, in order:

| Merge | What |
|---|---|
| `59a58c2` (PR 119) | **F1 — Fund Analytical Boundary**: a fund is not asked company questions; `has_no_company` gains ETF; `fund_cost` retained as a dated fact |
| `7528079` (PR 120) | **E1 — Non-US Description Acquisition**: a wordless named segment is asked against the package's untagged prose; knowledge schema 12; the `normalised`/`_indexed` accent mismatch fixed |
| `e5f5ff1` (PR 121) | **ED1 — Business Economic Relationships**: the filer's stated dependence of one business on another, inside Business Understanding; schema 13 as a *cross-schema read* (the 12-corpus stays valid, marked never-asked) |

GitHub PR numbers and the owner's historical `#N` sequence diverged at
F1; merge commits are titled by slice name since.

## ⛔ The one blocker — ED1 live acceptance (funding, not code)

The OpenAI account reads `credit_balance_exhausted` (fresh 429s,
2026-08-13). Once Marcos funds it, run exactly:

```bash
movrvest observe VOW3.DE --to 10
movrvest observe CAT --to 10
movrvest observe DIS --to 10
```

**`--to 10` is required** — the schema-12 corpus fills the quorum under
ED1's cross-schema read, so a plain `observe` count-stops and takes
zero asked readings. **And read the log, never the exit code**:
`observe` exits 0 and prints the stored consensus even when every
reading attempt 429'd. Expected outcomes: VOW3.DE establishes the FS
relationship from the filer's own sentences (predominantly, never
total); CAT is genuinely open; DIS must stay empty (the control). Then
verify `/dossiers/VOW3.DE` renders the segment dependence line, and
decisions are unchanged. No code change is needed.

## Awaiting CTO rulings (do not start without one)

1. **Decision convergence** — measured (`f80912f`,
   `docs/architecture/DECISION_CONVERGENCE_MEASUREMENT.md`): the
   grounded route changes **zero** decisions/scores/committees across
   six companies; labels and applicability only. Recommended: **no
   production decision change**; re-measure when a grounded bank
   reaches statement quorum. The disposable harness is
   `tools/decision_convergence.py` — delete it when the ruling lands.
2. **The fidelity display slice** — the standing candidate with a
   completed §23 sentence (`EQUITY_DOSSIER_FIDELITY.md` slices 1 + 4):
   show the earned classification (a held bank reads *Bank*, not "Not
   classified" under a false sentence) and the financial question set.
3. **E2 — attributed category corroboration** — held
   (`EVIDENCE_PROPORTIONALITY.md` repair 2).
4. **F2 — "what am I actually buying when I own this fund?"** — parked
   (`FUND_EVIDENCE_RESEARCH.md`).

## The equity arc, in reading order

`EQUITY_DOSSIER_FIDELITY.md` (what the dossier hides) →
`EVIDENCE_PROPORTIONALITY.md` (the claim ladder was non-monotonic; E1
repaired acquisition) → `ECONOMIC_DRIVER_DEPENDENCY.md` (revenue
diversity ≠ driver diversity; ED1 built §8) →
`DECISION_CONVERGENCE_MEASUREMENT.md` (rerouting changes nothing
today). Memory index: the ▶ entries at the top of
`.claude/…/memory/MEMORY.md` mirror this.

## The crypto arc (unchanged, parked)

Everything above the assessment layer stays parked by the owner: CIO
recommendation, aggregation, weighting, overall score, thesis,
portfolio coupling. Asset Quality stays UNKNOWN at quorum 2, accepted
three times. `CRYPTO_DOSSIER_UI.md` is the newest crypto surface;
nothing crypto changed in this arc.

## Traps (the ones this arc added — older ones still hold)

- **`git archive HEAD` in isolation, every time** — still the only
  reliable catch for tree-vs-commit drift.
- **A knowledge schema bump has two shapes**: shown-text changes
  re-read the corpus (10, 11, 12); asked-question changes are
  cross-schema reads with a per-observation never-asked flag (13, after
  8→9). Prefer the second whenever the text shown is bit-identical —
  it saved the corpus once already.
- **`observe` trusts its exit code too much** (see the blocker above),
  and **a plain `observe` cannot widen an already-quorate company** —
  `--to` is the widening mechanism.
- **The pipeline's `quality_of` ignores `model_for` by documented
  design** ("a company reaches the default"). Any convergence slice
  must decide that coupling explicitly.
- **E1's passage cap drops the longest role sentences** — ED1's
  relationship ask therefore uses its own tighter radius (300); a
  causal sentence contains the name it is about.
- Yahoo still answers wrongly without failing: `fundInceptionDate` was
  six years off for IB01.L; sector/industry are null for half the
  sample under 401 degradation.

## Environment quickstart

```bash
source .venv/bin/activate
python -m pytest -q                     # 2150, ~12s
python -m uvicorn app.api.main:app --port 8000   # API
cd apps/web/movrvest-web && npm run dev          # frontend
```

The knowledge corpus note: under schema 13 only JPM and VOW3.DE restore
through the store door; the rest are schema-11/12 archives awaiting the
funded re-observation cycle (`observe SYMBOL --to 10` per symbol).
Until then their dossier understanding sections honestly read as
unread, and `playbook-coverage` runs over a thinner corpus than the
platform has actually read.
