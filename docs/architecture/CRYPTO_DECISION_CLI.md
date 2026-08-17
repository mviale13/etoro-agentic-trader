# Asking the canonical crypto decision from a terminal

**Status: DV7, built. The last surface of the convergence arc. No model
call, no acquisition, no production write, and no journal write at all.
Stopped for ruling.**

> **A thin adapter, and nothing else.** `movrvest crypto-decision BTC`
> prints the same answer the crypto dossier renders, the portfolio brief
> carries, the research pipeline admits on and the journal records. The
> command owns no rule, no threshold and no wording of its own: every
> sentence it prints was worded by the layer that established it.

---

## 1. The CLI audit, and the chosen shape

Measured across the existing verbs rather than assumed:

| convention | what the CLI does |
|---|---|
| **naming** | a `crypto-*` family already exists — `crypto-market`, `crypto-playbook`, `crypto-quality`, `crypto-events`, `crypto-intelligence`. `decide` is taken by the investment-question command. |
| **shape** | `symbol` positional, `nargs="?"`, corpus when omitted |
| **read vs write** | separated *at the verb level*. `judge`, `observe`, `acquire` write; every rendering verb reads. |
| **output** | human-readable, `textwrap` at width 76, indented sections |
| **exit codes** | measured on five siblings: `crypto-playbook`, `crypto-market`, `committees`, `committee-judgment` and `considerations` all report an unheld asset and **exit 0**. Non-zero means the command could not do its job. |
| **structured output** | **no `--json` convention exists.** One verb of roughly fifty emits JSON — `brain`, which dumps wholesale as a debug surface. |
| **asset resolution** | a crypto verb asserts `AssetClass.CRYPTO` and lets its service refuse; `ASSIGNMENTS` is used to *enumerate* the corpus, never to classify a single symbol |

**Chosen: `movrvest crypto-decision [SYMBOL]`** — one verb, one optional
argument, no flags. The smallest surface consistent with the family it
joins.

**A verb that almost exposed it already**: `movrvest evaluate SYMBOL`
runs the canonical pipeline, so since DV4 it *does* produce the crypto
decision. It is the wrong home — it builds a whole Brain (broker
credentials, market perception), renders through the equity-shaped
console renderer, and writes. The canonical crypto decision is a read
over stored judgments taking milliseconds and needing no credentials,
which is exactly the shape of every other `crypto-*` verb.

## 2. Read-only, and the CLI's own law decides it

`judge.py` states the principle in its own docstring: *rendering must not
manufacture events, or "the committee has reviewed this eleven times"
becomes a count of page views wearing the language of review.*

The canonical decision is a projection over what `judge` recorded, so
printing it must not append. **The write already exists** — DV6 journals
through the normal decision-execution path (the portfolio, dossier and
research routes, and `evaluate`), by the one writer that slice
established. A second writer here is exactly what the brief forbids.

**Proved rather than asserted**: a test monkeypatches
`JsonEventRepository.save` to raise, then runs the command over all four
specimens and the corpus. Measured live against a cloned evidence root,
the events directory is byte-identical before and after.

## 3. The canonical service

`DigitalAssetDecisionService.decide` — the same object the crypto
dossier, `ExecutivePipeline._digital_asset`,
`CandidateResearchService._can_be_described` and the DV6 journal writer
all consume. There is no second constructor of crypto investment
meaning, and the command reads no provider finding, market signal,
committee row or legacy arithmetic.

## 4–7. The specimens, live

| | printed |
|---|---|
| **BTC** | `INVESTIGATE` · `conviction: withheld` · Supply Governance's conclusion under *What is established*, carrying its own "investment meaning is not established" clause · Value Capture under *The wrong instrument for this asset — knowledge, never adverse* · `decided under: digital-asset-gates@1` · both judgment ids |
| **ETH** | `INVESTIGATE` · the evidenced value-capture mechanism established · the issuance-rule gap and the maximum-supply silence under *Open questions, each in its owner's words* |
| **TAO** | `MONITOR` · a judged decision, its applicability findings named — never *"no judgment recorded"* |
| **ARB** | `INVESTIGATE` · the 81% circulating-supply spread under *Material uncertainty — stated as uncertainty, never as adverse*, and absent from every other section |

No rank, no score, no strengths, no risks appear for any of them —
asserted on *labelled numbers* rather than on words, because the words
legitimately appear: the withheld-conviction sentence says *"no score
exists for a digital asset"*, which is the platform refusing to produce
one. A word blacklist would have forbidden the refusal along with the
thing refused.

## 8. Refusals

An asset no committee has judged — whether a token nobody has looked at,
an equity, or an unknown ticker — gets one true sentence:

> *AAPL — no committee has recorded a judgment for this asset, so this
> platform has reached no decision about it. That is a statement about
> this platform rather than about the asset, and it is not a verdict
> against it.*

It claims nothing about what the symbol *is*, which is the honest limit
of a surface that cannot resolve an asset class without the brain
pipeline — and it is the sentence `considerations` already prints for
the same state. **Not judged never becomes REJECT or a default MONITOR**,
asserted directly. Malformed arguments exit 2 through argparse, as every
other verb does.

## 9. Journal and dedup

Zero writes, so DV6's dedup is untouched and cannot be duplicated by
this command. Repeated invocation changes nothing, which is the whole
point of the read/write split.

## 10. Regression

**0 movements** on DV2's six-equity panel and **0** across all fourteen
portfolio holdings. The change surface is one modified file —
`app/cli.py`, **+25 lines of registration** — plus two new files. **No
existing command file was touched**, so no equity or fund verb could
have changed behaviour.

## 11. Test protection

Every specimen is declared in the module, and no test reads the acquired
store, so an empty evidence root cannot silence them.
`test_the_suite_exercised_every_specimen` asserts the corpus is exactly
BTC/ETH/TAO/ARB and fails unless each was actually rendered. The stub is
a *subclass* of the canonical service rather than a mock, so anything
the command calls that the stub does not declare still reaches the live
implementation.

## 12–13. Gates

`pytest -q` 3062 passed · ruff check + format clean · `mypy app` clean
(598 files) · `npm run build` clean · production `data/` byte-identical,
and the live runs used a cloned evidence root whose events directory
hashed identically before and after.

## 14. Authority divergence

**None found.** Every consumer of crypto investment meaning — dossier,
portfolio, executive brief, research admission, journal, and now the CLI
— reaches `DigitalAssetDecisionService` and nothing else. The arc
DV1→DV7 closes with one judgment, one admission rule, one history and
one answer.
