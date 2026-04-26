"""
反馈服务
处理人工反馈、错误归因、样本沉淀
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import json

from app.services.scoring_service import scoring_service


@dataclass
class FeedbackResult:
    """反馈处理结果"""
    success: bool
    feedback_id: Optional[int] = None
    case_id: Optional[int] = None
    error_type: Optional[str] = None
    message: str = ""


class FeedbackService:
    """
    反馈服务

    工作流:
    1. 接收反馈
    2. 错误归因
    3. 沉淀到样本库
    4. 更新 Prompt (标记)
    """

    # 错误类型定义
    ERROR_TYPES = {
        "overestimated": {
            "name": "高估",
            "description": "评分过高",
            "examples": ["来源不可靠但给分高", "旧闻误判为增量", "利好兑现仍给高分"],
        },
        "underestimated": {
            "name": "低估",
            "description": "评分过低",
            "examples": ["重要政策给分低", "增量信息未识别"],
        },
        "old_news": {
            "name": "旧闻误判",
            "description": "将旧闻误判为增量",
            "examples": ["重复发布的消息", "已被市场消化的信息"],
        },
        "direction_error": {
            "name": "方向错误",
            "description": "利好/利空判断错误",
            "examples": ["利好判断为利空", "超预期判断为低于预期"],
        },
        "mapping_error": {
            "name": "映射错误",
            "description": "板块/个股映射不准确",
            "examples": ["未映射到受益板块", "错误映射到无关板块"],
        },
        "false_positive": {
            "name": "误报",
            "description": "噪音误判为有效信息",
            "examples": ["小作文当真", "标题党"],
        },
        "false_negative": {
            "name": "漏报",
            "description": "重要信息未识别",
            "examples": ["重要新闻未标记", "紧急新闻未识别"],
        },
    }

    def process_feedback(
        self,
        news_id: int,
        original_analysis: Dict[str, Any],
        corrections: Dict[str, Any],
        error_type: str,
        error_detail: str = "",
        reviewer: str = "",
        db=None,
    ) -> FeedbackResult:
        """
        处理反馈

        Args:
            news_id: 新闻ID
            original_analysis: 原始分析结果
            corrections: 修正内容
            error_type: 错误类型
            error_detail: 错误详情
            reviewer: 审核人
            db: 数据库会话

        Returns:
            FeedbackResult
        """
        try:
            # 1. 保存反馈记录
            from app.models.analysis import Feedback
            feedback_record = Feedback(
                news_id=news_id,
                corrected_type=corrections.get("type"),
                corrected_score=corrections.get("score"),
                corrected_level=corrections.get("level"),
                corrected_subscores=corrections.get("subscores"),
                error_type=error_type,
                error_detail=error_detail,
                reviewer=reviewer,
                reviewed_at=datetime.now(),
                feedback_status="approved",
            )
            db.add(feedback_record)
            db.flush()

            # 2. 沉淀到样本库
            from app.models.analysis import CaseLibrary
            case_type = "negative" if error_type in ["overestimated", "false_positive"] else "positive"

            case_record = CaseLibrary(
                news_id=news_id,
                case_type=case_type,
                error_type=error_type if case_type == "negative" else None,
                news_title=original_analysis.get("title", ""),
                news_content=original_analysis.get("content", ""),
                news_source=original_analysis.get("source"),
                source_confidence=original_analysis.get("scores", {}).get("source_confidence"),
                original_analysis=original_analysis,
                corrected_analysis=corrections,
            )
            db.add(case_record)
            db.flush()

            # 3. 标记需要更新 Prompt
            self._mark_prompt_update_needed(error_type, db)

            db.commit()

            return FeedbackResult(
                success=True,
                feedback_id=feedback_record.id,
                case_id=case_record.id,
                error_type=error_type,
                message="反馈已处理，样本已沉淀",
            )

        except Exception as e:
            db.rollback()
            return FeedbackResult(
                success=False,
                error_type=error_type,
                message=f"处理失败: {str(e)}",
            )

    def _mark_prompt_update_needed(self, error_type: str, db):
        """标记需要更新的 Prompt 类型"""
        # 这里可以记录到数据库或文件
        # 简化实现：打印日志
        pass

    def get_error_statistics(self, db, days: int = 7) -> Dict[str, Any]:
        """
        获取错误统计（用于复盘）

        Args:
            db: 数据库会话
            days: 统计最近天数

        Returns:
            统计数据
        """
        from app.models.analysis import Feedback
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        feedbacks = db.query(Feedback).filter(Feedback.reviewed_at >= cutoff).all()

        # 按错误类型统计
        error_counts: Dict[str, int] = {}
        total_count = len(feedbacks)

        for fb in feedbacks:
            if fb.error_type:
                error_counts[fb.error_type] = error_counts.get(fb.error_type, 0) + 1

        # 计算各类错误占比
        error_rates = {
            et: round(count / total_count * 100, 2) if total_count > 0 else 0
            for et, count in error_counts.items()
        }

        # 计算评分偏差
        score_adjustments = []
        for fb in feedbacks:
            if fb.corrected_score is not None and fb.original_analysis:
                original_score = fb.original_analysis.get("final_score", 0)
                if original_score:
                    adjustment = fb.corrected_score - original_score
                    score_adjustments.append(adjustment)

        avg_adjustment = sum(score_adjustments) / len(score_adjustments) if score_adjustments else 0

        return {
            "period_days": days,
            "total_feedbacks": total_count,
            "error_counts": error_counts,
            "error_rates": error_rates,
            "avg_score_adjustment": round(avg_adjustment, 2),
            "most_common_error": max(error_counts, key=error_counts.get) if error_counts else None,
        }

    def get_case_library_stats(self, db) -> Dict[str, Any]:
        """获取样本库统计"""
        from app.models.analysis import CaseLibrary

        total_cases = db.query(CaseLibrary).count()
        positive_cases = db.query(CaseLibrary).filter(CaseLibrary.case_type == "positive").count()
        negative_cases = db.query(CaseLibrary).filter(CaseLibrary.case_type == "negative").count()

        # 按错误类型统计反例
        error_type_counts: Dict[str, int] = {}
        counter_cases = db.query(CaseLibrary).filter(CaseLibrary.case_type == "negative").all()
        for case in counter_cases:
            if case.error_type:
                error_type_counts[case.error_type] = error_type_counts.get(case.error_type, 0) + 1

        # 使用次数最多的案例
        most_used = db.query(CaseLibrary).order_by(CaseLibrary.usage_count.desc()).first()

        return {
            "total_cases": total_cases,
            "positive_cases": positive_cases,
            "negative_cases": negative_cases,
            "error_type_counts": error_type_counts,
            "most_used_case": {
                "id": most_used.id,
                "title": most_used.news_title[:50] if most_used else None,
                "usage_count": most_used.usage_count if most_used else 0,
            } if most_used else None,
        }

    def increment_case_usage(self, db, case_id: int):
        """增加案例使用次数"""
        from app.models.analysis import CaseLibrary
        case = db.query(CaseLibrary).filter(CaseLibrary.id == case_id).first()
        if case:
            case.usage_count += 1
            case.last_used_at = datetime.now()
            db.commit()

    def get_cases_for_fewshot(
        self,
        db,
        current_news: Dict[str, Any],
        case_type: str = "all",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        获取用于 Few-shot 的案例

        Args:
            db: 数据库会话
            current_news: 当前新闻
            case_type: 案例类型 (positive/negative/all)
            limit: 返回数量

        Returns:
            案例列表
        """
        from app.models.analysis import CaseLibrary

        query = db.query(CaseLibrary)

        if case_type != "all":
            query = query.filter(CaseLibrary.case_type == case_type)

        # 按使用次数和新鲜度排序
        cases = query.order_by(
            CaseLibrary.usage_count.desc(),
            CaseLibrary.created_at.desc()
        ).limit(limit * 2).all()  # 多取一些用于筛选

        # 简单相似度匹配（标题关键词）
        current_keywords = set()
        if current_news.get("title"):
            title = current_news["title"].lower()
            for i in range(len(title) - 1):
                current_keywords.add(title[i:i+2])

        scored_cases = []
        for case in cases:
            score = 0
            if case.news_title:
                case_title = case.news_title.lower()
                for i in range(len(case_title) - 1):
                    if case_title[i:i+2] in current_keywords:
                        score += 1

            scored_cases.append((score, case))

        # 排序并返回 top N
        scored_cases.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": case.id,
                "news_title": case.news_title,
                "news_content": case.news_content[:200] if case.news_content else "",
                "case_type": case.case_type,
                "error_type": case.error_type,
                "analysis": case.corrected_analysis or case.original_analysis,
            }
            for _, case in scored_cases[:limit]
        ]


# 全局单例
feedback_service = FeedbackService()
