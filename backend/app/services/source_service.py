"""
来源可信度服务
提供来源分层和评分功能
"""
from typing import Dict, Optional
from dataclasses import dataclass

# 来源可信度配置
SOURCE_CONFIGS: Dict[str, Dict] = {
    # 一手官方来源
    "交易所公告": {
        "level": "official",
        "score": 95,
        "need_review": False,
        "description": "上交所、深交所、北交所官方公告",
        "examples": ["上海证券交易所", "深圳证券交易所", "北京证券交易所"],
    },
    "证监会": {
        "level": "official",
        "score": 95,
        "need_review": False,
        "description": "中国证监会及其派出机构",
        "examples": ["中国证监会", "证监会", "证券监管委员会"],
    },
    "发改委": {
        "level": "official",
        "score": 90,
        "need_review": False,
        "description": "国家发展和改革委员会",
        "examples": ["国家发改委", "发改委"],
    },
    "央行": {
        "level": "official",
        "score": 90,
        "need_review": False,
        "description": "中国人民银行",
        "examples": ["中国人民银行", "央行"],
    },
    "财政部": {
        "level": "official",
        "score": 90,
        "need_review": False,
        "description": "财政部",
        "examples": ["财政部"],
    },
    "政府官网": {
        "level": "official",
        "score": 88,
        "need_review": False,
        "description": "政府官方网站",
        "examples": ["中国政府网", "gov.cn"],
    },

    # 权威财经媒体
    "财联社": {
        "level": "authoritative",
        "score": 80,
        "need_review": False,
        "description": "财联社",
        "examples": ["财联社", "CLS"],
    },
    "证券时报": {
        "level": "authoritative",
        "score": 78,
        "need_review": False,
        "description": "证券时报",
        "examples": ["证券时报", " Securities Times"],
    },
    "上海证券报": {
        "level": "authoritative",
        "score": 78,
        "need_review": False,
        "description": "上海证券报",
        "examples": ["上海证券报", "上证报"],
    },
    "中国证券报": {
        "level": "authoritative",
        "score": 78,
        "need_review": False,
        "description": "中国证券报",
        "examples": ["中国证券报", "中证报"],
    },
    "经济参考报": {
        "level": "authoritative",
        "score": 75,
        "need_review": False,
        "description": "经济参考报",
        "examples": ["经济参考报"],
    },

    # 主流财经媒体
    "华尔街见闻": {
        "level": "media",
        "score": 70,
        "need_review": False,
        "description": "华尔街见闻",
        "examples": ["华尔街见闻", "Wall Street CN"],
    },
    "第一财经": {
        "level": "media",
        "score": 68,
        "need_review": False,
        "description": "第一财经",
        "examples": ["第一财经", "Yicai"],
    },
    "21世纪经济报道": {
        "level": "media",
        "score": 65,
        "need_review": False,
        "description": "21世纪经济报道",
        "examples": ["21世纪经济报道", "21经济"],
    },
    "东方财富": {
        "level": "media",
        "score": 65,
        "need_review": True,
        "description": "东方财富网",
        "examples": ["东方财富", "East Money"],
    },
    "新浪财经": {
        "level": "media",
        "score": 55,
        "need_review": True,
        "description": "新浪财经",
        "examples": ["新浪财经", "Sina Finance"],
    },
    "凤凰财经": {
        "level": "media",
        "score": 55,
        "need_review": True,
        "description": "凤凰财经",
        "examples": ["凤凰财经"],
    },

    # 自媒体
    "微信公众号": {
        "level": "self_media",
        "score": 40,
        "need_review": True,
        "description": "微信公众号文章",
        "examples": ["微信公众号", "微信公众平台"],
    },
    "雪球": {
        "level": "self_media",
        "score": 45,
        "need_review": True,
        "description": "雪球平台",
        "examples": ["雪球", "Xueqiu"],
    },
    "微博": {
        "level": "self_media",
        "score": 30,
        "need_review": True,
        "description": "微博",
        "examples": ["微博", "Weibo"],
    },
    "论坛": {
        "level": "self_media",
        "score": 20,
        "need_review": True,
        "description": "各种论坛帖",
        "examples": ["论坛", "股吧"],
    },

    # 来源不明
    "来源不明": {
        "level": "unknown",
        "score": 10,
        "need_review": True,
        "description": "无法确定来源",
        "examples": [],
    },
    "小作文": {
        "level": "unknown",
        "score": 5,
        "need_review": True,
        "description": "疑似小作文或不实传闻",
        "examples": ["网传", "据知情人士", "市场传闻"],
    },
}


@dataclass
class SourceResult:
    """来源分析结果"""
    source_name: str
    level: str
    score: int
    need_review: bool
    matched_keyword: str


def get_source_info(source: str) -> SourceResult:
    """
    获取来源信息

    Args:
        source: 来源名称

    Returns:
        SourceResult
    """
    if not source:
        return SourceResult(
            source_name="未知",
            level="unknown",
            score=50,
            need_review=True,
            matched_keyword="",
        )

    source = source.strip()

    # 精确匹配
    if source in SOURCE_CONFIGS:
        config = SOURCE_CONFIGS[source]
        return SourceResult(
            source_name=source,
            level=config["level"],
            score=config["score"],
            need_review=config["need_review"],
            matched_keyword=source,
        )

    # 模糊匹配
    for keyword, config in SOURCE_CONFIGS.items():
        if keyword in source or source in keyword:
            return SourceResult(
                source_name=source,
                level=config["level"],
                score=config["score"],
                need_review=config["need_review"],
                matched_keyword=keyword,
            )

    # 检查示例匹配
    for keyword, config in SOURCE_CONFIGS.items():
        for example in config.get("examples", []):
            if example in source or source in example:
                return SourceResult(
                    source_name=source,
                    level=config["level"],
                    score=config["score"],
                    need_review=config["need_review"],
                    matched_keyword=keyword,
                )

    # 默认值
    return SourceResult(
        source_name=source,
        level="unknown",
        score=50,
        need_review=True,
        matched_keyword="",
    )


def get_source_level_description(level: str) -> str:
    """获取来源级别描述"""
    descriptions = {
        "official": "官方/一手来源",
        "authoritative": "权威财经媒体",
        "media": "主流财经媒体",
        "self_media": "自媒体",
        "unknown": "来源不明",
    }
    return descriptions.get(level, "未知")


def get_review_threshold(source_level: str) -> int:
    """获取触发人工复核的分值阈值"""
    thresholds = {
        "official": 0,      # 官方来源不需要复核
        "authoritative": 85,  # 权威媒体 > 85 才复核
        "media": 70,        # 主流媒体 > 70 复核
        "self_media": 50,   # 自媒体 > 50 复核
        "unknown": 30,      # 来源不明 > 30 复核
    }
    return thresholds.get(source_level, 60)


# 全局单例
source_service = type('SourceService', (), {
    'get_source_info': staticmethod(get_source_info),
    'get_source_level_description': staticmethod(get_source_level_description),
    'get_review_threshold': staticmethod(get_review_threshold),
    'configs': SOURCE_CONFIGS,
})()
