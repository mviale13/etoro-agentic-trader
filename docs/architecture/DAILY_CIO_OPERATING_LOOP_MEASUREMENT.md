# The daily operating loop: what one bounded cycle actually is today

**Status: research. 2026-08-19. No production change.** Stage 0 traced
every component of the candidate loop before anything ran; stage 1 ran
one due acquisition cycle and one immediate same-day repeat against an
**isolated copy of the evidence root** (471MB, 5,801 files — production
`data/` untouched throughout), then read the three investor surfaces
against the same completed cycle. Settings were loaded from the ignored
repository-root `.env` into process memory only; every model seam was
forced off; the boundary instrumentation hard-failed on any model,
Massive or SEC host and on any mutating HTTP verb outside the two
providers whose POST is a read-only data query. No balance, credential
or account identifier appears in this report.

## Conclusion

# B. COMPONENTS READY, DAILY CONTRACT NOT READY

**The components compose safely.** A due cycle is bounded (191.9s, 301
HTTP calls, 26 securities), spends nothing it is forbidden to spend,
cannot trade or message anyone by construction, degrades per component
on provider failure, and leaves every store the surfaces read from
filled — including 26 identity observations appended exactly once, on
real acquisitions only.

**What does not exist is the contract.** There is **no cycle identity
anywhere in the system** — no cycle id, no completion stamp, no status,
no record that an acquisition happened at all beyond per-record
timestamps. And **decisions are journaled by page views, not by
cycles**: the one real recommendation change this measurement caught
(DIS, PREPARE → RECOMMEND) entered the journal because *this
measurement opened a page*, not because a cycle concluded. Until a
cycle is a recorded thing and deciding is the cycle's act rather than
the page's, the five investor questions cannot be answered *about* a
cycle — §7 names the precise blockers.

---

## 1. Stage 0 — the trace, before anything ran

### Can anything trade, message, or spend on a model?

**No, structurally.** The broker client exposes exactly one HTTP method
— `EtoroClient.get` — and its capture hard-codes `"http_method":
"GET"`; there is no POST/PUT/DELETE anywhere under `app/brokers/`, no
order-construction code, and the `live_gate_open` setting is consumed
by nothing. The only POSTs in the whole tree are read-only data queries
(SoSoValue metrics, chain JSON-RPC). No mail, webhook, notification or
messaging library exists in the codebase. `movrvest acquire` imports no
writer, reader or synthesis module — no model seam is reachable from
it. The run confirmed all of it at the transport boundary: 362 requests
across the whole measurement, zero to a model host, zero to Massive or
SEC, zero mutating.

### The step matrix

| step | network | model | writes | freshness rule | retry | failure scope |
|---|---|---|---|---|---|---|
| `movrvest acquire` | eToro ×7 · Yahoo · TokenInsight · CoinGecko · DefiLlama · chain RPCs · SoSoValue · press | none | 14 cache dirs (replace) · identity + journal (append) · eToro captures (immutable) | `is_from_today` per store; quotes/VIX 15-min TTL | none (one paced 429 retry at CoinGecko only) | **portfolio/opportunities unguarded — eToro outage kills the command**; everything else degrades per component |
| `movrvest morning` | eToro ×1 | none | 1 eToro capture | — | none | total |
| `movrvest brain` | eToro ×4 + Fear&Greed | none | eToro captures · market archive | market/facts from stored doors | none | portfolio unguarded |
| `movrvest evaluate` | eToro ×4 + Fear&Greed | none | **decision journal** + captures | stored doors | none | total |
| `movrvest decide` | eToro ×1 (guarded) | none | `data/decisions` append-only | stored knowledge only | none | worded absences |
| `GET /api/today` | eToro + **uncached Yahoo** + Fear&Greed | none | **an event per page view** | none | none | unguarded 500 |
| `GET /executive/portfolio` | eToro ×4 + Fear&Greed | none | **decision journal** + market archive + captures | stored doors for market data | none | **whole page 500s on eToro outage** |
| `GET /research/candidates` | eToro ×4 + Fear&Greed | none | **decision journal** + captures | stored doors | none | 500 |

Three further stage-0 facts, each load-bearing:

- **Two different "today" surfaces exist.** `GET /api/today` runs the
  *legacy* committee stack with an uncached `YahooMarketProvider()` and
  a raw `ValueProvider()` per request — the page-view law's
  counterexample, measured at **19 outbound calls and one journal write
  per view** — and the frontend does not even call it. The dashboard's
  real Today card is built inside `/executive/portfolio`.
- **The rich reason is not stored.** A journaled decision carries its
  contemporaneous `rationale` string and scores; the
  `DecisionSynthesis` (because / despite / review-if) is rebuilt on
  request and never persisted. The change feed pairs consecutive
  journal records and reuses the recorded rationale verbatim — so a
  change *does* carry its contemporaneous reason, at rationale
  granularity.
- **No book-wide staleness, refusal or coverage counter exists.** The
  research funnel counts coverage for the watched universe; the
  portfolio cards carry no `evidence_as_of` at all.

## 2. Stage 1 — the due cycle, measured

Fundamentals in the copied root dated 2026-08-08/09 — today's cycle was
genuinely due, not a cache walk.

| | run 1 (due) | run 2 (same-day repeat) |
|---|---|---|
| elapsed | **191.9s** | **7.8s** |
| HTTP calls | **301** | **61** |
| files added / changed | 41 / 112 | 7 / 12 |
| identity observations | **+26 (one per funded read)** | **0** |
| exit code | 0 | 0 |

**Run 1 call volume by provider**: Yahoo 184 (fundamentals + quotes
batch + calendars + FX) · DefiLlama 33 · CoinGecko API 16 + web 16 ·
TokenInsight 10 · press (CoinDesk/Cointelegraph/TheBlock/Decrypt) 25 ·
eToro 7 · SoSoValue 4 · chain RPCs 3 · GitHub 3. Raw HTTP was
**observable end to end** — httpx, requests and curl_cffi were all
intercepted at the transport, so no count here is an estimate.

**Outcome**: 26 securities asked, 24 priced, 9 strip instruments, VIX,
FX, 5 tokens fully evidenced (ratings, facts, protocols, supply, flows,
events). HYPE and TAO returned no price and were reported as exactly
that — the cycle's own render names them, which is the honest per-item
absence. Two Yahoo 401 crumb errors during calendars were absorbed as
per-component degradations; nothing aborted.

**The repeat is cheap but not idempotent.** The from-today gates
suppressed the entire fundamentals sweep. What re-ran: eToro ×7 (the
account is perceived live every cycle, by design), and — the finding —
**the crypto-events/press corridor, which has no from-today gate**:
~48 of the repeat's 61 calls (press 25, CoinGecko web 16, GitHub 3,
DefiLlama hacks 4), the events caches rewritten, treasuries re-fetched,
and **five new journal captures appended per repeat**. The journal's
"two looks are two lines" honesty is working as designed; the
*acquisition* above it simply never checks whether it already looked
today.

**Identity observations behaved exactly as #216 promised, on their
first production-shaped run**: 26 streams created, filed under
canonical symbols (`identity/BTC.jsonl`, not `BTC-USD`), one line each
after run 1 — and still one line each after run 2, because a
cache-served read observes nothing.

## 3. The surfaces, against the completed cycle

| route | latency | outbound calls during the request | writes during the read |
|---|---|---|---|
| `GET /api/today` | 3.85s | **19** | 1 recommendation event |
| `GET /executive/portfolio` | 3.44s | 8 (eToro + Fear&Greed) | decision journal + market archive + captures |
| `GET /research/candidates` | 1.77s | 8 | decision journal + captures |

Three reads added **17 files** to the evidence root — sixteen eToro
captures and a market snapshot — and journalled **29 decisions**. That
is measure 14 answered in the strongest form: every surface fetches
independently after acquisition (eToro always; `/api/today` Yahoo too),
and none of them reads a *cycle* — each rebuilds its own present.

**Time to first investor-usable output**: 191.9s of acquisition plus
3.4s of page build ≈ **3.3 minutes** end to end. (`/api/today` answers
in 3.85s with no acquisition at all — but from the legacy committee
stack over uncached reads, which is a different and worse answer, not a
faster route to the same one.)

## 4. Decisions: produced, unchanged, changed (measures 9–10)

The two pipeline surfaces journalled **29 decisions** today. Against
the latest prior day in the copied root (2026-08-17, 23 decisions):
**one state change — DIS, PREPARE → RECOMMEND — carrying its
contemporaneous rationale**, everything else unchanged or newly
covered. The change-feed mechanism (consecutive journal records, state
inequality, severity by lifecycle distance) detects exactly this shape
and re-decides nothing.

But the provenance of those 29 records is the finding: **they exist
because this measurement opened two pages.** `movrvest acquire` writes
no decisions; the pipeline runs when a route runs. On a day nobody
opens the dashboard, no decision is recorded and no change can ever be
detected — "did any recommendation change since yesterday?" is
currently a question about *page traffic*, not about the book.

## 5. Coverage and freshness after the cycle (measures 7–8)

Fundamentals store: 26 records from today (the book, candidates within
budget, and BTC-USD strip), 53 records from 2026-08-08/12 — past-book
securities the cycle no longer asks for. Quotes: 32 today. The cycle is
**book-scoped by design**: coverage of the current book is complete,
and staleness of the store as a whole is an artifact of the book
changing shape. No surface reports either number today (stage 0's
missing counter).

Refusals: HYPE and TAO unpriced, named per item in the cycle's render;
DOCUMENT_REFUSED and the filing stores are untouched by this loop
(acquire never reaches EDGAR — measured zero SEC calls).

## 6. The remaining measures, answered

- **11 — "nothing changed" vs "the cycle failed":
  indistinguishable today.** Acquire's exit code (1 when nothing
  priced) is the only failure signal and nothing stores it; a surface
  rendered five minutes after a failed cycle serves yesterday's
  evidence with per-record dates and no statement that a cycle was
  attempted. This is the sharpest gap the DailyCIOCycle object exists
  to close.
- **12 — failure scope**: measured and asymmetric. Every downstream
  provider degrades one component (the 401s and unpriced tokens cost
  exactly their own rows), but the two eToro perception calls are
  unguarded — a broker outage kills the whole cycle, and 500s the whole
  portfolio page.
- **13 — do the surfaces agree on one completed cycle?** No such thing
  exists to agree on. They agree *approximately* because they read the
  same stores, but `/api/today` decides from a different stack over
  different (uncached) reads, and every surface re-perceives the
  account at its own moment.
- **15 — latency and volume**: the fundamentals sweep dominates the due
  cycle (Yahoo, 184 calls, sequential per security); the press corridor
  dominates the repeat (~48 calls, ungated). eToro is never the cost
  (7 calls, rate-budget paced).

## 7. Stage 2 — the contract, tested against what was measured

The candidate `DailyCIOCycle` object **survives with two revisions and
one hard prerequisite**.

**The prerequisite: deciding must become the cycle's act.** The object
promises "recommendation changes with reasons" and "unchanged
decisions" — neither is producible while the journal is written by
page views. The minimal change is not a scheduler: it is that the
explicit cycle, after acquisition, runs the one pipeline pass the
portfolio route already runs and journals under the cycle's identity.
The components for this are built and measured; only the composition is
missing.

**Revision one: the reason needs to be captured at decision time.**
"Changes with reasons" at rationale granularity works today (the
journal keeps it, the feed quotes it). If the richer
because/despite/review-if synthesis is wanted in the cycle record, it
must be persisted when the decision is made — it is currently rebuilt
on request and a later rebuild is not contemporaneous.

**Revision two: `next_due_time` should be informational only** — a
statement of when the freshness gates will next open (midnight UTC for
the day-gated stores, +15min for quotes), not a scheduling promise.
Everything else in the object maps onto measured facts: the acquisition
summary is `MarketAcquisition` (already in memory, currently
discarded); freshness/coverage is a walk over `stored_at` this
measurement performed in four lines; provider failures and last-known
readings are already per-record facts awaiting aggregation;
attention items and "no action suggested" are renderings of the change
feed and the funnel.

**Semantics, confirmed against the measurement**: COMPLETE must mean
every *stage* ran — run 1 was COMPLETE with two unpriced tokens and two
401s, and calling it anything else would make every real cycle FAILED.
PARTIAL names the stage or family (the eToro-abort case is today's only
whole-cycle failure and should become PARTIAL-with-last-known rather
than an abort — the guard the acquisition currently lacks). "No
changes" is never "nothing was read" — the cycle record carries the
read counts that make the difference stateable. No sentiment reaches
any BUY/SELL/HOLD (the provider sentiment is measured as display-only
today; the contract keeps it there). Personal Ticker News stays
on-demand and outside the budget (its gates were off throughout; zero
Massive calls). Identity history stays visible and non-decision-bearing
(#215 §10, untouched). **The loop recommends; it never trades** — and
uniquely among these guarantees, that one is structural today: there is
no code that could.

### The smallest useful v1

**One explicit command — `movrvest cycle` or a dashboard button — that
does four things in order**: run the existing acquisition; run the one
pipeline pass over the book and journal its decisions under a cycle id;
write one `DailyCIOCycle` record (append-only, the journal pattern);
and render it — what changed, what needs attention, what was refused,
what to consider, or "no action suggested" said outright. No scheduler,
no daemon, no notifications, no queue, no new analyst, no new score:
the measurement found nothing the explicit command cannot do, and the
rabbit-hole guard holds. A scheduler is a decision about *when* to
press the button and belongs to a later slice, after the button exists
and its record proves trustworthy.

### What blocks A, precisely

1. **No cycle identity** — nothing records that a cycle ran, completed,
   or failed; built, this dissolves measure 11.
2. **Page-view deciding** — the journal must be written by the cycle
   for "changed/unchanged since yesterday" to be a fact about the book.
3. **The eToro abort** — one unguarded perception call turns a broker
   outage into FAILED with no view at all, where PARTIAL over
   yesterday's held book is producible.
4. **Surface consistency** — `/api/today` (legacy stack, uncached
   reads, event per view) must either consume the cycle record or be
   retired; the frontend already does not use it.
5. **The ungated press corridor** — a repeat should not cost 48 calls
   and five journal captures; the events acquisition needs the same
   from-today gate every other family has.

## 8. Boundaries held

Research only — nothing implemented, no production composition changed
· isolated evidence root, production `data/` untouched and clean · zero
model calls (seams forced off; transport assertion never fired) · zero
Massive, zero SEC, zero leadership, zero filing observations · no
email, notification, messaging or trade path exists to avoid · no retry
added anywhere · `.env` loaded into process memory, never copied or
printed; no balance, credential or account identifier in this report or
in any artifact · call counts recorded at the transport boundary for
httpx, requests and curl_cffi — nothing here is an estimate, and had
any library hidden its transport that would have been stated rather
than guessed.

---

## 9. Owner ruling — 2026-08-19

Conclusion B is accepted, and the explicit Daily CIO cycle is
**approved as the next product slice** — no scheduler, daemon,
notifications, queue or dashboard button yet.

### The persistence contract, corrected

One final append-only cycle record is **insufficient**: a process
failure before that single write leaves *never started*
indistinguishable from *started and interrupted*. The minimum
lifecycle is two events and a derivation:

- append **STARTED** before the first network or acquisition action;
- append **one terminal event** after orchestration finishes;
- derive an **incomplete/interrupted** presentation wherever a STARTED
  has no terminal event.

**No terminal event is ever manufactured for a hard process kill** —
the dangling STARTED *is* the record of the interruption, and a reader
derives that meaning rather than a writer inventing it.

### Execution status and evidence sufficiency are separate dimensions

**COMPLETE means every required cycle stage ran.** It does not mean
every provider succeeded, every security was fully evidenced, every
analyst answered, or every security received an investment
recommendation. Per-security refusals and evidence gaps may exist
inside a COMPLETE cycle and **must remain visible** — the run-1
measurement (COMPLETE with two unpriced tokens and two provider 401s)
is the normal shape of a healthy cycle, not an exception to it.

### Unequal information coverage is an expected operating condition

**Information availability must never become a proxy for company
quality.** Missing evidence must not be scored as adverse, converted to
zero, or treated as proof that a business is weak. An evidence gap
constrains the *claim* and the *permissible action*; it does not
automatically prevent judgment.

### "Every security gets a course"

Means a useful explicit disposition in the existing product vocabulary
— never a forced BUY/SELL/HOLD, and never investing capital where
identity, pricing or risk cannot be bounded.

### Frozen for the next slice

Analyst thresholds, quorum rules, recommendation semantics, position
sizing and decision policy are all **unchanged** in the coming
implementation. Any movement there requires a separate measurement —
run over recorded cycle output, which is exactly what the spine exists
to produce.
