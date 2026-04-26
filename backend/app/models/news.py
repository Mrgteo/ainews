import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, Numeric, JSON
from sqlalchemy.sql import func
from app.database import Base


class NewsType(str, enum.Enum):
    URGENT = "紧急"
    IMPORTANT = "重点关注"
    GENERAL = "一般参考"
    NOISE = "已处理噪音"


class ExpectationDiff(str, enum.Enum):
    EXCEED = "超预期"
    MEET = "符合预期"
    BELOW = "低于预期"
    UNCLEAR = "无法判断"


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    pub_time = Column(DateTime(timezone=True))
    source = Column(String(100))
    url = Column(String(1000), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # AI评分字段
    importance_score = Column(Integer, nullable=True)
    is_incremental = Column(Boolean, nullable=True)
    expectation_diff = Column(String(50), nullable=True)
    key_points = Column(JSON, nullable=True)
    category = Column(String(50), nullable=True)
    final_score = Column(Numeric(5, 2), nullable=True)
    news_type = Column(String(50), nullable=True)

    # 来源标记字段
    is_important = Column(Boolean, default=False)  # 同花顺红字重要消息

    # 状态字段
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title={self.title}, news_type={self.news_type})>"
