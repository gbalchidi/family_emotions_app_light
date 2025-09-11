from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Proxy settings (optional)
    http_proxy: Optional[str] = Field(default=None, env="HTTP_PROXY")
    https_proxy: Optional[str] = Field(default=None, env="HTTPS_PROXY")
    no_proxy: Optional[str] = Field(default=None, env="NO_PROXY")
    
    max_phrase_length: int = Field(default=500)
    min_phrase_length: int = Field(default=2)
    
    rate_limit_messages: int = Field(default=10)
    rate_limit_window: int = Field(default=60)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()