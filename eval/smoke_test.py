"""
Phase 1 smoke test — verify LangSmith tracing works end-to-end.

Run: python -m eval.smoke_test
Expected: agent returns a response, trace appears in LangSmith project H-agent_eval.
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from psycopg_pool import AsyncConnectionPool

from app.agent.graph import create_agent
from app.config import settings


async def main():
    print(f"[smoke_test] LANGSMITH_TRACING={os.getenv('LANGSMITH_TRACING')}")
    print(f"[smoke_test] LANGSMITH_PROJECT={os.getenv('LANGSMITH_PROJECT')}")
    print(f"[smoke_test] MODEL_PROVIDER={settings.model_provider}")

    pool = AsyncConnectionPool(conninfo=settings.checkpointer_db_url, open=False)
    await pool.open()
    print("[smoke_test] DB pool opened")

    agent = await create_agent(pool)
    print("[smoke_test] Agent created")

    config = {"configurable": {"thread_id": "eval_smoke_001"}}
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "halo"}]},
        config=config,
    )

    response = result["messages"][-1].content
    print(f"[smoke_test] Response: {response[:200]}")
    print("[smoke_test] Done — check LangSmith dashboard: https://smith.langchain.com")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
