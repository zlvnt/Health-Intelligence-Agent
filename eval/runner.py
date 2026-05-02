"""
Phase 5 — Eval runner.
Invokes agent on 15 cases, runs all evaluators, sends results to LangSmith.

Usage:
    python -m eval.runner          # N=1 dev cycle
    python -m eval.runner --n 3    # N=3 final portfolio batch
"""
import argparse
import asyncio
import time

import asyncpg
from dotenv import load_dotenv

load_dotenv()

from langsmith import aevaluate
from psycopg_pool import AsyncConnectionPool

from app.agent.graph import create_agent
from app.config import settings
from eval.cases import user_id_to_telegram_id
from eval.evaluators.deepeval_wrappers import (
    response_quality_evaluator,
    task_completion_evaluator,
    tool_correctness_evaluator,
)
from eval.evaluators.loop_detection import loop_detection
from eval.evaluators.routing import routing_accuracy

_pool: AsyncConnectionPool | None = None
_agent = None


async def _init():
    global _pool, _agent
    _pool = AsyncConnectionPool(conninfo=settings.checkpointer_db_url, open=False)
    await _pool.open()
    _agent = await create_agent(_pool)
    print("[runner] Agent initialized")


async def _reset_case(telegram_id: int):
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    await conn.execute("DELETE FROM meals WHERE telegram_id = $1", telegram_id)
    await conn.execute("DELETE FROM users WHERE telegram_id = $1", telegram_id)
    await conn.close()


def _extract_route(messages: list) -> list[str]:
    route = ["orchestrator"]
    for msg in messages:
        for tc in getattr(msg, "tool_calls", []) or []:
            name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            if name.startswith("transfer_to_"):
                agent_name = name.replace("transfer_to_", "")
                if agent_name not in route:
                    route.append(agent_name)
    return route


def _extract_tools(messages: list) -> list[str]:
    tools = []
    for msg in messages:
        for tc in getattr(msg, "tool_calls", []) or []:
            name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            if name and not name.startswith("transfer_to_"):
                tools.append(name)
    return tools


def _count_handoffs(messages: list) -> int:
    count = 0
    for msg in messages:
        for tc in getattr(msg, "tool_calls", []) or []:
            name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            if name.startswith("transfer_to_"):
                count += 1
    return count


def _extract_text(msg) -> str:
    content = getattr(msg, "content", None)
    if not content:
        return ""
    if isinstance(content, list):
        return " ".join(
            block["text"] for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    return str(content).strip()


async def target_fn(inputs: dict) -> dict:
    telegram_id = user_id_to_telegram_id(inputs["user_id"])
    queries = inputs["queries"]
    case_id = inputs["case_id"]

    await _reset_case(telegram_id)
    settings.test_telegram_id = telegram_id  # safe: max_concurrency=1

    thread_id = f"eval_{case_id}_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    routes_per_turn, tools_per_turn, total_handoffs = [], [], 0
    final_response = ""

    for query in queries:
        turn_tools: list[str] = []
        async for _ns, chunk in _agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
            stream_mode="updates",
            subgraphs=True,
        ):
            for update in chunk.values():
                for msg in (update.get("messages", []) if isinstance(update, dict) else []):
                    for tc in getattr(msg, "tool_calls", []) or []:
                        name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                        if name and not name.startswith("transfer_"):
                            turn_tools.append(name)

        # aget_state() gives top-level messages for route + final response
        state = await _agent.aget_state(config)
        messages = state.values.get("messages", [])

        routes_per_turn.append(_extract_route(messages))
        tools_per_turn.append(turn_tools)
        total_handoffs += _count_handoffs(messages)

        for msg in reversed(messages):
            if getattr(msg, "type", "") == "ai":
                text = _extract_text(msg)
                if text:
                    final_response = text
                    break

    print(f"[runner] Case {case_id} done | route={routes_per_turn} | tools={tools_per_turn} | handoffs={total_handoffs}")

    return {
        "final_response": final_response,
        "routes_per_turn": routes_per_turn,
        "tools_used_flat": [t for turn in tools_per_turn for t in turn],
        "total_handoffs": total_handoffs,
    }


async def run_eval(n_repetitions: int = 1):
    await _init()
    print(f"[runner] Starting eval — dataset=H-agent_eval, N={n_repetitions}, max_concurrency=1")

    results = await aevaluate(
        target_fn,
        data="H-agent_eval",
        evaluators=[
            task_completion_evaluator,
            tool_correctness_evaluator,
            response_quality_evaluator,
            routing_accuracy,
            loop_detection,
        ],
        num_repetitions=n_repetitions,
        max_concurrency=1,
        experiment_prefix="H-agent_eval",
    )

    print("[runner] Eval complete — view at https://smith.langchain.com")
    await _pool.close()
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1, help="Number of repetitions (default=1)")
    args = parser.parse_args()
    asyncio.run(run_eval(n_repetitions=args.n))
