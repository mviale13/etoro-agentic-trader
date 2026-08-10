# Handoff — 2026-08-10

Everything is committed and green. Start a fresh window here.

## State

`main` is at `ba82d54` (S5.3). One PR is open and awaiting your ruling:

| PR | What | State |
|---|---|---|
| [#108](https://github.com/mviale13/etoro-agentic-trader/pull/108) | Crypto Intelligence, slice 1 | **open, awaiting ruling** |

Merged today, in order: `#103` (S5 asset quality — and it also carried
S3/S4/S4.5/S4.6, which had never been pushed), `#104` (S5.1 Model C
gate), `#105` (supply-schedule research), `#106` (S5.2 cache schema +
mechanical issuance), `#107` (S5.3 supply policy meaning).

Gates on `#108`: ruff, ruff format, mypy (532 files), **1845 tests**,
verified with `git archive HEAD` in isolation.

## Where the work is

**The owner pivoted off Asset Quality.** Crypto Asset Quality is
accepted as a deliberately narrow layer that stays UNKNOWN for every
asset — quorum 2, one scorable question, and three separate rulings
declining to lower it. Do not try to earn factor #2.

The direction is **Crypto Intelligence**: *what changed, what appears to
be driving it, why it matters, what to watch.* Slice 1 is built and
open.

## What to read first

1. `.claude/…/memory/MEMORY.md` — first line points at the current
   direction.
2. `docs/architecture/CRYPTO_INTELLIGENCE.md` — slice 1, including a
   critical product assessment and the recommended next steps.
3. `CLAUDE.md` — the crypto section is current through this slice.

## Next steps, in the order the report recommends

1. **Current events and narratives.** The biggest remaining gap and the
   reason BTC's brief is flow-heavy. The `ATTRIBUTED` claim type exists
   and has no live producer.
2. **The LLM synthesis layer.** It now has a grounded structured object
   to write from and a deterministic floor to fall back to.
3. **Only then a decision contract.** Drivers are currently rule-derived
   — a sign test on a 30-day sum — and should not move a recommendation.

## Two things I would fix early

- **BTC's 30-day flow reports the sum without the dispersion.** $128m
  net across 18 of 30 positive days reads as steadier demand than the
  data supports. Stated in the PR; not fixed.
- **`_identifiers` consolidation is done** (`tests/reachability.py`), but
  the text-search-matches-its-own-docstring trap bit five times before
  that. Use `reachable()` for every new import guard.

## Open, unchanged, not mine to take

Two rulings from earlier slices remain open and are recorded in
`memory/movrvest-crypto-sequence.md`. Neither blocks the intelligence
direction.
