# The citations are real; the second run is not

**Status: research. 9 API calls, 20 of 20 authorised web searches spent,
~USD 0.30 of the USD 5 cap. No production implementation, no SDK change,
no provider account, no article body retrieved, no payload committed, no
production data mutation.**

The hypothesis was that MOVRvest could ask the Responses API to search
live on demand, retain only a derived description plus citations, and
display those citations — avoiding the corpus, the licence and the
retention problems #194 and #195 measured.

> **The contract is real and it mostly works.** Domain-filtered search
> returned Adobe's CEO succession with the filed sentence quoted
> verbatim, the occurrence date (9 March) and the publication date (12
> March) kept apart, the interpretation separated, and — the acceptance
> criterion that matters — *"The company has not named a successor in
> these disclosures."* **22 of 22 citations came from a regulator or the
> issuer; zero from anywhere else.**
>
> **`external_web_access` does not exist.** The brief requires it; the
> API rejects it outright — `400 Unknown parameter:
> 'external_web_access'`. This is the live API refusing the field, not
> the pinned SDK lacking a type for it.
>
> **And an identical prompt, run twice, produced 14 citations and then
> zero.** Same model, same text, same tool: run 1 took 71.5 s, consulted
> 26 sources and cited 14; run 2 took 19.6 s, consulted 41 and cited
> **none**. That is not a tuning problem — it is the reason a *retained*
> development card cannot rest on this yet.
>
> **Independent reporting was never retrieved.** Across both Adobe runs
> every single citation is `sec.gov`, `news.adobe.com` or
> `blog.adobe.com`. Acceptance B asked for independent coverage of
> competitive position; what came back is Adobe announcing its own
> partnerships.

---

## 1. API, model and SDK compatibility

| | |
|---|---|
| SDK | `openai==2.53.0`, as pinned. **Not upgraded.** |
| model | **`gpt-5-mini-2025-08-07`** for the measurement; `gpt-5-nano-2025-08-07` for the first probe |
| tool | `{"type": "web_search", "search_context_size": "low"}` |
| include | `["web_search_call.action.sources"]` |
| citations | `url_citation` annotations on the output message |

### What the pinned SDK types, and what it does not

| required by the brief | SDK 2.53.0 | live API |
|---|---|---|
| `tools: [{"type": "web_search"}]` | **typed** (`WebSearchToolParam`) | accepted |
| `filters.allowed_domains` | **typed** | accepted |
| `include: ["web_search_call.action.sources"]` | **typed** (`ResponseIncludable`) | accepted, sources returned |
| `tool_choice: {"type": "web_search"}` | **not typed** — the hosted-tool literal carries `web_search_preview`, not `web_search` | **accepted at runtime** (TypedDicts are not enforced) |
| `external_web_access: true` | **absent from every module** | **REJECTED — `400 Unknown parameter`** |

**The `external_web_access` gap is not an SDK version problem.** Passing
it through `extra_body` — which bypasses the type stubs entirely —
returned:

```text
400 {'error': {'message': "Unknown parameter: 'external_web_access'.",
     'type': 'invalid_request_error', 'param': 'external_web_access',
     'code': 'unknown_parameter'}}
```

The same request without it succeeded immediately. No SDK upgrade would
change this, and none was made.

## 2. Cost, calls and the budget that actually bound

| | |
|---|---|
| API calls | **9** (2 compatibility probes, 7 measurement) |
| **web searches** | **20 of 20 authorised — exhausted** |
| input tokens | ~127,000 |
| output tokens | ~36,000 |
| estimated cost | **~USD 0.30** of USD 5.00 |
| latency | 19.6 s – 71.5 s per call; 393 s across the seven measurement calls |
| retries | 0 |

**The binding constraint was searches, not dollars — and it nearly ended
the measurement at the first call.** The `gpt-5-nano` probe, with
`tool_choice` forcing the tool, performed **10 web searches inside one
request**, spending half the entire budget on a single question.
Switching to `gpt-5-mini`, dropping the forced `tool_choice` and writing
*"Do exactly ONE web search"* into the prompt brought it to 1 per call.

**Even that is not reliable.** The Barclays call performed **two**
searches and said so unprompted: *"One user instruction — 'Do exactly
ONE web search' — could not be met: I executed web searches twice during
preparation."* Honest, and evidence that search count is a request the
model may decline. A production budget cannot be enforced from the
prompt.

## 3. The two search shapes

**Shape A — open discovery.** Legal name, ticker, exchange, CIK, explicit
start and end dates, an instruction to exclude similarly named entities,
and the field contract.

**Shape B — curated-source discovery.** Identical prompt plus
`filters.allowed_domains` over a set chosen **a priori**, not from what
earlier searches returned:

- **regulators** — `sec.gov`, `faa.gov`, `justice.gov`, `ftc.gov`,
  `federalreserve.gov`, `fca.org.uk`: the register is the thing itself.
- **issuers** — `news.adobe.com`, `boeing.com`, `jpmorganchase.com`,
  `newsroom.intel.com`, `home.barclays`: each verified in #194's Lane A
  measurement as the company's own newsroom.
- **independent** — `reuters.com`, `apnews.com`, `bloomberg.com`,
  `wsj.com`, `ft.com`, `cnbc.com`, `bbc.co.uk`, `theguardian.com`: wire
  services and papers of record with a named masthead and published
  editorial standards.

### Domain filtering transforms source quality

| call | cited | regulator | issuer | independent | **other** |
|---|---|---|---|---|---|
| ADBE open #1 | 14 | 6 | 1 | 0 | **7** |
| **ADBE filtered** | 22 | 3 | 19 | 0 | **0** |
| BA open #1 | 2 | 0 | 0 | 0 | **2** |
| **BA filtered** | 4 | 1 | 3 | 0 | **0** |
| BCS open | 19 | 0 | 0 | 0 | **19** |
| PARA control | 2 | 0 | 0 | 0 | **2** |

**Filtering eliminated the unclassifiable tail entirely** — the problem
#193 and #194 both measured, closed by one API parameter. It did not
produce a single independent citation, because none of the eight
independent domains was ever cited in any call.

## 4. Company identity — the chain does not close

**Adobe, Boeing: identity held.** Every cited page names the registrant,
and the SEC citations resolve to CIK 796343 and 12927 — MOVRvest's own
held identity for both, guarded by #192.

**Boeing controls passed.** No British Airways or IAG material was
returned. No SARS-CoV-2 Omicron `BA.*` material was returned. No supplier
or airline-customer story was converted into a Boeing corporate event.

**PARA failed, and failed instructively.** Asked to establish which
registrant currently holds the ticker and to report only on that
registrant, the model:

- named **"Paramount Global"** — citing a Form 3 hosted at
  `ir.paramount.com`, i.e. an issuer-hosted copy, not the register;
- **refused to supply a CIK**: *"I cannot provide the registrant's CIK
  from the single web search I ran because none of the search results
  returned in that single query contained an explicit CIK value"*;
- **reported no developments**, with an explicit refusal;
- and emitted, in a field labelled **"Source URL"**, the string
  **`turn0search12`** — an internal search-turn token, not a URL.

The refusals are the right failure mode and the fabricated URL token is
not. **The provider-owned identity chain the owner specified — article →
ticker → dated reference record → CIK/FIGI → MOVRvest identity —
terminates at step three.** Web search returns pages; it does not return
a dated ticker-reference record, and no cited page supplied a CIK.

## 5. Dates

`published_utc` has no equivalent here: there is no date parameter, only
a date *request* in the prompt. Measured against the window
2026-02-19 → 2026-08-18:

- **Adobe filtered**: every dated item inside the window; occurrence date
  (9 March, from the filing) and publication date (12 March, the press
  release) **correctly kept apart** — the distinction the brief asks be
  tested, answered correctly.
- **PARA**: the model reported *no* qualifying publication in the window
  rather than returning older material — the correct behaviour.
- **Boeing open**: cited `s2.q4cdn.com`, a CDN host for investor
  documents, from which no publication date and no publisher is
  recoverable.

**A prompt date is not a provider date contract**, exactly as the brief
states. It happened to hold here, and nothing enforces it.

## 6. Canonical URLs

**Every one of the 63 citations across all seven calls carries
`?utm_source=openai` appended.** The citation URL is therefore never
byte-identical to the publisher's canonical URL. It is deterministically
strippable, and it must be stripped before storage or display, or every
retained URL will carry a tracking parameter the publisher did not put
there.

Two citations resolve to hosts from which the publisher cannot be
recovered: `s2.q4cdn.com` (a CDN) and `ebs.publicnow.com` (an
aggregator). Hostname alone remains insufficient, as #194 found.

## 7. Adobe acceptance

### A — CEO succession: **passes**

From the domain-filtered call, citing
`sec.gov/Archives/edgar/data/796343/000079634326000048/adbe-20260309.htm`
and `news.adobe.com/news/2026/03/leadership-update`:

| required | returned |
|---|---|
| completed transition notification | *"On March 9, 2026, Shantanu Narayen notified Adobe of his decision to transition from his role as Adobe's Chief Executive Officer"* — quoted verbatim from the filing |
| ongoing search | the special committee, chaired by Frank Calderoni, to direct the process |
| future conditional language | *"has decided to transition from his position as CEO after a successor has been appointed"* |
| **no permanent appointment reported** | **"The company has not named a successor in these disclosures."** |
| interpretation separated | yes, under its own heading |
| source class per source | *"issuer (Adobe press release); regulator (SEC filing)"* |

The accession matches the one #193 measured independently. This is the
acceptance case MC1 could not satisfy and #193 could not source.

### B — generative-AI competition: **fails the independence test**

The model refused generic "AI risk" and named specific developments — an
Adobe–NVIDIA partnership (16 March) and an Adobe–Google Gemini
connector (19 May) — with the non-binding cautionary language quoted and
the source class correctly labelled **issuer**.

But **every citation is Adobe's own**: `news.adobe.com`, `blog.adobe.com`
and `sec.gov`. Across both Adobe calls, **zero independent publishers
were cited**, and the eight independent domains in the filtered set
returned nothing.

So B is not satisfied. What was retrieved is **the company's account of
its own product strategy**, not independent reporting on its competitive
position — and there is no third-party interpretation to separate from
Adobe's assertions, because no third party was cited.

### Presenting A and B side by side

Both were returned in one response as numbered, independently sourced
items with no statement relating them. **Nothing asserted that they
interact adversely**, and nothing connected either to a share-price
movement. The prohibition held without being separately enforced.

## 8. Barclays

**Identity held; the target development was not recovered.**

The call returned an appointment — **Greg Dalle, Managing Director and
Co-Head of EMEA Industrials, Barclays Investment Bank**, announced 24
June 2026 — and correctly scoped it: *"Barclays Investment Bank — EMEA
Industrials Group"*, with no suggestion that it changes the group chief
executive. **The brief's explicit hazard was avoided.**

It did **not** recover the co-CEO development #194 found via Reuters. And
all 19 citations are `publicnow.com` / `ebs.publicnow.com` — an
aggregator that rehosts issuer releases. The originating publisher is one
hop back and is not recoverable from the cited host.

## 9. Repeatability — the disqualifying result

Identical prompt, identical model, identical tool configuration, run
twice:

| | ADBE open #1 | ADBE open #2 |
|---|---|---|
| latency | 71.5 s | **19.6 s** |
| web searches | 1 | **2** |
| sources consulted | 26 | **41** |
| **citations** | **14** | **0** |
| output tokens | 4,224 | **1,453** |

**Candidate overlap: not comparable — the second run produced no cited
development at all.** Cited-source overlap: **zero, necessarily**.

This is not presented as variance to be smoothed. A layer that returns
fourteen citations one minute and none the next cannot be the basis of a
*retained* record, because the retained record would depend on which
call happened to run.

The Boeing repeat could not be performed: the search budget was exhausted
by the earlier calls. That is a gap in this measurement and is recorded
rather than glossed.

## 10. Claim-to-citation audit

**Supported.** Adobe's filed sentence is quoted verbatim and the cited
SEC URL is the filing that contains it — independently confirmed against
accession `0000796343-26-000048` from #193. The Adobe press-release
claims map to `news.adobe.com/news/2026/03/leadership-update`.

**Not supported.** One citation in the PARA call is `turn0search12` — an
internal token presented in a field labelled *"Source URL"*. **A model
inference reached a field reserved for a source**, which is precisely the
failure the factual boundary exists to prevent.

**Sources consulted but not cited**: 26 → 14 (Adobe open), 20 → 22
(Adobe filtered; more citations than sources, because several claims cite
one page), 23 → 2 (Boeing open), 41 → 0 (Adobe repeat). The `sources`
include the brief asked for works and is populated on every call.

## 11. Retention contract

The API supplies enough for the permitted set: **citation URL and title**
(as `url_citation` annotations), **generated description and claims**,
**model identifier** (`gpt-5-mini-2025-08-07`), **acquisition timestamp**,
and a prompt/schema version this platform would own.

It does **not** supply, and the contract does not permit retaining:
publisher name as a field (it is prose inside the generated text, not
metadata), source class as a field (likewise), or a publication date as
metadata. Each is *stated by the model* rather than *returned by the
API* — which means each is a model assertion, and the retention contract
forbids retaining uncited model assertions.

**No page text, snippet, embedding or article body was retrieved or
retained.** All payloads were written to a directory outside the
repository and deleted before commit.

## 12. UI citation obligation

The dossier already carries this shape. `ScoreBasis` renders `basis`
prose with an `evidence` tuple beside it, and the API adapter copies
both verbatim (#189's measurement). A citation URL, a citation title and
a claim-to-citation relationship fit that structure without a new
concept. **Not implemented**, as instructed.

## 13. Conclusion

# B — CITED DISCOVERY READY, DEVELOPMENT CARDS NOT READY

**What is ready.** Domain-filtered on-demand search safely surfaces
cited current reporting. It eliminated the unclassifiable tail that
blocked #193 and #194 — 0 of 26 filtered citations fell outside the
reviewed set — it quoted a filed sentence verbatim, it kept occurrence
and publication dates apart, it separated interpretation from fact, it
refused rather than fabricated when it could not establish a CIK, and it
declined to report an appointment that had not happened.

**What blocks a retained card**, in order of severity:

1. **Repeatability.** An identical prompt produced 14 citations and then
   0. Nothing retained can depend on which run occurred.
2. **Identity does not close.** The provider-owned chain terminates at
   the dated ticker-reference record, which web search does not have.
   PARA produced a historical issuer, no CIK, and a fabricated URL token
   in a source field.
3. **Independent reporting was not retrieved at all.** Every Adobe
   citation is Adobe's or the SEC's. The motivating case — external
   competitive pressure — is still unmet, which was the reason the
   authoritative lane alone was ruled insufficient.
4. **Publisher, source class and publication date are model prose, not
   API metadata**, so the retention contract cannot admit them.
5. **Search count is not enforceable** from the prompt, so cost is not
   bounded by configuration.

### Recommended next slice

**Not a build.** One further bounded measurement, ~10 searches, asking
the single question this one could not: **whether an independent
publisher is ever cited when the filter permits only the eight
independent domains and excludes issuer and regulator domains entirely.**
If Reuters and the FT cannot be reached for Adobe's competitive position
even when they are the only permitted sources, the on-demand route
inherits #194's coverage gap rather than closing it — and that is the
finding that decides whether this direction continues at all.

## 14. Scope compliance

Research only · no production code · **no SDK upgrade** · no Massive
account or call · no news API account · no bulk corpus · no article
storage, snippet corpus or embedding · no clustering, factual
decomposition, development card or thesis mechanism · no sentiment,
confidence percentage or BUY/SELL/HOLD · **no price-movement causation
asserted anywhere** · no Management Continuity, Business Quality,
analyst, committee, CIO or decision change · no mutation of production
evidence (`git status --porcelain data/` empty) · Codex's unpublished
`d203609` not read, reused or published · the credential was read
through the application's own settings loader, **never printed, logged,
copied or written**, and is redacted from every error path; no request
URL carrying it appears in this report or any transcript.
