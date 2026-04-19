from langchain_core.tools import tool

from app.config import settings
from app.db import queries


def _get_telegram_id(telegram_id: int | None) -> int:
    """Get telegram_id, using test ID if in test mode and none provided."""
    if telegram_id is None:
        if settings.test_mode:
            return settings.test_telegram_id
        else:
            raise ValueError("telegram_id is required (not in test mode)")
    return telegram_id


# --- Tracking Agent Tools (existing) ---

@tool
async def log_meal(
    food_name: str,
    calories: float,
    telegram_id: int | None = None,
    protein_g: float = 0.0,
    carbs_g: float = 0.0,
    fat_g: float = 0.0,
) -> str:
    """Log a meal for the user. Call this after estimating nutrition info."""
    telegram_id = _get_telegram_id(telegram_id)

    meal = await queries.add_meal(
        telegram_id=telegram_id,
        food_name=food_name,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    )
    return f"Logged: {meal.food_name} ({meal.calories} kcal)"


@tool
async def get_daily_summary(telegram_id: int | None = None) -> str:
    """Get today's total nutrition intake and compare against calorie goal."""
    telegram_id = _get_telegram_id(telegram_id)

    totals = await queries.get_daily_totals(telegram_id)
    goal = await queries.get_calorie_goal(telegram_id)

    summary = (
        f"Today's intake ({totals['meal_count']} meals):\n"
        f"- Calories: {totals['calories']:.0f} kcal\n"
        f"- Protein: {totals['protein_g']:.1f}g\n"
        f"- Carbs: {totals['carbs_g']:.1f}g\n"
        f"- Fat: {totals['fat_g']:.1f}g"
    )

    if goal:
        remaining = goal - totals["calories"]
        summary += f"\n\nGoal: {goal:.0f} kcal | Remaining: {remaining:.0f} kcal"
    else:
        summary += "\n\nNo calorie goal set yet."

    return summary


@tool
async def get_meal_history(days: int = 7, telegram_id: int | None = None) -> str:
    """Get the user's meal history for the past N days."""
    telegram_id = _get_telegram_id(telegram_id)

    meals = await queries.get_meal_history(telegram_id, days)
    if not meals:
        return f"No meals logged in the past {days} days."

    lines = [f"Meals (past {days} days):"]
    for m in meals:
        date_str = m.logged_at.strftime("%b %d, %H:%M")
        lines.append(f"- {date_str}: {m.food_name} ({m.calories:.0f} kcal)")
    return "\n".join(lines)


@tool
async def set_calorie_goal(daily_calories: float, telegram_id: int | None = None) -> str:
    """Set or update the user's daily calorie goal."""
    telegram_id = _get_telegram_id(telegram_id)

    await queries.set_calorie_goal(telegram_id, daily_calories)
    return f"Daily calorie goal set to {daily_calories:.0f} kcal."


# --- Assessment Agent Tools (placeholder) ---

@tool
async def collect_health_data(data_type: str, value: str, telegram_id: int | None = None) -> str:
    """Store a piece of health/lifestyle data collected from the user.
    data_type examples: 'age', 'weight', 'height', 'activity_level', 'dietary_preference', 'health_goal'
    """
    telegram_id = _get_telegram_id(telegram_id)

    # TODO: persist to user profile in DB
    return f"Stored {data_type}: {value} for user {telegram_id}"


# --- Planning Agent Tools (placeholder) ---

@tool
async def create_health_plan(plan_summary: str, telegram_id: int | None = None) -> str:
    """Create and store a structured health plan for the user."""
    telegram_id = _get_telegram_id(telegram_id)

    # TODO: persist plan to DB
    return f"Health plan created for user {telegram_id}: {plan_summary}"


# --- Intervention Agent Tools (placeholder) ---

@tool
async def suggest_adjustment(issue: str, suggestion: str, telegram_id: int | None = None) -> str:
    """Suggest an adjustment to the user's health plan based on adherence issues."""
    telegram_id = _get_telegram_id(telegram_id)

    # TODO: persist adjustment to DB
    return f"Adjustment suggested for '{issue}': {suggestion}"
