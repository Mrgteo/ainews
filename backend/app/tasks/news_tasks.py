import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.news import NewsArticle
from app.services.scraper import TonghuashunScraper
from app.services.analyzer import NewsAnalyzer
from app.services.scorer import ScoreCalculator

logger = logging.getLogger(__name__)


@celery_app.task(name="scrape_news")
def scrape_news_task(days: int = 3):
    """爬取新闻任务"""
    from app.main import app

    logger.info(f"开始执行爬取任务，近{days}天")

    with SessionLocal() as db:
        scraper = TonghuashunScraper()
        news_list = scraper.scrape(days=days)

        saved_count = 0
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
        logger.info(f"爬取完成，新增 {saved_count} 条新闻")

    return {"saved": saved_count, "total": len(news_list)}


@celery_app.task(name="analyze_news")
def analyze_news_task(news_id: int):
    """分析单条新闻"""
    from app.main import app

    logger.info(f"开始分析新闻 ID: {news_id}")

    with SessionLocal() as db:
        article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
        if not article:
            logger.warning(f"新闻 ID {news_id} 不存在")
            return {"error": "News not found"}

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
            logger.info(f"新闻 ID {news_id} 分析完成，综合评分: {final_score}")

        return {"news_id": news_id, "final_score": article.final_score}


@celery_app.task(name="analyze_all_news")
def analyze_all_news_task(unprocessed_only: bool = True):
    """批量分析所有新闻"""
    logger.info("开始批量分析新闻")

    with SessionLocal() as db:
        query = db.query(NewsArticle)
        if unprocessed_only:
            query = query.filter(NewsArticle.is_processed == False)

        articles = query.all()
        logger.info(f"找到 {len(articles)} 条待分析新闻")

        analyzer = NewsAnalyzer()
        analyzed_count = 0

        for article in articles:
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

        db.commit()
        logger.info(f"批量分析完成，成功分析 {analyzed_count} 条新闻")

    return {"analyzed": analyzed_count, "total": len(articles)}
