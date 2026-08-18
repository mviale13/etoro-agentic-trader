# A ticker is not an issuer, and it is not an issuer *for ever*

**Status: built. Repair 2 of the two the owner ordered, independent of
repair 1. No model call, no acquisition, no production data mutation, no
schema bump, no backfill, and no band, statement, consensus or decision
moved.**

PR #190 found this before it found anything it was looking for:

> **`PARA` resolves to Banzai International.** Paramount Global was
> acquired and delisted, the SEC reassigned the ticker, and a harvest
> keyed on it returned **seven Item 5.02 filings belonging to another
> company**. Every filing was genuine, every date was real, the
> regulator received all of it — and none of it was about the company
> the reader asked for.

Invariant 2, on its third recorded occasion: *identity is enforced
before the reading, and a perfectly grounded, exactly cited reading of a
genuine filing is still wrong when the filing is another company's.*

---

## 1. The axis that was missing

`app/domain/provider_identity.py` already exists and already answers the
harder-sounding question: whether **two providers** describing a symbol
are describing the same instrument. Its own docstring names the failure
this repair is about and does not address it —

> *"Symbols are venue-local, reused across venues and **reassigned over
> time**"*

— because it compares two claims made *now*. The missing axis is
**time**: one register, one symbol, two moments, two companies.

So this is not a second identity module competing with the first. It
compares a dated claim against a dated claim, and it is the only thing
here that does.

## 2. No new field, no schema bump, no backfill

The guarantee cost nothing to apply retroactively, because **every
source this platform has ever held already carries the issuer's registry
number inside the address it was fetched from**:

```text
https://www.sec.gov/Archives/edgar/data/4962/000000496226000080/axp-20251231.htm
                                        ^^^^
```

`issuer_id_in(location)` reads it. A record taken before this existed is
exactly as protected as one taken after, and `data/statements` was not
touched — its fingerprint is unchanged.

Two details the corpus forced:

- **Leading zeros are presentation.** EDGAR prints the same filer as
  `4962` in an archive path and `0000004962` in an accession. Two
  spellings of one number must not read as two issuers.
- **An address this cannot parse yields no claim**, not a guess. A
  guess is the failure being guarded against.

## 3. The rule

`reconcile(held, resolved)` returns nothing and raises `IssuerReassigned`
on conflict. There is no third outcome worth expressing: either the two
readings agree about the issuer, or the platform stops.

**It resolves nothing and prefers nothing.** Where two dated claims
disagree, the disagreement is raised — never settled by taking whichever
was read most recently, because preferring the newer one is exactly how
a reassignment becomes a silent substitution.

Three deliberate non-refusals, each with a reason:

| | why it does not raise |
|---|---|
| nothing held | a first reading has nothing to disagree with |
| two different registers | SEC's `1159508` and an LEI number the same company; comparing across registers would raise on every provider change, which is noise |
| an unreadable held address | no claim on one side means the symbol is honestly **unguarded**, and refusing there would block every non-EDGAR provider |

**The limit is stated rather than hidden.** This catches a symbol
changing hands *between* two readings. It cannot catch a symbol that was
already pointing at the wrong issuer the first time it was read.

## 4. Where it sits, and the hazard in wiring it

At `PrimarySourceResolver.resolve`, **before the document is fetched and
before anything reads a word of it**. Every path that opens a filing —
statement acquisition, knowledge acquisition, `statement-shape`,
`statement-audit`, and any future development or leadership reader — is
covered by one check rather than each remembering to make it.

The resolver's own shape created the hazard. It asks each provider in
turn and collects each failure into `reasons` so it can report a
coverage gap honestly. Had the guard raised a `PrimarySourceUnavailable`,
**a reassignment would have fallen through to the next register and
served the wrong company's filing anyway**. So:

- `IssuerReassigned` is **not** a subclass of `PrimarySourceUnavailable`
  — asserted by a test, because a caller that treated "no source" and
  "two different companies" alike would word a reassignment as a company
  this platform does not cover, which is the opposite of what happened;
- it **propagates** out of the provider loop rather than joining
  `reasons` — asserted by a test that gives the resolver a second
  provider and proves it is never asked.

The held identity arrives as a callable, so the resolver stays a
provider seam and does not learn how evidence is kept. It is bound at
construction rather than frozen at import — the rule `evidence_root`
earned.

**Which held identity, where several exist:** the **newest** filing. A
symbol that changed hands legitimately, and was re-read under the
operator's own direction, settles on the identity it most recently
accepted. Comparing against the oldest would leave a company
permanently refused for a change already accounted for.

## 5. Measured

### It refuses the case that was actually observed

```text
PARA does not denote the same issuer it did when this platform last read
evidence for it. Held: PARA denoted Paramount Global (SEC EDGAR 813828)
as of 2024-01-01. Resolved now: PARA denoted Banzai International, Inc.
(SEC EDGAR 1826011) as of 2025-07-09. A ticker is reassigned when a
company is acquired or delisted, so the two readings are both honest and
describe different companies — and this platform cannot tell which one
was meant.
```

### It disturbs nothing live

Every one of the 24 companies whose statements this platform holds,
resolved through the guard against its own held identity:

| | |
|---|---|
| resolved | **24** |
| refused | **0** |
| unavailable | **0** |

Every one produced a real held issuer number from its stored address —
AAPL `320193`, AXP `4962`, KO `21344`, MUFG `67088` — so the guard is
not passing by finding nothing to compare.

## 6. Scope compliance

Repair 2 of 2, branched from `main` independently of repair 1 · no
Management Continuity work, no `LeadershipEvent`, no event contract, no
continuity state · no Company Development Radar work · no model call ·
no acquisition · no production data mutation · no schema bump and no
backfill · no band, factor, threshold, recipe, vocabulary, playbook,
financial-model, committee, CIO or decision change.

Gates: **3,090 tests pass** (3,078 + 12 new), `ruff check` and
`ruff format --check` clean, `mypy app` clean over 600 files, and the
commit verified in isolation from `git archive HEAD`.

## 7. Recorded, not solved

- **A first reading is unguarded**, by construction (§3). Catching a
  symbol that was wrong on its first read needs a second independent
  statement of identity — an LEI the document declares, or a reviewed
  issuer list — which is `IdentityCheck.DOCUMENT_LEI` and
  `SECURITY_REGISTRY`, neither of which EDGAR supplies.
- **A delisted ticker leaves the SEC map entirely** — `WBA` and `X` are
  no longer in `company_tickers.json`, so they raise *"not listed with
  the SEC"* rather than being caught here. That is a coverage gap and it
  is worded as one, correctly, but it is a *different* symptom of the
  same underlying fact and nothing links the two.
- **`provider_identity` and this module do not know about each other.**
  One compares providers, the other compares moments. Whether an issuer
  identity should be one object carrying both axes is a real question
  and is not answered here.
