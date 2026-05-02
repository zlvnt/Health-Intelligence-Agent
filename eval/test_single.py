"""
Quick integration test — run 1 case through target_fn and evaluators B, E.
Usage: python -m eval.test_single
"""
import asyncio

from dotenv import load_dotenv
load_dotenv()

import eval.runner as runner
from eval.runner import _init, target_fn
from eval.evaluators.routing import routing_accuracy
from eval.evaluators.loop_detection import loop_detection
from eval.cases.logging_cases import LOGGING_CASES


async def main():
    await _init()

    case = LOGGING_CASES[0]  # Case 1 — log nasi goreng
    inputs = {
        "case_id": case["id"],
        "queries": case["queries"],
        "user_id": case["user_id"],
        "category": case["category"],
        "difficulty_tier": case["difficulty_tier"],
    }
    reference_outputs = {
        "expected_route_per_turn": case["expected_route_per_turn"],
        "expected_route_options": case["expected_route_options"],
        "expected_tools_per_turn": case["expected_tools_per_turn"],
        "rubric_d": case["rubric_d"],
        "applicable_metrics": case["applicable_metrics"],
    }

    print(f"[test] Running case {case['id']}: {case['queries'][0]}")
    outputs = await target_fn(inputs)

    print(f"\n[test] outputs:")
    print(f"  final_response:   {outputs['final_response'][:120]}")
    print(f"  routes_per_turn:  {outputs['routes_per_turn']}")
    print(f"  tools_used_flat:  {outputs['tools_used_flat']}")
    print(f"  total_handoffs:   {outputs['total_handoffs']}")

    b = routing_accuracy(inputs, outputs, reference_outputs)
    e = loop_detection(inputs, outputs, reference_outputs)
    print(f"\n[test] B routing_accuracy: {b}")
    print(f"[test] E loop_detection:   {e}")

    await runner._pool.close()


if __name__ == "__main__":
    asyncio.run(main())
