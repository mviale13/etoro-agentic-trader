from app.domain.pattern import Pattern
from app.services.investor_dna_service import InvestorDNAService


def test_confidence_is_zero_without_patterns() -> None:
    dna = InvestorDNAService().analyze([])

    assert dna.confidence == 0
    assert dna.avoids_high_volatility is False


def test_recurring_cash_pattern_updates_investor_dna() -> None:
    patterns = [
        Pattern(
            title="Recurring Cash Strategy",
            description="You consistently maintain a high cash allocation.",
            confidence=90,
        )
    ]

    dna = InvestorDNAService().analyze(patterns)

    assert dna.confidence == 90
    assert dna.avoids_high_volatility is True


def test_highest_pattern_confidence_is_used() -> None:
    patterns = [
        Pattern(
            title="Recurring Cash Strategy",
            description="You consistently maintain a high cash allocation.",
            confidence=80,
        ),
        Pattern(
            title="Diversification Pattern",
            description="Your portfolio is regularly diversified.",
            confidence=95,
        ),
    ]

    dna = InvestorDNAService().analyze(patterns)

    assert dna.confidence == 95
