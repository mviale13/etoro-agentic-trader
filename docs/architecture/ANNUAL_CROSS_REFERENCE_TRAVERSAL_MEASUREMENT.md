# Can a cross-reference index be followed to the sections it points at?

**Status: research. 2026-08-19. No production change.** Step 4 of
[`TWENTY_F_REFUSAL_SEMANTICS.md`](TWENTY_F_REFUSAL_SEMANTICS.md) §4's
order, measured against the three filings #210/#211 refuse — C, BCS,
NWG — with FITB and HON as negative controls and DB and MUFG as
readable-20-F controls. Ten fetches from the regulator's archive
(~1.5MB total, every response 200, 0.12–0.24s); all section evidence
read from the same cached corpus bytes #211 measured; no model call
selected anything.

## Conclusion

# B. COMPONENT RESOLUTION READY, SECTION EXTRACTION NOT READY

**Component resolution is deterministic and regulator-stated for every
corpus member** — the accession's own filing index names each
component's regulator type (`20-F`, `EX-15.2`), so no filename is ever
parsed and no issuer is ever matched.

**Section extraction is not a contract yet, and the three filings fail
it for three different reasons.** Citigroup's extraction *works* — every
probed page address opens with the filer's own caption for what the
index claims lives there — but one working filer is not a contract:
BCS's printed pages **do not exist in any form in any component of its
accession**, so its extraction is permanently refusable rather than
buildable; NWG needs an index parse this platform has not built (the
guide is a two-column table whose flat text cannot say which component
owns a page list) and a semantics ruling on serving one column of two;
and the index-parse layer itself met three structurally different index
shapes in three filings, one containing the filer's own typography
errors. What blocks A is named precisely in §6.

---

## 1. What each filer's index actually is

Three shapes, none alike:

| | shape | addresses | complications |
|---|---|---|---|
| **C** (10-K) | flat rows, item → page list | one pagination, its own document | 5 disjoint ranges for Item 1; ranges of different items **overlap** |
| **BCS** (20-F) | lettered sub-items (4.A–4.D) → page lists | one pagination, its own document | roman page `ii`; caption qualifiers *"(Note 25)"*; the filer's own typos — `109-115. 441-443`, `75. 92-99` (periods where commas belong) |
| **NWG** (20-F) | **two-column table**: every caption carries two page lists | **two components** — the primary document and `EX-15.2` | rows also cite `Exhibit 8.1`, `Exhibits 12.1 and 12.2` inside page columns |

BCS's asterisk footnote, verbatim: *"Captions have been included only in
respect of pages with multiple sections on the same page…"* — the
captions disambiguate **within** a page and confirm the references are
to pages *of this document*.

## 2. Component resolution — deterministic, regulator-stated (measures 1–2)

`index.json` for all seven accessions names every component with its
size. For the mapping an index row needs — *"Exhibit 15.2"* → a file —
the accession's own filing index states it as data:

> `EXHIBIT 15.2 · nwg-20251231xex15d2.htm · EX-15.2 · 1186862`

alongside `FORM 20-F · nwg-20251231x20f.htm` and rows for `EX-8.1`,
`EX-12.1`. **No filename is parsed and no name is guessed**: the
regulator's type column is the resolution. C's and BCS's references say
*"in this document"* and resolve to the primary component trivially.
None of the three accessions contains any PDF component (measured: zero
`.pdf` entries in all three).

## 3. Page identity — where printed pages survive, and where they do not (measure 3)

The load-bearing structural fact. A **page marker** was defined as a
standalone integer element immediately preceding a page-break, and the
resulting chain validated for consecutiveness — never a greedy walk
through loose integers, which a 54MB financial document satisfies
spuriously (measured: BCS "reaches page 502" on a greedy walk while
containing no page structure at all — **width-as-truth's cousin, and
exactly the check the contract must forbid**).

| component | page-break markup | validated chain | verdict |
|---|---|---|---|
| **C** primary (iXBRL) | 317 `<hr page-break-after>` | **2→317, 316/317 numbered, 315 consecutive steps** | pages addressable |
| **NWG** primary (iXBRL) | 315 CSS breaks | **1→310, 310/310 mapped, no gaps** | pages addressable |
| **NWG** `EX-15.2` | 322 CSS breaks | **161 page-images** (`g001.jpg`…), hidden 1pt text layer, **1** standalone integer in the whole file | ordinals exist; **printed page numbers do not** |
| **BCS** primary (iXBRL) | **0** breaks, 0 `<hr>` | — | **no page identity in any form** |

BCS was exhausted, not sampled: no page-break CSS, no running
header/footer pattern (0 hits on four shapes), no page-like anchor among
39,361 `id`s (they are XBRL facts and contexts), no `title=` or `data-`
attributes anywhere, and no PDF sibling. **The pages its index cites
exist only in a print layout that never entered the accession.**

NWG's `EX-15.2` is the inverse trap: 161 pages exist as ordinals (one
JPEG per page, breaks between), but no printed number ties ordinal 12 to
*the guide's* "page 12" — the correspondence is an assumption with an
off-by-cover failure mode, and checking it would mean reading images,
which is not this platform's evidence. The hidden text layer (1.0M
chars) is the filer's own embedded text but carries no page addresses.

## 4. Extraction, measured where pages are addressable (measures 4–6)

**Every probed C address opens with the filer's own caption for the item
that cites it** — the structural check that replaces prose similarity:

| cited by | page | opens with (filer's caption) |
|---|---|---|
| Item 1 (4–36) | 4 | `OVERVIEW Citigroup's history dates back…` |
| Item 7 (8–36) | 8 | `MANAGEMENT'S DISCUSSION AND ANALYSIS…` |
| Item 1A (49–62) | 49 | `RISK FACTORS` |
| Items 7/7A (64–120) | 64 | `MANAGING GLOBAL RISK` |
| Item 1 (121–127) | 121 | `SIGNIFICANT ACCOUNTING POLICIES…` |
| Item 8 (134–298) | 134 | `CONSOLIDATED FINANCIAL STATEMENTS…` |
| Item 1 (299–300) | 299 | `SUPERVISION, REGULATION…` |

Joins are the norm, not the exception (measure 4): C's Item 1 is **five
disjoint ranges**; NWG's Item 4 (primary column) is **eleven**. The
unions:

| | pages | chars | shared with sibling item |
|---|---|---|---|
| C Item 1 | 48 | 166,352 | **29 pages (8–36)** |
| C Item 7 | 86 | 301,322 | 29 pages |
| NWG Item 4 (col 1) | 64 | 215,386 | **27 pages** |
| NWG Item 5 (col 1) | 87 | 276,534 | 27 pages |

**A page-cited section is a union that overlaps its sibling** (measure
5): Citigroup's own index places pages 8–36 in *both* Item 1 and Item 7,
and NWG's Item 4.A cites pages inside the Notes (page 175 opens *"Notes
to the consolidated financial statements continued — 3 Operating
expenses"*). The overlap is the filer's claim, not a parse error — a
business description served this way *contains* a large part of the
performance discussion, which the item-run reader never produces and
every downstream consumer currently assumes.

Business and discussion resolve **independently** (measure 6): separate
range sets, separately extractable, separately refusable — the #210
independence carries through unchanged.

## 5. Citation, refusal, statements, network (measures 7–10)

**7 — citation.** Every extracted span can carry the full address:
accession, component filename as the regulator's type table names it,
printed page number, and the byte span the page occupies in the
component (the page marker *is* a byte offset). For C page 4:
`0000831001-26-000011 · c-20251231.htm · page 4 · [html span]`. Nothing
about the citation needs invention.

**8 — refusal.** Structural and already observed in-corpus, never a
judgment call: refuse when the referenced component has **no validated
pagination chain** (BCS — the whole filing), when a cited page is
**outside the chain** (BCS's roman `ii`), when a **non-page token sits
in a page column** (NWG's `Exhibit 8.1` inside 4.C's list), and when
ordinals exist but printed numbers do not (NWG `EX-15.2`). Each names
what was observed, in #210's typed-reason shape.

**9 — statements.** Untouched by construction: traversal reads pages;
statement location resolves its own run in the primary (#211 measured
BCS and NWG refusing both narrative sections while serving income
statement and balance sheet — 1,811/2,660 and 2,480/1,850 chars). A
future traversal *adds* readings and can take nothing away.

**10 — network.** Ten fetches, all 200: seven `index.json` (21–49KB,
0.12–0.24s), one `EX-15.2` (1.19MB), one filing index page (71KB), one
repeatability refetch of C's `index.json` — **byte-identical** to the
first. All at immutable accession addresses with the platform's declared
user agent. Section evidence: zero new fetches — the same cached bytes
whose digests #211 pinned. Storage: session scratchpad only; `data/`
untouched.

## 6. What blocks A, named

1. **The index parse is not yet a deterministic contract.** Three
   filings produced three structurally different indexes. C's flat rows
   parse cleanly. BCS's rows carry the filer's own typography errors
   (`109-115. 441-443`) and a roman page — rules exist but must be
   *stated*, not improvised. NWG's guide is a **table** whose two page
   columns are owned by two components: flat text cannot assign a list
   to a component, so the parse must run on the tabular chain (the
   BQ28 machinery), which this slice did not build.
2. **BCS cannot be extracted, ever, from this accession** — its refusal
   is the contract's mandatory branch, not an edge case.
3. **NWG's whole-item semantics need a ruling**: the filer says Item 4
   is *both* columns; the primary column alone is extractable and the
   exhibit column is not. Serving one column is a partial reading and
   must be declared as one — whether that partial reading is acceptable
   is the owner's call, not a parser default.
4. **The shared-page semantics need a ruling**: C's business description
   built this way contains 29 pages of its own MD&A, by the filer's own
   assignment. Whether a section that overlaps its sibling may enter the
   knowledge stream unmarked is a question about evidence, not parsing.

## 7. Controls

**FITB and HON print real item→page indexes too** — not merely the
phrase (*"ITEM 1 About Honeywell 49…"*; *"Item 1. Business 20,
Employees 20, 62…"*). So an index's presence can never be the entry
condition: the gate stays #210's measured conjunction — apparatus
**and** absent section run — and traversal is only ever *entered* on a
filing already refused. FITB and HON keep their located sections and are
never traversed. DB and MUFG print no item→page index (#209: zero guide
phrases) and are read by the #211 dispatch; traversal has nothing to
parse there and never runs.

## 8. Boundaries held

No issuer-symbol matching (component identity from the regulator's type
table; page identity from validated chains) · no prose similarity · no
width-as-truth (the greedy-walk trap is measured and named as forbidden)
· no model selected any component or range · `DOCUMENT_REFUSED`
untouched — nothing here removes a refusal until a traversal positively
establishes a section, which none does yet · `section_locator`,
statements, Business Quality, committees, CIO and Ticker News untouched
· nothing persisted to production data.
