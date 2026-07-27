from app.domain.daily_reflection import DailyReflection

REFLECTIONS: tuple[DailyReflection, ...] = (
    DailyReflection(
        title="CIO Reflection",
        message=(
            "A great investment advisor isn't the one that's always certain. "
            "It's the one that knows when certainty isn't possible."
        ),
        source="cio",
    ),
    DailyReflection(
        title="CIO Reflection",
        message=(
            "A healthy portfolio should create long periods where patience "
            "is the best decision."
        ),
        source="cio",
    ),
    DailyReflection(
        title="Doctor Reflection",
        message=("Risk deserves attention before opportunity."),
        source="doctor",
    ),
    DailyReflection(
        title="Scout Reflection",
        message=(
            "The companies everyone talks about are rarelythe only great opportunities."
        ),
        source="scout",
    ),
    DailyReflection(
        title="Memory Reflection",
        message=(
            "Your investing habits are becoming part of your competitive advantage."
        ),
        source="memory",
    ),
)
