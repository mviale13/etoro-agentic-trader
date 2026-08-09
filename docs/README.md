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
| What is an investment assessment? | [`architecture/INVESTMENT_ASSESSMENT.md`](architecture/INVESTMENT_ASSESSMENT.md) — **accepted, frozen**: the bounded evaluative claim that offers a course to a decision; it offers, never decides, an implication is directional, and the Yahoo boundary keeps secondary restatements out of every basis |
| How do filing-grade financial facts enter? | [`architecture/FINANCIAL_STATEMENT_ACQUISITION.md`](architecture/FINANCIAL_STATEMENT_ACQUISITION.md) — the earned §19a reopening the assessment design fixed. Three statements, each located as the run they form rather than by title match, anchors checked cell by cell, rows read by the platform, one consensus per statement — and `FinancialUnderstanding` above them, which measures and never scores |
| Can statement shape choose the financial model? | [`architecture/FINANCIAL_LANGUAGE_CORPUS.md`](architecture/FINANCIAL_LANGUAGE_CORPUS.md) — **measured, conclusion B**: 44 companies, 4 jurisdictions. Shape separates financial-institution statements from ordinary ones without error, and cannot separate a bank from an insurer — so no divergence rule was earned, and `model_for()` still derives from the playbook |
| What positively distinguishes a bank's statements from an insurer's? | [`architecture/FINANCIAL_LANGUAGE_EVIDENCE.md`](architecture/FINANCIAL_LANGUAGE_EVIDENCE.md) — **measured, conclusion A**: two concepts acquired out of six candidates, 24 companies at 5/5, zero false positives either way. A bank strikes an interest subtotal; an insurer prints a premium line. Acquired as `StatementLanguage` and connected to nothing — `model_for()` is untouched |
| Which playbook reads a security, and which financial language? | [`architecture/PLAYBOOK_SELECTION.md`](architecture/PLAYBOOK_SELECTION.md) — the grounded selector, and the boundary the bank slice exposed: **what a company is and how it is read financially are two classifications**, and neither may be changed to suit the other |
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
