# app/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Azure Data Explorer Settings
    KUSTO_CLUSTER_URL: str  # The full ADX cluster URL
    KUSTO_DATABASE_NAME: str
    KUSTO_CLIENT_ID: str
    KUSTO_CLIENT_SECRET: str
    KUSTO_TENANT_ID: str

    # API Settings
    API_TITLE: str = "Azure Data Explorer Query API"
    API_PREFIX: str = "/api"
    DEBUG_MODE: bool = False

    # OpenAI Settings
    OPENAI_API_KEY: str
    OPEN_AI_MODEL: str = "gpt-4"  # default model

    # Anthropic Settings
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"  # default model

    # Organization Settings
    ORGANIZATION_ID: str
    ENVIRONMENT_ID: str

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()