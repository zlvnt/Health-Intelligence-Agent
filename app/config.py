from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    telegram_bot_token: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/health_agent"
    checkpointer_db_url: str = "postgresql://postgres:postgres@localhost:5432/health_agent"
    qdrant_url: str = "http://localhost:6333"

    model_config = {"env_file": ".env"}


settings = Settings()
