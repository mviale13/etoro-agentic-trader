"""What the configured credentials are allowed to do."""

from app.domain.api_grant import ApiGrant

#: The scopes the live API actually returned, verbatim.
GRANTED = [
    "etoro-public:market-data:read",
    "etoro-public:money.balance:read",
    "etoro-public:trade.demo:read",
    "etoro-public:trade.demo:write",
    "etoro-public:trade.real:read",
    "etoro-public:trade.real:write",
    "etoro-public:watchlist:read",
    "etoro-public:watchlist:write",
]

ME = {
    "gcid": 27756168,
    "realCid": 111,
    "demoCid": 222,
    "username": "movr",
    "firstName": "Marcos",
    "dateOfBirth": "1980-01-01",
    "scopes": GRANTED,
}


def test_capability_is_read_off_the_scope_not_off_a_known_list() -> None:
    """
    The trap this walked into, caught by running it against the real API.

    The published documentation names the trading scopes
    `etoro-public:real:write` and `etoro-public:demo:write`. The live API
    returns `etoro-public:trade.real:write`. Matching the documented list
    failed open: a key able to place real orders was reported read-only,
    which is the most dangerous direction for the mistake to run.
    """

    grant = ApiGrant.from_payload(ME)

    assert grant.can_trade_real
    assert not grant.is_read_only

    # A scope nobody has documented is still a write.
    invented = ApiGrant(scopes=("etoro-public:something-new:write",))

    assert invented.write_scopes == ("etoro-public:something-new:write",)
    assert not invented.is_read_only


def test_real_money_trading_is_named_first_and_plainly() -> None:
    grant = ApiGrant.from_payload(ME)

    assert grant.stated == (
        "can place real-money orders, and holds 3 write permissions in total"
    )


def test_the_other_write_permissions_are_counted_not_dismissed() -> None:
    """This platform does not know what all of them reach."""

    grant = ApiGrant.from_payload(ME)

    assert len(grant.write_scopes) == 3
    assert "3 write permissions" in grant.stated


def test_genuinely_read_only_credentials_say_so() -> None:
    grant = ApiGrant.from_payload(
        {**ME, "scopes": [s for s in GRANTED if s.endswith(":read")]}
    )

    assert grant.is_read_only
    assert grant.stated == "read-only"


def test_unreported_scopes_are_not_read_as_harmless() -> None:
    """
    An absent `scopes` array means eToro did not say.

    Reporting that as read-only would turn a gap in knowledge into a
    safety claim — the substitution the rest of this platform stopped
    making everywhere else.
    """

    grant = ApiGrant.from_payload({"gcid": 1})

    assert grant.scopes == ()
    assert not grant.is_read_only
    assert grant.stated == "no scopes reported"


def test_only_identifiers_and_scopes_are_kept() -> None:
    """The response also carries a name, a date of birth and a gender."""

    grant = ApiGrant.from_payload(ME)

    assert grant.real_account_id == 111
    assert grant.demo_account_id == 222
    assert not hasattr(grant, "first_name")
    assert not hasattr(grant, "date_of_birth")


def test_a_missing_identifier_stays_missing() -> None:
    grant = ApiGrant.from_payload({"scopes": [], "realCid": None, "demoCid": "222"})

    assert grant.real_account_id is None
    assert grant.demo_account_id is None
