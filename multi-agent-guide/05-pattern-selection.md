# 5. Pattern Selection

The decision is not "should I use multi-agent or not". The decision is which pattern fits the workload. Single-agent is one option among several. Supervisor multi-agent is another. Skipping the comparison and defaulting to whatever the framework's README example shows is how projects end up with architectures that do not match their requirements.

## 5.1 The patterns to choose between

**Single agent.** One LLM, one prompt, one toolbox. Default for any task that does not have a specific reason to fan out. Cheapest, easiest to debug, lowest latency.

**Single agent + intent classifier.** A small fast model (Haiku, GPT-4o-mini) classifies user intent first. The intent maps to a code path that may invoke a domain LLM, a deterministic function, or a rule-based response. The classifier is one extra LLM call; the rest is regular code. Used when intent space is finite and the LLM is overkill for routing.

**Supervisor multi-agent.** This guide's main subject. One supervisor LLM, multiple specialist agents, handoff mechanism. Used when domain expertise is divergent enough that prompts cannot share, or when routing genuinely needs LLM judgment.

**Plan-and-execute.** A planner LLM generates a sequence of steps. An executor LLM (or several) runs each step. Used when the work is structured enough to plan up front and the plan benefits from explicit inspection or modification before execution. Common in agentic coding tools and research assistants.

**Hierarchical multi-agent.** Supervisors of supervisors. A top-level orchestrator routes between domain orchestrators, each of which routes to specialists. Used when the system is large enough that a single supervisor's prompt would be unmanageable. Rarely needed below 8–10 specialist agents.

**Peer-to-peer / debate.** Agents communicate directly without a central coordinator, often pushing against each other (debate) or building on each other's work (collaboration). Used in evaluation, red-teaming, and multi-perspective analysis. Adversarial by design.

## 5.2 Decision criteria

Five questions narrow the choice.

**1. Can routing be expressed as keyword matching or simple rules?**

If `meal_log` requests always contain food words, `account` requests always contain billing terms, and the categories are mutually exclusive, an LLM is overkill for routing. A classifier (or even regex) is faster, cheaper, and more consistent across model swaps.

If routing depends on subtle signals — tone, implied intent, multi-clause messages with mixed concerns — LLM judgment is the right tool.

**2. Are the sub-tasks independent or sequential?**

Independent sub-tasks (search five sources, analyze three documents, query four databases) benefit from parallelism. Multi-agent runs them concurrently; single-agent runs them one at a time. Wall-clock time difference is large.

Sequential sub-tasks (collect data → plan → track → adjust) do not benefit from multi-agent in the parallelism dimension. The pattern's value here is purely prompt isolation, which has to be weighed against the coordination tax.

**3. Does each role need different prompts, models, or knowledge bases?**

Legal review and medical review on the same document need different prompts (different tone, different jargon), possibly different models (specialized fine-tunes), and definitely different RAG corpora. Multi-agent maps to this naturally.

Roles that could share a prompt with a switch ("if billing, do X; if technical, do Y") do not need separate agents. The switch is what an intent classifier does, more efficiently.

**4. How much state needs to flow between agents?**

If agents work on disjoint slices of the request and their outputs combine at the end, state flow is minimal. Multi-agent works well.

If agents need to share rich state — user profile, prior decisions, accumulated context — every agent re-parsing that state from message history is fragile. Multi-agent works *despite* the framework here, not because of it. A typed shared store (database, structured object) reduces the friction.

**5. What is the latency and cost budget?**

A multi-agent turn at 4 LLM calls instead of 1 is roughly 4× the cost and 2-3× the latency. If the workload is high-volume customer chat, this matters. If the workload is a once-an-hour analysis, it does not.

## 5.3 A decision flow

Working from the decisions a project can answer:

```
Is the task a single coherent step?
├── Yes → Single agent
└── No, multiple steps:
        Are they independent / parallelizable?
        ├── Yes → Multi-agent (supervisor or plan-and-execute, depending on planning needs)
        └── No, sequential:
                Do steps need different prompts/models/knowledge?
                ├── Yes → Multi-agent (supervisor)
                └── No:
                        Is routing simple (keyword/pattern)?
                        ├── Yes → Single agent + intent classifier
                        └── No → Multi-agent (supervisor) — judgment-based routing
```

The flow biases toward simpler patterns. This is intentional. Multi-agent is correctly chosen when at least one node in the flow says "yes" to a multi-agent path. Defaulting to multi-agent because the framework supports it is the failure mode this section exists to prevent.

## 5.4 Examples

**Customer support bot for a SaaS product.** Categories: billing, technical, sales. Intent boundaries are clear. Most messages map cleanly to one category. → Single agent + intent classifier. The classifier picks the category, the domain LLM handles the conversation. Going multi-agent would add cost without solving a problem.

**Research assistant that synthesizes information from web search, academic papers, internal documents, and APIs.** Sources are independent. Each has its own retrieval logic and prompt. Final step is synthesis. → Multi-agent. Specialists handle each source in parallel; a synthesizer combines.

**Legal contract review.** Aspects: clause identification, risk assessment, citation lookup, comparison to template. Each aspect has different prompt structure and may use different models. → Multi-agent (supervisor) or plan-and-execute, depending on whether the aspects always run in the same order.

**Medical triage chatbot.** Categories: symptom intake, urgency assessment, escalation, general info. Some steps need to happen in sequence (intake before assessment). Routing has subtle dimensions (severity assessment is not a keyword match). → Multi-agent (supervisor), with explicit handoff between intake and assessment specialists.

**Habit tracker / fitness assistant.** Steps: collect user data, generate plan, log activity, adjust over time. Sequential. Each step has a clear tool that does the actual work. Routing is keyword-matchable on most messages. → Single agent + intent classifier. Splitting into specialists adds overhead without solving a real problem.

## 5.5 The migration path

Most projects do not need to commit to a pattern up front. Single agent + classifier is a good starting point. It runs the same tools as a multi-agent setup would, just under one prompt. If the prompt becomes unmanageable or specific failure modes (tool selection drift, persona bleed) appear, splitting one role out into a specialist is mechanical: extract the relevant tools and prompt section into a new agent, route to it for the relevant intent.

Going the other direction — collapsing a multi-agent setup back to single agent — is harder. State and prompt structure assume the split. The lesson: start simple, escalate when you have evidence that simpler is not enough.
