RAG_CASES = [
    {
        "id": 15,
        "category": "rag_routing",
        "queries": ["berapa kalori tempe goreng?"],
        "user_id": "eval_test_15",
        "expected_route_per_turn": [["orchestrator", "tracking_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["nutrition_tool"]],
        "rubric_d": None,
        "applicable_metrics": ["B", "C", "F", "G"],
        "difficulty_tier": 4,
        "source": "matrix",
        "notes": (
            "Cuma test routing + tool selection + cost/latency. "
            "RAG faithfulness/precision butuh evaluator dedicated (Phase out of scope)."
        ),
    },
]
