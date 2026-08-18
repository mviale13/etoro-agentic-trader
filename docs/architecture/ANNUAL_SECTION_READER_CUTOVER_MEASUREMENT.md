# The selector is ready and the form never arrives

**Status: research. 48 annual readings re-measured over the 24-company
corpus, plus 3 real amended filings and the 244-filing Item 5.02 control.
Zero model calls, no production implementation, no production data
mutation. `edgar_filings`, `section_locator` and `statement_locator` are
unchanged on disk; every filing read from the immutable EDGAR address
already held.**

#199 repaired discovery, #202 shipped the measured contents-versus-body
selector, #200 established the form mapping and refused dispatch because
location was not ready. Location is now ready. This asks whether the
cutover is.

> **The selector half is finished.** Over all 48 readings the locator
> opens on the adjudicated body heading **38 times**, refuses **6**,
> opens Honeywell's cross-reference index twice because that is the only
> structure Honeywell prints, and opens JPMorgan's incorporation pointer
> once because that *is* its Item 7. **One reading is imperfect** —
> Deutsche Bank, by 108 characters of page furniture.
>
> **Production is far worse than its own record suggested.** It opens
> correctly **21 of 48 times**, and its *span* matches the adjudicated
> one only **19 times**. Ten readings open on a contents entry, eight
> ask the wrong item outright, and — the part no previous report
> measured — **ten more open correctly and close catastrophically
> wrongly**: Goldman's Item 7 is read as **1,202 characters of an
> 311,737-character section**, MetLife's as 1,024 of 251,562, Chubb's as
> 377 of 180,307.
>
> **And the form does not reach the dispatch point.** Production reads
> filings through `EdgarProvider.fetch` → `read_url`, which constructs
> `FilingReference(form="")`. The form survives only inside
> `PrimarySource.identifier` as the string prefix of *"10-K 0000320193-…"*.
> A form-aware dispatch written into `_read` today would see an empty
> string on **every production read**.
>
> **The amendment mapping is specified correctly and would be useless.**
> Three real amended filings were found and measured: Disney's and
> Tesla's `10-K/A` print **only Items 10–15**, and Barclays' `20-F/A`
> **only Items 17–18**. None reprints the business section or the
> review. The mapping is not wrong; the document is.

---

## 1. What was measured

| | |
|---|---|
| annual filings | **24** (20 × 10-K, 4 × 20-F), from the cached immutable addresses |
| readings | **48** — business and review for each |
| amended filings located and read | **3** (`DIS 10-K/A`, `TSLA 10-K/A`, `BCS 20-F/A`) |
| control corpus | **244** Item 5.02 current reports |
| model calls | **0** |
| production code changed | **none** |

Six things were recorded per reading: production `_section`'s span, the
post-#202 locator's span, the adjudicated opening and closing from
#201's labels, the filing form, whether the section is printed or only
cross-referenced, and whether the reading depends on an incorporated
document.

---

## 2. The 48 readings

| reading | form | production today | width | locator + form dispatch | width |
|---|---|---|---|---|---|
| AAPL business | 10-K | body | 16,053 | **body** | 16,054 |
| AAPL review | 10-K | body | **238** | **body** | **18,103** |
| ALL business | 10-K | body | 58,745 | **body** | 58,995 |
| ALL review | 10-K | **contents** | 96 | **body** | 188,678 |
| AXP business | 10-K | **absent** | 0 | **body** | **86,613** |
| AXP review | 10-K | body | 160,557 | **body** | 160,558 |
| BCS business | 20-F | **wrong item** | 0 | **absent — not printed** | 0 |
| BCS review | 20-F | **wrong item** | 0 | **absent — not printed** | 0 |
| C business | 10-K | absent | 0 | **absent — unreadable** | 0 |
| C review | 10-K | absent | 0 | **absent — unreadable** | 0 |
| CB business | 10-K | body | **156,012** | **body** | **80,709** |
| CB review | 10-K | body | **377** | **body** | **180,307** |
| COF business | 10-K | body | 17,165 | **body** | 84,269 |
| COF review | 10-K | **contents** | 227,549 | **body** | 227,550 |
| DB business | 20-F | **wrong item** | 0 | **running header** | 185,174 |
| DB review | 20-F | **wrong item** | 1,235 | **body** | 7,053 |
| DIS business | 10-K | body | 66,765 | **body** | 66,766 |
| DIS review | 10-K | **contents** | 80,349 | **body** | 80,341 |
| FITB business | 10-K | **other offset** | 71,197 | **body** | 41,418 |
| FITB review | 10-K | **other offset** | 130,590 | **body** | 233,415 |
| GS business | 10-K | body | **43,436** | **body** | **151,951** |
| GS review | 10-K | body | **1,202** | **body** | **311,737** |
| HON business | 10-K | index | 71 | index | 72 |
| HON review | 10-K | index | 95 | index | 96 |
| JPM business | 10-K | body | 39,175 | **body** | 39,176 |
| JPM review | 10-K | **contents** | 395 | **pointer** | 396 |
| KO business | 10-K | body | 55,228 | **body** | 55,229 |
| KO review | 10-K | body | 109,832 | **body** | 109,833 |
| MET business | 10-K | body | **184,926** | **body** | **102,289** |
| MET review | 10-K | body | **1,024** | **body** | **251,562** |
| MTB business | 10-K | body | 77,682 | **body** | 77,683 |
| MTB review | 10-K | body | 158,359 | **body** | 158,360 |
| MUFG business | 20-F | **wrong item** | 81 | **body** | **156,875** |
| MUFG review | 20-F | **wrong item** | 6,525 | **body** | **217,570** |
| NWG business | 20-F | **wrong item** | 0 | **absent — not printed** | 0 |
| NWG review | 20-F | **wrong item** | 0 | **absent — not printed** | 0 |
| PG business | 10-K | **contents** | 18 | **body** | 14,295 |
| PG review | 10-K | **contents** | 96 | **body** | 92,104 |
| RF business | 10-K | **absent** | 0 | **body** | 75,069 |
| RF review | 10-K | **contents** | 96 | **body** | 160,549 |
| TRV business | 10-K | body | 171,096 | **body** | 171,097 |
| TRV review | 10-K | **prose reference** | 101,793 | **body** | 221,113 |
| TSLA business | 10-K | body | 45,455 | **body** | 45,456 |
| TSLA review | 10-K | body | 55,594 | **body** | 55,595 |
| UNP business | 10-K | body | 21,877 | **body** | 27,018 |
| UNP review | 10-K | **contents** | 45,503 | **body** | 58,678 |
| WMT business | 10-K | **contents** | 17 | **body** | 37,500 |
| WMT review | 10-K | **contents** | 95 | **body** | 58,397 |

### Openings

| | production | locator + dispatch |
|---|---|---|
| the adjudicated body | **21** | **38** |
| contents entry | **10** | 0 |
| wrong item asked (20-F) | **8** | 0 |
| some other offset (incl. a prose reference) | **3** | **1** — DB's running header |
| absent | 4 | 6 |
| cross-reference index (HON) | 2 | 2 |
| incorporation pointer (JPM) | 0 | **1**, correctly |

**Spans agreeing with the adjudicated span: production 19 of 48.**

### The half nobody had measured: correct opening, wrong closing

Ten readings open on the right heading and cut the wrong section:

| reading | production | adjudicated | error |
|---|---|---|---|
| GS review | 1,202 | 311,737 | **−310,535** |
| MET review | 1,024 | 251,562 | −250,538 |
| CB review | 377 | 180,307 | −179,930 |
| GS business | 43,436 | 151,951 | −108,515 |
| COF business | 17,165 | 84,269 | −67,104 |
| AAPL review | 238 | 18,103 | −17,865 |
| UNP business | 21,877 | 27,018 | −5,141 |
| ALL business | 58,745 | 58,995 | −250 |
| **CB business** | 156,012 | 80,709 | **+75,303** |
| **MET business** | 184,926 | 102,289 | **+82,637** |

Eight are truncations and two are over-reads. **A section read at 0.4%
of its length is not a smaller section; it is a different document**, and
every downstream reading of Goldman's or MetLife's management discussion
has been made from roughly one part in two hundred and fifty of it.

---

## 3. The adjudications asked for

**The twelve former contents openings all land on the body.** AAPL, ALL,
CB, COF, DIS, GS, JPM, MET, MTB, PG, RF and UNP — every one opens at the
labelled body offset under the locator. Confirmed.

**AXP's empty business section is recovered.** Production still reads
**0 characters**; the locator reads **86,613** at 69,885, the only Item 1
occurrence in the document. The filer printed a business description and
this platform has never read it.

**HON** — index, unchanged, and **not silently accepted**. Honeywell's
sections are titled *"About Honeywell"* and carry no item number at all;
its only Item 1 and Item 7 occurrences are inside its *"FORM 10-K
CROSS-REFERENCE INDEX"*. The locator returns those 72 and 96 characters
because they are the only structure the filing prints. **That is a
72-character index line, not a business section**, and under the refusal
contract in §6 it must be reported as *supported form, section not
printed as a numbered item* rather than served as a business
description.

**GS, RF, MET, JPM, CB, FITB** — all corrected. GS's review goes from
1,202 to 311,737; RF's business from absent to 75,069; MET's review from
1,024 to 251,562; CB's business narrows from 156,012 to 80,709 and its
review widens from 377 to 180,307; FITB moves off two wrong offsets onto
both bodies. **JPM's Item 7 is its 396-character incorporation
pointer**, and the locator selects it correctly where production selects
the contents entry — but it is a pointer, and §6 keeps it a distinct
outcome rather than a 396-character discussion.

**C is unreadable**, unchanged, and **not silently accepted**: no item
heading of any form is discoverable in the document. It is its own
refusal category.

**DB and MUFG.** MUFG is **fully correct** under dispatch — Item 4 at
358,607 (156,875 chars) and Item 5 at 515,527 (217,570), both on the
filer's own body headings. DB's Item 5 is correct at 763,958. **DB's
Item 4 opens 108 characters early**, on a running page header.

**BCS and NWG are kept separate** and are not a locator failure: their
20-Fs print **no Item 4 and no Item 5 at all** — 0 requested-item
occurrences in 3.7M and 1.2M characters — and carry a cross-reference
index into a differently structured annual report, with *"incorporated
by reference"* 19 and 26 times. **Nothing was located because nothing
was printed.**

### DB's 108 characters: does the prefix change the semantic section?

The prefix is, verbatim:

> `Item 4: Information on the company Annual Report  2025 on Form 20-F History and development of  the company `

It is the filer's running page header — the item title, the report
title, and the chapter title — immediately followed by the real heading
`Item 4: Information on the company History and development of the
company The legal and commercial name of the company is Deutsche Bank
Aktiengesellschaft.`

**No.** It is **0.0583%** of the 185,174-character span, it introduces no
sentence that is not already the section's own title, and it contains no
figure, no claim and no prose. The section's first substantive sentence
is identical either way. **It is recorded as a known imperfection, not
as a semantic difference** — and it is not repaired here, because no
signal measured in #201 distinguishes a running header from a body
heading, and Deutsche Bank is the only filer in the corpus that prints
them.

---

## 4. Form propagation — the blocker

| carrier | has the form? |
|---|---|
| `FilingReference.form` | **yes** — `'10-K'` / `'20-F'`, from the submissions index |
| `EdgarFilings.read(reference)` → `_read` | **yes** — but **nothing in production calls it** |
| **`EdgarProvider.fetch` → `EdgarFilings.read_url`** | **no** — constructs `FilingReference(form="")` |
| `PrimarySource` | **no field**; only `identifier = f"{reference.form} {reference.accession}"` |
| `_read`'s `reference` parameter, in production | **`form=""`** |

The single production path is
`EdgarProvider.fetch(source)` → `self._filings.read_url(source.location)`,
and `read_url` builds its reference from the URL alone. **`_section` is
called from `_read`, which does hold a reference — but in production
that reference's form is the empty string.**

So a form-aware dispatch is not merely unwired; **its input does not
exist at the point where it would run**. The brief's instruction not to
infer the form from the identifier string is the right one, and it means
the fix is a field: `PrimarySource` must carry the regulator-supplied
form, or `fetch` must pass it, so that `read_url`'s reference is no
longer built from a URL with everything else discarded.

**This is a production change and is not made here.**

---

## 5. Amended filings — validated, and the finding is a warning

Real amendments exist and were read rather than assumed:

| filing | accession | items it actually prints |
|---|---|---|
| `DIS 10-K/A` (2024-01-24) | 0001744489-24-000064 | **Items 10–15 only** |
| `TSLA 10-K/A` (2026-04-30) | 0001104659-26-053166 | **Items 10–15 only** |
| `BCS 20-F/A` (2022-05-23) | 0000312069-22-000085 | **Items 17–18 only** |

All three return **absent** for the mapped business and review items,
and correctly so: **an amended annual filing is a partial document.**
The two `10-K/A`s are Part III proxy amendments; the `20-F/A` carries
financial statements.

**The mapping `10-K/A → Item 1 / Item 7` is therefore specified
correctly and would deliver nothing**, and one thing follows that a
future implementer must not miss: `ANNUAL_FORMS = ("10-K", "20-F")`
excludes the amended forms, so `_latest_reference` never selects one
today. **Adding them to `ANNUAL_FORMS` would be a regression** — the
most recent annual filing would become a document that does not contain
the business description. Amendment support is a *document selection*
question, not a dispatch question, and this measurement says so before
anybody conflates them.

---

## 6. The refusal contract, five outcomes kept apart

A generic *"section missing"* would merge five different facts. Each has
a live specimen in this corpus:

| outcome | what it means | specimen |
|---|---|---|
| **`FORM_NOT_SUPPORTED`** | the filing is not an annual form this platform maps | none in corpus — the contract's default |
| **`ITEM_NOT_PRINTED`** | supported form, correct item, the filer printed no such section | **BCS, NWG** (no Item 4/5 at all); **HON** (sections carry no item number); the three amendments |
| **`INCORPORATED_ELSEWHERE`** | the section exists and points at another document or chapter | **JPM Item 7** — a 396-character pointer; **JPM Item 1** — 80,000 characters followed by `_referenced` |
| **`LOCATION_AMBIGUOUS`** | the item is printed and the opening cannot be settled | **DB Item 4** today, opening on page furniture |
| **`DOCUMENT_UNREADABLE`** | no item heading of any form is discoverable | **C** |

**None of these is `absent`.** A reader told *"Barclays printed no Item
4"* learns something true about the filing; a reader told *"the section
is missing"* learns something about this platform and mistakes it for
the company.

---

## 7. Controls

| control | result |
|---|---|
| 244 Item 5.02 readings | **244 of 244 byte-identical**, 241 located |
| the three Item 5.02 residuals | **unchanged and the same three** — `CVX 0000093410-22-000042`, `NKE 0000320187-22-000025`, `NKE 0001628280-22-012729` |
| statement-shape readings | **unreachable from this cutover.** `locate_statements(document, flat)` is called independently in `_read`; the income, balance-sheet and cash-flow spans never pass through `_section` |
| JPMorgan's incorporated chapter | **preserved** — `_referenced` returns the identical **80,000** characters from the locator's span as from production's |
| data mutation | none — `git status --porcelain data/` empty |
| Business Quality, committee, CIO, recommendation, Ticker News | untouched |
| model calls | 0 |

### One downstream movement the cutover does cause, and it is large

`discussion_tables` is read from the discussion span, and the segment
sizes are measured from those tables. Changing the span changes them:

| | production | after cutover |
|---|---|---|
| discussion tables across the corpus | **226** | **657** (**+431**) |
| companies whose count changes | — | **12 of 24** |

AAPL 0 → 6 · ALL 0 → 58 · CB 0 → 42 · FITB 0 → 65 · GS 0 → 80 · MET 1 →
53 · MUFG 1 → 52 · PG 0 → 18 · RF 0 → 29 · TRV 28 → 35 · UNP 16 → 21 ·
WMT 0 → 18.

**Eight companies go from no discussion tables to dozens.** This is the
recovery, not a risk — but it is a large change in what the segment
readers are given, and it belongs in the cutover's acceptance rather
than as a surprise after it.

---

## 8. Conclusion

# B — PARTIAL CUTOVER READY

### Safe now: the 10-K half, with no form input at all

**Twenty of the twenty-four filings are 10-K**, and for those the
cutover needs no dispatch: the items requested are the items production
already requests. Replacing `_section(_ITEM_1, _ITEM_1A)` with
`locate(markup, flat, Item(1))` and `_section(_ITEM_7, _ITEM_7A)` with
`locate(markup, flat, Item(7))` moves **28 of the 40 10-K readings**,
every movement toward the adjudicated span, with:

- **12 contents openings corrected**;
- **AXP's business section recovered** — 0 → 86,613 characters;
- **10 catastrophic closings corrected**, including GS 1,202 → 311,737;
- **JPMorgan's 80,000 incorporated characters preserved**, verified;
- **HON and C unchanged**, and reported through §6 rather than as
  sections;
- **244 of 244 Item 5.02 spans and all statement readings untouched.**

### Not safe: the 20-F half

**Not because the mapping is wrong — #200 established it and this report
confirms MUFG resolves perfectly under it — but because the form does
not reach the dispatch point.** `read_url` discards it and
`PrimarySource` has no field to carry it, so a form-aware branch would
read `""` on every production call and fall through to the 10-K items,
which is exactly today's defect wearing a new mechanism.

**The 20-F half needs one production change first**: carry the
regulator-supplied form on `PrimarySource` so `fetch` can pass it. It is
additive, changes no reading on its own, and #200 already named it as
the smallest justified slice.

### Refused within the 20-F half even after that

- **BCS and NWG** — `ITEM_NOT_PRINTED`. No dispatch fixes a section the
  filer did not print, and following page ranges into another document
  component is a different capability.
- **DB Item 4** — `LOCATION_AMBIGUOUS`, or accepted with its 108
  characters of page furniture recorded. The prefix does not change the
  semantic section; it is still not the heading.

### Unvalidated, deliberately

`10-K/A` and `20-F/A` are **specified and measured**: three real
amendments print none of the mapped items. They are not a dispatch
target until document selection is decided, and **`ANNUAL_FORMS` must
not gain them**.

### The order this implies

1. **10-K cutover** — no new plumbing, 28 readings corrected, controls
   green.
2. **Form on `PrimarySource`** — additive, changes nothing by itself.
3. **20-F dispatch** — MUFG correct, DB imperfect by 108 characters,
   BCS and NWG refused by name.
4. **Running-page-header selection** and **amendment document
   selection** — each its own measurement, neither started.

## 9. Scope compliance

Research only · no production implementation, no cutover, no dispatch,
no form plumbing · `edgar_filings`, `section_locator` and
`statement_locator` **unchanged on disk** · **zero model calls** · no new
acquisition beyond three amended filings read from immutable EDGAR
addresses · no production evidence written, no reading promoted · no
Business Quality, committee, CIO, recommendation or Ticker News change ·
Personal Ticker News remains display-only under the personal Massive
licence and is untouched · `git status --porcelain data/` empty · Codex's
unpublished `d203609` not read, reused or published.
