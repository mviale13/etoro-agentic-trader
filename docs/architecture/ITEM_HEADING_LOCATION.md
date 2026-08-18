# The other numbering a regulator uses

**Status: built. Repair 1 of the two the owner ordered. No model call, no
acquisition, no production data mutation, and no band, statement,
consensus, decision or annual-report section moved.**

PR #190 measured that **42 of 231 Item 5.02 filings (18%) were
unreadable**, one cause in three variants: the filer typesets a
non-breaking space, a thin space or a markup-split word inside the
heading. The owner's instruction was to reuse `section_locator.py`,
which already solves exactly that and says so in its own docstring.

Reusing it turned out to need one thing first.

> **`section_locator` could not express `Item 5.02` at all.** Its
> candidate pattern is `\bitem\s+(\d{1,2})\s*([a-c])?\s*[.:—-]?` — which
> reads an annual report's `1`, `1A`, `7A` and reads `Item 5.02` as
> **`Item 5` with the fraction eaten by the trailing-punctuation group**.
> The typography was never the only problem: a section keyed on 5.02
> could not be asked for.
>
> **With the fraction expressible, `locate()` finds 241 of 244 — against
> 201 for the literal rule. 40 recovered, 0 lost.**
>
> **And the annual-report path cannot move, because it does not use this
> module.** `edgar_filings` locates its sections with its own literal
> rule and imports `section_locator` nowhere; `statement_locator`, the
> one live consumer, imports `Evidence` and `observe` and none of the
> changed names. Both are pinned by tests.

---

## 1. The change

Two lines of contract, and nothing else.

```python
#: before
_CANDIDATE = re.compile(r"(?i)\bitem\s+(\d{1,2})\s*([a-c])?\s*[.:—-]?")

#: after
_CANDIDATE = re.compile(
    r"(?i)\bitem\s+(\d{1,2})(?:\.(\d{2})(?!\d))?\s*([a-c])?\s*[.:—-]?"
)
```

`Item` gains a `fraction`, **last in the field order** — `Item(1, "A")`
meant a suffix before this existed and still does. Inserting a field
ahead of an existing one would silently change every positional call and
no type checker would see it, because both are `str`. The three existing
locator tests construct `Item(1, "A")` positionally; putting the field
first broke all three, which is how the hazard was found rather than
argued.

`order` becomes `(number, fraction, suffix)`. The fraction is compared as
the two printed digits rather than as a number — the same ordering,
`"01" < "02" < "10"`, without inventing a value for an item that has
none. A bare `Item 5` sorts before `5.02`, which is what a filer's own
sequence does.

### Why the dotted group is bound as tightly as it is

This pattern governs the annual-report path's discovery too, so the dot
must **touch** the number, **exactly two** digits must follow, and a
third must not. Each clause is a live hazard, and each is pinned:

| printed | reads as | why it matters |
|---|---|---|
| `Item 1. 10 years ago…` | `Item 1` | a loose group would make the fraction `10` |
| `Item 5. 02 is not a fraction` | `Item 5` | the dot must touch the number |
| `Item 5.021` | `Item 5` | `(?!\d)` |
| `Item 1A.` | `Item 1A` | the suffix group is untouched |

## 2. Proof the annual-report path cannot move

Two independent proofs, because "it should be fine" is not one.

### Structural

`edgar_filings.py` contains the string `section_locator` **zero times**.
It pairs literal openings with literal closings and takes the widest
pair — its own rule, unchanged by this.

`statement_locator.py` imports exactly
`from app.providers.section_locator import Evidence, observe` — the
structural *scoring*, which this change does not touch — and none of
`discover`, `Item`, `candidates`, `sequence` or `locate`. So no
statement, no consensus and no band is reachable from here.

Both are asserted over the modules' own source.

### Empirical

`discover()` run over all 24 annual reports this platform holds, before
and after, comparing every occurrence as `(number, suffix, position,
printed)`:

| | |
|---|---|
| **identical** | **22 of 24** |
| differing | 2 — HON and MET |

The two differences are exactly the intended behaviour and nothing else:

```text
HON  at 524,353   'Item 5.'   →  'Item 5.02 '
MET  at 1,454,077 'Item\xa05.' →  'Item\xa05.05 '
```

Both are cross-references to *current-report* items printed inside a
10-K, which is precisely the numbering that was previously being read
wrong. And because `_section` never consults this module, neither
changes what is read: `movrvest statement-shape` for HON and MET is
**byte-identical** before and after.

HON is a pinned control (MEDIUM 62, 3/3) and MET is a pinned control
(LOW 40, 3/3). Neither moved.

## 3. What the change buys, measured

`locate()` asked for `Item 5.02` over the same 244-filing corpus PR #190
measured, against the committed literal opening on the same documents:

| | filings |
|---|---|
| literal `item 5.02` present in the flattened text | **201** |
| `section_locator.locate()` found the section | **241** |
| **recovered** — the literal rule was blind | **40** |
| **lost** — the literal rule saw it and the locator did not | **0** |

Located section width: min 362, median 1,832, max 18,207 characters.

**Three filings of 244 are still not located**, and they are reported
rather than rounded away. They are a residual for the extraction
measurement to name, not a reason to widen a pattern until the number
reaches 244.

## 4. What was measured and deliberately NOT taken

The owner's phrase was *"reuse `section_locator.py`"*, and the largest
available reading of that is to rewire `edgar_filings._section` — the
annual-report path — to resolve through the locator as well. That
reading was measured and refused.

**It is not a small repair. It changes 26 of 48 section reads and loses
one.**

| | business section | discussion section |
|---|---|---|
| **recovered** (empty → read) | **3** — AXP, DB, RF | 0 |
| **lost** (read → empty) | **1 — HON** | 0 |
| width moved | 14 | 12 |
| unchanged | 6 | 12 |

Some of the movement is obviously right — **AXP's business description
is empty today and its filer printed 86,613 characters of one**, and
PG's 18-character and WMT's 17-character "business sections" are
table-of-contents entries that become 16,623 and 37,500. Some is not
obviously anything: JPMorgan's falls 66%, Chubb's 47%, MetLife's 41%,
Fifth Third's 42%, and Goldman's discussion rises from 1,202 characters
to 311,737.

**Nobody can say which of those 26 are correct without a labelled
corpus**, and building that corpus is the measurement step the owner has
already placed after these two repairs. Adopting the rewire now would be
choosing 26 unverified readings to gain 3 verified ones, and losing
Honeywell's business description in the process.

Recorded here so the next slice starts from the number rather than
rediscovering it. **AXP's empty business description is a live,
separately actionable defect** and is not fixed by this slice.

## 5. Consumed by nothing yet

The fraction is a thing this locator can express and nothing asks it
for. A test walks every module under `app/` and asserts that
`section_locator.py` is the only one that mentions it.

Its consumer is the transition-extraction measurement the owner ordered
next, which cannot read an Item 5.02 section without it. That is the
product story: **18% of a document class this platform already fetches
is currently unreadable, and the measurement that decides whether
Management Continuity is ever built cannot run over a corpus with a hole
that size in it.**

## 6. Scope compliance

Repair 1 of 2, independent of the issuer-identity guard · no Management
Continuity work · no `LeadershipEvent`, CLI, event contract or continuity
state · no model call · no acquisition · no production data mutation
(`git status --porcelain data/` empty) · no band, factor, threshold,
recipe, vocabulary, schema, playbook, financial-model or decision change
· the annual-report rewire measured and **not** taken.

Gates: **3,092 tests pass** (3,078 + 14 new), `ruff check` and
`ruff format --check` clean, `mypy app` clean over 598 files, and the
commit verified in isolation from `git archive HEAD`.
