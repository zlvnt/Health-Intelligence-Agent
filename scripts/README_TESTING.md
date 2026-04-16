# Agent Flow Testing

Scripts untuk audit dan testing multi-agent orchestration behavior.

## Files

### 1. `test_simple.py` ⭐ Start here
Quick test untuk liat berapa LLM calls dan basic flow.

**Usage:**
```bash
# Single scenario (default: "I ate 1 apple")
python scripts/test_simple.py

# Multiple scenarios
python scripts/test_simple.py multi
```

**Output:** Console logs showing call count per scenario.

---

### 2. `test_agent_flow.py` 📊 Detailed audit
Comprehensive audit dengan detailed logs (prompts, tools, tokens, cost).

**Usage:**
```bash
python scripts/test_agent_flow.py
```

**Output:**
- `test_results/YYYYMMDD_HHMMSS_scenario.json` - Raw data
- `test_results/YYYYMMDD_HHMMSS_scenario.md` - Readable report

**Audit data includes:**
- Each LLM call (agent, input prompt, tools, output)
- Each tool execution (name, args, result)
- Routing decisions
- Token usage & cost estimate
- Flow diagram

---

## Prerequisites

Make sure services are running:
```bash
docker-compose up -d  # PostgreSQL + Qdrant
```

Environment variables in `.env`:
```
ANTHROPIC_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/health_agent
CHECKPOINTER_DB_URL=postgresql://user:pass@localhost:5432/health_agent
QDRANT_URL=http://localhost:6333
```

---

## Test Scenarios

### Scenario 1: Simple Meal Log
**Input:** "I just ate 1 apple"
**Expected:**
- Orchestrator → Tracking
- Tracking: lookup_nutrition + log_meal
- Stop (no summary check)
- **Target: 3-5 LLM calls**

### Scenario 2: Meal + Summary
**Input:** "I ate 2 burgers and fries. How much today?"
**Expected:**
- Orchestrator → Tracking
- Tracking: lookup + log + get_daily_summary
- Orchestrator observes
- Maybe route to Intervention (if over budget)
- **Target: 5-8 LLM calls**

### Scenario 3: Summary Only
**Input:** "How many calories today?"
**Expected:**
- Orchestrator → Tracking
- Tracking: get_daily_summary
- Orchestrator observes
- Maybe Intervention
- **Target: 4-7 LLM calls**

### Scenario 4: Set Goal
**Input:** "Set my calorie goal to 2000"
**Expected:**
- Orchestrator → Tracking
- Tracking: set_calorie_goal
- Stop immediately
- **Target: 3 LLM calls**

---

## Analyzing Results

### Check Call Count
```bash
# Look for "Total LLM calls" in output
python scripts/test_simple.py multi | grep "LLM calls"
```

### Check Routing Logic
Open the generated `.md` file in `test_results/`:
- See flow diagram
- Check why orchestrator routed to each agent
- Verify stop triggers worked

### Check Token Usage
In the `.md` summary:
- Total tokens should be <15K for complex scenarios
- Simple scenarios should be <5K tokens
- Cost should be <$0.05 per scenario

---

## Common Issues

### Too Many Calls (>10)
**Symptoms:** Call count exceeds 10 for simple scenarios.

**Debug:**
1. Check `.md` report: which agent is being called multiple times?
2. Look for routing loops (Orchestrator → Agent A → Orchestrator → Agent A → ...)
3. Check if stop rules in `app/agent/prompts.py` are clear enough

**Fix:** Improve prompt stop instructions or lower `recursion_limit` in `app/agent/graph.py`

---

### Tool Called Unnecessarily
**Symptoms:** `get_daily_summary` called even for simple logging.

**Debug:**
1. Check tracking agent's tool calls in `.md` report
2. Look at tracking agent's reasoning (input messages)

**Fix:** Update `TRACKING_PROMPT` to be more explicit about when NOT to call tools

---

### Intervention Not Triggered
**Symptoms:** User over budget but no intervention.

**Debug:**
1. Check if `get_daily_summary` was called (observation requires this)
2. Look at orchestrator's observation logic in call logs

**Fix:** Verify observation rules in `ORCHESTRATOR_PROMPT`

---

## Performance Targets

| Metric | Simple | Complex |
|--------|--------|---------|
| LLM calls | 3-5 | 5-8 |
| Total tokens | <5K | <15K |
| Cost | <$0.02 | <$0.05 |
| Duration | <5s | <10s |

If exceeding these, optimize prompts or consider reducing agent count.
