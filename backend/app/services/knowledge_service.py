"""
概念知识库服务
管理板块-产业链-个股的映射关系
"""
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

# 内置概念知识库
BUILTIN_CONCEPTS: Dict[str, Dict] = {
    # 新能源汽车
    "新能源汽车": {
        "type": "sector",
        "parent": "汽车",
        "stocks": ["比亚迪", "宁德时代", "理想汽车", "小鹏汽车", "蔚来汽车", "吉利汽车", "长城汽车"],
        "keywords": ["电动车", "新能源汽车", "锂电", "动力电池", "充电桩", "新能源", "电车"],
        "industry_chain": ["上游锂矿", "中游电池", "下游整车"],
        "description": "新能源汽车产业链",
    },
    # 人工智能
    "人工智能": {
        "type": "sector",
        "parent": "科技",
        "stocks": ["科大讯飞", "海康威视", "寒武纪", "商汤科技", "百度", "阿里云"],
        "keywords": ["AI", "人工智能", "大模型", "机器学习", "深度学习", "算力", "AIGC", "ChatGPT"],
        "industry_chain": ["算力", "算法", "应用"],
        "description": "人工智能板块",
    },
    # 半导体
    "半导体": {
        "type": "sector",
        "parent": "科技",
        "stocks": ["中芯国际", "华虹半导体", "北方华创", "中微公司", "韦尔股份", "闻泰科技"],
        "keywords": ["半导体", "芯片", "晶圆", "集成电路", "光刻机", "封测", "IDM"],
        "industry_chain": ["设计", "制造", "封测", "设备"],
        "description": "半导体产业链",
    },
    # 医疗器械
    "医疗器械": {
        "type": "sector",
        "parent": "医药",
        "stocks": ["迈瑞医疗", "联影医疗", "乐普医疗", "微创医疗", "威高集团"],
        "keywords": ["医疗器械", "医疗设备", "耗材", "IVD", "体外诊断"],
        "industry_chain": ["高端设备", "耗材", "IVD"],
        "description": "医疗器械板块",
    },
    # 创新药
    "创新药": {
        "type": "sector",
        "parent": "医药",
        "stocks": ["恒瑞医药", "百济神州", "信达生物", "君实生物", "复星医药"],
        "keywords": ["创新药", "生物医药", "靶向药", "PD-1", "CAR-T", "ADC"],
        "industry_chain": ["研发", "临床", "上市"],
        "description": "创新药板块",
    },
    # 光伏
    "光伏": {
        "type": "sector",
        "parent": "新能源",
        "stocks": ["隆基绿能", "通威股份", "阳光电源", "晶澳科技", "天合光能", "TCL中环"],
        "keywords": ["光伏", "太阳能", "硅料", "硅片", "电池片", "组件", "TOPCon", "HJT"],
        "industry_chain": ["硅料", "硅片", "电池片", "组件", "逆变器"],
        "description": "光伏产业链",
    },
    # 风电
    "风电": {
        "type": "sector",
        "parent": "新能源",
        "stocks": ["金风科技", "明阳智能", "三峡能源", "节能风电", "东方电缆"],
        "keywords": ["风电", "风机", "海风", "陆风", "风电场"],
        "industry_chain": ["整机", "叶片", "塔筒", "海缆"],
        "description": "风电产业链",
    },
    # 储能
    "储能": {
        "type": "sector",
        "parent": "新能源",
        "stocks": ["宁德时代", "比亚迪", "阳光电源", "南都电源", "亿纬锂能", "派能科技"],
        "keywords": ["储能", "锂电池", "钠离子电池", "PCS", "BMS", "EMS"],
        "industry_chain": ["电芯", "PACK", "系统"],
        "description": "储能产业链",
    },
    # 低空经济
    "低空经济": {
        "type": "sector",
        "parent": "交运",
        "stocks": ["亿航智能", "小鹏汽车", "山河智能", "万丰奥威"],
        "keywords": ["低空经济", "eVTOL", "无人机", "飞行汽车", "低空"],
        "industry_chain": ["整机制造", "核心零部件", "运营服务"],
        "description": "低空经济新兴板块",
    },
    # 机器人
    "机器人": {
        "type": "sector",
        "parent": "制造",
        "stocks": ["绿的谐波", "汇川技术", "埃斯顿", "拓普集团", "三花智控", "石头科技"],
        "keywords": ["机器人", "工业机器人", "人形机器人", "减速器", "伺服电机", "协作机器人"],
        "industry_chain": ["核心零部件", "整机制造", "系统集成"],
        "description": "机器人产业链",
    },
    # 房地产
    "房地产": {
        "type": "sector",
        "parent": "地产",
        "stocks": ["万科A", "保利发展", "招商蛇口", "金地集团", "华侨城A"],
        "keywords": ["房地产", "地产", "楼市", "开发商", "房贷", "土地"],
        "industry_chain": ["开发", "施工", "销售"],
        "description": "房地产板块",
    },
    # 银行
    "银行": {
        "type": "sector",
        "parent": "金融",
        "stocks": ["工商银行", "建设银行", "中国银行", "农业银行", "招商银行", "兴业银行"],
        "keywords": ["银行", "商业银行", "信贷", "存款", "净息差"],
        "industry_chain": [],
        "description": "银行板块",
    },
    # 券商
    "券商": {
        "type": "sector",
        "parent": "金融",
        "stocks": ["中信证券", "华泰证券", "国泰君安", "海通证券", "广发证券"],
        "keywords": ["券商", "证券公司", "投行", "经纪业务", "财富管理"],
        "industry_chain": [],
        "description": "券商板块",
    },
    # 保险
    "保险": {
        "type": "sector",
        "parent": "金融",
        "stocks": ["中国平安", "中国人寿", "中国太保", "新华保险"],
        "keywords": ["保险", "寿险", "财险", "保额"],
        "industry_chain": [],
        "description": "保险板块",
    },
    # 白酒
    "白酒": {
        "type": "sector",
        "parent": "消费",
        "stocks": ["贵州茅台", "五粮液", "泸州老窖", "山西汾酒", "洋河股份"],
        "keywords": ["白酒", "酱香", "浓香", "清香", "高端白酒", "次高端"],
        "industry_chain": [],
        "description": "白酒板块",
    },
    # 消费电子
    "消费电子": {
        "type": "sector",
        "parent": "科技",
        "stocks": ["苹果概念", "华为概念", "小米集团", "立讯精密", "歌尔股份", "蓝思科技"],
        "keywords": ["消费电子", "手机", "电脑", "平板", "智能穿戴", "TWS"],
        "industry_chain": [],
        "description": "消费电子板块",
    },
    # 军工
    "军工": {
        "type": "sector",
        "parent": "制造",
        "stocks": ["中航沈飞", "中航西飞", "航发动力", "中航光电", "振华科技"],
        "keywords": ["军工", "国防", "航空", "航天", "船舶", "兵器"],
        "industry_chain": [],
        "description": "军工板块",
    },
    # 稀土
    "稀土": {
        "type": "sector",
        "parent": "矿产",
        "stocks": ["北方稀土", "盛和资源", "五矿稀土", "广晟有色"],
        "keywords": ["稀土", "有色金属", "钕铁硼", "镨钕", "永磁材料"],
        "industry_chain": ["矿山", "冶炼", "深加工"],
        "description": "稀土板块",
    },
    # 氢能源
    "氢能源": {
        "type": "sector",
        "parent": "新能源",
        "stocks": ["亿华通", "厚普股份", "雄韬股份", "潍柴动力"],
        "keywords": ["氢能源", "氢能", "燃料电池", "制氢", "储氢", "加氢"],
        "industry_chain": ["制氢", "储氢", "运氢", "加氢站"],
        "description": "氢能源产业链",
    },
    # 数据要素
    "数据要素": {
        "type": "sector",
        "parent": "科技",
        "stocks": ["科大讯飞", "电信运营商", "云赛智联", "深桑达A"],
        "keywords": ["数据要素", "数据确权", "数据交易", "数据安全", "隐私计算"],
        "industry_chain": [],
        "description": "数据要素概念板块",
    },
}


@dataclass
class ConceptMatch:
    """概念匹配结果"""
    concept_name: str
    concept_type: str
    relevance_score: float
    matched_keywords: List[str]
    related_stocks: List[str]


class KnowledgeBase:
    """概念知识库"""

    def __init__(self):
        self.concepts = BUILTIN_CONCEPTS.copy()
        self._build_index()

    def _build_index(self):
        """构建关键词索引"""
        self.keyword_to_concepts: Dict[str, List[str]] = {}
        self.stock_to_concepts: Dict[str, List[str]] = {}

        for concept_name, concept_data in self.concepts.items():
            # 关键词索引
            for keyword in concept_data.get("keywords", []):
                if keyword not in self.keyword_to_concepts:
                    self.keyword_to_concepts[keyword] = []
                self.keyword_to_concepts[keyword].append(concept_name)

            # 个股索引
            for stock in concept_data.get("stocks", []):
                if stock not in self.stock_to_concepts:
                    self.stock_to_concepts[stock] = []
                self.stock_to_concepts[stock].append(concept_name)

    def add_concept(self, concept_name: str, concept_data: Dict):
        """添加概念"""
        self.concepts[concept_name] = concept_data
        self._build_index()

    def find_concepts(self, keywords: List[str]) -> List[ConceptMatch]:
        """
        根据关键词查找相关概念

        Args:
            keywords: 关键词列表

        Returns:
            匹配的概念列表
        """
        concept_scores: Dict[str, Dict] = {}

        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 精确匹配关键词
            for kw, concepts in self.keyword_to_concepts.items():
                if keyword_lower in kw.lower() or kw.lower() in keyword_lower:
                    for concept_name in concepts:
                        if concept_name not in concept_scores:
                            concept_scores[concept_name] = {
                                "matched_keywords": [],
                                "score": 0.0,
                            }
                        concept_scores[concept_name]["matched_keywords"].append(kw)
                        concept_scores[concept_name]["score"] += 1.0

            # 完全匹配关键词
            if keyword in self.keyword_to_concepts:
                for concept_name in self.keyword_to_concepts[keyword]:
                    if concept_name not in concept_scores:
                        concept_scores[concept_name] = {
                            "matched_keywords": [],
                            "score": 0.0,
                        }
                    concept_scores[concept_name]["matched_keywords"].append(keyword)
                    concept_scores[concept_name]["score"] += 2.0

        # 计算归一化分数
        results = []
        max_score = max((s["score"] for s in concept_scores.values()), default=1.0)

        for concept_name, data in concept_scores.items():
            concept_data = self.concepts.get(concept_name, {})
            results.append(ConceptMatch(
                concept_name=concept_name,
                concept_type=concept_data.get("type", "sector"),
                relevance_score=data["score"] / max_score,
                matched_keywords=data["matched_keywords"],
                related_stocks=concept_data.get("stocks", []),
            ))

        # 按相关度排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    def find_stocks(self, keywords: List[str]) -> List[str]:
        """
        根据关键词查找相关个股

        Args:
            keywords: 关键词列表

        Returns:
            相关的个股列表
        """
        concepts = self.find_concepts(keywords)
        stocks_set: Set[str] = set()

        for concept in concepts:
            for stock in concept.related_stocks:
                stocks_set.add(stock)

        return list(stocks_set)

    def get_concept_stocks(self, concept_name: str) -> List[str]:
        """获取指定概念的相关个股"""
        concept = self.concepts.get(concept_name)
        if concept:
            return concept.get("stocks", [])
        return []

    def match_stocks(self, keywords: List[str], candidate_stocks: List[str] = None) -> List[Dict]:
        """
        匹配个股

        Args:
            keywords: 关键词列表
            candidate_stocks: 候选个股列表（用于限制范围）

        Returns:
            匹配结果列表
        """
        concepts = self.find_concepts(keywords)
        results = []

        for concept in concepts:
            for stock in concept.related_stocks:
                # 如果有候选列表，只返回候选中的
                if candidate_stocks and stock not in candidate_stocks:
                    continue

                results.append({
                    "stock": stock,
                    "concept": concept.concept_name,
                    "relevance_score": concept.relevance_score,
                    "matched_keywords": concept.matched_keywords,
                })

        # 去重并排序
        seen = set()
        unique_results = []
        for r in results:
            if r["stock"] not in seen:
                seen.add(r["stock"])
                unique_results.append(r)

        unique_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return unique_results


# 全局单例
knowledge_base = KnowledgeBase()
