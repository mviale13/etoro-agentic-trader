# The gate closed before the measurement, and the measurement is the prohibited act

**Status: research, Stage 0 only. Stopped at the permitted-use gate.
Zero model calls, zero spend, no account created, no feed retrieved, no
prototype built, no production implementation, no data mutation. Three
documents fetched: Google's Terms of Service, `news.google.com/robots.txt`
and Google's own crawler documentation.**

The task was to define the smallest useful News Scout over native Google
News RSS, behind a Stage 0 permitted-use gate. The gate is the whole
report.

> **Automated retrieval of `news.google.com/rss/search` is PROHIBITED,
> not silent.** `news.google.com/robots.txt` says `Disallow: /` for every
> user-agent, with a thirteen-path allow-list that does not include
> `/rss`. Google's Terms of Service — effective 30 July 2026 — name it
> directly under *"Don't abuse our services"*: **"using automated means
> to access content from any of our services in violation of the
> machine-readable instructions on our web pages (for example, robots.txt
> files that disallow crawling, training, or other activities)"**. The
> robots file is not adjacent to the contract; the contract incorporates
> it.
>
> **And this platform is blocked twice.** The same file carries a group
> naming `anthropic-ai`, `ClaudeBot` and `Claude-Web` with `Disallow: /`
> and **no allow-list at all** — for those agents not even the homepage
> is permitted.
>
> **So there is no LOCAL PROTOTYPE tier to fall back to.** Conclusion B
> assumes the retrieval is lawful and only the *production rights* are
> unresolved. Here the retrieval is the prohibited act, so a local
> prototype would not be a smaller version of the problem — it would be
> the problem, run once.
>
> **Every measurement the brief asks for requires exactly those
> requests**, so none was made. That is not an incomplete report; it is
> what a gate is for.
>
> **One thing the gate did surface: #194 already made ~400 of these
> requests**, and its licence review recorded *"any licensing statement —
> missing"* without checking `robots.txt`. The gap was in the method, not
> in the conclusion it reached.

---

## 1. Stage 0 — the permitted-use classification

### The primary sources, quoted

**`https://news.google.com/robots.txt`**, retrieved in full (484 bytes,
HTTP 200):

```text
User-agent: *
Disallow: /
Allow: /$
Allow: /?
Allow: /home$
Allow: /home?
Allow: /home/
Allow: /nwshp$
Allow: /topics/
Allow: /publications/
Allow: /stories/
Allow: /swg/
Allow: /about$
Allow: /about?
Allow: /about/

User-agent: Googlebot
Disallow: /
Allow: /$
Allow: /?
Allow: /home$
Allow: /home?
Allow: /home/

User-agent: CCBot
User-agent: GPTBot
User-agent: ChatGPT-User
User-agent: PerplexityBot
User-agent: anthropic-ai
User-agent: ClaudeBot
User-agent: Claude-Web
Disallow: /
```

**Google Terms of Service, effective 30 July 2026**, section *"Don't
abuse our services"*, eighth bullet, verbatim:

> *"using automated means to access content from any of our services in
> violation of the machine-readable instructions on our web pages (for
> example, robots.txt files that disallow crawling, training, or other
> activities)"*

and, in the same list:

> *"using our services (including the content they provide) to violate
> anyone's legal rights, such as intellectual property or privacy
> rights"*

### The path test

`/rss/search?q=…` is matched by no `Allow` rule in the `*` group. The
allow-list covers `/`, `/home`, `/nwshp`, `/topics/`, `/publications/`,
`/stories/`, `/swg/` and `/about` — and nothing else. Under Google's own
published robots specification the longest matching rule wins; here the
only matching rule is `Disallow: /`.

**There is no officially documented Google News feed or API to hold a
permissive grant.** Google retired the Google News API in 2011 and has
published no replacement, so the `/rss/search` endpoint is undocumented
rather than licensed. **Nothing here can be classified `PERMITTED`
because no grant exists to read.**

### The classification

| required use | classification | the clause that decides it |
|---|---|---|
| **Automated RSS retrieval** of `/rss/search` | **PROHIBITED** | `robots.txt` `Disallow: /`, incorporated by the ToS abuse bullet |
| Automated retrieval **by this platform's own agents** | **PROHIBITED**, independently and totally | the `anthropic-ai` / `ClaudeBot` / `Claude-Web` group, no allow-list |
| **Display in an application** | **REQUIRES CLARIFICATION** on its own terms — and **unreachable**, because the only lawful input is missing | ToS: using the content to *"violate anyone's legal rights, such as intellectual property"*; Google grants no publisher rights |
| **Caching feed identifiers and metadata** | **SILENT** — and moot | no clause addresses caching feed metadata; the retrieval that produces it is prohibited |
| **Persistent storage** | **SILENT** — and moot | the word *storage* appears in neither document |
| **Commercial or production use** | **PROHIBITED** | inherits the retrieval prohibition; no separate grant exists |

**Two of the six are `SILENT`, and silence is not the blocker.** The
blocker is the first row, and it is upstream of everything else: a use
that cannot lawfully begin does not need its downstream rights resolved.

### The strongest counterargument, and why it fails

Google documents that **Feedfetcher** — the crawler that reads RSS and
Atom feeds for Google News — *ignores* `robots.txt`, on the stated
grounds that it acts as a direct agent of a human user rather than as a
robot.

It does not transfer. That rule describes **Google's fetcher reading
publishers' feeds**; it is Google explaining its own behaviour on other
people's servers. It grants nobody permission to read **Google's own**
disallowed paths, and it runs in the opposite direction to the use
proposed here.

A second reading — that `robots.txt` governs only crawling for search
indexing, so a scheduled feed poll is something else — is closed by the
contract's own wording: *"robots.txt files that disallow crawling,
training, **or other activities**"*.

**I am not a lawyer and this is not legal advice.** It is a reading of
two published documents, both quoted above so the reading can be checked
rather than trusted.

---

## 2. What was therefore not measured

Every item below requires repeated automated requests to the disallowed
path. **None was performed.** They are listed so that the report is
plainly an unfinished measurement blocked at a gate, not a measurement
that came back empty.

| the brief asked for | status |
|---|---|
| query forms 1–6 (ticker, name, OR, financial context, six categories, negative terms) | **NOT MEASURED — blocked at Stage 0** |
| items returned per query | **NOT MEASURED** |
| publisher / date completeness | **NOT MEASURED** (#194 recorded 100% over 400 items, obtained from the disallowed path) |
| window leakage | **NOT MEASURED** (#194 recorded 0 of 400 outside 180 days, same provenance) |
| BA and PARA collision rate | **NOT MEASURED** — and it is the measurement that mattered most |
| duplicate GUIDs · normalized-headline duplicates | **NOT MEASURED** |
| query overlap | **NOT MEASURED** |
| result latency · feed stability across repeated reads | **NOT MEASURED** |
| minimum information for incremental "new since last read" | **NOT MEASURED** |

**No negative control was run either**, so this report establishes
nothing about how often an unrelated issuer is returned — which is
exactly the risk the negative controls existed to size.

---

## 3. What is settled without any new retrieval

Two questions the brief asks can be answered from #194's own recorded
observations, because they are properties of the endpoint rather than
of a sample.

### Google discovery links can never be treated as canonical publisher links

**Settled: no.** #194 recorded that all 100 `<link>` values in each feed
point at `news.google.com`, and that following one lands on
`consent.google.com/ml?continue=…` — a consent wall, not the publisher's
article. The feed supplies the publisher's *home* URL and never the
*article* URL.

This is structural. No query form, sampling window or retry changes it,
and it disqualifies `discovery_url` from being the *"open discovery
result"* affordance the object is built around: the one thing an
investor would do with a lead — open it — does not work.

### `<source>` names the distributor, not the origin

**Settled: yes.** #194 recorded *"Boeing (BA) Stock May Be Fully Priced
Following Its 12% Slide — Yahoo Finance"* filed with **Yahoo Finance** as
publisher. So `publisher_label` is a rehost label, and safe wording must
never call it the source.

---

## 4. The `NewsLead` object, reviewed without data

The object is well-shaped where it matters and it has one structural
problem the gate does not cause.

**What is right.** `queried_company_identity` recording *why the query
was run* rather than asserting the item concerns that company is the
correct separation, and it is the same discipline as Invariant 2 —
identity is not established by having asked. `refusal_reason` beside a
status, and `retrieved_at` beside `published_at`, are both right.

**The structural problem: three of the four verification states are
unreachable from this source.**

| state | reachable? |
|---|---|
| `UNVERIFIED` | yes — every item |
| `IDENTITY_CONFIRMED` | **no** — the feed carries no issuer identifier, and #194 found no CIK, ISIN, LEI or ticker field |
| `SOURCE_VERIFIED` | **no** — there is no canonical article URL to verify against |
| `REFUSED` | yes |

A `verification_status` whose only attainable values are *unverified*
and *refused* is not a state machine; it is a constant with a refusal
branch. The inbox it produces would be **permanently unverified by
construction**, and the honest label for that is not *"lead"* but
*"headline we cannot attribute, linking to a consent wall"*.

**This is worth recording even though the gate makes it moot**, because
it is the finding that would have decided the slice on product grounds
had the rights been clean: the phase gate asks what becomes better for
the investor, and a permanently unverified inbox whose links do not open
does not yet answer it.

---

## 5. #194's provenance, reported rather than buried

#194 retrieved **400 items across five companies** from
`news.google.com/rss/search`. Its licence review recorded *"any
licensing statement — **missing**"* and marked the lane inadmissible on
identity, canonical URL and licence. It did not check `robots.txt`, and
`robots.txt` is where the answer was.

Three things follow, and they are separate:

1. **#194's conclusion is unaffected.** It ruled the lane inadmissible;
   this report finds a further and stronger reason it is inadmissible.
2. **#194's measurements were obtained from a disallowed path.** They
   remain in the record as a description of what the endpoint returned;
   nothing in this platform consumes them, and nothing should begin to.
3. **The method gap is the reusable lesson.** *A missing licence
   statement and a machine-readable refusal are two different findings,
   and only one of them requires reading a second file.* A future source
   review fetches `robots.txt` **before** the first data request, not
   after four hundred of them.

---

## 6. Re-entry conditions

Each is checkable, and none is a retry of the same request.

1. **A written grant from Google** covering automated retrieval,
   display, caching and storage of Google News feed content — a licensed
   product or an agreement. Until one exists there is nothing to
   classify as `PERMITTED`, and a same-day retry is not a re-entry
   condition.
2. **Drop Google entirely and read publishers directly.** #194 measured
   per-publisher RSS as metadata-excellent and **company-query-less**:
   CNBC, NPR, BBC and The Guardian all dated with GUIDs, but no company
   parameter, so company-specific acquisition means ingesting whole
   feeds and filtering. That is a larger and different proposition, and
   it is lawful on its face — each publisher's own `robots.txt` and
   terms decide it, one publisher at a time.
3. **A licensed news vendor whose terms permit non-display use and
   derived works.** The Massive review already measured that the free
   Individuals tier forbids exactly this — *"Use Market Data for
   non-display use or to create derivative works"* — so this route means
   a business tier **and written confirmation that third-party news
   articles fall inside or outside "Market Data"**, which that review
   left unresolved.
4. **Issuer newsrooms**, which #194 found live for BA
   (`boeing.mediaroom.com`) and INTC (`newsroom.intel.com`) — first-party,
   company-scoped, and carrying the issuer identity Google News does not.

**EDGAR is untouched by any of this.** It remains the authoritative,
identified, dated, public-domain lane, and nothing in this report
changes it.

---

## 7. Conclusion

# C — NOT READY

**The blocker is permitted use, and it is established rather than
suspected.**

`news.google.com/robots.txt` disallows `/rss/search` for every
user-agent, and Google's Terms of Service — effective 30 July 2026 —
make automated access in violation of that file a breach by name. This
platform's own agents are additionally named in the file and blocked
outright with no allow-list.

**Conclusion B was unavailable, and the reason is worth stating.** B
reads *"local prototype ready, production rights unresolved"*, which
presumes a lawful retrieval whose downstream rights are open. Here the
retrieval is itself prohibited, so there is no smaller lawful version to
build: a local prototype is the same act performed once. The brief's
instruction to *"keep the work local and conclude at most LOCAL
PROTOTYPE READY"* anticipated `SILENT`; the finding is `PROHIBITED`.

**Two findings survive the gate and are independent of it:**

- **A Google News discovery link can never be a canonical publisher
  link.** It resolves to a consent wall, structurally, so the object's
  one investor-facing affordance does not work.
- **Three of `NewsLead`'s four verification states are unreachable from
  this source**, so the inbox would be permanently unverified by
  construction — a product objection that would stand even with clean
  rights.

**Nothing was built and nothing was retrieved from the feed.** The
smallest justified next step is not a smaller prototype; it is
re-entry condition 2 or 4 — publisher and issuer feeds, whose rights are
decided one publisher at a time and whose identity is first-party — or
nothing at all, which is also an acceptable answer to a source that
cannot lawfully be read.

## 8. Scope compliance

Research only, Stage 0 only · **no feed request issued to
`news.google.com`** · no prototype, no production implementation, no
production integration · no `CompanyDevelopment` created · no claim
extraction, source-chain assertion, article-count vote, sentiment,
materiality, price causation, thesis implication or BUY/SELL/HOLD · no
article body retained · no RSS.app or feed converter · **zero model
calls** · zero spend, no account created · no data mutation,
`git status --porcelain data/` empty · no form-aware dispatch, no
development cards · Codex's unpublished `d203609` not read, reused or
published.
