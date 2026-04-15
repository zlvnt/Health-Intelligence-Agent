from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import get_daily_summary, get_meal_history, log_meal, set_calorie_goal
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
    tools = [log_meal, get_daily_summary, get_meal_history, set_calorie_goal, nutrition_tool]

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return agent
