from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_handoff_tool, create_supervisor

from app.agent.model import create_llm
from app.agent.prompts import (
    ASSESSMENT_PROMPT,
    INTERVENTION_PROMPT,
    ORCHESTRATOR_PROMPT,
    PLANNING_PROMPT,
    TRACKING_PROMPT,
)
from app.agent.tools import (
    collect_health_data,
    create_health_plan,
    get_daily_summary,
    get_meal_history,
    log_meal,
    set_calorie_goal,
    suggest_adjustment,
)
from app.config import settings
from app.rag.nutrition import create_nutrition_tool

llm = create_llm()  # Uses provider from settings.model_provider


async def create_agent():
    # TODO: Fix checkpointer initialization
    # For now, skip checkpointer (no conversation persistence)
    checkpointer = None

    nutrition_tool = create_nutrition_tool()

    # Handoff tool so tracking_agent can escalate to intervention_agent directly
    handoff_to_intervention = create_handoff_tool(
        agent_name="intervention_agent",
        description="Escalate to intervention_agent when calorie goal is significantly exceeded or under-met.",
    )

    # Worker agents
    assessment_agent = create_react_agent(
        model=llm,
        tools=[collect_health_data],
        name="assessment_agent",
        prompt=ASSESSMENT_PROMPT,
    )

    planning_agent = create_react_agent(
        model=llm,
        tools=[create_health_plan],
        name="planning_agent",
        prompt=PLANNING_PROMPT,
    )

    tracking_agent = create_react_agent(
        model=llm,
        tools=[
            log_meal,
            get_daily_summary,
            get_meal_history,
            set_calorie_goal,
            nutrition_tool,
            handoff_to_intervention,
        ],
        name="tracking_agent",
        prompt=TRACKING_PROMPT,
    )

    intervention_agent = create_react_agent(
        model=llm,
        tools=[suggest_adjustment],
        name="intervention_agent",
        prompt=INTERVENTION_PROMPT,
    )

    # Supervisor orchestrator
    workflow = create_supervisor(
        agents=[assessment_agent, planning_agent, tracking_agent, intervention_agent],
        model=llm,
        prompt=ORCHESTRATOR_PROMPT,
        output_mode="last_message",
    )

    agent = workflow.compile(checkpointer=checkpointer)
    return agent
