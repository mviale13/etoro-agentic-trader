# One Item 5.02 is not one event

**Status: research. Read-only over SEC EDGAR, no model call, no
production implementation, no score, band, committee, Business Quality
or decision change. Stopped for owner ruling.**

The question was whether regulator-filed leadership-event sequences
support a generic, event-triggered Management Continuity assessment.
They do not yet, and the blocker is one structural fact measured across
244 filings rather than a shortage of evidence.

> **The unit of an Item 5.02 filing is a *document*, not a *transition*.
> Of the 132 segments a candidate classifier read as a covered-officer
> event, 85 — 64% — name two or more people**, and there is no
> per-person, per-role segmentation anywhere in the platform. Every
> verdict such a classifier produces is a statement about a filing that
> happens to mention a CEO, not about what happened to the CEO.
>
> **Adobe proves it in the clearest language the corpus contains.** On
> 9 March 2026 Adobe filed: *"Shantanu Narayen notified Adobe of his
> decision to transition from his role as Adobe's Chief Executive
> Officer. Adobe is conducting a search for Mr. Narayen's successor. Mr.
> Narayen will remain as Adobe's Chief Executive Officer until his
> successor is appointed."* The candidate rule classified it
> **`appointment`** — backwards — because *"until his successor is
> appointed"* contains an appointment verb inside a future conditional
> clause about the thing that has **not** happened.
>
> **Eleven CEO transitions were hand-checked against known facts; five
> were classified wrongly.** Not one of the five open→close links the
> corpus produced was correct, and the two real transitions with a
> genuine vacancy — Boeing and Intel — were not detected as openings at
> all.
>
> **One free repair is real and separable.** 42 of 231 filings (18%)
> were unreadable because the filer typesets a **non-breaking space**
> (28), a **thin space** (11) or a markup-split word (3) inside
> `Item 5.02`. Normalising the heading took location from **183/231 to
> 244/244**. `app/providers/section_locator.py` already solves exactly
> this and is wired only into `statement_locator`.

---

## 1. The corpus

| | |
|---|---|
| source | SEC EDGAR submissions index + the filed 8-K document |
| filter | `form == "8-K"` **and** the regulator's own `items` field contains `5.02` |
| window | filings dated 2022-01-01 onward |
| companies | **16** |
| industries | **16**, one each |
| Item 5.02 filings | **244** |
| model calls | **0** |

Software (ADBE) · restaurants (SBUX) · aerospace (BA) · apparel (NKE) ·
semiconductors (INTC) · healthcare (CVS) · consumer fitness (PTON) ·
consumer products (EL) · airlines (LUV) · automotive (F) · department
stores (KSS) · banking (JPM) · energy (CVX) · pharmaceuticals (PFE) ·
railroads (UNP) · media (DIS).

**Press coverage introduced nothing.** Every fact below is a filer's own
typeset words or the regulator's own index field.

### The three dates are genuinely distinct, and were kept apart

| | |
|---|---|
| **filing date** — when the regulator received it | `filingDate`, present for 244/244 |
| **occurrence date** — the filer's date of earliest event | `reportDate`, present for 244/244 |
| **effective date** — when the change takes effect | in the section text, present for **157/244 (64%)** |

Filing and occurrence differ for **130 of 157** filings that state an
effective date; the lag runs 0–7 days, which is the four-business-day
rule. **87 of 244 (36%) state no effective date at all**, so an
effective date is a field that is frequently absent and must never be
defaulted from either of the others.

Peloton illustrates the distinction exactly: its CEO departure
**occurred** 2024-04-27 and was **filed** 2024-05-02. A layer keyed on
the filing date would date the event five days late.

## 2. An identity defect, found before any measurement

**`PARA` resolves to Banzai International, not Paramount.**

`EdgarFilings._cik` matches a ticker against the SEC's current company
list. Paramount Global was acquired and delisted; the ticker was
reassigned. The harvest pulled seven Item 5.02 filings under "PARA"
which are **another company's officer changes**, and nothing downstream
could have seen it — a leadership timeline is precisely the kind of
evidence where a wrong issuer looks entirely plausible.

This is Invariant 2, in a third place: *identity is enforced before the
reading, and a perfectly grounded reading of a genuine filing is still
wrong when the filing is another company's.* PARA was dropped and DIS
substituted.

Two more tickers — **WBA** and **X** — are **not in the SEC ticker map
at all**, both having been acquired. A ticker-keyed event stream
silently loses a company on delisting and silently acquires a different
one on reassignment.

## 3. Q3 — which filing grammars the existing parser misses

Measured by running the **committed** location rule (`edgar_filings._section`:
pair each opening with the first closing after it, widest pair wins)
over all 231 filings of the first harvest.

| | |
|---|---|
| located | **183** |
| missed | **48** |

Of the 48, seven were the misidentified PARA. **All 42 remaining misses
are one cause**, in three variants, found by dumping the exact
characters between the word and the number:

| n | separator | |
|---|---|---|
| **28** | `U+00A0` **NO-BREAK SPACE** | `Item 5.02` |
| **11** | `U+2009` **THIN SPACE** | `Item 5.02` |
| **3** | the word split by markup | `I tem 5.02` |

**Nothing else missed.** No filer used a different number format, and no
filer omitted the heading.

Replacing the literal opening with `\s`-tolerant matching — one change,
and exactly what `section_locator.py`'s `_CANDIDATE` already does —
took location to **244 of 244**. That module's own docstring names this
defect (*"Matching literally missed `Item\xa01.` — Amazon and Boeing
typeset a non-breaking space there"*), and `grep` shows it is imported
only by `app/providers/statement_locator.py`. **The repair exists, is
tested, and is not wired into the path that reads named items.**

This is reported as a **parser miss**, separately from every deliberate
decline below.

## 4. Q2 — can the event kinds be distinguished without a model?

**Partially, and not reliably enough to assert anything.** Four
measured obstacles.

### 4.1 The item's own title contaminates every keyword count

Item 5.02's regulator-defined title is *"Departure of Directors or
Certain Officers; Election of Directors; Appointment of Certain
Officers; Compensatory Arrangements of Certain Officers"*, and every
filer prints it. Counted over the raw section:

| word | raw | with the title stripped |
|---|---|---|
| depart | **243 / 244** | 45 |
| appoint | **242 / 244** | 102 |
| elect | **242 / 244** | 71 |

Any rule read over an unstripped section is reading the regulator's
form, not the filer's statement. Stripping is mechanical and was done
for everything below.

### 4.2 The regulator's own sub-item letter is the strongest signal and is usually absent

`(b)` departure · `(c)` appointment · `(d)` director election ·
`(e)` compensation. Where a filer prints one it is decisive. It is
printed in **67 of 244 sections (27%)**.

| letter | segments |
|---|---|
| none | **177** |
| (b) | 27 |
| (e) | 22 |
| (d) | 16 |
| (c) | 4 |

The `items` field on the submissions index carries only `5.02`, never
the letter — so the regulator's classification is available for a
quarter of the corpus and no more.

### 4.3 The vocabulary for a succession search barely exists

Over the filer's own words, across 244 filings:

| | occurrences |
|---|---|
| `interim` | 31 (12%) |
| `transition` | 42 (17%) |
| `successor` | 12 (4%) |
| `search` | **4 (1%)** |
| `succession` | **3 (1%)** |
| `permanent` | **2 (0%)** |

**Category 1 of the brief — a planned CEO succession search — is named
in four filings out of 244.** And "permanent appointment" is not
signalled by the word *permanent* at all; it can only be inferred from
the *absence* of *interim*, which is an inference from silence.

### 4.4 `interim` cannot be attached to the right person

Of the 58 sentences containing *interim*, a rule keyed on the
surrounding verbs could attribute **21** to an appointment being made
and **8** to someone ceasing — and **29 (50%) it could not attribute at
all**.

The consequence is live in the corpus:

- **Intel, 2025-03-10.** Lip-Bu Tan appointed CEO — a **permanent**
  appointment. Classified `interim appointment`, because the same
  filing records the interim co-CEOs standing down.
- **Starbucks, 2024-08-11.** Brian Niccol appointed CEO — **permanent**.
  Classified `departure + interim appointment`.

## 5. Q1 — can an opening and its closure be linked deterministically?

# No.

Tested with the most generous still-deterministic rule: an opening is a
segment naming the CEO role with a departure verb and no CEO appointment;
a closure is the next CEO appointment for the same company.

Five openings were detected across sixteen companies. **All five are
wrong**, and the two transitions with a real vacancy were not detected.

| company | rule's answer | what actually happened |
|---|---|---|
| **BA** | open 2023-02-16 → close 2023-12-08 | Calhoun announced his departure **2024-03-24**; Ortberg elected **2024-07-30**. Neither filing was read as an opening |
| **INTC** | open 2023-12-29 → close 2024-12-01 | Gelsinger resigned **2024-12-01**; Tan appointed **2025-03-10**. The rule's "opening" is a **restatement** of an earlier event and its "closure" is the actual opening |
| **DIS** | open 2023-07-12 → close 2026-02-02 | a contract extension read as a 2½-year vacancy |
| **SBUX** | open 2024-09-12 → **none found** | the "opening" is Michael Conway, *"chief executive officer, **North America**"* — a divisional officer |
| **UNP** | open 2023-08-11 → close 2025-12-12 | the "opening" opens with *"As previously reported…"* |

Three further named causes fall out of this table:

- **Restatements.** 24 of 246 segments say the event was already
  reported. A stream that treats each filing as a new event double-counts
  them, and Intel's case shows a restatement being read as the opening
  of a transition that had already closed.
- **Qualified titles.** 54 segments name an officer of something other
  than the registrant — *"chief executive officer, North America"*,
  *"Chief Executive Officer of Intel Products"*. Matching the role
  string alone promotes a divisional officer to the company's CEO.
- **Biographies.** 11 of the 16 segments the regulator letters `(d)` — a
  **director** election — name a covered officer role in their text,
  because a new director's biography states the roles they held at other
  companies. Intel's December 2024 director election reads as a filing
  about a CEO, a COO and a President.

## 6. The hand-checked audit

Counts are worthless unless the classifier is checked against events
whose facts are known. Eleven CEO transitions, verified one by one:

| | filing | classified | correct? |
|---|---|---|---|
| BA | 2024-03-24 Calhoun steps down, **no successor** | departure + replacement | **wrong** |
| BA | 2024-07-30 Ortberg elected | departure + replacement | **wrong** |
| NKE | 2024-09-19 Hill in, Donahoe out | departure + replacement | correct |
| INTC | 2024-12-01 Gelsinger out, interim co-CEOs | departure + interim | correct |
| INTC | 2025-03-10 Tan appointed **permanent** | interim appointment | **wrong** |
| SBUX | 2024-08-11 Niccol appointed **permanent** | departure + interim | **wrong** |
| DIS | 2022-11-20 Iger in, Chapek terminated | departure + replacement | correct |
| CVS | 2024-10-17 Joyner in, Lynch out | departure + replacement | correct |
| EL | 2024-10-29 de La Faverie in, Freda out | departure + replacement | correct |
| PTON | 2024-04-27 McCarthy resigns, interim co-CEOs | departure + interim | correct |
| **ADBE** | **2026-03-09 Narayen transitioning, search underway** | **appointment** | **wrong** |

**Six of eleven correct.** A layer that is right about a CEO transition
five times in nine would be worse than saying nothing, because an
investor cannot tell which five.

Adobe's three other filings show the same failure in three more shapes:
a **retention letter** describing a hypothetical severance was read as a
`departure`; a **Chief Strategy Officer's** resignation was read as a
covered `departure + replacement` because an unrelated `(e)`
compensation paragraph was glued to it; and four **performance share
programs** carry `roles=[CEO, CFO, President]` because the plan names
its participants.

## 7. Q4 — does CEO / CFO / COO / President cover the corpus?

**It covers the transitions, and the four-role set is not the part that
needs widening.**

| role named in the filer's own words | sections |
|---|---|
| President | 135 (55%) |
| Chief Executive Officer | 95 (38%) |
| Chief Financial Officer | 59 (24%) |
| Chair of the board | 68 (27%) |
| Chief Operating Officer | 29 (11%) |
| other named C-suite | 29 (11%) |
| Chief Accounting Officer / Controller | 27 (11%) |
| General Counsel / Chief Legal Officer | 10 (4%) |
| Treasurer | 7 (2%) |

**78 of 244 sections name none of the four** — and inspection shows
these are overwhelmingly the correct exclusions: equity plan amendments,
severance plans and director appointments.

Two observations, neither of which earns a change:

- **Chief Accounting Officer / principal accounting officer** appears in
  27 sections and *is* a named principal officer under the rule. It is
  the only candidate the evidence puts forward, and it is not needed for
  any transition in this corpus.
- **The four-role set's real defect is that it does not express a
  narrowing.** It has no way to say *of the registrant, not of a division
  or a former employer* — which is what §5 measured as 54 qualified
  titles and 11 biography contaminations. Adding roles would make that
  worse, not better.

## 8. Q5 — can a current continuity *state* be established?

**No. Only filings can be reported, and not even events.**

A state such as *"the CEO seat is filled on an interim basis"* is the
conjunction of three things this corpus cannot supply deterministically:
which person, in which role, and whether an earlier opening is still
open. §5 shows the third fails outright; §4.4 shows the second fails for
half the *interim* sentences; and the 64% multi-person figure shows the
first has no mechanism at all.

**And absence is not evidence of stability.** The corpus begins
2022-01-01 and holds only what was fetched. A company with no Item 5.02
in that window may have had no transition, or may have had one in 2021,
or may be a filer this platform cannot read at all (§10).

## 9. Q6 and Q7 — would a course, or a silence, invent meaning?

### Q6 — a course such as WAIT or MONITOR

**Yes, it would invent investment meaning, and it is declined.**

Nothing measured here relates a leadership transition to an investment
outcome. This platform holds no such evidence, and the brief's own
constraint — *do not infer that a transition is adverse* — is exactly
the inference a `WAIT` would encode: it would tell an investor to defer
a decision *because* an officer changed. That is Invariant 10 in its
semantic form — an established event is authority to report the event,
never authority to invent what the event means for a holding.

The precedent is on the record twice: S5.3 parked issuance magnitude
`OUTSIDE_ASSET_QUALITY` because *the same figure means different things
depending on where it goes*, and BQ20 refused a bank margin a
corporate threshold could not read. A CEO departure is the same shape —
Apple's in 2011 and a distressed retailer's are not one quantity.

### Q7 — what a company with no leadership event must be told

**"No Item 5.02 event was filed in the window this platform read"** —
a statement about this platform's evidence, dated and bounded, never
*"leadership is strong"*, *"stable"* or *"continuity is intact"*.

This is Invariant 1 and the F1 fund ruling applied unchanged: IB01.L
rendered *"Business quality LOW (40)"* from a `dividend_yield: 0.0` on a
share class that cannot distribute, because an absence was scored
instead of stated. A silent 8-K record is the same absence.

## 10. Q8 — the coverage gap for non-SEC issuers

Measured against the 24-company statement corpus a continuity layer
would have to serve:

| | 8-K filed since 2022 | with Item 5.02 | 6-K filed |
|---|---|---|---|
| **BCS** Barclays | **0** | **0** | 202 |
| **NWG** NatWest | **0** | **0** | 840 |
| **DB** Deutsche Bank | **0** | **0** | 22 |
| **MUFG** Mitsubishi UFJ | **0** | **0** | 169 |
| AAPL, TSLA, WMT, PG, MET, ALL, TRV, CB, COF, FITB, RF, AXP | 39–154 | 6–14 | 0 |

**Foreign private issuers file no 8-K and there is no Item 5.02
equivalent.** They file 6-K, which is a wrapper around whatever the home
regulator required, with no item taxonomy at all. **Four of the
twenty-four companies whose statements this platform already reads are
structurally unreachable**, and the gap is not a matter of effort: the
document class does not exist.

Two further gaps: a delisted issuer leaves the SEC ticker map entirely
(WBA, X), and a reassigned ticker resolves to a different company
(PARA, §2).

## 11. Conclusion

# C — NOT READY

**The precise blocker: one Item 5.02 section is not one event, and no
per-person, per-role segmentation exists.**

Stated so it can be checked and so its removal is recognisable:

> **64% of the segments a classifier reads as a covered-officer event
> (85 of 132) name two or more people.** Until a filing can be
> decomposed into *(person, role, action, effective date)* tuples, every
> classification is a property of a document rather than of a
> transition — which is why Boeing's "no successor named" and Boeing's
> "successor named" produce the identical verdict, and why Adobe's
> succession search is read as an appointment.

**Option B was considered and refused.** A descriptive *event state*
would require that the platform can say *what happened to whom*; §6
shows it is right about a hand-checked CEO transition six times in
eleven. What is genuinely earned today is narrower than an event state
and should not be dressed as one: a **filing-level record** — this
company filed an Item 5.02 on these dates, and here is the filer's own
text. That is an inventory of documents, and calling it a continuity
state would be the overstatement every rule here exists to prevent.

### What would move this to B, named

1. **Per-person segmentation.** Decompose a section into person-scoped
   spans before any classification. This is the whole blocker.
2. **Registrant-scoped role matching.** A rule that refuses
   *"chief executive officer, North America"* and a biography's
   *"served as Chief Executive Officer of Cadence"*. §5 gives 54 and 11
   live specimens.
3. **Clause mood.** Adobe's *"until his successor is appointed"* and the
   retention letter's *"in the event of a termination"* are conditional
   clauses about things that have not happened. A rule that reads them
   as events is not repairable by adding keywords.
4. **A restatement rule.** 24 segments announce that they are restating.

### Free and separable, whatever is ruled

The **heading normalisation** (§3) is one change, its repair is already
written and tested in `section_locator.py`, and it moves item-section
location from 183/231 to 244/244. It is independent of everything above
and of any continuity layer: it is a parser defect that costs 18% of a
document class this platform already fetches.

## 12. Scope compliance

Research only · no production implementation · no score, confidence
percentage, sentiment or management-quality grade proposed or computed ·
no CIO, committee, Business Quality or decision change · **no model
call** · no inference that any transition is adverse · no inference
about any stock price · parser misses (§3) and source failures (§2, §10)
reported separately from the deliberate declines (§9) · every figure is
a filer's own typeset words, the regulator's own index field, or a count
over them.

Work was done in a worktree from `origin/main` so that unrelated
uncommitted leadership-event work in the primary tree was never read,
staged or modified.
