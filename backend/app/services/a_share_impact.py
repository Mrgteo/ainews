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

    # 直接利好A股（需要按顺序检查，注意长短匹配）
    # 注意：短的关键词要放在后面，避免误匹配
    DIRECT_POSITIVE = [
        # 政策/监管类
        "降准", "降息", "证监会", "交易所", "发改委", "央行", "财政部",
        "注册制", "IPO", "并购重组", "北向资金", "社保", "公募",
        "救市", "护盘", "松绑", "扶持", "银保监会", "金融监管",
        "完善制度", "改革", "专项行动方案", "财政补贴", "税收优惠",
        "政府采购", "以旧换新", "设备更新", "试点", "产业化",

        # 个股利好类型（根据用户提供的消息类型库）
        # 重大资产重组
        "资产注入", "发行股份购买资产", "资产置换", "重组方案获批",
        "重组完成", "恢复审核", "重大资产重组",

        # 并购收购
        "收购", "并购", "控股股权", "取得控制权", "股权收购",
        "现金收购", "产业协同",

        # 控制权变更
        "控制权变更", "国资入主", "央企入主", "产业资本入主",
        "战略投资", "实控人变更", "控股股东变更", "表决权委托",

        # 业绩相关
        "业绩暴增", "净利润大幅增长", "扭亏为盈", "业绩超预期",
        "扣非净利润增长", "创历史新高", "业绩预增", "净利润增长",
        "净利润",  # 单独添加，因为可能被数字隔开

        # 订单合同
        "重大合同", "中标", "大额订单", "采购协议", "长期供货",
        "进入供应链", "客户定点",

        # 产品/技术
        "产品获批", "注册证", "临床成功", "通过认证", "量产",
        "技术突破", "商业化", "新品发布", "量产成功",

        # 回购增持
        "回购", "注销式回购", "股东增持", "高管增持",  # 增持要放在"支持"前面
        "承诺不减持", "延长限售期",

        # 股权激励/分红
        "股权激励", "员工持股", "特别分红", "高股息",

        # 交易状态改善（这些是利好）
        "撤销退市风险警示", "撤销其他风险警示", "撤销风险警示",
        "纳入沪深港通", "纳入指数", "恢复上市", "复牌",

        # 供需/价格
        "价格上涨", "供不应求", "需求爆发", "排产上调",
        "库存下降", "限产", "供给收缩",

        # 技术突破
        "技术突破", "全球首款", "国内首创",
        "良率提升", "成本下降",

        # 短关键词放最后（避免误匹配）
        "鼓励", "增持", "摘帽", "支持",
    ]

    # 直接利空A股（需要按顺序检查，注意长短匹配）
    DIRECT_NEGATIVE = [
        # 退市风险
        "退市风险警示", "实施退市风险", "*ST", "ST", "终止上市",
        "退市整理期", "可能被终止上市", "实施退市",

        # 监管处罚
        "监管调查", "问询函", "行政处罚", "纪律处分", "监管函",
        "警示函", "涉嫌", "被立案",

        # 业绩暴雷
        "业绩预亏", "净利润亏损", "由盈转亏", "亏损扩大",
        "业绩暴雷", "商誉减值", "资产减值",

        # 审计非标
        "审计非标", "无法表示意见", "否定意见", "保留意见",
        "持续经营能力存在重大不确定性",

        # 并购重组失败
        "重组失败", "终止重大资产重组", "终止收购", "重组未通过",
        "撤回申请", "控制权变更失败",

        # 股东减持
        "减持", "清仓式减持", "质押爆仓", "司法冻结",
        "轮候冻结", "司法拍卖", "债务违约", "资金紧张",

        # 实控人/高管出事
        "实控人被留置", "董事长失联", "高管被调查",
        "被采取强制措施", "资金占用", "违规担保",

        # 经营风险
        "停产整改", "安全事故", "产品召回", "合同终止",
        "订单取消", "客户流失", "库存积压", "产能过剩",

        # 行业利空
        "补贴退坡", "集采", "医保控费", "价格战",
        "出口管制", "制裁", "反倾销", "监管收紧",

        # 审计/财务问题
        "非标意见", "财务造假", "信披违规",

        # 短关键词放最后
        "处罚", "立案", "收紧", "核查", "通报", "批评",
        "限制", "叫停", "暂停IPO", "打压",
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

        # 0. 特殊处理：先检查"撤销"类关键词，因为它们包含"退市风险警示"等词但实际是利好
        revoke_keywords = ["撤销退市风险警示", "撤销其他风险警示", "撤销风险警示", "申请撤销"]
        for kw in revoke_keywords:
            if kw.lower() in text:
                return {
                    "adjustment": 0,
                    "coefficient": 1.0,
                    "reason": f"直接利好A股: {kw}",
                    "affected_sectors": ["整体市场"],
                    "is_direct": True
                }

        # 1. 检查直接利好 - 按关键词长度从长到短排序，避免短词误匹配
        sorted_positive = sorted(self.DIRECT_POSITIVE, key=len, reverse=True)
        for kw in sorted_positive:
            if kw.lower() in text:
                # 避免"支持率"被误匹配为"支持"
                if kw == "支持" and "支持率" in text:
                    continue
                return {
                    "adjustment": 0,
                    "coefficient": 1.0,
                    "reason": f"直接利好A股: {kw}",
                    "affected_sectors": ["整体市场"],
                    "is_direct": True
                }

        # 2. 检查直接利空 - 按关键词长度从长到短排序
        sorted_negative = sorted(self.DIRECT_NEGATIVE, key=len, reverse=True)
        for kw in sorted_negative:
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
