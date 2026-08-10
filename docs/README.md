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
| How do we work? | [`ENGINEERING_CONSTITUTION.md`](ENGINEERING_CONSTITUTION.md) — **§23–24 first**: *no new architecture without a product story*. Every PR answers **what becomes better for the investor?** — "nothing, but the domain is cleaner" and the PR waits |
| Which package owns what? | [`architecture/REPOSITORY_INVENTORY.md`](architecture/REPOSITORY_INVENTORY.md) |
| What is built, what is missing? | [`PROJECT_STATE.md`](PROJECT_STATE.md) |
| What is next, and what is open? | [`architecture/MIGRATION_PLAN.md`](architecture/MIGRATION_PLAN.md) |
| How does the pipeline work? | [`architecture.md`](architecture.md) — **v5.0 section only** |
| What is knowledge, once the reader is known to vary? | [`architecture/KNOWLEDGE_CONSENSUS.md`](architecture/KNOWLEDGE_CONSENSUS.md) — **accepted**: observation vs consensus, the content-blind rule that separates them, and the decisions that bind the implementation |
| What is an investment decision? | [`architecture/INVESTMENT_DECISION.md`](architecture/INVESTMENT_DECISION.md) — **accepted**: the canonical object every future CIO engine must produce; a decision resolves disagreement, never uncertainty, and answers exactly one question |
| What is an investment assessment? | [`architecture/INVESTMENT_ASSESSMENT.md`](architecture/INVESTMENT_ASSESSMENT.md) — **accepted, frozen**: the bounded evaluative claim that offers a course to a decision; it offers, never decides, an implication is directional, and the Yahoo boundary keeps secondary restatements out of every basis |
| How do filing-grade financial facts enter? | [`architecture/FINANCIAL_STATEMENT_ACQUISITION.md`](architecture/FINANCIAL_STATEMENT_ACQUISITION.md) — the earned §19a reopening the assessment design fixed. Three statements, each located as the run they form rather than by title match, anchors checked cell by cell, rows read by the platform, one consensus per statement — and `FinancialUnderstanding` above them, which measures and never scores |
| Can statement shape choose the financial model? | [`architecture/FINANCIAL_LANGUAGE_CORPUS.md`](architecture/FINANCIAL_LANGUAGE_CORPUS.md) — **measured, conclusion B**: 44 companies, 4 jurisdictions. Shape separates financial-institution statements from ordinary ones without error, and cannot separate a bank from an insurer — so no divergence rule was earned, and `model_for()` still derives from the playbook |
| Where does the Financial Statement Domain end? | [`architecture/FINANCIAL_DOMAIN_BOUNDARY.md`](architecture/FINANCIAL_DOMAIN_BOUNDARY.md) — **accepted**: statements establish financial *language*, never prudential regulatory *status*. Prudential concepts belong to a separate domain sourced from a filing's regulatory sections, and `FinancialModel.BANK` stays derived from business understanding until a **Prudential Understanding** layer exists. Read this before proposing any statement-to-model rule |
| Can the BANK contract's own demands be grounded? | [`architecture/BANK_PRUDENTIAL_EVIDENCE.md`](architecture/BANK_PRUDENTIAL_EVIDENCE.md) — **measured, conclusion D**: CET1 and the LCR discriminate perfectly (10/10 banks, 0/9 non-banks, including three interest-based non-deposit lenders) and are unreachable — CET1 for 8 of 10 banks, the LCR for all 10. Nothing acquired; the named blocker is one more located region |
| What positively distinguishes a bank's statements from an insurer's? | [`architecture/FINANCIAL_LANGUAGE_EVIDENCE.md`](architecture/FINANCIAL_LANGUAGE_EVIDENCE.md) — **measured, conclusion A**: two concepts acquired out of six candidates, 24 companies at 5/5, zero false positives either way. A bank strikes an interest subtotal; an insurer prints a premium line. Acquired as `StatementLanguage` and connected to nothing — `model_for()` is untouched |
| Why did one conclusion prevail over another? | [`architecture/COMMITTEE_OPINION.md`](architecture/COMMITTEE_OPINION.md) — **implemented**: a committee states a stance over referenced findings, names the rule that produced it, and never names an action; the Executive synthesis reads them as supporting case / reservations / uncertainty / decision. Carries the **investment-profile determination** (§4 — not inferred, not a committee conclusion: a missing multi-period measurement, and the playbook already owns the need) and the **two-stack question** for the owner (§5) |
| How does every future assessment reach one object? | [`architecture/ASSESSMENT_CONVERGENCE.md`](architecture/ASSESSMENT_CONVERGENCE.md) — **accepted architecture, nothing implemented**: the owner ruled `CommitteeOpinion` the reference implementation of the Assessment layer without merging the pipelines. Convergence is by **projection, not merger**; a kind is **five declarations**; a stance is a direction and a course is a verb; and **shape converges, but only evidence class admits** — no committee assessment can warrant while every remit is provider-fed. Nine laws and the interleaved sequence |
| Which playbook reads a security, and which financial language? | [`architecture/PLAYBOOK_SELECTION.md`](architecture/PLAYBOOK_SELECTION.md) — the grounded selector, and the boundary the bank slice exposed: **what a company is and how it is read financially are two classifications**, and neither may be changed to suit the other |
| Which questions apply to a digital asset? | [`architecture/CRYPTO_ARCHETYPES.md`](architecture/CRYPTO_ARCHETYPES.md) — **built (S3)**: a `TokenArchetype` is a name for a set of `AnalyticalCapability` lenses, and a question is owned by a lens — so HYPE composes the venue's questions and the chain's, and Bitcoin is never asked what it pays its holders. **Applicability is decided from the archetype alone**, before a figure is read, and the same fee figure means a security budget, a burn or a buyback depending on the source's own sentence. Consumed by nothing |
| What does a supply number count? | [`architecture/CRYPTO_SUPPLY_SEMANTICS.md`](architecture/CRYPTO_SUPPLY_SEMANTICS.md) — **built (S4.6)**: five supply concepts, each carrying whose methodology produced it. Two numbers conflict only if they claim the same thing, so ADA's three-way disagreement dissolves — TokenInsight was reporting the ledger's `supply` and the reading S1 *rejected* was its `circulation` — while HYPE's stands because two vendors publish no exclusion set. TAO's emitted supply is now primary via Bittensor's own RPC. The re-judgment is reported and deliberately not written into `judge()` |
| What can a crypto fact *become*? | [`architecture/CRYPTO_EVIDENCE_AUTHORITY.md`](architecture/CRYPTO_EVIDENCE_AUTHORITY.md) — **measured (S4.5)**: `EvidenceAuthority` is a second axis beside standing, not a replacement for it. Two demonstrations that primary is not a synonym for true (a canonical, deterministic blob-fee computation wrong by 850 million ×; a protocol's own `totalSupply` counting tokens that do not exist), and one that primary settles what vendors could not — Cardano's ledger explains the three-way ADA supply conflict definitionally. Recommends Model C with a five-step gate, and S4.6 before S5 |
| What market is an asset trading inside? | [`architecture/CRYPTO_MARKET_CONTEXT.md`](architecture/CRYPTO_MARKET_CONTEXT.md) — **built (S4)**: a third crypto evidence family, separate from token and protocol facts. Every figure carries its interval and its universe; the comparator is MOVRvest's cap-weighted return over a *named* set rather than the provider's aggregate capitalisation change (a factor of three apart on the Layer 1 category). A peer group is a vendor's category and never an archetype — and where the taxonomy cannot support a comparison, TAO gets none rather than a fake one |
| Which qualities of a digital asset can be judged today? | [`architecture/CRYPTO_ASSET_QUALITY.md`](architecture/CRYPTO_ASSET_QUALITY.md) — **built (S5)**: the four-factor signal is deleted, not repaired. **Readiness** is a fourth vocabulary and a property of the *question*, so no asset can make a question scorable. Volume over market cap is refuted as liquidity (BTC ranks 158th of 233, 1inch 52nd); a vendor's `total_supply` is the protocol maximum for 83 of 145 capped assets; and two sources agreeing to the last bit are one source. One question of nineteen scores, the quorum is two, so **every crypto asset reads UNKNOWN** — which is the finding, and the owner's call |
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
