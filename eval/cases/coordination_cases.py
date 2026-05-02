COORDINATION_CASES = [
    {
        "id": 13,
        "category": "coordination",
        "queries": [
            "umur 25, berat 70kg, sedentary, mau turun 5kg dalam 2 bulan — kasih plan diet"
        ],
        "user_id": "eval_test_13",
        "expected_route_per_turn": [
            ["orchestrator", "assessment_agent", "planning_agent"]
        ],
        "expected_route_options": None,
        "expected_tools_per_turn": [["collect_health_data", "create_health_plan"]],
        "rubric_d": (
            "Response (a) confirms assessment data was saved (age, weight, activity level, "
            "goal explicitly mentioned), (b) concrete diet plan tailored to user info — target "
            "~1500 kcal/day (deficit ~500 kcal from TDEE sedentary 70kg), (c) realistic for "
            "5kg/2 months goal, (d) info threading: planning agent must reference data that "
            "assessment just collected (not a generic plan). Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 1,
        "source": "matrix",
        "notes": (
            "Tier 1 — cross-specialist coordination dalam 1 turn, info threading critical. "
            "Data flow via context (LangGraph supervisor passes shared state), bukan DB persistence."
        ),
    },
    {
        "id": 14,
        "category": "coordination",
        "queries": ["aku log junk food terus, gimana?"],
        "user_id": "eval_test_14",
        "expected_route_per_turn": [
            ["orchestrator", "tracking_agent", "intervention_agent"]
        ],
        "expected_route_options": None,
        "expected_tools_per_turn": [["handoff_to_intervention", "suggest_adjustment"]],
        "rubric_d": (
            "Response (a) identifies junk food pattern via Tracking lookup (or acknowledges "
            "no data exists yet), (b) hands off to Intervention, (c) Intervention provides "
            "non-judgmental + actionable suggestion (e.g., gradual swap, identify trigger), "
            "(d) does NOT loop and offer to log a meal again (regression bug). Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 1,
        "source": "regression",
        "notes": (
            "Tests bahwa tracking_agent NGGAK loop offer log setelah handoff (bug regression). "
            "Critical bug check."
        ),
    },
]
