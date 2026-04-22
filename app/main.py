import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from app.agent.graph import create_agent
from app.config import settings
from app.db.database import engine
from app.db.models import Base
from app.telegram.bot import create_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    pool = AsyncConnectionPool(conninfo=settings.checkpointer_db_url, open=False)
    await pool.open()
    logger.info("Postgres connection pool opened")

    app.state.agent = await create_agent(pool)
    logger.info("Agent initialized")

    bot = create_bot(app.state.agent)
    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()
    logger.info("Telegram bot polling started")

    yield

    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()
    await pool.close()
    logger.info("Shutdown complete")


app = FastAPI(title="Health Intelligence Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    result = await app.state.agent.ainvoke(
        {"messages": [("user", request.message)]},
        config=config,
    )

    response = ""
    for msg in reversed(result["messages"]):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            response = msg.content
            break

    return {"response": response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
