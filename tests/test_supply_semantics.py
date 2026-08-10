"""S4.6: crypto supply is an accounting vocabulary, not one number.

One test per acceptance criterion. The one that matters most cannot be
read off the code: that two figures stop conflicting when the evidence
shows they count different things, and keep conflicting when it does
not.

**Nothing here touches the network or the store.** Every case runs on the
readings recorded during the S4.6 measurement on 2026-08-10 — the ledger
totals, the protocol's own accounting and each vendor's claim — pushed
through the real service.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.provenance import Provenance
from app.domain.supply_mappings import mappings_for
from app.domain.supply_semantics import (
    Comparison,
    SupplyConcept,
    SupplyFact,
    compare,
)
from app.domain.token_fact_validation import TokenClaimSet
from app.providers.primary_sources import _xxh64, storage_key
from app.providers.primary_supply_provider import PrimarySupplyProvider
from app.services.supply_semantics_service import SupplySemanticsService

READ = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


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


# ── the recorded readings ───────────────────────────────────────────

#: Cardano's ledger at epoch 648, in lovelace, as the chain published it.
_ADA_LEDGER = {
    "epoch_no": 648,
    "circulation": "36550320207145109",
    "treasury": "1450053248585177",
    "reward": "797735740883044",
    "supply": "38803572882173527",
    "reserves": "6196427117826473",
}

#: Hyperliquid's own answer. `totalSupply` counting unemitted tokens is
#: the finding, not a transcription slip.
_HYPE_TOKEN = {
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

#: Every vendor's supply claim on the same day, per security.
_CLAIMS: dict[str, dict[str, dict[str, float]]] = {
    "ADA": {
        "TokenInsight": {
            "circulating_supply": 38_803_572_882.0,
            "max_supply": 45_000_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 37_353_519_634.0,
            "total_supply": 45_000_000_000.0,
            "max_supply": 45_000_000_000.0,
        },
        "Yahoo Finance": {"circulating_supply": 36_550_320_128.0},
    },
    "HYPE": {
        "TokenInsight": {
            "circulating_supply": 336_685_219.0,
            "max_supply": 1_000_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 222_445_714.0,
            "max_supply": 1_000_000_000.0,
        },
    },
    "ARB": {
        "TokenInsight": {
            "circulating_supply": 1_275_000_000.0,
            "max_supply": 10_000_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 6_614_056_381.0,
            "total_supply": 10_000_000_000.0,
            "max_supply": 10_000_000_000.0,
        },
    },
    "TAO": {
        "TokenInsight": {"circulating_supply": 8_644_817.0, "max_supply": 21_000_000.0},
        "CoinGecko": {
            "circulating_supply": 9_597_491.0,
            "total_supply": 21_000_000.0,
            "max_supply": 21_000_000.0,
        },
    },
    "BTC": {
        "TokenInsight": {
            "circulating_supply": 20_068_225.0,
            "max_supply": 21_000_000.0,
        },
        "CoinGecko": {
            "circulating_supply": 20_068_243.0,
            "max_supply": 21_000_000.0,
        },
    },
}


class _Vendor:
    def __init__(self, name: str) -> None:
        self._name = name

    def claim_set(self, symbol: str) -> TokenClaimSet | None:
        values = _CLAIMS.get(symbol.upper(), {}).get(self._name)

        if values is None:
            return None

        return TokenClaimSet(
            source=self._name,
            read=Provenance(source=self._name, observed_at=READ),
            symbol_echo=symbol.upper(),
            **values,  # type: ignore[arg-type]
        )


class _Chain:
    """The stored chain readings, produced by the real provider."""

    @staticmethod
    def facts(symbol: str) -> tuple[SupplyFact, ...]:
        provider = PrimarySupplyProvider(
            cardano=_FakeCardano(),  # type: ignore[arg-type]
            hyperliquid=_FakeHyperliquid(),  # type: ignore[arg-type]
            arbitrum=_FakeArbitrum(),  # type: ignore[arg-type]
            subtensor=_FakeSubtensor(),  # type: ignore[arg-type]
        )

        return provider.facts(symbol)


class _FakeCardano:
    SURFACE = type("S", (), {"name": "Cardano ledger totals"})

    @staticmethod
    def totals() -> dict[str, object]:
        return dict(_ADA_LEDGER)


class _FakeHyperliquid:
    SURFACE = type("S", (), {"name": "Hyperliquid info API"})

    @staticmethod
    def token() -> dict[str, object]:
        return dict(_HYPE_TOKEN)


class _FakeArbitrum:
    @staticmethod
    def total_supply() -> object:
        from app.providers.primary_sources import ArbitrumRpc

        provider = ArbitrumRpc()

        provider._post = lambda payload: {  # type: ignore[method-assign]
            "result": hex(9_999_998_977_630_200_000_000_000_000)
        }

        return provider.total_supply()


class _FakeSubtensor:
    @staticmethod
    def total_issuance() -> object:
        from app.providers.primary_sources import SubtensorRpc

        provider = SubtensorRpc()

        provider._post = lambda payload: {  # type: ignore[method-assign]
            "result": "0x" + (11_218_142_119_340_581).to_bytes(8, "little").hex()
        }

        return provider.total_issuance()


def _service() -> SupplySemanticsService:
    return SupplySemanticsService(
        sources=tuple(  # type: ignore[arg-type]
            _Vendor(name) for name in ("TokenInsight", "CoinGecko", "Yahoo Finance")
        ),
        primary=_Chain(),  # type: ignore[arg-type]
    )


def _picture(symbol: str):  # type: ignore[no-untyped-def]
    picture = _service().established(symbol, AssetClass.CRYPTO)

    assert picture is not None

    return picture


# ── acceptance 1: circulating supply is not one primitive ───────────


def test_supply_is_a_vocabulary_rather_than_a_field() -> None:
    """Acceptance 1.

    Five concepts, each forced by the corpus. Nothing in the layer is
    allowed to call an unqualified `circulating_supply` a fact.
    """

    assert len(list(SupplyConcept)) == 5

    assert SupplyConcept.CIRCULATING_ESTIMATE.is_methodology_dependent
    assert SupplyConcept.EXCLUDED_BALANCE.is_methodology_dependent
    assert not SupplyConcept.EMITTED_SUPPLY.is_methodology_dependent
    assert not SupplyConcept.MAX_SUPPLY.is_methodology_dependent


def test_every_circulating_figure_names_whose_definition_produced_it() -> None:
    for symbol in ("ADA", "HYPE", "ARB", "TAO", "BTC"):
        for fact in _picture(symbol).of(SupplyConcept.CIRCULATING_ESTIMATE):
            assert fact.methodology.defined_by, (symbol, fact.source)
            assert fact.methodology.stated, (symbol, fact.source)


# ── acceptance 2 and 3: ADA, and the rule ───────────────────────────


def test_ada_provider_differences_map_to_ledger_semantics() -> None:
    """Acceptance 2.

    Three vendors, three ledger quantities, each to within a rounding
    error. TokenInsight was never reporting a circulating estimate at
    all — it was reporting everything the ledger has issued.
    """

    picture = _picture("ADA")

    emitted = {
        fact.source: fact.value for fact in picture.of(SupplyConcept.EMITTED_SUPPLY)
    }

    assert emitted["Cardano ledger totals"] == 38_803_572_882.173527
    assert emitted["TokenInsight"] == 38_803_572_882.0

    circulating = {
        fact.source: fact.value
        for fact in picture.of(SupplyConcept.CIRCULATING_ESTIMATE)
    }

    assert circulating["Cardano ledger totals"] == 36_550_320_207.145109
    assert circulating["Yahoo Finance"] == 36_550_320_128.0
    assert circulating["CoinGecko"] == 37_353_519_634.0


def test_ada_stops_conflicting_because_the_concepts_differ() -> None:
    """Acceptance 3, and the key outcome of the whole slice.

    The three-way circulating disagreement resolves into two
    corroborations and two coexistences. What remains a conflict is a
    genuine one, and it is not about circulating supply at all.
    """

    picture = _picture("ADA")

    # Keyed by concept as well as by the two sources: the same pair of
    # vendors is compared once per quantity, and a pair-only key would
    # let the last comparison overwrite the one being asserted.
    verdicts = {
        (item.left.concept, item.left.source, item.right.source): item.verdict
        for item in picture.comparisons
    }

    # TokenInsight was measuring the ledger's own supply.
    assert (
        verdicts[
            (SupplyConcept.EMITTED_SUPPLY, "Cardano ledger totals", "TokenInsight")
        ]
        is Comparison.CORROBORATED
    )

    # The reading S1 *rejected* matches the ledger's circulation.
    assert verdicts[
        (SupplyConcept.CIRCULATING_ESTIMATE, "Cardano ledger totals", "Yahoo Finance")
    ] is (Comparison.CORROBORATED)

    # CoinGecko counts rewards; the ledger's circulation does not. Both
    # are right, and the numbers differing is not a contradiction.
    assert (
        verdicts[
            (SupplyConcept.CIRCULATING_ESTIMATE, "Cardano ledger totals", "CoinGecko")
        ]
        is Comparison.COEXIST
    )
    assert (
        verdicts[(SupplyConcept.CIRCULATING_ESTIMATE, "CoinGecko", "Yahoo Finance")]
        is Comparison.COEXIST
    )

    # And the survivor is real: CoinGecko's "total supply" is Cardano's
    # protocol maximum, which the chain contradicts.
    assert (
        verdicts[(SupplyConcept.EMITTED_SUPPLY, "TokenInsight", "CoinGecko")]
        is Comparison.CONFLICTED
    )


def test_an_undisclosed_definition_never_earns_coexistence() -> None:
    """The rule that keeps the door from swinging too far open.

    Not knowing what a vendor excluded is a gap in this platform. If it
    counted as evidence of a different methodology, any two numbers
    could avoid conflicting by being equally unexplained.
    """

    def _fact(source: str, value: float, disclosed: bool) -> SupplyFact:
        from app.domain.supply_mappings import CARDANO_CIRCULATION, undisclosed

        return SupplyFact(
            concept=SupplyConcept.CIRCULATING_ESTIMATE,
            methodology=(CARDANO_CIRCULATION if disclosed else undisclosed(source)),
            value=value,
            unit="tokens",
            authority=EvidenceAuthority.SECONDARY_AGGREGATE,
            standing=EvidenceStanding.CLAIMED,
            source=source,
        )

    # Two silent vendors are presumed to be claiming the same fact.
    both_silent = compare(
        _fact("A", 100.0, disclosed=False), _fact("B", 200.0, disclosed=False)
    )

    assert both_silent.verdict is Comparison.CONFLICTED

    # And one disclosed against one silent does not coexist either: only
    # a *known* difference of definition earns that.
    mixed = compare(
        _fact("A", 100.0, disclosed=True), _fact("B", 200.0, disclosed=False)
    )

    assert mixed.verdict is Comparison.CONFLICTED
    assert "not evidence of a different one" in mixed.because

    # Two disclosed and genuinely different definitions do coexist.
    from app.domain.supply_mappings import (
        CARDANO_CIRCULATION,
        CARDANO_CIRCULATION_AND_REWARDS,
    )

    left = _fact("A", 100.0, disclosed=True)
    right = SupplyFact(
        concept=SupplyConcept.CIRCULATING_ESTIMATE,
        methodology=CARDANO_CIRCULATION_AND_REWARDS,
        value=200.0,
        unit="tokens",
        authority=EvidenceAuthority.SECONDARY_AGGREGATE,
        standing=EvidenceStanding.CLAIMED,
        source="B",
    )

    assert left.methodology.key == CARDANO_CIRCULATION.key
    assert compare(left, right).verdict is Comparison.COEXIST


# ── acceptance 4 and 5: HYPE ────────────────────────────────────────


def test_hype_future_emissions_are_not_counted_as_existing() -> None:
    """Acceptance 4.

    The protocol's own `totalSupply` counts 412 million tokens that do
    not exist. Emitted supply is the subtraction, and the future half is
    kept as its own fact rather than folded away.
    """

    picture = _picture("HYPE")

    emitted = picture.of(SupplyConcept.EMITTED_SUPPLY)
    future = picture.of(SupplyConcept.FUTURE_EMISSIONS)

    assert len(future) == 1
    assert future[0].value == 412_513_564.9696

    chain = next(fact for fact in emitted if fact.source == "Hyperliquid info API")

    assert chain.value == 999_044_028.5858 - 412_513_564.9696
    assert chain.value < float(_HYPE_TOKEN["totalSupply"])  # type: ignore[arg-type]


def test_hype_circulating_retains_its_exclusion_methodology() -> None:
    """Acceptance 5 and 9.

    The protocol's figure is not "the true circulating supply" — it is
    emitted supply after four named exclusions, and each exclusion is
    kept as its own balance. The Assistance Fund appears here as one of
    them and nowhere near its value-accrual role.
    """

    picture = _picture("HYPE")

    protocol = next(
        fact
        for fact in picture.of(SupplyConcept.CIRCULATING_ESTIMATE)
        if fact.source == "Hyperliquid info API"
    )

    assert protocol.methodology.disclosed
    assert len(protocol.methodology.excludes) == 4
    assert any("Assistance Fund" in item for item in protocol.methodology.excludes)

    excluded = picture.of(SupplyConcept.EXCLUDED_BALANCE)

    assert len(excluded) == 4

    fund = next(
        fact for fact in excluded if (fact.reported_as or "").startswith("0xfefe")
    )

    assert fund.value == 46_311_782.5847392306

    # The exclusions reconcile against the protocol's own figure.
    emitted = 999_044_028.5858 - 412_513_564.9696
    total_excluded = sum(fact.value for fact in excluded)

    assert round(emitted - total_excluded, 4) == protocol.value


def test_hype_remains_methodology_dependent() -> None:
    """Acceptance 5: S4.6 succeeds without inventing a true figure.

    Three sources, three numbers, and two of them publish nothing about
    what they exclude. The disagreement stands, and it stands for a
    stated reason.
    """

    picture = _picture("HYPE")

    assert picture.has_methodology_disagreement
    assert picture.conflicts

    estimates = {
        fact.source: fact.value
        for fact in picture.of(SupplyConcept.CIRCULATING_ESTIMATE)
    }

    assert estimates["Hyperliquid info API"] == 299_022_746.6799
    assert estimates["TokenInsight"] == 336_685_219.0
    assert estimates["CoinGecko"] == 222_445_714.0

    assert any(
        "do not publish what they exclude" in item.because for item in picture.conflicts
    )


def test_the_assistance_fund_is_not_merged_with_value_accrual() -> None:
    """Acceptance 9.

    One address, two analytical relationships. The supply layer knows
    it as a balance excluded from circulating and knows nothing about
    fees; the protocol-economics layer knows the reverse.
    """

    supply = _code("app/domain/supply_semantics.py") + _code(
        "app/providers/primary_supply_provider.py"
    )

    assert "holder_revenue" not in supply
    assert "protocol_revenue" not in supply
    assert "fees" not in supply.casefold()


# ── acceptance 6: ARB staleness needs evidence ──────────────────────


def test_arb_staleness_is_stated_as_evidence_not_as_precedence() -> None:
    """Acceptance 6.

    The figure is exactly the documented launch float and lands on a
    round number to seven significant figures. That is evidence, and the
    mapping says in as many words that it is not proof — no rule here
    makes an older or smaller provider lose.
    """

    mapping = next(
        item
        for item in mappings_for("ARB", "TokenInsight")
        if item.fact == "circulating_supply"
    )

    caveat = " ".join(mapping.caveats)

    assert "round number" in caveat
    assert "not proof" in caveat
    assert "dated readings" in caveat

    picture = _picture("ARB")

    # The conflict stands: nothing was resolved by precedence.
    assert picture.conflicts

    # And the chain corroborates CoinGecko's total, which is the one
    # thing the primary reading can settle.
    emitted = {
        fact.source: fact.value for fact in picture.of(SupplyConcept.EMITTED_SUPPLY)
    }

    assert round(emitted["Arbitrum One JSON-RPC"]) == 9_999_998_978
    assert emitted["CoinGecko"] == 10_000_000_000.0


def test_no_rule_prefers_a_provider() -> None:
    """Time alone does not establish truth, and neither does a name."""

    code = _code("app/domain/supply_semantics.py")

    for vendor in ("TokenInsight", "CoinGecko", "Yahoo"):
        assert vendor not in code


# ── acceptance 7: TAO may stay unresolved ───────────────────────────


def test_tao_emitted_supply_is_now_primary_and_the_rest_is_not() -> None:
    """Acceptance 7.

    The chain answers what exists. What circulates depends on whether
    staked TAO counts, and the chain has no opinion — so the vendors'
    estimates keep conflicting and the reason is stated.
    """

    picture = _picture("TAO")

    emitted = {
        fact.source: fact.value for fact in picture.of(SupplyConcept.EMITTED_SUPPLY)
    }

    assert round(emitted["Bittensor Subtensor JSON-RPC"], 6) == 11_218_142.119341

    # CoinGecko's "total supply" is the protocol maximum, and the chain
    # says otherwise. A real conflict, found by primary evidence.
    assert emitted["CoinGecko"] == 21_000_000.0

    assert picture.conflicts
    assert picture.unresolved


# ── acceptance 8: methodology is versioned and reproducible ─────────


def test_a_methodology_carries_a_version_and_a_comparison_key() -> None:
    """Acceptance 8.

    Two figures compare only if concept and methodology match, version
    included — so a definition that changes makes later readings
    knowably incomparable rather than silently comparable.
    """

    picture = _picture("ADA")

    for fact in picture.facts:
        assert fact.methodology.version
        assert "@" in fact.comparable_key
        assert fact.comparable_key.startswith(fact.concept.value)


def test_the_chain_readings_name_what_they_were_computed_from() -> None:
    for symbol in ("ADA", "HYPE", "ARB", "TAO"):
        chain = [fact for fact in _picture(symbol).facts if fact.authority.is_primary]

        assert chain, symbol

        for fact in chain:
            assert fact.components, (symbol, fact.concept)


def test_the_substrate_storage_key_is_derived_not_remembered() -> None:
    """A wrong key returns null rather than a wrong number.

    XXH64 is implemented here rather than imported, so the algorithm's
    own published vectors are the check — and the derived key is the one
    the chain answered to during the measurement.
    """

    assert _xxh64(b"") == 0xEF46DB3751D8E999
    assert _xxh64(b"a") == 0xD24EC4F1A98C6E5B

    assert storage_key("SubtensorModule", "TotalIssuance") == (
        "0x658faa385070e074c85bf6b568cf055557c875e4cff74148e4628f264b974c80"
    )


# ── acceptance 10, 11, 12, 13: nothing moved ────────────────────────


def test_no_dilution_or_quality_word_appears_anywhere() -> None:
    """Acceptance 10.

    Supply facts, and nothing about what they imply. Whether a structure
    is dilutive is S5's question and no word here anticipates it.
    """

    forbidden = (
        "dilution",
        "dilutive",
        "attractive",
        "favourable",
        "adverse",
        "supply_pressure",
        "tokenomics",
    )

    for module in (
        "app/domain/supply_semantics.py",
        "app/domain/supply_mappings.py",
        "app/providers/primary_supply_provider.py",
        "app/services/supply_semantics_service.py",
        "app/api/models/supply_adapter.py",
    ):
        code = _code(module).casefold()

        for word in forbidden:
            assert word not in code, (module, word)


def test_no_score_or_decision_path_can_import_the_supply_layer() -> None:
    """Acceptance 11: the standings a score reads are untouched."""

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
        "app/services/business_quality_service.py",
        "app/services/company_facts_service.py",
        "app/services/company_signal_service.py",
        "app/services/crypto_quality_signal_service.py",
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
                    "supply_semantics",
                    "supply_mappings",
                    "primary_supply_provider",
                )
            ):
                offenders.append(str(source.relative_to(root)))

    assert offenders == []


def test_the_token_fact_gate_is_not_rewritten() -> None:
    """Acceptance 12: S1's verdicts stand.

    The semantic layer explains a conflict; it does not resolve one in
    the store. `judge()` is untouched, so `CompanyFactsService` reads
    exactly what it read before and no factor moves.
    """

    code = _code("app/services/supply_semantics_service.py")

    assert "judge" not in code

    from app.services.crypto_quality_signal_service import CryptoQualitySignalService

    assert CryptoQualitySignalService.MOSTLY_ISSUED == 0.90
    assert CryptoQualitySignalService.PARTLY_ISSUED == 0.60
    assert CryptoQualitySignalService.MINIMUM_MEASURED == 2


def test_btc_is_unchanged_by_any_of_it() -> None:
    """Every reading agrees, and there is nothing to explain."""

    picture = _picture("BTC")

    assert not picture.conflicts
    assert not picture.coexisting
    assert not picture.has_methodology_disagreement


def test_equity_behaviour_is_unchanged() -> None:
    """Acceptance 13."""

    # Checked on what each module can reach: `playbook.py` has said
    # "network scale and supply" since long before this slice, and a
    # word search would forbid it from describing a digital asset.
    for module in (
        "app/domain/financial_question.py",
        "app/domain/playbook.py",
        "app/services/playbook_selector.py",
        "app/services/quality_signal_service.py",
    ):
        code = _code(module)

        assert "supply_semantics" not in code, module
        assert "supply_mappings" not in code, module
        assert "SupplyConcept" not in code, module


def test_nothing_but_a_cryptocurrency_gets_a_supply_picture() -> None:
    service = _service()

    for asset_class in (AssetClass.STOCK, AssetClass.ETF, AssetClass.UNKNOWN, None):
        assert service.established("ADA", asset_class) is None


def test_a_security_with_no_chain_reading_says_so() -> None:
    picture = _picture("BTC")

    assert any("No chain reading" in item for item in picture.unresolved)
