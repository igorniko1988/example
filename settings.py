from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='GT_',
        extra='ignore',
    )

    base_url: str | None = None
    auth_email: str | None = None
    auth_password: str | None = None
    binance_api_key: str | None = None
    binance_api_secret: str | None = None
    telegram_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_report_variants: str = 'rich,rich_failures'
    telegram_project_name: str = 'GT UI Tests'
    telegram_verify_ssl: bool = True


@lru_cache
def get_settings() -> TestSettings:
    return TestSettings()
