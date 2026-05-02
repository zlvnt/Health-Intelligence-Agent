INTERVENTION_CASES = [
    {
        "id": 10,
        "category": "intervention",
        "queries": [
            "log mie instan 3 bungkus dimakan barengan",
            "kebanyakan ya?",
            "gimana caranya biar gak ngulang?",
        ],
        "user_id": "eval_test_10",
        "expected_route_per_turn": [
            ["orchestrator", "tracking_agent"],
            ["orchestrator", "tracking_agent"],
            ["orchestrator", "intervention_agent"],
        ],
        "expected_route_options": None,
        "expected_tools_per_turn": [
            ["log_meal"],
            [],
            ["suggest_adjustment"],
        ],
        "rubric_d": (
            "Final response (Turn 3) (a) contains concrete suggestion to avoid mie instan "
            "repetition (e.g., meal prep, alternative protein, trigger awareness), (b) consistent "
            "with logged context from Turn 1 (references mie instan), (c) not generic "
            "'just eat healthy'. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 3,
        "source": "matrix",
        "notes": None,
    },
    {
        "id": 11,
        "category": "intervention",
        "queries": [
            "aku gak bisa diet udah seminggu",
            "mungkin karena stres kerjaan",
            "saran dong gimana cope-nya",
        ],
        "user_id": "eval_test_11",
        "expected_route_per_turn": [
            ["orchestrator", "intervention_agent"],
            ["orchestrator", "intervention_agent"],
            ["orchestrator", "intervention_agent"],
        ],
        "expected_route_options": None,
        "expected_tools_per_turn": [
            [],
            [],
            ["suggest_adjustment"],
        ],
        "rubric_d": (
            "Turn 3 response (a) acknowledges work stress as root cause (continuity from "
            "Turn 2 — context preservation), (b) provides concrete cope strategies "
            "(e.g., stress eating triggers, mindful eating, scheduled snacks), (c) does NOT "
            "give generic 'just relax' or 'get enough sleep' without context. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 3,
        "source": "real_logs",
        "notes": None,
    },
    {
        "id": 12,
        "category": "intervention",
        "queries": [
            "log boba 2 gelas hari ini",
            "kebiasaan banget aku tiap stres",
            "cara berhentinya susah",
        ],
        "user_id": "eval_test_12",
        "expected_route_per_turn": [
            ["orchestrator", "tracking_agent"],
            ["orchestrator", "tracking_agent", "intervention_agent"],
            ["orchestrator", "intervention_agent"],
        ],
        "expected_route_options": None,
        "expected_tools_per_turn": [
            ["log_meal"],
            ["handoff_to_intervention"],
            ["suggest_adjustment"],
        ],
        "rubric_d": (
            "Turn 3 response (a) acknowledges habitual stress eating + boba history "
            "(references Turn 1 context), (b) provides actionable substitution or gradual "
            "reduction plan (not abrupt 'stop drinking boba'), (c) empathetic tone — "
            "no shaming. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 2,
        "source": "matrix",
        "notes": "Tests handoff_to_intervention tool path (tracking → intervention).",
    },
]
