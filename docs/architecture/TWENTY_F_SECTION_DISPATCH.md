# A 20-F is read at the items a 20-F prints

**Status: built. 2026-08-19.** The third and last step of the order
[`TWENTY_F_REFUSAL_SEMANTICS.md`](TWENTY_F_REFUSAL_SEMANTICS.md) §4 set
out: the carrier (#210), the Citigroup correction (#210), and the exact
20-F dispatch (this one). Page-range traversal remains step 4 and
remains unscoped.

---

## 1. What the investor gets

Two of the four held 20-F filings are now **read**, and the other two are
**refused in words**. Before this slice all four were silently empty or
silently wrong.

| symbol | form | section | before | after | outcome |
|---|---|---|---|---|---|
| **BCS** | 20-F | Item 4 | 0 · **no refusal** | 0 | **`CROSS_REFERENCE_INDEX`** |
| **BCS** | 20-F | Item 5 | 0 · **no refusal** | 0 | **`CROSS_REFERENCE_INDEX`** |
| **DB** | 20-F | Item 4 | 0 · **no refusal** | **185,173** | read |
| **DB** | 20-F | Item 5 | 1,235 · **no refusal** | **7,052** | read |
| **MUFG** | 20-F | Item 4 | **81** · **no refusal** | **156,874** | read |
| **MUFG** | 20-F | Item 5 | 6,525 · **no refusal** | **217,569** | read |
| **NWG** | 20-F | Item 4 | 0 · **no refusal** | 0 | **`CROSS_REFERENCE_INDEX`** |
| **NWG** | 20-F | Item 5 | 0 · **no refusal** | 0 | **`CROSS_REFERENCE_INDEX`** |

**MUFG's business description is the clearest single number here: 81
characters became 156,874.** The 81 were a table-of-contents entry.

All four text digests match, bit for bit, the ones #209's stage-1
simulation predicted before any production code was written —
`41e8ba511f4ab522`, `303a025e43de8172`, `b2fb647ce987ad32`,
`7db7c0e8fcfd6b28`.

---

## 2. Why the item numbers are not interchangeable

The SEC prescribes both sequences, and they do not correspond.

| | describes the business | reviews performance | **Item 1 is** |
|---|---|---|---|
| **10-K** | Item 1 | Item 7 | *Business* |
| **20-F** | **Item 4** — *Information on the Company* | **Item 5** — *Operating and Financial Review and Prospects* | *Identity of Directors, Senior Management and Advisers* |

So asking a 20-F for Item 1 does not merely read the wrong section. It
reads a section about **people** as though it answered *what does this
company do* — and a filer whose Item 1 says *"Not applicable."* would
have that non-answer stored as its business description.

**This is Invariant 2, not a convenience.** Identity, grounding and
applicability are independent: a perfectly grounded, exactly cited
reading of the right filing is still wrong when it is cited for the
wrong claim.

---

## 3. The change

One mapping and one lookup. Everything under it is the code that already
existed.

```python
ANNUAL_SECTION_ITEMS: dict[str, tuple[Item, Item]] = {
    "10-K": (Item(1), Item(7)),
    "20-F": (Item(4), Item(5)),
}
```

`_read` replaces `normalized_form(reference.form) == "10-K"` with a
lookup on that dict. **The two forms differ only in which items are
asked for** — the locator, the refusal producer and the separation of
the two sections are the same code on both, which is what makes a 20-F
not a special case of a 10-K but the same reading against a different
item map.

**Keyed by exact normalised form, with no default and no prefix match.**
`20-F/A` resolves to nothing and falls to the legacy reader, because
Barclays' amendment prints only Items 17-18: dispatched, it would ask a
document for a section it does not contain and report the answer as the
company's.

### No legacy fallback after a refusal

A 20-F whose Item 4 cannot be located is **refused**, never re-read
under `_ITEM_1`. Falling back would read a 20-F's *directors* as its
business — precisely the reading the mapping exists to remove, and it
would do it silently. Pinned by a test that reads one document under
both forms: as a `20-F` it is refused twice; as a `10-K` the same bytes
yield both sections.

---

## 4. Deutsche Bank's 108 characters — accepted, not repaired

DB's Item 4 opens 108 characters before the body heading. Verbatim:

> `Item 4: Information on the company Annual Report  2025 on Form 20-F History and development of  the company `

It is the filer's **running page header** — the item title, the report
title and the chapter title — and the body heading follows immediately:

> `Item 4: Information on the company History and development of the company The legal and co…`

**Ruled harmless by the owner and left alone.** The 185,173 characters
that follow are the section. Trimming it would mean teaching the reader
to recognise a running header, which is a capability with its own blast
radius and no measurement behind it; `section_locator` is untouched, and
so is this opening.

---

## 5. Barclays and NatWest — two refusals, not one failure

Both carry `CROSS_REFERENCE_INDEX` on **both** sections, and the two
refusals are **independent objects**, each naming the item it was asked
for:

> BCS · business description — *"The filing prints no **Item 4** heading and carries its own cross-reference index."*
>
> BCS · performance discussion — *"The filing prints no **Item 5** heading and carries its own cross-reference index."*

A reader is told **which section** could not be supplied, rather than
that the document failed. A filing may print one and not the other, and
refusing both because one is missing would report this reader's coupling
as the filer's silence — pinned by a test on a document that prints Item
4 and omits Item 5, where the business description is read and only the
discussion is refused.

The detector is unchanged from #210: the measured **conjunction** of an
absent item run and the filer's own cross-reference apparatus. Neither
half works alone — the phrase alone refuses Fifth Third and Honeywell,
which print both the phrase and their sections.

---

## 6. Controls

### Every 10-K reading is byte-identical — 40 of 40

Text digest, width, regions, tables and refusal object compared across
all 20 held 10-K filings.

**Citigroup's refusal is byte-identical**, reason and wording both. The
one filing #210 corrected did not move when the dispatch widened.

### Every statement span is byte-identical — 72 of 72

All 24 filings × 3 statements. **None lost.** And the refusing 20-Fs
demonstrate #210's load-bearing result on a second form:

| | income | balance sheet | cash flow |
|---|---|---|---|
| **BCS** — both sections refused | **1,811** | **2,660** | 0 |
| **NWG** — both sections refused | **2,480** | **1,850** | 0 |
| DB | 2,648 | 2,620 | 3,757 |
| MUFG | 3,162 | 3,002 | 4,902 |

Barclays and NatWest refuse both narrative sections and still yield
their income statement and balance sheet. An exception would have taken
those away in order to report the first refusal. (Their cash flow
statements read 0 **before this slice as well** — a pre-existing absence
on the statement run, untouched here and not caused by it.)

### No issuer branch

The AST guard from #210 now also rejects `deutsche`, ` db `, `mufg`,
`bcs` and `nwg` in anything `edgar_filings` **executes** — docstrings
excluded, so the prose may still quote where a wording came from. A
dispatch that worked because four issuers were spelled into it would
pass every measurement above and generalise to nothing.

### Scope

No 20-F/A · no page-range traversal · no incorporated-document traversal
· no issuer branch · **no `section_locator` change** · no DB repair · no
model call · no data mutation (`git status --porcelain data/` empty) ·
no Business Quality, committee, CIO, recommendation or Ticker News
change · `UNSUPPORTED_FORM` still produced by no code path.

### Gates

**3,331 tests** · ruff check + format · mypy (605 files) ·
`git diff --check` · HEAD verified from an isolated archive.

The 24 filings were re-fetched from the regulator's own archive at their
immutable accession addresses, with the platform's declared user agent,
and the before/after measurement was run over the identical cached bytes
from two worktrees — `main` at `19b03b8` and this branch.

---

## 7. Six superseded pins, updated rather than deleted

The 10-K cutover left six tests asserting *exactly one form*. Each is
narrowed to the contract that survives:

| test | was | now |
|---|---|---|
| `..._is_an_exact_lookup_over_the_mapped_forms` | equality against `"10-K"` | the **mapping**: exactly two keys, nothing looser resolves |
| `..._selects_the_reader_and_only_for_the_mapped_forms` | `20-F` in the legacy set | `20-F` dispatched; the unmapped set still reads identically |
| `..._reaches_this_module_only_for_mapped_forms` | source grep | every mapped item has **no fraction and no suffix** |
| `..._uses_this_module_for_the_mapped_forms` | source grep | the mapping's keys |
| `..._still_prefers_the_section_over_its_entry` | specimen form `20-F` | specimen form `8-K` |
| `..._on_the_legacy_path_still_produces_no_refusal` | `20-F` in the list | `20-F/A` in the list |

**Three of them asserted a source literal against a whole module.** They
are now assertions about what the dispatch *answers*, which is both the
question worth pinning and the shape that does not break when a line is
rewrapped.

---

## 8. Recorded, not solved

- **`UNSUPPORTED_FORM` is still produced by nothing.** An unmapped form
  falls to the legacy reader, which returns whatever the old anchors
  find and refuses nothing. Closing that is a separate decision: it
  would change what every non-annual document returns.
- **BCS and NWG cash flow statements read 0**, from the statement run
  and not from this dispatch. Unmeasured here.
- **The 108-character prelude** is accepted rather than understood. A
  running-header capability would remove it and is unscoped.
- **The contents-listing threshold** remains the locator's documented
  residual: a listing of fewer than six following entries is not set
  aside. It shaped the test fixtures in this slice and no live reading.
