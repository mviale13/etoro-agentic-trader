# Financial Statement Acquisition

Status: **Executing the accepted sequence** (2026-08-08). The demand
and the road were fixed when the assessment design was accepted:
[`INVESTMENT_ASSESSMENT.md`](INVESTMENT_ASSESSMENT.md) records that
`JPM.entry.0001` reached `MONITOR` for want of exactly these facts,
and that the primary statements enter the knowledge layer through the
proven tabular chain, as their own knowledge slice with its own
measurements, before any warranting kind is built. This document
designs that slice; the PR that carries it is its review.

---

## Why this document exists

The first live decision measured the gap. Everything the platform has
established about JPMorgan is *structural* — which segments exist,
their sizes, their ways of earning, the archetype they add up to —
and no deterministic rule over structure alone can say whether owning
the business is attractive. The assessment design closed every
shortcut: provider fundamentals are secondary restatements of a
readable primary source and are inadmissible in any assessment's
basis, so a warranting kind's load-bearing claims must be
filing-grade, and filing-grade financial facts do not yet exist.

This slice makes the first of them exist. The consolidated income
statement — the audited statement the filer printed, located where
the filer typeset its title, read cell by cell through the exact
chain that took segment sizes to 10/10.

**Business Quality waits.** Deliberately, per the fixed sequence: the
kind is designed only once the facts it would rest on are established
and measured. Nothing in this slice defines a kind, a course, or a
rule table.

---

## The governing principle

> **A financial fact is a figure the filer printed, at an address
> this platform checked, under words the filer chose. What could not
> be located is absent, with its reason worded — never estimated,
> never restated from a provider.**

Every design decision below is tested against that sentence.

---

## Concepts kept apart

### A statement fact and a metric

This slice acquires what the filer printed. It derives nothing: no
margin, no growth, no ratio, no per-share arithmetic. A derived
quantity enters the platform the way the segment share did — as
arithmetic this platform performs over two checked figures, defined
when a consumer's rule table demands it and not before. Acquiring
metrics ahead of the kind that needs them would be taxonomy-first,
and the door stays shut.

### The statement stream and the segment stream

A statement observation is its own stream, never pooled with the
segment observations. The rule is the one that forced schema 10: a
consensus over readings that were shown different text would be
measuring two different strings and calling the difference
instability. The segment corpus is untouched — no re-read, no
supersession, no new spend on what is already established. The new
store starts its own schema counter at 1.

### The anchor and the row

The reading locates **one cell** per concept: the figure for the most
recent period, asserted with its value and checked back against the
document — the mix reading's discipline, unchanged. The platform then
reads **the rest of the row itself**: every cell on the anchored row
that prints a number under a named column becomes a figure, read
deterministically off the parsed table. The model locates; the
platform reads. Prior periods arrive as evidence without a single
additional model claim.

### The period stated and the period inferred

No period is ever inferred. Each figure carries its column header
verbatim — the filer's own words for what the column is — and the
document's reporting period travels on the source. Which column is
"most recent" is asserted only by the anchor's position and is
checkable by any reader against the headers stored beside it. A
column whose header the platform cannot read yields no figure.

### Scale kept, never normalized

The caption travels verbatim ("in millions, except per share data")
and the printed cell travels verbatim. Nothing rescales. A future
consumer that needs two figures on one scale gets them the way
`MeasuredShare` does — from one table — or states that it cannot.

---

## The object

`FinancialStatementObservation` — one reading of one statement of one
immutable document.

**The statement.** A closed vocabulary, `StatementKind`, holding
exactly `income_statement` today. The balance sheet and the cash flow
statement enter one at a time, when a consumer's demand is measured —
the same way every vocabulary on this platform has grown. The
mechanism below is already general; the vocabulary is deliberately
not.

**The concepts.** A closed vocabulary, `StatementConcept`, holding
`total_revenue` and `net_income`. A concept is a contract:

- the one figure it asks for, worded as a question about the
  statement;
- the row labels this platform accepts as answering it — declared in
  code, matched after `normalised`, and grown only by a live refusal
  naming the label a real filer used. The reading cannot relabel a
  row: a located cell whose row label matches no declared form is
  refused, with the filer's label in the refusal.

**The facts.** One per concept, always present, each either:

- **located** — the checked anchor figure plus the platform-read row,
  every figure carrying its label, header, printed text, value, cell
  address and caption; or
- **absent** — with the reason worded: the reading located no cell,
  the located cell was refused (and why), or no statement section was
  located at all. Three different facts, only some about the company,
  worded apart per the platform's absence discipline.

**The source and the reading.** The same `PrimarySource` identity and
`Provenance` every observation carries.

---

## Locating the statement

The third application of the structural-section rule: **a statement
is located where the filer typeset its title.** The openings are the
titles filers give the audited income statement ("Consolidated
statements of income", "… of operations", "… of earnings"); the
closings are the titles of the statements that follow it and the
notes heading. Among occurrences, only those that begin a block are
candidates — a table-of-contents entry and a cross-reference in a
note are not sections — and the widest block-beginning pair wins,
exactly as Items 1 and 7 are located today.

The tables inside that span are parsed by the same
`read_tables` the discussion uses, inheriting the three earned parse
rules unchanged: colspan words cover their columns, a page-split
table is merged where the filer's own repeated label column proves
continuity, and headers gate the merge.

A filing in which no statement title begins a block yields a
deterministic observation with every concept absent for the worded
reason — no model call, no spend, and the absence distinguishes "this
platform located no statement" from "the statement holds no such
row".

---

## The reading

One request, in the mix reading's shape: the parsed tables, every
cell addressed; the concepts to locate; cells and values, never
computations. The platform then enforces, in order:

1. **Existence and agreement** — `figure_at`: the cited cell exists,
   prints a number, and prints the number the reading asserted. A
   header row, a label column, an unlabeled row or an unheaded column
   is refused as measuring nothing.
2. **Correspondence** — the row's label, read off the document, must
   match a form the concept declares. "Total noninterest expense"
   cannot become revenue because a reading pointed at it.
3. **Distinctness** — two concepts cannot cite one cell.
4. **The row expansion** — performed by the platform, after the
   anchor survives.

A reading that fails any check is discarded whole and asked again,
up to the same bounded attempts the segment extraction uses; the last
refusal's wording survives. A concept the reading *omits* is a
different outcome — a claim that no cell holds it — stored as a
worded absence for the consensus to adjudicate.

---

## Consensus

`FinancialStatementConsensus`, derived on read, never stored — the
same architecture, the same `Agreement` machinery, the same quorum of
5, the same content-blind strict majority per claim over the
observations that addressed it. The comparable answer for a located
fact is the anchor — printed value at cell address — so two readings
that found the same figure in the same cell agree, and a settled fact
is verbatim one observation's, evidence and all. A settled absence
carries its modal reason with the count. Ties and pluralities settle
nothing and serve their distribution.

The decision path, when a warranting kind eventually consumes these
facts, consumes the consensus only. An observation reaches an
assessment through `consensus_of` or not at all — the knowledge
platform's standing rule, inherited whole.

---

## Surfaces

- `movrvest statements SYMBOL` — the consensus over stored statement
  observations of the current filing: every concept with its width,
  cell, printed figure and caption, absences with reasons. Developer
  inspection, exactly as `movrvest knowledge` is.
- `movrvest observe-statements SYMBOL [--to N]` — the explicit,
  counted spend that fills the statement quorum. Stops on the count,
  never the content.

---

## What this model forecloses

- A derived metric acquired ahead of the consumer that demands it.
- A provider's restatement entering this store under any label.
- A share, growth rate or margin computed by the model — the model
  locates cells; arithmetic is this platform's, later, on demand.
- Pooling statement readings with segment readings, or entries shown
  different statement text with each other.
- A period inferred from a publication date or a column position.
- A rescaled or normalized figure — the printed cell and its caption
  are the fact.
- Reading until the statement classifies — the stopping rule is a
  count fixed before anything is read.
- Any assessment, kind, course or rule defined in this slice.

---

## The measurement

On JPM, the reference corpus's complete-chain company, whose Item 8
carries the audited statements in the same document its segment
evidence came from:

1. `movrvest observe-statements JPM` to the quorum of 5.
2. Report the consensus: which concepts settled, at what width, at
   which cells — and every absence with its reason.
3. The expectation, stated before the spend: anchors are cells, and
   cells measured 10/10 stable on segment sizes; prose does not enter
   this reading anywhere. An unsettled anchor at quorum is therefore
   a finding about the statement's shape, not noise to be re-read.

The segment corpus is not re-read, and no other company is observed
in this slice — breadth is Operation First Reading's economy, and
statement coverage follows the same three streams once the mechanism
is proven on one company.
