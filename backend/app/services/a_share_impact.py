"""
A股市场影响力分类器
判断新闻对A股市场的影响调整分
"""
from typing import Dict, List, Optional


class AShareImpactClassifier:
    """
    A股市场影响力分类器

    判断新闻对A股市场的评分调整分 (-40 ~ +10)

    调整说明：
    - +0: 直接影响A股（国内政策、监管等），不调整
    - -5~-15: 间接影响（美股映射、中东地缘等）
    - -20~-40: 低/无影响（海外社会事件、娱乐新闻）
    """

    # 直接利好A股（不调整）
    DIRECT_POSITIVE = [
        "降准", "降息", "证监会", "交易所", "发改委", "央行", "财政部",
        "注册制", "IPO", "并购重组", "北向资金", "社保", "公募",
        "救市", "护盘", "松绑", "扶持", "支持", "鼓励",
        "银保监会", "金融监管", "完善制度", "改革",
    ]

    # 直接利空A股（不调整）
    DIRECT_NEGATIVE = [
        "监管调查", "问询函", "处罚", "立案", "ST", "退市",
        "打压", "收紧", "核查", "通报", "批评",
        "限制", "叫停", "暂停IPO",
    ]

    # 美股映射规则（调整 -8~-15分）
    US_MARKET_MAPPING = {
        "英伟达": {"板块": ["AI", "半导体", "算力"], "adjustment": 10},
        "nvidia": {"板块": ["AI", "半导体", "算力"], "adjustment": 10},
        "特斯拉": {"板块": ["新能源", "智能驾驶"], "adjustment": 10},
        "tesla": {"板块": ["新能源", "智能驾驶"], "adjustment": 10},
        "苹果": {"板块": ["消费电子", "苹果链"], "adjustment": 5},
        "谷歌": {"板块": ["AI", "云计算"], "adjustment": 8},
        "微软": {"板块": ["AI", "软件"], "adjustment": 8},
        "meta": {"板块": ["元宇宙", "互联网"], "adjustment": 5},
        "亚马逊": {"板块": ["电商", "云计算"], "adjustment": 5},
        "纳斯达克": {"板块": ["科技股"], "adjustment": 8},
        "道琼斯": {"板块": ["工业", "金融"], "adjustment": 5},
        "标普": {"板块": ["整体市场"], "adjustment": 5},
    }

    # 美联储政策影响（调整 -8~-12分）
    FED_POLICY = {
        "降息": -10,
        "加息": -10,
        "宽松": -10,
        "缩表": -8,
        "维持利率": -3,
        "量化宽松": -10,
        "量化紧缩": -8,
    }

    # 低/无影响力关键词（调整 -25~-35分）
    LOW_IMPACT_KEYWORDS = [
        # 海外社会事件
        "枪击", "恐袭", "爆炸", "选举", "抗议", "骚乱",
        "火灾", "地震", "海啸", "台风", "灾害",
        # 娱乐新闻
        "主播离职", "明星", "网红", "直播带货", "演唱会",
        "电影", "电视剧", "综艺", "八卦", "恋情",
        # 外国军事
        "外国军队", "外国演习", "外国武器", "外国战舰",
        # 单一公司非重大
        "产品发布", "新品上市", "价格", "降价", "涨价",
    ]

    # 国内相关关键词（遇低影响力词但包含这些则减轻惩罚）
    DOMESTIC_KEYWORDS = [
        "中国", "A股", "国内", "央行", "证监会", "发改委",
        "上证", "深证", "沪深", "科创板", "创业板",
        "港股", "恒生", "国企", "央企", "政策",
    ]

    # 中东/地缘政治关键词（调整 -10~-20分）
    GEOPOLITICAL_KEYWORDS = [
        "伊朗", "以色列", "中东", "霍尔木兹", "沙特", "OPEC",
        "俄罗斯", "乌克兰", "欧洲", "德国", "法国", "英国",
    ]

    def classify_impact(self, title: str, content: str = "") -> Dict:
        """
        分类新闻对A股的评分影响

        Args:
            title: 新闻标题
            content: 新闻内容（可选）

        Returns:
            {
                "adjustment": -40 ~ +10,   # 评分调整分
                "coefficient": 0.0 ~ 1.0, # 影响力系数（兼容旧接口）
                "reason": str,              # 判断理由
                "affected_sectors": [],    # 受影响板块
                "is_direct": bool          # 是否直接影响
            }
        """
        text = (title + " " + (content or "")).lower()

        # 1. 检查直接利好 - 不调整
        for kw in self.DIRECT_POSITIVE:
            if kw.lower() in text:
                return {
                    "adjustment": 0,
                    "coefficient": 1.0,
                    "reason": f"直接利好A股: {kw}",
                    "affected_sectors": ["整体市场"],
                    "is_direct": True
                }

        # 2. 检查直接利空 - 不调整
        for kw in self.DIRECT_NEGATIVE:
            if kw.lower() in text:
                return {
                    "adjustment": 0,
                    "coefficient": 1.0,
                    "reason": f"直接利空A股: {kw}",
                    "affected_sectors": ["整体市场"],
                    "is_direct": True
                }

        # 3. 检查美股映射 - 调整 -8~-15分
        for us_stock, info in self.US_MARKET_MAPPING.items():
            if us_stock.lower() in text:
                sentiment = 0
                if any(w in text for w in ["涨", "升", "大涨", "飙升", "创新高"]):
                    sentiment = 1  # 利好A股
                elif any(w in text for w in ["跌", "降", "大跌", "暴跌", "创新低"]):
                    sentiment = -1  # 利空A股

                adjustment = info["adjustment"] * sentiment
                return {
                    "adjustment": adjustment,
                    "coefficient": 1.0 + adjustment / 100,  # 0.9~1.1
                    "reason": f"美股{us_stock}传导",
                    "affected_sectors": info["板块"],
                    "is_direct": False
                }

        # 4. 检查美联储政策 - 调整 -8~-12分
        for policy, adjustment in self.FED_POLICY.items():
            if policy.lower() in text:
                return {
                    "adjustment": adjustment,
                    "coefficient": 1.0 + adjustment / 100,
                    "reason": f"美联储{policy}",
                    "affected_sectors": ["整体市场", "北向资金", "外资"],
                    "is_direct": False
                }

        # 5. 检查低影响力关键词
        for kw in self.LOW_IMPACT_KEYWORDS:
            if kw.lower() in text:
                # 进一步判断是否为国内相关
                is_domestic = any(k.lower() in text for k in self.DOMESTIC_KEYWORDS)

                if is_domestic:
                    # 国内相关，减轻惩罚
                    return {
                        "adjustment": -10,
                        "coefficient": 0.9,
                        "reason": f"国内低影响力: {kw}",
                        "affected_sectors": [],
                        "is_direct": False
                    }
                else:
                    # 海外/娱乐，严重惩罚
                    return {
                        "adjustment": -35,
                        "coefficient": 0.65,
                        "reason": f"低影响力: {kw}",
                        "affected_sectors": [],
                        "is_direct": False
                    }

        # 6. 检查中东/地缘政治
        for kw in self.GEOPOLITICAL_KEYWORDS:
            if kw.lower() in text:
                # 检查是否与A股直接相关
                is_related = any(k.lower() in text for k in ["A股", "上证", "能源", "石油", "天然气", "油价"])
                if is_related:
                    return {
                        "adjustment": -10,
                        "coefficient": 0.9,
                        "reason": f"地缘相关: {kw}",
                        "affected_sectors": ["能源", "石油"],
                        "is_direct": False
                    }
                else:
                    return {
                        "adjustment": -20,
                        "coefficient": 0.8,
                        "reason": f"地缘事件: {kw}",
                        "affected_sectors": [],
                        "is_direct": False
                    }

        # 7. 国内市场新闻 - 不调整
        if any(k in text for k in ["A股", "上证", "深证", "沪深", "创业板", "科创板", "主板"]):
            return {
                "adjustment": 0,
                "coefficient": 1.0,
                "reason": "A股市场新闻",
                "affected_sectors": [],
                "is_direct": True
            }

        # 8. 港股联动 - 小调整
        if any(k in text for k in ["港股", "恒生", "H股", "AH股"]):
            return {
                "adjustment": -5,
                "coefficient": 0.95,
                "reason": "港股联动",
                "affected_sectors": ["AH股"],
                "is_direct": False
            }

        # 9. 默认：国内新闻不调整
        if any(d in text for d in ["中国", "国内", "政策", "经济"]):
            return {
                "adjustment": 0,
                "coefficient": 1.0,
                "reason": "国内新闻",
                "affected_sectors": [],
                "is_direct": False
            }

        # 10. 其他默认小调整
        return {
            "adjustment": -5,
            "coefficient": 0.95,
            "reason": "其他新闻",
            "affected_sectors": [],
            "is_direct": False
        }


# 全局单例
a_share_impact_classifier = AShareImpactClassifier()
