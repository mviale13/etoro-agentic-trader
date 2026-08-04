from app.domain.daily_reflection import DailyReflection


class DailyReflectionService:
    def today(self) -> DailyReflection:
        return DailyReflection(
            title="CIO Reflection",
            message=(
                "A healthy portfolio should create long periods "
                "where patience is the best decision."
            ),
            source="cio",
        )
