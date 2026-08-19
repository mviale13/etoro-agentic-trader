# Identity history: what must be remembered before anything refreshes itself

**Status: research. 2026-08-19. No production change.** The #145 audit
(`research/identity-history`, open and parked) revalidated against
current `main` (`7789a67`) — after #192's issuer-reassignment guard,
#205's dated-CIK news guard, #212's Ticker Events measurement and
#214's word-boundary fix — and extended by one bounded live read of six
named specimens. PR #145 is treated throughout as the prior measurement
being revalidated, not as current code.

## Conclusion

# B. RETENTION READY, GATING NOT READY

**The overwrite defect still exists on current main, unchanged in
structure** — and the live corpus has now demonstrated the complete
forget-flip the audit predicted: SPCX's vendor claim has drifted into
agreement, so today's acquire writes only the agreeing account and the
2026-08-13 contradiction survives nowhere queryable. **What must be
remembered is specifiable now** (§7) and reuses the repository's
observation-stream / derive-on-read pattern with no new framework.
**Whether a remembered contradiction gates is not decidable from this
measurement** — the four candidate rules pull apart exactly where the
evidence classes have different reach, and one of the two tenancy
instruments was impeached live by PARA (§5). That decision is the
owner's, and §8 states it with the measured tension attached.

---

## 1. The lifecycle on current main, retraced (trace items 1–4, 7)

Every finding of #145 §1 reproduces on `7789a67`:

| question | current main |
|---|---|
| broker claim origin | `CrossProviderIdentityService.from_broker` over the live `WatchlistItem` — **never persisted**, exists only in flight |
| vendor claim persistence | inside the fundamentals record, `data/cache/fundamentals/{KEY}` — schema 4's `vendor_identity`, verbatim |
| replace or append? | **replace** — `JsonCache.write` is one `write_text` over the key's single file; no append, no version, no tombstone; `data/cache/` is gitignored |
| who derives `IdentityStanding` | `CompanyFactsService._identity` → `join_identity(live broker claim, latest stored vendor claim)` — a pure function of exactly those two inputs; `CrossProviderIdentityService.identity` for the ad-hoc question |
| old contradiction queryable after a newer agreeing claim? | **No.** One write and it is gone; the store can produce only the latest account |

## 2. Where the standing decides things (trace item 5)

The chain is live and unbroken: `join_identity` →
`CompanyFactsService` (which also gates monetary **translation** on
identity) → `MarketCapMagnitude.identity` →
`identity_authorised` — **UNRESOLVED blocks** — → market-cap input
eligibility inside `QualitySignalService` (the absolute-threshold
factor) → `decision_evidence_builder` → the CIO. The #143 amendment's
prerequisite gate is intact: the claims that produce UNRESOLVED are
**decision-bearing evidence held in a store whose write semantics
forget contradictions.**

## 3. The four intervening PRs change none of this (trace item 6)

Verified by import graph, not by changelog: `issuer_identity` (#192),
`personal_ticker_news_service` and `massive_news_provider` (#205)
import neither `provider_identity` nor the fundamentals cache — zero
overlap. **Three identity lifecycles now coexist and do not touch**:
the filing path (#192: ticker→CIK at EDGAR, with reassignment
protection), the news path (#205: two dated CIK resolutions per
window), and the fundamentals path (#134/#143: the cross-provider join
— the only one of the three with **no temporal protection of any
kind**). #212 built nothing. #214 changed how a form *word* is
recognised inside `_forms` and did not touch persistence, the ladder or
the gates. The defect the audit named is exactly as it was.

## 4. The specimens, current (one bounded live read)

Six reads, 2026-08-19 09:03 UTC, one request per symbol ~3s apart, no
retries, all succeeded; recorded in full in the session scratchpad and
nothing written — the evidence root was isolated and stayed empty,
`data/` clean. Broker-side names are held evidence (the #145 corpus of
2026-08-16 and the pinned fixtures); brokers claims are not persisted,
which is finding one.

| specimen | vendor says today | standing today | movement since #145 |
|---|---|---|---|
| **SPCX** | *"Space Exploration Technologies Corp."* · EQUITY | **ASSUMED** | **the forget-flip completed** — was UNRESOLVED on the 2026-08-13 payload (*"SPAC and New Issue ETF"*), the vendor has since drifted into agreement, and an acquire today stores only that agreement |
| **SE** | *"Sea Limited"* (longName null) | **UNRESOLVED** — eToro's *"Sea Ltd-ADR"* states a form, the vendor states none | unchanged, and still one wording drift from a silent ASSUMED |
| **NFLX** | *"Netflix, Inc."* | **ASSUMED** | #214 verified live: the manufactured ETF agreement is gone — both names carry no form word |
| AAPL | *"Apple Inc."* | ASSUMED | stable control — firstTradeDate 1980-12-12 |
| KO | *"Coca-Cola Company (The)"* | ASSUMED | stable control — firstTradeDate 1962-01-02 |
| **PARA** | *"Banzai International, Inc."* | (not on the book; symbol-change control) | see §5 — the reassigned symbol whose dated issuer evidence exists |

**SPCX is now the complete specimen.** A real contradiction existed
(#134, measured 2026-08-13/15); real resolution evidence exists (§5);
the contradiction dissolved from live state by drift; and the store
recorded none of it at any point. Candidate facts A, B and C are three
different facts about SPCX with three different sources today —
A from the live payloads, B from prose and test fixtures only, C from a
payload field the platform still does not read.

## 5. The three candidate facts, tested separately

**A — current standing.** Derivable now, correctly, for every specimen
(§4). `IdentityStanding` keeps its present-tense meaning; nothing here
needs history.

**B — historical contradiction.** For SPCX: *eToro said "Space
Exploration Technologies Corp" while Yahoo said "SPAC and New Issue
ETF" (quoteType ETF), measured 2026-08-13/15.* On current main this
fact is **not queryable from any store** — it survives as prose in
`PROVIDER_CLAIM_BOUNDARY.md` and as pinned fixtures, an engineering
record rather than evidence. For SE the contradiction is live and *would*
be stored at the next acquire — and erased at the acquire after the
vendor's wording drifts. **Retention is the only thing that makes B a
fact the platform can cite with dates and claim contents.**

**C — resolution evidence.** The classes, measured:

- **Dated instrument tenancy, from the vendor's own payload.** SPCX:
  `firstTradeDateMilliseconds` → **2026-06-12** — the instrument now
  under the symbol began trading then, which partitions the ETF-era
  claims from the current entity's the S4.6 way. Present in the payload
  and **still unread by the platform**.
- **The same field, impeached by the reassigned symbol.** PARA:
  `firstTradeDate` → **2021-02-12** — the *entity's* own trading
  history, not the symbol's 2026-08-07 reassignment (provider-reported,
  #212). **`firstTradeDate` marks a tenancy boundary for SPCX and fails
  to mark one for PARA**, so it is a candidate input, never a rule.
- **Dated issuer tenancy from a second source.** The dated-CIK
  instrument (#204/#205) partitions PARA cleanly (Paramount CIK
  0000813828 at 2023-06-01; Banzai CIK 0001826011 today) — and is
  **SEC-scoped**: nothing equivalent exists for a non-US listing with
  no CIK or for a UCITS fund (IB01.L carries neither CIK nor ISIN in
  any held payload). **Non-US securities and funds do not currently
  have sufficient resolution evidence** (measure item answered: no).
- **Explicit provider correction.** No channel exists in any payload —
  unchanged from #145, reconfirmed against the live reads.
- **Absence from the newest payload.** Observed for SPCX, and it is
  exactly what the ruling forbids treating as resolution: drift is
  indistinguishable from correction without memory.

## 6. The candidate architecture, tested against the code that exists

Every element has a precedent in-tree, none requires a framework:

- **`IdentityStanding` stays current-claims-only.** Zero corpus
  movement by construction: all 66 joins keep their standing (64
  ASSUMED, IB01.L CORROBORATED, SE UNRESOLVED — #214 already moved
  NFLX). The candidate adds a *second fact*, never edits the first.
- **An append-only claim stream, derive-on-read** — the
  `CompanyKnowledgeObservation` → `consensus_of` shape, or the
  journal's JSON Lines with schema-on-the-line. Both claims recorded
  verbatim per funded acquire, **broker claim included** (today it is
  never persisted, so half of every contradiction is unrecordable).
- **Contradiction as a derived fact** over the stream, not a stored
  verdict — #113's three-axes lesson: the answer, the observations and
  the evidence move separately.
- **Resolution only by named evidence** (§5's classes), never by
  absence — S4.6's dissolution pattern, and the journal's
  correction-names-what-it-corrects rule.
- **Storage and compatibility.** The fundamentals cache is untouched
  (schema 4 keeps serving the latest claim for A); the stream is new
  storage under the evidence root, hermetic by #118's rules. No
  migration, no read-path break; a fresh clone shows an empty history,
  which is what it is.
- **Retention starts at the first funded acquire after the build.**
  SPCX's 2026-08-13 contradiction predates any store and is *not*
  reconstructable; it enters history as this document's citation, not
  as an observation.

**Automatic refresh (the planned Daily CIO cycle) is unsafe today and
becomes recordable-safe with retention**: today every scheduled acquire
is an unwitnessed overwrite that can flip UNRESOLVED→ASSUMED silently
(SE is one drift away); with the stream, refresh *records* — whether a
remembered contradiction also *gates* is precisely the unresolved
ruling.

## 7. What must be remembered — the retention half, ready

Per security, per funded acquire: **both claims verbatim** (provider,
symbol, name, taxonomy, exchange, and the tenancy fields the payload
already carries — `firstTradeDateMilliseconds`, `ipoExpectedDate` —
today discarded), the acquire's timestamp, and the join the platform
derived from them at that moment. Append-only; the current standing
stays derived from the latest claims; the historical-contradiction fact
is derived from the whole stream; a resolution is an entry naming its
evidence class and the observations it dissolves.

## 8. The owner question — the gating half, not ready

Should an unresolved historical contradiction:

1. **gate every future decision permanently?** Falsified in #145 for
   typo-class transients, and this measurement adds the sharper case:
   where tenancy evidence is out of reach (non-US, funds — §5), a
   permanent gate fires hardest exactly where the evidence to lift it
   is weakest.
2. **gate only while it may concern the currently represented
   instrument?** The cleanest semantics, and it *requires* tenancy
   evidence — which `firstTradeDate` supplies for SPCX, fails to supply
   for PARA, and nothing supplies for a non-SEC listing. Under this
   rule those securities degrade to option 1 silently.
3. **remain visible but never gate?** Preserves every decision as it
   is today and makes the history purely testimonial — the SPCX ETF
   claims would have gated nothing at any point.
4. **another precisely specified rule?** The measurement supports one
   candidate worth stating: *gate while unresolved AND the
   contradiction's claims post-date the current instrument's
   established tenancy start; where no tenancy evidence exists, do not
   gate but surface* — a composite of 2 and 3 keyed on whether C-class
   evidence is available for that security.

No production implementation, no retention built, and PR #145 stays
open and parked: this measurement narrows its ruling, it does not
replace it.

## 9. Boundaries held

Research only · one bounded live read, six requests, one per named
specimen, no retry, every request recorded · no Massive News or Ticker
Events call · no model call · evidence root isolated and left empty,
`data/` clean, no production mutation · #145 not merged, rebased or
modified · `DOCUMENT_REFUSED`, `section_locator`, statements, Business
Quality, committees, CIO and News untouched.

---

## 10. Owner ruling — 2026-08-19

**Retention is adopted, exactly as §7 specifies.** Every explicit
funded fundamentals acquisition preserves the identity claims it
observed — both claims verbatim, the optional raw tenancy fields, and
the standing derived at capture — in a new append-only stream under the
evidence root, written **before** the latest-value cache replacement,
schema on every record. The fundamentals cache is not modified or
migrated; a fresh installation has empty history; SPCX's 2026-08-13
contradiction is **not** reconstructed from prose or fixtures.

**The gating question is answered: option 3, for now — visible, never
gating.** `IdentityStanding` stays current-claims-only, the current
UNRESOLVED gate is unchanged, and **no historical gate exists**. The
read surface must disclose explicitly that historical contradiction is
not decision-bearing.

**The lifecycle wording is fixed**: a previously UNRESOLVED capture
followed by newer agreement is worded *"previously disputed; current
claims agree"* — never *resolved* and never *corrected*, because §5
measured that no resolution evidence class is uniformly available and
absence from the newest payload is not one. **No resolution-event type
is built** until a resolving evidence class is; **no tenancy inference**
— `firstTradeDate` and `ipoExpectedDate` are retained as raw
observations and infer nothing, because PARA impeached the field as a
rule.

No backfill, no Ticker Events integration, no Daily CIO scheduler yet,
and PR #145 stays open and parked: this adopts the retention half of
its question and leaves the gating half where §8 put it — decidable
later, on retained evidence.
