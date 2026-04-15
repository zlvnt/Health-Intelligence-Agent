from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.sql import func

from app.db.database import async_session
from app.db.models import Meal, User


async def get_or_create_user(telegram_id: int) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def add_meal(
    telegram_id: int,
    food_name: str,
    calories: float,
    protein_g: float = 0.0,
    carbs_g: float = 0.0,
    fat_g: float = 0.0,
) -> Meal:
    async with async_session() as session:
        meal = Meal(
            telegram_id=telegram_id,
            food_name=food_name,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
        )
        session.add(meal)
        await session.commit()
        await session.refresh(meal)
        return meal


async def get_daily_meals(telegram_id: int) -> list[Meal]:
    today_start = datetime.combine(datetime.now().date(), time.min)
    async with async_session() as session:
        result = await session.execute(
            select(Meal)
            .where(Meal.telegram_id == telegram_id, Meal.logged_at >= today_start)
            .order_by(Meal.logged_at)
        )
        return list(result.scalars().all())


async def get_daily_totals(telegram_id: int) -> dict:
    today_start = datetime.combine(datetime.now().date(), time.min)
    async with async_session() as session:
        result = await session.execute(
            select(
                func.coalesce(func.sum(Meal.calories), 0),
                func.coalesce(func.sum(Meal.protein_g), 0),
                func.coalesce(func.sum(Meal.carbs_g), 0),
                func.coalesce(func.sum(Meal.fat_g), 0),
                func.count(Meal.id),
            ).where(Meal.telegram_id == telegram_id, Meal.logged_at >= today_start)
        )
        row = result.one()
        return {
            "calories": float(row[0]),
            "protein_g": float(row[1]),
            "carbs_g": float(row[2]),
            "fat_g": float(row[3]),
            "meal_count": row[4],
        }


async def get_meal_history(telegram_id: int, days: int = 7) -> list[Meal]:
    from datetime import timedelta

    since = datetime.now() - timedelta(days=days)
    async with async_session() as session:
        result = await session.execute(
            select(Meal)
            .where(Meal.telegram_id == telegram_id, Meal.logged_at >= since)
            .order_by(Meal.logged_at.desc())
        )
        return list(result.scalars().all())


async def set_calorie_goal(telegram_id: int, goal: float) -> float:
    user = await get_or_create_user(telegram_id)
    async with async_session() as session:
        user_ref = await session.get(User, user.id)
        user_ref.daily_calorie_goal = goal
        await session.commit()
    return goal


async def get_calorie_goal(telegram_id: int) -> float | None:
    user = await get_or_create_user(telegram_id)
    return user.daily_calorie_goal
