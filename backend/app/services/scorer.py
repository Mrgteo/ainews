from typing import Optional
from app.config import settings
from app.schemas.news import NewsAnalysisResult, NewsTypeEnum


class ScoreCalculator:
    """综合评分计算器 (v1.2 - A股市场导向)"""

    # 预期差评分映射
    EXPECTATION_MAP = {
        "超预期": 20,
        "符合预期": 10,
        "低于预期": 0,
        "无法判断": 5,
    }

    # 类别敏感度映射
    CATEGORY_SENSITIVITY = {
        "宏观": 10,
        "行业": 8,
        "公司": 6,
        "市场": 7,
        "其他": 3,
    }

    # 增量因子
    INCREMENTAL_FACTOR = 1.0
    PARTIAL_INCREMENTAL_FACTOR = 0.5
    NON_INCREMENTAL_FACTOR = 0.3

    # 传导路径评分映射（用于 a_share_relevance）
    TRANSMISSION_PATH_SCORES = {
        "A": 35,  # 直接政策
        "B": 30,  # 主体直连
        "C": 22,  # 板块传导
        "D": 15,  # 风险偏好
        "E": 8,   # 无传导路径
    }

    # 利好/利空 sentiment 评分因子
    SENTIMENT_BULLISH_FACTOR = 1.0
    SENTIMENT_BEARISH_FACTOR = -1.0
    SENTIMENT_NEUTRAL_FACTOR = 0.0

    @classmethod
    def calculate_final_score(
        cls,
        importance_score: int,
        is_incremental: bool,
        expectation_diff: str,
        category: str,
        is_important: bool = False,
        a_share_impact_adjustment: float = 0.0,
        sentiment_score: float = 50.0,
        transmission_path: str = "E",
    ) -> float:
        """计算综合评分 (v1.2)

        Args:
            a_share_impact_adjustment: A股影响力调整分 (-40~+10)
            sentiment_score: 利好利空评分 (0-100, 50为中性)
            transmission_path: 传导路径 (A/B/C/D/E)
        """
        importance = float(importance_score)

        # 计算 a_share_relevance 评分（传导路径 + 重要性）
        transmission_score = cls.TRANSMISSION_PATH_SCORES.get(transmission_path, 8)
        a_share_relevance = (transmission_score * 0.6 + importance * 0.4)

        # 同花顺红字重要消息 boost
        if is_important:
            a_share_relevance = min(100, a_share_relevance + 10)

        # 计算 sentiment 因子
        if sentiment_score >= 60:
            sentiment_factor = (sentiment_score - 50) / 50 * 100 * cls.SENTIMENT_BULLISH_FACTOR
        elif sentiment_score <= 40:
            sentiment_factor = (50 - sentiment_score) / 50 * 100 * cls.SENTIMENT_BEARISH_FACTOR
        else:
            sentiment_factor = 0.0

        # 增量因子
        incremental_factor = (
            cls.INCREMENTAL_FACTOR if is_incremental else cls.NON_INCREMENTAL_FACTOR
        )

        # 预期差因子
        expectation_factor = cls.EXPECTATION_MAP.get(expectation_diff, 5)

        # 敏感度因子
        sensitivity = cls.CATEGORY_SENSITIVITY.get(category, 3)

        # 使用新权重配置计算最终分
        final_score = (
            a_share_relevance * settings.WEIGHT_A_SHARE_RELEVANCE
            + sentiment_factor * settings.WEIGHT_SENTIMENT / 100
            + incremental_factor * 30 * settings.WEIGHT_INCREMENTAL / 0.15
            + sensitivity * 10 * settings.WEIGHT_SCOPE / 0.15
        )

        # 同花顺红字重要消息分段加分 boost
        if is_important:
            if final_score >= 70:
                boost = 5
            elif final_score >= 40:
                boost = 10
            else:
                boost = 12
            final_score = min(100, final_score + boost)

        # 加上A股影响调整分
        final_score = final_score + a_share_impact_adjustment

        return round(min(100, max(0, final_score)), 2)

    @classmethod
    def determine_news_type(cls, final_score: float) -> str:
        """根据分数确定新闻类型"""
        if final_score >= 80:
            return NewsTypeEnum.URGENT.value
        elif final_score >= 60:
            return NewsTypeEnum.IMPORTANT.value
        elif final_score >= 40:
            return NewsTypeEnum.GENERAL.value
        else:
            return NewsTypeEnum.NOISE.value

    @classmethod
    def calculate_from_analysis(
        cls, analysis: NewsAnalysisResult, is_important: bool = False,
        a_share_impact_adjustment: float = 0.0,
        sentiment_score: float = 50.0, transmission_path: str = "E"
    ) -> tuple[float, str]:
        """从分析结果计算综合评分和类型 (v1.2)

        Args:
            a_share_impact_adjustment: A股影响力调整分 (-40~+10)
            sentiment_score: 利好利空评分 (0-100, 50为中性)
            transmission_path: 传导路径 (A/B/C/D/E)
        """
        final_score = cls.calculate_final_score(
            importance_score=analysis.importance_score,
            is_incremental=analysis.is_incremental,
            expectation_diff=analysis.expectation_diff.value,
            category=analysis.category,
            is_important=is_important,
            a_share_impact_adjustment=a_share_impact_adjustment,
            sentiment_score=sentiment_score,
            transmission_path=transmission_path,
        )

        news_type = cls.determine_news_type(final_score)

        return final_score, news_type

    @classmethod
    def recalculate_score(
        cls, news_data: dict, a_share_impact_adjustment: float = 0.0,
        sentiment_score: float = 50.0, transmission_path: str = "E"
    ) -> tuple[float, str]:
        """根据已有数据重新计算评分 (v1.2)"""
        importance_score = news_data.get("importance_score", 50)
        is_incremental = news_data.get("is_incremental", False)
        expectation_diff = news_data.get("expectation_diff", "无法判断")
        category = news_data.get("category", "其他")
        is_important = news_data.get("is_important", False)

        final_score = cls.calculate_final_score(
            importance_score=importance_score,
            is_incremental=is_incremental,
            expectation_diff=expectation_diff,
            category=category,
            is_important=is_important,
            a_share_impact_adjustment=a_share_impact_adjustment,
            sentiment_score=sentiment_score,
            transmission_path=transmission_path,
        )

        news_type = cls.determine_news_type(final_score)

        return final_score, news_type
