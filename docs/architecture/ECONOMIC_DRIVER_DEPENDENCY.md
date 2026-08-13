# Does revenue diversity mean driver diversity? — measured, nothing built

**Status: research only, measured 2026-08-13 at `7528079` (post-E1).
Nothing in this document is a mandate to build, and no dependency
taxonomy, enum or score is created here** (Constitution §23–24, and the
ruling's own instruction: let recurring evidence shapes earn
vocabulary). E2 remains held.

The research question:

> Does MOVRvest distinguish what a business earns from the economic
> role that business plays inside the company — or does it confuse
> revenue diversity (revenue appears in several reporting segments)
> with economic-driver diversity (those revenues depend on meaningfully
> different underlying sources of demand)?

The finding, in one sentence: **the pipeline holds only the first
question's vocabulary — `RevenueModel` answers "how does this segment
earn" and nothing anywhere can hold "business A economically drives
business B" — while the corpus contains a filer that states the
dependence in a dedicated business-model sentence, a titled risk
disclosure, and a KPI, all of them now acquired or reachable and none
of them representable.**

---

## 1. Volkswagen: the dependency, measured from the issuer's own report

Every quote below is from `VWAGzusammengefassterLagebericht-2025-12-31`
(the package E1 made readable), located by search over the platform's
own flattened reduction — not recalled, not assumed.

**What VW itself says the relationship is** — a dedicated
business-model sentence:

> *"Das Geschäftsmodell des Konzernbereichs Finanzdienstleistungen
> liegt im Wesentlichen in der Vertriebsunterstützung für Produkte des
> Konzernbereichs Automobile."*
> ("The Financial Services division's business model consists
> essentially in sales support for the Automotive division's
> products.")

*Im Wesentlichen* — essentially — is the filer's own quantifier:
predominant, not total.

**What generates FS demand** — stated as a driver, in the filer's own
causal wording:

> *"Die Entwicklung der Fahrzeugauslieferungen an Kunden des
> Volkswagen Konzerns ist entscheidend und wesentlich für die
> Generierung neuer Aufträge für den Konzernbereich
> Finanzdienstleistungen."*
> (Vehicle deliveries are "decisive and material" for the generation
> of new FS contracts.)

**The dependence, disclosed under its own title** in the risk report:

> *"Abhängigkeit des Konzernbereichs Finanzdienstleistungen: Der
> Konzernbereich Finanzdienstleistungen hängt vom Absatz des
> Volkswagen Konzerns ab und jedes Risiko, das die
> Fahrzeugauslieferungen des Konzerns negativ beeinflusst, könnte sich
> nachteilig auf das Geschäft des Konzernbereichs auswirken."*

**The KPI is itself the relationship claim**: FS performance is
reported as the *Penetrationsrate* — the share of the Group's own
vehicle deliveries that FS finances or leases, 37.2% (34.1%), with
11.5m new contracts and a 30.0m-contract portfolio. A business whose
headline metric is penetration of the parent's product deliveries is
measured, by the filer's own choice, as an attached business.

**The extent — not assumed 100%, measured for the residue**: the FS
activity list is *"Händler- und Kundenfinanzierung, das Leasing, das
Direktbank- und Versicherungsgeschäft, das Flottenmanagement sowie
Mobilitätsangebote des Volkswagen Konzerns"* — dealer and customer
financing of Group vehicles, leasing, insurance, fleet management,
mobility, plus a direct bank. In 1.59M characters of report text:
*Direktbank* appears **five times, always inside that activity list**;
deposits (*Einlagen*) once, as treasury counterparty risk, never as a
demand story; **financing of non-Group brands appears zero times**
(*Fremdmarken*, *markenfremd*: no hits); Volkswagen Bank GmbH appears
as a *funding* vehicle (bond issuance, ratings). The filer offers no
independent-demand narrative for any FS activity. Contrast the other
captive in the corpus: Caterpillar's 10-K explicitly finances
"Caterpillar **and other** equipment" — a filer that *does* have
non-captive scope says so.

**The balance-sheet half of the dependence** — FS is exposed to the
same driver twice:

> *"…trägt der Konzernbereich Finanzdienstleistungen in der Regel das
> Risiko, dass der Marktwert der am Vertragsende veräußerten Fahrzeuge
> unter dem … vereinbarten Restwert liegt"* (residual-value risk on
> the Group's own vehicles), and dealer buy-back obligations:
> *"Der Konzernbereich Finanzdienstleistungen schließt regelmäßig
> Verträge ab, die Händler verpflichten, Fahrzeuge zurückzukaufen."*

### If Volkswagen stopped successfully selling vehicles, what happens to FS?

Evidence-backed, from the four disclosures above: **new contract
generation collapses** (deliveries are "decisive and material" for new
FS orders, and the dependence disclosure extends every delivery risk
to FS); **the 30.0m-contract portfolio runs off** over its terms with
nothing replacing intake — a penetration rate has nothing left to
penetrate; **residual-value losses amplify the same shock**, because
FS carries the market value of the used VW fleet against contracted
residuals, and a vehicle-demand collapse is exactly the scenario that
breaks them, at portfolio scale; the dealer buy-back book concentrates
the identical exposure. FS is not a hedge or a second engine — it is
**economically downstream of vehicle sales on the flow side and
leveraged to the vehicle fleet's value on the stock side**. The
independent residue (deposit-taking, some insurance float) is a
funding operation the filer nowhere presents as a demand source.

### The verdict on the 18%

**Mostly a different monetization layer around the same automotive
economic engine** — interest, lease and insurance margin on the same
vehicle transaction and ownership cycle — not a second engine.
"Predominantly downstream" is the filer's own framing (*im
Wesentlichen Vertriebsunterstützung*), and the evidence supports
exactly that: predominant, filer-stated, quantified by a penetration
KPI, with no evidenced independent demand stream and a small
unmeasured residue.

---

## 2. The intersegment row: quantified relationship evidence, already acquired

The tagged segment note — text the platform has read at 5/5 — prints:

| | Pkw u. leichte Nfz. | Nutzfahrzeuge | Finanzdienstleistungen |
|---|---|---|---|
| Umsatzerlöse mit externen Dritten | 217,299 | 41,517 | 57,853 |
| **Umsatzerlöse mit anderen Segmenten** | **27,185** | 1,022 | 4,283 |

The platform deliberately measures shares from the external row (the
correct arithmetic choice) and discards the intersegment row's
meaning: **€27.2bn of the Pkw segment's revenue is sales to other
segments** — overwhelmingly vehicles sold into FS's leasing book. The
internal flow *is* the captive mechanism, in the accounts, at checked
addresses, uninterpreted.

## 3. What the current contracts can and cannot represent

Traced field by field:

- `BusinessSegment` / consensus segment: name, description evidence,
  `revenue_models`, `revenue_share`. **No field can reference another
  segment.** `RevenueModel` is the answer vocabulary for "how does
  this segment earn" — `financial_spread`, `premiums` — and it is the
  *same* vocabulary for VW's captive as for BNP Paribas's actual
  banking. Nothing distinguishes them anywhere downstream.
- `BusinessUnderstanding` / `CompanyArchetype`: engine, mechanisms
  with support, contingencies. Inputs are (mechanism, share) pairs.
  `GROUNDED_PAIRS` can express *composition of the whole company*
  ("service business, then lender") — it cannot express a relation
  **between** two established businesses.
- So `business A → economically drives business B` is unrepresentable
  in every layer from observation to archetype, and therefore can
  neither be established, consensus-checked, nor rendered — while the
  filer states it in prose the platform can now reach (E1) and
  quantifies it in tables the platform has already read.
- Two path notes, measured: E1's passage cap **dropped** the two
  strongest role sentences for `Finanzdienstleistungen` (the
  business-model sentence and the dependence disclosure sit outside
  the 18k neighbourhood; the *Penetrationsrate* sentence made it in) —
  but even had they arrived, the extraction schema has no slot to
  receive a relationship claim. **The contract is the binding
  constraint, not the evidence path.**

## 4. Does the missing relation distort archetype selection today?

Measured, and the honest answer is: **not for any current corpus
outcome — the distortion today is in meaning, and the verdict risk is
latent.**

- **VOW3.DE**: the refusal is *not* caused by the missing relation.
  Counterfactual, in memory only (never stored): granting Pkw its
  manufacturing mechanism makes the unchanged engine read
  **single-engine — manufacturing at 89% → Industrial**. Share
  arithmetic alone already reaches the role-aware conclusion for VW —
  but on weaker grounds than the filer offers: 89% dominance happens
  to outweigh an 19% segment that the filer says is not a second
  engine at all. The two justifications agree here by arithmetic
  accident.
- **CAT** (specimen, schema-11 archive): Financial Products —
  `financial_spread, premiums`, the canonical captive ("The various
  financing plans offered by Cat Financial are designed **to support
  sales of Caterpillar products** and generate financing income",
  10-K) — is **6.2% of measured revenue and plays no part in the
  verdict**: CAT reads Diversified because manufacturing and services
  each cover 103.2%, co-riding the same three industrial segments.
- **The latent case is structural**: any filer whose captive exceeds
  the engine's lead/tie thresholds reads *multi-engine → Diversified*
  on revenue diversity alone — precisely the confusion this ruling
  names. No current corpus company sits there (VW's captive is 19%
  under an 89% engine; CAT's is 6%), so the distortion is a boundary
  waiting for a company, not a shipped wrong answer.
- **Where the confusion already shows**, two places: (1) the rendered
  meaning — VW's FS as "financial_spread, 18–19%" is indistinguishable
  in vocabulary from a bank's lending, the Zero Fake Meaning shape
  (an established number whose economic meaning is not established);
  (2) inside CAT's own verdict — "multi-engine — manufacturing,
  services lead together" reads two mechanisms as two engines when
  both ride the same machines, the same customers and the same
  installed fleet: mechanism diversity is not driver diversity even
  *within* one segment set.

## 5. The control: Disney, where independence is real

DIS (specimen): Entertainment, Sports, Experiences — subscription/
advertising/licensing vs sports rights vs park attendance and
merchandise. Measured contrasts with VW:

- Every stored description span is **self-contained** — no segment's
  description references another segment's products or demand.
- The filer states **no dependence disclosure and no penetration-style
  KPI** tying one segment's activity to another's output, in any
  evidence this platform holds.
- The demand sources are distinct economic activities: streaming
  subscription demand, advertising markets, sports-rights viewing,
  travel and park attendance.

Honest nuance, stated rather than hidden: Disney's franchises are a
shared *intangible* — content feeds parks and merchandise. That is a
complementarity around a common creative asset, not demand derivation:
Experiences does not exist "essentially in sales support" of
Entertainment, no risk section says park attendance depends on film
output, and nothing measures parks by penetration of streaming
subscribers. Calling any DIS segment "supporting" would destroy
meaning — which is exactly why the ruling forbids inventing a
taxonomy from one clear captive case: **VW and DIS are the two poles,
and the corpus between them (AAPL's geographic segments, which hide
driver structure entirely; TSLA's captive folded *inside* its
Automotive segment's own description; GOOG's semi-independent
engines) shows the shapes vary too much to name from one example.**

## 6. Answers to the ruling's questions

1. **Does MOVRvest distinguish what a segment earns from its economic
   role?** No. Question 1 has a vocabulary (`RevenueModel`) and a full
   evidence contract; question 2 has no representation anywhere, and
   the two are currently collapsed into one — the captive's
   `financial_spread` and the bank's are the same word.
2. **VW's FS**: predominantly downstream of the automotive core — the
   filer's own business-model sentence, dependence disclosure, driver
   sentence and KPI say so; the unmeasured independent residue is a
   funding-side operation with no evidenced demand independence. The
   18% is mostly a monetization layer, not diversification.
3. **Would representing the relation change VW's understanding without
   weakening standards?** It would not change the archetype *outcome*
   (Industrial arrives by arithmetic once Pkw grounds) — it would
   change the **grounds** and the **rendered meaning**: today the
   platform would say "Industrial because manufacturing is 89% of
   revenue"; the filer supports the stronger sentence "one automotive
   business system whose financial layer exists, in the filer's own
   words, essentially to support vehicle sales." Evidence standards
   would not weaken — the relation is *more* evidenced than most
   description claims (a dedicated sentence, a titled risk, a KPI, an
   intersegment row at checked addresses).
4. **Does the missing relation affect others materially?** Not in any
   current verdict (CAT 6.2%, immaterial; DIS genuinely independent;
   TSLA intra-segment; AAPL invisible behind geographic segmentation).
   It is latent for any future filer with a large captive, and it
   already shapes meaning wherever a captive's mechanisms render in a
   bank's vocabulary.

## 7. Recorded for whoever builds, deliberately without a proposal

- The strongest relationship evidence sits in **three already-reachable
  forms**: the filer's own role sentences (untagged prose, E1's scope —
  currently cap-dropped for exactly the longest sections), the
  dependence risk disclosure (a *titled* section), and the
  intersegment revenue row (tagged, read, discarded). No new source is
  needed; a slot is.
- E1's `named_passage` cap dropped the two strongest sentences for the
  one segment that needed them — any future slice that asks a role
  question must not inherit a passage budget tuned for description
  spans.
- The engine's "multi-engine" wording treats mechanism diversity as
  engine diversity (CAT), which is this same confusion one level down.
- A relation slot would need the same discipline as every claim here:
  filer-stated, span-evidenced, consensus-pooled — VW shows it can be
  (its sentence is as quotable as any description), and DIS shows the
  *absence* of a relation must remain the representable default, never
  an inferred "independent" label.
