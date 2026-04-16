"""
Simple agent flow test with basic logging.

Easier to run and understand than test_agent_flow.py.
Just runs a single scenario and prints the flow.
"""

import asyncio
import json
from datetime import datetime

from langchain_core.messages import HumanMessage

from app.agent.graph import create_agent


async def test_simple_scenario():
    """Run a simple test and print the flow."""
    print("\n" + "=" * 60)
    print("SIMPLE AGENT FLOW TEST")
    print("=" * 60 + "\n")

    # Create agent
    print("Creating agent...")
    agent = await create_agent()

    # Test scenario
    user_input = "I just ate 1 apple"
    user_id = "test_user_simple"

    print(f"User input: {user_input}\n")
    print("Running agent...\n")
    print("-" * 60)

    # Run agent
    config = {"configurable": {"thread_id": user_id}}
    call_count = 0

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=user_input)]}, config=config, version="v2"
        ):
            event_type = event.get("event")
            name = event.get("name", "")
            data = event.get("data", {})

            # Track LLM calls
            if event_type == "on_chat_model_end":
                call_count += 1
                output = data.get("output", {})

                # Check for tool calls
                tool_calls = []
                if hasattr(output, "tool_calls") and output.tool_calls:
                    tool_calls = [tc["name"] for tc in output.tool_calls]

                content = output.content if hasattr(output, "content") else ""
                content_preview = content[:100] if content else "[tool calls only]"

                print(f"Call {call_count}: {name}")
                if tool_calls:
                    print(f"  → Tools: {', '.join(tool_calls)}")
                else:
                    print(f"  → Response: {content_preview}")
                print()

            # Track tool executions
            elif event_type == "on_tool_end":
                tool_name = name
                print(f"  ✓ Tool executed: {tool_name}")

        # Get final response
        final_state = await agent.aget_state(config)
        final_messages = final_state.values.get("messages", [])
        final_response = final_messages[-1].content if final_messages else "No response"

        print("-" * 60)
        print(f"\nTotal LLM calls: {call_count}")
        print(f"\nFinal response:")
        print(f"{final_response}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


async def test_multiple_scenarios():
    """Run multiple scenarios with different complexities."""
    scenarios = [
        ("Simple log", "I ate 1 apple"),
        ("With summary", "I ate 2 burgers. How much today?"),
        ("Set goal", "Set my calorie goal to 2000"),
    ]

    agent = await create_agent()

    for i, (name, user_input) in enumerate(scenarios, 1):
        print(f"\n{'=' * 60}")
        print(f"Scenario {i}: {name}")
        print(f"Input: {user_input}")
        print("=" * 60)

        config = {"configurable": {"thread_id": f"test_{i}"}}
        call_count = 0

        try:
            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=user_input)]}, config=config, version="v2"
            ):
                if event.get("event") == "on_chat_model_end":
                    call_count += 1

            print(f"✓ Completed in {call_count} LLM calls")

        except Exception as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(0.5)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "multi":
        asyncio.run(test_multiple_scenarios())
    else:
        asyncio.run(test_simple_scenario())
