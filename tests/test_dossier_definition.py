"""What kind of investment case each kind of security gets.

The asset-specific definition beneath the shared dossier shell. These
tests pin the semantics the backend declares — titles, headings, score
names, and which sections belong — because the page renders them
verbatim and infers nothing.
"""

from app.domain.asset_class import AssetClass
from app.domain.dossier_definition import DossierKind, definition_for
from app.domain.score_basis import SCORE_LABELS, score_labels_for


def test_a_stock_is_an_equity_dossier() -> None:
    definition = definition_for(AssetClass.STOCK)

    assert definition.kind is DossierKind.EQUITY
    assert definition.title == "Equity dossier"
    assert definition.classification_heading == "Company type"
    assert definition.score_labels["quality"] == "Business quality"
    assert definition.filings_apply
    assert definition.filings_inapplicable_because is None


def test_a_cryptocurrency_is_a_crypto_dossier() -> None:
    """One is ownership in a business; the other is a crypto asset."""

    definition = definition_for(AssetClass.CRYPTO)

    assert definition.kind is DossierKind.CRYPTO
    assert definition.title == "Crypto dossier"
    assert definition.classification_heading == "Asset type"

    # A token's quality score counts network scale, liquidity, issuance
    # and age. Real measurements, none of them about a business.
    assert definition.score_labels["quality"] == "Asset quality"


def test_a_token_has_no_filings_rather_than_unread_ones() -> None:
    """Not applicable is not missing.

    A crypto dossier used to render "No filing has been read for BTC.
    Reading one is an explicit spend…" — an acquisition-shaped absence
    promising work nobody can do. The definition states the truth: the
    subject publishes none, as a property of the asset class.
    """

    definition = definition_for(AssetClass.CRYPTO)

    assert not definition.filings_apply
    assert definition.filings_inapplicable_because is not None
    assert "publishes no filings" in definition.filings_inapplicable_because
    assert "property of the asset class" in definition.filings_inapplicable_because
    assert "not missing evidence" in definition.filings_inapplicable_because


def test_a_commodity_shares_the_no_filings_fact_and_nothing_else() -> None:
    """Gold files no accounts either, but it is not a crypto dossier."""

    definition = definition_for(AssetClass.COMMODITY)

    assert definition.kind is DossierKind.GENERAL
    assert not definition.filings_apply
    assert definition.filings_inapplicable_because is not None
    assert "commodity" in definition.filings_inapplicable_because

    # No business behind it, so its quality is not called a business's.
    assert definition.score_labels["quality"] == "Asset quality"


def test_an_unclassified_security_gets_the_general_case() -> None:
    """A kind nobody established is not promoted to a company or a token."""

    for asset_class in (AssetClass.UNKNOWN, None):
        definition = definition_for(asset_class)

        assert definition.kind is DossierKind.GENERAL, asset_class
        assert definition.title == "Investment dossier", asset_class
        assert definition.classification_heading == "Investment type", asset_class
        assert definition.filings_apply, asset_class


def test_a_fund_gets_the_general_case_with_its_own_filings_boundary() -> None:
    """A fund dossier is still a named future specialization (F1 built
    none), but its filings absence is its own: company filing knowledge
    is not part of the fund playbook, worded as this platform's limit —
    never as a claim about what funds publish, in either direction."""

    definition = definition_for(AssetClass.ETF)

    assert definition.kind is DossierKind.GENERAL
    assert definition.title == "Investment dossier"
    assert definition.classification_heading == "Investment type"
    assert not definition.filings_apply

    reason = definition.filings_inapplicable_because or ""

    assert "not part of the fund playbook" in reason
    assert "limit of this platform" in reason
    assert "publishes no" not in reason


def test_every_definition_names_all_five_scores() -> None:
    """The label set is the score set: nothing renders unnamed."""

    for asset_class in (*AssetClass, None):
        definition = definition_for(asset_class)

        assert set(definition.score_labels) == set(SCORE_LABELS), asset_class
        assert all(definition.score_labels.values()), asset_class


def test_score_labels_follow_the_one_positive_kind_fact() -> None:
    """Asset labels only where the class is known to have no company.

    UNKNOWN keeps the company labels: calling an unclassified security's
    quality "Asset quality" would assert a kind nobody established.
    """

    assert score_labels_for(AssetClass.CRYPTO)["quality"] == "Asset quality"
    assert score_labels_for(AssetClass.COMMODITY)["quality"] == "Asset quality"

    # A fund joined the boundary in F1: no fund surface may be labelled
    # "Business quality" while no business-quality assessment runs for it.
    assert score_labels_for(AssetClass.ETF)["quality"] == "Asset quality"

    assert score_labels_for(AssetClass.STOCK) == SCORE_LABELS
    assert score_labels_for(AssetClass.UNKNOWN) == SCORE_LABELS
    assert score_labels_for(None) == SCORE_LABELS


def test_only_the_quality_label_varies() -> None:
    """The other four scores mean the same thing for every asset.

    Evidence, valuation, safety and portfolio fit are claims about the
    reading, the price, the record and the account — not about whether
    a business stands behind the security.
    """

    crypto = definition_for(AssetClass.CRYPTO).score_labels

    for name, label in SCORE_LABELS.items():
        if name == "quality":
            continue

        assert crypto[name] == label, name
