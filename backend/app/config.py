import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "舆情监控与汇总系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # DeepSeek API 配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 数据库配置 (开发环境使用 SQLite)
    DATABASE_URL: str = "sqlite:///./sentiment.db"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # Chrome Driver 配置
    CHROME_DRIVER_PATH: Optional[str] = None

    # 爬虫配置
    SCRAPE_TIME_RANGE_DAYS: int = 1
    SCRAPE_INTERVAL_MINUTES: int = 15
    REQUEST_DELAY_MIN: int = 3
    REQUEST_DELAY_MAX: int = 8
    MAX_RETRIES: int = 3

    # 评分权重配置
    WEIGHT_IMPORTANCE: float = 0.4
    WEIGHT_INCREMENTAL: float = 0.3
    WEIGHT_EXPECTATION: float = 0.2
    WEIGHT_SENSITIVITY: float = 0.1

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
