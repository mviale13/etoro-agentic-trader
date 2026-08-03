"""What kind of thing a security is."""

from __future__ import annotations

from enum import StrEnum


class AssetClass(StrEnum):
    """
    The kind of asset an instrument represents.

    Different kinds of asset are evidenced differently, and by different
    tickers. A company has fundamentals; a cryptocurrency has none, and a
    company data provider asked about one still answers — with a market
    capitalisation that reads exactly like a balance-sheet figure. Knowing
    the kind is what stops the platform assessing a token as if it were a
    business, and what tells it which ticker actually prices the asset.
    """

    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    UNKNOWN = "unknown"

    @classmethod
    def from_etoro(
        cls,
        asset_type_id: int,
    ) -> AssetClass:
        """Classify an eToro instrument by its asset type id."""

        return _ETORO_ASSET_TYPES.get(asset_type_id, cls.UNKNOWN)

    @property
    def has_company_fundamentals(self) -> bool:
        """Whether asking a company data provider about this is meaningful."""

        return self in (AssetClass.STOCK, AssetClass.ETF)

    @property
    def has_no_company(self) -> bool:
        """
        Positively known to have no business behind it.

        Deliberately not `not has_company_fundamentals`. An instrument this
        platform could not classify is UNKNOWN, and saying an unknown thing
        has no business would be asserting something nobody established —
        the same substitution the rest of the decision path stopped making.
        """

        return self in (AssetClass.CRYPTO, AssetClass.COMMODITY)

    @property
    def noun(self) -> str:
        """How to name this to the investor, in a sentence."""

        return _NOUNS.get(self, "security")


#: eToro's asset type ids, as observed in the investor's own watchlists.
#:
#: Only the ids the account actually holds or watches are mapped. An id
#: nobody has seen is UNKNOWN rather than guessed, because a wrong class
#: here would send a security to the wrong ticker and the wrong evidence.
_ETORO_ASSET_TYPES: dict[int, AssetClass] = {
    2: AssetClass.COMMODITY,
    5: AssetClass.STOCK,
    6: AssetClass.ETF,
    10: AssetClass.CRYPTO,
}


#: Names that read as English rather than as an enum value.
_NOUNS = {
    AssetClass.STOCK: "company",
    AssetClass.ETF: "fund",
    AssetClass.CRYPTO: "cryptocurrency",
    AssetClass.COMMODITY: "commodity",
}
