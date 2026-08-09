# Positive evidence of a financial language

**Status: measured, 2026-08-09. Conclusion A — the distinction is
earned. Acquired, and connected to nothing.**

The previous measurement
([`FINANCIAL_LANGUAGE_CORPUS.md`](FINANCIAL_LANGUAGE_CORPUS.md)) closed
with two facts that this slice takes as its premises:

1. **Statement shape identifies a financial-institution family, and
   cannot select `BANK`.** Eight banks and five insurers matched the
   JPMorgan triad — no gross profit, no operating income, an
   unclassified balance sheet — identically. So did a filing this
   platform failed to read.
2. **Bank-specific behaviour requires positive evidence of bank
   financial language, not merely the absence of generic industrial
   concepts.** `FinancialModel.BANK` declines two questions for want of
   regulatory capital and deposit-funding evidence, and no absence
   establishes either.

The route those two facts imply, and the one this slice serves:

```text
Canonical statements → Financial understanding
                     → Positive financial-language evidence → Financial model
```

Never:

```text
Missing generic concepts → BANK
```

This slice acquires the third box. It does not build the fourth arrow.

---

## The distinction, in one sentence

A bank strikes a subtotal for interest, because it earns by lending at
more than it pays. An insurer earns a premium, and prints no interest
subtotal at all. Both are lines on the face of the income statement.

## What was acquired, and what was refused

Six candidate concepts were named for investigation. **Two were
acquired.** The other four were measured against the corpus and
rejected, each for a stated reason.

| Candidate | Verdict | Why |
|---|---|---|
| **net interest income** | **acquired** | Printed by 12 of 12 banks whose income statement this platform reads, in four jurisdictions and under both US GAAP and IFRS. Printed by no insurer and no control. One label form. |
| **premium revenue** | **acquired** | Printed by 4 of 5 insurers, by no bank and no control. Two label forms, both meaning earned premium revenue under US GAAP. |
| interest income | rejected | Coca-Cola, Tesla, Walmart and Procter & Gamble all print it. It separates nothing. It is a component, not the subtotal that says how a filer accounts for itself. |
| interest expense | rejected | The same, and worse — Disney, Union Pacific and every insurer in the corpus print it too. |
| claims / policyholder benefits | rejected | Not a row. Five insurers print five different labels: `Claims and claim adjustment expenses`, `Property and casualty insurance claims and claims expense`, `Policyholder benefits and claims`, `Losses and loss adjustment expenses incurred`, and Chubb splits it across `Losses and loss expenses` and `Policy benefits`. And Citigroup prints `Total provisions for credit losses and for benefits and claims` — the bank a loose insurance rule would have caught. |
| insurance reserves / policyholder liabilities | rejected | Not a row, and not one concept. A property-and-casualty insurer prints `Unearned premiums` and `Unpaid losses and loss expenses`; a life insurer prints `Future policy benefits` and `Policyholder account balances`. Accepting both under one concept would flatten two materially different accounting concepts because they are economically similar. |

Answering the seventh question asked of each candidate — *amount,
structural feature, or family of rows*: the two acquired concepts are
**amounts**, each grounded to one cell like every other figure this
platform holds. The four rejected ones are **families**, which is
precisely why they were rejected: a family has no row to ground.

## The grounding contract

Equality after `normalised`, never containment — the rule every
`StatementConcept` is held to. What each concept accepts, and what sits
next to it on the same real statements and is refused:

| Concept | Accepted | Refused, and printed by |
|---|---|---|
| `net_interest_income` | `net interest income` | `Net interest income after provision for credit losses` — a different quantity, struck after an expense, printed **directly beneath** the line it is not by COF, TFC, FITB, MTB, RF, DB and MUFG. Also `Interest income`, `Interest expense`, `Total interest income`, `Net interest margin`. |
| `premium_revenue` | `premiums`, `net premiums earned` | `Net premiums written` and `Increase in unearned premiums` — Chubb prints all three, and only the last is revenue. `Preferred stock redemption premium` — a different sense of the word, printed further down the same statement by MetLife and AIG. `Insurance premiums, including deposit insurance` — MUFG's bancassurance line, which is not a clean premium revenue row. |

Both concepts are claimed for the filings measured. `premium_revenue`
is claimed for **US GAAP only**: the corpus holds no IFRS insurer, and
an IFRS 17 filer prints `Insurance revenue`, which is a
differently-defined quantity. It is deliberately not listed.

---

## The corpus

Every row is a live 5-of-5 statement quorum, derived by
`statement_consensus_of` over stored observations and read back from
`data/statements/`. **Expected** is an evaluation label; it exists in
this document and in no production module.

<!-- generated from the store; see the slice that added this file -->

| Symbol | Expected | Quorum | `net_interest_income` | `premium_revenue` | Established language |
|---|---|---|---|---|---|
| **AXP** | bank | 5/5 | `Net interest income` = 17,364 **5/5** | — | **interest based** |
| **BCS** | bank — IFRS, UK | 5/5 | `Net interest income` = 14,501 **5/5** | — | **interest based** |
| **C** | bank | 5/5 | `Net interest income` = 59,792 **5/5** | — | **interest based** |
| **COF** | bank | 5/5 | `Net interest income` = 42,878 **5/5** | — | **interest based** |
| **DB** | bank — IFRS, Germany | 5/5 | `Net interest income` = 15,673 **5/5** | — | **interest based** |
| **FITB** | bank | 5/5 | `Net Interest Income` = 5,982 **5/5** | — | **interest based** |
| **GS** | bank | 5/5 | `Net interest income` = 13,559 **5/5** | — | **interest based** |
| **JPM** | bank | 5/5 | `Net interest income` = 95,443 **5/5** | — | **interest based** |
| **MTB** | bank | 5/5 | `Net interest income` = 6,948 **5/5** | — | **interest based** |
| **MUFG** | bank — IFRS, Japan | 5/5 | `Net interest income` = 3,684,254 **5/5** | — | **interest based** |
| **NWG** | bank — IFRS, UK | 5/5 | `Net interest income` = 12,829 **5/5** | — | **interest based** |
| **RF** | bank | 5/5 | `Net interest income` = 4,991 **5/5** | — | **interest based** |
| **ALL** | insurer | 5/5 | — | — | **neither established** |
| **CB** | insurer | 5/5 | — | `Net premiums earned` = 53,014 **5/5** | **insurance based** |
| **MET** | insurer | 5/5 | — | `Premiums` = 49,779 **5/5** | **insurance based** |
| **TRV** | insurer | 5/5 | — | `Premiums` = 43,914 **5/5** | **insurance based** |
| **AAPL** | generic | 5/5 | — | — | **neither established** |
| **DIS** | generic | 5/5 | — | — | **neither established** |
| **HON** | generic | 5/5 | — | — | **neither established** |
| **KO** | generic | 5/5 | — | — | **neither established** |
| **PG** | generic | 5/5 | — | — | **neither established** |
| **TSLA** | generic | 5/5 | — | — | **neither established** |
| **UNP** | generic | 5/5 | — | — | **neither established** |
| **WMT** | generic | 5/5 | — | — | **neither established** |

**Evidence quality: every claim in the table settled 5 of 5.** Not one
concept was unsettled, in any company, in either direction. The reader
does not wobble on statement rows the way it wobbles on prose — the
noise floor that made the consensus architecture necessary
(`reader_stability`) is not present here.

### Errors

| | Count | Which |
|---|---|---|
| **False positives, interest based** | **0** | no insurer, no control |
| **False positives, insurance based** | **0** | no bank, no control |
| **False negatives, interest based** | **0** | every measurable bank established it |
| **False negatives, insurance based** | **1** | **ALL** — Allstate splits premiums into `Property and casualty insurance premiums` and `Accident and health insurance premiums and contract charges` and prints no total, so no row can be grounded. It reads *neither established*, which is honest and is not an insurer classified as something else. |
| **Ambiguous** | **0** | no company established both markers |
| **Unevaluable** | **2** | **TFC**, **AIG** — blocked below |

## The mixed case

The corpus contains no company that establishes both markers, so
`BOTH` is **unexercised**. It exists anyway, because the derivation must
be total: Santander, BNP Paribas and MUFG are bancassurers, and MUFG
does print `Insurance premiums, including deposit insurance` beside its
net interest income. A function unable to say *both* would have to pick
one and would be silently wrong the first time it met such a filer.

This is the corpus's clearest remaining gap. It is named rather than
guessed at.

## Reading validity — the guard held, and earned its keep

Concept absence counts as evidence only where the statement was located
**and read**, shown by some concept of that statement being established
(`_was_read`). The guard was carried over from the shape measurement and
was load-bearing twice in this slice:

- **Santander.** Adding the IFRS income-statement title located a
  section for Santander — the *wrong* one, the statement of recognised
  income and expense. It establishes no concept at all, so it claims
  nothing and reads `NOT_ESTABLISHED`. That is what made the title
  change safe to take: coverage improved for Barclays and NatWest
  without any boundary rule being relaxed, and the one mislocation is
  inert.
- **MUFG.** The regression case is intact and its lesson sharpened.
  MUFG's *balance sheet* rows still read only `Total` and establish
  nothing. Its *income statement* turned out to be readable all along —
  once the platform knew to look for the line a bank actually prints.
  A statement that establishes nothing is not evidence that the company
  prints nothing; it may only mean nobody asked it the right question.

## Acquisition failures fixed

Four, each blocking named corpus cases, each with a positive and a
rejection fixture in `tests/test_statement_language.py`.

| Fix | Unblocked | Rejection fixture |
|---|---|---|
| **A filer may name its own equity.** `names_its_own_equity` accepts *Total ⟨words⟩ ⟨holders⟩ equity* where the words between are none of a declared forbidden set. Replaces a `CONCEPT_LABELS` entry that had hard-coded **one company's wording by name**. | ALL, MET, CB, DIS, WMT balance sheets — all now 5/5 on `Total Allstate shareholders' equity` = 30,610, `Total MetLife, Inc.'s stockholders' equity` = 28,398, `Total Chubb shareholders' equity` = 73,757, `Total Disney Shareholders' equity` = 109,869, `Total Walmart shareholders' equity` = 99,617 | Refuses every grand total in all 44 corpus filings, including `Total liabilities, mezzanine equity and equity` (MET), `Total liabilities, redeemable noncontrolling interest, and shareholders' equity` (WMT) and `Total equity excluding non-controlling interests` (BCS). Accepts 9 rows across the corpus; all 9 are the parent's equity. |
| **The IFRS income-statement title.** `Consolidated income statement(s)` — the IFRS word order, not a stylistic variant. | BCS, NWG | Measured against JPM, GS, AAPL and TRV before adding: not one of their statements moved. |
| **A spanning title containing a digit is a title.** `read_number` is lenient by design and read 31 out of `Year Ended December 31`, so that row became the header, the real header row was read as data, and every figure in four statements was refused as sitting under an unnamed column. `prints_only_a_number` tests for a letter. | COF, CB income statements | A row whose single distinct cell is a bare number is still the header; an empty row is still no header. |
| **The reading is told which labels are accepted.** Withholding them made it guess, and one guess discards the whole observation rather than the one concept — `_validated` is unchanged and still discards. | ALL, C, AXP, DB, KO, WMT, UNP, BCS, NWG | Grants nothing: every cited cell is still read back out of the document, its label still checked, its address still required to be distinct. It can only turn a guess into an omission. |

### Still blocked, and not fixed

**TFC and AIG** fail on a defect outside the four authorised classes:
their statements' **columns are misaligned with their headers**. AIG
prints its 2025 figure at column 4 while the 2025 header sits at column
5. That is a table-parsing defect, not a title or label one, and fixing
it means touching the column model that every figure in the platform
rests on. It is named here rather than attempted.

---

## The representation

The smallest that carries the evidence, in
`app/domain/statement_language.py`:

```text
FinancialStatementConsensus (income statement)
        ↓  language_of — pure, deterministic, no model asked
EstablishedLanguage
    language:       INTEREST_BASED | INSURANCE_BASED | BOTH
                    | NEITHER | NOT_ESTABLISHED
    markers:        both concepts, established or absent with a reason
    statement_read: the guard, carried so no consumer can forget it
    support:        the narrowest agreement beneath the markers
```

It is carried on `FinancialUnderstanding.language` and rendered by
`movrvest financials`, which prints beside it that the language does not
select the model below it.

**One asymmetry a consumer must respect.** `INTEREST_BASED` and
`INSURANCE_BASED` are positive about the marker they name and merely
silent about the other. Allstate proves a premium line can be missed, so
a company reading `INTEREST_BASED` is *established* to strike an
interest subtotal and only *not shown* to earn premiums. Nothing may
read the second half as strongly as the first.

## Connected to nothing

- `PlaybookSelector` — unchanged.
- Every business playbook route — unchanged.
- `model_for()` — unchanged. The financial model is still derived from
  the business playbook.
- `FinancialModel` — no member added or removed. No `INSURER` model.
- No BANK liquidity decline. No regulatory concept acquired: CET1,
  Tier 1, the leverage ratio, LCR and NSFR remain `BANK` acquisition
  demands and are not needed to identify a statement language.
- No company, ticker, industry or jurisdiction is named anywhere in
  production. This slice **removed** the one name that was there.
- Expected corpus labels live in this document and in the tests, never
  in extraction or classification.

### What earning the fourth arrow would still take

Selecting `BANK` from `INTEREST_BASED` is not one step away, and this
document does not propose it. `BANK` declines leverage and cash
generation for want of regulatory capital and deposit-funding evidence.
An interest subtotal establishes that a filer accounts for itself around
interest; it does not establish that it takes deposits, and the two
declines are about deposits. Either those declines are re-derived from
what an interest-based language actually evidences, or the regulatory
facts are acquired. That choice is the next design question, and it is
the owner's.
