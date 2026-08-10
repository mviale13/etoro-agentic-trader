"""S5.3: what a supply policy actually tells an investor.

A measurement slice. Its findings are the reason no second quality
factor was created, so they are asserted here rather than left in a
document — a conclusion that only lives in prose cannot fail when the
corpus moves under it.

The two that decide the slice:

  predictability does not discriminate — all three mechanical assets are
  equally explicit and equally projectable, and only mutability separates
  them, one against two

  magnitude does discriminate — five-year expansion runs 2.7% to 14.5%,
  a factor of five, across those same three assets

**Nothing here reads the network.** The readings are those recorded on
2026-08-10, pushed through the real provider.
"""

from __future__ import annotations

from typing import Any

from app.domain.mechanical_issuance import MechanicalIssuance, RuleMutability
from app.providers.issuance_rule_provider import IssuanceRuleProvider
from tests.reachability import reachable

# ── the recorded readings ───────────────────────────────────────────

_BTC_HEIGHT = 961_892
_BTC_CIRCULATION = 2_006_838_666_655_096

_ADA_TOTALS = {
    "epoch_no": 648,
    "circulation": "36550320207145109",
    "treasury": "1450053248585177",
    "reward": "797735740883044",
    "supply": "38803572882173527",
    "reserves": "6196427117826473",
    "fees": "29001560197",
    "deposits_stake": "4404684000000",
    "deposits_drep": "530000000000",
    "deposits_proposal": "500000000000",
}

_ADA_PARAMS = [{"monetary_expand_rate": 0.003, "treasury_growth_rate": 0.2}]
_ADA_INFO = [{"start_time": 1_786_139_091, "end_time": 1_786_571_091}]

_SOL_GOVERNOR = {"initial": 0.08, "taper": 0.15, "terminal": 0.015}
_SOL_RATE = {"epoch": 1014, "total": 0.03704903227186841}


class _Cardano:
    SURFACE = type("S", (), {"name": "Cardano ledger totals"})
    RULE = "ada-ledger-supply/1"

    @staticmethod
    def totals() -> dict[str, object]:
        return dict(_ADA_TOTALS)


class _Recorded(IssuanceRuleProvider):
    def __init__(self) -> None:
        super().__init__(cardano=_Cardano())  # type: ignore[arg-type]

    @staticmethod
    def _get(
        url: str,
        params: dict[str, str] | None = None,
        as_json: bool = True,
    ) -> Any:
        if "blocks/tip/height" in url:
            return str(_BTC_HEIGHT)
        if "blockchair" in url:
            return {
                "data": {"blocks": _BTC_HEIGHT + 1, "circulation": _BTC_CIRCULATION}
            }
        if "epoch_params" in url:
            return _ADA_PARAMS
        if "epoch_info" in url:
            return _ADA_INFO
        raise AssertionError(url)

    @staticmethod
    def _rpc(method: str) -> Any:
        if method == "getInflationGovernor":
            return dict(_SOL_GOVERNOR)
        if method == "getInflationRate":
            return dict(_SOL_RATE)
        raise AssertionError(method)


def _rules() -> dict[str, MechanicalIssuance]:
    provider = _Recorded()

    found = {symbol: provider.rule(symbol) for symbol in ("BTC", "ADA", "SOL")}

    assert all(rule is not None for rule in found.values())

    return {symbol: rule for symbol, rule in found.items() if rule is not None}


def _expansion(symbol: str, years: int) -> float:
    """Five-year supply expansion as a share of what exists today."""

    rules = _rules()
    rule = rules[symbol]

    named = {p.name: p.value for p in rule.parameters}

    if symbol == "BTC":
        provider = _Recorded()
        tip = int(named["tip height"])
        blocks = int(years * IssuanceRuleProvider.BTC_BLOCKS_PER_YEAR)
        new = provider._btc_emitted(tip + blocks) - provider._btc_emitted(tip)  # noqa: SLF001
        emitted = rule.state.emitted
        assert emitted is not None
        return new / 1e8 / emitted

    if symbol == "ADA":
        reserves = named["reserves"]
        rho = named["rho, monetary expansion rate"]
        epochs = int(years * 365.25 * 86_400 / named["epoch length"])
        emitted = rule.state.emitted
        assert emitted is not None
        return reserves * (1 - (1 - rho) ** epochs) / emitted

    # Solana's rate *is* the expansion, so no supply figure is needed.
    rate = named["current rate"]
    cumulative = 1.0
    for _ in range(years):
        cumulative *= 1 + rate
        rate = max(named["terminal rate"], rate * (1 - named["taper"]))
    return cumulative - 1


# ── C: predictability does not discriminate ─────────────────────────


def test_all_three_mechanical_assets_are_equally_explicit() -> None:
    """The finding that stopped predictability becoming factor #2.

    Every parameter of every rule is read from the chain, and every rule
    projects. A factor scoring explicitness would give all three the
    same answer — a measure that cannot tell three assets apart is not
    a measure of those assets.
    """

    for symbol, rule in _rules().items():
        assert rule.parameters_are_all_read, symbol
        assert rule.is_projectable, symbol


def test_only_mutability_separates_them_and_it_is_one_against_two() -> None:
    """The single dimension with any discriminating power, and it is thin.

    One protocol-fixed asset is not a corpus. Banding on it would rest
    the whole distinction on Bitcoin being the only example of its kind
    that this platform reads.
    """

    mutability = {symbol: rule.mutability for symbol, rule in _rules().items()}

    assert mutability["BTC"] is RuleMutability.PROTOCOL_FIXED
    assert mutability["ADA"] is RuleMutability.GOVERNANCE_PARAMETER
    assert mutability["SOL"] is RuleMutability.GOVERNANCE_PARAMETER

    protocol_fixed = [
        s for s, m in mutability.items() if m is RuleMutability.PROTOCOL_FIXED
    ]

    assert len(protocol_fixed) == 1


# ── C: magnitude does discriminate ──────────────────────────────────


def test_five_year_expansion_spans_a_factor_of_five() -> None:
    """Same three assets, same predictability, and magnitudes far apart.

    That is what makes them two questions rather than one: a single
    number combining them would have to weigh a dimension on which the
    corpus is unanimous against one on which it spreads five-fold.
    """

    expansion = {symbol: _expansion(symbol, 5) for symbol in ("BTC", "ADA", "SOL")}

    assert 0.02 < expansion["BTC"] < 0.03
    assert 0.10 < expansion["ADA"] < 0.11
    assert 0.14 < expansion["SOL"] < 0.15

    assert max(expansion.values()) / min(expansion.values()) > 4


def test_the_two_orderings_are_not_the_same() -> None:
    """Predictability ranks BTC first and ties the other two; magnitude
    ranks all three. They cannot be one factor."""

    rules = _rules()

    by_mutability = sorted(
        rules,
        key=lambda s: 0 if rules[s].mutability is RuleMutability.PROTOCOL_FIXED else 1,
    )
    by_expansion = sorted(rules, key=lambda s: _expansion(s, 5))

    assert by_expansion == ["BTC", "ADA", "SOL"]
    # Bitcoin leads both, and below it predictability says nothing while
    # magnitude puts ADA and SOL 4 points apart.
    assert by_mutability[0] == "BTC"
    assert abs(_expansion("ADA", 5) - _expansion("SOL", 5)) > 0.03


# ── the horizons, and what they may claim ───────────────────────────


def test_a_projection_is_never_presented_as_a_fact() -> None:
    """Wording is the whole safeguard here.

    The surface says *under the currently observed policy*, and every
    horizon carries the rule version that produced it.
    """

    code = reachable("app/commands/issuance.py", with_literals=True)

    # The heading the projection sits under, and the disclaimer beneath
    # it. Both are literals in the rendering, so both are reachable.
    assert "under the currently observed policy" in code
    assert "not a forecast and not an observation" in code

    # And every horizon can be re-run: it names the rule that made it.
    for rule in _rules().values():
        assert rule.path

        for step in rule.path:
            assert step.rule_version == rule.provenance.rule_version


def test_solana_expansion_needs_no_supply_figure() -> None:
    """Its rate *is* the expansion, so the projection avoids the one
    quantity Solana does not publish."""

    rule = _rules()["SOL"]

    assert rule.state.emitted is None

    # And the expansion is still computable.
    assert _expansion("SOL", 1) > 0


# ── the boundaries the ruling set ───────────────────────────────────


def test_the_surface_scores_nothing_and_prices_nothing() -> None:
    """Section 16: no price, no valuation, no market context."""

    code = reachable("app/commands/issuance.py")

    for forbidden in (
        "price",
        "market_cap",
        "fdv",
        "valuation",
        "quality",
        "score",
        "band",
        "dilut",
    ):
        assert forbidden not in code, forbidden


def test_nothing_that_decides_can_reach_the_issuance_layer() -> None:
    """Acquired, rendered, and consumed by no score."""

    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent

    for target in (
        "app/services/crypto_asset_quality_service.py",
        "app/domain/crypto_quality.py",
        "app/services/company_signal_service.py",
    ):
        text = (root / target).read_text(encoding="utf-8")

        assert "mechanical_issuance" not in text, target
        assert "issuance_rule_provider" not in text, target


def test_the_quality_model_is_unchanged() -> None:
    """S5.3 measured and built no factor. Quorum stands, and the one
    scorable question is still the only one."""

    from app.domain.crypto_quality import MINIMUM_SCORED, READINESS, RULES

    assert MINIMUM_SCORED == 2
    assert len(RULES) == 1

    scorable = [key for key, ruling in READINESS.items() if ruling.readiness.scores]

    assert len(scorable) == 1
