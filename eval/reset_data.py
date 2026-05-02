"""
Phase 2 — Eval DB isolation.
Run before each eval batch to wipe eval test data.

Usage: python -m eval.reset_data
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()

import asyncpg

from app.config import settings


async def main():
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)

    # Eval users occupy telegram_id range 90001–90099
    meals = await conn.execute("DELETE FROM meals WHERE telegram_id BETWEEN 90001 AND 90099")
    users = await conn.execute("DELETE FROM users WHERE telegram_id BETWEEN 90001 AND 90099")

    print(f"[reset_data] {meals} meals deleted")
    print(f"[reset_data] {users} users deleted")

    await conn.close()
    print("[reset_data] Done — eval DB clean")


if __name__ == "__main__":
    asyncio.run(main())
