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

## The mapping, exactly

Two rules. Not a taxonomy — the corpus has earned two, and a rule
without a quorate case behind it would be this platform's own Yahoo.

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

Both playbooks run the standard four fundamental analysts. This slice
changes which *explanation* frames a case, never which analysts run.

**Deliberately unmapped:** the other ten rankable archetypes
(Lender, Insurer, Asset manager, Subscription, Advertising,
Transaction, Licensing, Retailer, Service business, Commodity
producer). No company at quorum concludes any of them, so a mapping
would be untestable. A future filing that establishes one lands in the
refusal path below — named, never defaulted — until its rule is earned.

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
