"""
多阶段分析引擎 v2
实现 Prompt 体系 + 多阶段工作流
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from openai import OpenAI

from app.config import settings
from app.services.prompt_engine import prompt_engine
from app.services.rag_service import rag_service
from app.services.scoring_service import scoring_service
from app.services.a_share_impact import a_share_impact_classifier

logger = logging.getLogger(__name__)


class AnalysisStageResult:
    """分析阶段结果"""

    def __init__(self, stage: str, success: bool, data: Dict = None, error: str = None):
        self.stage = stage
        self.success = success
        self.data = data or {}
        self.error = error
        self.timestamp = datetime.now()


class NewsAnalyzerV2:
    """
    多阶段新闻分析引擎

    工作流:
    1. 事实抽取 (Fact Extraction)
    2. 增量判断 (Incremental Check)
    3. 影响推演 (Impact Analysis)
    4. 评分复核 (Scoring & Review)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = settings.DEEPSEEK_MODEL

        if not self.api_key:
            logger.warning("未配置 DeepSeek API Key，AI 分析功能将不可用")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

        self.prompt_engine = prompt_engine
        self.rag_service = rag_service
        self.scoring_service = scoring_service

    async def analyze(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行多阶段分析

        Args:
            news: {
                "id": int,
                "title": str,
                "content": str,
                "source": str,
                "pub_time": datetime,
            }

        Returns:
            完整分析结果
        """
        if not self.client:
            return self._generate_fallback_result(news)

        results = {}
        stages = []

        try:
            # 阶段一：事实抽取
            stage1 = await self._extract_facts(news)
            stages.append(stage1)
            if stage1.success:
                results["facts"] = stage1.data

            # 阶段二：增量判断 (使用 RAG)
            stage2 = await self._check_incremental(news, results.get("facts", {}))
            stages.append(stage2)
            if stage2.success:
                results["incremental"] = stage2.data

            # 阶段三：影响分析
            stage3 = await self._analyze_impact(news, results.get("facts", {}))
            stages.append(stage3)
            if stage3.success:
                results["impact"] = stage3.data

            # 阶段四：评分与分类
            stage4 = await self._score_and_classify(news, results)
            stages.append(stage4)
            if stage4.success:
                results["scoring"] = stage4.data

            # 整合结果
            final_result = self._build_final_result(news, results)

            logger.info(f"分析完成: news_id={news.get('id')}, score={final_result.get('final_score')}")
            return final_result

        except Exception as e:
            logger.error(f"分析失败: {e}")
            return self._generate_error_result(news, str(e), stages)

    async def _extract_facts(self, news: Dict[str, Any]) -> AnalysisStageResult:
        """阶段一：事实抽取"""
        try:
            prompt = self.prompt_engine.build_master_prompt(
                title=news.get("title", ""),
                content=news.get("content", ""),
                source=news.get("source", ""),
                pub_time=str(news.get("pub_time", "")),
            )

            response = await self._call_llm(
                prompt,
                system="你是一个专业的金融新闻分析师。你需要从新闻中抽取关键事实，并区分确认事实、推断事实和不确定信息。"
            )

            # 解析响应
            data = self._parse_json_response(response)
            if data is None:
                data = {"facts": {"confirmed": [], "inferred": [], "uncertain": []}}

            return AnalysisStageResult("fact_extraction", True, data)

        except Exception as e:
            logger.error(f"事实抽取失败: {e}")
            return AnalysisStageResult("fact_extraction", False, error=str(e))

    async def _check_incremental(
        self,
        news: Dict[str, Any],
        facts: Dict,
    ) -> AnalysisStageResult:
        """阶段二：增量判断"""
        try:
            # 查找相似历史新闻
            similar_news = await self.rag_service.find_similar(
                title=news.get("title", ""),
                content=news.get("content", ""),
                top_k=5,
            )

            # 构建增量判断 Prompt
            prompt = self.prompt_engine.build_incremental_prompt(
                current_news={
                    "title": news.get("title", ""),
                    "content": news.get("content", ""),
                },
                similar_news_history=similar_news,
            )

            response = await self._call_llm(
                prompt,
                system="你是一个专业的增量信息识别分析师。你需要判断新闻是否包含市场尚未充分消化的新信息。"
            )

            data = self._parse_json_response(response)

            # 使用 RAG 辅助判断
            if data:
                rag_result = await self.rag_service.check_incremental(
                    current_news=news,
                    similar_news=similar_news,
                )
                # 合并 RAG 结果
                if rag_result:
                    data["rag_analysis"] = rag_result

            if data is None:
                data = {"incremental_score": 50, "incremental_level": "unknown"}

            return AnalysisStageResult("incremental_check", True, data)

        except Exception as e:
            logger.error(f"增量判断失败: {e}")
            return AnalysisStageResult("incremental_check", False, error=str(e))

    async def _analyze_impact(
        self,
        news: Dict[str, Any],
        facts: Dict,
    ) -> AnalysisStageResult:
        """阶段三：影响分析"""
        try:
            prompt = self.prompt_engine.build_sentiment_prompt(
                news_facts=facts,
                affected_objects=[],
            )

            response = await self._call_llm(
                prompt,
                system="你是一个专业的市场影响分析师。你需要分析新闻对市场的影响方向（利好/利空/中性）和影响路径。"
            )

            data = self._parse_json_response(response)
            if data is None:
                data = {"sentiment_direction": "neutral", "impact_objects": []}

            return AnalysisStageResult("impact_analysis", True, data)

        except Exception as e:
            logger.error(f"影响分析失败: {e}")
            return AnalysisStageResult("impact_analysis", False, error=str(e))

    async def _score_and_classify(
        self,
        news: Dict[str, Any],
        analysis_results: Dict[str, Any],
    ) -> AnalysisStageResult:
        """阶段四：评分与分类"""
        try:
            facts = analysis_results.get("facts", {})
            incremental = analysis_results.get("incremental", {})
            impact = analysis_results.get("impact", {})

            # 是否为同花顺红字重要消息
            is_important = news.get("is_important", False)

            # 获取A股影响力调整分
            impact_result = a_share_impact_classifier.classify_impact(
                title=news.get("title", ""),
                content=news.get("content", "")
            )
            a_share_adjustment = impact_result["adjustment"]

            # 使用评分服务计算最终分数
            # 从 impact 结果中获取 sentiment_score
            sentiment_score = impact.get("sentiment_score", 50)

            score_result = self.scoring_service.score(
                importance_score=incremental.get("importance_score", 50),
                incremental_score=incremental.get("incremental_score", 50),
                expectation_score=incremental.get("expectation_score", 50),
                scope_score=incremental.get("scope_score", 50),
                source_confidence_score=50,  # 来源可信度
                market_reaction_score=50,  # 行情反应
                sentiment_score=sentiment_score,  # 利好利空评分
                is_important=is_important,
                a_share_impact_adjustment=a_share_adjustment,
            )

            # 分类
            classification_prompt = self.prompt_engine.build_classification_prompt(
                title=news.get("title", ""),
                content=news.get("content", ""),
                source=news.get("source", ""),
            )

            classification_response = await self._call_llm(
                classification_prompt,
                system="你是一个专业的新闻分类分析师。你需要将新闻分为一级和二级分类。"
            )

            classification = self._parse_json_response(classification_response)

            data = {
                "score_result": {
                    "final_score": score_result.final_score,
                    "subscores": score_result.subscores,
                    "level": score_result.level,
                    "confidence": score_result.confidence,
                    "need_manual_review": score_result.need_manual_review,
                    "review_reasons": score_result.review_reasons,
                },
                "classification": classification or {},
            }

            return AnalysisStageResult("scoring", True, data)

        except Exception as e:
            logger.error(f"评分失败: {e}")
            return AnalysisStageResult("scoring", False, error=str(e))

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        """调用 LLM"""
        if not self.client:
            raise RuntimeError("LLM client not initialized")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析 JSON 响应"""
        try:
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"JSON 解析失败: {e}, 响应: {response[:200]}")
            return None

    def _build_final_result(self, news: Dict, results: Dict) -> Dict[str, Any]:
        """构建最终结果"""
        scoring = results.get("scoring", {}).get("score_result", {})
        classification = results.get("scoring", {}).get("classification", {})
        incremental = results.get("incremental", {})
        impact = results.get("impact", {})

        return {
            "news_id": news.get("id"),
            "title": news.get("title"),

            # 分类
            "news_type": classification.get("primary_type", "其他"),
            "news_subtype": classification.get("secondary_type", ""),
            "classification_confidence": classification.get("classification_confidence", 0.5),

            # 多维度评分
            "scores": scoring.get("subscores", {}),

            # 最终评分
            "final_score": scoring.get("final_score", 50),
            "news_level": scoring.get("level", "normal"),

            # 增量信息
            "incremental_level": incremental.get("incremental_level", "unknown"),
            "new_facts": incremental.get("new_facts", []),
            "historical_known_facts": incremental.get("historical_known_facts", []),

            # 影响对象
            "affected_objects": impact.get("impact_objects", []),

            # 置信度与复核
            "confidence": scoring.get("confidence", 0.5),
            "need_manual_review": scoring.get("need_manual_review", True),
            "review_reasons": scoring.get("review_reasons", []),

            # 分析详情
            "facts": results.get("facts", {}),
            "impact": impact,

            "analyzed_at": datetime.now().isoformat(),
        }

    def _generate_fallback_result(self, news: Dict) -> Dict[str, Any]:
        """生成默认结果"""
        return {
            "news_id": news.get("id"),
            "title": news.get("title"),
            "news_type": "其他",
            "news_subtype": "",
            "scores": {
                "importance": 50,
                "incremental": 50,
                "expectation": 50,
                "scope": 50,
                "source_confidence": 50,
                "market_reaction": 50,
            },
            "final_score": 50,
            "news_level": "normal",
            "incremental_level": "unknown",
            "new_facts": [],
            "historical_known_facts": [],
            "affected_objects": [],
            "confidence": 0.3,
            "need_manual_review": True,
            "review_reasons": ["API Key 未配置"],
            "facts": {},
            "impact": {},
            "analyzed_at": datetime.now().isoformat(),
        }

    def _generate_error_result(
        self,
        news: Dict,
        error: str,
        stages: List[AnalysisStageResult],
    ) -> Dict[str, Any]:
        """生成错误结果"""
        failed_stages = [s.stage for s in stages if not s.success]

        return {
            "news_id": news.get("id"),
            "title": news.get("title"),
            "error": error,
            "failed_stages": failed_stages,
            "final_score": 50,
            "news_level": "normal",
            "confidence": 0.1,
            "need_manual_review": True,
            "review_reasons": [f"分析阶段失败: {', '.join(failed_stages)}"],
            "analyzed_at": datetime.now().isoformat(),
        }


# 全局单例
analyzer_v2 = NewsAnalyzerV2()
