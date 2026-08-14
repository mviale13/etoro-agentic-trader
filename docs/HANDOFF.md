# Handoff — start here

**State at `3dee58e` (main, clean, in sync).** Read `CLAUDE.md` first,
then this. Everything below was measured on this tree, not recalled.

---

## What just shipped, newest first

| PR | What | Where it is documented |
|---|---|---|
| #125 | **Crypto questions grouped by what is held.** Block 32–35% → 24% of the page; the doubled applicability reason (10× on BTC) fixed; 19 questions before and after. | `CRYPTO_DOSSIER_UI.md` §question taxonomy |
| #124 | **Protocol economics reach the crypto dossier.** Served, parsed without a `facts` field, rendered by nothing. HYPE now shows $842.7k fees / $534.9k to holders, both entities apart. | `CRYPTO_DOSSIER_UI.md` §protocol economics |
| #123 | **Judged market facts reach the crypto dossier.** Parser had no `facts` key; the unjudged-committee crash blanked *every* crypto page on a fresh clone. | `CRYPTO_DOSSIER_UI.md` §judged market facts |
| #122 | **F3 — why the recommendation changed.** "Stable — 6 consecutive reviews" over 8 state changes. | `EQUITY_DOSSIER_FIDELITY.md` §9 |
| `70e8522` | **DP1 — segment naming disambiguation.** A brand named after the filer stole a segment's description. **Schema 14, no cross-schema read.** | `DESCRIPTION_OWNERSHIP_ALTITUDE.md` §8 |

---

## The next three, in the owner's order

1. **Eliminate repeated committee / reason / maturity noise.** Measured
   on BTC: the committee conclusion renders twice (once in *What can
   usefully be said*, once in *What each committee concluded*); the lens
   sentence repeats 7×; *"First observed on one capture"* repeats 13×
   under a heading that already said "1 capture recorded"; `Times
   convened: 5` and `Evidence it weighed 0 findings` are counters with
   no investor meaning.
2. **Design the crypto decision bridge.** The page ends *"for digital
   assets it does not yet recommend at all."* Not before the noise is
   cleared.
3. **Asset Quality is explicitly NOT next.** Its weakness is truthful —
   the platform has not earned a score. The UX mistake was letting it
   occupy more space than the strong intelligence, which #124/#125
   addressed.

---

## Two blockers you will hit

**Model credits are exhausted.** Fresh 429
`credit_balance_exhausted`, confirmed by `movrvest observe VOW3.DE
--to 10` writing `invalid_extraction`. No reader work is possible.
`MOVRVEST_READER_PROVIDER` is unset and there is **no Anthropic key**,
so OpenAI is the only route.

**The knowledge corpus is dark.** Schema 14 takes no cross-schema read,
so all 33 entries read as unread and every equity dossier shows
*"Not established"* for the earned playbook. That is by design and
honest. It restores with `movrvest observe SYMBOL --to 10` once funded —
**read the log, not the exit code**.

**VOW3.DE is frozen.** `DP1 complete → schema-14 validation blocked →
DP2 unchosen`. Do not infer DP2 from schema-11/12 observations, and do
not touch the `services` co-tag or the `DIVERSIFIED` defect.

---

## Traps this session actually hit

- **HEAD isolation caught three environment dependencies the working
  tree hid**: `data/events/` is gitignored (F3's tests read the
  developer's tree), `.env` is absent in the archive (a test called
  `/executive/` which needs `TRADING_MODE`), and `data/cache/` is
  gitignored (protocol tests). Always `git archive HEAD` before
  trusting a commit.
- **`JsonEventRepository` and `JsonCompanyKnowledgeStore` default to
  path literals** (`data/events`, `data/knowledge`) that
  `conftest.py`'s hermetic root cannot redirect. Declare the path in
  the test; do not change the production default without a ruling.
- **There is no JavaScript test runner.** Frontend proofs are
  `npm run build` (which typechecks) plus the rendered page, with the
  committed contract pinned in Python.
- **Check the rendered page, not the payload.** #124 was found only by
  reading eight rendered dossiers.

---

## The architectural guard worth knowing about

`tests/test_crypto_dossier_reaches_the_page.py` — the same
parsed-but-never-rendered defect was found **twice** in one file, so the
guard is about the class: every top-level key the route serves must be
read by `parseDossier` (scoped to that function — `record.facts` also
appears in the journal parser, and a file-wide search reported the
dropped section as read), and every field `CryptoDossier` parses must be
referenced by the page. Both halves were verified by re-creating the two
historical defects and watching the suite fail.

---

## Standing rules

- Every PR answers *what becomes better for the investor?* Architecture
  is frozen; only the owner lifts it (Constitution §23–24).
- The frontend calculates nothing analytical; absences carry the
  backend's own reason.
- Zero paid model calls unless explicitly funded and authorised.
