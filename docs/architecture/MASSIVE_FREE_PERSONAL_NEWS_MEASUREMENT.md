# The endpoint works, the identity gate works, and five publishers wrote everything

**Status: research. 30 authenticated API requests, the full allocation,
all HTTP 200. USD 0.00. Zero model calls. No provider payload written to
disk, no article body retrieved, no `CompanyDevelopment` created, no
production implementation. The API key was read from the ignored
repository-root `.env`, sent only in an `Authorization` header, and is
absent from this report, every command, every commit and every file.**

The question was whether Massive's standard News can serve an on-demand,
display-only news inbox for one personal, non-commercial user.

> **It is available and it is fast.** `/v2/reference/news` and
> `/v3/reference/tickers/{ticker}` are both documented *Included* on
> Stocks Basic and both returned 200 on every call, median latency
> **0.36 s**. Twelve companies returned 50 items each with **600 of 600**
> carrying id, title, publisher, author, timestamp, article URL, tickers
> and a provider summary.
>
> **The identity hazard is real and the gate for it works.** `PARA`
> today resolves to **Banzai International** (CIK 0001826011); at
> 2023-06-01 the same ticker resolves to **Paramount Global** (CIK
> 0000813828). The ticker was reassigned, and the news endpoint's
> `tickers` array carries **bare strings — no CIK, no FIGI** — so an
> article tagged `PARA` cannot say which company it is about. The dated
> reference endpoint separates them for two calls per company.
>
> **The blocker is coverage, and it is severe.** Across all 600 items
> there are **five distinct publishers**. The Motley Fool wrote **401 of
> 600 (67%)**, GlobeNewswire 111 (18%), Benzinga 52, Investing.com 31,
> Zacks 5. **Apple's 50 items came from one publisher. Coca-Cola's 50
> came from one publisher.** No query returned more than five.
>
> **And a ticker association is not aboutness.** One Union Pacific item
> carries **44 tickers**; Paramount's carries 32, Apple's 27. These are
> market round-ups filed against everything they name, which is why
> AAPL and KO share seven articles.
>
> **So the intended v1 use — discovering Adobe AI competitive reporting
> — is not supported by this corpus.** The sample did not contain broad
> established-independent publisher coverage. It was dominated by retail
> investment commentary and press-release distribution.

---

## 1. Method, budget and credential handling

| | |
|---|---|
| authenticated requests | **30 of 30 allocated** |
| HTTP status | **200 × 30**, no 429, no entitlement refusal |
| pacing | single-threaded, sequential, monotonic clock, **≥13 s between request start times** |
| retries | **none** — automatic retries disabled |
| USD spend | **0.00** |
| model calls | **0** |
| provider payload retained | **none** — responses processed in memory; only derived counts written |
| article bodies retrieved | **none** |
| SDK / MCP / WebSocket | **none used** |
| pagination | **manual, one explicit call** — no automatic pagination |

**Credential handling.** `MASSIVE_API_KEY` was read from the ignored
repository-root `.env`, which was never copied into a worktree, archive
or fixture. Only its presence and length were checked. It travelled in
an `Authorization: Bearer` header and never in a URL, query string or
command-line argument. No request headers, no authenticated URLs and no
complete request objects were printed; provider error text passes
through a redactor before display. `?apiKey=` authentication was not
used.

**Call class split:** 15 news, 15 ticker-reference.
**Latency:** min 0.29 s, median 0.36 s, max 0.66 s.

### A sequencing failure, reported rather than smoothed over

The brief was amended mid-run to require retrieving Massive's REST
`llms.txt` **before** any authenticated request. **That amendment
arrived after all 30 calls had completed**, so the documentation gate
did not gate anything. It was executed immediately afterwards and is
recorded here as a retrospective check rather than a precondition,
because that is what it was.

| | |
|---|---|
| `https://massive.com/docs/rest/llms.txt` | retrieved **2026-08-18T13:20:43Z**, HTTP 200, 31,528 bytes |
| SHA-256 | `3d97823a53a68d17b5262ccf3c42087486729612e42b9c3cde9de7913633ea21` |
| opened from it | `stocks/news.md`, `stocks/tickers/ticker-overview.md` |
| documentation requests | **3**, none counted against the authenticated budget |

**No contradiction was found between the documentation and the endpoints
called**, with one exception recorded in §5. The Benzinga endpoint
family appears in the index at `rest/partners/benzinga/news.md` and
**was not called**.

---

## 2. Availability and entitlement

| endpoint | documented plan access | observed |
|---|---|---|
| `GET /v2/reference/news` | *"Included in all Stocks plans"* — Stocks Basic **Included**, *Updated hourly* | **200 on 15 of 15** |
| `GET /v3/reference/tickers/{ticker}` | Stocks Basic **Included**, *Updated daily* | **200 on 15 of 15** |

**No entitlement error, no payment prompt, no 429.** Conclusion C is
excluded on evidence.

**Rate-limit headers: none.** Not one of the 30 responses carried a
header matching `rate`, `limit` or `retry`. Call accounting is therefore
**not observable from the provider's responses** and must be counted
client-side — which bears directly on the owner's stated precondition
that *"call accounting is observable"* before any MCP evaluation.

---

## 3. Schema, measured over 600 items

| field | present | note |
|---|---|---|
| `id` | **600 / 600** | provider article identity; stable |
| `title` | 600 / 600 | |
| `publisher` | 600 / 600 | object: name, homepage, logo, favicon |
| `author` | 600 / 600 | |
| `published_utc` | 600 / 600 | RFC3339 |
| `article_url` | 600 / 600 | **publisher's own URL, not a redirector** |
| `tickers` | 600 / 600 | **bare symbol strings** |
| `image_url` | 600 / 600 | |
| `description` | 600 / 600 | provider summary |
| `keywords` | 597 / 600 | |
| `insights` | 595 / 600 | sentiment + reasoning, per ticker |
| `amp_url` | 31 / 600 | |
| **`updated_utc`** | **absent from the schema** | see below |

**There is no last-updated timestamp.** The documented field list has
`published_utc` and nothing else temporal. `PersonalNewsLead.updated_at`
is therefore **unfillable from this source** and must be dropped rather
than left as a null that implies it could be populated.

**A real advantage over the discovery-link lane.** `article_url` is the
publisher's own address. #203 recorded that Google News links resolve to
a consent wall; here *"Open publisher link"* actually opens the
publisher. That is the single biggest technical improvement over
everything measured in #194 and #203.

### Provider sentiment — measured, never adopted

`insights` carries a per-ticker `sentiment` and a `sentiment_reasoning`
string. Across the corpus:

| value | n |
|---|---|
| positive | 1,511 |
| neutral | 1,352 |
| negative | 628 |
| bearish | 8 |
| bullish | 3 |
| mixed | 1 |

**The vocabulary is not even internally consistent** — `positive` and
`bullish` and `negative` and `bearish` coexist in one field, so the
provider is emitting at least two scales through one key. Recorded as a
measurement. **It is not adopted, not displayed, not scored, and does
not reach any judgment**, per the brief and per Invariant 10: an
established figure is not authority to invent what it means.

---

## 4. Identity — the contract, and the case that proves it

### The reassignment control: PARA

| lookup | name | CIK | composite FIGI |
|---|---|---|---|
| `PARA` **today** | **Banzai International, Inc. Class A** | **0001826011** | BBG00YG9XLK3 |
| `PARA` **at 2023-06-01** | **Paramount Global Class B** | **0000813828** | BBG000C496P7 |

The symbol was reassigned. Banzai's `list_date` is 2023-12-15 and it is
`active: true` today.

**And the news endpoint straddles the change without saying so.** The
`ticker=PARA` query returned 50 items spanning **2024-07-03 to
2025-08-05** — Paramount-era reporting — while the ticker *now* belongs
to Banzai. An inbox labelling those items "Paramount" would be asserting
an identity the feed never supplied; labelling them "Banzai" would be
worse. **The `tickers` array is strings only: no CIK, no FIGI, nothing
that survives a reassignment.**

### The ambiguity control: BA

| lookup | name | CIK | composite FIGI |
|---|---|---|---|
| `BA` **today** | Boeing Company | 0000012927 | BBG000BCSST7 |
| `BA` **at 2019-01-02** | Boeing | 0000012927 | BBG000BCSST7 |

**Stable across seven years, same CIK, same FIGI.** The
British-Airways-style collision that free-text news search produces does
not arise here, because the query is a ticker in a single listing
namespace rather than a phrase. **This is a genuine advantage of the
lane and it should be stated as one.**

### The foreign-issuer control: BCS

`BCS` at 2022-01-03 → **Barclays PLC**, CIK **0000312069**, type
`ADRC`, locale `us`. The CIK matches the accession prefix of the
Barclays 20-F already held in the annual corpus
(`0000312069-26-000004`), so the provider's identity and this
platform's own filing evidence agree independently.

### The identity gate this measurement earns

Two reference calls per company, and it detects the PARA case:

> Resolve the ticker at **today** and at the **oldest returned
> article's date**. If the CIK is identical, every item in the window is
> attributable to that issuer. If it differs, the window spans a
> reassignment and every item in it is `ISSUER_REASSIGNED`.

**Stated limit:** this is a *window* test, not a per-article test. An
item published within days of a reassignment can still be misattributed,
and closing that would cost one reference call per distinct
(ticker, date) — infeasible at 5 requests per minute. **Query success
and ticker text never establish issuer identity**, and neither does this
gate; it establishes only that the window contains no reassignment.

---

## 5. Coverage, duplication and relevance

### Publisher concentration — the blocker

**Five distinct publishers across 600 items.**

| publisher | items | share |
|---|---|---|
| The Motley Fool | **401** | **67%** |
| GlobeNewswire Inc. | 111 | 18% |
| Benzinga | 52 | 9% |
| Investing.com | 31 | 5% |
| Zacks Investment Research | 5 | 1% |

Per company, distinct publishers in 50 items: **AAPL 1 · KO 1** · INTC 2
· F 3 · CVX 3 · ADBE 4 · BA 4 · BCS 4 · PFE 4 · T 4 · PARA 5 · UNP 5.

**The sample did not contain broad established-independent publisher
coverage. It was dominated by retail investment commentary and
press-release distribution.** The Motley Fool, Benzinga and
Investing.com all publish journalism and commentary; the measured
problem is **concentration and authority**, not the absence of
journalism. And **no query form, window or pagination changes it** — it
is who the provider aggregates.

**Benzinga content arrives through the standard endpoint.** 52 items
were published by Benzinga without any `/benzinga/` endpoint being
called. The brief's prohibition on that endpoint family was observed;
this is noted so that nobody later mistakes the presence of Benzinga
items for a breach of it.

### Duplication

| measure | result |
|---|---|
| duplicate provider `id`s | **0** in every query — 50 of 50 distinct, 12 times |
| duplicate normalised headlines | **real and uneven**: BCS **28 distinct of 50** (44% duplicated), PARA 45/50, UNP 49/50, the other nine 50/50 |
| same article returned for two companies | **18 pairs**, worst AAPL/KO **7**, KO/CVX 4 |

`id` equality is a clean de-duplication key. Headline-fingerprint
de-duplication is only needed for a minority of tickers, and **neither
may imply that two items describe the same real-world development** —
they reduce duplicate inbox rows and nothing more.

### Ticker association is not aboutness

Maximum tickers on a single article: **UNP 44 · PARA 32 · AAPL 27 ·
KO 27 · INTC 24 · ADBE 23 · F 20 · T 20 · BA 17 · PFE 17 · BCS 15 ·
CVX 14**.

An article tagged with 44 symbols is a market round-up. This is the
mechanism behind the 18 cross-query collisions, and it means an inbox
must say **"news reported for this ticker"** and never "news about this
company" — the provider is asserting association, not subject.

### Repeatability, pagination, history

**Repeatability is perfect.** The identical ADBE query repeated 24 calls
later returned the same 50 ids **in the same order**, set-equal, 50/50
overlap.

**Pagination did not continue the sequence.** Page one (`limit=50`,
`order=desc`, `sort=published_utc`) covered 2026-05-10 → 2026-08-16.
The provider's own `next_url` cursor returned **10 items, all dated
2026-08-18** — *newer* than page one's newest — with **zero overlap**,
and the `limit=50` did not survive into the cursor. Whatever the cause,
**the cursor is not a reliable continuation**, and *"new since last
read"* must not be built on it.

**Minimum information for incremental read**, therefore: the set of
`id`s already shown, plus the newest `published_utc` seen. Both come
free with the response and neither requires the cursor.

**History exceeds its documentation.** Stocks Basic is documented as
**2 years**; a `published_utc.lt=2023-01-01` query returned 10 items
dated 2022-12-31 — roughly 3.6 years back — and the PARA and UNP windows
also begin slightly beyond two years. **Reported as observed, and not to
be relied on**: undocumented over-delivery is not an entitlement.

**Geographic coverage** is US-centric by construction. BCS, a UK issuer,
resolves as a US-listed `ADRC` and its 50 items come from the same five
US publishers.

---

## 6. `PersonalNewsLead`, revised against the measurement

| field | verdict |
|---|---|
| `provider_article_identity` | **keep** — `id`, 600/600, zero duplicates |
| `queried_company_identity` | **keep** — records why the query ran, asserts nothing |
| `associated_provider_tickers` | **keep, and label as association** — up to 44 per item |
| `resolved_issuer_identities` | **keep** — CIK + composite FIGI + share-class FIGI from the dated endpoint, never from the news item |
| `headline` · `provider_summary` · `publisher` · `published_at` · `provider_url` · `retrieved_at` | **keep** — all 600/600 |
| **`updated_at`** | **drop** — no such field exists in the schema |
| `status` | **keep all four**, and all four are reachable |

Unlike #203's object, whose `IDENTITY_CONFIRMED` and `SOURCE_VERIFIED`
states were unreachable, **every state here can be attained**:
`DISPLAY_ONLY` by default, `ISSUER_REASSIGNED` by the §4 gate (PARA
demonstrates it), `IDENTITY_AMBIGUOUS` where the dated lookup cannot
resolve, `REFUSED` on entitlement or absence.

---

## 7. Conclusion

# B — TECHNICALLY AVAILABLE, COVERAGE INSUFFICIENT

**Technically available**, and more so than anything previously
measured: both endpoints are entitled on Stocks Basic, 30 of 30 calls
returned 200 at a median 0.36 s, the schema is complete on every field
that matters, `article_url` opens the publisher rather than a consent
wall, results are exactly repeatable, and provider `id` gives clean
de-duplication.

**Identity is not the blocker.** The hazard is real — `PARA` moved from
Paramount Global to Banzai International and the news feed carries no
identifier that notices — but the dated reference endpoint resolves it
for two calls per company, and `BA` and `BCS` both came back stable and
correct against this platform's own filing evidence. The gate and its
limit are specified in §4.

### The precise blocker

**Publisher concentration.** Five publishers wrote all 600 items; The
Motley Fool wrote 67% of them; Apple's and Coca-Cola's fifty items each
came from a single publisher. Combined with articles carrying up to 44
tickers: **the sample did not contain broad established-independent
publisher coverage, and was dominated by retail investment commentary
and press-release distribution, associated with a symbol.**

**The problem is concentration and authority, not the absence of
journalism.** The Motley Fool, Benzinga and Investing.com all publish
journalism and commentary; what the corpus lacks is *breadth* and
*independent established publishers*, and five sources cannot be a
cross-section however good any one of them is.

**This defeats the stated v1 use directly.** The intended boundary
names *"Adobe AI competitive reporting may be discovered and displayed
through Massive standard News."* Discovering competitive reporting
requires the breadth this sample does not have. The other three v1
clauses are unaffected: SEC-evidenced events remain established
elsewhere, and display-only plus no-automatic-effect are boundaries this
measurement respects throughout.

### What would change the answer

Not a query change, a window change or pagination — the concentration is
the aggregator's publisher set. It would take either a different tier or
provider whose publisher list is measurably wider, or an acceptance that
the inbox is *"commentary and press releases reported for this ticker"*,
which is a smaller and more honest promise than the one v1 makes. **That
is the owner's call, not this report's** — and if it is accepted, §4's
identity gate, §6's revised object and §5's incremental-read rule are
ready to specify it.

### Personal-use boundary, unchanged by any of the above

The Individuals ToS governs *"personal, individual, non-business, or
non-commercial use"*, and the prior contract review found its Market
Data terms forbid **non-display use and derivative works**. Everything
described here is display-only and stays inside that line; nothing
measured licenses a `CompanyDevelopment`, a score or a judgment, and the
free individual licence is not widened by the provider's own AI or MCP
documentation.

## 8. Scope compliance

Research only · no production code · no `CompanyDevelopment` created ·
no clustering into developments · no claim extraction, rewriting or
summarising of provider content · **no provider content sent to any
language model** · provider sentiment measured and **not adopted** · no
materiality, price causation or thesis implication · no BUY/SELL/HOLD ·
Business Quality, committees, CIO and recommendations untouched · no
article body retrieved · **no `/benzinga/` endpoint called** · no paid
endpoint, no SDK, no MCP, no WebSocket, no browser automation · no
automatic pagination, no automatic retries · **30 of 30 authenticated
requests, ≥13 s apart, no 429** · USD 0.00 · no provider payload
persisted · the API key appears in no file, commit, test, fixture or
line of this report, and `.env` was never copied · `git status
--porcelain data/` empty · Codex's unpublished `d203609` not read,
reused or published.
