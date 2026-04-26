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

    # 评分权重配置 (v1.2 - A股市场导向优化)
    WEIGHT_A_SHARE_RELEVANCE: float = 0.30  # A股关联度
    WEIGHT_SENTIMENT: float = 0.25  # 利好利空方向
    WEIGHT_INCREMENTAL: float = 0.15  # 增量
    WEIGHT_SCOPE: float = 0.15  # 影响范围
    WEIGHT_SOURCE_CONFIDENCE: float = 0.10  # 来源可信度
    WEIGHT_MARKET_REACTION: float = 0.05  # 行情反应

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
