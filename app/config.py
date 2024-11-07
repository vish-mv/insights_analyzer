from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Azure Data Explorer Settings
    KUSTO_CLUSTER_URL: str
    KUSTO_DATABASE_NAME: str


    # API Settings
    API_TITLE: str = "Azure Data Explorer Query API"
    API_PREFIX: str = "/api"
    DEBUG_MODE: bool = False

    # OpenAI API Key
    OPENAI_API_KEY: str

    # Anthropic Api key
    ANTHROPIC_API_KEY: str

    # Organization ID
    ORGANIZATION_ID: str
    ENVIRONMENT_ID: str

    #Models Name
    OPEN_AI_MODEL: str
    ANTHROPIC_MODEL: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
