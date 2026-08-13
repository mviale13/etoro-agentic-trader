# Would role-aware archetype selection classify Volkswagen? — measured, and refuted

**Status: research only, measured 2026-08-13 at `035c3f0`. Nothing was
built and nothing in this document is a mandate to build**
(Constitution §23–24). Harness: `tools/archetype_relationship.py`
(read-only; delete when the ruling lands). Every number below came out
of the live archetype engine over stored readings — none is recalled,
none is projected except where a row says PROJECTED.

The ruling's question:

> Does the archetype engine confuse diversity of revenue mechanisms
> with diversity of independent economic engines, and can ED1's
> established economic relationships resolve that distinction without
> weakening evidence standards?

**The answer is yes to the first half and no to the second, and the
second half fails for a reason the ruling did not anticipate.** The
engine does confuse the two — comprehensively, in every decided verdict
the corpus holds. But economic dependency is not the fix, because
Volkswagen's refusal happens *upstream of every diversity rule*, and a
relationship-aware interpretation changes **zero verdicts across nine
companies**. The confusion the ruling correctly identified turns out to
live somewhere else entirely.

---

## 0. Two findings that reframe the experiment before it starts

**Nothing in the store carries an economic relationship.** ED1 shipped
its contract on 2026-08-13; its acceptance readings are credit-blocked
and were never taken. A scan of all 33 knowledge files and 75
observations finds **zero** `EconomicRelationship` records. So route B
cannot be run against established relationships at all — it is run
against *projections* of what ED1 would establish, each carrying the
filer quote measured in
[`ECONOMIC_DRIVER_DEPENDENCY.md`](ECONOMIC_DRIVER_DEPENDENCY.md) §1 and
labelled PROJECTED everywhere below. This weakens the experiment's
authority over the *meaning* half of the question and, as §3 shows,
not at all over the verdict half: the headline result holds however
generously the projections are granted.

**Only two companies restore under the current schema.** VOW3.DE and
JPM are schema 12; the other 31 files are schema 11 and the store
deliberately restores them as absent. The harness relabels a *copy*
11 → 12 in a temp directory to reach them (`data/` is opened read-only),
exactly as the convergence harness did. That bypasses a gate and
changes no claim — every segment, share and mechanism is what the
reading stored — but those rows are **archived readings, not knowledge
this platform currently holds**, and are marked so.

---

## 1. Why Volkswagen refuses today — the arithmetic, exactly

Read live from `CompanyKnowledgeService.established("VOW3.DE")`, a
quorate consensus of 5 observations:

| Segment | Share | `RevenueModel`s established | Size agreement | Earning agreement |
|---|---|---|---|---|
| `Pkw und leichte Nutzfahrzeuge` | **75.9%** | **none** | unanimous 5/5 | unanimous 5/5 (that there are none) |
| `Nutzfahrzeuge` | 13.2% | manufacturing, retail, services | unanimous 5/5 | narrow majority 3/5 |
| `Finanzdienstleistungen` | 19.3% | financial_spread, premiums, services | unanimous 5/5 | unanimous 5/5 |

(Shares sum to 108.5% because each segment's revenue includes
intersegment sales while the denominator is the external total — the
known and correct >100% shape. The ruling's brief quotes 67.5/12.9/18.0,
which are the same three segments as shares of *external* revenue only.
The two bases order the segments identically and no conclusion here
turns on which is used.)

The engine's own steps, in order:

1. `segments_because` is None — the readings agree which segments exist.
2. `earning` = segments with any mechanism = **`Nutzfahrzeuge`,
   `Finanzdienstleistungen`**. `Pkw` is excluded here.
3. `measurable` = those of them with a measured size = the same two.
4. `explained` = 0.132 + 0.193 = **0.325**.
5. `ENOUGH_EXPLAINED` = 0.50. **0.325 < 0.50 → `too-little-explained`.**

> *"Only 33% of this company's revenue is both measured and shown to
> earn a particular way. Naming the business after that would
> generalise from its smaller part."*

**The threshold that causes abstention is a description-coverage floor,
not a diversity rule.** `LEADS` (0.5) and `TIED` (0.05) — the rules that
decide single-engine versus Diversified, and the only rules a
relationship could possibly inform — are never reached. The engine
returns before ranking anything.

**The additional fact that would make the current rule classify** is
therefore exactly one thing: an established way of earning for
`Pkw und leichte Nutzfahrzeuge`. Nothing else. Not a relationship, not
a threshold, not a new mechanism vocabulary.

And the separation the ruling asked for is real and decisive:

- *"MOVRvest lacks evidence that Volkswagen is predominantly
  automotive"* — **false**. It holds a unanimous 5/5 size for a segment
  worth 75.9% of measured revenue, plus the filer's own dependence
  disclosure for the financial arm.
- *"MOVRvest's archetype contract requires a different kind of evidence
  before it may express that conclusion"* — **true**. The contract
  consumes (mechanism, share) pairs. A segment with a size and no
  mechanism is invisible to it, however large. VW's 75.9% enters the
  arithmetic as **nothing**, and its own refusal sentence says "33%"
  about a company three-quarters of which it has measured.

The refusal is epistemically correct under the contract, and the
contract is measuring description coverage while wording the result as
though it were about the business.

---

## 2. Route B: the relationship-aware interpretation

Defined as the smallest evidence-respecting change: **a segment the
filer states is economically driven by another business contributes no
*independent engine* to the mechanism ranking.** Its revenue still
counts as explained, its size is untouched, it is never erased — only
its claim to be a *separate* engine is withdrawn.

Two projections, both from filer statements already measured against
the documents:

| Symbol | Dependent | Driver (filer's own altitude) | Warrant |
|---|---|---|---|
| VOW3.DE | `Finanzdienstleistungen` | "the Automotive division's products… vehicle deliveries" | business-model sentence (*im Wesentlichen Vertriebsunterstützung*), titled dependence risk, penetration KPI 37.2%, intersegment row; zero hits for non-Group financing |
| CAT | `Financial Products Segment` | "sales of Caterpillar products" | the filer's support sentence — **but the same filer says it finances "Caterpillar *and other* equipment"**, so its disclosed dependence is qualified where VW's is not |

Controls with no relationship stated in any evidence held: DIS, NVDA,
JPM, BNP.PA, META, NFLX.

### The result

| Symbol | Route A | Route B | Changed? |
|---|---|---|---|
| VOW3.DE | Not classified (`too-little-explained`) | Not classified (`too-little-explained`) | **no** |
| CAT | Diversified (`no-single-way-of-earning-leads`) | Diversified (same rule) | **no** |
| DIS | Diversified | Diversified | no |
| JPM | Diversified | Diversified | no |
| NVDA | Manufacturer | Manufacturer | no |
| BNP.PA | Service business, then lender | Service business, then lender | no |
| UMI.BR | Diversified | Diversified | no |

**Zero changes.** Route B is inert over the entire corpus, and for three
independent reasons that are worth separating:

- **VOW3.DE** — the relationship is applied and cannot matter: the
  refusal is upstream. Withdrawing FS's engine claim actually *lowers*
  the ranking's reach (coverage drops to manufacturing/retail/services
  at 13.2%), and excluding FS's revenue from `explained` as well would
  refuse VW **harder**, at 13.2%.
- **CAT** — its captive carries **no established mechanism at all**
  (the description settled 2/2/1, no strict majority), so it is already
  outside the ranking. Route B withdraws a claim the engine never had.
- **Everyone else** — no relationship is stated, so route B is
  definitionally route A. This is NVDA's control, and it holds by
  construction: absence of relationship evidence changes nothing and
  is never read as independence.

### Where route B *would* matter — the latent boundary, measured

Swept over 42 synthetic maker-plus-captive shapes: route B changes the
verdict in **10**, and **every one requires the captive's mechanism to
cover ≥50% of measured revenue** (e.g. maker 55% / captive 55%:
A = Diversified, B = Manufacturer). Corpus reality: VW's captive covers
19.3%, CAT's 6.2%. The capability is real and the corpus does not
exercise it — a boundary waiting for a company, precisely as
`ECONOMIC_DRIVER_DEPENDENCY.md` §4 predicted, now with the threshold
measured.

---

## 3. Volkswagen's real blocker: description altitude, crossed with the relationship

The two axes, run together. `Pkw` is *granted* mechanisms (never
inferred from its name) to ask what the rules then do:

| `Pkw` mechanisms | Route A | Route B |
|---|---|---|
| none (today) | Not classified — `too-little-explained` 32.5% | Not classified — `too-little-explained` 32.5% |
| manufacturing | **Manufacturer** (mfg 89.2%, clear) → Industrial | **Manufacturer** → Industrial |
| manufacturing + services | **Service business** (services 108.5% over mfg 89.2%) | **Diversified** (mfg 89.2% ties services 89.2%) |
| manufacturing + retail + services (its sibling's own shape) | **Service business** | **Diversified** |

Three things follow, and they are the core of this measurement.

**Description-altitude reconciliation is required. Economic dependency
is neither sufficient nor, in the likely cases, helpful.** Answer **B**
of the ruling's A/B/C — with a sharp caveat below.

**VW earns `INDUSTRIAL` only under the narrowest description outcome.**
If `Pkw` establishes manufacturing *alone*, both routes reach
Manufacturer at 89.2% and the existing Industrial playbook follows,
from issuer-grounded facts, with no provider industry and no common
knowledge. But `Nutzfahrzeuge` — the closest available analogue, the
same filer, the same document, a vehicle-making segment — established
**manufacturing, retail and services**. If `Pkw` reads like its sibling,
VW reads **Service business** under today's rules: the ubiquitous
`services` co-tag rides all three segments to 108.5% and outranks
manufacturing's 89.2%. This is the BNP.PA lesson (*services is a
ubiquitous co-tag, not a distinguishing engine*) arriving at a
manufacturer.

**In that likely case, relationship-awareness makes VW worse, not
better.** Route B removes FS's services tag, which drops services to
89.2% — exactly tying manufacturing — and the engine returns
**Diversified**. The role-aware interpretation converts a wrong answer
(Service business) into a different wrong answer (Diversified), and
moves VW *further* from Industrial than route A does.

So the honest answer is **B, with a warning that B alone is not enough**:
reconciling the description altitude is necessary, and depending on what
that reconciliation establishes, the `services` co-tag problem may still
have to be answered before VW reads Industrial. Dependency is not on the
critical path either way.

---

## 4. Two structural limits found in ED1's own contract

Both are properties of the shipped contract, measured by trying to build
on it:

**The driver is free text and resolves to no segment.** ED1 defines
`driver` deliberately at the filer's own altitude — VW's is
*"Konzernbereich Automobile"*, which is **not a reportable segment**: it
spans `Pkw` and `Nutzfahrzeuge` together. So the strongest form of
relationship-aware reasoning — *attribute the dependent segment's
coverage to its driver's engine* — **is not implementable**. There is
no mechanical link from "the Automotive division" to a segment whose
mechanisms could receive the attribution. Only exclusion (route B) is
constructible, which is why route B is the only variant tested.

**A mechanical engine-count is worse than either route.** Tested as
route C — count material segments not stated-dependent:

| VOW3.DE | DIS | CAT | JPM | NVDA | BNP.PA |
|---|---|---|---|---|---|
| **2** independent (Pkw, Nutzfahrzeuge) | 3 | 3 | 3 | 2 | 3 |

VW comes out with **two** independent engines, because the filer never
states that Commercial Vehicles depends on Passenger Cars — they are one
division in the filer's own account, and the contract cannot see a
division. Route C would read VW as *diversified*, manufacturing the
exact error the ruling set out to remove. Recorded so nobody builds it.

---

## 5. What `DIVERSIFIED` actually measures — the finding that displaces the hypothesis

The ruling asked whether the operational rule is effectively *multiple
material revenue mechanisms* rather than *multiple material economic
engines*. It is, and the corpus is unanimous about it.

For every company reaching a `DIVERSIFIED` verdict, the tied leading
mechanisms and the segments carrying them:

| Symbol | Verdict | Tied mechanisms | Coverage | Carried by | Distinct segment sets |
|---|---|---|---|---|---|
| DIS | Diversified | licensing, services, transaction | 1.020 each | Entertainment, Sports, Experiences | **1 — identical** |
| CAT | Diversified | manufacturing, services | 1.032 each | Construction, Resource, Power & Energy | **1 — identical** |
| JPM | Diversified | financial_spread, services, transaction | 0.832 each | CCB, CIB | **1 — identical** |
| UMI.BR | Diversified | commodity, services | 0.558 each | **Recycling** | **1 — identical** |

**Four of four `DIVERSIFIED` verdicts are produced by mechanism tags
riding an identical set of segments.** Not one is produced by
economically distinct engines. Umicore is the reductio: it is declared
*Diversified* because a **single segment** (Recycling, 55.8%) carries
two mechanism tags.

So `DIVERSIFIED` today operationally means *no single mechanism tag is
5pp clear of another over the same segments* — it measures **tag
co-occurrence within a segment set**, not driver diversity between
businesses. The stronger investor-relevant meaning the ruling proposed —
*multiple material economic engines whose underlying demand is not
predominantly derived from one another* — is **not what the rule
computes**, and route B does not bring it closer, because the confusion
lives *inside* the segment set rather than between a dependent business
and an independent one.

**This displaces the ruling's hypothesis about DIS.** Economic-driver
independence is not what separates DIS from VW under the current rules —
DIS is genuinely diversified and reaches the right verdict by a tie
among three tags on three segments, which is the same mechanism that
gives Umicore a wrong one. What actually separates them today is
**description coverage**: DIS has all three material segments described,
VW has only its two small ones.

---

## 6. The matrix

Archived rows are schema-11 readings reached through the harness, not
current knowledge. Relationships are PROJECTED — none is stored.

| Company | Current archetype | Material businesses | Revenue models | Relationships | Apparent revenue diversity | Evidenced driver structure | Current-rule verdict | Relationship-aware counterfactual | Change? | Why | Confidence / limit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **VOW3.DE** (live) | *Not classified* | Pkw 75.9%, Nutzfahrzeuge 13.2%, Finanzdienstl. 19.3% | Pkw **none**; CV mfg/retail/services; FS spread/premiums/services | FS ← Automotive (PROJECTED; 4 disclosures) | 5 mechanisms | one automotive system + a filer-stated attached finance layer | `too-little-explained` 32.5% < 50% | `too-little-explained` 32.5% | **no** | refusal is upstream of every diversity rule; 75.9% of revenue has no mechanism | high — live, quorate 5/5; relationship projected |
| **CAT** (archived) | Diversified | Construction 37.1%, Resource 18.5%, Power 47.6%, Financial 6.2% | mfg+services ×3; Financial **none** | Financial ← equipment sales (PROJECTED, *qualified* by "and other equipment") | 2 mechanisms | 3 industrial segments + immaterial captive | `no-single-way-of-earning-leads` (mfg 1.032 = services 1.032) | identical | **no** | captive has no established mechanism; the tie is mfg/services co-riding the same 3 segments | high — the verdict never involved the captive |
| **DIS** (archived) | Diversified | Entertainment 45.0%, Sports 18.7%, Experiences 38.3% | 5/5/4 mechanisms | **none stated** | 6 mechanisms | genuinely distinct demand (streaming, ads, sports rights, attendance) | `no-single-way-of-earning-leads` (3 tags at 1.020) | identical | **no** | no relationship exists to apply; verdict rests on a 3-tag tie over one identical segment set | high — but the *right* verdict for a reason unrelated to engines |
| **JPM** (live) | Diversified | CCB 41.0%, CIB 42.3%, AWM 13.0% | spread/services/transaction; AWM **none** | none stated | 4 mechanisms | one balance-sheet business, several product lines | `no-single-way-of-earning-leads` (3 tags at 0.832) | identical | **no** | a bank's own products co-ride; owner already ruled JPM stays Diversified by design | high — live, quorate |
| **BNP.PA** (archived) | Service business, then lender | CIB 37.1%, CPBS 52.2%, IPS 13.5% | spread/services ×2; IPS fees/premiums/services | none stated | 4 mechanisms | standalone banking, no captive relation | `one-way-of-earning-leads` (services 1.028) | identical | **no** | filer states no dependence, so nothing can mark a bank as an arm — the safeguard is ED1's contract, not a name | high — 11 observations |
| **NVDA** (archived) | Manufacturer | Compute 89.6%, Graphics 10.4% | licensing/mfg/services; mfg | none stated | 3 mechanisms | one engine | `one-way-of-earning-leads` (mfg 1.000) | identical | **no** | absence of relationship evidence changes nothing and never implies independence | high — the ordinary-case control |
| **UMI.BR** (archived) | Diversified | Recycling 55.8%, Catalysis 28.0%, Battery 6.3%, Specialty 9.4% | commodity+services; mfg ×2 | none stated | 3 mechanisms | **one segment carries the tie** | `no-single-way-of-earning-leads` (commodity 0.558 = services 0.558, both on Recycling alone) | identical | **no** | the clearest evidence that the rule measures tag co-occurrence | high — and the strongest counter-example to the current meaning of Diversified |
| **META** (archived) | *Not classified* | FoA 98.9%, RL 1.1% | **none** | none stated | 0 | unknown | `nothing-explained` | identical | **no** | nothing to rank | high |
| **NFLX** (archived) | *Not classified* (unranked) | one operating segment | subscription | none stated | 1 | unknown | `nothing-measured` | identical | **no** | no measured size | high |

---

## 7. The ruling's questions, answered

**1. Why does Volkswagen remain unresolved despite overwhelming evidence
that automotive dominates?** Because the archetype contract consumes
(mechanism, share) pairs, and VW's dominant segment — 75.9% of measured
revenue, size unanimous at 5/5 — has **no established mechanism**. It
enters the arithmetic as nothing, the coverage floor sees 32.5%, and the
engine refuses before any diversity rule runs. The platform is not
missing evidence that VW is automotive; it is missing the *particular
kind* of evidence its contract accepts, and its refusal sentence says
"33%" about a company it has measured three-quarters of.

**2. Does ED1 provide the missing fact, or is description-altitude
reconciliation also required?** **Reconciliation is required; ED1's
relationship is not the missing fact.** Answer **B**, not C — with the
caveat in §3 that reconciliation alone may still leave the `services`
co-tag problem to answer. Applying the projected relationship changes
VW's verdict not at all, and cannot: the refusal is upstream.

**3. Does VW legitimately earn `INDUSTRIAL` under a relationship-aware
interpretation, without provider industry or common knowledge?**
**Not from relationship-awareness.** It earns Manufacturer → Industrial
from issuer-grounded facts alone *if and only if* `Pkw` establishes
manufacturing without a co-riding `services` tag — and then it earns it
identically **with or without** the relationship. If `Pkw` reads like
its own sibling segment, VW reads *Service business* (route A) or
*Diversified* (route B), and relationship-awareness is the worse of the
two.

**4. Does CAT expose the same defect or a different one?** **A
different one.** CAT's captive is 6.2% *and carries no established
mechanism*, so it plays no part in any verdict — route B withdraws a
claim the engine never had. CAT's `Diversified` comes from manufacturing
and services tying at 103.2% over the **same three industrial
segments**: mechanism co-riding, one level below the dependency
question. Its filer also *qualifies* its dependence ("Caterpillar and
other equipment") where VW's does not, which is the distinction that
keeps a captive-finance rule from over-reaching.

**5. What makes DIS genuinely different from VW?** Economically:
self-contained description spans, no dependence disclosure, no
penetration-style KPI, and distinct demand sources (subscription,
advertising, sports rights, attendance) — complementarity around shared
IP is not demand derivation. **But that is not what the current rules
use.** Today DIS differs from VW by *description coverage* (3 of 3
material segments described versus 2 of 3, the described ones being the
small ones). DIS's Diversified verdict rests on a 3-tag tie over one
identical segment set — the same mechanism that mis-classifies Umicore.

**6. Would any correct archetype regress under relationship-aware
reasoning?** **Not in the current corpus** — zero verdicts move. Two
regression risks are nevertheless measured and real: route C
(engine-counting) reads VW as *two* independent engines and would
manufacture diversification; and route B applied to a VW whose `Pkw`
carries a services co-tag converts *Service business* into *Diversified*
rather than into Industrial. Neither risk is hypothetical arithmetic —
both are printed in §3 and §4.

**7. Is the current meaning of `DIVERSIFIED` economically defensible?**
**No.** It is accidentally measuring revenue-model diversity — more
precisely, **mechanism-tag co-occurrence within one segment set**. Four
of four Diversified verdicts are ties among tags riding *identical*
segments, and one of them (UMI.BR) is a tie carried by a **single
segment**. A verdict that can be produced by one segment wearing two
tags is not a statement about a company having several businesses.

**8. What is the smallest production rule change supported by the
evidence?** **None is supported today.** The relationship-aware change
this experiment was convened to evaluate moves nothing and is not worth
shipping on this corpus. The co-riding defect is real, but no candidate
rule tested improves the corpus without losing a correct answer: a rule
refusing verdicts whose contenders ride an identical segment set would
refuse **all four** Diversified verdicts, including DIS's correct one.
The two changes the evidence *does* point at are both outside this
experiment's remit and each needs its own ruling — (a) reconciling
description altitude so a segment's mechanism can be established at the
altitude its filer describes it, which is the only thing that unblocks
VW; and (b) the `services` co-tag problem, already named at BNP.PA and
now measured at a manufacturer.

---

## 8. The §23 sentence

The candidate the ruling offered:

> *After this change, the investor can rely on MOVRvest to distinguish a
> genuinely diversified company from an integrated company that
> monetizes one underlying economic engine in several ways.*

**Not earned.** The corpus refutes it as a description of what
relationship-aware selection would deliver: the change distinguishes
nothing that is not already distinguished, in nine of nine companies.
Worse, the sentence is currently *false in the other direction* — the
platform cannot make that distinction today and route B does not give
it, because what defeats the distinction is tag co-occurrence inside one
segment set, not an undetected dependency.

The sentence the measurement *does* support is a smaller and different
one, and it belongs to the description-altitude work rather than to this
experiment:

> *After this change, the investor can see what kind of business
> Volkswagen is at all — today the platform holds a unanimous size for
> 76% of its revenue and reports that it knows 33% of the company.*

And one this experiment records as **not yet sayable by anything built
or proposed**:

> *After this change, the investor can tell a company with several
> businesses from a company whose one business is reported under several
> mechanism tags.*

Umicore is the standing evidence that the platform cannot say it today.

---

## 9. Recorded for whoever builds

- **The harness is disposable** — `tools/archetype_relationship.py`,
  delete when the ruling lands. It reproduces production's route A
  exactly on all nine companies, which is what makes route B's null
  result trustworthy rather than a harness artefact.
- **Route B is written as a re-implementation, not a patch**, so no
  production behaviour can change from anything in it.
- **ED1's `driver` is free text by design and resolves to no segment.**
  Any future role-aware rule must either accept exclusion-only
  semantics or earn a driver-identity contract — and the latter is a
  new evidence question, not a rule change.
- **A relationship must never be inferred** from intersegment revenue,
  segment names, shared branding or common ownership, and the *absence*
  of one must never be read as independence. Route B honours all of
  this by construction: it acts only on a filer statement, and its
  no-op on NVDA is the control.
- **VW's `im Wesentlichen` was preserved throughout.** No step here
  treats predominant dependence as total, and the projected statement
  carries the filer's qualifier intact.
