import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import news_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动中...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已创建")
    yield
    logger.info("应用关闭中...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="舆情监控与汇总系统 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router)


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "舆情监控系统 API",
        "docs": "/docs",
        "health": "/api/health",
    }
