LOGGING_CASES = [
    {
        "id": 1,
        "category": "logging",
        "queries": ["log nasi goreng 1 porsi tadi pagi"],
        "user_id": "eval_test_1",
        "expected_route_per_turn": [["orchestrator", "tracking_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["log_meal"]],
        "rubric_d": (
            "Response confirms 'nasi goreng' was logged, mentions calorie estimate "
            "in a reasonable range (300-700 kcal for 1 portion), and is written in "
            "Indonesian (matching user's language)."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 4,
        "source": "real_logs",
        "notes": None,
    },
    {
        "id": 2,
        "category": "logging",
        "queries": ["ganti nasi goreng tadi jadi mie ayam"],
        "user_id": "eval_test_2",
        "expected_route_per_turn": [["orchestrator", "tracking_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["log_meal"]],
        "rubric_d": (
            "Response either (a) confirms 'mie ayam' was logged with calorie estimate, "
            "OR (b) acknowledges that edit feature is unavailable and suggests a workaround. "
            "Response MUST NOT falsely claim it successfully edited/deleted the previous entry "
            "(anti-fabrication). Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 4,
        "source": "real_logs",
        "notes": None,
    },
    {
        "id": 3,
        "category": "logging",
        "queries": ["hapus log nasi goreng tadi"],
        "user_id": "eval_test_3",
        "expected_route_per_turn": [["orchestrator", "tracking_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [[]],
        "rubric_d": (
            "Response acknowledges that delete feature is unavailable, OR suggests a workaround "
            "(e.g., ignore the entry, or log a counter-adjustment). Response MUST NOT falsely "
            "claim the entry was deleted (anti-fabrication). Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 4,
        "source": "matrix",
        "notes": "Critical anti-fabrication test. Score A=fail if agent claims 'sudah dihapus'.",
    },
    {
        "id": 4,
        "category": "logging",
        "queries": ["apa yang aku makan kemarin?"],
        "user_id": "eval_test_4",
        "expected_route_per_turn": [["orchestrator", "tracking_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["get_meal_history"]],
        "rubric_d": (
            "Response displays a list of meals from the previous day with calorie per item, "
            "OR acknowledges that no tracking data exists yet. MUST NOT fabricate fake meal "
            "entries (anti-fabrication). Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 3,
        "source": "real_logs",
        "notes": None,
    },
]
