from typing import Optional
from app.config import settings
from app.schemas.news import NewsAnalysisResult, NewsTypeEnum


class ScoreCalculator:
    """综合评分计算器"""

    EXPECTATION_MAP = {
        "超预期": 20,
        "符合预期": 10,
        "低于预期": 0,
        "无法判断": 5,
    }

    CATEGORY_SENSITIVITY = {
        "宏观": 10,
        "行业": 8,
        "公司": 6,
        "市场": 7,
        "其他": 3,
    }

    INCREMENTAL_FACTOR = 1.0
    PARTIAL_INCREMENTAL_FACTOR = 0.5
    NON_INCREMENTAL_FACTOR = 0.3

    @classmethod
    def calculate_final_score(
        cls,
        importance_score: int,
        is_incremental: bool,
        expectation_diff: str,
        category: str,
    ) -> float:
        """计算综合评分"""
        importance = float(importance_score)

        incremental_factor = (
            cls.INCREMENTAL_FACTOR if is_incremental else cls.NON_INCREMENTAL_FACTOR
        )

        expectation_factor = cls.EXPECTATION_MAP.get(expectation_diff, 5)

        sensitivity = cls.CATEGORY_SENSITIVITY.get(category, 3)

        final_score = (
            importance * settings.WEIGHT_IMPORTANCE
            + incremental_factor * 30
            + expectation_factor * settings.WEIGHT_EXPECTATION / 0.2
            + sensitivity * settings.WEIGHT_SENSITIVITY / 0.1
        )

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
        cls, analysis: NewsAnalysisResult
    ) -> tuple[float, str]:
        """从分析结果计算综合评分和类型"""
        final_score = cls.calculate_final_score(
            importance_score=analysis.importance_score,
            is_incremental=analysis.is_incremental,
            expectation_diff=analysis.expectation_diff.value,
            category=analysis.category,
        )

        news_type = cls.determine_news_type(final_score)

        return final_score, news_type

    @classmethod
    def recalculate_score(cls, news_data: dict) -> tuple[float, str]:
        """根据已有数据重新计算评分"""
        importance_score = news_data.get("importance_score", 50)
        is_incremental = news_data.get("is_incremental", False)
        expectation_diff = news_data.get("expectation_diff", "无法判断")
        category = news_data.get("category", "其他")

        final_score = cls.calculate_final_score(
            importance_score=importance_score,
            is_incremental=is_incremental,
            expectation_diff=expectation_diff,
            category=category,
        )

        news_type = cls.determine_news_type(final_score)

        return final_score, news_type
