class ExchangeRateService:
    EUR_PER_USD = 0.85

    def usd_to_eur(self, amount: float) -> float:
        return round(amount * self.EUR_PER_USD, 2)
