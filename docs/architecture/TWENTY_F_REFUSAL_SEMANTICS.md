# The mapping is ready and the platform has no way to say why it refused

**Status: research. Eight 20-F readings simulated in memory, plus the
20-company 10-K cohort as controls. Zero model calls, no production
change, no dispatch implemented, no data mutation. `edgar_filings`,
`section_locator` and `edgar_provider` are unchanged on disk.**

#208 wired the locator for exactly `10-K`. This asks whether `20-F` can
follow.

> **The location half is finished.** Simulating the exact-`20-F`
> dispatch: **MUFG's Item 4 and Item 5 are both exact bodies** (156,875
> and 217,570 characters), **DB's Item 5 is an exact body** (7,053), and
> **DB's Item 4 opens 108 characters early** on the running page header
> the owner has ruled harmless. Four of four printed sections located.
>
> **The refusal half is not, and it is not close.** Barclays and NatWest
> would hand downstream **an empty string and nothing else**.
> `EdgarProvider` does not check for an empty business description at
> all — ESEF and Investor Relations both raise a worded
> `PrimarySourceUnavailable` for exactly that emptiness, and the SEC
> provider passes it through silently. **Nothing in `KnowledgeState`
> names a document shape**, and `absent_because` — the one carrier that
> could word it — is populated only when something raises.
>
> **So the four cases the ruling asks to be kept apart are today one
> case: empty.** A section printed but not located, a section
> cross-referenced elsewhere, a section genuinely not printed, and an
> unsupported form are indistinguishable downstream.
>
> **A generic structural detector does exist, and it found a fourth
> filing nobody was looking for.** *"cross-reference guide / index /
> information"* **and** a resolved item run containing neither requested
> item identifies **Barclays, NatWest — and Citigroup**. Neither half
> works alone. **Citigroup is not an unreadable document**, which is
> what #198 called it: it prints `FORM 10-K CROSS-REFERENCE INDEX — Item
> Number | Page` with rows like *"1. Business 4–36, 121–127, 129,
> 160–164, 299–300"*. Same shape as Barclays and NatWest, on a 10-K.

---

## 1. Stage 1 — the simulated exact-20-F dispatch

Eight readings, in memory, comparing the production reader against
`section_locator` Item 4 / Item 5 against the labelled expectation.

| reading | production (Item 1/7) | located at | ends | width | text digest | tables | regions | verdict |
|---|---|---|---|---|---|---|---|---|
| **DB** business | 0 | **578,475** | 763,649 | **185,174** | `41e8ba511f4ab522` | 1 | 0 | **harmless prelude — 108 chars early** |
| **DB** review | 1,235 | **763,958** | 771,011 | **7,053** | `303a025e43de8172` | 0 | 0 | **exact body** |
| **MUFG** business | 81 | **358,607** | 515,482 | **156,875** | `b2fb647ce987ad32` | 2 | 44 | **exact body** |
| **MUFG** review | 6,525 | **515,527** | 733,097 | **217,570** | `7db7c0e8fcfd6b28` | 52 | 336 | **exact body** |
| **BCS** business | 0 | — | — | 0 | `e3b0c442…` (empty) | 0 | 0 | **refused** |
| **BCS** review | 0 | — | — | 0 | `e3b0c442…` (empty) | 0 | 0 | **refused** |
| **NWG** business | 0 | — | — | 0 | `e3b0c442…` (empty) | 0 | 0 | **refused** |
| **NWG** review | 0 | — | — | 0 | `e3b0c442…` (empty) | 0 | 0 | **refused** |

What each filing prints of the two requested items:

| | Item 4/5 occurrences in the whole document | resolved run contains both |
|---|---|---|
| DB | **51** | yes |
| MUFG | **35** | yes |
| BCS | **0** | no — run is `['Item 17', 'Item 18']` |
| NWG | **0** | no — run is empty |

**Deutsche Bank's 108 characters are recorded as an imperfect opening,
not an exact one**, per the ruling. They are the filer's running page
header — the item title, the report title and the chapter title — and
the body heading follows immediately. Not repaired, not hardcoded, and
`section_locator` untouched.

### The downstream wording an empty result produces today

**None.** That is the finding.

```text
EdgarProvider.fetch → SourceDocument(business_description="")
```

`EdgarProvider` has **no guard on an empty business description**. The
two other providers do, for the identical emptiness:

> *"…tags no description of the company's operations or its segments, so
> there was nothing in it to read. **The filing is real; what this
> platform reads is not in it.**"* — `EsefProvider`

The SEC path raises nothing, so `CompanyKnowledgeService` proceeds to
extraction with an empty section and `absent_because` is never set.

---

## 2. The refusal-semantics gate

The four cases the ruling requires be visibly distinct, against the
types that exist:

| case | specimen | what the platform can say today |
|---|---|---|
| 1 · supported form, section **printed**, locator refused | none live — C was thought to be this | empty string, no reason |
| 2 · supported form, content **cross-referenced elsewhere** | **BCS, NWG, C** | empty string, no reason |
| 3 · supported form, expected item **genuinely not printed** | none confirmed in this corpus | empty string, no reason |
| 4 · **unsupported or unclassified** form | any non-`10-K`/`20-F` | falls to the legacy reader — **no refusal at all** |

**All four collapse to one.** They are the same empty string on the same
successful fetch.

### What exists, and what is missing

| carrier | state |
|---|---|
| `KnowledgeOutcome.absent_because: str` | **exists** — free text, and the right shape for wording |
| `KnowledgeState` | **5 members, none of which names a document shape**: `AVAILABLE_CACHED`, `AVAILABLE_ACQUIRED`, `UNAVAILABLE`, `PROVIDER_ERROR`, `INVALID_EXTRACTION` |
| a producer on the SEC path | **missing** — `EdgarProvider` never raises for an empty section |

`UNAVAILABLE` is documented as *"no provider holds a source for this
security. **A gap in coverage**: try another provider, not the same one
again."* That is a different claim from *"this provider holds the
document, and the content is represented as page ranges into another
component"*. **Reusing it would make a fact about a document read as a
fact about coverage**, and a reader told to try another provider would
be told to do the one thing that cannot help.

### Why an empty string is not an acceptable answer

Barclays' 20-F is 3.7M characters of a real annual report. An empty
business description, rendered by a surface that expects prose, becomes
*"the company describes no business"* — a claim about **Barclays**,
produced by a limit of **this platform**. That is Invariant 1 inverted:
absent evidence reported as an established absence.

---

## 3. Candidate structural detection — measured, and it found a fourth filing

Four signals were measured over all 24 filings, not assumed.

| signal | discriminates? |
|---|---|
| the filer's own index heading (*"Form 20-F item number"*, *"cross-reference"*) | **no, alone** — FITB (2 hits) and HON (3) print one and their sections too |
| Item 4/4.B and Item 5 index rows | **no** — BCS and NWG print their index rows as **bare numbers** (*"4 Information on the Company"*), so `discover()` sees nothing |
| page / caption references | **BCS only** — NWG and C print page ranges without the phrase |
| absence of a coherent printed Item 4/5 body sequence | **no, alone** — an absence with no reason attached |
| **the conjunction of the first and the last** | **yes** |

### The rule that separates them

> A filing represents this content through a **cross-reference index**
> where it prints a cross-reference guide, index or information heading
> for its own form **and** the resolved item run contains neither
> requested item.

Over all 24 filings this identifies exactly three, with no false
positive:

| | guide phrase | run contains both requested items | verdict |
|---|---|---|---|
| **BCS** (20-F) | 1 | **no** | **cross-reference only** |
| **NWG** (20-F) | 2 | **no** | **cross-reference only** |
| **C** (10-K) | 1 | **no** | **cross-reference only** |
| FITB (10-K) | 2 | yes | printed |
| HON (10-K) | 3 | yes | printed |
| the other 19 | 0 | yes | printed |

**Neither half works alone**, which is what the ruling required: the
phrase alone admits FITB and HON, and the absence alone carries no
reason. No issuer allowlist, no `BCS`/`NWG`/`DB`/`MUFG` branch, and no
keyword-only decision.

### Citigroup is not an unreadable document

#198 recorded C as *"document unreadable — no item heading of any
form"*. It is nothing of the kind. It prints, verbatim:

> `FORM 10-K CROSS-REFERENCE INDEX  Item Number  Page  Part I  1.
> Business 4–36, 121–127, 129, 160–164, 299–300  1A. Risk Factors 49–62
> 1B. Unresolved Staff Comments Not Applicable …`

1.53M characters of a real annual report, **2 `Item N` occurrences in
all of it**, and its Item 1 addressed by page range. It is the same
document shape as Barclays and NatWest, on a domestic form. **The
platform has been reporting a document-shape refusal as an unreadable
filing for three reports**, and the correction belongs here rather than
in the 10-K cutover that inherited it.

**And it changes the exposure.** #208 shipped the 10-K cutover with C
classified as *"expected absence after a locator refusal"*. That
classification was right about the behaviour and wrong about the reason,
and the behaviour does not change: C still returns nothing. What changes
is what the platform may say about it.

---

## 4. Conclusion

# REFUSAL CARRIER REQUIRED

**The 20-F mapping is correct and the location works** — 4 of 4 printed
sections located, one with a 108-character prelude already ruled
harmless. **The dispatch is not implemented**, because shipping it would
convert two filings from *asking the wrong item and getting nothing* to
*asking the right item and getting nothing*, with no more ability to say
why than before — and would do it while the platform still calls the
third such filing unreadable.

### The smallest carrier

**One enumeration and one producer.** No new service, no new layer.

1. **A reason on the refusal.** `PrimarySourceUnavailable` gains a
   typed reason — the four cases of §2, as an enum beside the message
   it already carries. `absent_because` already propagates the wording;
   what is missing is a machine-readable *which*.

2. **A producer on the SEC path.** `EdgarProvider.fetch` gains the guard
   `EsefProvider` and `InvestorRelationsProvider` already have, raising
   with the reason rather than passing an empty string through. This is
   where the asymmetry is closed.

3. **The document-shape fact**, from §3's conjunction, computed where
   the sections are located and carried on the reason so the wording can
   be specific:

   > *"This filing represents Item 4 and Item 5 through a cross-reference
   > index rather than printing them as locatable sections in the
   > document component read. Following page ranges into another
   > component is not implemented."*

### Propagation path

```text
EdgarFilings._read      → the shape it observed while locating
EdgarProvider.fetch     → raises PrimarySourceUnavailable(reason=…)
CompanyKnowledgeService → absent_because (already carries the string)
KnowledgeState          → needs one member, or the reason rides on the outcome
surfaces                → print the reason rather than an empty section
```

**Whether `KnowledgeState` gains a member is the one open design
question**, and it is not settled here: `UNAVAILABLE` currently means a
coverage gap, and overloading it would make a fact about a document read
as a fact about coverage. Naming a sixth member is one answer; carrying
the reason beside the state is another. **That choice is the owner's.**

### What must not be built

No `BCS`/`NWG`/`DB`/`MUFG` branch · no issuer allowlist · no
keyword-only rule · no repair of Deutsche Bank's prelude · no change to
`section_locator` · no incorporated-document or page-range traversal,
which is a separate capability and is named as unimplemented rather than
attempted.

### Order

1. **the refusal carrier** — this report's subject, unbuilt;
2. **the Citigroup correction**, which the carrier makes expressible;
3. **the exact 20-F dispatch**, which is otherwise ready;
4. page-range traversal, unscoped.

## 5. Scope compliance

Research only · **no production change**, no dispatch implemented, no
`section_locator` change, no DB repair, no issuer branch · **zero model
calls** · no new acquisition — every filing read from the cache taken at
the immutable EDGAR address · no data mutation, `git status
--porcelain data/` empty · no Business Quality, committee, CIO,
recommendation or Ticker News change · Ticker News remains display-only
· Codex's unpublished `d203609` not read, reused or published.

---

## 6. Implementation status — 2026-08-18 · the refusal carrier

**Built.** The carrier only. **No 20-F dispatch**, and no page-range or
incorporated-document traversal.

### Two parts, because they answer different questions

| | |
|---|---|
| `KnowledgeState.DOCUMENT_REFUSED` | **what operational situation occurred** |
| `SectionRefusal` + `RefusedSection` | **why this document could not supply this section** |

The reason is **not** attached to `UNAVAILABLE`. That state means a gap
in coverage — *try another provider* — and a document that was retrieved
and parsed successfully is not one.

### The sixth state

`DOCUMENT_REFUSED`: `is_available` **false**, `may_succeed_later`
**false**, always carries `absent_because`, and retains older cached
knowledge exactly as the other current-document failures do. It is
deliberately not retryable — nothing failed and nothing is intermittent,
so the same request is refused for the same structural reason until a
*capability* changes. A test pins all six members' properties and that
the five existing ones did not move.

### The typed reason

| member | when |
|---|---|
| `CROSS_REFERENCE_INDEX` | the section is represented by an index into another component or page range |
| `EXPECTED_SECTION_NOT_PRINTED` | the mapped form prints no candidate, and no index explains it |
| `SECTION_LOCATION_REFUSED` | candidates exist and no coherent location survived |
| `UNSUPPORTED_FORM` | no section mapping exists for the regulator's form |

**A reason is established, never inferred from emptiness.** "The text
came back empty" is the symptom all four share and evidence for none, so
each branch names something observed in the document — *"The filing
prints no Item 1 heading and carries its own cross-reference index"*,
*"No Item 1 heading occurs anywhere in the 1,532,908 characters read"*,
*"9 occurrence(s) of Item 1 were discovered and none resolved into a
coherent section"*.

The reason owns its wording, and every member names the filing and its
form, what was expected, what was observed, what capability is missing,
and — as its closing sentence — **that no claim about the company
follows**. A test asserts none of the six forbidden phrasings appears in
any member.

### The carrier's location

`SourceDocument.business_refusal` and `SourceDocument.discussion_refusal`
— **two carriers, because a filing may print one section and not the
other**, and refusing both because one is missing would report this
reader's coupling as the filer's silence. Both default to `None`, and an
AST audit asserts every `SourceDocument` construction passes keywords.

**Nothing raises.** `EdgarProvider.fetch` does *not* raise for an empty
business description, and `PrimarySourceUnavailable` and
`PrimarySourceProviderError` keep their meanings exactly.

### Financial-statement neutrality — the load-bearing result

**Citigroup, measured:**

| | |
|---|---|
| business description | **refused**, `CROSS_REFERENCE_INDEX` |
| income statement | **4,725 characters** |
| balance sheet | **2,128 characters** |
| cash flow statement | **3,325 characters** |

An exception would have taken all three away to report the first. All 48
readings and every statement span across the 24 filings are
**byte-identical** to before this slice.

### The Citigroup correction

#198 recorded C as *"document unreadable — no item heading of any
form"*, and #206 and #208 inherited it. It is now
`DOCUMENT_REFUSED` with:

> *"The SEC 10-K filing (0000831001-26-000011) is available, but its
> business description is supplied through a cross-reference index
> pointing to content outside the document component this platform
> reads. The filing prints no Item 1 heading and carries its own
> cross-reference index. MOVRvest did not follow those page or component
> references, so no business description was established from this
> filing. Nothing follows from this about what the company does."*

The behaviour is unchanged — C still yields no business section. What
changed is that the platform can now say why, and that the reason is
about the document.

### The pinned cases

| | today | after 20-F dispatch |
|---|---|---|
| **C** | **`CROSS_REFERENCE_INDEX`** | unchanged |
| FITB · HON | **no refusal** — both readable | unchanged |
| DB · MUFG | no refusal — legacy path | no refusal, sections located |
| BCS · NWG | no refusal — legacy path | **`CROSS_REFERENCE_INDEX`** |

**No company-symbol branch.** The detector is the measured conjunction —
the expected section run is absent **and** the filer prints its own
cross-reference apparatus — and a test asserts the module *executes* no
string naming any of the six issuers, checked over the AST with
docstrings excluded, because the prose above the detector quotes their
wordings to say where it came from.

### The consumer

`CompanyKnowledgeService` refuses **before any extraction**, on both the
`knowledge` and the `observe` paths — the second matters more, because
`observe` spends to the quorum and would otherwise bill five model calls
for a document carrying no section to read. Zero extractor calls, zero
store writes, older cached knowledge retained, and **never**
`INVALID_EXTRACTION`: nothing was extracted and nothing failed grounding.

### Controls

Five existing states unchanged · **48 readings and every statement span
byte-identical** · exact 10-K spans from #208 unchanged · 244/244 Item
5.02 unchanged · Ticker News untouched · no data mutation · no model
calls in any test · all constructors keyword-safe by AST audit · stored
sources decode compatibly, because the carriers live on the *document*
and never on the stored identity.

### Scope compliance

Carrier only · **no 20-F dispatch**, no page-range or
incorporated-document traversal, no `section_locator` change, no DB
repair, no issuer branch · **zero model calls** · no data mutation ·
Codex's unpublished `d203609` not read, reused or published.

---

## 7. Implementation status — 2026-08-19 · the exact 20-F dispatch

**Step 3 of §4's order is built.** See
[`TWENTY_F_SECTION_DISPATCH.md`](TWENTY_F_SECTION_DISPATCH.md).

`ANNUAL_SECTION_ITEMS` maps exact normalised form to the pair of items
that form prints — `10-K` to Item 1 / Item 7, `20-F` to Item 4 / Item 5
— and `_read` dispatches on a lookup with no default and no prefix
match. Stage 1's simulated readings became production readings and the
four text digests are unchanged from this report's table.

| | this report predicted | production produces |
|---|---|---|
| **DB** business | `41e8ba511f4ab522`, 108 chars early | same digest, prelude accepted |
| **DB** review | `303a025e43de8172` | same digest |
| **MUFG** business | `b2fb647ce987ad32` | same digest |
| **MUFG** review | `7db7c0e8fcfd6b28` | same digest |
| **BCS**, **NWG** | refused, both sections | `CROSS_REFERENCE_INDEX` ×4 |

**All 40 10-K readings and all 72 statement spans are byte-identical**,
Citigroup's refusal included. Barclays and NatWest refuse both narrative
sections and still yield their income statement and balance sheet, which
is §6's carrier result demonstrated on the second form.

**Step 4 — page-range and incorporated-document traversal — remains
unscoped**, and remains what BCS, NWG and C are refused *for*.
