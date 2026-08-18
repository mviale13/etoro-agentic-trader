# Reuters could not be opened

**Status: research. 3 requests, 15 web searches (cap 12, exceeded inside
the third response), USD 0.17 of the USD 1 cap. No production
implementation, no SDK change, no payload committed, no article body
stored, no development object created.**

One question: **can this route retrieve admissible independent reporting
when the filter permits only the eight reviewed independent domains — no
regulator, no issuer, no aggregator?**

> **No — and it failed at the easiest possible test.** The three known
> articles from #194 were named in the prompt by their own headlines.
> **All three returned zero citations.** The model's own account is not
> ambiguous: *"I could not access Reuters from my browsing tool … My
> attempt to open Reuters returned an access error."*
>
> **`reuters.com` was never successfully consulted in any of the three
> controls.** Bloomberg, WSJ, The Guardian and the BBC were reached, so
> the domain filter itself works — it is Reuters specifically that could
> not be opened, and all three known articles live there.
>
> **The budget broke before the discovery half could run.** Three
> requests produced **15 web searches** against a cap of 12; the run
> stopped before issuing a fourth. **Tests B and C were never
> executed**, and this report does not pretend otherwise.

---

## 1. The fixed eight-domain set

Reused from #196 exactly, written here before the calls were made, and
**not widened after seeing any result**:

`reuters.com` · `apnews.com` · `bloomberg.com` · `wsj.com` · `ft.com` ·
`cnbc.com` · `bbc.co.uk` · `theguardian.com`

**Prior rationale, unchanged**: wire services and papers of record with a
named masthead and published editorial standards, selected a priori
rather than because an earlier search returned them. No issuer domain,
no regulator domain, no aggregator.

## 2. Configuration

| | |
|---|---|
| model | `gpt-5-mini` |
| tool | `web_search`, `search_context_size: "low"` |
| filter | `filters.allowed_domains` = the eight above |
| tool_choice | **`"auto"`** — not forced, per ruling 5 |
| include | `["web_search_call.action.sources"]` |
| citations | `url_citation` annotations only, per ruling 6 |
| not passed | `external_web_access`, forced `tool_choice`, model-generated URL or publisher fields |

## 3. Ledger

| # | request | searches | consulted | **cited** | latency | in | out | cum. searches | cum. USD |
|---|---|---|---|---|---|---|---|---|---|
| 1 | A1 Reuters — Adobe AI suite | 4 | 14 | **0** | 55.7 s | | | 4/12 | 0.047 |
| 2 | A2 Reuters — Adobe CEO exit | 4 | **0** | **0** | 40.8 s | | | 8/12 | 0.094 |
| 3 | A3 Reuters — Barclays co-CEO | **7** | 3 | **0** | 50.1 s | | | **15/12** | 0.173 |
| — | B1, B2, C | — | — | — | **not issued** | | | search cap reached | |

**Totals: 3 requests of 6 · 15 searches of 12 · USD 0.173 of 1.00 ·
28,947 input and 7,759 output tokens.**

The third response performed **seven** searches on its own initiative.
A single response may exceed the intended action count, as the brief
anticipated; it is reported and no further request was issued.

## 4. Test A — known-article recovery controls

The easiest test available: the article already exists, its headline is
given, its publisher is named, and the filter permits that publisher.

### A1 — *"Adobe launches AI suite for corporate clients as competition heats up"*

- searches **4**, sources consulted **14**, citations **0**
- hosts consulted: `bloomberg.com`, `theguardian.com`, `wsj.com` —
  **`reuters.com` absent**
- the model said: *"I searched for that Reuters article, but **I could not
  access Reuters from my browsing tool** and therefore couldn't retrieve
  or verify any Reuters item. My attempt to open Reuters returned an
  access error."*

### A2 — *"Adobe shares drop as CEO exit fans uncertainty over AI strategy"*

- searches **4**, sources consulted **0**, citations **0**
- **no host was consulted at all** despite four search actions
- the model said: *"My attempts to open Reuters search pages returned no
  retrievable results (the search/open calls failed)."*

### A3 — *"Barclays names former Bank of America executive Joo as co-CEO of investment bank"*

- searches **7**, sources consulted **3**, citations **0**
- hosts consulted: `bbc.co.uk`, `theguardian.com` — **`reuters.com`
  absent**
- the model said: *"I could not find that Reuters article … I was unable
  to locate a Reuters item that matches that title or that reporting in
  the date range you specified."*

### What this establishes

**Three of three known articles: not reachable. Zero citations across
all three.**

The failure is not a judgement failure. The filter worked — four of the
eight permitted domains were consulted successfully. **The substrate
could not open `reuters.com`**, and Reuters is where all three known
articles live, and where both of #194's admissible Adobe items and its
Barclays co-CEO item came from.

A second observation, smaller and worth recording: consulting is not
retrieving. A1 consulted 14 sources across Bloomberg, WSJ and The
Guardian and cited **none** — consistent with those outlets' paywalls,
which #194 flagged as biasing any corpus away from established
reporting.

### One artifact, exactly as ruling 6 anticipates

Two responses emitted an **empty markdown citation `([]())`** in the
prose where a source would go. There is no annotation behind it. This is
precisely why citation annotations, not model-written links, are the
only source carrier: the prose contained a citation-shaped object
pointing at nothing.

## 5. Tests B and C — not executed

**B (unknown-development discovery, run twice)** and **C (independent
negative control)** were never issued, because the search cap was
reached inside A3's response and the budget rule stops before the next
request rather than after it.

So this report cannot state:

- whether independent reporting can be *discovered* rather than
  recovered from a known title;
- the two-run overlap, contradiction, date or cost comparison;
- whether the model correctly refuses rather than substituting an
  issuer, regulator or unreviewed source when nothing independent
  exists.

**They are open, not answered.** Recording them as untested is the
honest outcome; inferring them from A would be inventing a measurement.

That said, **B cannot succeed where A failed**: discovery of an unknown
Adobe development requires reaching publishers that reporting lives on,
and the largest of the eight could not be opened even when named. A
would have to pass before B was worth buying.

## 6. Source and date audit

Vacuous by construction, and stated rather than omitted: **zero
citations were produced across the three executed requests**, so there
is no cited page to audit for company identity, topic, publication date,
page type, rehosting or claim support. No item met acceptance condition
1 — *its URL comes from a citation annotation* — because no annotation
was returned.

No development was recorded. No interpretation was recorded. The
interpretation rule was never reached, because no publisher's causal
wording was retrieved to restate.

## 7. Conclusion

# C — INDEPENDENT REPORTING UNREACHABLE

The known Reuters controls could not be retrieved even when only
reviewed independent domains were permitted, and the model reported an
explicit access error against Reuters in two of the three.

**This route inherits #194's independent-source coverage blocker.** It
does not close it.

### The Company Development Radar direction stops here

Nothing is built. The chain of findings is now complete and each step is
measured rather than argued:

| | |
|---|---|
| **#193** | generic web search has no date or source contract |
| **#194** | a feed has a date contract; identity, canonical URL and licence are missing |
| **#195** | the licensed provider's free tier forbids the non-display, derived use a Radar is |
| **#196** | on-demand cited search works on regulator and issuer sources, is not repeatable, and never cited an independent publisher |
| **this** | and when only independent publishers are permitted, the largest of them cannot be opened at all |

The motivating case — Adobe's externally reported competitive pressure —
is not reachable by any acquisition route this platform has measured.
**The authoritative lane remains ready and remains insufficient for that
case**, which is the same position #196 left, now with the last
alternative closed.

### What this does not rule out

The failure measured is a **substrate reachability** failure against one
publisher, observed on one day from one environment. It is not a finding
about Reuters' licensing, about the eight-domain set, or about whether
the API would behave identically elsewhere. Re-testing later would cost
three requests and would be worth doing before treating the direction as
permanently closed.

## 8. Scope compliance

Research only · no production code · no Radar, development-card or
authoritative-lane implementation · no model-generated source fields
requested · no provider account, no Massive, no SDK change · no article
storage, snippet corpus or embedding · no sentiment, score, confidence,
recommendation or price causation · no analyst, committee, CIO or
decision change · no mutation of production evidence (`git status
--porcelain data/` empty) · Codex's unpublished leadership branch not
read, reused or published · payloads written outside the repository and
deleted before commit · the credential was read through the
application's own settings loader, never printed, logged, copied or
written, and is redacted from every error path.
