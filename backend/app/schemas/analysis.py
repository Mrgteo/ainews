"""
分析结果 Schema - v2
用于多阶段分析的结果结构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AffectedObject(BaseModel):
    """影响对象"""
    object_type: str = Field(description="类型: index/sector/stock")
    object_name: str = Field(description="名称")
    direction: str = Field(description="方向: bullish/bearish/neutral")
    confidence: float = Field(ge=0, le=1, description="置信度")
    impact_path: Optional[str] = None
    impact_strength: Optional[str] = None


class IncrementalResult(BaseModel):
    """增量判断结果"""
    incremental_score: int = Field(ge=0, le=100)
    incremental_level: str = Field(description="high/medium/low/none")
    new_facts: List[str] = []
    historical_known_facts: List[str] = []
    is_repetition: bool = False
    judgment_basis: Optional[str] = None


class ClassificationResult(BaseModel):
    """分类结果"""
    primary_type: str
    secondary_type: Optional[str] = None
    classification_confidence: float = Field(ge=0, le=1)
    key_entities: List[str] = []
    relevant_sectors: List[str] = []


class SentimentResult(BaseModel):
    """影响方向结果"""
    sentiment_score: int = Field(ge=-100, le=100)
    sentiment_direction: str = Field(description="bullish/bearish/neutral")
    impact_objects: List[Dict[str, Any]] = []
    multi_mixed: bool = False


class FactsResult(BaseModel):
    """事实抽取结果"""
    confirmed: List[str] = []
    inferred: List[str] = []
    uncertain: List[str] = []


class SubScores(BaseModel):
    """多维度评分"""
    importance: float = Field(ge=0, le=100)
    incremental: float = Field(ge=0, le=100)
    expectation: float = Field(ge=0, le=100)
    scope: float = Field(ge=0, le=100)
    source_confidence: float = Field(ge=0, le=100)
    market_reaction: float = Field(ge=0, le=100)


class AnalysisResultV2(BaseModel):
    """v2 分析结果"""
    news_id: int
    title: str

    # 分类
    news_type: str
    news_subtype: Optional[str] = None
    classification_confidence: float = Field(ge=0, le=1, default=0.5)

    # 多维度评分
    scores: Dict[str, float]

    # 最终评分
    final_score: float = Field(ge=0, le=100)
    news_level: str = Field(description="urgent/important/normal/noise")

    # 增量信息
    incremental_level: str
    new_facts: List[str] = []
    historical_known_facts: List[str] = []

    # 影响对象
    affected_objects: List[Dict[str, Any]] = []

    # 置信度与复核
    confidence: float = Field(ge=0, le=1)
    need_manual_review: bool
    review_reasons: List[str] = []

    # 分析详情
    facts: Optional[Dict[str, Any]] = None
    impact: Optional[Dict[str, Any]] = None

    analyzed_at: str


class AnalyzeRequestV2(BaseModel):
    """v2 分析请求"""
    news_id: Optional[int] = None
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    pub_time: Optional[datetime] = None
    include_history: bool = Field(default=True, description="是否包含历史相似新闻")
    include_context: bool = Field(default=True, description="是否包含行情上下文")


class FeedbackCreate(BaseModel):
    """反馈创建"""
    news_id: int
    analysis_id: Optional[int] = None

    # 修正内容
    corrected_type: Optional[str] = None
    corrected_score: Optional[float] = Field(None, ge=0, le=100)
    corrected_level: Optional[str] = None
    corrected_subscores: Optional[Dict[str, float]] = None

    # 错误归因
    error_type: Optional[str] = None
    error_detail: Optional[str] = None

    # 备注
    notes: Optional[str] = None
    reviewer: Optional[str] = None


class CaseLibraryCreate(BaseModel):
    """案例库创建"""
    news_id: Optional[int] = None

    # 案例类型
    case_type: str  # positive, negative
    error_type: Optional[str] = None

    # 样本内容
    news_title: str
    news_content: Optional[str] = None
    news_source: Optional[str] = None
    source_confidence: Optional[int] = None

    # 分析结果
    original_analysis: Optional[Dict[str, Any]] = None
    corrected_analysis: Optional[Dict[str, Any]] = None

    # 标签
    tags: List[str] = []


class SourceConfidenceConfig(BaseModel):
    """来源可信度配置"""
    source_name: str
    source_level: str  # official, authoritative, media, self_media, unknown
    base_score: int = Field(ge=0, le=100)
    need_manual_review: bool = False
    review_threshold: Optional[int] = None
    description: Optional[str] = None
    examples: List[str] = []


class KnowledgeConceptCreate(BaseModel):
    """概念知识库创建"""
    concept_name: str
    concept_type: str  # sector, industry, chain, stock
    parent_concept: Optional[str] = None
    related_stocks: List[str] = []
    keywords: List[str] = []
    description: Optional[str] = None
