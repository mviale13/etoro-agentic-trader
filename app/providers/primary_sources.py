"""Canonical state, read directly — the S4.5 authority experiment.

Four surfaces, one instrument. They are grouped because they exist to
answer a single question — *what can a crypto fact be, when it is
computed from primary state rather than reported by an aggregator?* — and
because none of them is in production: nothing caches them, no surface
serves them, and no score can see them. A source that later earns
production use moves out of this module into one of its own.

```text
Ethereum   execution RPC        canonical      base-fee burn, computable here
Hyperliquid  protocol API       canonical      supply accounting, fund balance
Cardano    ledger totals        canonical      the ledger's own supply concepts
Bitcoin    explorer API         NOT canonical  fee totals only a node can derive
```

**The Bitcoin row is the finding, not a gap.** A Bitcoin block carries no
fee figure. Recovering one requires the value of every transaction input,
which requires an indexed node this platform does not run — so the fee
total is somebody else's arithmetic over canonical state, and it is
labelled as that rather than as an on-chain reading. The contrast with
Ethereum, where the block itself publishes both terms of the burn, is
the whole point of the experiment.

Nothing here is cached, stored, scored or decided. Each read is an
explicit spend taken by `movrvest primary`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.primary_computation import (
    MechanismEvidence,
    ObservationWindow,
    PrimaryComputation,
    SourceSurface,
)

TIMEOUT = 45

#: One reading with no corroboration is a claim, whatever it was read
#: from. The authority axis records *what kind* of thing it is; this
#: slice changes no standing rule, so every figure below is CLAIMED.
_UNRULED = (
    "Read from canonical state and reproducible from the rule and inputs "
    "recorded beside it. It is a claim rather than established because "
    "this platform has one access path and no ruling yet on whether a "
    "reproducible primary computation may establish without a second "
    "source."
)


# ── Ethereum: the execution layer's own burn ────────────────────────


class EthereumRpc:
    """Ethereum mainnet state over a public JSON-RPC endpoint.

    The endpoint is a stranger's machine, and what it serves is a ledger
    anyone can verify — which is the distinction the authority axis is
    built on. A wrong answer here would be a wrong answer about a public
    object, checkable against any other node; a wrong answer from an
    aggregator is checkable against nothing.
    """

    SURFACE = SourceSurface(
        key="ethereum-execution-rpc",
        name="Ethereum execution JSON-RPC",
        network="ethereum-mainnet",
        endpoint="https://ethereum-rpc.publicnode.com",
        canonical=True,
        because=(
            "the endpoint serves Ethereum's own execution state; every "
            "field read below is part of a block header that any node "
            "reproduces independently."
        ),
    )

    #: The rule that produced the figure. A later rule recomputes the
    #: same window rather than overwriting what this one said.
    RULE = "eth-base-fee-burn/1"

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or self.SURFACE.endpoint

    def _post(self, payload: Any) -> Any:
        response = requests.post(
            self._endpoint,
            headers={
                "content-type": "application/json",
                "user-agent": "movrvest/1.0",
            },
            json=payload,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    def tip(self) -> int:
        answer = self._post(
            {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
        )

        return int(answer["result"], 16)

    def blocks(self, first: int, last: int) -> dict[int, dict[str, Any]]:
        """Every header in a range, batched.

        Batched because the alternative is one round trip per block and
        a 300-block window would then be a rate-limit problem rather
        than a measurement. Seven requests read an hour of Ethereum.
        """

        found: dict[int, dict[str, Any]] = {}

        for start in range(first, last + 1, 50):
            end = min(start + 49, last)

            answers = self._post(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": number,
                        "method": "eth_getBlockByNumber",
                        "params": [hex(number), False],
                    }
                    for number in range(start, end + 1)
                ]
            )

            for answer in answers:
                result = answer.get("result")

                if isinstance(result, dict):
                    found[int(answer["id"])] = result

        return found

    def base_fee_burn(
        self,
        blocks: int = 300,
        behind_tip: int = 10,
    ) -> PrimaryComputation:
        """Ether destroyed by the base fee over a stated window of blocks.

        The computation needs **no protocol constant**: every block
        publishes both terms, and their product is the ether the
        protocol removed from supply. That is exactly why it is the
        component this platform computes — see the caveat, which is the
        measurement that decided it.
        """

        last = self.tip() - behind_tip
        first = last - blocks + 1

        headers = self.blocks(first, last)

        if len(headers) < blocks:
            raise LookupError(
                f"Only {len(headers)} of {blocks} block headers were read, "
                "so no window was measured."
            )

        burn_wei = sum(
            int(headers[number]["baseFeePerGas"], 16)
            * int(headers[number]["gasUsed"], 16)
            for number in range(first, last + 1)
        )

        return PrimaryComputation(
            key="eth-base-fee-burn",
            label="Ether burned by the base fee",
            surface=self.SURFACE,
            entity="Ethereum mainnet, execution layer",
            window=ObservationWindow(
                kind="blocks",
                observed_at=datetime.now(UTC),
                first_block=first,
                last_block=last,
                first_timestamp=int(headers[first]["timestamp"], 16),
                last_timestamp=int(headers[last]["timestamp"], 16),
            ),
            value=burn_wei / 1e18,
            unit="ETH",
            formula=(
                "sum over the window of baseFeePerGas × gasUsed, in wei, "
                "divided by 1e18"
            ),
            rule_version=self.RULE,
            authority=EvidenceAuthority.PRIMARY_DERIVED,
            standing=EvidenceStanding.CLAIMED,
            inputs=(
                "eth_getBlockByNumber(number, false).baseFeePerGas",
                "eth_getBlockByNumber(number, false).gasUsed",
                "eth_getBlockByNumber(number, false).timestamp",
            ),
            because=_UNRULED,
            caveats=(
                "The base fee is one of two burned components. The other "
                "— blob fees — needs a blob base fee derived from "
                "excessBlobGas and a protocol constant that changes at "
                "forks, and this platform does not track that constant. "
                "Computed with the constant it knew, the blob base fee "
                "came out 4.2e15 wei against the node's own 4.97e6: "
                "wrong by a factor of 850 million, from canonical "
                "inputs, by a computation that looked deterministic. So "
                "this figure is the base-fee component only, and is a "
                "floor on the burn rather than the whole of it.",
                "A window of blocks is not a day. Scaling it to a daily "
                "rate is arithmetic over one observation, and one hour "
                "of Ethereum is not a trend.",
            ),
        )


# ── Hyperliquid: the protocol's own API ─────────────────────────────


class HyperliquidInfo:
    """Hyperliquid's own `info` API — the protocol describing itself.

    Canonical in the sense that matters: the operator of the endpoint is
    the protocol, and the accounting it publishes is the accounting the
    protocol applies. That does not make it self-explanatory, which the
    supply reconciliation below demonstrates.
    """

    SURFACE = SourceSurface(
        key="hyperliquid-info-api",
        name="Hyperliquid info API",
        network="hyperliquid-l1",
        endpoint="https://api.hyperliquid.xyz/info",
        canonical=True,
        because=(
            "the protocol operates this endpoint and it publishes the "
            "protocol's own state — token accounting and account "
            "balances — rather than a third party's view of it."
        ),
    )

    RULE = "hype-supply-reconciliation/1"

    #: The token identifier the protocol itself returns for HYPE, read
    #: from `spotMeta` and confirmed by name on every use. A hard-coded
    #: identifier nobody re-checks is how a reading ends up describing
    #: another asset.
    HYPE_NAME = "HYPE"

    #: Hyperliquid's Assistance Fund address, by the protocol's own
    #: convention. Confirmed below against the token's own
    #: non-circulating list rather than trusted from documentation.
    ASSISTANCE_FUND = "0xfefefefefefefefefefefefefefefefefefefefe"

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or self.SURFACE.endpoint

    def _post(self, body: dict[str, Any]) -> Any:
        response = requests.post(
            self._endpoint,
            headers={
                "content-type": "application/json",
                "user-agent": "movrvest/1.0",
            },
            json=body,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    def token(self) -> dict[str, Any]:
        """HYPE's own record, found by name rather than by a stored id."""

        meta = self._post({"type": "spotMeta"})

        for token in meta.get("tokens", []):
            if token.get("name") == self.HYPE_NAME:
                details = self._post(
                    {"type": "tokenDetails", "tokenId": token["tokenId"]}
                )

                if not isinstance(details, dict):
                    raise LookupError(
                        "The protocol returned no token details for HYPE."
                    )

                details["tokenId"] = token["tokenId"]

                return dict(details)

        raise LookupError(
            "The protocol's own spot metadata lists no token named "
            f"{self.HYPE_NAME}, so nothing was read."
        )

    def circulating_supply(self) -> PrimaryComputation:
        """The protocol's own circulating supply, and the rule behind it.

        Reconciled rather than copied. The protocol publishes a
        `circulatingSupply` field and also the three quantities it is
        made of, and checking that they agree is what turns a read field
        into an understood one — which is how the surprise below was
        found.
        """

        details = self.token()

        total = float(details["totalSupply"])
        circulating = float(details["circulatingSupply"])
        future = float(details["futureEmissions"])

        excluded = details.get("nonCirculatingUserBalances") or []

        non_circulating = sum(float(row[1]) for row in excluded)

        residual = total - non_circulating - future

        return PrimaryComputation(
            key="hype-circulating-supply",
            label="HYPE circulating supply, as the protocol defines it",
            surface=self.SURFACE,
            entity=f"HYPE token {details['tokenId']}",
            window=ObservationWindow(kind="instant", observed_at=datetime.now(UTC)),
            value=circulating,
            unit="HYPE",
            formula=(
                "totalSupply − sum(nonCirculatingUserBalances) − "
                f"futureEmissions, checked against the protocol's own "
                f"circulatingSupply field (residual {residual:,.4f} vs "
                f"reported {circulating:,.4f})"
            ),
            rule_version=self.RULE,
            authority=EvidenceAuthority.PRIMARY_OBSERVATION,
            standing=EvidenceStanding.CLAIMED,
            inputs=(
                "info(spotMeta).tokens[name=HYPE].tokenId",
                "info(tokenDetails).totalSupply",
                "info(tokenDetails).circulatingSupply",
                "info(tokenDetails).futureEmissions",
                "info(tokenDetails).nonCirculatingUserBalances",
            ),
            because=_UNRULED,
            caveats=(
                f"`totalSupply` includes {future:,.0f} tokens that do not "
                "exist yet: the protocol's own figure only reconciles "
                "once future emissions are subtracted. Reading it as "
                "*tokens in existence* is wrong by that amount, and "
                "nothing in the field name says so.",
                f"Which accounts are non-circulating is a policy, not a "
                f"chain fact: {len(excluded)} addresses are excluded by "
                "the protocol's own choice. Another party applying a "
                "different list gets a different, equally defensible "
                "number.",
            ),
        )

    def assistance_fund(self) -> MechanismEvidence:
        """That the Assistance Fund exists and holds HYPE, from the protocol.

        Evidence about a mechanism, and deliberately not about its size:
        one reading of a balance cannot say what flowed in over a day.
        Establishing that the fund exists, is named by the protocol's own
        non-circulating accounting, and holds the token is a different
        and answerable question.
        """

        details = self.token()

        excluded = {
            str(row[0]).lower(): float(row[1])
            for row in (details.get("nonCirculatingUserBalances") or [])
        }

        state = self._post(
            {"type": "spotClearinghouseState", "user": self.ASSISTANCE_FUND}
        )

        balances = {
            item["coin"]: float(item["total"]) for item in state.get("balances", [])
        }

        held = balances.get(self.HYPE_NAME)

        listed = excluded.get(self.ASSISTANCE_FUND.lower())

        evidence = [
            f"address {self.ASSISTANCE_FUND}",
            (
                f"holds {held:,.4f} HYPE by the protocol's own spotClearinghouseState"
                if held is not None
                else "holds no HYPE by the protocol's own state"
            ),
        ]

        if listed is not None:
            evidence.append(
                f"listed among the token's nonCirculatingUserBalances at "
                f"{listed:,.4f} HYPE"
            )

        return MechanismEvidence(
            key="hype-assistance-fund",
            label="The Assistance Fund exists and holds HYPE",
            surface=self.SURFACE,
            observed=(
                "The protocol's own API returns a balance for the "
                "Assistance Fund address and excludes that address from "
                "circulating supply by name."
            ),
            evidence=tuple(evidence),
            authority=EvidenceAuthority.PRIMARY_OBSERVATION,
            standing=EvidenceStanding.CLAIMED,
            observed_at=datetime.now(UTC),
            because=(
                "Two independent readings from the protocol's own state "
                "agree: the fund's balance, and its appearance in the "
                "token's non-circulating list. Neither is a third "
                "party's description of the mechanism."
            ),
            does_not_establish=(
                "how much reached the fund over any interval — a balance "
                "at a moment conflates what arrived, what was spent and "
                "what the price did",
                "that 99% of fees go to it, which remains DefiLlama's "
                "sentence and not the protocol's",
                "that the accumulation is worth anything to a holder",
            ),
        )


# ── Cardano: the ledger's own supply concepts ───────────────────────


class CardanoLedger:
    """Cardano's ledger accounting, as the chain itself computes it.

    The surface that made the supply question answerable: Cardano's
    ledger publishes *several* supply quantities, each with a defined
    meaning, and the vendors that appeared to disagree turn out to be
    reporting different ones.
    """

    SURFACE = SourceSurface(
        key="cardano-ledger-totals",
        name="Cardano ledger totals",
        network="cardano-mainnet",
        endpoint="https://api.koios.rest/api/v1/totals",
        canonical=True,
        because=(
            "the figures are the ledger's own epoch accounting — "
            "circulation, treasury, reserves and rewards are quantities "
            "the protocol itself maintains, not a vendor's estimate of "
            "them."
        ),
    )

    RULE = "ada-ledger-supply/1"

    #: Lovelace per ADA.
    UNIT = 1_000_000

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or self.SURFACE.endpoint

    def _get(self, path: str = "") -> Any:
        """The one place this adapter touches the network."""

        response = requests.get(
            f"{self._endpoint}{path}",
            headers={"accept": "application/json", "user-agent": "movrvest/1.0"},
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    def totals(self) -> dict[str, Any]:
        rows = self._get()

        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise LookupError("The ledger endpoint returned no epoch totals.")

        return dict(rows[0])

    def supply_concepts(self) -> tuple[PrimaryComputation, ...]:
        """Every supply quantity the ledger itself defines.

        Returned as several facts rather than one, because that is what
        the ledger publishes. Collapsing them into a single "supply"
        would recreate exactly the ambiguity that made three vendors
        look like they disagreed.
        """

        totals = self.totals()

        observed_at = datetime.now(UTC)

        window = ObservationWindow(kind="epoch", observed_at=observed_at)

        epoch = totals.get("epoch_no")

        def _computation(
            key: str,
            label: str,
            field: str,
            means: str,
        ) -> PrimaryComputation:
            return PrimaryComputation(
                key=key,
                label=label,
                surface=self.SURFACE,
                entity=f"Cardano mainnet, epoch {epoch}",
                window=window,
                value=int(totals[field]) / self.UNIT,
                unit="ADA",
                formula=f"totals.{field} lovelace ÷ 1,000,000",
                rule_version=self.RULE,
                authority=EvidenceAuthority.PRIMARY_OBSERVATION,
                standing=EvidenceStanding.CLAIMED,
                inputs=(f"GET /totals → [0].{field}", "GET /totals → [0].epoch_no"),
                because=_UNRULED,
                caveats=(means,),
            )

        return (
            _computation(
                "ada-circulation",
                "ADA in circulation",
                "circulation",
                "What the ledger counts as circulating: issued, and not "
                "in the treasury, the reserves or the reward pot.",
            ),
            _computation(
                "ada-supply",
                "ADA supply",
                "supply",
                "Everything issued out of reserves — circulation plus "
                "the treasury plus undistributed rewards. Larger than "
                "circulation by construction.",
            ),
            _computation(
                "ada-treasury",
                "ADA in the treasury",
                "treasury",
                "Held by the protocol's own treasury. Whether it counts "
                "as circulating is a policy question, and different "
                "vendors answer it differently.",
            ),
            _computation(
                "ada-reward",
                "ADA in the reward pot",
                "reward",
                "Earned and not yet withdrawn. Counted by some vendors "
                "and not others, which is most of the gap between them.",
            ),
        )


# ── Bitcoin: the contrast case ──────────────────────────────────────


class BitcoinExplorer:
    """Bitcoin fee totals — a third party's arithmetic over canonical state.

    Deliberately not labelled primary. A Bitcoin block publishes no fee
    total; recovering one requires the value of every transaction input,
    which requires an indexed node. What this reads is a competent
    explorer's computation, and this platform cannot reproduce it.

    The contrast with Ethereum is the point of including it: the same
    economic question — what did users pay to use the network — is
    primary-computable on one chain and not on the other, and the
    difference is a property of the ledgers rather than of the effort
    spent.
    """

    SURFACE = SourceSurface(
        key="mempool-space",
        name="mempool.space",
        network="bitcoin-mainnet",
        endpoint="https://mempool.space/api",
        canonical=False,
        because=(
            "a Bitcoin block carries no fee figure, so this endpoint "
            "serves the operator's own computation over the ledger "
            "rather than a field the ledger publishes. It is somebody "
            "else's arithmetic, and this platform cannot re-run it "
            "without an indexed node."
        ),
    )

    RULE = "btc-fee-observation/1"

    #: Satoshi per bitcoin.
    UNIT = 100_000_000

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or self.SURFACE.endpoint

    def _get(self, path: str, as_text: bool = False) -> Any:
        """The one place this adapter touches the network."""

        response = requests.get(
            f"{self._endpoint}{path}",
            headers={"user-agent": "movrvest/1.0"},
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.text if as_text else response.json()

    def block_fees(self) -> PrimaryComputation:
        """Fees paid in the most recent block, as the explorer computed them."""

        height = int(str(self._get("/blocks/tip/height", as_text=True)).strip())

        blocks = self._get(f"/v1/blocks/{height}")

        if not isinstance(blocks, list) or not blocks:
            raise LookupError("The explorer returned no blocks.")

        block = blocks[0]

        extras = block.get("extras") or {}

        fees = extras.get("totalFees")

        if fees is None:
            raise LookupError(
                "The explorer returned a block with no fee total, so "
                "nothing was measured."
            )

        return PrimaryComputation(
            key="btc-block-fees",
            label="Fees paid in one Bitcoin block",
            surface=self.SURFACE,
            entity=f"Bitcoin mainnet, block {block['height']:,}",
            window=ObservationWindow(
                kind="blocks",
                observed_at=datetime.now(UTC),
                first_block=int(block["height"]),
                last_block=int(block["height"]),
                first_timestamp=int(block["timestamp"]),
                last_timestamp=int(block["timestamp"]),
            ),
            value=float(fees) / self.UNIT,
            unit="BTC",
            formula=(
                "the explorer's own totalFees for the block, in satoshi, "
                "divided by 100,000,000 — this platform performed no "
                "arithmetic over ledger state"
            ),
            rule_version=self.RULE,
            authority=EvidenceAuthority.SECONDARY_COMPUTATION,
            standing=EvidenceStanding.CLAIMED,
            inputs=(f"GET /v1/blocks/{height} → [0].extras.totalFees",),
            because=(
                "Read from a third party's computation over canonical "
                "state. This platform cannot reproduce it: the fee total "
                "is the sum of inputs minus outputs across every "
                "transaction, and the block alone does not carry input "
                "values."
            ),
            caveats=(
                "One block is roughly ten minutes of Bitcoin and its fee "
                "total varies widely between blocks. It is an "
                "observation, not a rate.",
                "A second explorer is not corroboration of the ledger — "
                "it is a second party running the same arithmetic. "
                "blockchain.info's published total_fees_btc was "
                "**negative** when this was measured, which is what an "
                "unreproducible figure failing silently looks like.",
            ),
        )
