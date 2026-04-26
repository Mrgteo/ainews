"""
分析 API 路由 - v2 多阶段分析
"""
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.news import NewsArticle
from app.models.analysis import AnalysisResult, Feedback, CaseLibrary, SourceConfidence
from app.schemas.analysis import (
    AnalysisResultV2,
    AnalyzeRequestV2,
    FeedbackCreate,
    CaseLibraryCreate,
    SourceConfidenceConfig,
    KnowledgeConceptCreate,
)
from app.services.analyzer_v2 import analyzer_v2
from app.services.scoring_service import scoring_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["分析 v2"])


@router.post("/analyze", response_model=AnalysisResultV2)
async def analyze_news_v2(
    request: AnalyzeRequestV2,
    db: Session = Depends(get_db),
):
    """
    v2 多阶段新闻分析

    工作流:
    1. 事实抽取
    2. 增量判断 (RAG 辅助)
    3. 影响分析
    4. 评分与分类
    """
    try:
        # 构建新闻数据
        news_data = {
            "id": request.news_id,
            "title": request.title,
            "content": request.content or "",
            "source": request.source or "",
            "pub_time": request.pub_time,
        }

        # 执行多阶段分析
        result = await analyzer_v2.analyze(news_data)

        # 如果提供了 news_id，保存分析结果到数据库
        if request.news_id:
            article = db.query(NewsArticle).filter(NewsArticle.id == request.news_id).first()
            if article:
                # 更新原始字段（兼容旧系统）
                article.importance_score = int(result.get("scores", {}).get("importance", 50))
                article.final_score = result.get("final_score", 50)
                article.news_type = result.get("news_level", "normal")
                article.is_processed = True
                article.processed_at = datetime.now()

                # 保存详细分析结果
                analysis_record = AnalysisResult(
                    news_id=request.news_id,
                    news_type=result.get("news_type"),
                    news_subtype=result.get("news_subtype"),
                    classification_confidence=result.get("classification_confidence", 0.5),
                    importance_score=result.get("scores", {}).get("importance"),
                    incremental_score=result.get("scores", {}).get("incremental"),
                    expectation_score=result.get("scores", {}).get("expectation"),
                    scope_score=result.get("scores", {}).get("scope"),
                    source_confidence_score=result.get("scores", {}).get("source_confidence"),
                    market_reaction_score=result.get("scores", {}).get("market_reaction"),
                    final_score=result.get("final_score"),
                    news_level=result.get("news_level"),
                    incremental_level=result.get("incremental_level"),
                    new_facts=result.get("new_facts", []),
                    historical_known_facts=result.get("historical_known_facts", []),
                    affected_objects=result.get("affected_objects", []),
                    confidence=result.get("confidence", 0.5),
                    need_manual_review=result.get("need_manual_review", False),
                    analysis_detail=result,
                )
                db.add(analysis_record)

                # 添加到 RAG 库
                await rag_service.add_news(
                    news_id=article.id,
                    title=article.title,
                    content=article.content or "",
                )

                db.commit()

        return result

    except Exception as e:
        logger.error(f"v2 分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/feedback")
def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
):
    """提交人工反馈"""
    try:
        # 创建反馈记录
        feedback_record = Feedback(
            news_id=feedback.news_id,
            analysis_id=feedback.analysis_id,
            corrected_type=feedback.corrected_type,
            corrected_score=feedback.corrected_score,
            corrected_level=feedback.corrected_level,
            corrected_subscores=feedback.corrected_subscores,
            error_type=feedback.error_type,
            error_detail=feedback.error_detail,
            notes=feedback.notes,
            reviewer=feedback.reviewer,
            reviewed_at=datetime.now(),
            feedback_status="pending",
        )
        db.add(feedback_record)

        # 如果有修正内容，更新新闻记录
        if feedback.corrected_level or feedback.corrected_score:
            article = db.query(NewsArticle).filter(NewsArticle.id == feedback.news_id).first()
            if article:
                if feedback.corrected_score is not None:
                    article.final_score = feedback.corrected_score
                if feedback.corrected_level:
                    article.news_type = feedback.corrected_level

        db.commit()

        return {"message": "反馈已提交", "feedback_id": feedback_record.id}

    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")


@router.post("/cases")
def create_case(
    case: CaseLibraryCreate,
    db: Session = Depends(get_db),
):
    """创建案例（用于 Few-shot 学习）"""
    try:
        case_record = CaseLibrary(
            news_id=case.news_id,
            case_type=case.case_type,
            error_type=case.error_type,
            news_title=case.news_title,
            news_content=case.news_content,
            news_source=case.news_source,
            source_confidence=case.source_confidence,
            original_analysis=case.original_analysis,
            corrected_analysis=case.corrected_analysis,
            tags=case.tags,
        )
        db.add(case_record)
        db.commit()

        return {"message": "案例已创建", "case_id": case_record.id}

    except Exception as e:
        logger.error(f"创建案例失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/cases", response_model=List[dict])
def get_cases(
    case_type: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    """获取案例库（用于 Few-shot）"""
    try:
        query = db.query(CaseLibrary)

        if case_type:
            query = query.filter(CaseLibrary.case_type == case_type)

        if tags:
            # 支持按标签筛选
            query = query.filter(CaseLibrary.tags.contains([tags]))

        cases = query.order_by(CaseLibrary.usage_count.desc()).limit(limit).all()

        return [
            {
                "id": c.id,
                "news_title": c.news_title,
                "news_content": c.news_content,
                "case_type": c.case_type,
                "error_type": c.error_type,
                "tags": c.tags,
            }
            for c in cases
        ]

    except Exception as e:
        logger.error(f"获取案例失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ============= 来源可信度管理 =============

@router.get("/sources", response_model=List[dict])
def get_source_configs(db: Session = Depends(get_db)):
    """获取来源可信度配置"""
    try:
        sources = db.query(SourceConfidence).all()
        return [
            {
                "id": s.id,
                "source_name": s.source_name,
                "source_level": s.source_level,
                "base_score": s.base_score,
                "need_manual_review": s.need_manual_review,
                "description": s.description,
            }
            for s in sources
        ]
    except Exception as e:
        logger.error(f"获取来源配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources")
def create_source_config(
    config: SourceConfidenceConfig,
    db: Session = Depends(get_db),
):
    """创建来源可信度配置"""
    try:
        # 检查是否已存在
        existing = db.query(SourceConfidence).filter(
            SourceConfidence.source_name == config.source_name
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="来源已存在")

        record = SourceConfidence(
            source_name=config.source_name,
            source_level=config.source_level,
            base_score=config.base_score,
            need_manual_review=config.need_manual_review,
            review_threshold=config.review_threshold,
            description=config.description,
            examples=config.examples,
        )
        db.add(record)
        db.commit()

        return {"message": "来源配置已创建", "id": record.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建来源配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_source_confidence_score(source: str, db: Session) -> float:
    """获取来源可信度评分"""
    if not source:
        return 50.0  # 默认中等可信度

    # 精确匹配
    config = db.query(SourceConfidence).filter(
        SourceConfidence.source_name == source
    ).first()
    if config:
        return float(config.base_score)

    # 模糊匹配（包含）
    configs = db.query(SourceConfidence).all()
    for config in configs:
        if config.source_name in source or source in config.source_name:
            return float(config.base_score)

    # 默认值（根据常见来源模式）
    default_scores = {
        "交易所": 95,
        "证监会": 95,
        "发改委": 90,
        "央行": 90,
        "财政部": 90,
        "财联社": 80,
        "证券时报": 78,
        "上证报": 78,
        "中证报": 78,
        "华尔街见闻": 70,
        "东方财富": 65,
        "新浪": 55,
        "腾讯": 50,
        "微信公众号": 40,
        "微博": 30,
        "论坛": 20,
        "来源不明": 10,
    }

    for keyword, score in default_scores.items():
        if keyword in source:
            return float(score)

    return 50.0  # 未知来源默认50


# ============= 反馈与复盘管理 =============

@router.get("/feedback/stats")
def get_feedback_stats(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """获取反馈统计（用于复盘）"""
    try:
        from app.services.feedback_service import feedback_service
        return feedback_service.get_error_statistics(db, days)
    except Exception as e:
        logger.error(f"获取反馈统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/cases/stats")
def get_case_library_stats(db: Session = Depends(get_db)):
    """获取样本库统计"""
    try:
        from app.services.feedback_service import feedback_service
        return feedback_service.get_case_library_stats(db)
    except Exception as e:
        logger.error(f"获取样本库统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/cases/fewshot")
def get_fewshot_cases(
    news_title: str = Query(..., description="当前新闻标题"),
    news_content: str = Query(default="", description="当前新闻内容"),
    case_type: str = Query(default="all", description="positive/negative/all"),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """获取用于 Few-shot 的案例"""
    try:
        from app.services.feedback_service import feedback_service
        current_news = {"title": news_title, "content": news_content}
        cases = feedback_service.get_cases_for_fewshot(db, current_news, case_type, limit)
        return cases
    except Exception as e:
        logger.error(f"获取 few-shot 案例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/process")
def process_feedback(
    news_id: int,
    original_analysis: dict,
    corrections: dict,
    error_type: str,
    error_detail: str = "",
    reviewer: str = "",
    db: Session = Depends(get_db),
):
    """处理反馈并沉淀到样本库"""
    try:
        from app.services.feedback_service import feedback_service
        result = feedback_service.process_feedback(
            news_id=news_id,
            original_analysis=original_analysis,
            corrections=corrections,
            error_type=error_type,
            error_detail=error_detail,
            reviewer=reviewer,
            db=db,
        )
        return {
            "success": result.success,
            "feedback_id": result.feedback_id,
            "case_id": result.case_id,
            "message": result.message,
        }
    except Exception as e:
        logger.error(f"处理反馈失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/error/types")
def get_error_types():
    """获取错误类型定义"""
    from app.services.feedback_service import feedback_service
    return [
        {
            "code": code,
            "name": data["name"],
            "description": data["description"],
            "examples": data["examples"],
        }
        for code, data in feedback_service.ERROR_TYPES.items()
    ]


@router.get("/review/pending")
def get_pending_reviews(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
):
    """获取待复核的新闻（需要人工审核的新闻）"""
    try:
        # 获取需要复核的新闻
        pending = db.query(AnalysisResult).filter(
            AnalysisResult.need_manual_review == True,
            AnalysisResult.review_status == "pending"
        ).order_by(AnalysisResult.final_score.desc()).limit(limit).all()

        return [
            {
                "analysis_id": p.id,
                "news_id": p.news_id,
                "final_score": p.final_score,
                "news_level": p.news_level,
                "confidence": p.confidence,
                "incremental_level": p.incremental_level,
                "review_reasons": "需要人工复核",
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pending
        ]
    except Exception as e:
        logger.error(f"获取待复核列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/{analysis_id}/approve")
def approve_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """审核通过分析结果"""
    try:
        analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="分析记录不存在")

        analysis.review_status = "approved"
        db.commit()

        return {"message": "审核通过"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"审核失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/{analysis_id}/reject")
def reject_analysis(
    analysis_id: int,
    reason: str = "",
    db: Session = Depends(get_db),
):
    """驳回分析结果"""
    try:
        analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="分析记录不存在")

        analysis.review_status = "pending"
        # 记录驳回原因
        analysis.analysis_detail = analysis.analysis_detail or {}
        analysis.analysis_detail["reject_reason"] = reason

        db.commit()

        return {"message": "已驳回"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"驳回失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
