# The research plan — what stands between INVESTIGATE and capital

**Status: accepted and built.** `INVESTIGATE` ended in a description of
missing evidence. This layer turns it into a closed plan: one
requirement per decision-critical blocker, each naming what is missing,
what would resolve it, and — the part the product was missing —
**whether MOVRvest can do anything about it**.

---

## Stage 0 — measured before anything was built

Stored evidence only: no provider call, no model, no acquisition, no
funded cycle, no store mutation. Eight assets.

### 1. The blocker set is reproducible from three typed sources, exactly

The decision's own blocker count (`unresolved` + `material_uncertainties`)
is reproduced **8 of 8** by:

1. committee assessments in a blocking state — `unavailable`, or
   abstained because `insufficient_evidence` / `applicability_unestablished`;
2. assessment statements whose shape is `UNCERTAIN`;
3. `assessment.silent_about` **minus** `silent_committees`.

| | committee | uncertain | silent | derived | decision |
|---|---|---|---|---|---|
| BTC | 0 | 0 | 0 | 0 | 0 |
| ETH | 1 | 0 | 1 | 2 | 2 |
| ADA | 1 | 0 | 0 | 1 | 1 |
| SOL | 0 | 0 | 1 | 1 | 1 |
| HYPE | 1 | 2 | 0 | 3 | 3 |
| TAO | 2 | 0 | 0 | 2 | 2 |
| ARB | 1 | 1 | 0 | 2 | 2 |
| 1INCH | 0 | 0 | 0 | 0 | 0 |

Three findings forced that shape:

- **`silent_committees` is a documented subset of `silent_about`**, so
  subtracting it is a typed dedup rather than a name match. TAO forces
  it: its two silent subjects *are* its two committees, and counting
  both gave 4 where the decision carries 2.
- **A silent non-committee subject is its own blocker.** ETH and SOL are
  silent about *Maximum supply* and no committee is, which is the entry
  the first derivation missed.
- **`not_economically_applicable` is never a blocker.** BTC's Value
  Capture committee abstains on it and BTC has no blockers. A question
  that is the wrong instrument for an asset is answered, not blocked.

### 2. Not one watch item resolves any blocker — anywhere

**7 blockers, 10 watch items, 0 connections**, corpus-wide.

The two vocabularies cannot meet by construction. A blocker's refs are
source names (`CoinGecko`, `Hyperliquid info API`) and committee keys
(`supply_governance`); a watch item's are metric refs
(`network.fees.hyperliquid-protocol`, `flow.30d`) and event ids.

So HYPE's fee-economy item standing beside three unrelated supply
blockers was **not a HYPE defect** — it was the corpus-wide state, and
every one of the ten items was an orphan. A requirement is therefore
derived from **the blocker**; a watch item is contextual evidence that
resolves nothing, and it stays under Developments where it already
rendered.

`brief.would_change_view` was removed for the same reason: every entry
it could ever carry is an orphan.

### 3. `IssuanceRuleProvider.rule()` conflates two opposite claims

It is a hard-coded `BTC`/`ADA`/`SOL` allowlist that returns a bare
`None` for everything else, and its docstring reads that `None` as *an
allocation-release token… there is no rule to read*.

**The corpus falsifies that.** TAO's own developments record
*"Bittensor (TAO) First Halving Reduces Block Rewards and Daily
Issuance"* — a mechanical rule plainly exists — while `rule("TAO")`
returns `None`.

So `None` means only *this platform has not read one*. **Absence of a
rule and absence of a reader are opposite claims**, and until the
provider distinguishes them nothing may say which it is. A test asserts
the plan never claims *allocation-release*, *no rule exists* or *does
not have*.

### 4. The distribution of what MOVRvest can actually do

| next step | count |
|---|---|
| `NOT_CURRENTLY_RESOLVABLE` | 6 |
| `CONVENE_COMMITTEE` | 1 (ADA) |

**Six of seven blockers have no executable path.** That is the honest
content of the plan, and the brief anticipated it: *a token with no
executable research path says so rather than manufacturing activity*.

`NextStepKind` therefore declares **two members, not six**. The brief
offered `NEXT_COMPARABLE_OBSERVATION`, `RECONCILE_HELD_EVIDENCE`,
`TARGETED_PRIMARY_RESEARCH`, `OWNER_RULING` and `CAPABILITY_MISSING`;
the corpus produces none of them, and this repository's standing rule is
that a vocabulary member is observed before it is named. What each would
need:

- **`NEXT_COMPARABLE_OBSERVATION`** — a blocker whose resolution is a
  repeat reading of a figure already acquired. None exists: the only
  repeat-reading items are watch items, and they resolve nothing.
- **`RECONCILE_HELD_EVIDENCE`** — a supply conflict where *every*
  source discloses its exclusions. HYPE's circulating estimate has 3 of
  4 undisclosed, ARB's 2 of 2, HYPE's emitted supply 1 of 2. The flag
  exists (`SupplyMethodology.disclosed`) and no live conflict clears it.
- **`TARGETED_PRIMARY_RESEARCH`** / **`CAPABILITY_MISSING`** — both need
  the issuance provider to distinguish *no rule* from *no reader*.
- **`OWNER_RULING`** — needs a blocker whose resolution is a policy
  decision. None is currently typed as such.

---

## What was built

`app/api/models/crypto_research_plan.py` — `ResearchRequirement`,
`ResearchPlan`, `NextStepKind`. Communication, not the CIO: it reads a
decision already made and explains it.

**Every sentence belongs to the layer that established it.** What is
missing is the committee's `because` or the assessment's `uncertainty`;
why it matters is a `LicensedMeaning` or the committee's own question.
The counts in *"3 of 4 sources publish no exclusion set"* are counted
from `SupplyMethodology.disclosed`, never parsed from prose.

**Two duplications the live render caught.** `resolution_needed` was
`f"An answer to: {cell.question}"` while `why_it_matters` was the same
question — the same sentence twice in one row. And the next-step
sentence repeated the *"a statement about this platform, not the
protocol"* qualifier that the quoted `what_is_missing` already carried.
Both are gone.

## What it never says

No cadence, no sufficiency threshold, no completeness figure, no score,
no progress. No *"MOVRvest will monitor / will research / will alert"*.
No button, because no workflow is reachable from a page view.
Resolving a requirement licenses **reconsideration and nothing more**,
and the sentence saying so is rendered verbatim.

## Measured surface

HYPE, the worst case at three requirements:

| | before | after | target |
|---|---|---|---|
| desktop 1440×900 | — | **1,760px** | ≈1,800 ✅ |
| mobile 375×812 | — | **3,486px** | ≈3,000 ⚠️ 16% over |

First desktop viewport carries identity, quote, course, readiness and
the principal blocker. Zero open disclosures, zero buttons.

The mobile overage is recorded rather than hidden: closing it costs a
metric's provenance, one of the three developments, or the exposure
receipt wording, and the brief forbids removing those merely to meet the
number.

## Corpus controls

- **BTC** — 0 requirements, stated absence, and **no HYPE issuance
  wording**.
- **TAO** — 2 requirements, both *economic role not established*; supply
  conflicts preserved and no negative-quality word anywhere.
- **ADA** — 1 requirement, `CONVENE_COMMITTEE`, retryable. The one asset
  MOVRvest can act on today.
- **1INCH** — sparse: 0 requirements and a stated absence, not empty
  shells.
- **ETH** — 2 requirements, one of them its *own* committee's *"no
  mechanical issuance rule is held"*, which is ETH's sentence and not
  HYPE's leaking.

## Recorded, not solved

- The issuance provider's `None` still conflates two claims. Fixing it
  is the prerequisite for three of the five undeclared next-step kinds.
- `NextStepKind` has no member for *an owner ruling would resolve this*
  because nothing is typed that way.
- The plan reads the committee matrix, the assessment and the supply
  picture. There is no shared notion of *acquired for a requirement*,
  and this layer must never acquire.
