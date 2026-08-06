"""Which company a European ticker means, established rather than guessed."""

import pytest

from app.providers.european_issuers import EUROPEAN_ISSUERS, RegisteredIssuer
from app.providers.issuer_identity import (
    IssuerIdentityRegistry,
    IssuerRegistryError,
    IssuerUnknown,
)

EXAMPLE = RegisteredIssuer("BNP.PA", "FR0000131104", "BNP PARIBAS")


def record(lei: str, name: str) -> dict:
    return {"attributes": {"lei": lei, "entity": {"legalName": {"name": name}}}}


class Registry(IssuerIdentityRegistry):
    """The real registry with the call to GLEIF replaced, and counted."""

    def __init__(self, records: object, issuers: dict | None = None) -> None:
        super().__init__(
            issuers={EXAMPLE.symbol: EXAMPLE} if issuers is None else issuers
        )
        self.calls = 0
        self._records_returned = records

    def _records(self, issuer: RegisteredIssuer) -> list[dict]:
        self.calls += 1

        if isinstance(self._records_returned, Exception):
            raise self._records_returned

        return list(self._records_returned)


def test_a_symbol_off_the_list_is_a_gap_and_never_a_guess() -> None:
    """
    A ticker is not an identity, and a near-enough one is worse than none.

    `SAN` is Sanofi in Paris and Banco Santander in Madrid. A platform
    that resolved an unlisted symbol by resemblance would read a real
    filing, ground every quote in it, and describe the wrong company.
    """

    with pytest.raises(IssuerUnknown) as unknown:
        Registry([]).of("SAN")

    assert "not on this platform's list" in str(unknown.value)


def test_the_issuer_comes_from_the_body_that_maintains_the_mapping() -> None:
    identity = Registry([record("R0MUWSFPU8MPRO8K5P83", "BNP PARIBAS")]).of("bnp.pa")

    assert identity.lei == "R0MUWSFPU8MPRO8K5P83"
    assert identity.legal_name == "BNP PARIBAS"
    assert identity.isin == "FR0000131104"


def test_an_isin_that_now_names_another_company_is_refused() -> None:
    """
    The check the reviewed list exists to make possible.

    An ISIN mistyped into another real company's resolves perfectly well
    and returns a real LEI. What it cannot do is come back with the name
    the entry was verified against.
    """

    registry = Registry([record("549300E9PC51EN656011", "SANOFI")])

    with pytest.raises(IssuerUnknown) as refused:
        registry.of("BNP.PA")

    assert "verified again" in str(refused.value)


def test_a_longer_legal_name_still_matches_the_one_recorded() -> None:
    """A suffix is a renaming a reader would not call one."""

    identity = Registry([record("R0MUWSFPU8MPRO8K5P83", "BNP PARIBAS SA")]).of("BNP.PA")

    assert identity.lei == "R0MUWSFPU8MPRO8K5P83"


def test_an_ambiguous_answer_is_refused_rather_than_chosen_from() -> None:
    registry = Registry(
        [
            record("R0MUWSFPU8MPRO8K5P83", "BNP PARIBAS"),
            record("549300E9PC51EN656011", "SANOFI"),
        ]
    )

    with pytest.raises(IssuerUnknown) as refused:
        registry.of("BNP.PA")

    assert "2 companies" in str(refused.value)


def test_an_outage_is_a_different_answer_from_a_gap() -> None:
    """
    Only one of the two is worth asking about again.

    A caller told merely "no identity" could not tell a company this
    platform has not established from a register that was down for a
    minute.
    """

    registry = Registry(IssuerRegistryError("GLEIF could not be reached."))

    with pytest.raises(IssuerRegistryError):
        registry.of("BNP.PA")


def test_an_identity_is_established_once_per_run() -> None:
    """An issuer's LEI does not change between two lookups in one run.

    It is asked for twice — once to find the current document, once to
    check that the document fetched is the one that was found.
    """

    registry = Registry([record("R0MUWSFPU8MPRO8K5P83", "BNP PARIBAS")])

    registry.of("BNP.PA")
    registry.of("BNP.PA")

    assert registry.calls == 1


def test_every_listed_issuer_carries_an_isin_and_the_name_it_was_verified_as() -> None:
    """
    The list is the one link in the chain with no authority to ask.

    Which is exactly why each entry has to be checkable by hand: an ISIN
    a reader can look up against the exchange, and the legal name the
    lookup returned.
    """

    assert len(EUROPEAN_ISSUERS) > 30

    for symbol, issuer in EUROPEAN_ISSUERS.items():
        assert issuer.symbol == symbol
        assert len(issuer.isin) == 12
        assert issuer.isin[:2].isalpha()
        assert issuer.isin.isalnum()
        assert issuer.legal_name.strip()
