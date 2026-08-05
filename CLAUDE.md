# MOVRvest

An Artificial Chief Investment Officer. It turns verified evidence into
transparent investment recommendations. **MOVRvest recommends; the investor
decides.**

This file is loaded automatically at the start of every session. Keep it
short, and keep it true — everything here is checkable.

---

## Read these first

| Question | Document |
|---|---|
| How do we work? | [`docs/ENGINEERING_CONSTITUTION.md`](docs/ENGINEERING_CONSTITUTION.md) |
| Which package owns what? | [`docs/architecture/REPOSITORY_INVENTORY.md`](docs/architecture/REPOSITORY_INVENTORY.md) |
| What is built, what is missing? | [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) |
| What is next, and what is open? | [`docs/architecture/MIGRATION_PLAN.md`](docs/architecture/MIGRATION_PLAN.md) |
| How does the pipeline work? | [`docs/architecture.md`](docs/architecture.md) — **v5.0 section only** |
| What state is the frontend in? | [`docs/frontend/UX_UI_INVENTORY.md`](docs/frontend/UX_UI_INVENTORY.md) — audit + slice-by-slice execution log |

[`docs/README.md`](docs/README.md) indexes the above and names the one
reference doc ([`docs/ETORO_API.md`](docs/ETORO_API.md)). The ~20 older
documents that predated the current architecture — several contradicting each
other and the code — now live under [`docs/archive/`](docs/archive/). Treat
anything not listed above as historical unless you verify it against the code.

---

## Commands

```bash
source .venv/bin/activate      # required; the tooling is not on the system PATH

python -m pytest -q            # ~670 tests, fast
python -m ruff check .
python -m mypy app             # must be clean

cd apps/web/movrvest-web && npm run build     # frontend gate
```

CLI: `movrvest evaluate SYMBOL`, `movrvest brain`, `movrvest today`.
API: `python -m uvicorn app.api.main:app --port 8000 --reload`.

---

## Verify the commit, not the working tree

Pre-commit stashes unstaged changes but **leaves untracked files in place**,
so hooks can pass on a tree the commit does not contain. This has already
shipped a commit that imported two files it did not include.

```bash
git archive HEAD | tar -x -C /tmp/headcheck && cd /tmp/headcheck \
  && source /path/to/.venv/bin/activate && python -m mypy app && python -m pytest -q
```

Run it before trusting any commit that adds files.

The pre-commit hooks need the venv on PATH:
`export PATH="$PWD/.venv/bin:$PATH"` before `git commit`.

---

## Invariants

These are not style preferences. Breaking them damages the product.

1. **Absent evidence is reported as absent, never estimated.** A plausible
   number on an investment dashboard reads as a measurement. If the platform
   cannot evidence a figure, it says so.
2. **The Brain stores facts, never conclusions.**
3. **Analysts assess; only the Artificial CIO decides.**
4. **Communication explains decisions; it never makes them.**
5. **The dashboard presents; it never calculates.**
6. **One business concept, one implementation.**

The UI labels its own honesty: every page declares its data provenance via
`<PageIntegrity>`, and cards carry a live / partial / placeholder pill. If
you make something real, update its pill.

---

## Before you build

**Verify the import graph before believing any document, including this one.**

```bash
grep -rln "app.services.committees" app --include="*.py" | grep -v __pycache__
```

The repository previously carried four parallel "committee" implementations
while the docs labelled a dead one canonical and the live one legacy. That
cost real time. Check what actually imports a package before building on it
or deleting it.

**Reuse before creating.** The Communication layer, the per-security
analysis, and the investment-case aggregate all already existed and were
simply unwired. Search before writing something new.

---

## Working rhythm

Ship one vertical slice at a time: a complete capability from Brain to a
surface the investor sees, fully tested, gates green, then commit.

**Start a new session at slice boundaries**, not mid-slice. Each slice ends
green and committed, so the repository fully describes the state and a fresh
window loses nothing.

---

## Environment notes

- The repository lives in iCloud Drive. It creates conflict copies
  (`reasoning_service 2.py`); `.gitignore` covers `* [0-9].*`, but check for
  them if type-checking reports odd duplicates.
- The preview-server tooling cannot access the iCloud path — run dev servers
  with plain background shell commands instead.
- Yahoo Finance rate-limits (401s). Per-security signals can flip between
  runs, which can flip a decision. Do not treat a single run as truth.
