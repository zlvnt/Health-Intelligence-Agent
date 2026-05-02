ROUTING_CASES = [
    {
        "id": 5,
        "category": "routing",
        "queries": ["kasih saran diet turun 5kg dalam 2 bulan"],
        "user_id": "eval_test_5",
        "expected_route_per_turn": [["orchestrator", "planning_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["create_health_plan"]],
        "rubric_d": (
            "Response includes (a) concrete diet plan (daily calorie target, food types, "
            "optional exercise frequency), (b) realistic for 5kg/2 months goal (deficit "
            "~600-700 kcal/day), (c) mentions the plan was saved. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 4,
        "source": "matrix",
        "notes": None,
    },
    {
        "id": 6,
        "category": "routing",
        "queries": ["aku gagal diet udah 3 hari makan junk food"],
        "user_id": "eval_test_6",
        "expected_route_per_turn": [["orchestrator", "intervention_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["suggest_adjustment"]],
        "rubric_d": (
            "Response (a) shows empathy — acknowledges struggle without being judgmental, "
            "(b) identifies root cause or pattern, (c) provides actionable adjustment suggestion "
            "(not generic 'just stop eating junk food'). Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 4,
        "source": "matrix",
        "notes": None,
    },
    {
        "id": 7,
        "category": "routing",
        "queries": ["halo aku baru, mau mulai tracking"],
        "user_id": "eval_test_7",
        "expected_route_per_turn": [["orchestrator", "assessment_agent"]],
        "expected_route_options": None,
        "expected_tools_per_turn": [["collect_health_data"]],
        "rubric_d": (
            "Response (a) friendly greeting, (b) starts asking for basic info "
            "(age/weight/goal/activity level), (c) does NOT immediately ask user to log meals "
            "before basic data is collected. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 4,
        "source": "matrix",
        "notes": None,
    },
    {
        "id": 8,
        "category": "routing",
        "queries": ["tadi makan banyak banget"],
        "user_id": "eval_test_8",
        "expected_route_per_turn": None,
        "expected_route_options": [
            [["orchestrator", "tracking_agent"]],
            [["orchestrator"]],
            [["orchestrator", "intervention_agent"]],
        ],
        "expected_tools_per_turn": [[]],
        "rubric_d": (
            "Response (a) asks for clarification (what was eaten, when, how much) OR offers to "
            "log meal OR shows light empathy, (b) does NOT push assessment data collection "
            "(age/weight/etc.) — regression bug, (c) does NOT immediately lecture on nutrition "
            "without context. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 2,
        "source": "regression",
        "notes": "Regression dari bug 'assessment terlalu persistent'. Failure = assessment_agent dipanggil.",
    },
    {
        "id": 9,
        "category": "routing",
        "queries": ["aku makan banyak tadi, bingung mau diet apa, terus aku log apa ya?"],
        "user_id": "eval_test_9",
        "expected_route_per_turn": None,
        "expected_route_options": [
            [["orchestrator", "tracking_agent"]],
            [["orchestrator", "planning_agent"]],
            [["orchestrator", "tracking_agent", "planning_agent"]],
        ],
        "expected_tools_per_turn": [[]],
        "rubric_d": (
            "Response (a) addresses at least 1 sub-question clearly (does not ignore all), "
            "(b) does not loop between agents (max 2 handoffs total), (c) does not hang, "
            "error, or return empty. Response in Indonesian."
        ),
        "applicable_metrics": ["A", "B", "C", "D", "E"],
        "difficulty_tier": 1,
        "source": "adversarial",
        "notes": "Dim E (loop detection) primary metric. Threshold handoff = 3 (di atas itu = fail).",
    },
]
