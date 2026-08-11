# Hermetic Evidence Execution

**Status: accepted, built.** The invariant:

> Given the same declared evidence inputs, analytical execution produces
> the same result regardless of developer-local caches or machine state.

Caches may accelerate acquisition. **Caches may not silently become
undeclared analytical inputs.**

---

## 1. What the five failures had in common

Five separate times across the crypto work, a test read evidence that
existed on the developer's machine and not in a clean checkout. Each one
looked like a test-writing mistake. They were the same architectural
mistake, and it is not about caching at all:

> **An analytical call declared a *subject* and never an *evidence
> set*.**

`committee.judge("ADA")`, `committee.evidence("ETH")`,
`service.for_asset("TAO")` — every one takes an identifier. The service
then resolved its own evidence by defaulting a dependency to a path
literal relative to the process's working directory. Seventeen such
literals existed:

```text
data/cache/protocol_facts     data/cache/issuance_rules
data/cache/primary_supply     data/cache/coingecko_facts
data/cache/token_facts        data/cache/crypto_market
data/cache/crypto_events      data/cache/etf_flows
data/cache/ratings            data/cache/quotes
data/cache/fundamentals       data/cache/earnings
data/cache/sentiment          data/cache/fx
data/journal                  data/judgments
data/evidence
```

Every one correct in production. Every one an undeclared input
everywhere else.

**Measured, not argued.** Editing one field of
`data/cache/issuance_rules` flips Cardano's supply-governance verdict:

```text
ADA verdict, real cache:      governance_set
ADA verdict, poisoned cache:  consensus_bound
```

The caller was `SupplyGovernanceCommittee()` — no evidence declared at
all.

**And the reading half was not the whole of it.** Running the suite was
observed *creating* `data/cache/fx` in the developer's own tree. Tests
were mutating the state they were accidentally reading.

---

## 2. The seam

The conftest already **was** the hermetic boundary — it silences
credentials so a unit test cannot spend money, and blocks the wire so a
keyless provider cannot spend a rate limit. It was missing one
dimension: the filesystem.

So the fix is one owner for the root and one more guard in the place
that already holds the other two.

`app/infrastructure/evidence_root.py` — `evidence_root()` and
`evidence_path(*parts)`, reading `MOVRVEST_EVIDENCE_ROOT` and defaulting
to `data`. Every store and cache builds its default from it:

```python
JsonCache(evidence_path("cache", "issuance_rules"), schema=SCHEMA)
```

The test suite points that variable at a fresh temporary directory per
session. A test that forgets to supply fixtures now reads an *empty*
store and says so, rather than reading a machine.

**Resolved at construction, never in a signature.** Ruff caught three
stores defaulting `root=evidence_path("journal")` in the parameter list
— evaluated once at import, which would freeze the location and ignore
every later redirection. That is the same class of bug as the one being
fixed, and the fix is the same: ask, do not assume.

**This is not a cache switch.** Caching is unchanged and production
reads exactly what it read before, verified by running the surfaces
after the change.

---

## 3. What now constitutes a declared evidence input

The seam was already latent: every analytical service takes its evidence
door as a constructor argument, and the tests that got it right were
already using it. What changed is that the *ambient* alternative is no
longer reachable by accident.

```text
declared     SupplyGovernanceCommittee(issuance=<a door you supplied>)
             InvestorAssessmentService(supply=..., matrix=...)
             ValueCaptureCommittee(protocol=..., journal=...)

production   the same constructors, handed the stored doors explicitly —
             CachedIssuanceRuleProvider.stored(), and the services the
             registry builds

test         fixtures, and an evidence root that is a temporary
             directory whatever else happens
```

Four behavioural tests hold the line, each building a *genuinely
readable* poisoned cache first — a stub that merely looked like a cache
would prove nothing:

1. a poisoned cache cannot alter a fixture-backed **verdict**;
2. a poisoned cache cannot alter a fixture-backed **assessment**;
3. the stored path, deliberately selected, **does** participate — the
   guarantee is *declared wins*, not *nothing works*;
4. a committee given an empty door **abstains** rather than hunting.

Plus an AST guard: no module outside `evidence_root.py` may name an
evidence directory in code. Docstrings are exempt — describing the
layout is not depending on it.

---

## 4. Historical judgments: auditable, not reproducible

The ruling asked whether an existing historical judgment can be
explained without today's cache. Measured against `JudgmentRecord`:

```text
carried      evidence_digest, evidence_count, refs,
             committee identity + version + fingerprint,
             applicability, state, verdict, confidence, because
not carried  what the findings actually said
```

So the honest answer is:

- **We can always say that the evidence changed**, and #113's
  `EvidenceMovement` is exactly that comparison. That does not depend on
  any cache.
- **We cannot reconstruct what the committee saw.** The digest is
  one-way and the finding sentences are not stored.

**Auditable, not reproducible.** That is not a deficiency for *this*
invariant — history is not an analytical input, and nothing in the
replay path reads a cache — so history is unchanged and remains
append-only. It is a real limit on a different question, and it is
recorded here rather than fixed.

---

## 5. `MATERIAL_SPREAD` stays provisional

The 25% constant from PR #117 is **not** a general definition of
investor materiality and nothing should treat it as one. The corpus
already shows that what a spread *means* depends on context: Bittensor's
two circulating readings 9.9% apart form a useful bound, while
Hyperliquid's much larger span matters partly because one reading
exceeds the protocol maximum — a fact about the *kind* of disagreement
rather than its size. Future materiality may belong to the quantity or
the question rather than to one global threshold. No decision is taken.

---

## 6. Acquisition debt after this fix

- **There is still no shared notion of "acquired for committee N".**
  Unchanged from PR #116: Fee Capture reads a stored protocol door,
  Supply Governance reads a cached issuance door, and `movrvest acquire`
  fills neither. This slice makes the dependency *explicit*; it does not
  orchestrate it. The acquisition orchestrator remains a separate slice
  and this work did not prove it inseparable.
- **`data/` is one root with mixed tenancy.** Acquisition caches
  (regenerable), append-only records (`journal`, `judgments`) and
  tracked knowledge all hang from it. Redirecting the root redirects all
  three together, which is right for tests and coarse for anything else.
- **A clean checkout still has no evidence.** That is by design —
  acquisition is an explicit spend — but it means the corpus surfaces
  are empty until `movrvest acquire`, `observe` and `judge` have run.
