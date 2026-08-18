# A contents entry is a heading in a listing, and a listing is countable

**Status: research. 402 labelled occurrences over the 24 held annual
reports, plus the 244-filing Item 5.02 control corpus. Zero model calls,
no production implementation, no production data mutation. `_section`,
`section_locator` and `statement_locator` are unchanged on disk — the
rules below were run over the live `Candidate` objects in a research
harness, and the one place a compiled pattern was substituted (to
reconstruct pre-#199 behaviour) restores it and asserts the restore.**

#198 named the contents-versus-body tie-break and refused to guess at
it. This is the measurement it asked for.

> **The distinguishing evidence is not width, not position, not
> capitalisation and not proximity to the words "table of contents".
> It is that a contents entry is *followed by more of the same listing*:
> a chain of further items, each advancing the item number, each within
> a couple of thousand characters of the last.** Counting that chain
> separates all 36 contents entries from all 39 body headings **with no
> errors**, and the separation survives across a plateau of parameter
> settings rather than balancing on one.
>
> **The defect is four times larger than #198 recorded.** Twelve of the
> 24 filings open Item 1 on a contents entry, not two — AAPL, ALL, CB,
> COF, DIS, GS, JPM, MET, MTB, PG, RF and UNP. **Every Item 7 is already
> correct**, which is itself the clue: nothing about Item 7 is different
> except how the listing happens to score.
>
> **Two premises this task was given do not reproduce.** DB and MUFG do
> **not** open Item 4 on a contents entry. MUFG opens on its body
> heading and is entirely correct today; DB opens on a **running page
> header** 108 characters before its body heading. #200's own recorded
> widths (156,875 and 185,174) already contradicted its §7 sentence, and
> direct measurement agrees with the widths.
>
> **#199 introduced one of the twelve.** Before the suffix guard,
> Goldman Sachs opened Item 1 on its **body** at 200,346; the guard made
> the contents entry a candidate for the first time and `_width_score`
> preferred it. The proposed selector restores the pre-#199 span exactly
> — same opening, same closing, 151,951 characters.
>
> **The corpus forced a label the taxonomy did not have.** Deutsche Bank
> prints its item title at the top of every printed page: **38 running
> page headers**, each a genuine block-beginning numbered heading, each
> indistinguishable from a body heading on every signal measured. They
> are why *"the later occurrence wins"* is not merely inelegant but
> wrong — it would cut DB's Item 4 from 185,174 characters to 4,607.

---

## 1. Method

Every filing read from the immutable address the resolver already holds,
cached once, and every pass run over that cache so the offsets are
comparable between passes.

| | |
|---|---|
| annual filings | **24** (20 × 10-K, 4 × 20-F) |
| requested items | 10-K → Item 1, Item 7 · 20-F → **Item 4, Item 5** (#200's mapping, measured only — **no dispatch is implemented**) |
| requested-item occurrences discovered | **402** |
| occurrences the current structural test accepts | **119** |
| control corpus | **244** Item 5.02 current reports, #190's own filter |
| model calls | **0** |

Occurrences were labelled from **the printed text and what follows it**
— never from the numeric signals under test, which is the whole point of
keeping the two apart. `begins_a_block` was recomputed from precomputed
block edges for speed and **asserted identical to the production
function** on every occurrence of three sampled filings (188 of 188, 0
mismatches).

### The labels

| label | n | what it is |
|---|---|---|
| `PROSE_REFERENCE` | **283** | inside a sentence |
| `OTHER_OR_AMBIGUOUS` — *running header* | **41** | page furniture repeating the item title |
| `BODY_HEADING` | **39** | opens the substantive section |
| `CONTENTS_HEADING` | **36** | an entry in the document's own listing of its items |
| `CROSS_REFERENCE_INDEX` | **2** | Honeywell's *"FORM 10-K CROSS-REFERENCE INDEX"* |
| `INCORPORATED_POINTER` | **1** | JPMorgan's Item 7, which names the pages its content appears on |

`RUNNING_HEADER` is recorded as a sub-class of `OTHER_OR_AMBIGUOUS`
rather than as a seventh label, because the task fixed the taxonomy. It
is reported separately throughout because it behaves like nothing else
in the corpus.

**All 283 rejected occurrences fail on one observation** — none of them
begins a block. Not one rejected occurrence begins a block, so the
existing structural test is doing exactly the job it claims, and every
rule below only ever *removes* candidates from the accepted set.

---

## 2. What is actually wrong today

Reproducing `section_locator.locate()` over all 24 filings gives #198's
B column exactly (AXP 86,613 · RF 91,902 · MET 109,704 · CB 82,121 ·
FITB 41,418 · HON 72/96 · JPM 40,653/396 · PG 16,623/92,104). Against
the labels:

| outcome | n |
|---|---|
| opens on the labelled `BODY_HEADING` | **26** |
| **opens on a `CONTENTS_HEADING`** | **12** |
| opens on the `CROSS_REFERENCE_INDEX` — the only candidate there is | 2 |
| opens on the `INCORPORATED_POINTER` — correctly | 1 |
| opens on a **running page header**, 108 characters early | 1 |
| absent | 4 (BCS ×2, NWG ×2) |
| absent — document unreadable | 2 (C) |

**The twelve, all Item 1, none of them Item 7:**

AAPL · ALL · CB · COF · DIS · GS · JPM · MET · MTB · PG · RF · UNP.

#198 found two of these (RF, MET) because it was reading widths and only
RF's and MET's contents openings produced a width that looked wrong. The
other ten produce plausible widths and are wrong in the same way.

---

## 3. The nine signals, measured

Over the 36 `CONTENTS_HEADING` and 39 `BODY_HEADING` occurrences, best
single cut, with the number of occurrences that cut misclassifies:

| # | signal | contents (min/med/max) | body (min/med/max) | best single cut | wrong |
|---|---|---|---|---|---|
| 1 | distance back to a contents marker | 21 / 264 / 1,290 | 9 / 16 / 3,300 | — | **10 of 54** |
| 2a | item occurrences within 1k | 7 / 19 / 25 | 1 / 2 / 16 | body < 7 | 6 of 75 |
| 2b | item occurrences within 3k | 11 / 23 / 32 | 1 / 4 / 26 | body < 17 | 8 of 75 |
| 2c | distinct items within 3k | 11 / 23 / 23 | 1 / 3 / 23 | body < 17 | 8 of 75 |
| 3a | page-number grammar in the next 2k | 1 / 11 / 26 | 0 / 0 / 1 | body < 2 | 1 of 75 |
| 3b | bare numbers in the next 500 | 5 / 10 / 22 | 0 / 0 / 13 | body < 5 | 4 of 75 |
| 4 | the same item appears again later | 1 / 5 / 45 | 0 / 2 / 38 | body < 3 | **26 of 75** |
| 5 | characters to the next item occurrence | 18 / 97 / 838 | 216 / 3,602 / 251,562 | contents < 378 | 9 of 75 |
| 6a | **listing run — consecutive ascending items following** | **12 / 13 / 22** | **0 / 0 / 1** | **body < 8** | **0 of 75** |
| 6b | the same run, backwards | 0 / 4 / 9 | 0 / 0 / 4 | body < 5 | 18 of 75 |
| 7 | candidate-to-next-peer width | 18 / 97 / 838 | 216 / 20,718 / 251,562 | contents < 900 | 5 of 75 |
| 8 | relative document position | — | — | contents < 0.21 | **18 of 75** |
| 9 | begins a block / capitals | — | — | — | **separates nothing** (see below) |

### What each result means

**Signal 1 is actively misleading and the reason is worth keeping.**
An EDGAR filing prints *"Table of Contents"* as a **running page header
on every page**, so the nearest contents marker is *closer* to the body
heading (median 16 characters) than to the contents entry (median 264).
The signal that looks most obviously right is the one that points the
wrong way.

**Signal 3b nearly works and fails on the case that matters.** MetLife's
body Item 1 opens *"Item 1. Business Index to Business Page Business
Overview & Strategy 5 Segments and Corporate & Other 6 …"* — a **section
index inside the body**, 13 bare numbers in 500 characters. Counting
numbers cannot tell a document's contents from a section's own index.
Signal 3a survives it only because MetLife's index carries no further
*item* numbers.

**Signal 5 and signal 7 overlap, and the overlap is real.** Chubb's body
Item 7 has an item occurrence 378 characters later; Goldman's contents
Item 7 has one 726 characters later. A single gap cannot separate them.

**Signal 8 is an observation and nothing more**, as the task required. It
was recorded, and it separates nothing: Honeywell's cross-reference index
sits at relative position **0.998**, at the very end of the document.

**Signal 9 is what the module already uses, and it has run out.** Every
one of the 119 eligible occurrences begins a block; capitals are a filer
habit, not a role. Typography got the corpus this far and cannot go
further — which is #198's own first invariant arriving in practice.

### Signal 6a, stated exactly

> A candidate's **listing run** is the number of item occurrences that
> follow it in an unbroken chain, where each step advances the item
> number and each step is no more than `G` characters long.

No window, no width, no page numbers, no vocabulary. It says only: *the
document keeps listing items after this one*.

| | contents / index | body | running header | incorporated pointer |
|---|---|---|---|---|
| listing run (G = 2,000) | **12 – 22** | **0 – 1** | **0 – 1** | 4 |

---

## 4. Is the run a structure or a fitted constant?

The two parameters were swept, and the corpus outcome recorded at each
setting.

### Classification errors over all 119 eligible occurrences

| G \ length | 3 | 5 | 6 | 8 | 10 |
|---|---|---|---|---|---|
| 1,000 | 5 | 4 | 4 | 4 | 4 |
| **2,000** | 1 | **0** | **0** | **0** | **0** |
| 3,000 | 1 | 1 | 1 | **0** | **0** |
| 5,000 | 2 | 1 | 1 | **0** | **0** |

### The whole corpus reading, over 54 settings

**49 of the 54 settings produce a byte-identical set of 48 spans.** The
five that do not are all at the corners, and each is named:

| setting | what differs |
|---|---|
| (4,000, 2) (4,000, 3) (4,000, 4) | `UNP Item 1` — at G = 4,000 the body heading chains 4 steps |
| (1,000, 12) | `COF` `GS` `MTB` `PG` Item 1 — their contents runs are only 2 at G = 1,000 |
| (1,500, 12) | `GS` `MTB` Item 1 — the same cause |

**Chosen: G = 2,000, length ≥ 6.** It is interior to the largest clean
block (G = 2,000, length 5–10), and both margins are wide: the longest
non-listing run is 4 (JPMorgan's pointer) and the shortest listing run
is 12 (four separate filings). Nothing in the corpus sits between 5 and
11.

**The single false positive, documented as the task requires.**
JPMorgan's Item 7 is an `INCORPORATED_POINTER` whose run is 4 at
G = 2,000 — correctly *not* a listing — but 6 at G = 3,000, where it
would be misclassified. The cause is structural and will recur: **a
filing whose sections are all pointers is a list of items with page
numbers, which is what a table of contents is.** JPMorgan's Part II
prints Item 7, 7A, 8 and 9 as consecutive short pointer blocks. The
selected rule survives it twice over — once because G = 2,000 classifies
it correctly, and once because Rule B below would reach the right span
even if it did not (§6).

---

## 5. The four primary specimens

### RF Item 1 — 14 occurrences

| # | offset | printed | label | evidence | verdict |
|---|---|---|---|---|---|
| 0 | 118,097 | `Item\xa01.` | **CONTENTS_HEADING** | begins a block · **listing run 22** · next item +19 · 19 page-grammar hits · under *"FORM 10-K INDEX"* at −113 | **reject as opening** |
| 1 | **134,930** | `Item\xa01.` | **BODY_HEADING** | begins a block · **listing run 0** · next item +2,598 · 0 page-grammar hits | **select** |
| 2–13 | 247,384 – 362,100 | `Item 1.` | PROSE_REFERENCE ×12 | none begins a block | reject (unchanged) |

Contents text: `Item 1. Business 8 Item 1A. Risk Factors 20 Item 1B.
Unresolved Staff Comments 40 …`
Body text: `Item 1. Business Regions Financial Corporation is a FHC
headquartered in Birmingham, Alabama…`

**Correct span 134,930 → 209,999 = 75,069**, closing on the body's
`Item 1A. Risk Factors An investment in the Company involves risks…`.
Today: 118,097 → 209,999 = 91,902, over-wide by **16,833** characters of
front matter.

### MET Item 1 — 2 occurrences

| # | offset | label | evidence | verdict |
|---|---|---|---|---|
| 0 | 380,376 | **CONTENTS_HEADING** | listing run 22 · next item +21 · 19 page-grammar hits | **reject as opening** |
| 1 | **387,791** | **BODY_HEADING** | listing run 0 · next item +102,289 · **13 bare numbers** (its own *"Index to Business"*) | **select** |

MetLife is the specimen that kills the bare-number signal and the
contents-marker signal at once: its body heading carries a section index
*and* sits 16 characters after a running *"Table of Contents"* header.
Only the listing run reads it correctly.

**Correct span 387,791 → 490,080 = 102,289**, closing on the body's
`Item 1A. Risk Factors Any or each of the events described below…`.
Today: 380,376 → 490,080 = 109,704, over-wide by **7,415**.

### DB Item 4 — 46 occurrences, and the premise that does not reproduce

| class | n | offsets | listing run |
|---|---|---|---|
| `CONTENTS_HEADING` | 1 | 412,292 | **15** |
| `BODY_HEADING` | 1 | **578,583** | 0 |
| **running page header** | **38** | 578,475 … 759,042 | 0 |
| `PROSE_REFERENCE` | 6 | — | — |

Each running header prints `<page> Deutsche Bank | Item 4: Information
on the company | Annual Report 2025 on Form 20-F | <chapter>` at the top
of a printed page, roughly every 5,000 characters. All 38 begin blocks.
All 38 are indistinguishable from the body heading on **every signal
measured**.

**DB does not open on its contents entry.** It opens at 578,475 — the
running header 108 characters before the body heading at 578,583 —
and reads 185,174 characters, which is #200's own recorded width. The
contents entry at 412,292 was never selected.

**Correct opening 578,583; selected opening 578,475; closing Item 4A at
763,649.** The residual over-width is **108 characters, 0.058% of the
span**, and no rule in this report removes it.

### MUFG Item 4 — 21 occurrences

| # | offset | label | listing run | verdict |
|---|---|---|---|---|
| 0 | 271,458 | `CONTENTS_HEADING` | 15 | reject as opening |
| 6 | **358,607** | **`BODY_HEADING`** | 0 | **select — and already selected today** |
| 1–5, 7–20 | — | `PROSE_REFERENCE` ×19 | — | reject (unchanged) |

`Item 4. Information on the Company. A. History and Development of the
Company MUFG is a bank holding company incorporated as a joint stock
company…`

**MUFG Item 4 is correct today and needs no repair**, as are MUFG Item 5
(515,527, 217,570) and DB Item 5 (763,958, 7,053 — the labelled body
heading). Of the eight 20-F readings, **one is imperfect by 108
characters and four are absent because the filing prints nothing.**

---

## 6. The rules considered, and the counterfactual for each

### Rule A — contents membership vetoes the candidate

A listing entry gets a contradicting observation and never reaches the
accepted set.

**Result: the twelve openings are all corrected, and Honeywell is
lost.** HON Item 1 and Item 7 become **absent**, because Honeywell's only
occurrences of either item are inside its cross-reference index. That is
the #199 recovery, deleted.

### Rule B — contents membership makes a candidate ineligible **to open a
section**, but only where that item has a non-listing candidate

Listing entries are removed from the accepted set **for items that also
have a non-listing accepted candidate**. Where an item's only candidates
are listing entries, they are retained — because the alternative is
silence about a section the filer did print.

**Result: the twelve openings are corrected and nothing else moves.**

| | A | B |
|---|---|---|
| Item 1 openings corrected | 12 | **12** |
| readings unchanged | 34 | **36** |
| HON Item 1 / Item 7 | **lost** | preserved, byte-identical |
| JPM Item 7 pointer | preserved at G = 2,000 | preserved at **every** G, by the no-alternative clause |
| Item 5.02 spans moved | 0 | **0** |

Rule B is robust to the one classification error the corpus contains:
even at G = 3,000, where JPMorgan's pointer is misread as a listing
entry, both of JPM Item 7's candidates are then listing entries, no
alternative exists, both are retained, and the resolved span is
unchanged.

### Rule "the later occurrence wins" — the prohibited shortcut, refused
on evidence

It agrees with Rule B on 46 of 48 readings, which is exactly why it is
dangerous. It disagrees on Deutsche Bank, and there it is catastrophic:

| reading | later-wins | correct | |
|---|---|---|---|
| DB Item 4 | opens 759,042 | opens 578,475 | **185,174 → 4,607 characters** |
| DB Item 5 | opens 769,275 | opens 763,958 | the last running header, not the section |

### Rule "the widest span wins" — refused, because it is what is running
today

`_width_score` already rewards width. It is the mechanism that produces
all twelve contents openings: the contents entry's step to the body's
peer is wider than the body's own. No counterfactual is needed; the
baseline *is* the counterfactual.

---

## 7. Exact corpus movement under Rule B

**12 of 48 readings move. All 12 are Item 1. All 12 land exactly on the
labelled body heading. All 12 narrow.**

| reading | today | → Rule B | width change |
|---|---|---|---|
| AAPL Item 1 | 19,179 (19,333) | **22,458 (16,054)** | −3,279 |
| ALL Item 1 | 131,576 (60,650) | **133,231 (58,995)** | −1,655 |
| CB Item 1 | 196,475 (82,121) | **197,887 (80,709)** | −1,412 |
| COF Item 1 | 175,868 (89,282) | **180,881 (84,269)** | −5,013 |
| DIS Item 1 | 64,786 (73,195) | **71,215 (66,766)** | −6,429 |
| GS Item 1 | 196,218 (156,079) | **200,346 (151,951)** | −4,128 |
| JPM Item 1 | 238,585 (40,653) | **240,062 (39,176)** | −1,477 |
| MET Item 1 | 380,376 (109,704) | **387,791 (102,289)** | −7,415 |
| MTB Item 1 | 125,985 (85,896) | **134,198 (77,683)** | −8,213 |
| PG Item 1 | 42,718 (16,623) | **45,046 (14,295)** | −2,328 |
| RF Item 1 | 118,097 (91,902) | **134,930 (75,069)** | −16,833 |
| UNP Item 1 | 31,655 (35,680) | **40,317 (27,018)** | −8,662 |

**Nothing else moves**: 36 readings identical, including every Item 7,
every 20-F reading, both Honeywell readings, both Barclays and NatWest
absences and both Citigroup absences.

### Closing peers — question 5

**No span is over-wide and no closing peer is a listing entry**, except
Honeywell's, where the index is the only structure the filing prints.
Every one of the twelve closings was read back from the text and is a
genuine body heading:

> `Item 1A. Risk Factors An investment in the Company involves risks…`
> (RF) · `Item 1A. Risk Factors Any or each of the events described
> below…` (MET) · `ITEM 1A. Risk Factors Factors that could have a
> material impact…` (CB) · `Item 1A. Risk Factors We face a variety of
> risks that are substantial and inherent…` (GS)

**This adjudicates CB and FITB** — #198's two unresolved narrowings.
Both close on the filer's own body `Item 1A`, verified by reading the
text at the closing offset rather than by comparing widths. CB Item 1 is
197,887 → 278,596; FITB Item 1 is 187,994 → 229,412 and does not move at
all. #198's A readings (156,013 and 71,198) ran past the real Item 1A.
**They are the same evidence as the other ten, not a separate
ambiguity.**

---

## 8. Mandatory controls

| control | result |
|---|---|
| RF prose cross-references stay rejected | **20 measured** (Item 1 ×12, Item 7 ×8; #198's "8" was a partial count), 0 accepted today, 0 accepted under Rule B |
| GS prose cross-references stay rejected | **37 measured** (Item 1 ×19, Item 7 ×18) — matches exactly; 0 accepted either way |
| no rejection can reverse | **structural** — Rule B only removes candidates from the accepted set and adds none |
| AXP unchanged | **69,885 → 156,498 (86,613)** and **284,450 → 445,008 (160,558)**, identical pre-#199, today and under Rule B |
| HON #199 recovery holds | Item 1 **absent pre-#199 → 557,781 (72) today → 557,781 (72) under Rule B**; Item 7 unchanged throughout |
| GS #199 recovery holds | see below |
| 244 Item 5.02 spans | **244 of 244 identical.** 241 located before, 241 after |
| the three Item 5.02 residuals | **still residual, and the same three** — `CVX 0000093410-22-000042`, `NKE 0000320187-22-000025`, `NKE 0001628280-22-012729` |
| DB/MUFG keep Item 4 / Item 5 | mapping measured only; **no dispatch, no form plumbing, no `_section` rewire** |
| BCS/NWG not treated as printing Item 4/5 | **0 requested-item occurrences discovered in either**; absent today, absent under Rule B; no page range followed |
| production untouched on disk | `git status --porcelain app/` empty |

### The GS control needs stating precisely, because it cannot hold as worded

Reconstructing the pre-#199 pattern in memory:

| | opening | closing | width |
|---|---|---|---|
| GS Item 1, **pre-#199** | 200,346 | 352,297 | 151,951 |
| GS Item 1, **today** | **196,218** | 352,297 | 156,079 |
| GS Item 1, **Rule B** | **200,346** | 352,297 | 151,951 |

**#199 did not widen Goldman's Item 1; it moved the opening onto the
contents entry.** Before the guard, `Item 1 Business` in the contents was
discovered as `Item 1B`, so the contents entry was not a candidate and
the body was the only Item 1 there was. The guard made it a candidate
and `_width_score` preferred it.

So the control *"GS #199 outcome remains unchanged"* and the objective
*"stop opening on contents entries"* are the same question with opposite
answers, because **GS is one of the twelve**. What is preserved is what
#199 actually recovered — Item 1 located, closing at 352,297 — and Rule B
returns the exact pre-#199 span. Reported rather than reconciled away.

---

## 9. The questions, answered

**1. Can contents membership become explicit contradictory evidence
against opening a section?** **Yes as a measurement, no as an
implementation.** It is measurable with no errors over 119 eligible
occurrences. But as *evidence* — Rule A, feeding
`Candidate.is_heading` — it deletes Honeywell's only reading of either
item. **Contents membership is a fact about a candidate's role, not
about whether it is a heading**, and the module's `Evidence` type means
the second thing.

**2. Should a genuine heading in the wrong structural role remain
useful as sequence evidence while being ineligible as the selected
opening?** **Yes, and the corpus shows exactly where it matters.** Under
Rule B a listing entry is retained precisely when its item has no other
candidate — and in the two cases where that happens (HON Item 1 and Item
7) the retained entry serves as **both** the opening and the closing
peer. In every other reading no closing peer is a listing entry, so the
retention costs nothing.

**3. Does the fix belong in candidate evidence, candidate selection or
peer resolution?** **Candidate selection** — between `candidates()` and
`sequence()`. Evidence is wrong for the reason in question 1. Peer
resolution is wrong because the closings are already correct: all 42
located readings close on a genuine peer, and no closing moves.

**4. How is the correct body chosen when both occurrences begin blocks
and have valid neighbours?** **By what follows, not by what precedes or
by how wide it is.** A contents entry is followed by 12 to 22 more items;
a body heading by 0 or 1. Both begin blocks, both have valid neighbours,
and the neighbours are what differ: the contents entry's neighbour has
another neighbour, and so does that one.

**5. Can the selector find the correct closing peer without producing
over-wide spans?** **Yes — it does not have to find one.** The closings
were already right; the openings were not. Zero over-wide spans, zero
closings on a listing entry outside Honeywell.

**6. Can the rule generalise across 10-K and 20-F without form-, issuer-
or ticker-specific exceptions?** **Yes.** One rule, no exceptions, no
form input, no issuer list. It corrects 12 of 20 10-K filers, leaves all
four 20-F filers exactly as they are, and moves none of the 244 current
reports. **It never reads the form**, which is what keeps it independent
of the dispatch #200 specified and this task forbids.

**7. Are CB and FITB resolved by the same evidence, or do they remain
genuinely ambiguous?** **Resolved by the same evidence.** CB was a
twelfth contents opening (196,475 → 197,887) and FITB was never wrong at
all. Both close on a body `Item 1A` read back from the text. Neither
remains ambiguous.

---

## 10. What is still not solved

**Running page headers.** 38 of Deutsche Bank's 46 Item 4 occurrences
are page furniture, and **no signal in this report distinguishes one from
a body heading** — listing run 0, block-beginning, no page grammar, low
local density. Deutsche Bank survives only because the earliest of them
sits 108 characters before the real heading. A filer whose running header
appeared *before* the section would be cut arbitrarily early, and this
corpus contains no such filer to measure. **This is a named residual, not
a solved case.**

**A pointer-structured filing is shaped like a table of contents.**
JPMorgan's Part II is a run of short pointer blocks with page numbers,
which is what the listing rule counts. It is classified correctly at
G = 2,000 and incorrectly at G = 3,000. One specimen is not a corpus.

**Honeywell's body is still not located.** Rule B preserves #199's
72-character reading, and that reading is Honeywell's cross-reference
index, not its business section. Honeywell's body sections carry no item
numbers at all (*"About Honeywell"*), so there is nothing for a numbered
selector to find. Unchanged, and unchanged deliberately.

**Citigroup is still unreadable** — no item heading of any form, as #198
recorded.

**Barclays and NatWest still print no Item 4 or Item 5.** Nothing here
changes that, and no page range was followed into any incorporated
component.

---

## 11. Conclusion

# A — GENERIC SELECTOR READY

### The evidence rule

> A candidate's **listing run** is the number of item occurrences
> following it in an unbroken chain where each step advances the item
> number and each step is at most **2,000** characters. A candidate whose
> listing run is **6 or more** is a **listing entry**.
>
> A listing entry is **ineligible to open a section for an item that has
> a non-listing accepted candidate**. Where an item's only accepted
> candidates are listing entries, they are retained.

### The implementation layer

`section_locator`, between `candidates()` and `sequence()` — **candidate
selection**, not `Evidence` and not peer resolution. `Candidate`,
`Evidence`, `is_heading`, `_width_score`, `sequence()`, `_CANDIDATE` and
`observe()` are all untouched, and so is `statement_locator`.

### Expected movements

**12 of 48 annual readings**, all Item 1, all narrowing, all landing on
the filer's own body heading: AAPL · ALL · CB · COF · DIS · GS · JPM ·
MET · MTB · PG · RF · UNP. **36 readings byte-identical.**

### Refusals preserved

BCS and NWG absent · C absent · all 20 RF and 37 GS prose
cross-references rejected · Honeywell's two readings unchanged · the
three Item 5.02 residuals still residual.

### Controls

**244 of 244** Item 5.02 spans identical · AXP identical · HON identical
· GS closing identical and the opening restored to its pre-#199 value ·
zero over-wide spans · zero closings moved · 49 of 54 parameter settings
give the identical corpus reading.

### What this does not include, deliberately

No 20-F dispatch · no form-field plumbing on `PrimarySource` · no
`_section` rewire · no annual-section rewire · no AXP repair beyond
leaving it untouched · no page ranges followed into incorporated
components · no running-header repair · **no production code changed**.

**The smallest justified slice is the selector alone**, inside
`section_locator`, with the 12 movements and the 244-filing control as
its acceptance. It is offered for ruling, not built: the phase gate
applies, and `_section` is still not wired to this module, so the
investor-facing benefit arrives only when the rewire that consumes it
does.

## 12. Scope compliance

Research only · no production implementation · `section_locator`,
`statement_locator` and `_section` **unchanged on disk** — the one
in-memory pattern substitution (pre-#199 reconstruction) restores the
live pattern and asserts the restore · **zero model calls** · no live
acquisition beyond reading filings from the immutable addresses the
resolver already holds · no production evidence written, no reading
promoted, no consensus, understanding, analyst, committee, CIO or
decision change · `git status --porcelain data/` empty · no form
dispatch · no ticker, filer or form exception anywhere in the rule ·
Codex's unpublished `d203609` not read, reused or published.
