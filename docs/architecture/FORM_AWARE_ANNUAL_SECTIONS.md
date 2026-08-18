# The mapping is right and two of the four filings do not print it

**Status: research. Zero model calls, no acquisition, no production
implementation, no production data mutation. Every filing read from the
immutable address the resolver already holds.**

The reader asks every annual filing for Item 1 as business and Item 7 as
management discussion. #198 measured that this is wrong for the four
20-F filers in the held corpus. This asks what the right contract is,
and whether it can be dispatched.

> **Item 4 and Item 5 are the correct analogues, and Deutsche Bank and
> Mitsubishi UFJ both prove it in their own printed headings** — *Item
> 4: Information on the Company* (185,174 and 156,875 characters) and
> *Item 5: Operating and Financial Review and Prospects*. The items the
> reader asks for today print, in the filers' own words, **"Not required
> because this document is filed as an annual report"** and **"Not
> applicable."**
>
> **Barclays and NatWest print no Item 4 and no Item 5 at all.** Their
> 20-F is a **cross-reference index**: *"SEC Form 20-F Cross reference
> information — Form 20-F item number | Page and caption references in
> this document"*, where item 4.B "Business overview" resolves to
> *"ii (Market and other data), 14-24, 186-188, 300-313, 355-357 (Note
> 2)"*. There is no section to locate; there are page ranges into a
> differently-structured document, and *"incorporated by reference"*
> appears 19 and 26 times.
>
> **And the form is discarded before it could be used.** `PrimarySource`
> has **no `form` field** — the form survives only as a string prefix
> inside `identifier`, and `EdgarFilings.read_url` constructs a
> reference with `form=""`, dropping it entirely.

---

## 1. Form metadata flow

| carrier | form available? |
|---|---|
| `FilingReference.form` | **yes** — `'20-F'`, `'10-K'`, regulator-supplied from the submissions index |
| `EdgarFilings._read(reference, …)` | **yes** — `reference` is in scope where `_section` is called |
| `PrimarySource` | **no field.** Only `identifier = f"{form} {accession}"`, e.g. `'20-F 0000312069-26-000004'` |
| `PrimarySource.source_type` | `annual_report` for both forms — it does not distinguish them |
| `EdgarFilings.read_url(url)` | **dropped** — constructs `FilingReference(form="")` |
| `SourceDocument` | only via `source.identifier` string parsing |

**The dispatch point is fine and the persistence is not.** `_section` is
called from `_read`, which holds the reference, so a form-aware dispatch
needs no new plumbing *there*. But anything downstream that wants to
know which mapping produced a section would have to parse a string
prefix, and the `read_url` path — used by `PrimarySourceProvider.fetch`
— has no form at all.

Neither is inferred from ticker, domicile, exchange, filename, company
name or a heading, and no proposal here does so.

## 2. The semantic roles, defined before the items

**`BUSINESS_DESCRIPTION`** — what the company does: principal
operations, products and services, organisational or geographic
structure where it forms part of the business description.

**`OPERATING_FINANCIAL_REVIEW`** — management's review of results,
financial condition, drivers and outlook. Not shareholder identity, not
related-party ownership, not an arbitrary financial table.

## 3. The labelled matrix — eight primary rows

| symbol | form | role | item | printed heading | at | closes | width | occ. | ruling |
|---|---|---|---|---|---|---|---|---|---|
| **DB** | 20-F | BUSINESS | **Item 4** | *Item 4: Information on the company* | 412,046 (contents) / **580,329** (body) | Item 4A | 185,174 | 46 | **correct item**; span opens on the contents |
| **DB** | 20-F | REVIEW | **Item 5** | *Item 5: Operating and Financial Review and Prospects* | 792,821-ish | Item 6 | **7,053** | 5 | **correct item, cross-referenced body** |
| **MUFG** | 20-F | BUSINESS | **Item 4** | *Item 4. Information on the Company* | — | Item 4A | 156,875 | 21 | **correct item and substantive** |
| **MUFG** | 20-F | REVIEW | **Item 5** | *Item 5. Operating and Financial Review and Prospects* | — | Item 7 | **217,570** | 14 | **correct item and substantive** |
| **BCS** | 20-F | BUSINESS | **Item 4** | *(none printed)* | — | — | **0** | **0** | **not printed — cross-reference index** |
| **BCS** | 20-F | REVIEW | **Item 5** | *(none printed)* | — | — | **0** | **0** | **not printed — cross-reference index** |
| **NWG** | 20-F | BUSINESS | **Item 4** | *(none printed)* | — | — | **0** | **0** | **not printed — cross-reference index** |
| **NWG** | 20-F | REVIEW | **Item 5** | *(none printed)* | — | — | **0** | **0** | **not printed — cross-reference index** |

Current-reader rows, for contrast:

| symbol | item asked today | what it prints | width |
|---|---|---|---|
| DB | Item 1 | *"Identity of Directors, Senior Management and Advisers — **Not required because this document is filed as an annual report**"* | 13,425 |
| MUFG | Item 1 | *"Identity of Directors, Senior Management and Advisers. **Not applicable.**"* | 64 |
| DB | Item 7 | *"Major Shareholders and Related Party Transactions"* | 6,883 |
| MUFG | Item 7 | *"Major Shareholders and Related Party Transactions"* | 6,526 |

**Neither current item can satisfy either role for any of the four.**

## 4. The questions, answered

**1. Is Item 4 the correct analogue of a 10-K Item 1?** **Yes**, where the
filer prints it. DB and MUFG both title it *Information on the Company*
and both carry history, business overview, organisational structure and
property — the `BUSINESS_DESCRIPTION` role as defined above.

**2. Whole Item 4, or specifically 4.B "Business Overview"?** **Whole
Item 4**, on the evidence. MUFG prints *"Item 4.B. Information on the
Company—Business Overview"* 33 times, but almost all are
**cross-references from elsewhere in the document**, not a section
opening. DB prints *Business Overview* as a heading inside Item 4 twice,
one of which reads *"Business Overview — Deutsche Bank's organization —
Please see 'Combined Management Report: Operating…'"*. A 4.B-only span
would drop history, organisational structure and property, all of which
the role includes.

**3. Do 4.A, 4.C or 4.D carry information the business reader needs?**
**Yes** — 4.A history and development, 4.C organisational structure and
4.D property are each part of the business description under this
platform's own definition of the role. That is the second reason to take
whole Item 4.

**4. Is Item 5 the correct analogue of Item 7?** **Yes** — both filers
title it *Operating and Financial Review and Prospects*, and MUFG's is
217,570 characters of substantive review.

**5. Does Item 5 contain a coherent review, or cross-reference another
document?** **Both, depending on the filer.** MUFG's is substantive. **DB's
is 7,053 characters** and its body opens on *"Material accounting
policies and critical accounting estimates"* — the substance sits in
DB's *Combined Management Report*, which Item 4's own text points at.

**6. Are Item 4 and Item 5 located correctly?** By `section_locator`,
**for DB and MUFG, with the same contents-versus-body caveat #198
recorded** — DB's Item 4 span opens at 412,046, which is the contents
entry, while the body is at 580,329. Production's `_section` cannot
locate either item for any of the four, because it is hard-coded to
Item 1 and Item 7 literals. **For BCS and NWG, neither method can locate
anything, because there is nothing printed to locate.**

**7. Do contents entries, prose references or incorporation distort the
candidates?** **Yes, all three.** Contents entries (DB Item 4, MUFG Item
4 — the span opens on *"Item 4. Information on the Company 18 Item 4A.
Unresolved Staff Comments 50…"*), prose cross-references (MUFG's 33
mentions of 4.B), and incorporation (BCS 19, NWG 26 occurrences of
*"incorporated by reference"*).

**8. Does one mapping work across all four filers?** **The mapping does;
the location does not.** Item 4 / Item 5 is the right request for all
four. Two of the four do not print those items.

**9. Are amendments distinguishable?** **Yes in principle, untested in
fact** — the held corpus contains only `10-K` and `20-F`. **No `10-K/A`
or `20-F/A` is present**, so amendment handling can be specified but not
validated here.

**10. What should an unsupported form do?** Refuse by name. See §7.

## 5. Deutsche Bank acceptance

*Why the current reading cannot satisfy `BUSINESS_DESCRIPTION`*: the
located text is the filer's statement that the item **does not apply** —
*"Not required because this document is filed as an annual report."* It
describes no operations, products or structure. It is a true statement
about a regulatory item and contains no business description at all.

*Where the business description begins*: Item 4, *"Information on the
company"*, whose body is at offset **580,329** — the contents entry sits
at 412,046 and the locator currently opens there.

*Where it closes*: Item 4A, *Unresolved Staff Comments*.

*The operating review*: Item 5, *Operating and Financial Review and
Prospects*, **7,053 characters**, closing at Item 6.

*Directly printed or incorporated*: **partly incorporated.** DB's Item 4
Business Overview says *"Please see 'Combined Management Report:
Operating…'"*, so the substance of both roles sits in a component this
platform would have to follow — the same shape as JPMorgan's
incorporation that `_referenced`/`_joined` already handles for 10-K.

## 6. Barclays and NatWest acceptance

Both file a 20-F that is a **wrapper plus a cross-reference index**, not
a sectioned annual report.

**BCS** prints, once: *"SEC Form 20-F Cross reference information — Form
20-F item number | Page and caption references in this document — 1
Identity of Directors… Not applicable — … 4 Information on the Company
A. History and development of the company 14, 80-83, 315-336, 402-406
(Note 25), 441, 449 — B. Business overview ii (Market and other data),
14-24, 186-188, 300-313, 355-357 (Note 2)…"*

**NWG** prints, once: *"Exhibit 15.2: Annual Report and Form 20-F
Information — … 4 Information on the Company A. History and development
of the Company B. Business overview … 10-12, 175-180, 297-308 — 1-27,
179-180, 258-267, 290-296"*.

| | BCS | NWG |
|---|---|---|
| markup | 54,325,749 | 22,268,419 |
| flattened text | 3,688,245 | 1,232,879 |
| tolerant `Item N` occurrences in the whole document | **3** | **5** |
| resolved item sequence | `['Item 17', 'Item 18']` | `[]` |
| `"incorporated by reference"` | **19** | **26** |
| `"Information on the Company"` | 1 — in the index | 1 — in the index |

**This is not a locator failure and not a dispatch failure.** It is a
different document shape: the substantive business description exists,
in the issuer's own annual report, addressed by page range rather than
by item heading. Neither method can find a section that was never
printed as one, and **the SEC cover/item wrapper must not be mistaken
for the business section** — which is exactly what a naïve "read
whatever Item 4 returns" would do if the index line were located.

## 7. MUFG acceptance

English-language 20-F, substantive throughout, and the mapping holds:
Item 4 156,875 characters, Item 5 217,570. Two structural cautions the
filing forced:

- the located Item 4 span **opens on the contents entry**, exactly as
  RF and MET do in #198 — the same unresolved tie-break, arriving on a
  second form;
- *Item 4.B* appears 33 times and is almost always a **cross-reference
  from elsewhere**, so equivalence must not be inferred from the heading
  alone. The one occurrence that opens a body is inside Item 4, which is
  why the whole item is the right span.

## 8. 10-K neutrality

Over all 20 held 10-K filers, asking Item 1 and Item 7:

**19 of 20 resolve the correct printed headings** — *Item 1. Business*
and *Item 7. Management's Discussion and Analysis*, in every typographic
variant the corpus prints. The twentieth, **C**, resolves neither and is
the document #198 already recorded as unreadable — unchanged by
anything here.

**Expected decision-bearing changes from a future form dispatch:
zero.** A 10-K would continue to request Item 1 and Item 7, which is
what it requests today. **This task changed no code.**

## 9. Proposed refusal contract

| form | business | operating review |
|---|---|---|
| `10-K` | Item 1 | Item 7 |
| `10-K/A` | Item 1 | Item 7 — **specified, unvalidated**; none in the corpus |
| `20-F` | **Item 4** | **Item 5** |
| `20-F/A` | Item 4 | Item 5 — **specified, unvalidated** |
| anything else | **refuse** | **refuse** |

The refusal must be named and must state the form:

> `annual-section mapping is not established for FORM`

and must **never fall back to 10-K item numbers**, which is the current
behaviour and the defect this measurement exists to describe.

A second refusal is needed and is **not** the same one:

> `FORM prints no such item; the content is incorporated by reference`

for BCS and NWG — where the mapping is right, the dispatch is right,
and the filing does not print the section. Reporting that as *"the
mapping is not established"* would blame the contract for a document
shape.

## 10. The four questions kept apart

| | DB | MUFG | BCS | NWG |
|---|---|---|---|---|
| 1. which item the form requires | **answered** — 4 / 5 | **answered** | **answered** | **answered** |
| 2. was it structurally located | partly — contents-vs-body | partly — contents-vs-body | **no — not printed** | **no — not printed** |
| 3. does the text satisfy the role | **yes** | **yes** | n/a | n/a |
| 4. incorporated by reference | **yes, partly** | no | **yes, wholly** | **yes, wholly** |

A correct dispatch with a failed locator is still a locator failure; a
located wrong item is still a dispatch failure. Today **all four are
dispatch failures**, and after a dispatch fix **two become locator
failures and two become incorporation cases.**

## 11. Conclusion

# B — FORM MAPPING READY, LOCATION NOT READY

**The mapping is established.** `20-F` → **Item 4** for
`BUSINESS_DESCRIPTION` and **Item 5** for `OPERATING_FINANCIAL_REVIEW`,
confirmed by two filers' own printed headings and by the fact that the
items currently requested say *"Not required"* and *"Not applicable"* in
the filers' own words. Whole Item 4 rather than 4.B, because 4.A, 4.C
and 4.D are part of the role as this platform defines it and because
4.B is overwhelmingly a cross-reference target.

**Location is the blocker, in two distinct forms:**

1. **BCS and NWG print no Item 4 and no Item 5.** Their 20-F is a
   cross-reference index into a separately structured annual report —
   3 and 5 tolerant `Item N` occurrences in 3.7M and 1.2M characters,
   with *"incorporated by reference"* 19 and 26 times. **A dispatch fix
   changes nothing for these two**, and following page ranges into
   another document component is a different capability from section
   location.
2. **DB's and MUFG's Item 4 spans open on the contents entry**, which is
   the RF/MET tie-break #198 named and the owner has explicitly refused
   to change without its own measurement. The mapping would be right and
   the span would still be wrong.

### Smallest justified production slice

**Not the dispatch.** A dispatch shipped now would move DB and MUFG from
one wrong section to a differently wrong span, and would move BCS and
NWG not at all — while the two defects that actually decide correctness
are both already queued and both explicitly refused pending measurement.

The smallest justified slice is instead the one this measurement makes
newly concrete: **carry the regulator-supplied form on `PrimarySource`
so that any later dispatch, refusal or diagnosis can name it.** It is
additive, changes no reading, and removes the only place where the form
is genuinely lost — `read_url`. It is offered as an observation, not a
recommendation to build: the phase gate applies, and no investor-facing
decision improves until the location work behind it is done.

## 12. Scope compliance

Research only · no production code · no form-dispatch implementation ·
no `_section` rewire · no `section_locator` scoring change · no
contents/body repair · **no AXP repair** · no CB/FITB adjudication ·
**zero model calls** · no live acquisition — every filing read from the
immutable address already held · no production evidence mutation, no
statement promotion · no analyst, consensus, committee, CIO or decision
change · `git status --porcelain data/` empty · Codex's unpublished
`d203609` not read, reused or published.
