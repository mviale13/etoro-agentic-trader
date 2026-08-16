# Identity history: what this platform means when sources stop disagreeing

**Status: research audit. One small precedented repair shipped (the
form lexer); the persistence question is measured, tested against the
candidate law, and stopped for ruling. No FX, Quality, threshold, band
or provider-quality change.**

The question, as set: *what does MOVRvest mean when evidence sources
once disagreed about an instrument's identity and later agree?* Not
whether SPCX is SpaceX — what a change of vendor account is evidence
**of**, and what the platform is entitled to forget.

---

## 1. The identity storage lifecycle, traced

**What is acquired.** Two claims per security. The **broker claim**
(symbol, name, raw `assetTypeId`, venue id, instrument id) arrives on
every live watchlist/account fetch. The **vendor claim** (symbol,
`longName`/`shortName`, `quoteType`, exchange) is extracted from the
same `Ticker.info` payload the fundamentals come from, at acquisition
(#143 amendment, fundamentals schema 4).

**Where it lives.** The broker claim is **never persisted** — it is
re-observed per session and exists only in flight. The vendor claim is
stored inside the fundamentals record:
`data/cache/fundamentals/{SYMBOL}.*.json`, one file per key.

**Append, version, or replace?** **Replace.** `JsonCache.write` is a
`write_text` over the key's single file — no append, no versioning, no
tombstone. `data/cache/` is gitignored, so an overwritten claim is
unrecoverable by any means. The store's contract manages *schema*
evolution carefully (five compatibility states, sequential migrations)
and *observation* history not at all — it was built as a daily
snapshot cache, which is what every other record in it is.

**What the join reads.** `CompanyFactsService._identity` derives the
#134 join on read, from exactly two inputs: the live broker claim and
the **latest** stored vendor claim. Nothing else exists to read.

**Is an old contradictory claim queryable?** **No.** After one
acquisition it is gone from the store; and in the live case it is
starker — the #134 SPCX conflict predates the schema-4 capture
entirely, so the conflicting account was **never stored at all**. It
survives only as prose in `PROVIDER_CLAIM_BOUNDARY.md` and as pinned
test fixtures: an engineering record, not queryable evidence.

**Can `UNRESOLVED → ASSUMED` occur solely because a conflicting
observation was overwritten?** **Yes — structurally guaranteed.** The
join is a pure function of (current broker claim, latest vendor
claim). Any payload drift that removes the disagreeing words flips the
standing, with no record that anything was ever in question. Since the
#143 amendment made identity a **prerequisite gate** on market-cap
input eligibility, this is no longer a display nuance: the claims that
produce UNRESOLVED are decision-bearing evidence held in a store whose
write semantics forget contradictions. That is the audit's central
finding.

## 2. The corpus, measured (not just SPCX)

Joins the next acquisition would derive (live broker book × the
2026-08-16 payload sweep; 66 equities/funds with both claims):

| Standing | Count | Who |
|---|---|---|
| ASSUMED | 64 | everything else — symbol equality alone |
| CORROBORATED | 1 | IB01.L (both names state UCITS/ETF) |
| UNRESOLVED | 1 | **SE** — eToro *"Sea Ltd-ADR"* states a form; Yahoo *"Sea Limited"* states none |

Three corpus facts beyond SPCX:

- **A second live conflict exists: SE.** It would be *recorded* at the
  next acquire — and is exactly as erasable afterwards: if either
  side's wording drifts (*"Sea Ltd-ADR"* → *"Sea Ltd"*), the standing
  flips to ASSUMED and the disagreement leaves no trace. The
  fragility is corpus-general.
- **A manufactured corroboration existed: NFLX.** The form lexer
  matched substrings, and `etf` is a substring of n**etf**lix — so
  *"Netflix, Inc."* read as a fund *on both sides* and the join
  reported agreement on instrument kind that no provider ever stated.
  Measured: the corpus's only accidental hit, and the only join the
  word rule moves. This is #110's `sent`-inside-*absent* lesson,
  relearned; **repaired in this PR** (words, not substrings; NFLX and
  SE pinned), decision-neutral since CORROBORATED and ASSUMED both
  pass the gate.
- **Observed forget-flips so far: one** (SPCX, §4). But every one of
  the 66 joins is one payload edit away from a silent standing change
  under current storage.

## 3. Correction, evolution, observation drift — what the evidence can tell apart

Three phenomena a newer observation might be:

- **Correction** — the provider fixed its own prior error.
- **Evolution** — the ticker→instrument relationship genuinely
  changed.
- **Observation drift** — successive payloads simply disagree.

What the acquired evidence can distinguish, measured against the live
SPCX payload:

- **No correction channel exists.** Yahoo's payload carries no
  revision, correction or claim-versioning field of any kind. A
  correction is indistinguishable from drift by payload content alone,
  and always will be until a source that marks corrections exists.
- **Evolution is partially evidenced — by fields we do not read.**
  The live SPCX payload carries `firstTradeDateMilliseconds`
  (≈ 2026-06-12) and `ipoExpectedDate` (`2026-06-12`): the instrument
  Yahoo now serves under SPCX **began trading on 12 June 2026**. The
  ticker's previous occupant (an ETF) is a different instrument; this
  is a **ticker reassignment**, observed through roughly two months of
  vendor lag. Neither field is read or stored today.
- **Distinguishing any of this requires memory.** Dating the *current*
  instrument helps only beside a record of what was previously
  claimed. With claim history destroyed on write, no phenomenon can be
  distinguished from any other after the fact — the platform cannot
  even say *that* the account changed, let alone why.

## 4. The SPCX timeline, reconstructed

| When | Evidence | Source |
|---|---|---|
| ≈ 2026-06-12 | the instrument now served under SPCX begins trading (its own `firstTradeDate`/`ipoExpectedDate`) | live payload, fields unread by the platform |
| 2026-08-13→15 | #134 measures the live join: eToro 15618 *"Space Exploration Technologies Corp"* (taxonomy 5) vs Yahoo *"SPAC and New Issue ETF"* (ETF) → **UNRESOLVED** | `PROVIDER_CLAIM_BOUNDARY.md`, pinned fixtures — never the store |
| 2026-08-16 | live payload: *"Space Exploration Technologies Corp."* / EQUITY — the vendor's mapping caught up with the June reassignment | this audit's sweep |
| next funded acquire | schema-4 capture stores the **agreeing** claim; join derives **ASSUMED** | current code, deterministic |

**What disappears:** the ETF account, entirely — it was never stored,
and after the first capture the store will contain only agreement. The
platform will hold no evidence that SPCX's identity was ever in
question, while the market-cap gate that #143's amendment built
*because* it was in question silently opens (subject to the other
crossings — today SPCX's denomination is UNRECONCILED anyway, so the
gate stays shut on an independent ground).

**What remains:** #134's prose and the regression fixtures — which pin
the *mechanism* (an UNRESOLVED join refuses), not the *instance*.

**Classification:** evolution (June reassignment) observed through
vendor lag, with the 2026-08-16 payload as the vendor correcting its
own stale mapping — and the resolving evidence for all of it sits in
two payload fields the platform discards.

## 5. The candidate law, tested

> *A later agreeing observation may add evidence, but mere recency
> cannot erase a previously established contradiction. Withdrawal of
> an identity conflict requires evidence that resolves the conflict,
> not merely absence of the conflicting claim in the latest payload.*

**Where the repository already obeys exactly this law:**

- **S4.6 (supply semantics)** — ADA's three-way conflict was withdrawn
  by *explanation* (the figures measured different ledger quantities),
  and HYPE's **stands** because no explaining disclosure exists.
  Conflicts dissolve by evidence, never by refresh. The transfer to
  identity is direct, because S4.6's own sentence transfers: *two
  claims only conflict if they describe the same thing* — and
  `firstTradeDate` is precisely the evidence that SPCX's two accounts
  described **two different tenancies of one ticker**. The conflict
  dissolves the S4.6 way, with evidence already in the payload.
- **The intelligence journal (#111)** — append-only; *a correction is
  a new entry naming what it corrects*; world-moved / source-revised /
  our-reading-changed are never conflated. The three phenomena of §3
  are this trichotomy under another name.
- **Judgment history (#113)** — an absent today is *"unrefreshed
  rather than contradicted"*; a historical verdict is never today's
  verdict; the earlier record stays reachable. Recency neither erases
  nor restates.
- **The identity module's own docstring** — *"a conflict is a finding
  to be shown, not a problem to be settled by whichever source the
  code happens to read first."* Overwrite-by-acquisition settles it by
  whichever source the code read **last** — the current storage
  contradicts the module's stated philosophy.

**The falsification attempt** — would permanent conflict memory create
false unresolved identities after legitimate provider corrections?
**Yes, for one class, and the corpus has not yet exhibited it.** A
transient vendor error (a typo-class wrong name served for a day)
would establish a contradiction that no future evidence can withdraw:
no correction channel exists (§3), and a typo has no tenancy evidence
to dissolve it. Under a strict reading — historical conflict gates
until explained — one bad payload poisons a security's market-cap
input permanently. Three things blunt this without breaking the law:

- both **observed** conflicts are not of this class (SPCX dissolves on
  tenancy evidence; SE's is *current*, not historical);
- the platform's own precedent for the repair is to keep **two facts
  apart** rather than choose one — the *current-claims join* (what the
  sources say today) and the *historical contradiction* (what was once
  observed, explained or not) — #113's three-axes move, applied to
  identity. The law then governs the historical fact and whatever the
  ruling decides it gates; the word UNRESOLVED keeps meaning what
  `IdentityStanding` defines (*evidence the providers **do** supply
  disagrees*, present tense);
- with claim history retained, a one-day blip is *visible as* a
  one-day blip — which does not by itself license erasure under the
  law, but gives the ruling an honest object to price instead of a
  hypothetical.

**Verdict: the law survives against the measured corpus and the
existing domain semantics, with the two-facts refinement.** What it
cannot survive as is a redefinition of the *current* standing
vocabulary; what remains genuinely open — and is the ruling — is
whether an unexplained historical contradiction gates decision inputs
forever, until explained, or not at all.

## 6. Existing history models, compared

| Boundary | Model | Fits identity? |
|---|---|---|
| provider caches (fundamentals, quotes, fx, ratings) | latest-only snapshot, replaced daily | where identity claims live **today** — built for provider state, not for contradiction-bearing evidence |
| knowledge observations (schema 14) | **append-only observations; consensus derived on read; decision path consumes the derivation only** | the closest fit: claims are observations, the join is a consensus-shaped derivation |
| intelligence journal (#111) | append-only JSONL; corrections name what they correct; world/source/reading trichotomy | the write-discipline and the correction vocabulary |
| judgment history (#113) | append-only records; `previously` reachable; absent ≠ contradicted | the two-facts separation and the never-restate rule |
| token-facts gate (#99) | rejected claims retained beside established ones, with reasons | retention of the losing account within one reading |
| monetary provenance (C5/C6) | derived claims carry evidence; snapshot-current, no history | shows a *derivation* discipline, not a history one |

The dividing line the repository already drew: **observations that
feed conclusions are append-only; provider state is latest-only.**
Since #143's amendment, identity claims feed a gate — they sit on the
wrong side of their own line. If the ruling adopts persistence, the
pattern to reuse is the observation-stream/derive-on-read shape that
three boundaries already implement; nothing here needs a bespoke
event-sourcing system.

## 7. The smallest correct repair, if warranted — not built, for the ruling

1. **Append, don't replace**: vendor identity claims become an
   append-only observation stream per symbol (the knowledge/journal
   write discipline), each entry dated by its acquisition; the
   fundamentals record keeps serving the latest for everything else.
   The broker claim, today never persisted, joins the same stream at
   acquisition if the ruling wants both sides remembered.
2. **The join derives from the full held set**, separating the
   current-claims standing from a retained historical-contradiction
   fact — never collapsing them into one word.
3. **Read the tenancy evidence**: `firstTradeDateMilliseconds` /
   `ipoExpectedDate` into the vendor claim — already in the payload,
   already in hand at acquisition, and the S4.6-shaped dissolution
   evidence for exactly the observed case.

What was shipped in this PR instead, because it was small, obvious and
precedented (#110's word-boundary lesson): the form lexer matches
words, not substrings. NFLX's manufactured corroboration becomes an
honest ASSUMED; IB01.L and SE are pinned unchanged; no gate outcome
moves anywhere in the corpus.

## 8. What would legitimately permit `UNRESOLVED → ASSUMED/VALIDATED`

- **A shared global identifier** — the ladder's own ESTABLISHED tier.
  Neither provider serves an ISIN on any reachable payload today.
- **Tenancy evidence dissolving the conflict** (the S4.6 route): the
  claims described different instruments behind one ticker —
  `firstTradeDate`/`ipoExpectedDate` partitioning the accounts, as
  SPCX's payload already does. The conflict is not *overruled*; it is
  shown to have never been a conflict about one instrument.
- **A provider's explicit correction**, should a source that marks
  corrections ever exist. None does now.
- **Never**: the conflicting claim merely being absent from the latest
  payload — which is the only transition the current storage is
  capable of representing.

**Stopped for ruling**: whether identity claims move to the
append-only side of the platform's own line; whether an unexplained
historical contradiction gates, and for how long; and whether the
broker claim is remembered alongside the vendor's.
