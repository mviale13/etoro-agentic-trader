# S5.1 — Supply structure, and when a chain reading may establish

**Status: built 2026-08-10. The Model C gate is installed and two primary
readings establish through it. Supply Structure remains
`VISIBLE_NOT_SCORED`, the quality quorum is unchanged at two, and no asset
gains a headline score.**

---

## A. What S5.1 can legitimately answer

> **How much of a protocol-defined maximum has been created, and is the
> remainder accounted for by the protocol itself?**

Not *what future supply pressure can a holder expect* — that needs a
schedule, and no source this platform reads publishes one for any of the
eight. The two questions look the same and are not, which is the finding
in section D.

---

## The Model C gate

The owner's rule, and emphatically **not** *deterministic primary
computation → ESTABLISHED*. Six requirements, all of which must hold:

| # | Requirement | Asks |
|---|---|---|
| 1 | Identity | does the canonical source confirm this figure is about this asset? |
| 2 | Semantics | does it reconcile against the protocol's own components? |
| 3 | Constants | is every constant stated by the source or independently checked? |
| 4 | Reproducibility | could a stranger obtain this without trusting this reading? |
| 5 | Perimeter | was it compared with another observation, and any difference exposed? |
| 6 | Versioning | are the rule, the formula and the state it was read at recorded? |

**A gate that cannot be evaluated fails.** Not knowing whether a
computation leaned on a remembered constant is exactly the state
Ethereum's blob base fee was in when it came out wrong by ~850 million ×,
and treating an unknown as a pass would rebuild the hole the gate was cut
to close.

Gate 5 requires comparison, **not agreement**. Hyperliquid's emitted
supply and CoinGecko's differ by 38.6% because the vendor counts tokens
the protocol says do not exist yet; exposing that is the gate doing its
job, and suppressing it to obtain a pass would be the opposite.

---

## C. Model C results

| Asset | Concept | Gates | Verdict | Blocking |
|---|---|---|---|---|
| ADA | emitted supply | 6/6 | **ESTABLISHES** | — |
| ADA | protocol maximum | 6/6 | **ESTABLISHES** | — |
| ADA | circulating estimate | 6/6 | **ESTABLISHES** | — |
| ADA | excluded balances ×2 | 5/6 | claimed | perimeter — nobody else reports them |
| HYPE | emitted supply | 6/6 | **ESTABLISHES** | — |
| HYPE | protocol maximum | 6/6 | **ESTABLISHES** | — |
| HYPE | future emissions | 5/6 | claimed | perimeter — nobody else reports it |
| HYPE | excluded balances ×4 | 5/6 | claimed | perimeter |
| ARB | emitted supply | 4/6 | claimed | **identity**, semantics |
| TAO | emitted supply | 5/6 | claimed | **semantics** |
| BTC · ETH · SOL · 1INCH | — | — | no primary surface exists | — |

### Why each failure is the right failure

**ARB fails identity.** `eth_call totalSupply()` on a hard-coded contract
address returns a number and nothing else — no name, no symbol. That the
address is ARB's is this platform's belief about an address, which is
precisely the shape invariant 2 exists for. It also fails semantics: an
ERC-20 total has no components to reconcile against.

**TAO fails semantics.** Subtensor publishes `TotalIssuance` and nothing
to check it against. Bittensor defines no circulating supply at all, so
there is nothing for issuance to reconcile with — an honest absence, not
a gap in the reading.

### The two reconciliations that passed

**Cardano reconciles to the lovelace.** Seven quantities the ledger
publishes sum to its own `supply` with a residual of **exactly zero**:

```
circulation + treasury + reward + deposits_stake
            + deposits_drep + deposits_proposal + fees = supply
38,803,572,882,173,527 lovelace = 38,803,572,882,173,527 lovelace
```

Drop `fees` and the identity misses by 29,001 ADA — small enough to read
as rounding, which is why the check uses every part.

**Cardano's maximum is now chain-derived.** `supply + reserves` comes to
**45,000,000,000 ADA exactly**. The reserves pot *is* the unissued
remainder, so the chain states its own cap by accounting for every
lovelace on either side of it. Two vendors say the same number; the chain
says why it is that number. This also discharges gate 3: the 1e6 lovelace
denomination is remembered, and a wrong power of ten would not land on a
round 45bn.

**Hyperliquid reproduces its own circulating figure.**
`totalSupply − futureEmissions − Σ nonCirculatingUserBalances =
circulatingSupply`, within one rounding step per figure at the precision
the protocol published. It needs no denomination constant at all — the
API publishes decimal token units.

---

## B. Corpus measurement

| Asset | Max supply | Emitted | Emitted/max | Overhang vs max | Named? |
|---|---|---|---|---|---|
| BTC | 21,000,000 (2 vendors) | 20,068,243 (1 vendor) | 95.6% | 4.4% | no |
| ETH | **none** | 120,682,058 (1 vendor) | **not applicable** | — | — |
| SOL | **none** | 631,882,479 (1 vendor) | **not applicable** | — | — |
| ADA | 45,000,000,000 **chain** | 38,803,572,882 **chain** | 86.2% | 18.8% | **yes, 2 balances** |
| HYPE | 1,000,000,000 **chain** | 586,532,752 **chain** | 58.7% | 70.1% | **yes, 4 balances** |
| ARB | 10,000,000,000 (2 vendors) | 9,999,998,978 (chain, unestablished) | 100.0% | 33.9–87.2% | no |
| TAO | 21,000,000 (2 vendors) | 11,218,394 (chain, unestablished) | 53.4% | 54.3–58.8% | no |
| 1INCH | 1,500,000,000 (2 vendors) | 1,499,999,999.997 (1 vendor) | 100.0% | 5.8% | no |

*Overhang* is the share of the maximum not in the market: unissued supply
plus supply issued into balances nobody counts as circulating. It is a
range where the vendors' circulating estimates conflict, because choosing
one would be choosing the answer.

**ETH and SOL are NOT APPLICABLE, not LOW.** Neither protocol defines a
maximum. That is a monetary design, not missing evidence, and inventing a
denominator would manufacture a number.

---

## D. The candidate scoring result: **VISIBLE_NOT_SCORED**

Option B. The evidence S5 named as the blocker arrived — two assets'
emitted supply now establishes — and the question still does not score,
for a better reason.

**The ratio and the exposure come apart.** Ranked by emitted share against
ranked by what is actually absent from the market:

```
by emitted share   1INCH · ARB · BTC · ADA · HYPE · TAO
by overhang        BTC · 1INCH · ADA · ARB · TAO · HYPE
```

**Arbitrum is the case.** 100% emitted — second-best on the candidate
factor — and between 33.9% and 87.2% of its maximum is sitting in balances
nobody names. Cardano is 86.2% emitted with 18.8% outstanding, every
lovelace of it named by the ledger. A band on the emitted share would rank
Arbitrum above Cardano on the strength of the ratio being higher, and the
holder's actual exposure runs the other way.

Three further reasons, each sufficient on its own:

1. **Coverage is 2 of 8 for an established ratio**, and Bitcoin — the
   asset with the most famous supply schedule in the class — is not one of
   them, because this platform has no Bitcoin primary surface.
2. **No schedule is held for any of the eight.** When the remainder
   arrives and to whom is the question a holder is actually asking.
3. **The vendor field cannot substitute.** CoinGecko's `total_supply`
   equals the protocol maximum for 83 of the 145 capped assets in the 250
   largest, and the chain impeached it for ADA and TAO.

It is reported, in full, on the dossier — with each figure's authority,
the gate outcome where a chain reading fell short, the overhang, and the
absence of a schedule.

---

## E. Revised quality quorum

Unchanged, and unreached.

| Scorable applicable questions | Assets |
|---|---|
| 0 | — |
| 1 | BTC, ETH, SOL, ADA, TAO, 1INCH, ARB, HYPE |
| 2+ | none |

`MINIMUM_SCORED` remains 2. Market robustness is still the only scorable
question, so no crypto asset emits a headline score. **F** is therefore
identical to the S5 corpus table: no verdict moved.

---

## G. Engineering provenance repair

PRs #104, #105 and #106 never existed; the real numbering stops at #102.
S3, S4, S4.5 and S4.6 were merged into a local `main` and never pushed, so
their merge commits carry hand-written `(#NNN)` suffixes matching nothing.
Corrected in place, with the real commits as the authority:

| Slice | Real commits | Was documented as | Now |
|---|---|---|---|
| S3 archetypes | `0fbc7ee` → `1054b9e` | "built and merged" | built, merged locally, no PR |
| S4 market context | `9ec2de4` → `509eb68` | "built and merged" | built, merged locally, no PR |
| S4.5 evidence authority | `5d694a7` → `fc17e38` | "measured and built" | built, merged locally, no PR |
| S4.6 supply semantics | `b236a41` → `2a493f0` | "built and merged" | built, merged locally, no PR |
| S5 asset quality | `77ef4d8` → squash `4cb9516` | — | PR #103, real |

All five reached GitHub together inside `4cb9516`. The per-slice history
is preserved on the `history/crypto-s3-to-s4.6` branch — pushed rather
than rewritten, so nothing was lost and nothing was invented.

*An identifier that looks plausible is not evidence that the event
happened.* The same rule the evidence layers live by, applied to the
repository.

---

## H. Recommendation

The quorum is not reached, so the next slice is an evidence question
rather than a scoring one. In order of how much they unlock:

1. **The emission schedule** — the single acquisition that would turn
   supply structure from *shown* into *scorable*, and it is the one the
   corpus says is missing for all eight. It is also the hardest: no
   provider this platform reads publishes it, so it is a research question
   before it is an engineering one.
2. **A second liquidity observation.** Order-book depth at venues this
   investor could actually trade on would answer the question S5 measured
   the inherited factor into the ground for. It is the only other question
   whose *investor meaning* is settled and whose evidence is merely
   missing.
3. **Bitcoin primary state.** A Bitcoin surface would let the largest
   holding in the class answer a supply question at all. It does not reach
   quorum on its own.

Everything else in the model is blocked on corroboration rather than
acquisition, and corroboration is a provider decision, not a slice.

---

## Boundaries held

- Legacy generic `circulating_supply` is not the scoring authority and is
  not read by the quality model.
- Emitted/max is never called dilution.
- Future supply pressure stays separate, and unscored.
- Project age stays retired; market context, valuation and Evidence
  Maturity stay out of Asset Quality.
- No CLAIMED protocol economics contribute a point.
- No decision threshold changed. Equity behaviour is untouched.
