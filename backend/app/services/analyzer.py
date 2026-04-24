import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from app.config import settings
from app.schemas.news import NewsAnalysisResult, ExpectationDiffEnum

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """AI新闻分析服务 - 基于DeepSeek"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = settings.DEEPSEEK_MODEL

        if not self.api_key:
            logger.warning("未配置DeepSeek API Key，AI分析功能将不可用")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def analyze_news(self, title: str, content: str) -> Optional[NewsAnalysisResult]:
        """分析单条新闻"""
        if not self.client:
            return self._generate_fallback_result()

        prompt = self._build_prompt(title, content)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个专业的金融新闻分析师。你的任务是分析财经新闻的重要性、增量属性和预期差。

请始终以JSON格式输出，包含以下字段：
- importance_score: 整数，0-100的重要性评分
- is_incremental: 布尔值，是否包含新的、未被市场充分消化的信息
- expectation_diff: 字符串，值为"超预期"、"符合预期"、"低于预期"或"无法判断"
- key_points: 字符串数组，列出2-3个核心要点
- category: 字符串，分类，值为"行业"、"公司"、"宏观"、"市场"或"其他"

请直接输出JSON，不要包含其他文字。"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )

            result_text = response.choices[0].message.content.strip()
            return self._parse_response(result_text)

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return self._generate_fallback_result()

    def _build_prompt(self, title: str, content: str) -> str:
        """构建分析Prompt"""
        return f"""新闻标题：{title}

新闻内容：
{content if content else '(无详细内容)'}

请分析这条新闻的：
1. 重要性评分 (0-100)
2. 是否是增量信息（市场尚未充分反应的新信息）
3. 预期差（与市场预期相比）
4. 核心要点
5. 新闻分类

输出JSON格式。"""

    def _parse_response(self, response_text: str) -> Optional[NewsAnalysisResult]:
        """解析AI响应"""
        try:
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]

            json_str = json_str.strip()

            data = json.loads(json_str)

            expectation_diff = data.get("expectation_diff", "无法判断")
            if expectation_diff not in [e.value for e in ExpectationDiffEnum]:
                expectation_diff = "无法判断"

            return NewsAnalysisResult(
                importance_score=int(data.get("importance_score", 50)),
                is_incremental=bool(data.get("is_incremental", False)),
                expectation_diff=ExpectationDiffEnum(expectation_diff),
                key_points=data.get("key_points", [])[:3],
                category=data.get("category", "其他"),
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"解析AI响应失败: {e}, 响应内容: {response_text[:200]}")
            return self._generate_fallback_result()

    def _generate_fallback_result(self) -> NewsAnalysisResult:
        """生成默认结果（当API不可用时）"""
        return NewsAnalysisResult(
            importance_score=50,
            is_incremental=False,
            expectation_diff=ExpectationDiffEnum.UNCLEAR,
            key_points=["未能获取AI分析"],
            category="其他",
        )

    async def analyze_news_async(self, title: str, content: str) -> Optional[NewsAnalysisResult]:
        """异步分析新闻"""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_news, title, content)

    def batch_analyze(self, news_list: list) -> list:
        """批量分析新闻"""
        results = []
        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            result = self.analyze_news(title, content)
            if result:
                results.append(result)
            else:
                results.append(self._generate_fallback_result())
        return results
