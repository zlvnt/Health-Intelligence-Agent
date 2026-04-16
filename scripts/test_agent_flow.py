"""
Agent flow testing script with detailed logging.

This script tests the multi-agent orchestration and logs:
- Each LLM call (agent, prompt, tools, output, tokens)
- Each tool execution (name, args, result)
- Routing decisions and stop triggers
- Total calls, tokens, and cost

Output: JSON (raw data) + Markdown (readable report)
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.graph import create_agent
from app.config import settings


class AgentFlowAuditor:
    """Captures detailed agent execution flow for audit."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []
        self.tool_executions: list[dict[str, Any]] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = None
        self.end_time = None

    def log_llm_call(
        self,
        agent_name: str,
        input_messages: list,
        tools: list[str],
        output: dict,
        tokens: dict,
    ):
        """Log a single LLM call."""
        self.calls.append(
            {
                "call_number": len(self.calls) + 1,
                "agent": agent_name,
                "input_messages": [self._serialize_message(m) for m in input_messages],
                "tools_available": tools,
                "output": output,
                "tokens": tokens,
            }
        )
        self.total_input_tokens += tokens.get("input", 0)
        self.total_output_tokens += tokens.get("output", 0)

    def log_tool_execution(self, tool_name: str, args: dict, result: Any):
        """Log a tool execution."""
        self.tool_executions.append(
            {
                "execution_number": len(self.tool_executions) + 1,
                "tool": tool_name,
                "arguments": args,
                "result": str(result)[:500],  # Truncate long results
            }
        )

    def _serialize_message(self, message) -> dict:
        """Serialize LangChain message to dict."""
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            tool_calls = []
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_calls = [
                    {"name": tc.get("name"), "args": tc.get("args")} for tc in message.tool_calls
                ]
            return {"role": "assistant", "content": content, "tool_calls": tool_calls}
        elif isinstance(message, ToolMessage):
            return {"role": "tool", "content": message.content, "tool_call_id": message.tool_call_id}
        else:
            return {"role": "unknown", "content": str(message)}

    def get_summary(self) -> dict:
        """Get audit summary."""
        duration = (
            (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        )

        # Estimate cost (Claude Sonnet 4: $3 input / $15 output per 1M tokens)
        input_cost = (self.total_input_tokens / 1_000_000) * 3
        output_cost = (self.total_output_tokens / 1_000_000) * 15
        total_cost = input_cost + output_cost

        return {
            "total_llm_calls": len(self.calls),
            "total_tool_executions": len(self.tool_executions),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "duration_seconds": round(duration, 2),
        }

    def export_json(self, filepath: Path):
        """Export audit data as JSON."""
        data = {
            "summary": self.get_summary(),
            "calls": self.calls,
            "tool_executions": self.tool_executions,
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def export_markdown(self, filepath: Path, scenario: str, user_input: str, final_output: str):
        """Export audit report as Markdown."""
        summary = self.get_summary()

        md = f"""# Agent Flow Audit Report

**Scenario:** {scenario}
**Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Test Input
```
{user_input}
```

## Summary
- **Total LLM Calls:** {summary['total_llm_calls']}
- **Total Tool Executions:** {summary['total_tool_executions']}
- **Total Tokens:** {summary['total_tokens']:,} (input: {summary['total_input_tokens']:,}, output: {summary['total_output_tokens']:,})
- **Estimated Cost:** ${summary['estimated_cost_usd']}
- **Duration:** {summary['duration_seconds']}s

## Flow Diagram
```
"""
        # Generate flow diagram
        for i, call in enumerate(self.calls, 1):
            agent = call["agent"]
            tools = ", ".join(call.get("tools_available", []))
            md += f"{i}. {agent}\n"
            if call["output"].get("tool_calls"):
                for tc in call["output"]["tool_calls"]:
                    md += f"   → Tool: {tc['name']}({tc['args']})\n"
            else:
                content = call["output"].get("content", "")[:100]
                md += f"   → Response: {content}...\n"

        md += "```\n\n"

        # Detailed call logs
        md += "## Detailed Call Logs\n\n"
        for call in self.calls:
            md += f"### Call {call['call_number']}: {call['agent']}\n\n"
            md += f"**Tools Available:** {', '.join(call['tools_available']) or 'None'}\n\n"

            # Input messages
            md += "**Input Messages:**\n"
            for msg in call["input_messages"][-3:]:  # Show last 3 messages
                role = msg["role"]
                content = msg["content"][:200]
                md += f"- **{role.title()}:** {content}...\n"
            md += "\n"

            # Output
            md += "**Output:**\n"
            if call["output"].get("tool_calls"):
                for tc in call["output"]["tool_calls"]:
                    md += f"- Tool Call: `{tc['name']}({json.dumps(tc['args'])})`\n"
            else:
                content = call["output"].get("content", "")
                md += f"```\n{content}\n```\n"
            md += "\n"

            # Tokens
            tokens = call["tokens"]
            md += f"**Tokens:** {tokens.get('input', 0)} input, {tokens.get('output', 0)} output\n\n"
            md += "---\n\n"

        # Tool executions
        if self.tool_executions:
            md += "## Tool Executions\n\n"
            for tool_exec in self.tool_executions:
                md += f"### Execution {tool_exec['execution_number']}: {tool_exec['tool']}\n"
                md += f"**Arguments:** `{json.dumps(tool_exec['arguments'])}`\n\n"
                md += f"**Result:**\n```\n{tool_exec['result']}\n```\n\n"
                md += "---\n\n"

        # Final output
        md += "## Final Output to User\n"
        md += f"```\n{final_output}\n```\n"

        with open(filepath, "w") as f:
            f.write(md)


async def run_test_scenario(scenario_name: str, user_input: str, user_id: str = "test_user_001"):
    """Run a test scenario and capture detailed logs."""
    print(f"\n{'='*60}")
    print(f"Running scenario: {scenario_name}")
    print(f"User input: {user_input}")
    print(f"{'='*60}\n")

    # Create auditor
    auditor = AgentFlowAuditor()
    auditor.start_time = datetime.now()

    # Create agent
    agent = await create_agent()

    # Mock token counting (since we don't have direct access to usage)
    # In real implementation, you'd intercept LLM calls to get actual tokens
    # For now, we'll estimate based on message lengths
    def estimate_tokens(text: str) -> int:
        """Rough estimate: 1 token ≈ 4 characters."""
        return len(text) // 4

    # Run agent with streaming to capture intermediate steps
    config = {"configurable": {"thread_id": user_id}}

    try:
        final_response = None
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=user_input)]}, config=config, version="v2"
        ):
            event_type = event.get("event")
            name = event.get("name", "")
            data = event.get("data", {})

            # Log LLM calls
            if event_type == "on_chat_model_stream" and "chunk" in data:
                # This is a streaming chunk from LLM
                pass  # We'll log the final message

            elif event_type == "on_chat_model_end":
                # LLM call completed
                agent_name = name or "unknown"
                input_msgs = data.get("input", {}).get("messages", [])
                output = data.get("output", {})

                # Extract tool calls if any
                output_content = output.content if hasattr(output, "content") else ""
                tool_calls = []
                if hasattr(output, "tool_calls") and output.tool_calls:
                    tool_calls = [{"name": tc["name"], "args": tc["args"]} for tc in output.tool_calls]

                # Estimate tokens
                input_text = " ".join([str(m.content) for m in input_msgs])
                output_text = str(output_content) + str(tool_calls)
                tokens = {
                    "input": estimate_tokens(input_text),
                    "output": estimate_tokens(output_text),
                }

                # Log call
                auditor.log_llm_call(
                    agent_name=agent_name,
                    input_messages=input_msgs,
                    tools=[],  # TODO: extract from agent config
                    output={"content": output_content, "tool_calls": tool_calls},
                    tokens=tokens,
                )

            # Log tool executions
            elif event_type == "on_tool_end":
                tool_name = name
                tool_input = data.get("input", {})
                tool_output = data.get("output", "")
                auditor.log_tool_execution(tool_name, tool_input, tool_output)

        # Get final state
        final_state = await agent.aget_state(config)
        final_messages = final_state.values.get("messages", [])
        final_response = final_messages[-1].content if final_messages else "No response"

    except Exception as e:
        final_response = f"ERROR: {str(e)}"
        print(f"❌ Error during execution: {e}")

    auditor.end_time = datetime.now()

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)

    json_path = results_dir / f"{timestamp}_{scenario_name}.json"
    md_path = results_dir / f"{timestamp}_{scenario_name}.md"

    auditor.export_json(json_path)
    auditor.export_markdown(md_path, scenario_name, user_input, final_response)

    # Print summary
    summary = auditor.get_summary()
    print(f"\n✅ Test complete!")
    print(f"   LLM Calls: {summary['total_llm_calls']}")
    print(f"   Tool Executions: {summary['total_tool_executions']}")
    print(f"   Tokens: {summary['total_tokens']:,}")
    print(f"   Cost: ${summary['estimated_cost_usd']}")
    print(f"\n📄 Results saved:")
    print(f"   JSON: {json_path}")
    print(f"   MD:   {md_path}")

    return auditor


async def main():
    """Run all test scenarios."""
    scenarios = [
        {
            "name": "simple_meal_log",
            "input": "I just ate 1 apple",
            "description": "Simple meal logging without summary check",
        },
        {
            "name": "meal_with_summary",
            "input": "I ate 2 burgers and a large fries. How much have I eaten today?",
            "description": "Meal logging + summary check (should trigger observation)",
        },
        {
            "name": "check_summary_only",
            "input": "How many calories have I eaten today?",
            "description": "Check daily summary (may trigger intervention if over budget)",
        },
        {
            "name": "set_goal",
            "input": "Set my daily calorie goal to 2000 kcal",
            "description": "Simple goal setting",
        },
    ]

    print("\n" + "=" * 60)
    print("AGENT FLOW AUDIT TEST SUITE")
    print("=" * 60)

    for scenario in scenarios:
        await run_test_scenario(scenario["name"], scenario["input"])
        await asyncio.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
