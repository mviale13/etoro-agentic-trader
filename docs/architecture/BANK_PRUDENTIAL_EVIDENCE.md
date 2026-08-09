# Can the BANK contract's own demands be grounded?

**Status: measured, 2026-08-09. Conclusion D — the evidence is not
available under current acquisition boundaries. Nothing was acquired.**

The platform can now establish that an income statement speaks an
**interest-based** financial language, from a net interest subtotal the
filer prints ([`FINANCIAL_LANGUAGE_EVIDENCE.md`](FINANCIAL_LANGUAGE_EVIDENCE.md)).
That is not permission to select `FinancialModel.BANK`, which asserts
things an interest subtotal does not evidence:

```text
INTEREST_BASED  +  bank-prudential evidence established  →  BANK eligible
```

This slice asked whether the right-hand term can be grounded. It asked
two questions separately, and they came back with opposite answers.

| | Question | Answer |
|---|---|---|
| **Discrimination** | Do the demanded facts separate banks from institutions that merely print an interest subtotal? | **Yes, decisively.** CET1 and the LCR: 10 of 10 banks, 0 of 9 non-banks. |
| **Availability** | Can they be grounded reliably? | **No.** CET1 is reachable for 2 of 10 banks. The LCR is reachable for **none**. |

The evidence exists, is universal among banks, and is unreachable. That
combination is what makes this D rather than A.

---

## First architectural decision: where these facts belong

**Not in `StatementConcept`.** Measured across every filing in the
corpus: CET1, Tier 1 capital, the regulatory leverage ratio and the LCR
appear on the face of a primary statement **zero times**. Not once, in
any jurisdiction. The documents do not place them there, so forcing them
into the face-of-statement domain would be inventing a location.

They are printed in **capital-management and liquidity-risk sections of
the annual filing, and in the tables inside them** — the same document
this platform already fetches, in regions it does not locate.

So the answer is the fourth candidate: **a separate grounded
prudential-understanding layer, acquired from its own located region**,
on the pattern `statement_locator` already established for the primary
statements. It is not a new document class, and it is not the notes.

### Each fact, against the six questions asked

| Fact | Where it is printed | Kind | Groundable directly? | Period | Across jurisdictions | Absence interpretable? |
|---|---|---|---|---|---|---|
| **CET1 capital** | capital-management section tables | **amount** | only where that section is acquired — 2 of 10 | balance-sheet date | yes: US, UK, DE, JP all disclose | **no** |
| **CET1 ratio** | same table, beside the amount | **ratio** | same | balance-sheet date | yes, but qualified differently — US banks print standardized *and* advanced approaches, so there are two | **no** |
| **Tier 1 capital** | same table | **amount** | same | balance-sheet date | yes | **no** |
| **regulatory leverage ratio** | capital tables; US banks print a supplementary leverage ratio | **ratio** | 1 of 10 — and see the trap below | balance-sheet date | yes, under different names | **no** |
| **liquidity coverage ratio** | liquidity-risk section | **ratio** | **0 of 10** | **not the statement's period** — commonly an average over the final quarter, so it does not share the filing's reporting period and cannot be treated as a year-end figure | yes | **no** |
| **deposit funding quality** *(the contract's wording when this was measured; since corrected — see below)* | nowhere — no filer prints it | **analytical conclusion** | never | — | — | — |
| **customer deposits** *(the wording that replaced it)* | face of the balance sheet | **amount** | not yet — the label collides with an asset, see below | balance-sheet date | yes, under many labels | not yet |

**Question six deserves its own sentence, because it is a safety
result.** Absence cannot be safely interpreted for any of these facts
today, and not because the guard is weak — because this platform
acquires no region that would have carried them. A fact missing from
every region it does acquire is missing from places it never looked.
The standing rule the statement stream holds — *an absence is evidence
only where the section that would carry it was located and read* — is
exactly what forbids reading anything into these absences now.

---

## The corpus

19 companies. `ROW` = named by a table row this platform acquires, so a
reading could cite the cell and `figure_at` would check it. `beyond` =
stated in the filing, in no acquired region — from outside that region a
capital table and a risk factor mentioning capital requirements are
indistinguishable. `—` = not mentioned anywhere in the filing.

| Symbol | Group | CET1 | Tier 1 capital | leverage ratio | LCR | deposits |
|---|---|---|---|---|---|---|
| **JPM** | bank, INTEREST_BASED | beyond | beyond | beyond | beyond | ROW |
| **GS** | bank, INTEREST_BASED | beyond | beyond | beyond | beyond | ROW |
| **C** | bank, INTEREST_BASED | beyond | beyond | beyond | beyond | ROW |
| **COF** | bank, INTEREST_BASED | **ROW** | **ROW** | beyond | beyond | ROW |
| **RF** | bank, INTEREST_BASED | beyond | beyond | beyond | beyond | ROW |
| **DB** | bank, IFRS Germany | beyond | beyond | beyond | beyond | ROW |
| **BCS** | bank, IFRS UK | beyond | beyond | beyond | beyond | ROW |
| **NWG** | bank, IFRS UK | beyond | beyond | beyond | beyond | ROW |
| **AXP** | bank, INTEREST_BASED | **ROW** | **ROW** | **ROW** | beyond | ROW |
| **MUFG** | bank, IFRS Japan | beyond | beyond | beyond | beyond | ROW |
| **AGNC** | interest-based, **not deposit-funded** | — | — | beyond | — | beyond |
| **NLY** | interest-based, **not deposit-funded** | — | — | **ROW** ⚠ | — | beyond |
| **ARCC** | interest-based, **not deposit-funded** | — | — | — | — | — |
| **TRV** | insurer | — | — | — | — | beyond |
| **MET** | insurer | — | beyond | beyond | — | beyond |
| **CB** | insurer | — | — | beyond | — | ROW |
| **AAPL** | generic | — | — | — | — | beyond |
| **KO** | generic | — | — | — | — | beyond |
| **WMT** | generic | — | — | — | — | — |

### Discrimination: CET1 and the LCR are perfect

| Fact | Banks mentioning | Non-banks mentioning | Verdict |
|---|---|---|---|
| **CET1** | **10 / 10** | **0 / 9** | perfect |
| **liquidity coverage ratio** | **10 / 10** | **0 / 9** | perfect |
| Tier 1 capital | 10 / 10 | 1 / 9 — MetLife | one false positive |
| regulatory leverage ratio | 10 / 10 | 4 / 9 — AGNC, NLY, MET, CB | **unusable alone** |
| deposits | 10 / 10 | 6 / 9 — incl. Apple and Coca-Cola | **unusable alone** |

The three institutions in the middle band are what make this result
worth having. **AGNC, NLY and ARCC are interest-spread businesses** — a
mortgage REIT earns almost nothing but net interest, and would read
`INTEREST_BASED` the moment this platform reads its income statement.
None of them mentions CET1 or the LCR, because none is a
prudentially-regulated bank. That is precisely the separation the BANK
contract needs and that an interest subtotal cannot make.

### ⚠ The trap: "leverage ratio" is not one concept

**Annaly prints `GAAP leverage ratio` and `Economic leverage ratio` as
addressable table rows.** A future slice that acquired a
`leverage_ratio` concept by matching that phrase would ground a real,
checkable, correctly-read figure from a mortgage REIT — and it would not
be a regulatory leverage ratio, would not evidence prudential
supervision, and would be the platform's most confident wrong answer to
date. Insurers mention the phrase too.

If a leverage ratio is ever acquired it must be the *regulatory* one,
named as such by the section it was printed in. This is the strongest
argument in the measurement for locating the prudential region before
acquiring any concept from it: the region is what disambiguates the word.

---

## The wording correction — proposed here, applied 2026-08-09

`BANK` named its cash-generation demand **`deposit funding quality`**.
No filer prints that. It was three claims wearing one name, and only the
first is a fact:

```text
deposits exist                  — a row on a balance sheet
deposits fund most of the book  — arithmetic over two rows
deposit funding is strong       — an analyst's verdict
```

Demanding the third as *evidence* asked the analyst to be handed the
very answer the question would produce, so the gap could never have
closed on evidence however much this platform acquired.

**Applied** in a later contract-correction slice, which changed the
wording and nothing else. The demand now reads:

- **`customer deposits`** — a printed amount;
- **`their share of total liabilities`** — arithmetic this platform
  performs over two checked cells, exactly as every `FinancialMeasure`
  is derived;
- **`the liquidity coverage ratio`** — unchanged.

*Quality* remains what it always was: an analyst's judgment over those
facts, belonging to a rule table and not to the evidence layer. Nothing
was acquired to satisfy the new wording, no analyst changed, and which
questions `BANK` answers and declines is exactly as before.

**Deposits were not acquired either, and the corpus says why.** They are
on the face of the balance sheet, but the contract is materially harder
than net interest income's was:

- The same word names an asset and a liability on the same statement.
  JPMorgan prints `Deposits with banks` — its own money placed at other
  banks — and `Deposits`, its ~$2.4tn of funding.
- Capital One prints `Interest-bearing deposits and other short-term
  investments` (asset) and `Interest-bearing deposits` (liability).
- **MUFG prints the identical string, `Interest-earning deposits in
  other banks`, on both sides** of its balance sheet.
- Position cannot rescue it: JPMorgan's balance sheet carries **two**
  `Total assets` rows, so "after total assets" is not a side.
- The two largest banks qualify the line inline — `Deposits (includes
  $ 76,569 and $ 44,855 at fair value)` — which exact matching refuses
  and `without_footnote` will not strip.
- Chubb, an insurer, prints `Policyholder contract deposits` in an
  addressable row.

A deposit concept is earnable, but it needs its own corpus pass to
settle a contract that cannot confuse funding with an asset. Shipping
one on the strength of this pass would have been the confident wrong
answer this platform exists to avoid.

---

## Conclusion — D: unavailable under current acquisition boundaries

The facts the BANK contract demands are **universally disclosed by
banks, perfectly discriminating, and unreachable**. CET1 is addressable
for 2 of 10 banks and the LCR for none, and the two exceptions are
accidents of section layout rather than a route: Capital One and
American Express happen to print their capital tables inside the Item 7
region this platform already acquires, and the other eight do not.

Nothing was acquired. A concept reaching 2 of 10 filings fails the
domain's own test — *a stable meaning across the filings for which it is
claimed* — and one reaching none is not a concept at all.

### The exact additional acquisition required

Not another source, and not another document class. **The same filings,
with one more located region.**

A **prudential-disclosure region**, resolved the way the primary
statements are: discovery over the titles filers actually typeset,
scored by structural evidence, resolved as the most coherent run, closed
at the next peer. The corpus already names the titles it would have to
discover, and the difficulty:

| Filing | Block-beginning capital/liquidity headings | The real section, in the filer's words |
|---|---|---|
| GS | 9 | `Capital Management and Regulatory Capital` |
| C | 17 | `CAPITAL RESOURCES` |
| RF | 3 | `Regulatory Capital` |
| DB | 59 | `Capital Adequacy Requirements` |
| COF | 12 | `CAPITAL MANAGEMENT` |
| AXP | 3 | `Liquidity Risk Management Process` |
| BCS | 28 | `Liquidity risk management (audited)` |
| NWG | 20 | `Capital adequacy` |

Between 3 and 59 candidates per filing, most of them contents entries
and risk-factor mentions. This is the same shape of problem
`statement_locator` was built for, and the same rule applies: **a title
match is not a location.** It is a slice of its own, and it is the one
that unblocks everything else here.

Once that region exists, the order is fixed by what this measurement
found: locate the region, then acquire **CET1** and the **LCR** — the
two perfect discriminators — and never acquire a bare `leverage ratio`,
because outside its section that phrase belongs to mortgage REITs as
readily as to banks.

### What is still unearned, stated plainly

```text
NET_INTEREST_INCOME → interest-based statement language     ✅ earned
interest-based      → regulated deposit bank                ❌ not earned
regulated deposit bank → BANK financial model               ❌ not earned
```

`BANK` continues to be selected by `model_for` from the business
playbook, and that coupling remains the only route.

## Constraints observed

Nothing in `app/` changed. `PlaybookSelector`, every playbook route,
`model_for()`, `FinancialModel`, `FinancialLanguage` and the reading
guard are untouched; no model was added or removed; no regulatory
concept was acquired; no liquidity decline was added; no analytical
judgment became a fact; no company, ticker, industry or jurisdiction is
named in production. Expected corpus labels live in this document only.
