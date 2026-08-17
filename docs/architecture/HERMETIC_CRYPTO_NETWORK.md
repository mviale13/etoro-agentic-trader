# A green suite must not mean a reachable host

**Status: built, CI1. The suite makes zero outbound HTTP requests and
2,795 tests pass. No model call, no credit, no live refresh, no crypto
analytical change, and `data/` byte-identical.**

BQ17's run passed because `mempool.space` happened to answer. That is
not a fix, and this slice does not treat it as one: the acceptance test
here is the suite passing with **every external call blocked and
recorded**, not the suite passing.

---

## 1. The accidental network path

Measured rather than guessed — a diagnostic plugin blocked `requests`
and `httpx` at the library level, recorded each attempt with the
production frame that made it, and ran the whole suite. **Nine attempts,
two distinct paths:**

```text
GET https://mempool.space/api/blocks/tip/height          × 8 tests
  app/api/routes/crypto_dossier.py:153   IssuanceRuleProvider().rule(asset)
  app/providers/issuance_rule_provider.py:140   _bitcoin()
  app/providers/issuance_rule_provider.py:612   _get  →  requests.get

POST https://arbitrum-one-rpc.publicnode.com             × 1 test
  app/providers/primary_sources.py:733   ArbitrumRpc._post  →  requests.post
```

| Test | Path | Endpoint | Testing integration? |
|---|---|---|---|
| `test_crypto_dossier_route.py` ×6 | `GET /crypto/{s}/dossier` → inline `IssuanceRuleProvider()` | `mempool.space`, then `api.blockchair.com` | **No** — payload shape, refusals, "unknown is never a zero" |
| `test_crypto_judged_facts.py` ×1 | same | same | **No** — asserts the `facts` key exists |
| `test_crypto_dossier_reaches_the_page.py` ×1 (fixture) | same | same | **No** — the parser reads every served section |
| `test_supply_establishment.py` ×1 | `ArbitrumRpc._post` | `arbitrum-one-rpc.publicnode.com` | **No** — a domain property about emitted share vs overhang |

**Not one of the nine intends to verify a live provider**, so §3's
"separate the genuine integration tests" has no candidates: there are
none to separate.

The endpoint in CI logs was `api.blockchair.com` and the endpoint here is
`mempool.space` — the same `_bitcoin()` path reads both in sequence, so
whichever fails first is the one CI reports. That is exactly the
non-determinism this slice removes.

## 2. Why the boundary did not intercept them

`tests/conftest.py` already blocks the wire — `NETWORK_SEAMS` names each
keyless provider class and `SEAM_METHODS` names its wire methods. It is
an **allowlist keyed by class name**, so anything not named is
unguarded, and its own docstring had already stated the cost: *"adding
one means adding it here. The cost of forgetting is invisible."*

It was forgotten three ways:

- **`ArbitrumRpc` and `SubtensorRpc`** sit in `primary_sources.py`
  beside four guarded siblings and were never added — the same
  omission twice.
- **`IssuanceRuleProvider`** was missing entirely. It is a whole
  provider rather than a chain adapter, which is likely why: the list
  reads as "chain surfaces", and this one is a reader over four of them.

And the credential guard could not have helped: every one of these
endpoints is keyless, which is precisely the case `NETWORK_SEAMS` exists
for.

## 3. The boundary chosen

**Two repairs, and the second is the one that lasts.**

**(a) The route declares its acquisition instead of inheriting it.**
`app/api/dependencies.py` exists for exactly this, and says so: *"A
handler that builds its services inline reaches for the network the
moment it is called… Declaring those services as FastAPI dependencies
moves construction to one place a test can override."* The crypto
dossier built `IssuanceRuleProvider()` inline; it now takes
`get_issuance_rule_provider` as a dependency.

**The production default is the same class the route always built** —
`IssuanceRuleProvider()`, acquisition intact. What moved is *where* it
is constructed, not *what* it is. Switching the default to the cached
`stored()` door would also fix the tests and would change what
production serves for an uncached asset; that is BQ16's recorded
crypto-dossier contract defect and stays its own slice.

`tests/conftest.py` supplies `CachedIssuanceRuleProvider.stored()` as an
autouse override — the same stored door every other service in that
route already opens, onto the same temp evidence root, so the route
renders the honest absence its siblings render. Declared in conftest
rather than in three test files because it belongs with the other
hermetic defaults, and a test that wants an acquiring provider overrides
it back visibly.

*(One implementation note worth keeping: the override must be a nullary
callable. FastAPI inspects an override's signature, and `stored`'s
optional `cache` argument was refused as an invalid request field. The
lambda also defers construction to request time, so the cache is rooted
at the temp evidence directory.)*

**(b) The guard is enumerated from the code.**
`tests/test_hermetic_boundary.py` parses the keyless provider modules
and asserts every class that **actually calls** `requests`/`httpx` has a
`NETWORK_SEAMS` entry, that every wire method of a guarded class is
named, and that no named seam points at a class or method that no longer
exists. A new chain adapter now fails on the day it is written rather
than on the day someone else's host goes down.

**Detected by what a method does, not by what it is called** — and that
distinction was earned during the slice. A name-based rule
(`_get`/`_post`/`_rpc`) reported CoinGecko's guard as broken: that class
has both `_get` and `_request`, and only `_request` touches the wire —
`_get` is a pacing wrapper around it. The name rule would have demanded
a guard on the wrapper and, in the general case, let a wire method with
an unexpected name through. The AST now looks for the library call
itself.

Verified to bite: removing `SubtensorRpc` from `NETWORK_SEAMS` fails the
guard with that exact class named.

## 4. Affected tests, before → after

| | Before (wire blocked) | After |
|---|---|---|
| `test_crypto_dossier_route.py` | **6 failed** | 8 pass |
| `test_crypto_judged_facts.py` | **1 failed** | pass |
| `test_crypto_dossier_reaches_the_page.py` | **1 error** (fixture) | pass |
| `test_supply_establishment.py` | passed, but **reached the wire** | passes offline |
| the three crypto files together | timed out on the wire | **23 pass in 1.1s** |

No assertion was weakened. The only test-file change is the conftest
default; the three crypto test files are untouched.

## 5. Proof with the network blocked

The whole suite, with `requests` and `httpx` blocked for every external
host and every attempt recorded:

```text
NO OUTBOUND HTTP ATTEMPTED

2795 passed in 13.57s
```

Before the repair, the same run produced **9 attempts, 7 failures and 1
error**. That is the difference between *passed* and *cannot depend on
the network*.

## 6. Sibling audit

Searched all provider modules for direct `requests`/`httpx` calls (26
call sites across 16 modules) and classified them:

| Class | Guarded by | State |
|---|---|---|
| `EthereumRpc`, `HyperliquidInfo`, `CardanoLedger`, `BitcoinExplorer` | `NETWORK_SEAMS` | already |
| **`ArbitrumRpc`, `SubtensorRpc`** | `NETWORK_SEAMS` | **added — the same defect class** |
| **`IssuanceRuleProvider`** (`_get`, `_rpc`) | `NETWORK_SEAMS` | **added — both protocols named** |
| `CoinGeckoMarketProvider` | `NETWORK_SEAMS` | already, and verified pointing at the real wire method |
| `TokenInsight`, `CoinGeckoFacts`, `TokenFacts` | `SETTINGS_READERS` | keyed; silenced credentials, different failure mode |
| EDGAR / ESEF / IR / LEI / DefiLlama / ETF flow / press / primary events | injected or stubbed per test | no attempt observed in the full run |

Two methods rather than one for the issuance reader, deliberately: it
speaks REST for Bitcoin's tip and JSON-RPC for Solana's inflation, and
naming only `_get` would have left Solana's schedule live while the
suite looked fixed.

The audit stopped at the boundary the brief drew: no provider was added,
removed or redesigned.

## 7. Production impact

**None, by construction.** `get_issuance_rule_provider()` returns
`IssuanceRuleProvider()` — verified at runtime to be the identical
class the route constructed before. No stored crypto fact, analytical
conclusion, committee, quality band or dossier section changed;
`git status --porcelain data/` is empty.

## 8. Gates

| Gate | Result |
|---|---|
| `pytest` | **2,795 pass**, 0 failures |
| `pytest` with the wire blocked | **2,795 pass, 0 outbound requests** |
| `ruff check` | clean |
| `ruff format --check` | **990 files already formatted** |
| `mypy app` | clean, 591 files |

**One item outside the network diagnosis, included deliberately**:
`ruff format` had drifted on 8 files — pre-existing on `main`, and mine,
from the `--no-verify` commits BQ15 and BQ16 used to get past the
network-dependent pre-commit hook. It is the *other* half of why CI was
red, it is mechanical, and leaving a reliability slice with a red
formatter would have been odd. The 8 files are reformatted and nothing
else about them changed.

That drift also has a cause worth naming: I had been running `ruff
check` and not `ruff format` before committing. Both now.

## Recorded, not solved

- **The crypto dossier's contract still overstates itself.** Its
  docstring says *"it acquires nothing"* while its production default
  acquires. This slice made that honest in tests and left production
  alone; making the route genuinely non-acquiring is BQ16's recorded
  defect and its own ruling.
- **`NETWORK_SEAMS` remains a list**, now with an enumerating guard over
  two modules. Extending that guard to every provider module would
  require classifying keyed providers too, which is a wider audit than
  this slice.

## Scope compliance

No crypto analytical conclusion changed · no stored crypto fact changed
· quality and committee logic untouched · no provider added · no live
data refresh · BQ16/BQ17 provenance untouched · no model or API credit ·
the dossier not redesigned — one inline construction became one declared
dependency with an unchanged default · `data/` byte-identical.
