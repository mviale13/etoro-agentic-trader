# MOVRvest documentation

This directory holds the project's documentation. Only the documents listed
under **Current** below are maintained and true to the code. Everything else
has been moved to [`archive/`](archive/) — it predates the current
architecture and is kept for provenance, not for guidance.

If a document is not listed here as current, verify it against the code before
trusting it. Several archived documents contradict each other and the code.

## Current

These are the documents a new session should read first. They are the same set
[`CLAUDE.md`](../CLAUDE.md) points to at the repository root.

| Question | Document |
|---|---|
| How do we work? | [`ENGINEERING_CONSTITUTION.md`](ENGINEERING_CONSTITUTION.md) |
| Which package owns what? | [`architecture/REPOSITORY_INVENTORY.md`](architecture/REPOSITORY_INVENTORY.md) |
| What is built, what is missing? | [`PROJECT_STATE.md`](PROJECT_STATE.md) |
| What is next, and what is open? | [`architecture/MIGRATION_PLAN.md`](architecture/MIGRATION_PLAN.md) |
| How does the pipeline work? | [`architecture.md`](architecture.md) — **v5.0 section only** |

## Reference

Factual references rather than guidance. Kept current-ish, but check against
the live surface before relying on a specific detail.

| Document | What it is |
|---|---|
| [`ETORO_API.md`](ETORO_API.md) | Inventory of the eToro read routes the platform calls. Verify a route against `app/brokers/` before trusting it. |

## Archive

[`archive/`](archive/) holds the superseded documents — early manifestos,
principles and vision statements (several of them near-duplicates), the
pre-v5.0 architecture notes, and old sprint logs. They record where the
project came from and are **not** a description of what it is now. Two iCloud
conflict copies of `architecture.md` were removed rather than archived.
