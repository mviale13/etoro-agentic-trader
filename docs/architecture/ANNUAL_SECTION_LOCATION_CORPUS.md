# Item 1 Business is discovered as Item 1B

**Status: research. 48 section readings over the 24 held annual reports.
Zero model calls, no production mutation, no implementation.
`_section`, `section_locator` and `statement_locator` are untouched on
disk.**

PR #191 refused to rewire annual-report section reading because the
change moved 26 of 48 readings and lost Honeywell's business section.
This is the labelled corpus it said was needed. It found the cause of
that loss, and it found that the largest part of the blast radius was
never real.

> **`Item 1 Business` is discovered as `Item 1B`.** The candidate
> pattern ends `\s*([a-c])?` under `(?i)`, so the optional suffix group
> eats the first letter of the following word — and *Business* is the
> commonest word to follow *Item 1* in a 10-K. Honeywell prints
> `ITEM 1 About Honeywell`, read as **Item 1A**, so Item 1 is never a
> candidate and the locator returns nothing. **That is the loss #191
> refused the rewire over, and it is a pre-existing defect rather than
> anything #191 introduced.**
>
> **A one-token guard fixes it and moves almost nothing.** Adding
> `(?![A-Za-z])` after the suffix group changes the reading for **2 of
> 24 companies** — Honeywell, recovering what was lost, and Goldman
> Sachs — and breaks no legitimate suffix.
>
> **#191's largest reported regression does not exist.** JPMorgan's
> "−66%" compared `business_text`, which is `_joined(business,
> referenced)` and carries **80,001 characters incorporated by
> reference**, against the locator's raw span. Like for like it is
> **39,176 → 40,653, +4%**. JPM is the only company where joined and raw
> differ at all.
>
> **The rewire is still unsafe, for a reason #191 did not find.** The
> locator opens Regions Financial's and MetLife's business sections on
> the **table-of-contents entry** rather than the body, because
> `_width_score` rewards width and the contents entry's step to the
> body's peer is the wider one.

---

## 1. Method

Three readings of every section over the same canonical flattened text
(`flatten(markup).text`), so every offset is comparable:

- **A** — production's `_section` rule, reproduced so its offsets could
  be recorded.
- **B** — `section_locator.locate()`.
- **C** — the label, adjudicated from structural evidence dumped for
  every occurrence of the opening item and its closing peer:
  `begins_a_block`, the 120 characters before the occurrence, the
  heading text, the resolved item sequence, and
  incorporation-by-reference language.

**No label was assigned from width alone**, and neither implementation
was treated as the expected answer.

## 2. The 48-row matrix

| symbol | form | section | A width | B width | A reads | B reads | label C |
|---|---|---|---|---|---|---|---|
| AAPL | 10-K | business | 16,054 | 19,333 | full section | full section | B (wider, peer-closed) |
| AAPL | 10-K | discussion | 239 | 18,103 | **contents entry** | full section | **B** |
| ALL | 10-K | business | 58,745 | 60,650 | full section | full section | B (wider, peer-closed) |
| ALL | 10-K | discussion | 97 | 188,678 | **contents entry** | full section | **B** |
| AXP | 10-K | business | 0 | 86,613 | absent | full section | **B** |
| AXP | 10-K | discussion | 160,558 | 160,558 | full section | full section | both agree |
| BCS | 20-F | business | 0 | 0 | absent | absent | **wrong item for 20-F** |
| BCS | 20-F | discussion | 0 | 0 | absent | absent | **wrong item for 20-F** |
| C | 10-K | business | 0 | 0 | absent | absent | document unreadable |
| C | 10-K | discussion | 0 | 0 | absent | absent | document unreadable |
| CB | 10-K | business | 156,013 | 82,121 | full section | full section | B (wider, peer-closed) |
| CB | 10-K | discussion | 378 | 180,307 | **contents entry** | full section | **B** |
| COF | 10-K | business | 17,165 | 89,282 | full section | full section | B (wider, peer-closed) |
| COF | 10-K | discussion | 227,550 | 227,550 | full section | full section | both agree |
| DB | 20-F | business | 0 | 13,425 | absent | contents→body (over-wide) | **wrong item for 20-F** |
| DB | 20-F | discussion | 1,236 | 6,883 | full section | contents→body (over-wide) | **wrong item for 20-F** |
| DIS | 10-K | business | 66,766 | 73,195 | full section | full section | B (wider, peer-closed) |
| DIS | 10-K | discussion | 80,350 | 80,341 | full section | full section | B (wider, peer-closed) |
| FITB | 10-K | business | 71,198 | 41,418 | full section | full section | B (wider, peer-closed) |
| FITB | 10-K | discussion | 130,591 | 233,415 | full section | full section | B (wider, peer-closed) |
| GS | 10-K | business | 43,437 | 151,951 | full section | full section | B (wider, peer-closed) |
| GS | 10-K | discussion | 1,203 | 311,737 | full section | full section | B (wider, peer-closed) |
| HON | 10-K | business | 72 | 0 | **contents entry** | absent | **A** (B misses) |
| HON | 10-K | discussion | 96 | 96 | **contents entry** | **contents entry** | both agree |
| JPM | 10-K | business | 39,176 | 40,653 | full section | full section | B (wider, peer-closed) |
| JPM | 10-K | discussion | 396 | 396 | **contents entry** | **contents entry** | both agree |
| KO | 10-K | business | 55,229 | 55,229 | full section | full section | both agree |
| KO | 10-K | discussion | 109,833 | 109,833 | full section | full section | both agree |
| MET | 10-K | business | 184,927 | 109,704 | full section | contents→body (over-wide) | neither — body start at a later offset |
| MET | 10-K | discussion | 1,024 | 251,562 | full section | contents→body (over-wide) | neither — body start at a later offset |
| MTB | 10-K | business | 77,683 | 85,896 | full section | full section | B (wider, peer-closed) |
| MTB | 10-K | discussion | 158,360 | 158,360 | full section | full section | both agree |
| MUFG | 20-F | business | 82 | 64 | **contents entry** | **contents entry** | **wrong item for 20-F** |
| MUFG | 20-F | discussion | 6,526 | 6,526 | full section | full section | **wrong item for 20-F** |
| NWG | 20-F | business | 0 | 0 | absent | absent | **wrong item for 20-F** |
| NWG | 20-F | discussion | 0 | 0 | absent | absent | **wrong item for 20-F** |
| PG | 10-K | business | 19 | 16,623 | **contents entry** | full section | **B** |
| PG | 10-K | discussion | 97 | 92,104 | **contents entry** | full section | **B** |
| RF | 10-K | business | 0 | 91,902 | absent | contents→body (over-wide) | neither — body start at a later offset |
| RF | 10-K | discussion | 97 | 160,549 | **contents entry** | full section | **B** |
| TRV | 10-K | business | 171,097 | 171,097 | full section | full section | both agree |
| TRV | 10-K | discussion | 101,793 | 221,113 | full section | full section | B (wider, peer-closed) |
| TSLA | 10-K | business | 45,456 | 45,456 | full section | full section | both agree |
| TSLA | 10-K | discussion | 55,595 | 55,595 | full section | full section | both agree |
| UNP | 10-K | business | 21,878 | 35,680 | full section | full section | B (wider, peer-closed) |
| UNP | 10-K | discussion | 45,504 | 58,678 | full section | full section | B (wider, peer-closed) |
| WMT | 10-K | business | 18 | 37,500 | **contents entry** | full section | **B** |
| WMT | 10-K | discussion | 96 | 58,397 | **contents entry** | full section | **B** |

## 3. Confusion tables

### Current reader (A)

| outcome | n |
|---|---|
| full section | 26 |
| **contents entry mistaken for body** | **12** |
| absent — heading never matched literally | 8 |
| document unreadable | 2 |

A's failure has one mechanism: it matches `item 1.` and `item 7.`
literally, so a filer typesetting `ITEM\xa01.` (AXP, MET, RF) is invisible
to it — and where the literal does match, it often matches the contents
entry and finds a closing peer a few characters later.

### `section_locator` (B)

| outcome | n |
|---|---|
| full section | 31 |
| **contents entry opened, body's peer closed — over-wide** | **3** |
| absent — suffix defect swallowed the item | 1 |
| absent — genuinely, or the wrong item for the form | 11 |
| document unreadable | 2 |

## 4. Movements by category

| category | n |
|---|---|
| **B recovers a section A could not see** | **10** |
| **B loses a section A reads** | **1** — HON, caused by the suffix defect |
| A and B agree exactly | 9 |
| B wider, closed at the resolved peer | 12 |
| B narrower, unadjudicated | 2 — CB, FITB |
| both empty | 6 |
| wrong item for the form | 8 |

## 5. Priority specimens

### AXP — the clearest case in the corpus. **C = B.**

A finds **zero** occurrences of its literal openings: American Express
typesets `ITEM\xa01.`. B opens at 69,885 — the **only** Item 1 occurrence
in the document — `begins_a_block` true, two supporting observations,
**zero rejected candidates**, closing at `ITEM\xa01A.\xa0\xa0\xa0\xa0RISK FACTORS`. The
resolved sequence runs Item 1 → 1A → 1B → 1C → 2 → 3 → 4 → 5 → 6 → 7 →
7A → 8 → 9 → 9A without a gap, and the span opens *"ITEM 1. BUSINESS
Overview American Express is a global payments and premium lifestyle
brand powered by technology."*

**AXP's business description is empty today and the filer printed 86,613
characters of one.**

### HON — the loss, and its cause. **C = contents entry; no body located.**

`discover()` returns **no Item 1 candidate at all** and the resolved
sequence begins at Item 1A, because `ITEM 1 About Honeywell` is read as
Item 1A. Under the guard, B returns the same 72-character contents line
A returns. **Neither method locates a body**, and A's 72 characters are
not a business section either — so the honest label is that Honeywell's
Item 1 body was never located by either.

### RF — B's own defect. **C = neither.**

B opens at 118,097 on *"Item 1. Business 8 Item 1A. Risk Factors 20…"* —
the **table of contents** — and closes at the body's `Item\xa01A. Risk
Factors` at 209,999. The body's Item 1 is at **134,930**: *"Item 1.
Business Regions Financial Corporation is a FHC headquartered in
Birmingham, Alabama."* The correct span is 134,930 → 209,999 =
**75,069**; B's is over-wide by 16,833 characters of front matter.

Both occurrences satisfy `begins_a_block`, and the contents-to-peer step
is wider than the body-to-peer step, so `_width_score` prefers the wrong
one. Eight further RF occurrences are prose cross-references and every
one is correctly `begins_a_block=False` — **the structural test works;
the tie-break between two genuine block-beginning headings does not.**

### MET — the same defect. **C = neither.**

B opens at 380,376 on the contents; the body is at 387,791 (*"Item 1.
Business Index to Business Page Business Overview & Strategy 5"*). A
opens on the body and reads 184,927; B reads 109,704 from the contents.

### RF discussion — **C = B.**

A reads 97 characters, a contents line. B opens on the body —
*"EXECUTIVE OVERVIEW Management believes the following sections…"* — and
closes at the body's Item 7A. B is right; A is a contents entry.

### GS — **C = B, and the guard widens it further.**

Both open at the same offset. A closes at 43,437; B at 151,951, and
under the guard at 156,079. B rejected **18** candidates, all prose
cross-references (*"Item 1 of this Form 10-K for further information
about our resolution plan"*), correctly `begins_a_block=False`.
Goldman's Item 1 carries its Regulation and Human Capital discussion, so
the wider span is the section. The discussion is the same shape: A
1,203, B 311,737, 19 rejected references.

### PG and WMT — **C = B.**

A reads 19 and 18 characters. Both are contents lines. B reads 16,623
and 37,500. There is nothing to weigh.

### JPM — **the reported regression is an artifact. C = both agree.**

| | |
|---|---|
| A raw span | **39,176** |
| A as `business_text` (`_joined`) | **119,177** |
| the difference | **80,001 characters incorporated by reference** |
| B raw span | **40,653** |

#191 compared 119,177 against 40,653 and reported −66%. Raw against raw
it is **+4%**. JPM is the only company in the corpus where joined and raw
differ — but it was the largest single regression in #191's table, and
it was not real.

### CB and FITB — **residual ambiguity, not adjudicated.**

B narrows both materially (CB 156,013 → 82,121; FITB 71,198 → 41,418)
and neither opening is a contents entry. Deciding them needs the body's
closing-peer offset resolved against the filing's own structure, which
this corpus recorded but did not adjudicate. **They are why the generic
rewire cannot be approved on this evidence.**

## 6. Incorporation by reference

Only **JPMorgan** carries a materially large incorporated chapter —
80,001 characters, which `_referenced` follows and `_joined` appends.
`section_locator` has no equivalent, so any future rewire must preserve
`_referenced`/`_joined` or JPMorgan's business description loses two
thirds of its content. It is the one case where #191's concern was
directionally right even though its number was not.

## 7. The 20-F problem — 8 of 48 rows

BCS, DB, MUFG and NWG file **20-F**, where **Item 1 is "Identity of
Directors, Senior Management and Advisers"** and **Item 7 is "Major
Shareholders and Related Party Transactions"**. Neither is a business
description and neither is MD&A. Deutsche Bank's Item 1 reads, in the
filing's own words, *"Not required because this document is filed as an
annual report."*

**Both methods ask the wrong question for these four filings.** The 20-F
equivalents are **Item 4 (Information on the Company)** and **Item 5
(Operating and Financial Review and Prospects)**, and neither `_ITEM_1`
nor `section_locator.Item(1)` is form-aware. This is a missing form
dispatch, not a locator defect, and it explains eight rows without
either implementation being at fault.

## 8. Absence contract, applied

| category | rows | example |
|---|---|---|
| genuinely absent / not required | 8 | DB Item 1 — *"Not required"* |
| incorporated by reference | 1 | JPM business, 80,001 chars followed |
| heading not located (literal miss) | 8 | AXP, RF, MET under A |
| heading located, structurally ambiguous | 3 | RF, MET — contents and body both begin blocks |
| contents entry mistaken for body | 12 (A), 3 (B) | PG 19 chars, WMT 18 chars |
| body opened, closing peer not established | 2 | CB, FITB — unadjudicated |
| document unreadable | 2 | C — no item heading of any form |

## 9. Controls

| control | result |
|---|---|
| Item 1 → 1A → 1B → 1C → 2 ordering | **holds** — AXP, RF, MET resolve the full sequence |
| Item 7 → 7A → 8 ordering | **holds** |
| dotted current-report numbering (#191) | **unchanged** under the guard |
| Item 5.02 controls from #191 | **unchanged** |
| typography normalisation alone establishes a boundary | **never** — every prose cross-reference in RF (8) and GS (18 + 19) is `begins_a_block=False` and rejected |
| prose references open or close sections | **no** |
| annual reports carrying current-report cross-references | **correctly interpreted** — HON and MET print `Item 5.02`/`Item 5.05` references and neither becomes a section |
| `Item(1, "A")` positional construction | **unchanged** — the guard adds a lookahead, not a field |

## 10. Estimated production impact

**Nothing in production moves today.** `_section` is not wired to
`section_locator`, and no stored evidence is re-read. The impact is on
future acquisitions only.

- **The suffix guard alone**: 2 of 24 companies change what a future
  `section_locator` reading would return. Nothing consumes it for annual
  reports, so live impact is **zero** — and it removes the single
  regression that blocked #191.
- **The full rewire**: 10 recoveries, 3 over-wide contents openings, 2
  unadjudicated narrowings, and JPMorgan's 80,001 incorporated
  characters at risk. **Not supportable on this corpus.**

## 11. Conclusion

# B — TARGETED REPAIRS ONLY

The generic rewire remains unsafe. Two named defects have generic,
separately justified repairs, and neither requires the rewire.

### Repair 1 — the suffix guard (smallest, recommended)

`\s*([a-c])?` → `\s*([a-c])?(?![A-Za-z])` in
`section_locator._CANDIDATE`.

A pre-existing defect: `Item 1 Business` reads as Item 1B, `Item 1
Company overview` as Item 1C, `ITEM 1 About Honeywell` as Item 1A.
Measured — **2 of 24 companies move**, no legitimate suffix breaks
(`Item 1A.`, `Item 7A.`, `ITEM 1A RISK FACTORS`, `Item 1B.` all still
read correctly), the dotted current-report numbering is untouched, and
it recovers exactly the Honeywell loss that stopped #191.

**It is a defect in a module already wired into `statement_locator`**, so
its correctness matters whether or not the annual-report rewire ever
happens — which is what makes it separately justified rather than
rewire-preparation.

### Repair 2 — contents-versus-body, named but not specified

`_width_score` rewards width, so where a contents entry and a body both
begin a block, the contents entry's step to the body's peer is wider and
wins. RF and MET both fail this way. **A repair needs a measurement this
corpus did not make** — how a contents entry differs structurally from a
body heading beyond width — and should not be guessed at.

### Not ready, explicitly

- the annual-report rewire (CB and FITB unadjudicated, RF and MET
  over-wide, JPMorgan's incorporation unhandled);
- form-aware item selection for 20-F filers (8 rows asking for the wrong
  item);
- AXP's repair, which this task was told not to make and does not.

## 12. Scope compliance

Research only · no production implementation · `_section`,
`section_locator` and `statement_locator` **unchanged on disk** — the
guard was simulated by substituting the compiled pattern in memory and
restoring it, asserted afterwards · **zero model calls** · no new
evidence acquired: every filing was read from the immutable address the
resolver already holds · no production evidence written, no reading
promoted, no consensus or company understanding altered · **AXP not
repaired** · no analyst, committee, CIO or decision change ·
`git status --porcelain data/` empty · Codex's unpublished `d203609` not
read, reused or published.
