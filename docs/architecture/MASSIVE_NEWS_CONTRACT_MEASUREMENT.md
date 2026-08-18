# The clause that decides it is not in the terms you agree to

**Status: research. 3 API requests, all unauthenticated. USD 0.00. Zero
model calls. No account created, no payment, no trial, no provider
integrated, no provider data retained, no production implementation.**

The task was to determine whether Massive closes the independent-lane
blockers #194 measured. The technical probe did not run, and it did not
need to: the licensing review — which required no account — settles the
question on its own.

> **A Company Development Radar is non-display use producing derived
> works, and that is precisely what the free tier forbids.** The Massive
> for Individuals Terms of Service incorporates a separate **Market Data
> Terms of Service** by reference, and it is that second document, not
> the one an account holder accepts at signup, which carries the
> operative clause:
>
> > *"…you may not: … (c) Redistribute, display, … or otherwise transfer
> > the Market Data—or any data, charts, analytics, research, or other
> > works based on, referring to, or **derived from** the Market Data
> > ("**Derived Works**")—to any third party or use the Market Data for
> > business or commercial purposes; (d) **Use Market Data for
> > non-display use or to create derivative works** … unless you are
> > licensed to do so"*
>
> **The word "storage" appears zero times in either document**, and
> neither states whether third-party news articles delivered through the
> API fall inside the definition of "Market Data". Both are marked
> `WRITTEN PROVIDER CLARIFICATION REQUIRED` rather than resolved by
> inference.
>
> **So the technical contract is secondary.** However well the API
> performs on identity, URL and date, production requires the *Massive
> for Businesses* agreement, and the free tier cannot lawfully be used
> to build what this platform intends to build.

---

## 1. What was tested, and what was not

| | |
|---|---|
| account created | **none** |
| plan tested | **none** |
| API requests | **3**, all unauthenticated |
| USD spend | **0.00** |
| model calls | **0** |
| provider data retained | **none** — no payload was written anywhere |

**The probe did not run because account creation is a step this agent
must not perform.** Signup requires email verification, and creating
accounts and authenticating is outside what may be done on the owner's
behalf under any circumstances. No disposable identity was created, no
credential borrowed and no verification bypassed — the brief's own stop
condition, invoked as written.

The owner was asked and ruled: **conclude on the licensing evidence, do
not pursue the probe.**

### The three requests that were made

| endpoint | status | latency |
|---|---|---|
| `/v3/reference/tickers` | **401** *API Key was not provided* | 0.38 s |
| `/v3/reference/tickers/{ticker}?date=…` | **401** | 0.30 s |
| `/v2/reference/news` | **401** | 0.30 s |

They establish only that the three endpoints the identity chain would
need **exist, are reachable, and reject an unauthenticated caller
cleanly**. No key existed to be leaked, and no request URL carrying one
appears in this report, any transcript or any file.

**A note on the name.** `polygon.io` now redirects to **`massive.com`**.
`massive.io` is a different company (MASV, file transfer) and is not the
provider under test — a confusion worth recording before anyone follows
a stale link.

## 2. The document chain, which is the finding

`massive.com/legal/terms` is a **1,433-character index**, not an
agreement. It points at three separate documents and states which
governs what:

| document | governs |
|---|---|
| Website Terms of Service | use of `massive.com` itself |
| **Massive for Individuals ToS** (37,813 chars) | *"personal, individual, non-business, or non-commercial use"* |
| **Massive for Businesses ToS** (60,752 chars) | *"individual, business, or commercial use"* |

The Individuals ToS then incorporates a fourth:

> *"Market Data is provided to you subject to the terms and conditions of
> the **Market Data Terms of Service**, which are incorporated herein by
> reference."*

**The operative restrictions are in the incorporated document, not in
the one accepted at signup.** An evaluation that read only the terms
presented during registration would have found the Individuals ToS
silent on storage, silent on derived works, silent on non-display use —
and would have concluded, wrongly, that nothing prohibited the intended
use.

## 3. Retention matrix — the eight questions

Answered from the documents' own words. Where they are silent, that is
recorded as silence.

| # | question | answer | basis |
|---|---|---|---|
| 1 | May the free account be used for **this private technical evaluation**? | **Apparently yes** | Individuals ToS governs *"personal, individual, non-business, or non-commercial use"*. A private, non-commercial technical evaluation by an individual falls inside that description on its face |
| 2 | May **metadata** be stored? | **`WRITTEN PROVIDER CLARIFICATION REQUIRED`** | The word *storage* appears **0 times** in either document. The nearest clause forbids Market Data being *"copied, reproduced, republished, uploaded, posted, publicly displayed, encoded, translated, transmitted, or distributed … to any other computer, server, website, or other medium"* — but scoped *"for publication or distribution or for any business or commercial enterprise"*. Private retention is neither granted nor refused |
| 3 | May **headlines or descriptions** be stored? | **`WRITTEN PROVIDER CLARIFICATION REQUIRED`** | Same silence, plus an unresolved prior question: whether third-party news text is "Market Data" at all (§4) |
| 4 | May **article text** be stored? | **No, and moot** | The API supplies no article body. Reproduction is separately restricted by the clause in row 2 |
| 5 | May **embeddings or derived structured facts** be stored? | **No, on this tier** | Market Data ToS (d): *"Use Market Data for **non-display use** or to create **derivative works** … unless you are licensed to do so"*. "Derived Works" is defined to include *"data, charts, analytics, research, or other works based on, referring to, or derived from the Market Data"* — a development card is squarely inside that definition |
| 6 | May results be **displayed to another user**? | **No, absent written consent** | (c) prohibits transfer *"to any third party"*; the reproduction clause requires *"Massive's express prior written consent"* |
| 7 | May the API support an **automated personal application**? | **`WRITTEN PROVIDER CLARIFICATION REQUIRED`** | The Individuals ToS contemplates API use for personal purposes, and (d) prohibits *non-display use* — the industry term for exactly programmatic consumption without human display. The two are in tension and no clause resolves it |
| 8 | What agreement would **production** require? | **Massive for Businesses ToS** | *"If you are using the Services for business or commercial purposes, you may not use any of the Services labeled for individual or personal use. Please contact sales@massive.com."* Non-Professional status further requires the holder to use data *"solely for their own personal, non-business use"* |

**No legal conclusion is drawn where the documents are silent**, and no
sales or support contact was made.

## 4. The unresolved definitional question

"Market Data" is defined as

> *"financial market data and other information relating to securities …
> and other information concerning financial markets made available by
> industry sources, financial exchanges, securities information
> processors, and **other third-party suppliers**"*

Third-party news articles delivered through the news endpoint plausibly
fall inside *"other information concerning financial markets made
available by … third-party suppliers"*, but the documents never say so,
and the news endpoint is never named in either terms document.

This matters more than it looks. **If news is Market Data**, clause (d)
prohibits the entire Radar on this tier. **If news is not Market Data**,
then no document in the chain states any use restriction on it at all —
which is not the same as permission. Either reading needs the provider
to say which, in writing.

`WRITTEN PROVIDER CLARIFICATION REQUIRED`.

## 5. Why Massive rather than Marketaux, briefly

Recorded as the reasoning behind the owner's selection, from public
documentation only, and **not remeasured**:

| | Massive | Marketaux |
|---|---|---|
| dated ticker-reference endpoint | documented — `/v3/reference/tickers/{ticker}?date=` | not documented |
| CIK and FIGI on the reference record | documented — composite and share-class FIGI, CIK | not documented |
| news-to-ticker association | documented | documented |
| stable article identity | documented article `id` | documented `uuid` |
| direct article URL | documented `article_url` | documented `url` |

The discriminator was the **dated** ticker-reference endpoint together
with CIK and FIGI: it is the only documented surface among the five
providers #194 catalogued that could have answered the PARA temporal
test — *can the same symbol produce two dated identities without silent
substitution* — which is the blocker #194 named. **Whether it actually
does so is unmeasured.**

## 6. What remains unmeasured

Every technical question the brief posed is open, and none of it was
approximated:

field completeness · the ticker → CIK/FIGI identity chain · point-in-time
resolution · the PARA temporal test · BA false-match controls (British
Airways, Omicron BA.\*) · articles associated with multiple tickers ·
canonical-URL directness and redirect behaviour · rehost publisher
preservation · `published_utc` bounds and window leakage · pagination
overlap and gaps · repeated-request stability · publisher-time versus
ingestion-time · Adobe acceptance A and B · Barclays ADR-versus-issuer
coverage.

**None of it was inferred from documentation and presented as a
result.** The field-completeness table this deliverable asks for cannot
honestly be produced without the probe, and an invented one would be
worse than its absence.

## 7. Conclusion

# B — LICENSING BLOCKED

Selected on the licensing half, which is decisive and independently
sufficient. **The technical half is unmeasured rather than confirmed**,
and this report does not claim it is ready.

### The exact blocker

**The free Individuals tier prohibits the use this platform intends.**
Market Data ToS (d) forbids *non-display use* and the creation of
*derivative works* absent a licence, and a development card derived from
retrieved reporting is a derivative work by the document's own
definition. Production therefore requires the **Massive for Businesses**
agreement — a commercial negotiation, not a technical step.

### What the owner would need before any probe becomes worthwhile

1. **A commercial decision.** If a Businesses agreement is not going to
   be sought, the probe measures the technical merits of a provider that
   cannot be used, and should not be run.
2. **Written clarification on two points** if it is: whether third-party
   news content is "Market Data" for the purposes of clause (d), and
   what retention of metadata and headlines is permitted. Both are
   silences, not refusals, and only the provider can close them.
3. **An account, created by the owner**, if and only if 1 and 2 point
   toward a licence worth having.

### And the standing alternative

#194's ruling is unaffected: the **authoritative lane is ready now**.
EDGAR carries no licensing restriction of this kind — filings are public
domain, the issuer's own releases arrive as attached exhibits, identity
is guarded by #192, and every item carries two regulator-stamped dates.
A Radar built there is narrower, and it is buildable today without any
commercial agreement at all.

## 8. Scope compliance

Research only · no production integration · no provider abstraction · no
cache or evidence-store write · **no API response committed or retained
anywhere** · no full-text retrieval · **zero model calls** · no
clustering, factual decomposition, development card, thesis mechanism or
sentiment · no analyst, committee, CIO or decision change · no mutation
of production evidence (`git status --porcelain data/` empty) ·
Codex's unpublished `d203609` not read, reused or published · **no
account created, no payment made, no trial started, no terms accepted,
and no sales or support contact** · no API key exists, and none appears
in any transcript, fixture, report, URL or diff.
