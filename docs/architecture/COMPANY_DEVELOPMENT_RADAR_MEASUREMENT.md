# A development has no number, and the web has no date

**Status: research, Stage 1 only. Stopped at the feasibility gate by the
owner's own stop condition. No production implementation, no model call,
no spend, no production data mutation.**

The hypothesis was that company-specific developments could be
discovered from current reporting rather than anticipated one bespoke
analyst at a time. Stage 1 tested the whole path on four companies, and
two of its steps failed before any model was asked anything.

> **The identity mechanism that works for crypto does not transfer.** A
> crypto event clusters on a shared figure because the figure *is* the
> event — eight accounts of one MicroStrategy sale collapse on `1690`.
> Across four outlets reporting **one** FAA decision about Boeing, the
> anchors shared by all four are **none** and the keywords shared by all
> four are **`boeing`** — the company name, the one token that cannot
> discriminate one development from any other. Across nine accounts of
> Adobe's CEO succession: **no shared anchor, no shared keyword, median
> pairwise headline overlap 0.09, minimum 0.00.** The FAA restoring
> certification authority contains no number at all.
>
> **63% of discovered sources cannot be classified, and the tail is not
> predictable.** 26 of 41: `cryptobriefing.com` on Adobe's CEO search, a
> crypto exchange's "academy" on Intel, three SEO litigation pages on
> JPMorgan, an AI-generated news site, and a University of Iowa course
> PDF. **A publication date is recoverable for 7 of 41** without
> fetching every page, so the 180-day window cannot be enforced at
> discovery — and a query scoped to 2026 returned material from 2015,
> 2021 and 2024.
>
> **What does work is the filed half.** Identity resolved through the
> #192 guard for all four companies; 32 8-K filings and 174 attached
> exhibits inside the window; and Adobe's CEO succession decomposes into
> exactly the three states that must stay distinct.

---

## 1. Corpus and why these four

Stage 1's gate, chosen for **materially different development shapes**
rather than for coverage.

| | industry | selected because |
|---|---|---|
| **ADBE** | software | required. A filed governance development sitting beside a diffuse competitive one no regulator files at all — the two hardest shapes in one company |
| **JPM** | banking | developments arrive as regulatory and legal actions and capital-allocation decisions: filed, dated instruments rather than narrative |
| **BA** | aerospace | physical incidents, a safety regulator and customer orders — an operational subject with a named counterparty, a shape software never produces |
| **INTC** | semiconductors | strategic review, divestiture and capital structure — dominated by transactions rather than by product |

Window: **180 days**, 2026-02-19 to 2026-08-18. No exception was used.

**Stage 2 was not run.** The gate did not pass, and the brief's
instruction is explicit: *do not spend calls scaling a broken method.*

## 2. Acquisition — what it cost

| | |
|---|---|
| EDGAR submissions indexes | 4 |
| 8-K filings in window | **32** |
| filing-index fetches (for exhibits) | 32 |
| exhibits enumerated | **174** |
| filing documents fetched and parsed | 4 (Adobe's Item 5.02 set) |
| web discovery queries | **4** |
| **model calls** | **0** |
| **cost** | **USD 0.00** |

Every EDGAR request is free, unauthenticated and rate-limited by
courtesy delay only. Identity for all four resolved through
`PrimarySourceResolver` with the guard merged in #192 — CIK from the
ticker map agreeing with the CIK in the held document's own address for
each.

## 3. Source contract — measured, and it does not hold

Classification by host, written as the rule a first implementation would
write:

| | items | share |
|---|---|---|
| **UNCLASSIFIED** | **26** | **63%** |
| regulator filing / publication | 7 | 17% |
| analyst or opinion commentary | 4 | 9% |
| established independent reporting | 2 | 4% |
| issuer publication | 2 | 4% |

**The unclassifiable tail is the finding, not the number.** It is not a
list an allowlist could have been extended to cover:

- `cryptobriefing.com` — a cryptocurrency outlet reporting Adobe's CEO search
- `phemex.com/academy/` — a crypto exchange's marketing content on Intel
- `lawfold.com` ×3, `sonnlaw.com` — SEO litigation pages and a law firm soliciting claimants, asserting settlement timing as fact
- `theaicronicle.com`, `theaiinsider.tech` — AI-generated news sites
- `hedrick.io`, `genesysgrowth.com`, `illustration.app`, `upskillist.com` — vendor-comparison content marketing
- `biz.uiowa.edu/.../f24_ADBE.pdf` — a university course handout
- `classaction.org` ×2 — **category listing pages**, not accounts of any development

A **regulator publication** class the brief did not name was produced by
the corpus: `faa.gov/newsroom` and `oig.dot.gov` are the regulator
speaking, and neither is a *filing*. Any source contract needs it.

### Dates

| | |
|---|---|
| publication date recoverable from the URL | **7 of 41** |
| not recoverable without fetching the page | **34 of 41** |

And the window is not enforceable even with effort: the four discovery
queries were scoped to 2026 and returned a 2015 Business Standard
article, a 2021 congressional press release and a 2024 DOT OIG report.
**A search engine's relevance ranking is not a date filter**, so every
candidate would have to be fetched and parsed before it could be
excluded — which inverts the cost model the whole idea rests on.

## 4. Development identity — the decisive measurement

The brief specifies identity from resolved company, subject/action,
affected object, occurrence window and originating source, and says
headline similarity alone must not be used. **Both halves are confirmed:
the specification is right, and nothing deterministic satisfies it.**

### The strongest multi-outlet case: one FAA decision, four outlets

| outlet | anchors | keywords |
|---|---|---|
| theepochtimes.com | `737`, `787` | boeing, can, resume, issuing, airworthiness, certificates |
| claimsjournal.com | `737`, `787` | faa, letting, boeing, resume, clearing, 737 |
| **faa.gov** (the origin) | **none** | months, safety, review, faa, allows, boeing |
| bloomberg.com | `737`, `787` | faa, allows, boeing, resume, clearing, 737 |

**Anchors shared by all four: none.** The originating source — the
regulator's own newsroom — carries no aircraft number in its headline at
all. **Keywords shared by all four: `boeing`.**

### Adobe's succession cluster, nine accounts of one filing

**No shared anchor. No shared keyword.** Pairwise headline word-overlap:

| cluster | min | median | max |
|---|---|---|---|
| FAA certificates | 0.19 | 0.25 | 0.82 |
| Adobe succession | **0.00** | **0.09** | 0.67 |

Two genuine members of one cluster share **no word at all**.

### Deduplication confusion, on the two clusters with known ground truth

| | FAA (4 items) | Adobe succession (9 items) |
|---|---|---|
| correct merges by shared anchor | **0** | **0** |
| correct merges by shared keyword | 0 (only `boeing`, which merges everything) | **0** |
| duplicate misses | **4 of 4** | **9 of 9** |
| incorrect merges | not reached — nothing merged | not reached |
| origin-source recovery | **0** — no item names the FAA release as its source in any machine-readable field | **0** |

Order-independence and repeated-run stability were **not measured**,
because a mechanism that merges nothing is stable trivially and the
number would be misleading.

**Why crypto's rule does not carry over.** `anchors_in` extracts
normalised figures, and on SEC text the figures it finds are the item
number (`5.02`), a day of the month (`14`), a regulation (`404(a)`), an
age (`58`) and page numbers (`3`, `4`). None is an economic quantity.
The crypto ruling — *an event's identity is its shared figure, not its
words* — holds because a token event **is** a quantity. A regulator
restoring an approval, a CEO beginning a succession and a foundry
ownership covenant are not.

## 5. Factual boundary — works on press, misfires on filings

`decompose` separates checkable statements from readings and was never
asked an equity question. Run on Adobe's four Item 5.02 sections:

| defect | specimen |
|---|---|
| **sentence split on honorifics** | *"Adobe is conducting a search for Mr."* / *"Narayen's successor."* — `Mr.` ends a sentence |
| **item boilerplate filed as a fact** | *"Item 5.02 Departure of Directors or Certain Officers; Election of Directors; …"*, anchor `5.02`, in all four |
| **signature blocks and page numbers filed as facts** | *"ADOBE INC."*, *"4"*, *"Date: July 17, 2026 By: /s/ LOUISE PENTLAND … 3"* |
| **legal conditionals read as causal** | *"in the event of a termination of her employment"*, *"are designed to be temporary in nature"*, *"Pursuant to the requirements of the Securities Exchange Act of 1934"* — all `is_causal=True` |

The last is MC1's finding recurring in a second layer: **a conditional
or future clause is not an event and not a causal claim**, and no
keyword rule separates them.

Company assertion, third-party interpretation and rumour were **not
separable at all** in Stage 1, because the sources carrying them
(§3) could not be classified — the boundary needs the source class
first, and the source class is the thing that failed.

## 6. Adobe acceptance

### A — CEO succession: **passes on the filed evidence**

From the 8-K, accession `0000796343-26-000048`, occurred 2026-03-09,
filed 2026-03-12:

| the three states, kept distinct | the filer's own words |
|---|---|
| **completed act** | *"On March 9, 2026, Shantanu Narayen notified Adobe of his decision to transition from his role as Adobe's Chief Executive Officer."* |
| **ongoing search** | *"Adobe is conducting a search for Mr. Narayen's successor."* |
| **current office status** | *"Mr. Narayen will remain as Adobe's Chief Executive Officer until his successor is appointed."* |
| (and) | *"Mr. Narayen will remain as Chair of Adobe's Board of Directors."* |

All three are present, dated and checkable, and the third is a **future
conditional** that must not be classified as an appointment — the error
MC1 measured and the reason this acceptance case exists.

**They are not distinguished by anything currently built.** The
decomposition returns seven undifferentiated "facts", two of them
fragments produced by the honorific split, with no distinction between a
completed act, an ongoing state and a conditional future.

Adobe filed a **second** leadership development in the same window,
which the corpus supplied unprompted and which is a clean test of the
same distinction: on 2026-06-08 the CFO resigned effective 2026-06-15,
and on 2026-06-11 Steven Day was appointed **interim** CFO. Two
developments, one company, one quarter, different offices.

### B — AI competition: **cannot be represented at all**

No regulator files it, so §3's failure is total here rather than
partial. Of the eight sources discovered, **zero** are regulator
filings, **zero** are issuer publications and **zero** are established
independent reporting. Six are vendor-comparison content marketing, one
is a stock-message-board aggregation, one is a university course PDF.

The brief requires naming the observed development and a mechanism
rather than writing "AI risk". The mechanism candidates the sources
gesture at — **pricing power** (a Creative Cloud price change), **competitive
position** (a competitor's growth rate), **customer retention** — are
each attached to figures this platform **did not retain, did not fetch
and cannot check**. Reporting them would be exactly the failure the
brief prohibits: a generated statement introducing a fact absent from a
retained source.

So Adobe B is recorded as **refused for want of an admissible source**,
not as an absence of a development. That distinction is the whole point
and is the one thing this measurement can state with confidence.

### The interaction test

**Not reached.** Stating the interaction of two simultaneous
developments without calling it adverse requires both to be represented
first. A is representable, B is not, and asserting an interaction
between an established fact and an unsourced one would manufacture the
very thing the constraint forbids.

## 7. Negative controls — and they arrive indistinguishable

Nine of the 41 items are the brief's negative controls: routine
publicity, duplicated reporting, opinion and immaterial announcements.
**Every one of them arrived through the same discovery surface, in the
same shape, with the same absence of a date, as the genuine
developments** — and two `classaction.org` items are *category listing
pages* that describe no development whatsoever.

A pipeline reading this corpus without a source contract would have
ingested a University of Iowa course handout and three SEO litigation
pages as company developments.

## 8. Model usage

**Zero model calls. USD 0.00 of the USD 5 authorised, 0 of the 30 calls.**

The brief's order is deterministic-first, and the deterministic stage
answered the gate question. Spending the budget would have measured
whether a model can cluster items whose *sources cannot be classified
and whose dates cannot be established* — which is scaling a method that
has already failed upstream of the model.

Consequently **not measured**: model clustering beyond deterministic
duplicates, model-assisted factual separation, mechanism proposals,
thesis links, repeatability across runs, and unsupported-claim rates.
Those remain open and are the first things a re-scoped Stage 1 should
buy.

## 9. Conclusion

# C — NOT READY

**Two blockers, both in acquisition, both upstream of any interpretation
question.**

1. **The discovery surface has no date contract and no source
   contract.** A publication date is unavailable for 34 of 41 candidates
   without fetching each one, a 2026-scoped query returns 2015 material,
   and 63% of what is returned cannot be classified by host — with a
   tail (a crypto outlet on Adobe, a crypto exchange on Intel, SEO
   litigation pages, AI-generated news, a course handout) that no
   allowlist could have anticipated. **Until a candidate carries a
   publisher, a date and a class before it is read, the window and the
   source contract are both unenforceable.**

2. **Development identity has no deterministic signal.** Four accounts
   of one FAA decision share no anchor and only the company name; nine
   accounts of one Adobe filing share no anchor and no keyword, with
   median headline overlap 0.09. The crypto mechanism does not transfer
   because an equity development frequently contains no figure at all.

**What is not blocked, and is worth saying plainly:** the filed and
issuer-published half works. Identity resolves under the #192 guard,
the window is exact because the regulator stamps both an occurrence and
a filing date, the origin is unambiguous because the filer is the
source, and Adobe's succession decomposes into the three states the
acceptance case demands. **A Radar restricted to regulator filings and
issuer publications is a different and much smaller proposition, and
nothing measured here rules it out** — it was offered as an alternative
scope and not taken, so it is recorded rather than concluded.

### Refusal states this measurement earns

- **no admissible source** — a development exists in discovered text and
  no source of an acceptable class carries it (Adobe B);
- **undatable** — a candidate whose publication date cannot be
  established, and which therefore cannot be placed in or out of the
  window;
- **unclustered** — accounts that plainly concern one development and
  share no identity signal, held as separate reports rather than merged
  or silently dropped;
- **no mechanism** — a development with sources but no statable economic
  mechanism, which is descriptive-only rather than relevant.

And the one the brief specifies, unchanged: **"no qualifying development
was found in the sources and time window this platform read"** — never
stable, safe, strong or unchanged.

## 10. Gaps recorded

- **Paywall.** Bloomberg carried the FAA story and is not fetchable;
  established independent reporting is the class most likely to be
  behind a paywall, which biases any corpus toward the unclassifiable
  tail.
- **Non-U.S. issuers.** MC1 measured that Barclays, NatWest, Deutsche
  Bank and Mitsubishi UFJ file zero 8-Ks. A filings-based Radar reaches
  none of them, and the open-web alternative is the surface that just
  failed.
- **Aggregators.** `finance.yahoo.com` re-hosts other publishers'
  articles under its own domain, so host-based classification
  misattributes the publisher — measured on the Intel corpus and not
  solved.

## 11. Scope compliance

Research only · no production code · no model call, no spend · no
sentiment score, confidence percentage, article-count vote or
BUY/SELL/HOLD · **no claim that any development caused a price
movement** — the discovered claim that Adobe's shares fell after the
March announcement is recorded here as a claim made by sources and is
asserted nowhere · no Management Continuity implementation · no
Business Quality, analyst, committee, CIO or decision change · no
mutation of production evidence (`git status --porcelain data/` empty) ·
Codex's unpublished leadership-event implementation was not read,
modified, published or reused.
