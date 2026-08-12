# Is evidence strength proportional to the claim? — measured, nothing built

**Status: research only, measured 2026-08-12 at `40eacde`. Nothing in
this document is a mandate to build** (Constitution §23–24). Ruled on
after the Equity Dossier Fidelity measurement, before any E1 slice.

The research question:

> Are MOVRvest's evidence requirements proportional to the claim being
> established, or has filing-grade consensus accidentally become the
> admission ticket for basic business knowledge?

The finding, in one sentence: **the claim ladder is non-monotonic — for
Volkswagen the platform has *established at filing grade* the deeper
claims (its material segments and their relative sizes, 5/5, from
checked cells) while *refusing* the shallower one ("an automotive
group") that five independent surfaces already agree on** — because the
category claim has no evidentiary home of its own and is reachable only
through the mechanism machinery, whose input failed to extract from a
German-language report.

---

## 1. Why VOW3.DE was refused — the exact chain

Traced through the five stored observations, the consensus, and
`understand()` / `select_grounded()`:

1. **Document**: `VWAG_JFB_Konzern-2025-12-31-DE` — the issuer-published
   German-language annual report (xhtml, `language='de'`), identity
   verified four ways including `DOCUMENT_LEI`. The strongest identity
   chain in the corpus.
2. **Segments named**: 3, in the filer's own words — *Pkw und leichte
   Nutzfahrzeuge*, *Nutzfahrzeuge*, *Finanzdienstleistungen* — at 5/5.
3. **Sizes measured**: revenue shares **67.5% / 12.9% / 18.0%** (sum
   98.4%), each a `MeasuredShare` over checked cells (*"Umsatzerlöse mit
   externen Dritten"*), at 5/5. Filing-grade, unanimous.
4. **Descriptions: none, five out of five.** Every reading returned
   `undescribed_because: "The description of '…' arrived with no words
   at all. Asked once more by name, the reader found no words describing
   it in the text this platform reads."` The company-level description
   captured is a *meta-sentence* — "Volkswagen AG reports the segments
   X, Y, Z" — the segment listing, not a description.
5. **Therefore `revenue_models = ()`** for every segment (mechanisms
   derive from descriptions), therefore `understand()` concludes *"how
   it earns is not established — its segments and their sizes are"*,
   therefore no archetype, therefore `select_grounded` refuses,
   therefore the industry route serves General Corporate.

**The failure class is acquisition scope, not filing absence and not
consensus disagreement.** Volkswagen's Geschäftsbericht describes its
divisions; the description prose is not in the text this platform reads
for this document shape. The absence is *consistent* across five
readings precisely because it is structural. `movrvest reader-defects`
already classifies it: *no description found when asked by name* —
3 companies (VOW3.DE, AAPL, CPNG); its sibling *document points
elsewhere for its tables* covers 7 more. The consensus and archetype
rules behaved correctly given their input; the input path is the defect.

---

## 2. The corpus ladder, measured

All 33 companies in the knowledge store, through the same doors
(`consensus_of` → `understand` → `select_grounded`):

- **6 of 33 reach a grounded classification**: BNP.PA (bank), CAT, DIS,
  JPM, UMI.BR (diversified), NVDA (industrial).
- **24 of 33 sit at one observation** — refused by **quorum alone**,
  regardless of content. TSLA's single reading already carries named
  segments, measured shares *and* mechanisms (multi-engine); JNJ's
  single reading is single-engine manufacturing at 100%. Both wait for
  four more paid readings before *any* grounded claim of *any* shape.
- **At quorum, only mechanism extraction blocks**: VOW3.DE (descriptions
  empty, German report) and META (5/5, sized, mechanisms lost to
  *description rejected by applicability*) are the two quorate refusals.
  NFLX is the third shape: quorate, one segment, sizes unmeasured —
  *mechanisms known, weights unmeasured*.

So the admission ticket today is: **five readings of the primary
filing, plus successful description extraction, for every claim shape
from "broad category" upward.** The quorum was calibrated to the
noisiest claim (prose readings agree 60–70%; sizes agree 100% — the
reader-noise-floor measurement) and is charged to all claims equally.

## 3. The claim shapes, empirically — what is required vs what would suffice

Measured on the focus corpus (VOW3.DE, JPM, BNP.PA, META, CAT, NVDA,
DIS, TSLA), with live probes of the candidate sources. No taxonomy is
declared here; the shapes below are the ones the corpus actually
separated.

| Claim shape | What MOVRvest requires today | What the evidence measured says would suffice | Verdict |
|---|---|---|---|
| **Who the issuer is** | Identity checks at acquisition (registry, approved source, content hash, LEI) | Exactly that — VOW3's chain carries four checks; GLEIF corroborates keyless (VOLKSWAGEN AKTIENGESELLSCHAFT, DE) | **Proportional.** Never blocked in the corpus |
| **What it fundamentally does / broad category** | The full archetype machinery: quorum-5 consensus + description extraction + mechanism vocabulary + an earned rule | Corroboration across independent authorities, *attributed*. For VOW3.DE today: provider label ("Auto Manufacturers", in-store), provider description ("manufactures automobiles and commercial vehicles… three segments", live), the filing's own segment names and shares (5/5 — 80.4% of revenue is vehicles), GLEIF identity. Four agreeing surfaces | **Disproportionate.** The shallowest business claim requires the deepest machinery, and has no home of its own |
| **How it makes money (mechanisms)** | Same machinery — correctly | The filing's own words, genuinely: the provider label cannot carry this claim (see JPM below). Requirement is right; the *extraction path* fails on non-US document shapes and applicability rejections | **Proportional in principle; blocked by repairable extraction defects** |
| **Material segments** | Filing consensus | Filing consensus — established for VOW3 at 5/5 | **Proportional, works** |
| **Relative significance** | Filing consensus over checked cells | Same — 67.5/12.9/18.0 established | **Proportional, works** |
| **Financial characteristics** | Statement consensus (own stream, own quorum) | Same; unread for VOW3 (statements never acquired) — honest absence | **Proportional** |
| **Investor interpretation** (playbook, questions, quality) | Grounded understanding + models | The platform's own judgment, on its own deepest evidence — the JPM precedent below is the proof this must *not* soften | **Proportional; must stay strict** |

### The JPM altitude demonstration

For the *category* claim, every source agrees JPM is a bank: the
regulator's registry (SIC **6021 — National Commercial Banks**), the
provider ("Banks — Diversified", "operates as a bank and financial
holding company"). For the *playbook* claim, the platform's own reading
of the filing concluded **Diversified** — lending, services and
transaction lead together — and the owner refused the obvious repair.
Both claims are right **at their own altitude**. This is the
proportionality principle already instantiated in the platform's
history: a provider/regulator label is sufficient for "what is this,
broadly" and *insufficient* for "which questions should it be asked" —
and the reverse: demanding playbook-grade evidence for the broad claim
is the VOW3.DE defect.

The same pattern across the probes: DIS — SIC "Amusement & Recreation",
Yahoo "Entertainment", platform *Diversified*; UMI.BR — Yahoo "Waste
Management" (a category-adjacent mislabel), platform *Diversified* from
its own filing. Secondary labels agree with each other at category
altitude and are corrected by the filing at playbook altitude.
**Neither direction of the ruling's warning survives measurement as a
rule: "primary only" is wrong for category (it starves a claim five
surfaces corroborate), and "secondary suffices" is wrong for
understanding (Yahoo would have made JPM a bank playbook).**

### Coverage honesty for the cheap sources

The provider label is not free of failure: **6 of 12 sampled store
entries carry null sector/industry** (the Yahoo-401 degradation the
coverage run measured). A category claim built on corroboration must
treat the provider as one witness with an availability problem, not as
ground truth — which is precisely what the existing claims-pool
discipline (S1: agreement of independent sources, disagreement exposed)
already knows how to say.

---

## 4. Repair directions, weighed from the measurement

Ruled on by the CTO, not here. In the order the evidence supports:

1. **Repair the description acquisition for non-US document shapes**
   (the VOW3.DE extraction defect; reader-defects already names the
   pattern across 10 companies in two causes). This fixes the
   *mechanism* claim the right way — the filing's own words — and is
   the only repair that can ever ground VOW3's archetype. It does not
   fix the proportionality inversion: META fails the same rung by a
   different cause (applicability rejection), and the next German filer
   fails it again until read.
2. **Allow corroborated evidence of different authority for the
   category claim only, attributed, and connected to no selector.** The
   measured basis: the claim is multiply corroborated today for every
   focus company; the architecture already holds every needed piece —
   the owner-approved-but-unbuilt *provider description as labelled
   context* ruling, the `FactOrigin`/authority vocabulary, and the S1
   discipline for pooling claimants. The hard rule already on record
   stands: **it must never reach a playbook selector** — the JPM
   demonstration is the reason. What it may do is *word* the platform's
   honest state: "the provider describes an automotive group; this
   platform's own reading has established its segments and sizes but
   not yet how they earn."
3. **Changing the archetype prerequisites** (e.g. letting segment
   *names* — "Pkw" — carry mechanism evidence): measurable, but it
   blurs the category claim into the mechanism claim by inference in
   code, each name-rule would need corpus-earning, and it softens
   exactly the rung the JPM precedent says must stay hard. Not
   supported.
4. **Lowering the quorum**: refuted by the platform's own noise-floor
   measurement — prose readings agree 60–70%, and the consensus
   architecture exists because one draw was demonstrably not knowledge.
   The quorum is right for prose-derived claims; the finding is that it
   is *charged to claims that are not prose-derived* (a category
   corroborated across independent authorities) and to companies whose
   single reading is only awaiting spend, which is a budgeting fact,
   not an epistemic one.
5. **A new knowledge layer**: not supported. No measured distinction
   here exceeds what existing boundaries can represent — the category
   claim fits the already-accepted *labelled context* ruling plus the
   existing authority/origin vocabulary. Declaring a new layer would be
   the S3 mistake in reverse.

## 5. What can MOVRvest responsibly know about Volkswagen today?

From evidence it already holds or can read keyless, with the honest
abstention line drawn where the measurement puts it:

| Claim | Standing today | From |
|---|---|---|
| Identity: Volkswagen AG, German issuer | **Known** | eToro identity, LEI-verified document chain, GLEIF |
| It is an automotive group | **Knowable, currently refused** — corroborated by four agreeing surfaces, two of them already in-store | Provider label + description; the filing's own segment names; 80.4% of measured revenue in vehicle segments |
| Its material businesses | **Established, filing grade** | 3 segments, filer's own words, 5/5 |
| Their relative significance | **Established, filing grade** | 67.5% / 12.9% / 18.0%, checked cells, 5/5 |
| How each earns | **Not established — and the cause is this platform's reading scope, not the filing** | descriptions absent from the text read, 5/5 consistent |
| Archetype / playbook | **Correctly refused given the above** — the rule needs the mechanism vocabulary | `select_grounded` behaved as designed |
| Financial characteristics | Not read (statements never acquired) | honest absence |
| Investor interpretation | **Abstain** | nothing below it is complete |

The system should begin abstaining **at the mechanism rung** — and
today it abstains two rungs earlier, at the category, while
simultaneously *displaying* the deeper established rungs (the dossier
renders the segments and shares it refuses to draw the obvious word
from).

### The same boundary, contrasting companies

- **JPM** — every rung established; category sources agree "bank"; the
  platform's own deeper rung overrides at playbook altitude.
  Proportionality working end to end.
- **META** — quorate, segments sized; mechanisms lost to an
  *applicability rejection* rather than empty text. Same inversion as
  VOW3.DE, different extraction cause: category refused while deeper
  rungs stand.
- **TSLA** — every rung present in a single reading; blocked purely by
  quorum. The honest sentence is "one reading, four more to earn
  consensus", which is a spend statement, not an evidence one.
- **NFLX** — quorate, mechanisms known, weights unmeasured: refuses at
  the *significance* rung, correctly (a real evidence gap on sizes).
- **ADBE / PG** — single readings that established no segments at all:
  the ladder honestly stops at identity, and the category claim would
  rest on secondary corroboration alone — the case that bounds how far
  repair #2 may reach without primary support beneath it.

## 6. Answer to the research question

**Yes — filing-grade consensus has accidentally become the admission
ticket for basic business knowledge.** Not by design: each gate is
individually right (the quorum for prose noise, mechanisms for
archetypes, the archetype for playbooks). The defect is that the
*category claim has no home*, so it inherits the strictest path by
default, and the inheritance produces the measured absurdity — a
platform that knows, at 5/5 from checked cells, that 80.4% of
Volkswagen's revenue is vehicles, telling the investor it cannot
classify Volkswagen.

Nothing here proposes what to build. The CTO holds the ruling across
§4's directions; repair 1 (extraction scope) and repair 2 (attributed
category corroboration, selector-fenced) are the two the measurement
supports, and they are independent.
