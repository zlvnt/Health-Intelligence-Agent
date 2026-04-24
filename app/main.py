import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from app.agent.flow_logger import run_and_log
from app.agent.graph import create_agent
from app.config import settings
from app.db.database import engine
from app.db.models import Base
from app.telegram.bot import create_bot

CHAT_LOG_DIR = Path("logs/chat")

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

    bot = None
    if settings.telegram_bot_token and settings.telegram_bot_token != "your-bot-token-here":
        bot = create_bot(app.state.agent)
        await bot.initialize()
        await bot.start()
        await bot.updater.start_polling()
        logger.info("Telegram bot polling started")
    else:
        logger.info("Telegram token not set, skipping bot")

    yield

    if bot:
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


def _extract_text(msg) -> str:
    content = getattr(msg, "content", None)
    if not content:
        return ""
    if isinstance(content, list):
        return "".join(
            block["text"] for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    if isinstance(content, str):
        return content.strip()
    return ""


@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    response = await run_and_log(
        app.state.agent,
        request.message,
        config,
        CHAT_LOG_DIR,
    )
    return {"response": response}


@app.get("/chat/history")
async def chat_history(session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    try:
        state = await app.state.agent.aget_state(config)
    except Exception:
        return {"messages": []}

    if not state or not getattr(state, "values", None):
        return {"messages": []}

    messages = state.values.get("messages", [])
    result = []
    last_assistant = None

    for msg in messages:
        msg_type = getattr(msg, "type", None)
        if msg_type == "human":
            if last_assistant:
                result.append({"role": "assistant", "content": last_assistant})
                last_assistant = None
            text = _extract_text(msg)
            if text:
                result.append({"role": "user", "content": text})
        elif msg_type == "ai":
            text = _extract_text(msg)
            if text:
                last_assistant = text

    if last_assistant:
        result.append({"role": "assistant", "content": last_assistant})

    return {"messages": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
