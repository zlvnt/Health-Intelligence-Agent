from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

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

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    api_key=settings.anthropic_api_key,
)


async def create_agent():
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.checkpointer_db_url)
    await checkpointer.setup()

    nutrition_tool = create_nutrition_tool()

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
        tools=[log_meal, get_daily_summary, get_meal_history, set_calorie_goal, nutrition_tool],
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
        output_mode="full_history",
    )

    agent = workflow.compile(checkpointer=checkpointer)
    return agent
