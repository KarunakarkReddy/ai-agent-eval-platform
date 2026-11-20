
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise AI Agent Management Platform"
    APP_ENV: str = "development"

    DATABASE_URL: str

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    LLM_TEMPERATURE: float = Field(default=0.2, ge=0, le=2)

    ROUTING_CONFIDENCE_THRESHOLD: float = Field(
        default=0.60, ge=0, le=1
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
