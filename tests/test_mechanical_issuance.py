"""S5.2b: what supply rule a protocol defines, and what follows from it.

Three chains publish enough to reconstruct how their supply grows, and
the differences between them are the finding: Bitcoin's rule is
consensus with unserved parameters, Cardano serves every parameter
including the epoch length, and Solana — which has no maximum at all —
publishes its whole schedule in one call.

**Nothing here reads the network.** Every case runs on the readings
recorded during the S5.2 measurement on 2026-08-10, pushed through the
real provider.
"""

from __future__ import annotations

from typing import Any

from app.domain.evidence_standing import EvidenceStanding
from app.domain.mechanical_issuance import (
    IssuanceMechanism,
    MechanicalIssuance,
    RuleMutability,
)
from app.providers.issuance_rule_provider import IssuanceRuleProvider
from tests.reachability import reachable

# ── the recorded readings ───────────────────────────────────────────

#: Bitcoin at the moment the residual was pinned down. Circulation is
#: Blockchair's precise figure at the same tip.
_BTC_HEIGHT = 961_887
_BTC_CIRCULATION = 2_006_837_104_155_096

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

#: 432,000 seconds apart — five days, read rather than remembered.
_ADA_INFO = [{"start_time": 1_786_139_091, "end_time": 1_786_571_091}]

_SOL_GOVERNOR = {
    "foundation": 0.0,
    "foundationTerm": 0.0,
    "initial": 0.08,
    "taper": 0.15,
    "terminal": 0.015,
}

_SOL_RATE = {"epoch": 1014, "total": 0.03704903227186841, "validator": 0.037049}


class _Cardano:
    SURFACE = type("S", (), {"name": "Cardano ledger totals"})
    RULE = "ada-ledger-supply/1"

    @staticmethod
    def totals() -> dict[str, object]:
        return dict(_ADA_TOTALS)


class _Recorded(IssuanceRuleProvider):
    """The real provider with its two wire methods answered from record."""

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


def _rule(symbol: str) -> MechanicalIssuance:
    outcome = _Recorded().rule(symbol)

    assert outcome is not None, symbol

    return outcome


# ── no asset gets an entry it has not earned ────────────────────────


def test_allocation_release_tokens_get_no_mechanical_rule() -> None:
    """The ruling's thirteenth section, made structural.

    Arbitrum's supply arrives because a contract releases an allocation,
    not because a rule creates it. An entry saying so *in the shape of a
    rule* would be a placeholder, and a placeholder on an investment
    surface is a claim.
    """

    for symbol in ("ARB", "HYPE", "1INCH", "TAO", "ETH"):
        assert _Recorded().rule(symbol) is None, symbol


# ── BTC: the rule reproduces, the total does not establish ──────────


def test_bitcoin_is_the_clean_mechanical_case() -> None:
    rule = _rule("BTC")

    assert rule.mechanism is IssuanceMechanism.HALVING_SUBSIDY
    assert rule.mutability is RuleMutability.PROTOCOL_FIXED
    assert rule.parameters_are_all_read
    assert rule.is_projectable

    # Era 4: the subsidy has halved four times.
    subsidy = next(p for p in rule.parameters if p.name == "current subsidy")

    assert subsidy.value == 3.125


def test_bitcoins_emitted_total_is_marked_derived_and_stays_claimed() -> None:
    """The residual is unexplained, so the total is not an established fact.

    The distinction that keeps the slice honest: Bitcoin's emitted figure
    is the *rule run to the tip*, not something a source published, and
    the difference from the one precise independent figure has not been
    itemised.
    """

    rule = _rule("BTC")

    assert rule.state.emitted_is_derived
    assert rule.standing is EvidenceStanding.CLAIMED

    residual = " ".join(rule.caveats)

    assert "28.95844904" in residual
    assert "constant to the satoshi" in residual
    assert "has not itemised it" in residual

    # And the honest limit on the comparison itself.
    assert "cannot tell the two apart" in residual


def test_the_projection_names_its_own_assumption() -> None:
    """Block intervals vary with hash rate, so a year is a convention.

    The horizons say so rather than presenting a date as a measurement.
    """

    rule = _rule("BTC")

    horizons = [step.horizon for step in rule.path]

    assert any("next halving" in h for h in horizons)
    assert all("ten-minute target" in h or "halving" in h for h in horizons), horizons

    assert any("vary with hash rate" in c for c in rule.caveats)

    for step in rule.path:
        assert step.rule_version == IssuanceRuleProvider.BTC_RULE


# ── ADA: nothing remembered ─────────────────────────────────────────


def test_cardano_reads_every_parameter_including_the_epoch_length() -> None:
    """The strongest gate-3 case in the corpus.

    rho and tau are protocol parameters the chain serves, and the epoch
    length is the difference between two timestamps the chain prints —
    so the projection leans on no constant this platform remembered.
    """

    rule = _rule("ADA")

    assert rule.mechanism is IssuanceMechanism.RESERVE_DRAW
    assert rule.provenance.constants == ()
    assert rule.parameters_are_all_read

    named = {p.name: p for p in rule.parameters}

    assert named["rho, monetary expansion rate"].value == 0.003
    assert named["tau, treasury growth rate"].value == 0.2
    assert named["epoch length"].value == 432_000.0

    for parameter in rule.parameters:
        assert "GET " in parameter.read_from, parameter.name


def test_cardano_separates_what_is_drawn_from_what_reaches_holders() -> None:
    """The ruling's fourth section, and only Cardano can answer it.

    tau of every draw goes to the treasury — a pot that is itself
    excluded from circulating supply — so the supply reaching holders is
    smaller than the supply issued, and the two are reported apart.
    """

    rule = _rule("ADA")

    drawn = [s for s in rule.path if "drawn from reserves" in s.horizon]
    holders = [s for s in rule.path if "reaching holders" in s.horizon]

    assert drawn and holders

    for a, b in zip(drawn, holders, strict=True):
        assert b.issuance < a.issuance
        # tau is 0.2, so holders receive exactly four fifths.
        assert abs(b.issuance / a.issuance - 0.8) < 1e-9


def test_cardanos_rule_is_governance_changeable_and_says_so() -> None:
    """A reproducible projection is not an immutable one.

    rho and tau are parameters Cardano's own governance can move, which
    is not the same epistemic footing as Bitcoin's consensus schedule
    even though both project cleanly today.
    """

    rule = _rule("ADA")

    assert rule.mutability is RuleMutability.GOVERNANCE_PARAMETER
    assert any("governance" in c for c in rule.caveats)

    assert _rule("BTC").mutability is RuleMutability.PROTOCOL_FIXED


# ── SOL: uncapped is not unruled ────────────────────────────────────


def test_an_uncapped_asset_can_have_the_best_published_rule() -> None:
    """The ruling's twelfth section, answered.

    Having no maximum does not mean having no rule. Solana publishes its
    whole schedule — where it started, how fast it falls, where it stops
    — in a single call, which is more than any capped asset in the
    corpus except Cardano.
    """

    rule = _rule("SOL")

    assert rule.mechanism is IssuanceMechanism.TAPERING_INFLATION
    assert rule.provenance.constants == ()
    assert rule.parameters_are_all_read

    named = {p.name: p.value for p in rule.parameters}

    assert named["initial rate"] == 0.08
    assert named["taper"] == 0.15
    assert named["terminal rate"] == 0.015


def test_solana_publishes_no_supply_so_none_is_invented() -> None:
    """A zero would be a figure nobody measured, on an investment object."""

    rule = _rule("SOL")

    assert rule.state.emitted is None
    assert rule.state.current_rate is not None

    assert any("rate, not an amount" in c for c in rule.caveats)


def test_the_taper_falls_towards_the_floor_and_never_below() -> None:
    rule = _rule("SOL")

    rates = [step.issuance for step in rule.path]

    assert rates == sorted(rates, reverse=True)
    assert all(rate >= 0.015 for rate in rates)


# ── the boundaries ──────────────────────────────────────────────────


def test_the_layer_scores_nothing() -> None:
    """A published rule is not thereby a good rule."""

    for module in (
        "app/domain/mechanical_issuance.py",
        "app/providers/issuance_rule_provider.py",
    ):
        code = reachable(module)

        for forbidden in ("dilut", "band", "quality", "score", "verdict"):
            assert forbidden not in code, (module, forbidden)

    # And nothing that decides can reach the layer at all.
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


def test_every_projection_carries_its_rule_version() -> None:
    """A projection nobody can re-run is a number with a story."""

    for symbol in ("BTC", "ADA", "SOL"):
        rule = _rule(symbol)

        for step in rule.path:
            assert step.rule_version
            assert step.rule_version == rule.provenance.rule_version


def test_nothing_here_establishes_yet() -> None:
    """S5.2b acquires evidence and decides nothing.

    Every rule is served as a claim: the layer is consumed by no score,
    and the ruling asked for readiness rather than a verdict.
    """

    for symbol in ("BTC", "ADA", "SOL"):
        assert _rule(symbol).standing is EvidenceStanding.CLAIMED
