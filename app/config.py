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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
