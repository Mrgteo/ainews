import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db, SessionLocal
from app.models.news import NewsArticle
from app.schemas.news import (
    NewsArticleResponse,
    NewsArticleListResponse,
    NewsArticleUpdate,
    NewsAnalysisResult,
    ScrapeRequest,
    StatsResponse,
    PageParams,
    NewsTypeEnum,
)
from app.services.scraper import TonghuashunScraper
from app.services.analyzer import NewsAnalyzer
from app.services.scorer import ScoreCalculator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["新闻"])


def parse_time_range(time_range: str) -> datetime:
    """解析时间范围"""
    now = datetime.now()
    if time_range == "1d":
        return now - timedelta(days=1)
    elif time_range == "3d":
        return now - timedelta(days=3)
    elif time_range == "7d":
        return now - timedelta(days=7)
    elif time_range == "30d":
        return now - timedelta(days=30)
    return now - timedelta(days=1)


@router.get("", response_model=NewsArticleListResponse)
def get_news_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    news_type: Optional[NewsTypeEnum] = None,
    time_range: str = Query(default="1d", pattern="^(1d|3d|7d|30d)$"),
    sort_by: str = Query(default="final_score", pattern="^(final_score|pub_time|importance_score)$"),
    is_incremental: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取新闻列表"""
    query = db.query(NewsArticle)

    if news_type:
        query = query.filter(NewsArticle.news_type == news_type.value)

    time_cutoff = parse_time_range(time_range)
    query = query.filter(NewsArticle.pub_time >= time_cutoff)

    if is_incremental is not None:
        query = query.filter(NewsArticle.is_incremental == is_incremental)

    total = query.count()

    if sort_by == "final_score":
        query = query.order_by(desc(NewsArticle.final_score))
    elif sort_by == "pub_time":
        query = query.order_by(desc(NewsArticle.pub_time))
    elif sort_by == "importance_score":
        query = query.order_by(desc(NewsArticle.importance_score))
    else:
        query = query.order_by(desc(NewsArticle.final_score))

    offset = (page - 1) * page_size
    articles = query.offset(offset).limit(page_size).all()

    return NewsArticleListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=articles,
    )


@router.get("/{news_id}", response_model=NewsArticleResponse)
def get_news_detail(news_id: int, db: Session = Depends(get_db)):
    """获取新闻详情"""
    article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return article


@router.post("/scrape")
def scrape_news(request: ScrapeRequest):
    """爬取新闻（同步执行）"""
    try:
        scraper = TonghuashunScraper()
        news_list = scraper.scrape(days=request.days)

        db = SessionLocal()
        saved_count = 0
        try:
            for news in news_list:
                existing = db.query(NewsArticle).filter(NewsArticle.url == news["url"]).first()
                if existing:
                    continue
                article = NewsArticle(
                    title=news["title"],
                    content=news.get("content"),
                    summary=news.get("summary"),
                    pub_time=news.get("pub_time"),
                    source=news.get("source"),
                    url=news["url"],
                )
                db.add(article)
                saved_count += 1
            db.commit()
        finally:
            db.close()

        return {"message": f"爬取完成，新增 {saved_count} 条新闻", "total": len(news_list), "saved": saved_count}
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")


@router.post("/analyze/{news_id}")
def analyze_single_news(news_id: int, db: Session = Depends(get_db)):
    """分析单条新闻（同步执行）"""
    article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")

    try:
        analyzer = NewsAnalyzer()
        analysis = analyzer.analyze_news(
            title=article.title,
            content=article.content or "",
        )

        if analysis:
            article.importance_score = analysis.importance_score
            article.is_incremental = analysis.is_incremental
            article.expectation_diff = analysis.expectation_diff.value
            article.key_points = analysis.key_points
            article.category = analysis.category

            final_score, news_type = ScoreCalculator.calculate_from_analysis(analysis)
            article.final_score = final_score
            article.news_type = news_type
            article.is_processed = True
            article.processed_at = datetime.now()
            db.commit()

            return {"message": "分析完成", "news_id": news_id, "final_score": final_score, "news_type": news_type}
        else:
            raise HTTPException(status_code=500, detail="AI分析返回结果为空")
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/analyze-all")
def analyze_all_news(unprocessed_only: bool = Query(default=True)):
    """批量分析新闻（同步执行）"""
    db = SessionLocal()
    try:
        query = db.query(NewsArticle)
        if unprocessed_only:
            query = query.filter(NewsArticle.is_processed == False)

        articles = query.all()
        analyzed_count = 0

        analyzer = NewsAnalyzer()

        for article in articles:
            try:
                analysis = analyzer.analyze_news(
                    title=article.title,
                    content=article.content or "",
                )

                if analysis:
                    article.importance_score = analysis.importance_score
                    article.is_incremental = analysis.is_incremental
                    article.expectation_diff = analysis.expectation_diff.value
                    article.key_points = analysis.key_points
                    article.category = analysis.category

                    final_score, news_type = ScoreCalculator.calculate_from_analysis(analysis)
                    article.final_score = final_score
                    article.news_type = news_type
                    article.is_processed = True
                    article.processed_at = datetime.now()
                    analyzed_count += 1
            except Exception as e:
                logger.error(f"分析新闻 {article.id} 失败: {e}")
                continue

        db.commit()
        return {"message": f"批量分析完成，成功分析 {analyzed_count} 条新闻", "analyzed": analyzed_count, "total": len(articles)}
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")
    finally:
        db.close()


@router.get("/stats/summary", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    total = db.query(NewsArticle).count()

    urgent_count = db.query(NewsArticle).filter(NewsArticle.news_type == "紧急").count()
    important_count = db.query(NewsArticle).filter(NewsArticle.news_type == "重点关注").count()
    general_count = db.query(NewsArticle).filter(NewsArticle.news_type == "一般参考").count()
    noise_count = db.query(NewsArticle).filter(NewsArticle.news_type == "已处理噪音").count()

    unprocessed_count = db.query(NewsArticle).filter(NewsArticle.is_processed == False).count()
    incremental_count = db.query(NewsArticle).filter(NewsArticle.is_incremental == True).count()

    avg_score = db.query(func.avg(NewsArticle.final_score)).scalar()

    return StatsResponse(
        total=total,
        urgent_count=urgent_count,
        important_count=important_count,
        general_count=general_count,
        noise_count=noise_count,
        unprocessed_count=unprocessed_count,
        incremental_count=incremental_count,
        avg_score=round(float(avg_score), 2) if avg_score else None,
    )


@router.put("/{news_id}/type")
def update_news_type(news_id: int, update: NewsArticleUpdate, db: Session = Depends(get_db)):
    """更新新闻类型"""
    article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")

    if update.news_type is not None:
        article.news_type = update.news_type
    if update.is_processed is not None:
        article.is_processed = update.is_processed
    if update.notes is not None:
        article.notes = update.notes

    article.processed_at = datetime.now()
    db.commit()

    return {"message": "更新成功"}


@router.delete("/{news_id}")
def delete_news(news_id: int, db: Session = Depends(get_db)):
    """删除新闻"""
    article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")

    db.delete(article)
    db.commit()

    return {"message": "删除成功"}
