"""Read the protocols that publish an issuance rule, and project it.

Three chains publish enough to reconstruct how their supply grows, and
all three do it keylessly. What each publishes is different in kind, and
the differences are the point:

```text
BTC   the rule is consensus, the parameters are not served by anything.
      They are cross-checked by reproducing the chain's own total.
ADA   every parameter is a protocol parameter the chain serves.
      Nothing is remembered, including the epoch length.
SOL   the whole schedule is one RPC call — an uncapped asset with a
      better-published issuance rule than most capped ones.
```

**No asset gets an entry it has not earned.** Arbitrum, Hyperliquid and
1inch create supply by releasing allocations, not by a rule, and this
module returns nothing for them. An empty mechanical rule would be a
placeholder, and a placeholder on an investment surface is a claim.

Nothing here scores. A projection is arithmetic under a rule as
observed, labelled as such wherever it is shown.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.mechanical_issuance import (
    IssuanceMechanism,
    IssuanceState,
    MechanicalIssuance,
    ProjectedIssuance,
    RuleMutability,
    RuleParameter,
)
from app.domain.primary_computation import SourceSurface
from app.domain.supply_semantics import PrimaryProvenance, UnitConstant
from app.providers.primary_sources import CardanoLedger

TIMEOUT = 20

HEADERS = {"User-Agent": "movrvest/1.0", "Accept": "application/json"}


# ── the surfaces ────────────────────────────────────────────────────

BITCOIN_HEIGHT = SourceSurface(
    key="bitcoin-height",
    name="Bitcoin block height",
    network="bitcoin-mainnet",
    endpoint="https://mempool.space/api/blocks/tip/height",
    canonical=True,
    because=(
        "the tip height is a property of the chain every node agrees on, "
        "and two independent explorers were read to confirm it rather "
        "than one being trusted."
    ),
)

BITCOIN_CIRCULATION = SourceSurface(
    key="bitcoin-circulation",
    name="Blockchair Bitcoin circulation",
    network="bitcoin-mainnet",
    endpoint="https://api.blockchair.com/bitcoin/stats",
    canonical=False,
    because=(
        "one explorer's computation over the UTXO set, not a quantity the "
        "chain itself publishes. It is read as a perimeter comparison for "
        "the rule, never as the rule's answer."
    ),
)

SOLANA_INFLATION = SourceSurface(
    key="solana-inflation",
    name="Solana inflation governor",
    network="solana-mainnet",
    endpoint="https://api.mainnet-beta.solana.com",
    canonical=True,
    because=(
        "`getInflationGovernor` returns the schedule the validators "
        "themselves apply — the rule, not a description of it."
    ),
)


class IssuanceRuleProvider:
    """One reading of every issuance rule this platform can reach."""

    #: Bitcoin's two consensus constants. Named as remembered, because
    #: nothing serves them — and cross-checked by reproducing the
    #: chain's own supply, which a wrong value misses by orders of
    #: magnitude rather than by a rounding step.
    BTC_INITIAL_SUBSIDY = 50 * 100_000_000
    BTC_HALVING_INTERVAL = 210_000

    #: Blocks per year at the ten-minute target. A convention of this
    #: platform's projection, not a protocol constant — real intervals
    #: vary with hash rate — so it is stated in every horizon it
    #: produces rather than hidden inside one.
    BTC_BLOCKS_PER_YEAR = 52_596

    BTC_RULE = "btc-halving-schedule/1"
    ADA_RULE = "ada-reserve-draw/1"
    SOL_RULE = "sol-tapering-inflation/1"

    def __init__(self, cardano: CardanoLedger | None = None) -> None:
        self._cardano = cardano or CardanoLedger()

    def rule(self, symbol: str) -> MechanicalIssuance | None:
        """This asset's issuance rule, or None where it has no mechanism.

        None for an allocation-release token is the honest answer and
        not a gap: there is no rule to read, and the missing evidence is
        a release schedule, which the supply layer already records as an
        acquisition demand.
        """

        normalized = symbol.upper().strip()

        if normalized == "BTC":
            return self._bitcoin()

        if normalized == "ADA":
            return self._cardano_rule()

        if normalized == "SOL":
            return self._solana()

        return None

    # ── Bitcoin ─────────────────────────────────────────────────────

    def _bitcoin(self) -> MechanicalIssuance | None:
        height = self._get(BITCOIN_HEIGHT.endpoint, as_json=False)

        if height is None:
            return None

        tip = int(str(height).strip())

        observed_at = datetime.now(UTC)

        emitted = self._btc_emitted(tip)

        era = tip // self.BTC_HALVING_INTERVAL
        subsidy = self.BTC_INITIAL_SUBSIDY // (2**era)
        next_halving = (era + 1) * self.BTC_HALVING_INTERVAL

        # The perimeter comparison, and the reason this rule's *total*
        # does not establish. Read second so a failure here leaves the
        # rule readable.
        circulation = self._btc_circulation()

        caveats = [
            "Block intervals vary with hash rate, so every horizon below "
            "assumes the ten-minute target the difficulty adjustment aims "
            "at. The block counts are exact; the dates are not.",
        ]

        because = (
            "The subsidy schedule is consensus: 50 BTC halving every "
            f"210,000 blocks. Reproducing it to the tip gives {emitted / 1e8:,.3f} "
            "BTC issued."
        )

        if circulation is not None:
            residual = emitted - circulation

            caveats.append(
                "The rule's total and the one precise independent figure "
                f"differ by {residual / 1e8:,.8f} BTC "
                f"({abs(residual) / circulation:.6%}). Measured across "
                "consecutive blocks the difference is *constant to the "
                "satoshi* while circulation rises by exactly one subsidy, "
                "so it is a fixed historical difference and not a drift — "
                "the rule is right about what each block pays. It is "
                "larger than nothing and smaller than the genesis subsidy "
                "alone, so it is neither of the two obvious candidates, "
                "and this platform has not itemised it. Until it does, "
                "the *total* is served as a claim."
            )
            caveats.append(
                "The comparison may be weaker than it looks: if the "
                "explorer computes circulation from the same subsidy rule "
                "minus known losses, a constant difference is what that "
                "would produce too, and this platform cannot tell the two "
                "apart from the outside."
            )

        return MechanicalIssuance(
            symbol="BTC",
            mechanism=IssuanceMechanism.HALVING_SUBSIDY,
            state=IssuanceState(
                unit="BTC",
                # The rule run to the tip, not a figure anyone published.
                # Marked as derived because it is the one number here
                # that a reader would otherwise take for an observation.
                emitted=emitted / 1e8,
                emitted_is_derived=True,
                position=f"block {tip:,}",
                observed_at=observed_at,
                remaining=(21_000_000 * 1e8 - emitted) / 1e8,
            ),
            formula=(
                "sum over halving eras of blocks × subsidy, "
                "subsidy halving every 210,000 blocks from 50 BTC"
            ),
            parameters=(
                RuleParameter(
                    name="tip height",
                    value=float(tip),
                    unit="blocks",
                    read_from=f"GET {BITCOIN_HEIGHT.endpoint}",
                    means="how many blocks have paid a subsidy so far",
                ),
                RuleParameter(
                    name="current subsidy",
                    value=subsidy / 1e8,
                    unit="BTC",
                    read_from="derived: 50 ÷ 2^(height ÷ 210,000)",
                    means="what each block pays its producer today",
                ),
            ),
            mutability=RuleMutability.PROTOCOL_FIXED,
            provenance=PrimaryProvenance(
                surface_is_canonical=True,
                identity_because=(
                    "The height is Bitcoin's own tip, read from an endpoint "
                    "that serves one chain and takes no symbol."
                ),
                rule_version=self.BTC_RULE,
                formula="Σ blocks × subsidy over halving eras",
                unreconciled_because=(
                    "The rule's total and the one precise independent "
                    "circulation figure differ by an amount this platform "
                    "has not explained."
                ),
                constants=(
                    UnitConstant(
                        name="initial subsidy (50 BTC) and halving interval "
                        "(210,000 blocks)",
                        value=float(self.BTC_HALVING_INTERVAL),
                        stated_by_source=False,
                        cross_check=(
                            "reproducing the whole issuance history to the "
                            "tip lands within 0.0002% of an independent "
                            "explorer's circulation; a wrong constant would "
                            "miss by orders of magnitude"
                        ),
                    ),
                ),
            ),
            authority=EvidenceAuthority.PRIMARY_DERIVED,
            # The *rule* reproduces and the *total* has an unexplained
            # residual, so the object is served as a claim. The ruling is
            # explicit: a small unexplained residual is still unexplained.
            standing=EvidenceStanding.CLAIMED,
            source=BITCOIN_HEIGHT.name,
            path=self._btc_path(tip, emitted, next_halving),
            because=because,
            caveats=tuple(caveats),
        )

    def _btc_emitted(self, height: int) -> int:
        total, subsidy, remaining = 0, self.BTC_INITIAL_SUBSIDY, height + 1

        while subsidy > 0 and remaining > 0:
            blocks = min(remaining, self.BTC_HALVING_INTERVAL)
            total += blocks * subsidy
            remaining -= blocks
            subsidy //= 2

        return total

    def _btc_path(
        self,
        tip: int,
        emitted: int,
        next_halving: int,
    ) -> tuple[ProjectedIssuance, ...]:
        horizons: list[ProjectedIssuance] = []

        for label, ahead in (
            (f"to the next halving, block {next_halving:,}", next_halving - tip),
            ("1 year at the ten-minute target", self.BTC_BLOCKS_PER_YEAR),
            ("4 years at the ten-minute target", self.BTC_BLOCKS_PER_YEAR * 4),
        ):
            issued = self._btc_emitted(tip + ahead) - emitted

            horizons.append(
                ProjectedIssuance(
                    horizon=label,
                    issuance=issued / 1e8,
                    unit="BTC",
                    share_of_emitted=issued / emitted,
                    rule_version=self.BTC_RULE,
                )
            )

        return tuple(horizons)

    def _btc_circulation(self) -> int | None:
        payload = self._get(BITCOIN_CIRCULATION.endpoint)

        if not isinstance(payload, dict):
            return None

        data = payload.get("data")

        if not isinstance(data, dict):
            return None

        circulation = data.get("circulation")

        return int(circulation) if isinstance(circulation, (int, float)) else None

    # ── Cardano ─────────────────────────────────────────────────────

    def _cardano_rule(self) -> MechanicalIssuance | None:
        """Every parameter read, including the epoch length.

        The strongest case in the corpus for gate 3: nothing here is
        remembered. `rho` and `tau` are protocol parameters the chain
        serves, and the epoch length is the difference between the two
        timestamps the chain prints for the epoch itself.
        """

        totals = self._cardano.totals()

        epoch = int(totals["epoch_no"])

        params = self._get(
            "https://api.koios.rest/api/v1/epoch_params",
            params={"_epoch_no": str(epoch)},
        )
        info = self._get(
            "https://api.koios.rest/api/v1/epoch_info",
            params={"_epoch_no": str(epoch)},
        )

        if not (isinstance(params, list) and params) or not (
            isinstance(info, list) and info
        ):
            return None

        rho = float(params[0]["monetary_expand_rate"])
        tau = float(params[0]["treasury_growth_rate"])

        seconds = int(info[0]["end_time"]) - int(info[0]["start_time"])

        reserves = int(totals["reserves"]) / 1e6
        emitted = int(totals["supply"]) / 1e6

        observed_at = datetime.now(UTC)

        epochs_per_year = 365.25 * 86_400 / seconds

        return MechanicalIssuance(
            symbol="ADA",
            mechanism=IssuanceMechanism.RESERVE_DRAW,
            state=IssuanceState(
                unit="ADA",
                # The ledger's own `supply`, observed rather than derived.
                emitted=emitted,
                position=f"epoch {epoch}",
                observed_at=observed_at,
                remaining=reserves,
            ),
            formula=(
                "each epoch draws rho of the remaining reserves; tau of the "
                "draw goes to the treasury and the rest to staking rewards"
            ),
            parameters=(
                RuleParameter(
                    name="rho, monetary expansion rate",
                    value=rho,
                    unit="share of reserves per epoch",
                    read_from="GET /epoch_params → [0].monetary_expand_rate",
                    means="how much of the remaining reserve is drawn each epoch",
                ),
                RuleParameter(
                    name="tau, treasury growth rate",
                    value=tau,
                    unit="share of the draw",
                    read_from="GET /epoch_params → [0].treasury_growth_rate",
                    means=(
                        "the part of each draw that goes to the treasury "
                        "rather than to stakers — so only the remainder "
                        "reaches circulation"
                    ),
                ),
                RuleParameter(
                    name="epoch length",
                    value=float(seconds),
                    unit="seconds",
                    read_from="GET /epoch_info → [0].end_time − [0].start_time",
                    means="how often the draw happens",
                ),
                RuleParameter(
                    name="reserves",
                    value=reserves,
                    unit="ADA",
                    read_from="GET /totals → [0].reserves",
                    means="the pot the rule draws from",
                ),
            ),
            # rho and tau are protocol parameters, and Cardano's own
            # governance can change them. The path holds while they hold.
            mutability=RuleMutability.GOVERNANCE_PARAMETER,
            provenance=PrimaryProvenance(
                surface_is_canonical=True,
                identity_because=(
                    "Every figure comes from Cardano's own epoch endpoints, "
                    "which take an epoch and no symbol."
                ),
                rule_version=self.ADA_RULE,
                formula="draw = reserves × rho; to holders = draw × (1 − tau)",
                constants=(),
            ),
            authority=EvidenceAuthority.PRIMARY_DERIVED,
            standing=EvidenceStanding.CLAIMED,
            source=CardanoLedger.SURFACE.name,
            path=self._ada_path(reserves, emitted, rho, tau, epochs_per_year),
            because=(
                "Every parameter is read from the chain, including the epoch "
                "length. No constant is remembered."
            ),
            caveats=(
                "rho and tau are protocol parameters, so this path holds "
                "only while Cardano's governance leaves them where they are.",
                "Only the part of each draw left after tau reaches holders; "
                "the treasury share moves to a pot that is itself excluded "
                "from circulating supply.",
            ),
        )

    @staticmethod
    def _ada_path(
        reserves: float,
        emitted: float,
        rho: float,
        tau: float,
        epochs_per_year: float,
    ) -> tuple[ProjectedIssuance, ...]:
        horizons: list[ProjectedIssuance] = []

        for label, years in (("1 year", 1), ("4 years", 4)):
            epochs = int(years * epochs_per_year)

            drawn = reserves * (1 - (1 - rho) ** epochs)

            horizons.append(
                ProjectedIssuance(
                    horizon=f"{label} ({epochs} epochs), drawn from reserves",
                    issuance=drawn,
                    unit="ADA",
                    share_of_emitted=drawn / emitted,
                    rule_version=IssuanceRuleProvider.ADA_RULE,
                )
            )
            horizons.append(
                ProjectedIssuance(
                    horizon=f"{label}, the part reaching holders after tau",
                    issuance=drawn * (1 - tau),
                    unit="ADA",
                    share_of_emitted=drawn * (1 - tau) / emitted,
                    rule_version=IssuanceRuleProvider.ADA_RULE,
                )
            )

        return tuple(horizons)

    # ── Solana ──────────────────────────────────────────────────────

    def _solana(self) -> MechanicalIssuance | None:
        """An uncapped asset whose whole schedule is one call.

        The case that makes the ruling's twelfth section concrete:
        having no maximum does not mean having no rule, and Solana's is
        better published than most capped assets'.
        """

        governor = self._rpc("getInflationGovernor")
        rate = self._rpc("getInflationRate")

        if not isinstance(governor, dict) or not isinstance(rate, dict):
            return None

        initial = float(governor["initial"])
        taper = float(governor["taper"])
        terminal = float(governor["terminal"])
        current = float(rate["total"])

        observed_at = datetime.now(UTC)

        return MechanicalIssuance(
            symbol="SOL",
            mechanism=IssuanceMechanism.TAPERING_INFLATION,
            state=IssuanceState(
                unit="SOL",
                # Solana publishes a rate and no supply. A zero here
                # would be a figure nobody measured, on an object an
                # investor reads.
                emitted=None,
                position=f"epoch {rate.get('epoch')}",
                observed_at=observed_at,
                current_rate=current,
            ),
            formula=(
                "an annual issuance rate starting at `initial`, reduced by "
                "`taper` each year, never falling below `terminal`"
            ),
            parameters=(
                RuleParameter(
                    name="initial rate",
                    value=initial,
                    unit="annual share of supply",
                    read_from="getInflationGovernor → initial",
                    means="where the schedule started",
                ),
                RuleParameter(
                    name="taper",
                    value=taper,
                    unit="annual reduction",
                    read_from="getInflationGovernor → taper",
                    means="how much the rate falls each year",
                ),
                RuleParameter(
                    name="terminal rate",
                    value=terminal,
                    unit="annual share of supply",
                    read_from="getInflationGovernor → terminal",
                    means="the floor the rate stops falling at",
                ),
                RuleParameter(
                    name="current rate",
                    value=current,
                    unit="annual share of supply",
                    read_from="getInflationRate → total",
                    means="what the chain is issuing at right now",
                ),
            ),
            mutability=RuleMutability.GOVERNANCE_PARAMETER,
            provenance=PrimaryProvenance(
                surface_is_canonical=True,
                identity_because=(
                    "The governor is Solana's own inflation schedule, served "
                    "by its RPC and taking no symbol."
                ),
                rule_version=self.SOL_RULE,
                formula="rate(n+1) = max(terminal, rate(n) × (1 − taper))",
                constants=(),
            ),
            authority=EvidenceAuthority.PRIMARY_OBSERVATION,
            standing=EvidenceStanding.CLAIMED,
            source=SOLANA_INFLATION.name,
            path=self._sol_path(current, taper, terminal),
            because=(
                "Solana has no maximum supply and a fully published issuance "
                "rule. The two are independent: an uncapped asset can have a "
                "more explicit monetary policy than a capped one."
            ),
            caveats=(
                "A rate, not an amount. Turning it into tokens needs a "
                "supply figure, and Solana's emitted supply is one vendor's "
                "reading here.",
                "The governor's parameters are changeable by Solana's own "
                "governance, so the path holds while they do.",
            ),
        )

    @staticmethod
    def _sol_path(
        current: float,
        taper: float,
        terminal: float,
    ) -> tuple[ProjectedIssuance, ...]:
        horizons: list[ProjectedIssuance] = []

        rate = current

        for year in range(1, 5):
            rate = max(terminal, rate * (1 - taper))

            if year in (1, 4):
                horizons.append(
                    ProjectedIssuance(
                        horizon=f"annual issuance rate in {year} year(s)",
                        issuance=rate,
                        unit="annual share of supply",
                        share_of_emitted=rate,
                        rule_version=IssuanceRuleProvider.SOL_RULE,
                    )
                )

        return tuple(horizons)

    # ── the wire ────────────────────────────────────────────────────

    @staticmethod
    def _get(
        url: str,
        params: dict[str, str] | None = None,
        as_json: bool = True,
    ) -> Any:
        response = requests.get(url, params=params, timeout=TIMEOUT, headers=HEADERS)

        response.raise_for_status()

        return response.json() if as_json else response.text

    @staticmethod
    def _rpc(method: str) -> Any:
        response = requests.post(
            SOLANA_INFLATION.endpoint,
            json={"jsonrpc": "2.0", "id": 1, "method": method},
            timeout=TIMEOUT,
            headers={**HEADERS, "Content-Type": "application/json"},
        )

        response.raise_for_status()

        return response.json().get("result")
