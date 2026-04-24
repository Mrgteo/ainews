from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class NewsTypeEnum(str, Enum):
    URGENT = "紧急"
    IMPORTANT = "重点关注"
    GENERAL = "一般参考"
    NOISE = "已处理噪音"


class ExpectationDiffEnum(str, Enum):
    EXCEED = "超预期"
    MEET = "符合预期"
    BELOW = "低于预期"
    UNCLEAR = "无法判断"


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    news_type: Optional[NewsTypeEnum] = None
    time_range: str = Field(default="1d", pattern="^(1d|3d|7d|30d)$")
    sort_by: str = Field(default="final_score", pattern="^(final_score|pub_time|importance_score)$")
    is_incremental: Optional[bool] = None


class NewsArticleCreate(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    pub_time: Optional[datetime] = None
    source: Optional[str] = None
    url: str


class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    is_processed: Optional[bool] = None
    notes: Optional[str] = None
    news_type: Optional[str] = None


class NewsAnalysisResult(BaseModel):
    importance_score: int = Field(ge=0, le=100)
    is_incremental: bool
    expectation_diff: ExpectationDiffEnum
    key_points: List[str] = []
    category: str


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    pub_time: Optional[datetime] = None
    source: Optional[str] = None
    url: str
    created_at: datetime
    importance_score: Optional[int] = None
    is_incremental: Optional[bool] = None
    expectation_diff: Optional[str] = None
    key_points: Optional[List[str]] = None
    category: Optional[str] = None
    final_score: Optional[float] = None
    news_type: Optional[str] = None
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class NewsArticleListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[NewsArticleResponse]


class ScrapeRequest(BaseModel):
    days: int = Field(default=3, ge=1, le=7)


class StatsResponse(BaseModel):
    total: int
    urgent_count: int
    important_count: int
    general_count: int
    noise_count: int
    unprocessed_count: int
    incremental_count: int
    avg_score: Optional[float] = None
