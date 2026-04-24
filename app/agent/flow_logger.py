"""Capture full agent execution flow to JSON logs for later audit."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage


def _extract_text(msg: Any) -> str:
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


async def run_and_log(agent: Any, user_input: str, config: dict, log_dir: Path) -> str:
    """Invoke agent via astream_events, write a JSON flow log, return final response."""
    start_time = datetime.now()
    calls: list[dict] = []
    tool_executions: list[dict] = []
    input_tokens = 0
    output_tokens = 0
    final_response = ""

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        version="v2",
    ):
        event_type = event.get("event")
        name = event.get("name", "")
        data = event.get("data", {})

        if event_type == "on_chat_model_end":
            output_raw = data.get("output")
            output = (
                output_raw[0]
                if isinstance(output_raw, list) and output_raw
                else output_raw
            )

            content_text = _extract_text(output) if output else ""
            tool_calls = []
            if output and getattr(output, "tool_calls", None):
                tool_calls = [
                    {"name": tc.get("name"), "args": tc.get("args")}
                    for tc in output.tool_calls
                ]

            usage = getattr(output, "usage_metadata", None) or {}
            in_tok = usage.get("input_tokens", 0)
            out_tok = usage.get("output_tokens", 0)
            input_tokens += in_tok
            output_tokens += out_tok

            calls.append(
                {
                    "call_number": len(calls) + 1,
                    "agent": name or "unknown",
                    "content": content_text,
                    "tool_calls": tool_calls,
                    "tokens": {"input": in_tok, "output": out_tok},
                }
            )

        elif event_type == "on_tool_end":
            tool_executions.append(
                {
                    "execution_number": len(tool_executions) + 1,
                    "tool": name,
                    "arguments": data.get("input", {}),
                    "result": str(data.get("output", ""))[:500],
                }
            )

        elif event_type == "on_chain_end" and name == "LangGraph":
            output = data.get("output", {})
            if isinstance(output, dict):
                messages = output.get("messages", [])
            elif isinstance(output, list):
                messages = output
            else:
                messages = []
            for msg in reversed(messages):
                if getattr(msg, "type", None) == "ai":
                    text = _extract_text(msg)
                    if text:
                        final_response = text
                        break

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    session_id = config.get("configurable", {}).get("thread_id", "unknown")

    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = start_time.strftime("%Y%m%d_%H%M%S_%f")[:-3]
    log_path = log_dir / f"{timestamp}_{session_id[:8]}.json"

    log_path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "timestamp": start_time.isoformat(),
                "user_input": user_input,
                "final_response": final_response,
                "summary": {
                    "total_calls": len(calls),
                    "total_tool_executions": len(tool_executions),
                    "total_input_tokens": input_tokens,
                    "total_output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "duration_seconds": round(duration, 2),
                },
                "calls": calls,
                "tool_executions": tool_executions,
            },
            indent=2,
            default=str,
        )
    )

    return final_response
