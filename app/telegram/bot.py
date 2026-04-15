from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings


def create_bot(agent) -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    async def handle_start(update: Update, context):
        await update.message.reply_text(
            "Hi! I'm your nutrition tracking assistant. "
            "Tell me what you ate, ask for your daily summary, or set a calorie goal."
        )

    async def handle_message(update: Update, context):
        user_id = update.effective_user.id
        config = {"configurable": {"thread_id": f"tg_{user_id}"}}

        # Inject telegram_id into the message so tools know which user
        text = update.message.text
        prefixed = f"[telegram_id={user_id}] {text}"

        result = await agent.ainvoke(
            {"messages": [("user", prefixed)]},
            config=config,
        )

        response = result["messages"][-1].content
        await update.message.reply_text(response)

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
