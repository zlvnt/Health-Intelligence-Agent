# 4. Common Pitfalls

The supervisor pattern produces a small set of failure modes that recur across projects. They are not bugs in the framework. They are inherent to how the pattern works, and most of the work after the skeleton is in place is defending against them.

## 4.1 Handoff loops

**What it looks like.** The trace shows `supervisor → specialist_A → supervisor → specialist_A → ...` cycling. Each iteration is a full LLM call. The conversation does not progress. Eventually a token limit, recursion limit, or rate limit halts the loop, and the user gets either an error or a confused partial response.

**Why it happens.** The supervisor sees a specialist's reply and decides the work is incomplete, so it routes back to the same specialist. The specialist sees the same context and produces a similar reply. The loop is stable: each side does what its prompt says.

A common trigger: the specialist asks the user a clarifying question instead of finalizing. The supervisor reads this as "the specialist did not finish" and routes again. The specialist is waiting for a user reply that never comes within this turn.

**Mitigation.**

A hard recursion limit at the graph level. LangGraph's `recursion_limit` config caps total node executions per turn:

```python
graph.invoke(state, config={"recursion_limit": 25})
```

This is a backstop, not a fix. The fix is in the supervisor prompt: a STOP rule that says once any specialist has replied in the current turn, the turn ends, regardless of whether the reply contains a question.

```
STOP RULE: Once any specialist has produced a reply in the current turn,
do not route to another specialist. Forward the reply to the user and stop.
A question from a specialist is a question to the user, not a request for more routing.
```

Cross-specialist handoffs (specialist A to specialist B directly) require their own loop guard: each handoff tool can be called at most once per turn, enforced in code if the framework allows hooks, otherwise in the prompt.

## 4.2 Prompt rule accumulation

**What it looks like.** The supervisor prompt grows from 200 words to 800 over the course of a project. New rules get added each time a behavior is observed in production: STOP rules, anti-fabrication rules, output formatting rules, language rules, ambiguous-input rules, anti-overstep rules. Each rule fixes one observed failure. The prompt becomes hard to reason about as a whole.

**Why it happens.** Multi-agent failure modes do not come with neat names. Each one looks like a unique bug the first time you see it. The natural reaction is to add a prompt clause that prevents that specific case. Over time, clauses interact in ways that were not anticipated.

The deeper cause: the supervisor is being asked to enforce policy with natural-language rules. Some kinds of policy are easier to enforce in code than in prompts. Routing rules that match keywords are an example — easier to implement as a classifier or regex than to express as prompt instructions the LLM follows reliably.

**Detection signal.** The prompt has more than three CRITICAL or ABSOLUTE markers. Rules contradict each other in edge cases. Different LLMs interpret the same prompt and produce different routing.

**Mitigation.**

Promote frequently-violated rules out of the prompt and into code. If the supervisor keeps routing to the wrong specialist for "log meal" requests, replace LLM routing for that intent with a keyword classifier. The supervisor becomes the fallback for ambiguous cases.

For rules that genuinely need to stay in the prompt, group them into named blocks and keep the count small. A flat list of fifteen rules is harder to follow than four blocks of three to four rules each.

## 4.3 Implicit state via conversation history

**What it looks like.** A specialist asks for information the user already provided. Or the specialist generates a generic output despite specific user data being present in the message history. Or two specialists disagree about a value because they parsed the same message differently.

**Why it happens.** Multi-agent state is the conversation history. Specialists do not share a typed object — they share a stream of messages, and each one parses what it needs out of free-form text. Parsing is LLM inference, with all the variance that implies.

A concrete pattern: the planning specialist's prompt says "base the plan on the assessment data." The model interprets this literally — assessment data means a structured summary from the assessment specialist. If the assessment ran but only persisted data via tool calls (no summary text), or if assessment was skipped entirely and the user provided the data directly in their message, the planner does not find what it expects and produces a generic template.

**Mitigation.**

Make state explicit. Persist user data through tools that write to a typed store (database, structured file). Specialists read from the store via tools, not by parsing message history.

```python
@tool
def get_user_profile(user_id: int) -> dict:
    """Return the user's stored profile: age, weight, goals, preferences."""
    return db.fetch_profile(user_id)
```

The planner now has a deterministic source of profile data. The conversation history is for conversation context, not for cross-agent communication.

This shifts complexity from prompt engineering to schema design, which is the better tradeoff. Schema bugs are easier to debug than prompt-interpretation drift.

## 4.4 Anti-fabrication and over-step

**What it looks like.** The supervisor, instead of routing to the assessment specialist, asks the user for their age and weight directly. The user replies. The supervisor then claims the data has been saved, even though no `collect_data` tool was ever called. The data exists nowhere.

A related variant: the assessment specialist collects data and, instead of stopping, also generates a full plan that the planner specialist was supposed to produce. The plan is not stored through `create_plan` because the planner never ran.

**Why it happens.** The supervisor and specialists are generative LLMs. They are trained to be helpful. When a user asks for a plan, the supervisor's model wants to provide one. If the next obvious step is "ask for age and weight", the model will ask, even though that is the assessment specialist's job. If the assessment specialist has data, the model will write a plan, even though the planner is supposed to.

**Mitigation.**

Explicit anti-overstep rules in each prompt. The supervisor's rule:

```
ANTI-OVERSTEP: Do not ask onboarding questions yourself (age, weight, goals,
preferences). Route to the assessment specialist instead.
```

The assessment specialist's rule:

```
SCOPE: Your only job is to collect data via the collect_data tool and summarize
what was collected. Do not generate plans, recommendations, or advice.
```

These rules work imperfectly. Different models follow them with different fidelity. The same prompt can produce conforming behavior on Haiku and over-stepping on a smaller model.

A more durable defense: tool design. If the only way to "save" data is to call `collect_data`, and the specialist's prompt forbids replying without calling tools, the model has fewer paths to the over-step failure mode.

## 4.5 Tool-use reliability is model-dependent

**What it looks like.** The supervisor decides correctly to route to a specialist — the reasoning trace shows "I should call transfer_to_assessment" — but no tool call is emitted. The supervisor replies with text instead. Or the assessment specialist correctly identifies four data points to save but only emits one `collect_data` call. The remaining three are mentioned in the response text but never persisted.

**Why it happens.** Tool calling is a separate capability from text generation. Some models, especially smaller or older ones, have a noticeable gap between deciding to use a tool and actually emitting the structured tool call. Reasoning models can produce long chain-of-thought that concludes "I will call X" and then skip emission.

**Detection.** Compare the tool calls emitted to what the prompt and reasoning suggest should happen. Cross-model testing on the same prompt and input. If model A emits the tool call and model B does not, the issue is in the model, not the prompt.

**Mitigation.**

If the budget allows, use a tool-reliable model for any agent whose value depends on tool emission. Anthropic's Claude family and OpenAI's GPT-4-class models are reliable in this dimension at the time of writing. Smaller models trade reliability for cost.

If the budget does not allow that, design tools so the model gets immediate feedback when it skips. A `collect_data` tool that returns "data not saved" if called with empty arguments is more useful than one that silently accepts anything. The model's next reasoning step has something to react to.

## 4.6 The supervisor's finalize step

**What it looks like.** A turn that should be one routing decision and one specialist reply ends up with three or four LLM calls. The supervisor runs once to route, the specialist runs (possibly with multiple tool calls), and then the supervisor runs again to "finalize" — wrap or forward the specialist's reply. Sometimes the supervisor runs a third time after that.

**Why it happens.** This is how the supervisor pattern is wired. After a specialist completes, control returns to the supervisor. The supervisor's prompt includes routing logic, so it evaluates whether more routing is needed. Even a STOP rule still requires an LLM call to read the rule and decide to stop.

The cost is real: the finalize step typically runs a full prompt and produces a non-trivial output. For a supervisor running on the same model as the specialists, this is ~1× the specialist cost again.

**Mitigation.**

Use a smaller model for the supervisor. Routing is cheaper reasoning than content generation. A Haiku-class supervisor with a Sonnet-class specialist is a common production split.

Some frameworks support skipping the finalize step entirely (return the specialist's reply directly). Check whether yours does. The tradeoff is losing the supervisor's ability to normalize formatting, enforce language rules, or catch anti-fabrication violations in the specialist's output.

Prompt caching helps for the part of the cost that is fixed: the supervisor's system prompt and persistent context. Anthropic and OpenAI both offer caching. A 90% discount on the static portion of supervisor calls is meaningful when the supervisor runs twice per turn.
