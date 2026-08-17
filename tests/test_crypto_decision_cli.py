"""Asking the canonical crypto decision from a terminal.

DV7, and the last surface of the convergence arc. The command is a thin
adapter: it owns no rule, no threshold and no wording of its own, and
every sentence it prints was worded by the layer that established it.

Pinned here:

1. **One authority.** The output is the canonical decision's own
   sentences, verbatim — so a wording that drifted from the dossier
   would fail rather than diverge quietly.
2. **Read-only.** `judge` is the CLI's one writing verb, and its own
   docstring says why: rendering must not manufacture events. Printing a
   projection over what `judge` recorded appends nothing, asserted
   against a repository that raises if written to.
3. **Nothing is fabricated.** No conviction, no rank, no strengths, no
   risks, no score — and the absence of a conviction is *named* rather
   than left blank.
4. **Not judged is not a verdict.** An asset no committee has looked at
   is reported as exactly that, and never as REJECT or a default
   MONITOR.

**No test here reads the acquired store.** Every specimen is declared,
so none can pass by exercising zero of them, and
`test_the_suite_exercised_every_specimen` fails unless all four were
rendered.
"""

from __future__ import annotations

import pytest

from app.cio.decision_state import DecisionState
from app.cio.digital_asset_decision import (
    DigitalAssetDecision,
    UnresolvedQuestion,
)
from app.commands.crypto_decision import CryptoDecisionCommand
from app.services.digital_asset_decision_service import (
    DigitalAssetDecisionService,
)

#: The DV3 specimens, each carrying the shape its live judgment has.
SPECIMENS: dict[str, DigitalAssetDecision] = {
    "BTC": DigitalAssetDecision(
        symbol="BTC",
        state=DecisionState.INVESTIGATE,
        rationale="Structural evidence is established and quoted below.",
        established=(
            "Supply Governance Committee established that new supply is "
            "created by a mechanical rule. On its investment meaning, what "
            "this conclusion means for an investment case is not established "
            "by this platform.",
        ),
        not_applicable=(
            "Value Capture Committee: This asset's established economic role "
            "is monetary, so the question is the wrong instrument.",
        ),
        judged=True,
        judgment_ids=("20260811T122514-e730d6ad", "20260811T122548-7739b78e"),
    ),
    "ETH": DigitalAssetDecision(
        symbol="ETH",
        state=DecisionState.INVESTIGATE,
        rationale="Structural evidence is established and quoted below.",
        established=(
            "Value Capture Committee established that measured network "
            "activity is captured for the token by an evidenced mechanism.",
        ),
        unresolved=(
            UnresolvedQuestion(
                owner="Supply Governance Committee",
                stated="No mechanical issuance rule is held for this asset.",
            ),
        ),
        judged=True,
        judgment_ids=("20260811T122514-41c52439",),
    ),
    "TAO": DigitalAssetDecision(
        symbol="TAO",
        state=DecisionState.MONITOR,
        rationale=(
            "No structural question is yet established as applicable to this "
            "asset. Establishing the asset's economic role is the advance."
        ),
        unresolved=(
            UnresolvedQuestion(
                owner="Supply Governance Committee",
                stated="No economic role is established for this asset.",
            ),
        ),
        judged=True,
        judgment_ids=("20260811T122514-77f93628",),
    ),
    "ARB": DigitalAssetDecision(
        symbol="ARB",
        state=DecisionState.INVESTIGATE,
        rationale="Structural evidence is established and quoted below.",
        established=(
            "Value Capture Committee established that measured network "
            "activity is not captured for the token.",
        ),
        material_uncertainties=(
            "Circulating supply cannot be stated as a single figure: "
            "available estimates run from 1.27 billion to 6.61 billion, a "
            "spread of 81%.",
        ),
        judged=True,
        judgment_ids=("20260811T122514-7ece7caa",),
    ),
}

#: Every symbol a test below actually rendered. Asserted at the end, so a
#: fixture that stopped producing specimens fails loudly rather than
#: leaving a parametrised test passing over an empty list.
RENDERED: set[str] = set()


class StubDecisions(DigitalAssetDecisionService):
    """The canonical service with declared answers.

    Subclassed rather than mocked so the command is exercised through
    the real seam: anything it calls that the stub does not declare
    would still reach the live implementation and fail loudly.
    """

    def decide(self, symbol: str) -> DigitalAssetDecision:
        asset = symbol.upper().strip()

        return SPECIMENS.get(
            asset,
            DigitalAssetDecision(
                symbol=asset,
                state=DecisionState.MONITOR,
                rationale="No committee has recorded a judgment about this asset.",
                judged=False,
            ),
        )


def render(symbol: str | None, capsys: pytest.CaptureFixture[str]) -> str:
    code = CryptoDecisionCommand(service=StubDecisions()).run(symbol)

    assert code == 0

    if symbol is not None and symbol.upper().strip() in SPECIMENS:
        RENDERED.add(symbol.upper().strip())

    return capsys.readouterr().out


# ── 1. the canonical decision, faithfully ───────────────────────────


@pytest.mark.parametrize("symbol", sorted(SPECIMENS))
def test_the_output_is_the_canonical_decisions_own_words(
    symbol: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One authority: the command quotes, it does not paraphrase."""

    decision = SPECIMENS[symbol]

    out = render(symbol, capsys)

    assert f"{symbol} — {decision.state.value}" in out
    assert _flat(decision.rationale) in _flat(out)
    assert _flat(decision.ceiling) in _flat(out)

    for line in (
        *decision.established,
        *decision.not_applicable,
        *decision.material_uncertainties,
    ):
        # Wrapped for the terminal, so compared on the words rather than
        # the line breaks.
        assert _flat(line) in _flat(out)

    for item in decision.unresolved:
        assert _flat(f"{item.owner}: {item.stated}") in _flat(out)


@pytest.mark.parametrize("symbol", sorted(SPECIMENS))
def test_the_authority_and_what_it_rests_on_are_printed(
    symbol: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`digital-asset-gates@1`, and the exact judgments beneath it."""

    out = render(symbol, capsys)

    assert "decided under: digital-asset-gates@1" in out

    for reference in SPECIMENS[symbol].judgment_ids:
        assert reference in out


@pytest.mark.parametrize("symbol", sorted(SPECIMENS))
def test_the_absent_conviction_is_named_and_never_a_number(
    symbol: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Withheld, said aloud. A blank would read as a surface that forgot."""

    out = render(symbol, capsys)

    assert "conviction: withheld" in out
    assert "Conviction: 0" not in out
    assert "conviction: 0" not in out


@pytest.mark.parametrize("symbol", sorted(SPECIMENS))
def test_nothing_is_fabricated(
    symbol: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No rank, no score, no strengths, no risks — the arc's four laws.

    Asserted on *labelled numbers* rather than on words, because the
    words legitimately appear: the withheld-conviction sentence says
    "no score exists for a digital asset", which is the platform
    refusing to produce one. A word blacklist would have forbidden the
    refusal along with the thing refused.
    """

    import re

    out = _flat(render(symbol, capsys))

    labelled_number = re.compile(
        r"\b(rank|score|conviction|strength|risk)\w*\s*[:=]?\s*-?\d",
        re.IGNORECASE,
    )

    assert labelled_number.search(out) is None, out

    # "Against this asset" is the adverse heading, and it must be absent
    # while the domain licenses nothing adverse.
    assert "Against this asset" not in out


# ── 2. the specimens that must stay themselves ──────────────────────


def test_bittensor_monitor_is_reported_as_a_decision(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """MONITOR is judged, and its reason is applicability rather than doubt."""

    out = render("TAO", capsys)

    assert "TAO — MONITOR" in out
    assert "economic role" in out
    assert "no committee has recorded a judgment" not in out.lower()


def test_arbitrum_spread_is_uncertainty_and_not_a_risk(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = render("ARB", capsys)

    assert "Material uncertainty" in out
    assert "never as adverse" in out
    assert "spread of 81%" in _flat(out)
    assert "Against this asset" not in out


def test_bitcoins_wrong_instrument_finding_is_labelled_as_knowledge(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = render("BTC", capsys)

    assert "knowledge, never adverse" in out
    assert "Against this asset" not in out


# ── 3. refusals, and the controls around them ───────────────────────


def test_an_asset_with_no_recorded_judgment_is_not_a_verdict(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Not judged is not REJECT, and not a default MONITOR either."""

    out = render("NEWTOKEN", capsys)

    assert "no committee has recorded a judgment" in out
    assert "statement about this platform" in _flat(out)

    for forbidden in ("REJECT", "MONITOR", "INVESTIGATE"):
        assert forbidden not in out


def test_an_equity_reaches_no_crypto_verdict(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The non-crypto control: the company path is not rerouted here.

    The command claims nothing about what AAPL *is* — it reports only
    what this platform holds, which is the honest limit of a surface
    that cannot resolve an asset class without the brain pipeline.
    """

    out = render("AAPL", capsys)

    assert "AAPL" in out
    assert "no committee has recorded a judgment" in out
    assert "INVESTIGATE" not in out
    assert "conviction" not in out.lower()


def test_the_corpus_lists_every_asset_without_ordering_them(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from app.domain.crypto_archetype import ASSIGNMENTS

    out = render(None, capsys)

    for asset in ASSIGNMENTS:
        assert asset in out

    assert "not ordered against each other" in _flat(out)
    assert "rank" not in _flat(out).lower()


# ── 4. read-only, proved rather than asserted ───────────────────────


def test_the_command_cannot_write_to_the_journal(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI's own law: rendering must not manufacture events.

    Proved by making a write raise rather than by reading the command
    and believing it — a future edit that journalled here would fail
    this test rather than silently start appending on every print.
    """

    from app.repositories.json_event_repository import JsonEventRepository

    def explode(*_: object, **__: object) -> None:
        raise AssertionError("crypto-decision must not write to the journal")

    monkeypatch.setattr(JsonEventRepository, "save", explode)

    for symbol in (*sorted(SPECIMENS), None):
        render(symbol, capsys)


def test_the_command_is_registered_and_reaches_the_canonical_service() -> None:
    """The wiring, so the verb cannot exist and be unreachable."""

    import inspect

    from app import cli

    source = inspect.getsource(cli)

    assert '"crypto-decision"' in source
    assert "crypto_decision.run(args.symbol)" in source

    from app.commands import crypto_decision

    assert (
        crypto_decision.CryptoDecisionCommand()._service.__class__
        is DigitalAssetDecisionService
    )


# ── 5. the guard against a suite that renders nothing ───────────────


def test_the_suite_exercised_every_specimen() -> None:
    """DV5's hazard, carried forward.

    Nothing here reads the acquired store, so an empty evidence root
    cannot silence these tests — but a fixture that stopped producing
    specimens would still leave the parametrised tests passing over an
    empty list.
    """

    assert set(SPECIMENS) == {"BTC", "ETH", "TAO", "ARB"}
    assert RENDERED == set(SPECIMENS), (
        "every specimen must be rendered by some test above"
    )


def _flat(text: str) -> str:
    return " ".join(text.split())
