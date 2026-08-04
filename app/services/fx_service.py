class FXService:
    USD_TO_EUR_RATE = 0.92

    def usd_to_eur(
        self,
        amount_usd: float,
    ) -> float:
        return round(
            amount_usd * self.USD_TO_EUR_RATE,
            2,
        )

    def portfolio(
        self,
        total_value_usd: float,
    ) -> dict[str, float]:
        return {
            "total_value_usd": total_value_usd,
            "total_value_eur": self.usd_to_eur(
                total_value_usd,
            ),
        }
