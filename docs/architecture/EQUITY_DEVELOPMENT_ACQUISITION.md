# A feed has a date contract; a search engine does not

**Status: research. Zero model calls, zero spend, no account created, no
terms accepted, no provider integrated, no production implementation, no
production data mutation.**

#193 ruled generic web search inadmissible. This asks the narrower
question the ruling left open: **which acquisition surfaces can supply a
stable, dated, attributable, company-resolved corpus**, measured lane by
lane against the record contract.

> **The date blocker is not intrinsic to independent reporting — it was
> intrinsic to search.** Google News RSS returned **400 items across
> four company queries with 0 outside the 180-day window and 0 undated**,
> and named the publisher on **100 of 100**. #193's *"a relevance
> ranking is not a date filter"* is true of search and false of a feed.
>
> **The blocker that survives is identity.** A feed query matches a
> string, not an issuer. `PARA` returns para-cycling, para-hockey and
> para-dressage and **not one Paramount item**; `BA` returns British
> Airways, and **SARS-CoV-2 Omicron BA.2.86**. #192's principle holds on
> this lane exactly as it held on EDGAR — *a symbol is not an issuer* —
> and no free feed carries a registry identifier to fix it.
>
> **Adobe's competitive development IS retrievable**, which #193 could
> not achieve: two Reuters items, dated and attributed, from 168
> candidates. That is a **1.2% admissible rate**, in a corpus led by
> Seeking Alpha (25), TradingView (16) and TradingKey (7).
>
> **And the authoritative lane is ready.** EDGAR's full-text search
> honoured the window exactly — **0 items outside it across all five
> companies** — and Barclays, which files no 8-K at all, filed **35
> 6-Ks** in the same window.

---

## 1. Corpus

The four from #193 plus one foreign private issuer from the held corpus,
so non-U.S. coverage is exposed rather than postponed. Window: **180
days**, 2026-02-19 → 2026-08-18.

| | CIK | jurisdiction |
|---|---|---|
| ADBE | 796343 | US |
| BA | 12927 | US |
| JPM | 19617 | US |
| INTC | 50863 | US |
| **BCS** Barclays PLC | 312069 | **UK — foreign private issuer** |

## 2. Provider matrix — live-tested versus documentation-only

| lane | source | tested | verdict |
|---|---|---|---|
| A | EDGAR submissions index | **live** | **admissible** |
| A | EDGAR full-text search (`efts.sec.gov`) | **live** | **admissible**, hard date filter |
| A | EDGAR per-company Atom | **live** | admissible, **operationally unreliable** |
| A | issuer newsroom / IR feeds | **live** | **2 of 5 issuers only** |
| A | regulator press / enforcement feeds | **live** | 5 of 7 reachable |
| B | Google News RSS | **live** | date + publisher yes; **URL, identity, licence no** |
| B | GDELT DOC 2.0 | **live** | **429 on 9 of 10 attempts** |
| B | established publisher RSS | **live** | metadata excellent, **no company query** |
| B | NewsAPI.org, Marketaux, Finnhub, Polygon.io, Alpha Vantage | **documentation only** | all require an account and acceptance of terms — **not tested, by instruction** |

Every documentation page was fetched and returned 200. **No account was
created, no trial started and no terms accepted**, so nothing about
those five is reported as observed behaviour.

## 3. Lane A — authoritative publications

### A1 · EDGAR submissions index — admissible for all five

| | current reports in window | forms | item codes |
|---|---|---|---|
| ADBE | 4 | 8-K | yes |
| BA | 3 | 8-K | yes |
| JPM | 16 | 8-K | yes |
| INTC | 9 | 8-K | yes |
| **BCS** | **35** | **6-K** | **no** |

Latency 0.18–0.33 s. Two dates per filing — the filer's own occurrence
date and the regulator's receipt date — plus an immutable accession.

**The non-U.S. finding is better than MC1's.** MC1 recorded foreign
private issuers as unreachable *for Item 5.02*. They are not unreachable
as a **publication stream**: Barclays filed more current reports in the
window than any US company here. What is missing is the *item
taxonomy*, not the dated, attributable document.

### A2 · EDGAR full-text search — the window is a filter

| | hits | outside the requested window |
|---|---|---|
| ADBE, BA, JPM, INTC, BCS | 3 / 0 / 2 / 2 / 0 | **0 / 0 / 0 / 0 / 0** |

`startdt`/`enddt` behave as a hard filter. Latency 0.32–0.70 s.

### A3 · EDGAR per-company Atom — good contract, unreliable service

40 entries each for ADBE, BA and JPM, every one carrying a stable `<id>`
and an `<updated>` timestamp **with a timezone**. But **INTC returned 0
entries after 40.08 s** and BCS 0 (the endpoint filters on `type=8-K`
and Barclays files 6-K). JPM took 4.37 s against ADBE's 0.37 s.

Usable, but not as a primary path: A1 supplies the same facts faster and
without the timeouts.

### A4 · Issuer newsroom feeds — **2 of 5**

| | result |
|---|---|
| **BA** | `boeing.mediaroom.com/…?pagetemplate=rss` — RSS, 5 items, all dated |
| **INTC** | `newsroom.intel.com/feed` — RSS, 10 items, all dated |
| **ADBE** | **no feed** — every candidate returns HTML |
| **JPM** | 404, and a read timeout on the IR host |
| **BCS** | 404 on both candidates |

Sitemaps exist for Boeing, JPMorgan and Barclays but carry `lastmod` —
a *modification* time, not a publication time — with no title and no
publisher. They are not a substitute.

**This matters less than it looks**, because the 8-K exhibit stream
already carries the issuer's own releases: **174 exhibits** across the
32 current reports in the window, filed by the issuer under its own
name, with the regulator's date on them.

### A5 · Regulator publication feeds — 5 of 7

Reachable and dated: **SEC press releases** (25), **DOJ** (25), **CFPB**
(21), **UK FCA** (20), **FTC** (10).

Not reachable: **SEC litigation releases 404**, and **FAA newsroom
403** — which is the source of #193's single best-sourced development
(the FAA restoring Boeing's airworthiness certification authority). A
regulator that blocks automated access is a coverage gap no contract
fixes.

## 4. Lane B — independent reporting

### B1 · GDELT DOC 2.0 — unusable rate

**429 on 9 of 10 attempts**, including five consecutive attempts at 6 s
spacing, each taking ~13 s to return the rejection. One call succeeded
and is the only evidence of its contract:

- returns `domain`, `language`, `seendate`, `socialimage`,
  `sourcecountry`, `title`, `url`, `url_mobile`;
- **75 articles, 0 outside the window, 0 undated** — the datetime filter
  works;
- **no publisher field** — only `domain`, and the brief states hostname
  alone is insufficient;
- **`seendate` is GDELT's crawl time, not the publisher's publication
  time** — the aggregator-ingestion-versus-publisher-time distinction
  the brief asks to be measured, decided against it;
- no stable item id beyond the URL, no summary, no updated timestamp,
  no source type.

Free and keyless, and neither its rate nor its field set is admissible.

### B2 · Google News RSS — the date and publisher contract holds

| | ADBE | BA | JPM | INTC | BCS |
|---|---|---|---|---|---|
| items | 100 | 100 | 100 | 100 | 100 |
| `<pubDate>` | 100 | 100 | 100 | 100 | 100 |
| `<source>` publisher | 100 | 100 | 100 | 100 | 100 |
| `<guid>` | 100 | 100 | 100 | 100 | 100 |
| distinct publishers | 33 | 45 | 21 | 28 | 27 |

**Window: 0 of 400 items outside the 180 days, 0 undated.** Oldest
returned 2026-02-23/24 against a boundary of 2026-02-19 — and the filter
held even when the `when:180d` operator was omitted.

**What it does not supply:**

- **the canonical article URL.** All 100 `<link>` values point at
  `news.google.com`, and following one lands on
  `consent.google.com/ml?continue=…` — a consent wall, not the
  publisher. The publisher's *home* URL is given; the *article* URL is
  not.
- **a source type.** Reuters and Seeking Alpha arrive identically
  shaped.
- **an origin for rehosts.** `<source>` names the **distributor**:
  *"Boeing (BA) Stock May Be Fully Priced Following Its 12% Slide —
  Yahoo Finance"* is filed with Yahoo Finance as the publisher.
- **any licensing statement** for storing metadata, excerpts or text.

### B3 · Established publisher RSS — excellent metadata, no company query

CNBC (two feeds, 30 items each), NPR (10), BBC (54), The Guardian (40) —
every item dated, with a `guid` and a description. Reuters' agency feed
and AP's business hub both **404**.

The disqualifier is not quality. These are **general business feeds with
no company parameter**: across 164 items the five corpus companies were
mentioned incidentally at most (CNBC business: Boeing 3, JPMorgan 3,
Intel 1). Company-specific acquisition would mean ingesting every
publisher's entire output and filtering — a different and much larger
proposition than a query.

## 5. Company identity — the blocker that survives

The brief asks that a ticker-only query be tested against reassignment
and collision. It fails comprehensively.

| query | what came back |
|---|---|
| **`PARA`** | USA Cycling **Para**-Cycling, FIH **Para** Hockey World Cup, USATF **Para** National Championships, FEI **Para** Dressage, **Para** South American Games — **zero Paramount items** |
| **`BA`** | British Airways Media Centre, British Airways/Pratt & Whitney, British Airways/Amex — and **"SARS-CoV-2 Omicron BA.2.86 and JN.1 expand tropism in human proximal intestinal epithelium"** |
| **`ADBE`** | Adobe, but almost entirely stock commentary — Yahoo Finance, Trefis, StockStory |
| `"The Boeing Company"` | materially cleaner: Boeing deliveries, af.mil, Boeing Newsroom, an Archer acquisition of a Boeing business |
| `Paramount` | the Paramount-Warner merger — **and Joe Lovano's "Paramount Quartet" in JazzTimes** |

**A ticker-only query resolves a string, not an issuer**, which is #192's
principle arriving on a second lane. A quoted legal name is materially
better and still not sufficient, and **no free feed exposes a CIK, LEI or
vendor entity identifier** to resolve against.

For every accepted item the brief requires a reason it belongs to the
company. On this lane the only available reason is *the query string
appeared* — which the brief explicitly rejects.

## 6. Minimum record contract, field by field

| field | EDGAR | Google News RSS | GDELT | publisher RSS |
|---|---|---|---|---|
| stable provider item id | **accession** | `<guid>` | ✗ (url only) | `<guid>` |
| canonical article URL | **yes** | **✗ Google redirect** | yes | yes |
| originating publisher | **the filer** | name, **but the distributor for rehosts** | ✗ (domain only) | **itself** |
| host kept apart from publisher | n/a | ✗ | ✗ | n/a |
| publication timestamp + tz | **yes** (two dates) | **yes** | **crawl time, not publication** | yes |
| updated timestamp | new accession | ✗ | ✗ | ✗ |
| hard query start/end | **yes, 0 leakage** | **yes, 0 leakage** | yes | ✗ (no query) |
| resolved company identity | **CIK, guarded by #192** | **✗ string match** | ✗ | ✗ |
| query match basis | the filer's own CIK | ✗ | ✗ | ✗ |
| headline | title | yes | yes | yes |
| summary / content | **full document** | ✗ | ✗ | description |
| source type | form + item code | ✗ | ✗ | n/a |
| pagination / cursor | index + `from`/`size` | ✗ (100 cap) | `maxrecords` | ✗ |
| correction behaviour | **new filing, never in place** | unknown | unknown | unknown |
| historical lookback | **full archive** | ~180 d observed | documented | feed length |
| rate limit | courtesy delay | not stated | **429 at 6 s spacing** | not stated |
| storage / licence | **public domain** | **unstated** | terms page fetched, no explicit grant found | per publisher |

**An item lacking publisher or publication date is inadmissible.** By
that rule Google News RSS items are admissible on *date and publisher*
and inadmissible on *identity, canonical URL and licence*.

## 7. Adobe acceptance

### A — CEO succession from regulator or issuer material: **passes**

8-K accession `0000796343-26-000048`, occurred 2026-03-09, filed
2026-03-12, publisher Adobe Inc. as filer, retrieved through the
identity guard merged in #192 with the CIK in the document's own address
agreeing with the ticker map. Three EX-99 exhibits are attached — the
issuer's own release, filed under its own name and the regulator's date.

Both publisher and date are established, exactly as required.

### B — an admissible independent source on generative-AI competition: **passes, barely**

168 items across three queries, **78 distinct publishers**, of which
**2 are from an established outlet** — both Reuters:

- *"Adobe launches AI suite for corporate clients as competition heats up"* — 2026-04-20
- *"Adobe shares drop as CEO exit fans uncertainty over AI strategy"* — 2026-03-13

**This is a change from #193**, where generic search returned zero
admissible sources and the development had to be refused. A feed with a
publisher field retrieves it.

Two cautions travel with it. The admissible rate is **1.2%**, in a
corpus led by Seeking Alpha (25), TradingView (16), TradingKey (7),
Yahoo Finance (6) and — again — a crypto outlet writing about Adobe. And
the second Reuters headline is itself **causal** (*"shares drop as CEO
exit fans uncertainty"*), which is precisely the claim the platform is
forbidden to adopt: it is retained as the publisher's words, never as
this platform's.

## 8. Negative controls

The five categories #193 measured on generic search were searched for in
300 Google News items across three companies. **None was found** — no
`lawfold`, no `classaction.org` category page, no `theaicronicle`, no
university handout. Google News applies a publisher-inclusion policy
that generic search does not.

**The negative controls did not disappear; they changed shape.** What
dominates instead is stock-commentary aggregation — Seeking Alpha,
TradingView, TradingKey, StockStory, Trefis, 24/7 Wall St., TIKR — plus
rehosts filed under the distributor's name. The feed **labels none of
them**: an item from Reuters and an item from TradingKey are
structurally identical, because there is no source-type field.

## 9. Non-U.S. coverage

Barclays, on the same query shape: **100 items, 0 outside window, 0
undated, 34 from an established UK or global outlet.**

| publisher | items |
|---|---|
| Home.Barclays | 17 |
| Reuters | 16 |
| Bloomberg | 12 |
| Barclays Investment Bank | 9 |
| Yahoo Finance | 6 |
| The Guardian | 4 |
| CNBC | 3 |
| Financial Times | 2 |

Two findings worth stating plainly. **Non-U.S. coverage on Lane B is
better than the U.S. independent lane for a diffuse topic** — 34 of 100
admissible against Adobe's 2 of 168. And **the aggregator recovers
issuer publications the issuer's own site does not expose**:
`home.barclays` has no working RSS, yet 26 of its releases arrived
through the feed, dated.

Barclays' 2026-08-17 Reuters item — *"Barclays names former Bank of
America executive Joo as co-CEO of investment bank"* — is a leadership
development for an issuer that files no 8-K. Lane B reaches what Lane A
structurally cannot.

## 10. Cost and operations

| | auth | free allowance | live-tested | latency | errors |
|---|---|---|---|---|---|
| EDGAR (all surfaces) | none | unlimited, courtesy delay | **yes** | 0.18–0.70 s (Atom to 40 s) | 2 endpoints 403/404 |
| Google News RSS | none | not stated | **yes** | ~1 s | none observed |
| GDELT DOC 2.0 | none | not stated | **yes** | ~13 s to a 429 | **90%** |
| publisher RSS | none | not stated | **yes** | <1 s | Reuters, AP 404 |
| NewsAPI, Marketaux, Finnhub, Polygon, Alpha Vantage | **API key** | documented | **no — would require accepting terms** | — | — |

**Nothing is recommended for being free.** EDGAR is recommended for
being *authoritative, identified and dated*; Google News RSS is **not**
recommended, despite being free and having the best date contract on the
lane, because identity, canonical URL and licence are all missing.

## 11. Conclusion

# B — AUTHORITATIVE LANE READY, INDEPENDENT LANE BLOCKED

**Lane A is ready now.** EDGAR supplies a stable item identity, two
dates per item, a resolved company identity guarded by #192, the issuer's
own releases as attached exhibits, an immutable correction model, full
history, and public-domain licensing — for U.S. issuers and for foreign
private issuers alike, the latter through 6-K rather than 8-K.

**Lane B is blocked on three specific things, and the date contract is
not one of them.** #193's finding must be narrowed: search has no date
contract, a feed does.

### The exact rulings required

1. **A company-identity contract.** No free feed resolves an issuer, and
   a ticker-only query is disqualifying — `PARA` returns para-sport and
   `BA` returns a SARS-CoV-2 lineage. Either a provider that carries a
   registry or vendor entity identifier is licensed, or this platform
   owns a resolution step that decides, per item, why it belongs to the
   company. **The second is not free**: it is the measurement this
   research recommends next.
2. **Canonical URL and storage rights.** Google News RSS supplies
   neither the article URL nor any statement of what may be stored.
   Without both, an item cannot be retained, re-checked or cited.
3. **An access decision on the keyed providers.** NewsAPI, Marketaux,
   Finnhub, Polygon and Alpha Vantage all require an account and
   acceptance of terms, which this task was forbidden to do. Whether
   they satisfy the identity and licensing gaps is **unmeasured and
   measurable** — and it is an owner decision, not a research one.

### Recommended next measurement

**One keyed financial-news provider, under owner approval, tested
against exactly this contract** — specifically whether it supplies a
vendor entity identifier that survives a ticker reassignment, a
canonical publisher URL, an explicit storage grant, and a source type.
Two candidates are worth one free-tier test each; the ruling needed
first is permission to create an account.

Until then, a Radar built on Lane A alone would be **authoritative,
dated, identified and narrow** — and would systematically miss Adobe's
competitive development and Barclays' co-CEO appointment, both of which
Lane B retrieved and neither of which any regulator files.

## 12. Scope compliance

Research only · no production provider integration · no scraping
framework · no development clustering · no sentiment, thesis implication
or BUY/SELL/HOLD · **zero model calls** · no CIO, analyst, committee or
decision change · no mutation of production evidence (`git status
--porcelain data/` empty) · Codex's unpublished leadership parser not
read, reused or published · **no subscription purchased, no trial
started and no terms accepted** — every keyed provider is reported as
documentation-only and is labelled as such throughout.
