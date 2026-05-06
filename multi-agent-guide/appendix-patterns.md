# Appendix: Multi-Agent Pattern Variants

The main guide focuses on the supervisor pattern. This appendix covers the other common multi-agent patterns: what they are, when they fit, and how they differ. Useful when supervisor is not the right tool for the workload.

## A.1 Supervisor

The pattern this guide covers in depth. Recap for comparison.

```
       Supervisor
       ↓  ↓  ↓
   A1   A2   A3   ← specialists
```

A central LLM coordinator routes user requests to one of several specialists. Each specialist has a focused role and tool set. The coordinator does not call domain tools because its job is routing.

**When to use.** Workloads where intent is clear once classified, but the right way to handle each intent differs significantly enough to warrant separate prompts and tool sets. Most "customer service router" or "domain expert dispatcher" use cases.

**Trade-off.** Coordination tax (multiple LLM calls per turn). Best when classifications are stable and routing decisions are not the bottleneck.

## A.2 Plan-and-Execute

```
   User: "Build feature X"
        ↓
   Planner LLM
        ↓
   Plan: [step1, step2, step3, step4]
        ↓
   Executor LLM (or pool)
        ↓
   step1 ✓ → step2 ✓ → step3 ✓ → step4 ✓
```

A planner agent decomposes the request into an explicit, ordered sequence of steps. An executor (or pool of executors) then runs the steps. The plan exists as a first-class artifact: it can be inspected, edited, or replanned mid-execution.

**Difference from supervisor.** Supervisor decides routing one step at a time, reactively. Plan-and-execute decides the whole sequence up front, proactively. Supervisor is reactive; plan-and-execute is deliberative.

**When to use.**
- Tasks with multiple dependent sub-steps where the order matters
- Workloads where you want a human or another agent to review the plan before execution
- Long-running tasks where intermediate state needs to be tracked against an explicit goal

**Concrete example.** Agentic coding tools (Cursor's agent mode, GitHub Copilot Workspace, Devin). User says "add OAuth login". Planner produces: "1. Add dependencies → 2. Create OAuth handler → 3. Update routes → 4. Add tests". Executor implements each step, possibly with intermediate human approval.

**Trade-off.** Plan quality is a single point of failure. A bad plan cascades into bad execution. Replanning is possible but adds complexity. Best when the task is structured enough that planning has high signal.

## A.3 Hierarchical

```
              Top Supervisor
              ↓           ↓
        Sub-Sup A      Sub-Sup B
        ↓  ↓  ↓        ↓  ↓  ↓
       a1 a2 a3       b1 b2 b3
```

Supervisors of supervisors. The top-level coordinator routes to a sub-coordinator, which then routes to a specialist. Tree depth can be 3+ levels.

**When to use.**
- Specialist count exceeds what one supervisor can reason about effectively (typically past 8–10)
- Specialists naturally cluster into domains (e.g. all "billing" specialists, all "technical" specialists)
- Different domains need different supervisor prompts because routing logic differs per domain

**Concrete example.** A large enterprise customer service system. Top supervisor routes between billing-domain, technical-domain, and sales-domain. Within billing, sub-supervisor routes between invoices, refunds, payment methods, dispute handling. Each level adds context that the layer below assumes.

**Trade-off.** Each level adds an LLM call to the turn. A 3-level hierarchy costs at least 3 routing calls per turn before any specialist runs. Tax compounds. Worth the cost only when single-supervisor prompts have actually become unmaintainable.

## A.4 Peer-to-Peer

```
   Agent A ←──→ Agent B
      ↕            ↕
   Agent C ←──→ Agent D
```

No central coordinator. Agents communicate directly with each other, often pushing against each other (debate) or building on each other's work (collaboration). Termination is determined by consensus, iteration limit, or a shared judge.

**When to use.**
- Adversarial setup is the design (debate, red-team / blue-team, proof-by-contradiction)
- Iterative refinement where multiple perspectives improve the output (writer + critic + editor cycles)
- Workloads where no single agent has the authority to decide what is "done"

**Concrete example.** A code-review pipeline. Agent A reviews for security issues. Agent B reviews for performance. Agent C reviews for readability. They run independently and produce critiques. Agent D synthesizes the critiques into a final review. There is no supervisor deciding which critic gets called; all run, and the synthesizer decides what matters.

Another: debate simulators for evaluation. Agent A argues a position, Agent B argues the opposing position, both iterate. A judge agent (or human) scores at the end. The "router" doesn't exist; both agents always run.

**Trade-off.** Coordination is harder. Without a central decision-maker, deciding when to stop and how to combine outputs requires either explicit rules (max iterations, consensus thresholds) or another agent acting as a judge, at which point the system starts looking hierarchical anyway.

## A.5 Comparison

| Pattern | Coordinator | Decision style | Best fit |
|---|---|---|---|
| Supervisor | Central LLM | Reactive, per-turn | Domain dispatch with clear intents |
| Plan-and-execute | Planner LLM | Deliberative, up front | Structured multi-step tasks |
| Hierarchical | Tree of supervisors | Reactive, multi-level | Many specialists clustered into domains |
| Peer-to-peer | None (or judge) | Iterative / consensus | Adversarial or collaborative refinement |

A workload may also combine patterns. A plan-and-execute system whose executors are themselves supervisors, for instance. Or a peer-to-peer debate where each "agent" is internally a supervisor over its own specialists. Real systems are often layered.

## A.6 Choosing among them

The decision criteria from Section 5 (Pattern Selection) apply across all four patterns, with shifts of emphasis:

- **Routing complexity** — high routing complexity favors supervisor or hierarchical
- **Sub-task independence** — high parallelism favors peer-to-peer
- **Need for upfront planning** — high planning value favors plan-and-execute
- **Specialist count** — high count favors hierarchical
- **Adversarial design** — required favors peer-to-peer (the others cannot model it)

The default starting point is still single-agent. The default escalation path, when single-agent is not enough, is supervisor. The other patterns are specialized tools: reach for them when the workload's shape specifically calls for them.
