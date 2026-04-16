from typing import Literal

from pydantic_settings import BaseSettings

ModelProvider = Literal["anthropic", "openai", "google", "ollama"]


class Settings(BaseSettings):
    # Model provider (default: anthropic)
    model_provider: ModelProvider = "anthropic"

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # OpenAI (GPT-4)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Google (Gemini)
    google_api_key: str = ""
    google_model: str = "gemini-1.5-pro"

    # Ollama (local models)
    ollama_model: str = "llama3.1"
    ollama_base_url: str = "http://localhost:11434"

    # Telegram
    telegram_bot_token: str

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/health_agent"
    checkpointer_db_url: str = "postgresql://postgres:postgres@localhost:5432/health_agent"

    # Vector Store
    qdrant_url: str = "http://localhost:6333"

    model_config = {"env_file": ".env"}


settings = Settings()
