from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./adrobot.db"
    keitaro_url: str = "https://tlgk.host"
    keitaro_api_key: str = ""
    keitaro_timeout: float = 20
    app_token: str = ""
    campaign_name_prefix: str = Field(default="test_bakhshyan_", min_length=1, max_length=100)


@lru_cache
def settings():
    return Settings()
