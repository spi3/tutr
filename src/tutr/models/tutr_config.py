"""Configuration model for tutr."""

from pydantic import BaseModel, Field

DEFAULT_MODEL = "gemini/gemini-3-flash-preview"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


class TutrConfig(BaseModel):
    """Runtime configuration for tutr."""

    provider: str | None = Field(
        default=None,
        description=(
            "Active LLM provider (e.g. 'gemini', 'anthropic', 'openai', 'xai', 'ollama')."
        ),
    )
    model: str = Field(
        default=DEFAULT_MODEL,
        description="LiteLLM model string (e.g. 'gemini/gemini-3-flash-preview').",
    )
    api_key: str | None = Field(
        default=None,
        description=(
            "API key for the active provider. Overridden at runtime by the provider's "
            "environment variable (e.g. GEMINI_API_KEY)."
        ),
    )
    ollama_host: str | None = Field(
        default=None,
        description=(
            "Base URL for a local Ollama server. Defaults to http://localhost:11434 "
            "when the 'ollama' provider is active. Overridden by OLLAMA_HOST env var."
        ),
    )
    show_explanation: bool | None = Field(
        default=None,
        description=(
            "When True, show a plain-language explanation alongside the generated command. "
            "When False, suppress the explanation. None inherits the provider default."
        ),
    )
    update_check_enabled: bool = Field(
        default=True,
        description=(
            "Enable automatic update checks on startup. "
            "Can be disabled via TUTR_UPDATE_CHECK=false."
        ),
    )
    no_execute: bool | None = Field(
        default=None,
        description=(
            "When True, print the generated command without executing it. "
            "None inherits the CLI flag default."
        ),
    )
