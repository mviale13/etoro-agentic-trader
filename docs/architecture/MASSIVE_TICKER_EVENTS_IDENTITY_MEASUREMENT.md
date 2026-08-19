# Massive Ticker Events — can it strengthen the dated-CIK identity gate?

**Status: research. 5 authenticated calls, 13 seconds apart, USD 0, no
model calls, nothing persisted to production data. 2026-08-18/19.**

The question: Personal Ticker News (#204/#205) refuses a whole result
when a ticker denoted different issuers across the article window —
today the guard spends **two** dated Ticker Details calls and compares
CIKs. Massive's experimental Ticker Events endpoint claims to return a
timeline of symbol changes. Can it replace either call, or sharpen the
refusal?

## Conclusion

# B. CORROBORATION ONLY

**What it adds:** a **provider-reported event date**, and a
**deterministic trigger**. The date matched the known change for PARA
and XYZ, but its semantics are not uniformly established — BA carries
the dataset boundary and BNZI carries an unexplained date — so an event
reported inside an article window is a trigger for **additional dated
Ticker Details checks around that date**, and never itself proof that
the issuer changed inside the window. It may *expose the possibility*
of an A→B→A round trip that the two-point bracket cannot detect;
closing that possibility requires additional authoritative resolution.
**It cannot replace either existing dated-CIK call today.**

**Why the existing dated-CIK guard remains necessary:** the identity
fields the comparison would rest on are **undocumented** in the events
response, the meaning of an event's date is only partially established,
and the former-entity flow **the docs themselves prescribe returned
404** in the one live case it exists for. An experimental endpoint
whose payload is richer than its own documentation is not a foundation
for an identity gate; it is a second witness.

---

## 1. Documentation gate — read before any authenticated request

| document | retrieved (UTC) | size | sha256 (first 24) |
|---|---|---|---|
| `massive.com/docs/rest/llms.txt` | 2026-08-18T22:22:46Z | 31,528 B | `3d97823a53a68d17b5262ccf` |
| `…/corporate-actions/ticker-events` (html) | 2026-08-18T22:22:47Z | 1,583,389 B | `471be478ec985b152060af16` |
| `…/corporate-actions/ticker-events.md` | 2026-08-18T22:22:57Z | 3,226 B | `d6d345d87821b4bc0e7437a9` |

`llms.txt` is **byte-identical** to the copy fingerprinted in #204's
measurement — the documentation index has not moved between the two
slices.

What the docs establish, before any call was spent:

- `GET /vX/reference/tickers/{id}/events`, experimental; `id` accepts
  *"a Ticker, CUSIP, or Composite FIGI"*; the only supported event type
  is `ticker_change`.
- *"When provided a ticker, events for the entity **currently**
  represented by that ticker are returned. To find events for entities
  previously associated with a ticker, obtain the relevant identifier
  using the Ticker Details Endpoint."* — exactly the flow measured as
  calls 2 → 3 below.
- **Included on Stocks Basic**; history *"2 years"* on Basic; *"Records
  date back to September 10, 2003."*
- The documented response carries `results.name` and `results.events[]`
  — **no CIK and no FIGI appear in the response-attributes table or the
  sample.**

## 2. Budget compliance

5 calls, counted client-side, stamped 22:23:56 / 22:24:09 / 22:24:22 /
22:24:35 / 22:24:48 UTC — **13 seconds between every pair**. No retries,
no pagination, no News endpoint, no model calls. The key was read from
the ignored repository-root `.env`, sent only as a header, and the
recording script asserts the credential appears nowhere in its output.
**Zero rate-limit headers on all five responses** — call accounting
remains unobservable from the provider, as in #204.

## 3. The five calls

| # | request | status | latency |
|---|---|---|---|
| 1 | events · `PARA` (current) | 200 | 0.35s |
| 2 | details · `PARA` at `2023-06-01` | 200 | 0.33s |
| 3 | events · `BBG000C496P7` (former entity's Composite FIGI, from call 2) | **404** | 0.31s |
| 4 | events · `BA` (stability control) | 200 | 0.29s |
| 5 | events · `XYZ` (SQ→XYZ control) | 200 | 0.30s |

### Call 1 — the current entity, with a reported date for the symbol

```json
{"results": {"name": "Banzai International, Inc. Class A Common Stock",
  "composite_figi": "BBG00YG9XLK3", "cik": "0001826011",
  "events": [
    {"ticker_change": {"ticker": "PARA"}, "type": "ticker_change", "date": "2026-08-07"},
    {"ticker_change": {"ticker": "BNZI"}, "type": "ticker_change", "date": "2026-05-08"}]}}
```

Three facts. **The current holder of `PARA` is Banzai International
(CIK 0001826011)** — agreeing with #204's dated resolution. **The
provider reports 2026-08-07 as the date it took the symbol** — a kind
of statement the dated-CIK guard does not make at all (the guard proves
the endpoints of a window disagree and says nothing about *when*), and
one whose reliability this measurement cannot certify: the same
response's `BNZI` date is unexplained (§4, item 10). And **the live
response carries `cik` and `composite_figi`**, which the documentation's
response table and sample do not mention at all.

### Call 2 — the former entity, resolved the documented way

`PARA` at 2023-06-01 → **Paramount Global**, CIK `0000813828`, Composite
FIGI `BBG000C496P7`, share-class FIGI `BBG001S6L063`. The same
resolution #204 measured, unchanged.

### Call 3 — the documented former-entity flow, and it 404s

```json
{"status": "NOT_FOUND", "request_id": "…", "message": "No events found for given ID"}
```

The docs prescribe exactly this: obtain the former entity's identifier
from Ticker Details, then ask events for it. **In the one live case the
flow exists for, it returned 404.** Two readings are possible and the
response cannot separate them: the Composite FIGI is not accepted as an
`{id}` in practice, or it is accepted and the provider holds no events
for a delisted entity. The message — *"No events found for given ID"* —
reads as the second and proves neither. **The refusal shape conflates
identifier rejection with data absence**, which is the same defect class
#210 measured in this platform's own reader and typed four ways.

No substitute call was made; the budget rules forbid probing the
ambiguity, and the ambiguity is itself the finding.

### Call 4 — BA, the stability control

```json
{"results": {"name": "Boeing Company", "composite_figi": "BBG000BCSST7",
  "cik": "0000012927",
  "events": [{"ticker_change": {"ticker": "BA"}, "type": "ticker_change", "date": "2003-09-10"}]}}
```

Boeing, one event, dated **2003-09-10 — exactly the documented start of
records**. So an epoch-dated event is *the beginning of the dataset*,
not a ticker change: Boeing did not rename itself in September 2003.
No British Airways and no Omicron reference appears anywhere in the
response — the free-text collision #194 measured does not exist on this
identifier-keyed surface, consistent with #204's ticker-scoped result.

### Call 5 — XYZ, the known-change control

```json
{"results": {"name": "Block, Inc.", "composite_figi": "BBG0018SLC07",
  "cik": "0001512673",
  "events": [
    {"ticker_change": {"ticker": "XYZ"}, "type": "ticker_change", "date": "2025-01-21"},
    {"ticker_change": {"ticker": "SQ"}, "type": "ticker_change", "date": "2015-11-18"}]}}
```

**The reported SQ → XYZ date, 2025-01-21, matches the known change**,
with the 2015 listing-era event beneath it. A match on this entity and
on PARA is evidence the reported date *can* be right — it does not
establish that an event date means the same thing everywhere, which BA's
boundary date and BNZI's unexplained one show it does not.

## 4. The ten measurements

1. **Status, latency, shape.** 200 ×4, 404 ×1; 0.29–0.35s. Shape on
   200: `results.name`, `results.cik`, `results.composite_figi`,
   `results.events[]` of `{type, date, ticker_change.ticker}`.
2. **Identifier types in practice.** Ticker: accepted, 4 of 4. Composite
   FIGI: **unresolvable** — the one attempt 404'd and the response
   cannot say whether the identifier type or the entity's coverage
   failed. CUSIP: not attempted (nothing in this slice holds one).
3. **Event representation.** `type` is always `ticker_change`; `date`
   is a **provider-reported event date** whose semantics vary by entity
   — a change date for XYZ and PARA, the dataset boundary for BA, and
   unexplained for BNZI; the event names **only the new ticker** — there
   is no old/new pair, so a chain is read from consecutive events.
4. **Reassigned ticker, current-entity behaviour.** As documented: the
   ticker resolves to the current holder (Banzai), never the former, and
   the former is reachable only through its own identifier — which is
   the flow that then 404'd.
5. **Does a stable historical identifier retrieve the former entity?**
   **Not in the measured case.** Paramount's Composite FIGI — obtained
   exactly as the docs direct — returned nothing. The former entity's
   chain is not reachable on this plan today, and with it goes any hope
   of answering *"who held this symbol at date D"* from this endpoint.
6. **The two-year Stocks Basic limit.** Events dated 2003 and 2015 were
   served in full — the documented limit **did not clip** the events
   timeline. Observed-exceeds-documented is the same shape #204 found on
   news history, and is recorded, not relied on.
7. **Can it replace either dated reference call? No — not today.** The
   shape of a replacement is visible: one events call yields the current
   CIK **and** a reported acquisition date, and comparing the oldest
   article against that date *would* reproduce PARA's refusal. But the
   comparison would rest on an undocumented `cik` field and on a date
   whose meaning is not uniformly established (see 10) — so **neither
   existing dated-CIK call can be replaced by it**.
8. **Or merely corroborate? Corroborate — as a trigger, not as proof.**
   The reported date (2026-08-07) is *consistent with* the two dated
   resolutions disagreeing, and a `ticker_change` event dated **inside**
   the article window is a **deterministic trigger for additional dated
   Ticker Details checks around that date** — it is not itself proof
   that the issuer changed inside the window, because an event date can
   also be a dataset boundary (BA) or something unexplained (BNZI). It
   may *expose the possibility* of an A→B→A round trip the two-point
   bracket cannot detect; **closing that possibility requires additional
   authoritative resolution**, which is dated Ticker Details again.
9. **Article aboutness.** Nothing here bears on it. The endpoint carries
   no article linkage of any kind, and no inference is made. Symbol
   continuity and aboutness remain separate questions (#204's ruling:
   association is not aboutness).
10. **Experimental-endpoint behaviour.** Three instabilities observed.
    The live payload is **richer than its own documentation** (`cik`,
    `composite_figi` — undocumented fields are fields that can vanish
    without notice). The 404 message conflates two different failures.
    And one event date is **unexplained**: Banzai listed as `BNZI` in
    December 2023, yet its `BNZI` event is dated 2026-05-08 — matching
    neither the listing date nor a two-year window clip (2024-08-18).
    Within a five-call budget that anomaly could not be probed; an
    event-date semantics this platform cannot state is one it cannot
    build a gate on.

## 5. Why B and not A

The candidate improvement is a *shape*, not an available instrument:
one call instead of two, a reported date where the bracket has none,
and a trigger for checks the bracket would never know to make. Every
piece of it rests on ground this measurement found unstable — an
**undocumented** `cik` field on an **experimental** endpoint, a
provider-reported date that matched the known change for two of the
entities measured, carried the dataset boundary for a third and an
unexplained value for a fourth, and a former-entity flow that fails
exactly where the reassignment problem lives. A date whose semantics
vary by entity cannot serve as a boundary anything is decided against.
The platform's own standard (S5.1): **a gate that cannot be evaluated
fails.** The dated-CIK guard runs on a documented, stable endpoint and
asks a question whose answer it can check. It stays, and every use of
an event here reduces to *"go ask the guard again, around this date"*.

What would move this to A, named precisely: `cik` and `composite_figi`
appearing in the endpoint's documented response contract; the event-date
semantics stated by the provider (change date vs record boundary vs
corporate action); and either the former-entity flow working or the gate
being reformulated to need only the current entity's acquisition date.

## 6. Boundaries held

Research only — no production change of any kind · Personal Ticker News,
sentiment, decisions and analyst output untouched · Related Tickers not
called · no News endpoint call · no model calls · no provider payload
stored in production data (`git status --porcelain data/` empty; the
measurement record lives in the session scratchpad and is quoted here) ·
credential never printed, never in argv or a URL, `.env` never copied,
and its absence from every artifact asserted in code.
