"""
Phase 4c — Metric E: loop detection.
Counts total handoffs across all turns. Fail if > threshold.
"""

HANDOFF_THRESHOLD = 3  # per case 9 spec: >3 handoffs = suspect loop


def _count_handoffs(messages: list) -> int:
    count = 0
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", []) or []
        for tc in tool_calls:
            name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            if name.startswith("transfer_to_"):
                count += 1
    return count


def loop_detection(inputs: dict, outputs: dict, reference_outputs: dict) -> dict | None:
    if "E" not in reference_outputs.get("applicable_metrics", ["A", "B", "C", "D", "E"]):
        return None

    total_handoffs = outputs.get("total_handoffs", 0)
    score = 1.0 if total_handoffs <= HANDOFF_THRESHOLD else 0.0
    return {
        "key": "no_loop",
        "score": score,
        "comment": f"total_handoffs={total_handoffs}, threshold={HANDOFF_THRESHOLD}",
    }
