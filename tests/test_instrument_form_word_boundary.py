"""An instrument-form word is a word, never a run of letters.

`_forms` used to test membership by substring, so the letters e-t-f
inside *Netflix* counted as the form ETF — and because both providers
spell Netflix the same way, the join came out CORROBORATED: a false
cross-provider agreement manufactured from a coincidence of letters,
on the exact rung of the ladder that exists to be stronger than
assumption.

Extracted from PR #145's independently established defect. #145 itself
remains open and parked; nothing here touches `join_identity`, its
ladder, any identity gate, persistence, or history.
"""

from __future__ import annotations

import pytest

from app.domain.provider_identity import (
    _INSTRUMENT_FORMS,
    IdentityStanding,
    ProviderIdentityClaim,
    _forms,
    join_identity,
)


def claim(provider: str, name: str, symbol: str = "X") -> ProviderIdentityClaim:
    return ProviderIdentityClaim(provider=provider, symbol=symbol, name=name)


# ── the defect and its live consequence ─────────────────────────────


def test_netflix_carries_no_instrument_form() -> None:
    """Control 1: the letters e-t-f inside a company name are not ETF."""

    assert _forms("Netflix, Inc.") == frozenset()
    assert _forms("Netflix Inc") == frozenset()


def test_nflx_is_assumed_rather_than_manufactured_corroborated() -> None:
    """Control 2: the join NFLX actually gets from the held evidence.

    Both providers name the company, neither names a form, and a join
    with no form evidence on either side rests on symbol equality
    alone — ASSUMED, the honest floor. The substring reader gave both
    names the manufactured form ETF and called that agreement.
    """

    identity = join_identity(
        "NFLX",
        (
            claim("eToro", "Netflix", symbol="NFLX"),
            claim("Yahoo Finance", "Netflix, Inc.", symbol="NFLX"),
        ),
    )

    assert identity.standing is IdentityStanding.ASSUMED
    assert not identity.establishes_identity


def test_a_hyphen_bounds_a_form_word() -> None:
    """Control 3: punctuation is a boundary, not part of a word."""

    assert _forms("Sea Ltd-ADR") == frozenset({"adr"})


def test_se_stays_unresolved_when_one_provider_states_adr() -> None:
    """Control 4: a stated form against silence is not agreement.

    The word-boundary fix must not weaken this rung: one account says
    what kind of instrument this is, the other does not mention it,
    and silence is not assent.
    """

    identity = join_identity(
        "SE",
        (
            claim("eToro", "Sea Ltd-ADR", symbol="SE"),
            claim("Yahoo Finance", "Sea Limited", symbol="SE"),
        ),
    )

    assert identity.standing is IdentityStanding.UNRESOLVED
    assert not identity.establishes_identity


# ── the vocabulary, word by word ────────────────────────────────────


@pytest.mark.parametrize("form", _INSTRUMENT_FORMS)
def test_every_standalone_form_word_still_matches(form: str) -> None:
    """Control 5: the fix narrows *how* a word matches, never which."""

    assert _forms(f"Example {form.upper()} Securities") == frozenset({form})
    assert _forms(f"Example ({form.upper()})") == frozenset({form})
    assert _forms(f"{form.upper()}") == frozenset({form})


@pytest.mark.parametrize("form", _INSTRUMENT_FORMS)
def test_no_form_matches_inside_a_larger_alphabetic_word(form: str) -> None:
    """Control 6: embedded letters are that word's letters."""

    assert _forms(f"Ab{form}cd Holdings") == frozenset()
    assert _forms(f"{form}ish Group") == frozenset()
    assert _forms(f"Grand{form} plc") == frozenset()


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        # Real name shapes the substring reader got wrong.
        ("Netflix, Inc.", frozenset()),  # etf inside Netflix
        ("Banco de Madrid", frozenset()),  # adr inside Madrid
        ("TrustCo Bancorp", frozenset()),  # trust inside TrustCo
        ("Fletcher Building", frozenset()),  # etc inside Fletcher
        ("Etna Resources", frozenset()),  # etn inside Etna
        ("Refunding Corp", frozenset()),  # fund inside Refunding
        # And the genuine articles beside them.
        ("Northern Trust", frozenset({"trust"})),
        ("iShares $ Treasury Bond 0-1yr UCITS ETF", frozenset({"ucits", "etf"})),
        ("iPath Series B Carbon ETN", frozenset({"etn"})),
        ("WisdomTree Physical Gold ETC", frozenset({"etc"})),
        ("Fidelity Funds SICAV", frozenset({"sicav"})),
        ("Vanguard Wellington Fund", frozenset({"fund"})),
    ],
)
def test_lookalike_names_against_genuine_forms(name: str, expected: frozenset) -> None:
    assert _forms(name) == expected


@pytest.mark.parametrize(
    "spelling",
    ["Sea Ltd-ADR", "Sea Ltd - ADR", "SEA LTD (ADR)", "sea ltd adr", "Sea Ltd. ADR."],
)
def test_case_and_punctuation_variants_behave_identically(spelling: str) -> None:
    """Control 7: casing and delimiters change nothing."""

    assert _forms(spelling) == frozenset({"adr"})


@pytest.mark.parametrize("spelling", ["NETFLIX", "netflix", "Netflix.", "(Netflix)"])
def test_no_case_or_punctuation_variant_resurrects_the_defect(spelling: str) -> None:
    assert _forms(spelling) == frozenset()


# ── nothing else moved ──────────────────────────────────────────────


def test_the_form_vocabulary_is_unchanged() -> None:
    """The fix is the matcher; the words are exactly what they were."""

    assert _INSTRUMENT_FORMS == (
        "etf",
        "etn",
        "etc",
        "ucits",
        "fund",
        "trust",
        "adr",
        "sicav",
    )


def test_the_spcx_shape_still_resolves_the_same_way() -> None:
    """Control 8: the live conflict the module was built for is intact."""

    identity = join_identity(
        "SPCX",
        (
            claim("eToro", "Space Exploration Technologies Corp", symbol="SPCX"),
            claim("Yahoo Finance", "SPAC and New Issue ETF", symbol="SPCX"),
        ),
    )

    assert identity.standing is IdentityStanding.UNRESOLVED
