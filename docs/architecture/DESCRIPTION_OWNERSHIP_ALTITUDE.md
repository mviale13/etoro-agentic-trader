# DA1 — Hierarchical Business Description Ownership: the research step, and why the slice stopped there

**Status: research only, measured 2026-08-13 at `3c57413`. DA1 was not
built, and this document is the reason** (requirement 11 of the ruling,
and Constitution §23–24). Harness: `tools/description_ownership.py`
(read-only, one network fetch, no model call — delete when the ruling
lands). Every quote below was located by search over the platform's own
flattened reduction of the issuer's own package; none is recalled.

The ruling scoped DA1 on a premise:

> Volkswagen does describe its automotive activities. The description
> exists at a different filer-defined organizational altitude
> (`Konzernbereich Automobile` / related brand-group/business-area
> structure), rather than under the exact reportable-segment label
> expected by the current ownership partition.

**The document refutes that premise.** Volkswagen describes
`Pkw und leichte Nutzfahrzeuge` under `Pkw und leichte Nutzfahrzeuge` —
in a dedicated sentence, in the filer's own words, at the exact
reportable-segment altitude the current partition expects. The
description is refused for a different reason entirely, and hierarchical
ownership would not reach it.

So the mandated research step ran to completion and the code step did
not start. What follows is the measurement, in the order the ruling
asked for it.

---

## 1. The filer-defined hierarchy — found, explicit, and quotable

The ruling asked for the hierarchy to be established from the document
rather than inferred. It is there, three times, in explicit containment
and correspondence verbs:

> **"Seit dem Geschäftsjahr 2025 umfasst der Konzernbereich Automobile
> die beiden berichtspflichtigen Segmente Pkw und leichte Nutzfahrzeuge
> sowie Nutzfahrzeuge."**
> *(Since financial year 2025 the Automotive division **comprises** the
> two reportable segments Passenger Cars and Light Commercial Vehicles,
> and Commercial Vehicles.)* — flat offset 330,007

> **"Der Konzernbereich Automobile umfasst dabei das Segment Pkw und
> leichte Nutzfahrzeuge, das Segment Nutzfahrzeuge, die sonstigen
> operativen Gesellschaften, die nicht allokierte Konzernfinanzierung
> und die Holdingfunktion."** — flat offset 403,397

> **"Der Konzernbereich Finanzdienstleistungen entspricht dem Segment
> Finanzdienstleistungen."**
> *(The Financial Services division **corresponds to** the Financial
> Services segment.)* — flat offset 331,017

So the hierarchy is:

```text
Volkswagen Konzern
    ↓ "Das Geschäftsmodell des Unternehmens umfasst die Konzernbereiche…"
Konzernbereich Automobile ─────────── Konzernbereich Finanzdienstleistungen
    ↓ "umfasst … das Segment"                    ↓ "entspricht dem Segment"
Pkw und leichte Nutzfahrzeuge                Finanzdienstleistungen
Nutzfahrzeuge
(+ sonstige operative Gesellschaften, Konzernfinanzierung, Holding)
```

**Requirement 11's escape clause is therefore *not* what stopped this
slice.** Hierarchical applicability is provable for VOW3.DE from
explicit issuer structure. It stopped for a stronger reason: the
hierarchy is not needed, and using it would be worse than not using it.

Note the third statement's shape, recorded because it matters for any
future hierarchical rule: `Konzernbereich Automobile` **contains two
segments plus three non-segment items**, while
`Konzernbereich Finanzdienstleistungen` **corresponds one-to-one** with
its segment. *Comprises* and *corresponds to* are different relations
and a rule that treated them alike would be wrong about one of them.

---

## 2. The description exists at the exact segment altitude

Immediately after the first hierarchy statement, the filer writes:

> **"Im Segment Pkw und leichte Nutzfahrzeuge werden im Wesentlichen die
> Pkw-Marken sowie die Marke Volkswagen Nutzfahrzeuge des Volkswagen
> Konzerns konsolidiert. Schwerpunkte der Geschäftstätigkeit sind die
> Entwicklung von Fahrzeugen, Motoren, Fahrzeugsoftware und -batterien,
> die Produktion und der Vertrieb von Pkw […] und leichten
> Nutzfahrzeugen sowie das Geschäft mit Originalteilen."**

That is a description of the business, under the segment's own name,
naming development, production, distribution and the original-parts
business. It is exactly the evidence the archetype engine is missing —
and it is *not* at a parent altitude.

Run through production's own ownership machinery
(`namings()` + `describes()`, unmodified):

| Candidate span, under the segment's own name | Verdict today |
|---|---|
| what the segment consolidates (`Im Segment … werden … konsolidiert`) | **ACCEPTED**, 0 chars from the naming |
| **what the business does** (`Schwerpunkte der Geschäftstätigkeit …`) | **REFUSED** — "prints under `'Nutzfahrzeuge'`" |
| the parts business | REFUSED |
| the product portfolio | REFUSED |

The one sentence that carries earning mechanisms is refused. The one
that is accepted says only which brands are consolidated — no way of
earning — which is why the stored consensus holds a 5/5 unanimous
*size* for this segment and zero mechanisms.

---

## 3. The actual defect: a brand name read as a segment naming

The refusal is character-precise and reproducible. Inside the segment's
own description passage the partition finds exactly one interrupting
naming:

```
at 330235: read as a naming of 'Nutzfahrzeuge'
   …werdenimwesentlichendiepkwmarkensowiedie|markevolkswagennutzfahrzeuge|desvolkswagenkonzernskonsolidiert…
```

That is **"die Marke Volkswagen Nutzfahrzeuge"** — the *brand*
Volkswagen Commercial Vehicles — inside a sentence whose subject is the
Passenger Cars segment. The filer is saying *this segment consolidates
the passenger-car brands **and** the VW Commercial Vehicles brand*. The
partition reads the brand mention as the document turning to speak about
the sibling **segment** `Nutzfahrzeuge`, so every following sentence —
including the only one that says how the business earns — is attributed
to the sibling and refused for the 75.9% segment.

**The counterfactual isolates it exactly.** Remove that single naming
and change nothing else:

| Span | Today | Brand naming removed |
|---|---|---|
| what the segment consolidates | ACCEPTED (0) | ACCEPTED (0) |
| **what the business does** | **REFUSED** | **ACCEPTED (127 chars)** |
| the parts business | REFUSED | REFUSED — 321 chars, beyond `NEARBY` |
| the product portfolio | REFUSED | REFUSED — 354 chars, beyond `NEARBY` |

One naming is the whole blocker for the mechanism-bearing sentence. The
other two stay refused on **distance**, and that is the proximity
contract working as designed — `NEARBY = 300` is untouched here and
should stay untouched.

This is not an altitude defect, not a hierarchy defect, and not a
semantic-matching gap. It is a **homonym defect in the positional
partition**: a longer phrase that is not one of the company's segments
(`Marke Volkswagen Nutzfahrzeuge`) contains a segment's name
(`Nutzfahrzeuge`) and is counted as naming it.

The existing nesting guard does not catch it and was never meant to.
`Naming.covers()` suppresses a *segment* naming swallowed by a longer
*segment* naming — its docstring cites this very company. Here the
swallowing phrase is a brand, which is not in the partition at all, so
there is nothing to do the covering.

The corpus scale of the collision, in this one document: **`Volkswagen
Nutzfahrzeuge` appears 14 times**, `Marke Volkswagen Nutzfahrzeuge`
twice, `Nutzfahrzeugmarken` twice — every one of them currently a
naming of the reportable segment.

---

## 4. Why building DA1 would not have fixed Volkswagen — and would have hurt

Three reasons, each measured rather than argued.

**It does not reach the blocked sentence.** The blocked description is
owned by the segment, not by the parent. A hierarchical path adds a
*second* way for a parent-altitude description to reach a child; it does
nothing about a child-altitude description being mis-partitioned to a
sibling. VW's 75.9% segment would stay unexplained and the corpus
verdict would stay `too-little-explained` at 32.5%.

**The description it would carry is the same passage — and carrying it
wholesale is the hazard the ruling itself named.** The parent-altitude
account of `Konzernbereich Automobile` covers both segments, and the
sibling's own sentence ends *"sowie damit in Zusammenhang stehende
Dienstleistungen"* (…and related services). Inheriting the parent's
mechanism set to the passenger-car segment therefore attaches `services`
to 75.9% of revenue. That is precisely the case the ruling forbade
("Attaching all three indiscriminately … can make `services` ride the
same revenue repeatedly and produce a worse archetype"), and the
previous experiment measured the consequence: VW then reads **Service
business**, or **Diversified** under role-aware exclusion — never
Industrial
([`ROLE_AWARE_ARCHETYPE_MEASUREMENT.md`](ROLE_AWARE_ARCHETYPE_MEASUREMENT.md)
§3).

**No corpus company needs it.** Every other company at quorum describes
its segments under their own names — DIS, JPM, CAT, NVDA, UMI.BR and
BNP.PA all already establish mechanisms that way, and none of their
segment names is nested inside a sibling's. A hierarchical ownership
path would ship as machinery with one intended beneficiary that it does
not benefit.

---

## 5. The corpus controls

Nothing was built, so nothing moved. Recorded as the ruling asked, with
the structural check that matters for whichever slice comes next:

| Company | Segments | Nested names? | Description path today | State |
|---|---|---|---|---|
| **VOW3.DE** | Pkw und leichte Nutzfahrzeuge, Nutzfahrzeuge, Finanzdienstleistungen | **yes** — `Nutzfahrzeuge` ⊂ `Pkw und leichte Nutzfahrzeuge` | exact-altitude, one sentence refused by a brand homonym | **blocked**, diagnosed |
| DIS | Entertainment, Sports, Experiences | no | self-contained, exact altitude | stable, 5 mechanisms |
| JPM | CCB, CIB, AWM | no | exact altitude via the abbreviation rule | stable |
| CAT | Construction, Resource, Power & Energy, Financial Products | no | exact altitude | stable |
| NVDA | Compute & Networking, Graphics | no | exact altitude | stable |
| BNP.PA | CIB, CPBS, IPS, Other Activities | no | exact altitude | stable |
| UMI.BR | Battery Materials, Catalysis, Recycling, Specialty Materials | no | exact altitude | stable |

**VOW3.DE is the only company in the corpus with nested segment names,
and the only one with the homonym exposure.** That is a reason to fix
the partition carefully — not a reason to call it a Volkswagen rule: the
shape is a filer naming a brand after one of its own segments, which is
ordinary corporate practice and will recur.

**BNP.PA — the `services` co-tag control.** No hierarchical description
ownership occurs there: all three segments are described under their own
names, and `services` covers 102.8% because each segment genuinely earns
that way, not because a description travelled. DA1 would not have
touched it, and the co-tag problem it exhibits is the separate defect
already recorded in the previous ruling. **Unchanged.**

---

## 6. Delivery report

1. **The filer-defined hierarchy** — found and explicit: §1, three
   verbatim statements with offsets, including the *comprises* /
   *corresponds to* distinction.
2. **The parent/child applicability evidence** — present and quotable,
   and **not required**, because the child describes itself.
3. **What could legitimately travel** — nothing needs to. The
   mechanism-bearing description is already owned by the measured
   segment at its own altitude.
4. **What could not travel and why** — the parent's mechanism set, which
   spans both automotive segments and would attach the sibling's
   `services` to 75.9% of revenue (§4). Two further sentences stay
   refused on the unchanged 300-character proximity bound.
5. **Business Understanding before → after** — **identical**. Nothing
   was built; `Pkw und leichte Nutzfahrzeuge` still carries a unanimous
   5/5 size and no mechanism.
6. **Unchanged archetype engine before → after** — **identical**:
   `too-little-explained`, 32.5% against the 0.50 floor, "Not
   classified". The threshold was not touched.
7. **Controls** — §5; all stable, none needed the new path.
8. **The `services` co-tag problem** — **unchanged**. Not made better
   (nothing was built) and not made worse. Recorded: had DA1 shipped as
   scoped, it would have made it *worse* for VW specifically.
9. **Blocked by model funding** — the reader-dependent half. Confirming
   *which* `RevenueModel`s the accepted sentence yields requires a real
   asked reading, and the account is still credit-blocked. This document
   deliberately does **not** assign mechanisms to that sentence: naming
   them from *"Entwicklung … Produktion … Vertrieb … Originalteile"*
   myself would be exactly the `segment name → RevenueModel` inference
   requirement 9 forbids, one level down. What is established is that
   the sentence is a *description of this segment* and is currently
   refused; what it establishes about earning is for the reader to say.
10. **Production CIO route untouched** — no production file was
    modified. `git status` shows two additions only: this document and
    `tools/description_ownership.py`. No `app/` module, no store, no
    `data/` file, no test, no frontend file. Full suite, ruff and mypy
    green at HEAD, unchanged from `3c57413`.

---

## 7. What the evidence supports next — for ruling, not for building

The smallest change that would unblock Volkswagen is **not** hierarchical
ownership. It is a sharpening of the existing positional partition:

> A phrase the document prints as part of a longer proper name that is
> not one of the company's own segments is not a naming of that segment.

That is one rule, in `namings()`, in the module that already contains
the nesting guard for the same company. It **strengthens** ownership
rather than weakening it — requirement 10 is served, not strained: it
removes false namings, and every span still has to be printed, still has
to sit under the segment's own naming, and still has to be within 300
characters of it. `NEARBY`, `ENOUGH_EXPLAINED`, span existence, source
identity and the structural-heading path are all untouched.

Three things that would have to be measured inside that slice, recorded
now so they are not discovered late:

- **How the brand is recognised without a company-specific rule.** The
  candidate is structural — a segment naming that is part of a longer
  capitalised proper-name phrase in the document's own casing — and it
  must be measured against the whole corpus, because a rule that
  suppressed *real* namings would cost sound descriptions elsewhere.
  The flattened text this partition runs over is casefolded, so the
  evidence for "longer proper name" has to be read from the original
  casing, which the `_indexed` origins already preserve.
- **Whether it is a schema event.** It changes *how already-established
  evidence is interpreted*, not what a reading is shown or asked. Under
  the store's own precedent that is the case that needs the most care:
  old observations must not silently acquire a stronger ownership
  relationship than the contract that produced them allowed. The honest
  reading is that the *refusals* stored in schema 12 were correct under
  schema 12's partition, so a re-read is required rather than a
  reinterpretation of stored text.
- **What the archetype then says, reported and not tuned.** With the
  sentence accepted, the reader may establish manufacturing and
  distribution for 75.9% of revenue — or it may establish something
  else. The previous measurement says the verdict swings between
  Industrial, Service business and Diversified depending on whether
  `services` comes with it, and **that outcome must be reported as
  evidence for the next ruling rather than designed for**.

The §23 sentence this would complete:

> *After this change, the investor can see what kind of business
> Volkswagen is — today the platform holds a unanimous size for 76% of
> its revenue, holds the filer's own sentence describing that business,
> and reports that it understands 33% of the company.*
