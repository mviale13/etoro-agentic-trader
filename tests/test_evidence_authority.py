"""S4.5: what a crypto fact can be when it is computed from primary state.

One test per acceptance criterion, plus the guards. The two that matter
most cannot be read off the code: that authority never becomes a
standing, and that a computation nobody could re-run reports itself as
irreproducible rather than as a number.

**Nothing here touches the network.** Every case runs on payloads
recorded during the S4.5 measurement on 2026-08-10 — including the ones
that produced the findings — pushed through the real adapters. The
hermetic guard in `conftest` blocks the wire on all four surfaces, so a
test that tried would go red rather than spend.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime

import pytest

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.primary_computation import (
    ObservationWindow,
    PrimaryComputation,
    SourceSurface,
)
from app.providers.primary_sources import (
    BitcoinExplorer,
    CardanoLedger,
    EthereumRpc,
    HyperliquidInfo,
)

READ = datetime(2026, 8, 10, 11, 0, tzinfo=UTC)


def _code(module: str) -> str:
    """A module's identifiers and literal values, without its prose."""

    root = pathlib.Path(__file__).resolve().parent.parent

    tree = ast.parse((root / module).read_text(encoding="utf-8"))

    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
    }

    words: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            words.append(node.id)
        elif isinstance(node, ast.Attribute):
            words.append(node.attr)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            words.append(node.name)
        elif isinstance(node, ast.alias):
            words.append(f"{node.name} {node.asname or ''}")
        elif isinstance(node, ast.ImportFrom):
            words.append(node.module or "")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                words.append(node.value)

    return "\n".join(words)


# ── acceptance 4: authority is not standing ─────────────────────────


def test_authority_and_standing_are_independent_vocabularies() -> None:
    """Acceptance 4.

    Overloading `standing` with provenance was the easy move. It would
    have made `ESTABLISHED` mean "came from a blockchain", which is
    exactly the substitution S1 exists to prevent.
    """

    standings = {member.value for member in EvidenceStanding}
    authorities = {member.value for member in EvidenceAuthority}

    assert standings & authorities == set()

    # Neither enum may name a member of the other.
    for authority in EvidenceAuthority:
        assert "established" not in authority.value
        assert "claimed" not in authority.value

    for standing in EvidenceStanding:
        assert "primary" not in standing.value
        assert "secondary" not in standing.value


def test_the_authority_axis_does_not_import_a_standing_rule() -> None:
    """The axis explains a standing; it never decides one."""

    code = _code("app/domain/evidence_authority.py")

    assert "EvidenceStanding" not in code
    assert "app.providers" not in code


def test_a_primary_reading_is_still_only_a_claim() -> None:
    """Acceptance 1 and 10: no standing rule moved in this slice.

    Every figure the experiment produces is CLAIMED. Being canonical
    earns a fact its authority label and nothing else — the ruling on
    whether reproducibility can establish is the owner's, and this slice
    exists to inform it rather than to take it.
    """

    surfaces = (
        EthereumRpc.SURFACE,
        HyperliquidInfo.SURFACE,
        CardanoLedger.SURFACE,
        BitcoinExplorer.SURFACE,
    )

    assert {surface.canonical for surface in surfaces} == {True, False}

    code = _code("app/providers/primary_sources.py")

    # The one standing any adapter may assign.
    assert "CLAIMED" in code
    assert "ESTABLISHED" not in code


# ── acceptance 2: primary is not automatically true ─────────────────


def test_the_blob_constant_finding_is_recorded_where_it_can_be_read() -> None:
    """Acceptance 2, from the measurement rather than from principle.

    Computed with the protocol constant this platform knew, Ethereum's
    blob base fee came out 4.2e15 wei against the node's own 4.97e6 —
    wrong by a factor of 850 million, from canonical inputs, by a
    computation that looked deterministic. The burn figure is therefore
    the base-fee component only, and says so.
    """

    burn = _eth_burn()

    assert burn.value > 0

    caveat = " ".join(burn.caveats)

    assert "blob" in caveat
    assert "constant" in caveat
    assert "floor" in caveat


def test_a_protocol_field_is_not_taken_at_its_name() -> None:
    """The second demonstration: Hyperliquid's own totalSupply.

    It includes 412 million tokens that do not exist yet. The
    reconciliation is what found that; copying the field would not have.
    """

    supply = _hype_supply()

    caveat = " ".join(supply.caveats)

    assert "do not exist yet" in caveat
    assert "policy" in caveat


# ── acceptance 3: reproducibility is mechanical, not claimed ────────


def test_every_computation_carries_what_a_stranger_would_need() -> None:
    """Acceptance 3.

    A surface, an entity, a window, the raw inputs, the formula and the
    rule version. A figure short of any of them is a number with a
    story, and the property says so rather than a reviewer noticing.
    """

    for computation in (_eth_burn(), _hype_supply(), _btc_fees(), *_ada_supply()):
        assert computation.is_repeatable, computation.key
        assert computation.inputs
        assert computation.formula
        assert computation.rule_version
        assert computation.surface.endpoint

    # Repeatable is not the same as checkable. Bitcoin's figure can be
    # fetched again from the same explorer and cannot be recovered from
    # the ledger here — repeating a source is not checking it.
    assert _eth_burn().is_independently_reproducible
    assert _hype_supply().is_independently_reproducible
    assert not _btc_fees().is_independently_reproducible


def test_a_computation_missing_its_rule_is_not_reproducible() -> None:
    """The property has to be able to say no, or it says nothing."""

    naked = PrimaryComputation(
        key="test",
        label="A number with a story",
        surface=SourceSurface(
            key="s",
            name="s",
            network="n",
            endpoint="",
            canonical=True,
            because="",
        ),
        entity="",
        window=ObservationWindow(kind="instant", observed_at=READ),
        value=1.0,
        unit="X",
        formula="",
        rule_version="",
        authority=EvidenceAuthority.PRIMARY_DERIVED,
        standing=EvidenceStanding.CLAIMED,
    )

    assert not naked.is_repeatable
    assert not naked.is_independently_reproducible


def test_the_burn_is_arithmetic_over_the_headers_and_nothing_else() -> None:
    """Determinism, checked by hand against the same inputs.

    Two blocks with known base fees and gas, and the answer is the sum
    of their products. If this needed anything the headers do not carry,
    it would not be reproducible by anyone else either.
    """

    burn = _eth_burn()

    expected = (90_125_203 * 59_924_449 + 90_000_000 * 60_000_000) / 1e18

    assert burn.value == pytest.approx(expected)
    assert burn.window.blocks == 2
    assert burn.window.seconds == 12


# ── acceptance 5 and 6: mechanism, amount, and three chains ─────────


def test_the_hype_mechanism_and_the_hype_amount_are_separate_findings() -> None:
    """Acceptance 5.

    That the Assistance Fund exists and holds HYPE is readable from the
    protocol's own state. What flowed into it over a day is not, from
    one reading — and the object says so in as many words rather than
    letting a balance stand in for a flow.
    """

    fund = _hype_fund()

    assert fund.authority is EvidenceAuthority.PRIMARY_OBSERVATION
    assert fund.standing is EvidenceStanding.CLAIMED

    # Two independent readings of the protocol's own state agree.
    assert any("0xfefe" in item for item in fund.evidence)
    assert any("46,311,782" in item for item in fund.evidence)
    assert any("nonCirculating" in item for item in fund.evidence)

    disclaimed = " ".join(fund.does_not_establish)

    assert "over any interval" in disclaimed
    assert "99%" in disclaimed
    assert "worth anything" in disclaimed


def test_three_chains_produce_three_different_authorities() -> None:
    """Acceptance 6.

    The same economic question — what did users pay, and where did it
    go — reaches a different kind of evidence on each chain, and the
    difference is a property of the ledgers rather than of the effort.
    """

    assert _eth_burn().authority is EvidenceAuthority.PRIMARY_DERIVED
    assert _hype_supply().authority is EvidenceAuthority.PRIMARY_OBSERVATION
    assert _btc_fees().authority is EvidenceAuthority.SECONDARY_COMPUTATION

    assert EthereumRpc.SURFACE.canonical
    assert HyperliquidInfo.SURFACE.canonical
    assert not BitcoinExplorer.SURFACE.canonical

    # And the Bitcoin reason is the ledger's shape, not a missing effort:
    # a block carries no fee figure, and recovering one needs the value of
    # every input, which needs an index only a node holds.
    assert "indexed node" in BitcoinExplorer.SURFACE.because

    because = _btc_fees().because or ""

    assert "input values" in because
    assert "cannot reproduce" in because


# ── acceptance 7: supply is not a chain primitive ───────────────────


def test_hype_circulating_supply_reconciles_only_through_a_policy() -> None:
    """Acceptance 7, on the protocol's own numbers.

    The protocol's `circulatingSupply` equals total, minus a **list of
    four excluded addresses**, minus tokens not yet emitted. Every term
    after the first is a choice, so the result is the protocol's policy
    rather than a fact the chain holds.
    """

    supply = _hype_supply()

    assert supply.value == pytest.approx(299_022_746.6799, abs=0.001)

    assert "nonCirculatingUserBalances" in supply.formula
    assert "futureEmissions" in supply.formula

    assert any("4 addresses" in caveat for caveat in supply.caveats)


def test_cardano_publishes_several_supply_quantities_not_one() -> None:
    """The finding that explains the vendor conflict structurally.

    Cardano's ledger defines circulation, supply, treasury and rewards
    separately. Three vendors reporting "circulating supply" were
    reporting three of them — so the S1 conflict was semantic, and the
    ledger settles it definitionally rather than by picking a winner.
    """

    concepts = {item.key: item.value for item in _ada_supply()}

    assert set(concepts) == {
        "ada-circulation",
        "ada-supply",
        "ada-treasury",
        "ada-reward",
    }

    circulation = concepts["ada-circulation"]
    supply = concepts["ada-supply"]
    treasury = concepts["ada-treasury"]
    reward = concepts["ada-reward"]

    assert circulation < supply
    assert circulation + reward + treasury == pytest.approx(supply, rel=0.001)

    # What each vendor was actually reporting, to the precision the
    # measurement found. TokenInsight matched the ledger's `supply` to
    # the unit; the reading S1 *rejected* matched `circulation`.
    assert supply == pytest.approx(38_803_572_882.17, abs=1.0)
    assert circulation == pytest.approx(36_550_320_207.15, abs=1.0)
    assert circulation + reward == pytest.approx(37_348_055_948.0, abs=1.0)


def test_no_provider_is_named_a_winner_for_supply() -> None:
    """The ruling's own instruction: measure, do not choose.

    Nothing in this slice prefers a vendor. The ledger's quantities are
    published as themselves, and which one deserves the name
    "circulating supply" is a decision nobody has taken.
    """

    code = _code("app/providers/primary_sources.py")

    for vendor in ("TokenInsight", "CoinGecko", "Yahoo"):
        assert vendor not in code


# ── acceptance 8: provider-scoped aggregates ────────────────────────


def test_a_provider_scoped_aggregate_can_never_be_corroborated() -> None:
    """Acceptance 8.

    A second vendor computing "the total crypto market cap" computes a
    different quantity over a different universe. Recording that as a
    permanent ceiling stops a future slice chasing a consensus that does
    not exist.
    """

    scoped = EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE

    assert not scoped.can_be_corroborated
    assert not EvidenceAuthority.ATTRIBUTED_OPINION.can_be_corroborated

    assert EvidenceAuthority.SECONDARY_AGGREGATE.can_be_corroborated
    assert EvidenceAuthority.PRIMARY_DERIVED.can_be_corroborated

    assert "no source-independent value" in scoped.corroboration


def test_every_authority_says_what_would_move_it() -> None:
    """An acquisition demand aimed at the wrong thing is wasted work."""

    for authority in EvidenceAuthority:
        assert len(authority.corroboration) > 40, authority
        assert len(authority.described) > 30, authority


# ── acceptance 9, 10, 11, 12: nothing moved ─────────────────────────


def test_no_score_or_decision_path_can_import_the_authority_experiment() -> None:
    """Acceptance 9 and 10, made structural."""

    root = pathlib.Path(__file__).resolve().parent.parent

    reasoning = (
        "app/analysts",
        "app/application/brain",
        "app/application/committees",
        "app/application/executive",
        "app/cio",
        "app/committee",
        "app/domain/business_quality.py",
        "app/domain/playbook.py",
        "app/domain/financial_question.py",
        "app/services/business_quality_service.py",
        "app/services/company_facts_service.py",
        "app/services/company_signal_service.py",
        "app/services/crypto_asset_quality_service.py",
        "app/services/playbook_selector.py",
        "app/services/quality_signal_service.py",
    )

    offenders: list[str] = []

    for target in reasoning:
        path = root / target

        files = (
            sorted(path.rglob("*.py"))
            if path.is_dir()
            else ([path] if path.exists() else [])
        )

        for source in files:
            text = source.read_text(encoding="utf-8")

            if any(
                name in text
                for name in (
                    "primary_sources",
                    "primary_computation",
                    "evidence_authority",
                )
            ):
                offenders.append(str(source.relative_to(root)))

    assert offenders == []


def test_no_quality_rule_reads_the_authority_axis() -> None:
    """Acceptance 10, restated for the model that replaced the factors.

    S4.5's guard was written when a factor table existed to be held
    still, and S5 replaced that table under an explicit ruling. What the
    guard was protecting survives and is stronger stated positively:
    **a rule gates on standing and never on authority.** Where a figure
    came from explains why a standing applies; it is not a second
    standing, and a primary reading is not thereby scorable.
    """

    from app.domain.crypto_quality import RULES

    # Every rule names the fact it reads, and no rule names a source,
    # a provider or an authority.
    for rule in RULES.values():
        stated = f"{rule.measures} {rule.answers}".casefold()

        for word in ("primary", "authority", "chain", "provider", "vendor"):
            assert word not in stated, (rule.name, word)

    # And the scoring gate is standing, at one place, by name.
    code = pathlib.Path("app/services/crypto_asset_quality_service.py").read_text(
        encoding="utf-8"
    )

    assert "EvidenceStanding.ESTABLISHED" in code
    assert "EvidenceAuthority" not in code


def test_the_experiment_stores_nothing() -> None:
    """Acceptance 11: no S1–S4 conflict was resolved by writing over it.

    The command is a measurement of this platform, in the family of
    `reader-stability` and `statement-shape`. It reaches no cache, so no
    stored standing can change because it ran.
    """

    for module in (
        "app/providers/primary_sources.py",
        "app/commands/primary.py",
    ):
        code = _code(module)

        assert "JsonCache" not in code
        assert "cache" not in code.casefold()


def test_equity_behaviour_is_unchanged() -> None:
    """Acceptance 12."""

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/financial_question.py",
        "app/domain/playbook.py",
        "app/services/playbook_selector.py",
    ):
        text = (root / module).read_text(encoding="utf-8").casefold()

        assert "authority" not in text, module
        assert "primary_computation" not in text, module


def test_no_model_is_asked_for_a_quantitative_primary_fact() -> None:
    """The ruling's seventh point, made structural.

    An LLM may later explain a mechanism. It may not produce a fee
    total, a supply or a burn — the trust chain for a quantitative
    primary fact stays machine-reproducible.
    """

    code = _code("app/providers/primary_sources.py")

    for name in ("openai", "anthropic", "completion", "prompt", "llm"):
        assert name not in code.casefold(), name


def test_a_security_with_no_verified_surface_is_not_read_by_resemblance() -> None:
    from app.commands.primary import SUBJECTS

    assert set(SUBJECTS) == {"BTC", "ETH", "ADA", "HYPE"}

    assert "SOL" not in SUBJECTS
    assert "ARB" not in SUBJECTS


# ── the recorded payloads ───────────────────────────────────────────


def _eth_burn() -> PrimaryComputation:
    """Two blocks, so the arithmetic can be checked by hand."""

    headers = {
        100: {
            "baseFeePerGas": hex(90_125_203),
            "gasUsed": hex(59_924_449),
            "timestamp": hex(1_786_358_987),
        },
        101: {
            "baseFeePerGas": hex(90_000_000),
            "gasUsed": hex(60_000_000),
            "timestamp": hex(1_786_358_999),
        },
    }

    provider = EthereumRpc()

    provider.tip = lambda: 111  # type: ignore[method-assign]
    provider.blocks = lambda first, last: headers  # type: ignore[method-assign]

    return provider.base_fee_burn(blocks=2, behind_tip=10)


#: Hyperliquid's own answer on 2026-08-10, verbatim. `totalSupply`
#: including unemitted tokens is not a transcription slip — it is the
#: finding.
_HYPE = {
    "name": "HYPE",
    "tokenId": "0x0d01dc56dcaaca66ad901c959b4011ec",
    "maxSupply": "1000000000.0",
    "totalSupply": "999044028.5858",
    "circulatingSupply": "299022746.6799",
    "futureEmissions": "412513564.9696",
    "nonCirculatingUserBalances": [
        ["0x43e9abea1910387c4292bca4b94de81462f8a251", "241194257.8480974734"],
        ["0xfefefefefefefefefefefefefefefefefefefefe", "46311782.5847392306"],
        ["0x0000000000000000000000000000000000000000", "1673.78676324"],
        ["0x000000000000000000000000000000000000dead", "2.71671343"],
    ],
}


def _hyperliquid() -> HyperliquidInfo:
    provider = HyperliquidInfo()

    provider.token = lambda: dict(_HYPE)  # type: ignore[method-assign]

    return provider


def _hype_supply() -> PrimaryComputation:
    return _hyperliquid().circulating_supply()


def _hype_fund():  # type: ignore[no-untyped-def]
    provider = _hyperliquid()

    provider._post = lambda body: {  # type: ignore[method-assign]
        "balances": [
            {"coin": "USDC", "total": "6105.00718469"},
            {"coin": "HYPE", "total": "46311782.5847392306"},
        ]
    }

    return provider.assistance_fund()


#: Cardano's ledger at epoch 648, in lovelace, as the chain published it.
_ADA = {
    "epoch_no": 648,
    "circulation": "36550320207145109",
    "treasury": "1450053248585177",
    "reward": "797735740883044",
    "supply": "38803572882173527",
    "reserves": "6196427117826473",
}


def _ada_supply() -> tuple[PrimaryComputation, ...]:
    provider = CardanoLedger()

    provider.totals = lambda: dict(_ADA)  # type: ignore[method-assign]

    return provider.supply_concepts()


def _btc_fees() -> PrimaryComputation:
    provider = BitcoinExplorer()

    def _get(path: str, as_text: bool = False):  # type: ignore[no-untyped-def]
        if as_text:
            return "961866"

        return [
            {
                "height": 961_866,
                "timestamp": 1_786_358_744,
                "extras": {"totalFees": 4_590_775, "reward": 317_090_775},
            }
        ]

    provider._get = _get  # type: ignore[method-assign]

    return provider.block_fees()
