"""
评分服务 - 统一评分体系
所有子项统一 0-100 分制，加权合成最终分
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ScoreResult:
    """评分结果"""
    subscores: Dict[str, float]  # 各维度评分
    final_score: float  # 最终评分
    weights: Dict[str, float]  # 权重
    level: str  # 级别: urgent, important, normal, noise
    confidence: float  # 置信度
    need_manual_review: bool  # 是否需要人工复核
    review_reasons: list  # 复核原因


class ScoringService:
    """
    统一评分体系

    评分维度及权重:
    - importance: 重要性 0.25
    - incremental: 增量 0.25
    - expectation: 预期差 0.20
    - scope: 影响范围 0.15
    - source_confidence: 来源可信度 0.10
    - market_reaction: 行情反应 0.05
    """

    WEIGHTS = {
        "importance": 0.25,
        "incremental": 0.25,
        "expectation": 0.20,
        "scope": 0.15,
        "source_confidence": 0.10,
        "market_reaction": 0.05,
    }

    # 分级阈值
    LEVEL_THRESHOLDS = {
        "urgent": 80,    # ≥80 紧急
        "important": 60,  # ≥60 重点
        "normal": 40,    # ≥40 一般
        "noise": 0,      # <40 噪音
    }

    # 人工复核触发条件
    REVIEW_TRIGGERS = {
        "final_score": 85,      # 最终分 ≥ 85
        "source_confidence": 70,  # 来源可信度 < 70
        "confidence": 0.70,      # 模型置信度 < 0.70 (即 70%)
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.WEIGHTS

    def score(
        self,
        importance_score: float,
        incremental_score: float,
        expectation_score: float,
        scope_score: float,
        source_confidence_score: float,
        market_reaction_score: float,
        need_counter_case_review: bool = False,
        is_important: bool = False,
        a_share_impact_adjustment: float = 0.0,
    ) -> ScoreResult:
        """
        计算最终评分

        Args:
            importance_score: 重要性评分 (0-100)
            incremental_score: 增量评分 (0-100)
            expectation_score: 预期差评分 (0-100)
            scope_score: 影响范围评分 (0-100)
            source_confidence_score: 来源可信度评分 (0-100)
            market_reaction_score: 行情反应评分 (0-100)
            is_important: 是否为同花顺红字重要消息
            need_counter_case_review: 是否需要反例检查
            a_share_impact_adjustment: A股影响力调整分 (-40~+10)

        Returns:
            ScoreResult
        """
        # 确保所有分数在 0-100 范围内
        scores = {
            "importance": max(0, min(100, importance_score)),
            "incremental": max(0, min(100, incremental_score)),
            "expectation": max(0, min(100, expectation_score)),
            "scope": max(0, min(100, scope_score)),
            "source_confidence": max(0, min(100, source_confidence_score)),
            "market_reaction": max(0, min(100, market_reaction_score)),
        }

        # 加权求和
        final_score = sum(scores[k] * self.weights[k] for k in scores)

        # 同花顺红字重要消息分段加分 boost
        if is_important:
            if final_score >= 70:
                boost = 5
            elif final_score >= 40:
                boost = 10
            else:
                boost = 12
            final_score = min(100, final_score + boost)
            scores["importance"] = min(100, scores["importance"] + boost)

        # 加上A股影响调整分
        final_score = final_score + a_share_impact_adjustment

        # 确定级别
        level = self._determine_level(final_score)

        # 计算置信度（基于评分分散度）
        confidence = self._calculate_confidence(scores)

        # 检查是否需要人工复核
        need_review, review_reasons = self._check_review_triggers(
            final_score, scores, confidence, need_counter_case_review
        )

        return ScoreResult(
            subscores=scores,
            final_score=round(final_score, 2),
            weights=self.weights,
            level=level,
            confidence=round(confidence, 2),
            need_manual_review=need_review,
            review_reasons=review_reasons,
        )

    def _determine_level(self, final_score: float) -> str:
        """根据分数确定级别"""
        if final_score >= self.LEVEL_THRESHOLDS["urgent"]:
            return "urgent"
        elif final_score >= self.LEVEL_THRESHOLDS["important"]:
            return "important"
        elif final_score >= self.LEVEL_THRESHOLDS["normal"]:
            return "normal"
        else:
            return "noise"

    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """
        计算置信度

        基于各维度评分的一致性：
        - 如果各维度评分接近，置信度高
        - 如果各维度评分差异大，置信度低
        """
        values = list(scores.values())
        if not values:
            return 0.5

        # 计算标准差
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        # 转换为置信度 (标准差越小，置信度越高)
        # 标准差 0 -> 置信度 1.0
        # 标准差 50 -> 置信度 0.5
        confidence = max(0.3, 1.0 - (std_dev / 100))

        return confidence

    def _check_review_triggers(
        self,
        final_score: float,
        scores: Dict[str, float],
        confidence: float,
        need_counter_check: bool,
    ) -> tuple[bool, list]:
        """检查是否触发人工复核"""
        triggers = []

        if final_score >= self.REVIEW_TRIGGERS["final_score"]:
            triggers.append(f"最终分 {final_score:.1f} ≥ {self.REVIEW_TRIGGERS['final_score']}，需要人工确认")

        if scores["source_confidence"] < self.REVIEW_TRIGGERS["source_confidence"]:
            triggers.append(f"来源可信度 {scores['source_confidence']:.1f} < {self.REVIEW_TRIGGERS['source_confidence']}")

        if confidence < self.REVIEW_TRIGGERS["confidence"]:
            triggers.append(f"模型置信度 {confidence:.1f} < {self.REVIEW_TRIGGERS['confidence']}")

        if need_counter_check:
            triggers.append("反例检查标记需要人工复核")

        # 检查评分是否被某个维度支配
        max_score = max(scores.values())
        min_score = min(scores.values())
        if max_score - min_score > 50:
            triggers.append(f"评分分散度大 (最高{max_score:.0f} vs 最低{min_score:.0f})，需确认评分合理性")

        return len(triggers) > 0, triggers

    def adjust_score(
        self,
        original_score: float,
        adjustment: float,
        reason: str,
    ) -> float:
        """
        根据人工反馈调整评分

        Args:
            original_score: 原始评分
            adjustment: 调整量 (-30 to +30)
            reason: 调整原因

        Returns:
            调整后的评分
        """
        new_score = original_score + adjustment
        return max(0, min(100, new_score))

    def get_level_distribution(self, scores: list) -> Dict[str, int]:
        """统计评分分布"""
        distribution = {"urgent": 0, "important": 0, "normal": 0, "noise": 0}
        for score in scores:
            level = self._determine_level(score)
            distribution[level] += 1
        return distribution


# 全局单例
scoring_service = ScoringService()
