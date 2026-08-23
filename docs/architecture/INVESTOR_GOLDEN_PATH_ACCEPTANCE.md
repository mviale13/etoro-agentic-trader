# The Investor Golden Path — product acceptance

**Status: research, stopped for the owner's ruling. Nothing here is a
repair.**

The question set by the owner on 2026-08-23: does the current product
help an investor reach an understandable course of action? Judged on
the live stack (`09b2297`, the real store, the recorded cycle
`5302671104f0`) by walking the actual journey — homepage → dossier →
evidence → price → envelope → news — for six representative cases.
This is a product acceptance, not an architecture inventory.

Budget compliance: exactly **9 Massive requests** (three dossier page
visits — DIS, MSFT, AMD — one each, no refresh, no retry, 13-second
pacing preserved; visits took 30/39/39 s). The other three cases were
read through the API dossiers and the crypto page, which trigger no
news. No funded cycle, no model call, no store mutation.

---

## 1. The six journeys

| | Homepage course | Dossier state · conviction | Why (as shown) | Gaps and refusals | Fundamentals authority | Price and provenance |
|---|---|---|---|---|---|---|
| **DIS** | RECOMMEND — "Consider adding to DIS." (holdings table) | RECOMMEND · 75, basis worded (5 of 5 families) | Rationale + synthesis: because = quality factors; despite = the qualified declining provider growth signal | none | 4 filing-evidence rows ("— FY filing"), 8 labelled fallbacks | Quote in store, dated, with provenance; **envelope: see finding 1** |
| **MSFT** | PREPARE (blocked cases) — "Wait… valuation" | PREPARE · 68 | *"Blocked by what it costs: valuation scores 55 against the 60…"* + *"This is a valuation ruling. It does not say MSFT is a weak business."* | none | 12 provider fallbacks, labelled | dated, attributed |
| **AMD** | PREPARE (blocked cases) — "Wait… quality" | PREPARE · 50 | *"business quality scores 62 against the 75 one needs"*; volatility 71.8% visible as safety evidence (safety 15), not as a rejection | none | 12 provider fallbacks | dated, attributed |
| **NESN.ZU** | not on the cycle (watched, unheld) | INVESTIGATE · 70 | *"Business quality has not been measured…"* | 1 named gap; **12 fundamentals REFUSED** — pre-identity record, worded (see §3) | all refused, honestly | "Yahoo Finance, 13 days ago" — stale and dated as stale |
| **HYPE** | INVESTIGATE — platform limit, worded; listing refusal on the homepage in the vendor's own words ("Supreme Finance USD") | INVESTIGATE (crypto dossier) | *"…what these conclusions are worth to an investment case is not established by this platform"* | market value CONFLICTED, both claimants + methodology sentence; 2 rejected claims ledgered | n/a (token) | **the established spot price renders nowhere — finding 2** |
| **UDMY** | not on the cycle | INVESTIGATE · **withheld** (no number) | rationale + 3 named gaps (valuation, quality, price history) | 12 fundamentals UNAVAILABLE, worded | all unavailable | none held; nothing invented |

News (three pages, ≤3 rows each, newest-first, collapsed, expandable):
DIS 3 rows (sentiment on 2 of 3 — exact-ticker rule), MSFT 3 (2 of 3),
AMD 3 (1 of 3). Coverage, association and display-only notices present
on every page.

## 2. The nine questions

1. **Can the investor tell what MOVRvest suggests doing? Yes.** Every
   case carries a course phrase on the homepage and a state + action on
   the dossier, including the honest edges (UDMY's withheld conviction
   is worded; HYPE's platform limit is worded).
2. **Can the investor tell why? Yes.** The blocker sentence names the
   gate and its numbers; the synthesis separates because / despite;
   MSFT's valuation ruling explicitly disclaims being a quality
   verdict. One wording nit (§3, P2): the RECOMMEND rationale still
   lists "risk" among satisfied gates after #239 removed the risk
   rejection.
3. **Quality vs security risk vs missing information? Yes, cleanly.**
   AMD is the proof: quality 62 (a measured shortfall), safety 15 (a
   measured violence), zero missing-evidence entries — three different
   statements on one page. UDMY is the inverse: nothing measured,
   everything named as missing, no number invented.
4. **Where capital is considered, is the maximum envelope visible and
   understandable? NO — finding 1.** The product's only two
   capital-asking courses (DIS and BNP.PA, RECOMMEND/ADD) have refused
   envelopes on a false premise, and the refusal itself renders on no
   investor surface.
5. **Are contradictory-looking facts explained by authority, period or
   source? Largely yes.** DIS's +132.7% / −48.3% pair is the showcase
   — two names, two authorities, the qualification in every sentence
   (#243 live). HYPE's conflicted market value names both claimants,
   both times, and the methodology question. Two residuals: the
   recorded cycle still quotes pre-#243 growth wording in the blocked
   section (a truthful historical record; resolves at the next funded
   cycle), and finding 1's false refusal sentence sits inside a payload
   whose own acquisition line says "26 priced of 26".
6. **Does any page imply missing evidence is negative evidence? No.**
   UDMY's quality is *unmeasured*, never LOW; NESN.ZU's refused
   fundamentals say the platform holds figures it will not attribute,
   not that the company lacks them.
7. **Does the homepage agree with the dossier and the latest cycle?
   Yes on states**, for all six. Wording drifts only where the record
   is older than a merged slice (growth sentences), which is the
   record being a record.
8. **Is any displayed number stale, unattributed, or presented with
   stronger authority than it earned?** Ages and sources ride on
   essentially everything, staleness is worded (NESN.ZU "13 days
   ago"). Two blemishes: the false "no market quote was acquired"
   sentence (finding 1 — the strongest authority violation, currently
   unrendered), and four of twenty age strings on the HYPE page drop
   the "received" qualifier because their adapters rebuild `Provenance`
   without `observation_stated` (§3, P2 — the #235 pattern in the
   remaining adapters).
9. **Is anything important technically present but effectively
   invisible? Yes, twice.** The entire capital arc (#221→#236) is
   invisible on the golden path (finding 1), and HYPE's established
   spot price is invisible on its own dossier (finding 2).

## 3. Findings

### Finding 1 — P1: the Capital Action Envelope neither computes nor shows for real capital-asking courses

Two halves, one investor consequence.

**It never computes.** The envelope's price gate looks the security up
in `brain.market.quotes` — the **market strip** (SPY, QQQ, IWM…), a
collection that cannot contain a holding. So every capital-asking
equity course ever recorded — 6 of 6 across all cycles, always DIS and
BNP.PA — carries `REFUSED: "no market quote for DIS was acquired this
cycle"`. The sentence is false: the same record says **"26 priced of
26 asked"**, and the store holds DIS at $107.78, stored 23:36 with
provenance. Downstream, #236's security-risk ceilings have never
composed for a real course (`security_risk_ceiling_pct` is null on
every recorded envelope), because refusal precedes composition.

**It never shows.** The homepage's two course groups are fed from
*candidates*; a holding's course appears only as a phrase in the
holdings table, with no envelope, no blocker and no conviction basis.
The dossier computes live and carries no envelope at all. So for the
product's two strongest suggestions — the ADD courses — no surface
renders the envelope sentence, not even the refusal. The `Envelope`
component exists and renders `stated` faithfully; nothing routes a
holding's course to it.

Not P0: the failure direction is conservative — nothing sizes, so no
incorrect capital action can follow. But the owner's capital arc is
currently inert and invisible exactly where it was built to act.

### Finding 2 — P1: a crypto asset's established price renders nowhere on its own dossier

HYPE's spot price is ESTABLISHED — corroborated by two claimants under
`token-fact-establishment@1`, carried with the #235 receipt-time
provenance, and used by the cycle to price the holding. The crypto
dossier's asset profile predates #231 and has no Price row: its Market
group shows market value (currently **CONFLICTED**, so no figure),
rank, and the 24-hour change. An investor asking the most basic
question — what does this platform say HYPE trades at — finds no
answer anywhere on the page, while the figure sits established one
layer below with better provenance than almost anything else on the
platform.

### P2 residuals (recorded; no repair slice, per the brief)

- Four of twenty age strings on the HYPE page drop the "received"
  qualifier: `crypto_dossier_adapter`, `crypto_playbook_adapter`,
  `supply_adapter`, `protocol_adapter` and `crypto_market_adapter`
  rebuild `Provenance(source, observed_at)` bare — the same laundering
  #235 fixed in `asset_profile_adapter`.
- The RECOMMEND rationale still names "risk" among satisfied gates;
  #239 removed the measured-risk rejection, so the claim is vacuous
  for measured risk (the unmeasured-risk gate remains real).
- The recorded cycle quotes pre-#243 growth wording in the homepage's
  blocked section beside live dossiers that word it qualified —
  truthful history, self-resolving at the next funded cycle.
- UDMY's `evidence_as_of` is null (nothing carries a reading);
  harmless but unhandled as wording.
- NESN.ZU's 12 REFUSED fundamentals stem from its pre-#134 stored
  record carrying no vendor identity claim; the refusal is the
  designed, honest behaviour, and the next funded acquisition writes a
  schema-5 record with identity and the fallbacks appear. Self-healing;
  named here so nobody "fixes" it by weakening the identity gate.

## 4. Conclusion

### B — READY WITH TARGETED REPAIRS

The reasoning an investor meets is coherent and honest: courses are
stated, whys are worded from the gates that decided, quality / risk /
absence are three visibly different things, non-comparable figures
carry their authority in their names, and missing evidence is never
dressed as negative evidence. Two P1 repairs, in investor-value order,
and no third:

1. **Make the Capital Action Envelope compute and show for
   capital-asking courses.** Feed the envelope's price gate the
   security's own stored quote — the one the same cycle's acquisition
   already priced and dated — and render the envelope sentence
   (bounded or refused) with the ADD course it belongs to, on the
   surface the investor actually reads. No threshold, policy or sizing
   arithmetic changes: the gates and ceilings exist and are tested;
   they are currently fed the wrong collection and rendered to nobody.
2. **Add the Price row to the crypto asset profile.** The fact, its
   claimants, its rule and its receipt-time provenance already exist in
   the judged pool; the adapter's groups predate them. Display only.

No P0 was found: every failure fails closed.
