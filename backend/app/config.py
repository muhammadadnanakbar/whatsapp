from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    waha_base_url: str = "http://localhost:3000"
    waha_api_key: str = ""
    waha_session: str = "default"
    participant_batch_size: int = 10
    participant_batch_delay_ms: int = 1500


@lru_cache
def get_settings() -> Settings:
    return Settings()
