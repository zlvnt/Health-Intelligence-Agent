from langchain_core.tools import tool

from app.db import queries


# --- Tracking Agent Tools (existing) ---

@tool
async def log_meal(
    telegram_id: int,
    food_name: str,
    calories: float,
    protein_g: float = 0.0,
    carbs_g: float = 0.0,
    fat_g: float = 0.0,
) -> str:
    """Log a meal for the user. Call this after estimating nutrition info."""
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
async def get_daily_summary(telegram_id: int) -> str:
    """Get today's total nutrition intake and compare against calorie goal."""
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
async def get_meal_history(telegram_id: int, days: int = 7) -> str:
    """Get the user's meal history for the past N days."""
    meals = await queries.get_meal_history(telegram_id, days)
    if not meals:
        return f"No meals logged in the past {days} days."

    lines = [f"Meals (past {days} days):"]
    for m in meals:
        date_str = m.logged_at.strftime("%b %d, %H:%M")
        lines.append(f"- {date_str}: {m.food_name} ({m.calories:.0f} kcal)")
    return "\n".join(lines)


@tool
async def set_calorie_goal(telegram_id: int, daily_calories: float) -> str:
    """Set or update the user's daily calorie goal."""
    await queries.set_calorie_goal(telegram_id, daily_calories)
    return f"Daily calorie goal set to {daily_calories:.0f} kcal."


# --- Assessment Agent Tools (placeholder) ---

@tool
async def collect_health_data(telegram_id: int, data_type: str, value: str) -> str:
    """Store a piece of health/lifestyle data collected from the user.
    data_type examples: 'age', 'weight', 'height', 'activity_level', 'dietary_preference', 'health_goal'
    """
    # TODO: persist to user profile in DB
    return f"Stored {data_type}: {value} for user {telegram_id}"


# --- Planning Agent Tools (placeholder) ---

@tool
async def create_health_plan(telegram_id: int, plan_summary: str) -> str:
    """Create and store a structured health plan for the user."""
    # TODO: persist plan to DB
    return f"Health plan created for user {telegram_id}: {plan_summary}"


# --- Intervention Agent Tools (placeholder) ---

@tool
async def suggest_adjustment(telegram_id: int, issue: str, suggestion: str) -> str:
    """Suggest an adjustment to the user's health plan based on adherence issues."""
    # TODO: persist adjustment to DB
    return f"Adjustment suggested for '{issue}': {suggestion}"
