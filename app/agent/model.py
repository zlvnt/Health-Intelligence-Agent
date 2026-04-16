"""
Model factory for flexible LLM provider switching.

Supports: Anthropic, OpenAI, Google, Ollama
Configure via environment variables.
"""

from typing import Literal

from langchain_core.language_models import BaseChatModel

from app.config import settings

ModelProvider = Literal["anthropic", "openai", "google", "ollama"]


def create_llm(provider: ModelProvider | None = None) -> BaseChatModel:
    """
    Create LLM instance based on provider.

    Args:
        provider: Model provider. If None, uses settings.model_provider (default: anthropic)

    Returns:
        BaseChatModel instance

    Examples:
        >>> llm = create_llm("anthropic")  # Claude
        >>> llm = create_llm("openai")     # GPT-4
        >>> llm = create_llm("google")     # Gemini
        >>> llm = create_llm("ollama")     # Local Llama
    """
    provider = provider or getattr(settings, "model_provider", "anthropic")

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=getattr(settings, "anthropic_model", "claude-sonnet-4-20250514"),
            api_key=settings.anthropic_api_key,
            temperature=0.7,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=getattr(settings, "openai_model", "gpt-4o"),
            api_key=settings.openai_api_key,
            temperature=0.7,
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=getattr(settings, "google_model", "gemini-1.5-pro"),
            google_api_key=settings.google_api_key,
            temperature=0.7,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=getattr(settings, "ollama_model", "llama3.1"),
            base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"),
            temperature=0.7,
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def create_fast_llm() -> BaseChatModel:
    """
    Create a fast, cheap model for simple tasks (routing, classification).

    Useful for orchestrator that doesn't need reasoning depth.
    """
    provider = getattr(settings, "model_provider", "anthropic")

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=settings.anthropic_api_key)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.google_api_key)

    else:
        # Fallback to main model
        return create_llm(provider)
