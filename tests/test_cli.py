from argparse import Namespace
from unittest.mock import AsyncMock, patch

import pytest

from app import cli


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_parser_accepts_brain_command() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["brain"])

    assert args.command == "brain"


def test_parser_accepts_company_symbol() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["company", "NVDA"])

    assert args.command == "company"
    assert args.symbol == "NVDA"


def test_parser_uses_default_explain_symbol() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["explain"])

    assert args.command == "explain"
    assert args.symbol == "SPY"


@pytest.mark.anyio
async def test_dispatches_brain_command() -> None:
    args = Namespace(command="brain")
    run = AsyncMock(return_value=0)

    with patch.dict(
        cli.COMMANDS,
        {
            "brain": (
                "Run the complete MOVRvest Artificial CIO pipeline",
                run,
            )
        },
    ):
        exit_code = await cli.dispatch(args)

    assert exit_code == 0
    run.assert_awaited_once_with()


@pytest.mark.anyio
async def test_dispatches_company_with_symbol() -> None:
    args = Namespace(
        command="company",
        symbol="MSFT",
    )

    with patch.object(
        cli.company,
        "run",
        new=AsyncMock(return_value=0),
    ) as run:
        exit_code = await cli.dispatch(args)

    assert exit_code == 0
    run.assert_awaited_once_with("MSFT")


@pytest.mark.anyio
async def test_dispatches_explain_with_symbol() -> None:
    args = Namespace(
        command="explain",
        symbol="ASML",
    )

    with patch.object(
        cli.explain,
        "run",
        new=AsyncMock(return_value=0),
    ) as run:
        exit_code = await cli.dispatch(args)

    assert exit_code == 0
    run.assert_awaited_once_with("ASML")


def test_parser_accepts_archetype_symbol() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["archetype", "DIS"])

    assert args.command == "archetype"
    assert args.symbol == "DIS"


@pytest.mark.anyio
async def test_dispatches_archetype_with_symbol() -> None:
    args = Namespace(
        command="archetype",
        symbol="NVDA",
    )

    with patch.object(
        cli.archetype,
        "run",
        new=AsyncMock(return_value=0),
    ) as run:
        exit_code = await cli.dispatch(args)

    assert exit_code == 0
    run.assert_awaited_once_with("NVDA")


def test_parser_accepts_decide_symbol_and_question() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["decide", "JPM", "entry"])

    assert args.command == "decide"
    assert args.symbol == "JPM"
    assert args.question == "entry"


@pytest.mark.anyio
async def test_dispatches_decide_with_symbol_and_question() -> None:
    args = Namespace(
        command="decide",
        symbol="JPM",
        question="entry",
    )

    with patch.object(
        cli.decide,
        "run",
        new=AsyncMock(return_value=0),
    ) as run:
        exit_code = await cli.dispatch(args)

    assert exit_code == 0
    run.assert_awaited_once_with("JPM", "entry")
