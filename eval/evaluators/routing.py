"""
Phase 4b — Metric B: routing accuracy.
Parses agent handoffs from LangGraph messages and compares to expected route.
"""


def _extract_route_from_messages(messages: list) -> list[str]:
    """
    Parse handoff chain from LangGraph ainvoke() messages.
    Handoffs appear as tool_calls with name 'transfer_to_<agent>'.
    Always starts with 'orchestrator'.
    """
    route = ["orchestrator"]
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", []) or []
        for tc in tool_calls:
            name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            if name.startswith("transfer_to_"):
                agent_name = name.replace("transfer_to_", "")
                if agent_name not in route:
                    route.append(agent_name)
    return route


def routing_accuracy(inputs: dict, outputs: dict, reference_outputs: dict) -> dict | None:
    if "B" not in reference_outputs.get("applicable_metrics", ["A", "B", "C", "D", "E"]):
        return None

    # Multi-turn: evaluate per turn, score = fraction of turns correct
    routes_per_turn = outputs.get("routes_per_turn", [])
    expected_per_turn = reference_outputs.get("expected_route_per_turn")
    expected_options = reference_outputs.get("expected_route_options")

    if not routes_per_turn:
        return {"key": "routing_accuracy", "score": 0.0, "comment": "No route data captured"}

    n_turns = len(routes_per_turn)
    correct = 0

    for i, actual_route in enumerate(routes_per_turn):
        if expected_per_turn is not None:
            expected = expected_per_turn[i] if i < len(expected_per_turn) else []
            if actual_route == expected:
                correct += 1
            comment_detail = f"turn {i+1}: actual={actual_route}, expected={expected}"
        elif expected_options is not None:
            # Ambiguous case — any option is acceptable
            turn_options = expected_options[i] if i < len(expected_options) else []
            if actual_route in turn_options:
                correct += 1
            comment_detail = f"turn {i+1}: actual={actual_route}, options={turn_options}"
        else:
            correct += 1  # No expectation defined — pass

    score = correct / n_turns if n_turns > 0 else 0.0
    return {
        "key": "routing_accuracy",
        "score": score,
        "comment": f"{correct}/{n_turns} turns routed correctly",
    }
