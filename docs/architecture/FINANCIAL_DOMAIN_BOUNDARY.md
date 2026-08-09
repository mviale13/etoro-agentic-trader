# The boundary of the Financial Statement Domain

**Status: accepted, 2026-08-09. The owner's ruling, on three
measurements. This is platform law, not a finding.**

Three slices asked, in different ways, whether a company's own financial
statements can tell this platform which financial model should read it.
The answer has a boundary, and the boundary is now named:

> **Financial statements establish financial *language*. They do not
> establish prudential regulatory *status*.**

Everything below follows from that one sentence.

## The four rulings

**1. Financial statements establish financial language.** Three values,
each earned against a corpus: `generic`, `interest-based`,
`insurance-based`. A net interest subtotal is positive evidence of the
second; a premium revenue line is positive evidence of the third
([`FINANCIAL_LANGUAGE_EVIDENCE.md`](FINANCIAL_LANGUAGE_EVIDENCE.md) —
24 companies, every claim 5 of 5, no false positive in either direction).

**2. They do not establish prudential regulatory status.** Measured, not
assumed. Across every filing in the corpus, in four jurisdictions and
under both accounting standards, CET1, Tier 1 capital, a regulatory
leverage ratio and the liquidity coverage ratio appear on the face of a
primary statement **zero times**
([`BANK_PRUDENTIAL_EVIDENCE.md`](BANK_PRUDENTIAL_EVIDENCE.md)).

**3. Prudential concepts belong to a separate evidence domain**, sourced
from the dedicated regulatory sections of the same filings —
capital-management and liquidity-risk sections, and the tables inside
them. They are not `StatementConcept`s and must never be added as such,
however convenient the reuse would be. The layer that will hold them has
a name: **Prudential Understanding**.

**4. `FinancialModel.BANK` cannot be selected from financial-statement
evidence alone**, and therefore remains derived from business
understanding by `model_for` until a Prudential Understanding layer
exists.

## Why the boundary falls exactly here

Because `BANK` is not a description of a statement. It is a question
contract that declines two questions, and it declines them for reasons
about **deposit funding** and **regulatory capital** — neither of which
any statement line evidences. A model selected from statements alone
would assert those reasons on evidence that never mentioned them, and
would tell an investor that a company's leverage awaits a Common Equity
Tier 1 ratio it does not have.

Two measurements pin the boundary from either side:

- **From below.** Statement *shape* — no gross profit, no operating
  income, an unclassified balance sheet — identifies a
  financial-institution family and stops. Eight banks and five insurers
  match it identically, and so does a filing this platform failed to
  read ([`FINANCIAL_LANGUAGE_CORPUS.md`](FINANCIAL_LANGUAGE_CORPUS.md)).
- **From above.** Statement *language* is not enough either. AGNC,
  Annaly and Ares are interest-spread lenders that read
  `interest-based` and are not prudentially-regulated banks. What
  separates them from banks — CET1, the LCR — is disclosed by 10 of 10
  banks and 0 of 9 non-banks, and is printed nowhere this platform
  currently locates.

So the gap between *interest-based* and *BANK* is not a missing rule. It
is a missing **domain**.

## The route, with the boundary marked

```text
Canonical financial statements
        ↓
Financial Understanding  ──→  financial language
        │                     generic | interest-based | insurance-based
        │
════════╪═══════════════ the boundary ═══════════════════════════
        │
Prudential Understanding ──→  prudential status        ← does not exist
        │                     (CET1, LCR, from a located
        │                      regulatory section)
        ↓
        FinancialModel
```

Above the line, evidence is a cell in a primary statement. Below it,
evidence is a cell in a regulatory disclosure. They are different
acquisitions, and a concept may not cross.

## What this forbids

- Adding CET1, Tier 1 capital, a leverage ratio, the LCR or the NSFR to
  `StatementConcept`.
- Connecting `StatementLanguage` to `FinancialModel` in any form,
  including as one term of a larger rule.
- Reading `interest-based` as *bank*, or as *deposit-funded*, or as
  *regulated*.
- Treating the absence of a prudential fact as evidence: this platform
  locates no region that would carry one, so every such absence is a
  fact about the platform.
- Selecting `BANK` for JPMorgan, or any company, from statement
  evidence.

## What it leaves standing

`model_for` derives the financial model from the business playbook,
unchanged, and continues to say that it is a coupling rather than a
conclusion. That coupling is now understood to be **correct for the
present state of the evidence** rather than merely unreplaced: no
statement fact can replace it, and the layer that could does not exist.

## What would move it

One acquisition, named by the measurement that closed:
a **located prudential-disclosure region**, resolved the way the primary
statements are — discovery over the titles filers typeset, scored by
structural evidence, resolved as the most coherent run. Between 3 and 59
capital and liquidity headings begin a block in each of these documents,
so a title match is not a location, and the region is also what
disambiguates the vocabulary: outside its own section, "leverage ratio"
belongs to a mortgage REIT as readily as to a bank.

Once that region exists, `Prudential Understanding` acquires **CET1** and
the **liquidity coverage ratio** — the two facts measured to discriminate
perfectly — and the fourth ruling above is the one that may then be
revisited. Not before.
