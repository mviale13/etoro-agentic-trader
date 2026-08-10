# Handoff — 2026-08-10

Everything is committed and green. Nothing is open. Start a fresh window
here.

## State

`main` is at `7c066ca`. Gates: ruff, ruff format, mypy (548 files),
**1984 tests**, verified with `git archive HEAD` in isolation.

Merged today, in order: `#103`–`#107` (the S1–S5.3 crypto sequence),
then five slices of the current direction:

| PR | What |
|---|---|
| `#108` | Crypto Intelligence slice 1 — what changed, what is driving it |
| `#109` | Events and narratives — a hedge separates a fact from a reading |
| `#110` | LLM synthesis — the validator, calibrated against live drafts |
| `#111` | The intelligence journal — a memory that refuses to overclaim |
| `#112` | The Value Capture Committee — the first bounded judgment |

## Where the work is

**The owner pivoted off Asset Quality** and it is settled: crypto
quality stays UNKNOWN for every asset, quorum 2, and three separate
rulings decline to lower it. **Do not try to earn factor #2.**

The arc that replaced it is complete for now:

```text
Evidence → Finding → Temporal Finding → Synthesis      (knowledge)
Eligible grounded findings → Committee → Judgment      (judgment)
```

**Everything below the line is explicitly parked by the owner**:
committee aggregation, recommendation coupling, Artificial CIO
reasoning, portfolio context, historical committee evolution. The §J
decision contract is a written specification and nothing more. Do not
start any of it without a new ruling.

## What to read first

1. `.claude/…/memory/MEMORY.md` — the first six lines are the crypto
   arc in order.
2. `docs/architecture/VALUE_CAPTURE_COMMITTEE.md` — the newest layer and
   the one whose boundaries are easiest to breach by accident.
3. `CLAUDE.md` — current through `#112`.

## Five rules this arc established, in the order they cost the most

1. **A hedge separates a fact from a reading; a number makes a fact
   *checkable*.** Two different properties. Conflating them filed
   *"AUSTRAC suspended Cryptolink's VASP registration"* as an opinion.
2. **An event's identity is its shared figure, not its words.** Eight
   accounts of one MicroStrategy sale collapse on `1690`.
3. **A validator over model output is wrong in both directions, and only
   live drafts show which.** It refused *"funds hold 1,223,634 BTC"*
   because `hold` is also a verdict, and separately let *"Coinbase led
   the buying"* through.
4. **A count of captures is never a duration of monitoring.** Three
   weekly looks are not three weeks.
5. **A committee owns its own applicability rule.** Routing it through
   `TokenArchetype` made BTC and TAO come out identical when their
   problems are opposite.

## Three traps that will bite again

- **`git archive HEAD` in isolation, every time.** Tests that read the
  gitignored `data/cache` or `data/journal` pass locally and fail on a
  clean checkout. This has now happened **three times** — S3, slice 1,
  and `#112`, where it caught six tests before they shipped.
- **A module that explains what it refuses fails a text search for the
  thing it refuses.** Use `reachable()` from `tests/reachability.py`,
  and prefer a behavioural test where the guard word appears in the
  prose. Six occurrences so far.
- **`data/journal/` is gitignored**, like `data/decisions/`. A fresh
  clone has no history and honestly says so; the committee and the
  temporal projection will show `first observed` until
  `movrvest acquire` has run more than once.

## What is live and what it costs

`movrvest acquire` is the only explicit spend — it fills the provider
stores, the event store and appends one journal capture per asset. A
page view or CLI read never fetches.

Two model seams are off by default and share the writer's provider
config: `MOVRVEST_INTELLIGENCE_SYNTHESIS` and
`MOVRVEST_COMMITTEE_JUDGMENT`. The Executive Writer's own flag is
already `on` in `.env`.

```bash
movrvest crypto-intelligence BTC --evidence
movrvest crypto-events BTC --evidence
movrvest intelligence-journal BTC --evidence
movrvest committee-judgment ETH --evidence
```

## Open, unchanged, not mine to take

Two rulings from the S-sequence remain open and are recorded in
`memory/movrvest-crypto-sequence.md`. Neither blocks anything above.
