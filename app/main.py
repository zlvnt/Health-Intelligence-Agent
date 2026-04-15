import asyncio
import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.agent.graph import create_agent
from app.db.database import engine
from app.db.models import Base
from app.telegram.bot import create_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Health Intelligence Agent")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def run():
    await init_db()

    agent = await create_agent()
    logger.info("Agent initialized")

    bot = create_bot(agent)
    logger.info("Starting Telegram bot (polling)...")

    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()

    try:
        # Keep running until interrupted
        await asyncio.Event().wait()
    finally:
        await bot.updater.stop()
        await bot.stop()
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(run())
