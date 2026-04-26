import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, Numeric, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class IncrementalLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExpectationType(str, enum.Enum):
    EXCEED = "exceed"        # 超预期
    MEET = "meet"           # 符合预期
    BELOW = "below"         # 低于预期
    UNKNOWN = "unknown"      # 无法判断


class AffectedObjectType(str, enum.Enum):
    INDEX = "index"          # 指数
    SECTOR = "sector"        # 板块
    STOCK = "stock"          # 个股


class ImpactDirection(str, enum.Enum):
    BULLISH = "bullish"      # 利好
    BEARISH = "bearish"      # 利空
    NEUTRAL = "neutral"      # 中性


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已审核
    INCORPORATED = "incorporated"  # 已纳入样本库


class CaseType(str, enum.Enum):
    POSITIVE = "positive"    # 正例
    NEGATIVE = "negative"    # 反例


class ErrorType(str, enum.Enum):
    OVERESTIMATED = "overestimated"      # 高估
    UNDERESTIMATED = "underestimated"    # 低估
    OLD_NEWS = "old_news"               # 旧闻误判
    DIRECTION_ERROR = "direction_error" # 方向错误
    MAPPING_ERROR = "mapping_error"     # 映射错误
    FALSE_POSITIVE = "false_positive"   # 误报


class AnalysisResult(Base):
    """新闻分析结果表 - 存储多阶段分析结果"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False, index=True)

    # 分类
    news_type = Column(String(50), nullable=True)      # 一级分类
    news_subtype = Column(String(50), nullable=True)   # 二级分类
    classification_confidence = Column(Numeric(5, 2), nullable=True)

    # 多维度评分 (0-100)
    importance_score = Column(Numeric(5, 2), nullable=True)
    incremental_score = Column(Numeric(5, 2), nullable=True)
    expectation_score = Column(Numeric(5, 2), nullable=True)
    scope_score = Column(Numeric(5, 2), nullable=True)
    source_confidence_score = Column(Numeric(5, 2), nullable=True)
    market_reaction_score = Column(Numeric(5, 2), nullable=True)

    # 最终评分
    final_score = Column(Numeric(5, 2), nullable=True)
    news_level = Column(String(20), nullable=True)  # urgent, important, normal, noise

    # 增量信息
    incremental_level = Column(String(10), nullable=True)  # high, medium, low, none
    new_facts = Column(JSON, nullable=True)  # 新增事实列表
    historical_known_facts = Column(JSON, nullable=True)  # 历史已知信息

    # 预期差
    expectation_type = Column(String(20), nullable=True)  # exceed, meet, below, unknown
    expectation_detail = Column(Text, nullable=True)

    # 影响对象 (JSON数组)
    affected_objects = Column(JSON, nullable=True)  # [{type, name, direction, confidence, reason}]

    # 置信度与复核
    confidence = Column(Numeric(5, 2), nullable=True)
    need_manual_review = Column(Boolean, default=False)
    review_status = Column(String(20), default="pending")

    # 分析详情
    analysis_detail = Column(JSON, nullable=True)  # 完整分析过程

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, news_id={self.news_id}, final_score={self.final_score})>"


class Feedback(Base):
    """人工反馈表 - 记录人工修正"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=True, index=True)

    # 修正内容
    corrected_type = Column(String(50), nullable=True)
    corrected_score = Column(Numeric(5, 2), nullable=True)
    corrected_level = Column(String(20), nullable=True)
    corrected_subscores = Column(JSON, nullable=True)

    # 错误归因
    error_type = Column(String(50), nullable=True)  # overestimated, underestimated, old_news, etc.
    error_detail = Column(Text, nullable=True)

    # 元数据
    reviewer = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    feedback_status = Column(String(20), default="pending")  # pending, approved, incorporated

    # 备注
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Feedback(id={self.id}, news_id={self.news_id}, error_type={self.error_type})>"


class CaseLibrary(Base):
    """案例库表 - 存储正例和反例"""
    __tablename__ = "case_library"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news_articles.id"), nullable=True, index=True)

    # 案例类型
    case_type = Column(String(20), nullable=True)  # positive, negative
    error_type = Column(String(50), nullable=True)  # 如果是负例

    # 样本内容
    news_title = Column(String(500), nullable=False)
    news_content = Column(Text, nullable=True)
    news_source = Column(String(100), nullable=True)
    source_confidence = Column(Integer, nullable=True)

    # 分析结果
    original_analysis = Column(JSON, nullable=True)  # 原始AI分析
    corrected_analysis = Column(JSON, nullable=True)  # 修正后分析

    # 用于 Few-shot 的示例
    example_prompt = Column(Text, nullable=True)
    example_response = Column(Text, nullable=True)

    # 标签
    tags = Column(JSON, nullable=True)  # ["新能源汽车", "政策", "超预期"]

    # 使用统计
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CaseLibrary(id={self.id}, news_title={self.news_title[:30]}, case_type={self.case_type})>"


class KnowledgeConcept(Base):
    """概念知识库 - 存储板块、产业链、个股映射"""
    __tablename__ = "knowledge_concepts"

    id = Column(Integer, primary_key=True, index=True)

    # 概念信息
    concept_name = Column(String(100), nullable=False, index=True)  # e.g., "新能源汽车"
    concept_type = Column(String(20), nullable=False)  # sector, industry, chain, stock
    parent_concept = Column(String(100), nullable=True)  # 上级概念

    # 相关股票
    related_stocks = Column(JSON, nullable=True)  # ["比亚迪", "宁德时代", ...]

    # 关键词
    keywords = Column(JSON, nullable=True)  # 用于召回

    # 描述
    description = Column(Text, nullable=True)

    # 置信度
    confidence = Column(Numeric(5, 2), default=1.0)

    # 使用统计
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeConcept(id={self.id}, name={self.concept_name}, type={self.concept_type})>"


class SourceConfidence(Base):
    """新闻来源可信度配置表"""
    __tablename__ = "source_confidence"

    id = Column(Integer, primary_key=True, index=True)

    # 来源信息
    source_name = Column(String(100), nullable=False, unique=True, index=True)
    source_level = Column(String(20), nullable=False)  # official, authoritative, media, self_media, unknown
    base_score = Column(Integer, nullable=False)  # 0-100

    # 处理规则
    need_manual_review = Column(Boolean, default=False)  # 是否需要人工复核
    review_threshold = Column(Integer, nullable=True)  # 触发复核的分值阈值

    # 描述
    description = Column(Text, nullable=True)

    # 示例
    examples = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SourceConfidence(id={self.id}, source={self.source_name}, level={self.source_level}, score={self.base_score})>"
