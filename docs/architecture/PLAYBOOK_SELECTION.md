# Playbook selection from Business Understanding

**Status: accepted; implemented in the slice that adds this document.**

The selector's question changes: not *what industry is this*, but *which
investment playbook applies to this business understanding*. An archetype
describes economic structure — what the settled facts say the business
is. A playbook describes how the investment should be analysed. This
document is the deterministic mapping between them, derived from the
five companies at quorum, and nothing wider.

```text
CompanyKnowledgeConsensus → CompanyArchetype → BusinessUnderstanding
                                                      ↓
                                              PlaybookSelector
                                                      ↓
                                            Investment Playbook
```

## The migration rule

The industry-driven selector is not replaced; it is *outgrown*, one
authoritative case at a time.

1. Understanding quorate **and** the mapping establishes exactly one
   playbook → the understanding-driven playbook, marked authoritative.
2. Below quorum, archetype undecided, or conclusion unmapped → the
   existing industry-driven selector, marked **not** authoritative, with
   the grounded route's refusal stated verbatim.
3. The two routes never blend. A grounded selection consumes consensus
   claims only; a fallback selection consumes none, and says so.
4. Every selection records which selector produced it and why.

An interpretation does not become authoritative merely because it
exists.

## The rule table, against the corpus at quorum

Every row below is a live `movrvest understanding` run, not a
projection.

| | Characteristic (rule) | Leading mechanisms, coverage | Unsettled claims | Playbook | Selection rule | Refusal / contingency |
|---|---|---|---|---|---|---|
| **DIS** | Diversified (`no-single-way-of-earning-leads`) | licensing 102%, services 102%, transaction 102% — within 5% of one another | how 'Experiences' earns, 4/5 (consumed) | **Diversified Business**, authoritative | `diversified-activates-diversified-business` | none — every observed alternative still concludes Diversified |
| **NVDA** | Manufacturer (`one-way-of-earning-leads`) | manufacturing 100%, >5% clear; licensing 90%, services 90% | how 'Graphics' earns, 3/5 (consumed) | **Industrial**, authoritative | `manufacturer-activates-industrial` | contingent: either observed minority answer concludes Diversified and would select Diversified Business |
| **CAT** | Diversified (`no-single-way-of-earning-leads`), unanimous on every consumed claim | manufacturing 103%, services 103% — within 5% | how 'Financial Products Segment' earns, 2/2/1 (excluded — no strict majority) | **Diversified Business**, authoritative | `diversified-activates-diversified-business` | the 2/5 answer concluding "Service business, then manufacturer" is excluded *and* unmapped — twice unable to control the selection |
| **META** | Not classified (`nothing-explained` — 0% of revenue explained; both descriptions refused on applicability) | none established | both segments' ways of earning | none grounded → industry fallback (Platform), **not authoritative** | — | refusal: archetype undecided, its own reason passed verbatim |
| **JPM** | Not classified (`nothing-explained` — no sizes either; the MD&A read is a 395-character pointer to a document filed separately) | none established | all six claims | none grounded → fallback, and the industry route decides nothing either: JPM is not on the investor's book, so no provider profile exists — Unclassified, **not authoritative** | — | refusal. A grounded Bank playbook would need `financial_spread` established at quorum, and nothing establishes it |
| **BNP.PA** | Service business, then lender (`one-way-of-earning-leads`), at 11 observations | services 103% (every segment), financial_spread 89% (CIB + CPBS), asset_management_fees 14%, premiums 14% | how 'CIB' earns, 6/10 (consumed); 'Other Activities' earning, no majority (excluded) | **Bank**, authoritative | `service-business-then-lender-activates-bank` | contingent: IPS's 3/10 minority answer drops `services` and would conclude Diversified, selecting Diversified Business |

The JPM row's own note — "a grounded Bank playbook would need
`financial_spread` established at quorum" — is what BNP.PA answered.
It took the deepening above to establish it without the archetype
resting on the narrowest majority a count of five allows.

## The financial-services vocabulary, frozen (2026-08-08)

The corpus earned its third rule, and earning it required deciding
what a financial-services conclusion *is*. The decision is recorded
here, frozen, with the evidence that forced each half of it.

**The measurement.** BNP Paribas at a consensus of **11 observations**
(deepened from 5 to settle a narrow claim; the count was fixed before
any reading, and the stopping rule never referenced content):

| Claim | Settled | Width |
|---|---|---|
| CIB size | 37% (18,997 of 51,223) | 10/10 |
| CPBS size | 52% (26,717 of 51,223) | 10/10 |
| IPS size | 14% (6,929 of 51,223) | 10/10 |
| CPBS earning | `financial_spread, services` | 8/10 |
| IPS earning | `asset_management_fees, premiums, services` | **7/10** |
| CIB earning | `financial_spread, services` | 6/10 |
| Other Activities size | absent, reason worded | 11/11 |

The claim the deepening was spent on settled decisively: IPS's
`services` went from a knife-edge 3/5 to **7/10**. The archetype no
longer rests on the narrowest majority the count allows.

**The finding that shaped the vocabulary: `services` is a ubiquitous
co-tag, not a distinguishing engine.** Every BNP segment earns by
`services` *as well as* by something else, so services covers 103% and
leads the ranking — while `financial_spread`, the engine that actually
separates this business from any other, covers 89% through the two
segments that are banks. The rules are right that services leads; a
mapping keyed on that alone would have been wrong about what the
company is.

**So the vocabulary is frozen on the pair, not on the primary.** The
conclusion `Service business, then lender` activates the Bank
playbook. Three decisions, each with its reason:

1. **A bare `Service business` stays unmapped.** A consulting firm and
   a universal bank share that primary, and only one of them is read
   on a balance sheet that *is* the business. Mapping the primary
   would be the industry substitution this selector exists to replace.
2. **"Lending is a leading engine" was rejected as too broad, on
   corpus evidence.** Caterpillar is a maker with a captive lender; a
   rule keyed that way would hand a manufacturer of excavators a
   bank's playbook. Held as a test rather than as a note.
3. **No new playbook was created.** The Bank playbook already existed
   for the industry route — same frame, now reachable from evidence.
   The grounded route's contribution is the *rule*, not another
   implementation of the same concept.

**Still deliberately unmapped:** `Insurer` and `Asset manager` as
primaries, and every other pair. BNP's own IPS establishes premiums
and asset-management fees at 14% coverage — real, and far from
leading. Those rules wait for a company whose filing makes them lead,
exactly as this one waited.

## The mapping, exactly

Three rules, in two tables. Not a taxonomy — the corpus has earned
three, and a rule without a quorate case behind it would be this
platform's own Yahoo.

**Precedence:** a pair rule is consulted before a primary rule,
because a pair is the same conclusion stated with one more fact in it.
A conclusion matches at most one entry in each table, so the mapping
stays unambiguous — and the tests hold both doors shut.

- **`manufacturer-activates-industrial`** — archetype primary is
  `MANUFACTURER` → the **Industrial** playbook. Why the structure
  activates the frame: when making goods runs through the leading share
  of measured revenue, the questions that decide the case are a maker's
  questions — the margin on what is made, the capital the making
  consumes, and the cash it returns through a demand cycle.
- **`diversified-activates-diversified-business`** — archetype primary
  is `DIVERSIFIED` → the **Diversified Business** playbook. Why: no
  single way of earning leads, so no single-mechanism lens applies; the
  business is read on the whole of its ordinary accounts, because no
  one engine's economics can stand for the company.

- **`service-business-then-lender-activates-bank`** — the *pair*
  (`SERVICE_BUSINESS`, `LENDER`) → the **Bank** playbook. Why: the
  segments that lend run through the larger part of measured revenue,
  and services rides alongside every one of them rather than
  distinguishing any — so the questions that decide the case are a
  bank's questions: the strength of a balance sheet that is the
  business rather than a support for it, what it earns on those
  assets, and how the lending grows. Earned by BNP.PA at 11
  observations; frozen above.

The first two playbooks run the standard four fundamental analysts;
the Bank playbook declines the cash-flow analyst with its reason
already stated in `PLAYBOOKS`. This slice changes which *explanation*
frames a case, and — for a bank — which analysts are asked, because
asking an industrial's question of a bank was always the defect.

**Deliberately unmapped:** the other rankable archetypes as primaries
(Insurer, Asset manager, Subscription, Advertising, Transaction,
Licensing, Retailer, Commodity producer, Lender alone, and
`Service business` without a lending runner-up), and every pair but
the one above. No company at quorum concludes any of them, so a
mapping would be untestable. A future filing that establishes one
lands in the refusal path below — named, never defaulted — until its
rule is earned.

## Refusal, with the reason

The grounded route refuses — and the industry selector serves, recorded
as fallback — when:

1. **Below quorum.** Nothing decided from a sub-quorum consensus is
   authoritative; the count is stated.
2. **Archetype undecided or unranked** (`primary` is None). The
   archetype's own `undecided_because` travels verbatim; the selector
   never re-words another layer's absence.
3. **Conclusion unmapped.** The rules decided something the corpus has
   not yet earned a playbook for. The conclusion is named; serving a
   default would recreate the industry-substitution this layer
   replaces.

Ambiguity ("maps to more than one") is structurally impossible today —
one primary, disjoint predicates — and the tests hold that door shut:
each archetype maps to at most one rule.

## The output contract

`PlaybookSelection` carries: the playbook; `authoritative`;
`selected_by` (`business_understanding` | `reported_industry`);
`rule_fired`; `facts_consumed` (consensus claims only — empty on
fallback, by invariant); `narrowest_agreement` (what the conclusion
rests on, worded with its count); `alternatives_considered` (each
unfired rule, with why its activating conclusion was not reached);
selection contingencies (each narrow or unsettled claim's observed
answers, mapped through the identical rules, each marked whether it
would change the selection); and `fallback_reason` (the grounded
route's refusal, verbatim, where it refused).

## Not in this slice

The research path (`ResearchStrategyFactory`, dossiers, committees)
keeps consuming the industry selector unchanged. The flip is a later
slice, gated as [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md) records: a
thicker quorate population, and this mapping proven on it first.

**Visibility shipped before the flip (EF1, 2026-08-13).** The equity
dossier now exposes this selector's grounded half — `select_grounded`
over the understanding the page already composes read-only — beside the
provider's industry, each in its honest state and neither substituting
for the other
([`EQUITY_DOSSIER_FIDELITY.md`](EQUITY_DOSSIER_FIDELITY.md) §7). The
displayed selection reroutes nothing, by test. The decision flip stays
gated on evidence, not architecture
([`DECISION_CONVERGENCE_MEASUREMENT.md`](DECISION_CONVERGENCE_MEASUREMENT.md)):
the measured counterfactual moved zero decisions, so **the convergence
experiment is repeated when a company with an established specialised
archetype — BANK first, BNP.PA the priority — reaches
financial-statement quorum for the specialised question set**, comparing
questions, applicability, evidence consumed, assessments, committees,
conviction and decision. The two routes coexisting today is a deferred
evidence gate, not an endorsement of two permanent analytical routes.

---

## What this selector does *not* decide (2026-08-08)

A playbook says **what a company is**. It does not say **which financial
language reads its statements**. The bank slice separated the two, and
the separation is now a boundary rather than an observation.

```text
Business understanding  → Business playbook  → what company is this?
Financial understanding → Financial model    → which financial language
                                               should the CIO speak?
```

`FinancialModel` (`app/domain/financial_question.py`) owns the financial
question set — which questions are meaningful for a kind of company,
which established facts answer them, and which generic questions must be
refused outright. `PlaybookKind` owns none of that.

**The case that forced it.** JPMorgan's grounded playbook is
*Diversified*: its own filing says lending, services and transaction
lead together within 5%, and the `(SERVICE_BUSINESS, LENDER)` pair the
BANK rule is keyed on was never reached. So JPM does not receive a
bank's financial questions, and under the generic model it still
receives the industrial leverage score on a liabilities-to-equity of
11.21×.

The obvious repair was to promote JPM to `BANK`. The owner refused it:

> That `--model bank` produces a much more sensible financial
> assessment is not evidence that JPM should classify as BANK. It is
> evidence that the BANK financial questions are better than the
> industrial ones for deposit-taking institutions. Those are different
> claims.

Changing a selector because the downstream interpretation looks better
is reasoning backwards from the desired outcome, and it would bend the
business ontology to suit an analyst. **A playbook route is earned by
evidence about the company, never by the convenience of what consumes
it.**

**How they are coupled today.** `model_for(playbook)` is the only route
between the layers, and it is a coupling *stated as one*: the financial
model follows the business playbook because no evidence has earned it
not to. `PlaybookKind.BANK` is its single non-generic entry; everything
else is `GENERIC`.

**The divergence that is not built.** A financial model selected from
the statements themselves — a filing printing no gross profit line, no
operating income line and an unclassified balance sheet is speaking a
bank's language whatever its segments say — is the natural second route.
Every one of those facts is already established on JPMorgan at 5/5. It
is not invented here: one company's statements are not a corpus, and
writing the rule now would be the same backwards reasoning in a new
place.
