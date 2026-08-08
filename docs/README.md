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
| What is knowledge, once the reader is known to vary? | [`architecture/KNOWLEDGE_CONSENSUS.md`](architecture/KNOWLEDGE_CONSENSUS.md) — **accepted**: observation vs consensus, the content-blind rule that separates them, and the decisions that bind the implementation |
| What is an investment decision? | [`architecture/INVESTMENT_DECISION.md`](architecture/INVESTMENT_DECISION.md) — **accepted**: the canonical object every future CIO engine must produce; a decision resolves disagreement, never uncertainty, and answers exactly one question |
| What is an investment assessment? | [`architecture/INVESTMENT_ASSESSMENT.md`](architecture/INVESTMENT_ASSESSMENT.md) — **accepted**: the bounded evaluative claim that offers a course to a decision; it offers, never decides, an implication is directional, and the Yahoo boundary keeps secondary restatements out of every basis |
| What state is the frontend in? | [`frontend/UX_UI_INVENTORY.md`](frontend/UX_UI_INVENTORY.md) — the pre-migration audit and the slice-by-slice execution log of the UX/UI Alignment mission (complete, PRs #8–#16) |

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
