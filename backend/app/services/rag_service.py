"""
RAG 服务 - 增量识别子系统
基于向量相似度召回历史相似新闻
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RAGService:
    """增量识别 RAG 子系统"""

    def __init__(self):
        # 简单实现：使用内存存储 + 关键词匹配
        # 生产环境应使用 ChromaDB / pgvector / Milvus
        self.embedding_cache = {}
        self.news_store = []  # 简化版新闻存储

    async def add_news(self, news_id: int, title: str, content: str, embedding: List[float] = None):
        """添加新闻到向量库"""
        # 简化实现：存储文本用于后续相似度计算
        self.news_store.append({
            "news_id": news_id,
            "title": title,
            "content": content[:500] if content else "",  # 截断存储
            "embedding": embedding,
            "indexed_at": datetime.now(),
        })

    async def find_similar(
        self,
        title: str,
        content: str,
        top_k: int = 10,
        days_back: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        召回相似新闻

        Args:
            title: 新闻标题
            content: 新闻正文
            top_k: 返回数量
            days_back: 搜索最近多少天的新闻

        Returns:
            相似新闻列表
        """
        if not self.news_store:
            return []

        # 计算文本相似度（简化实现）
        query_text = f"{title} {content[:200] if content else ''}"
        query_keywords = self._extract_keywords(query_text)

        scored_news = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for news in self.news_store:
            if news["indexed_at"] < cutoff_date:
                continue

            # 计算关键词重叠度
            news_keywords = self._extract_keywords(f"{news['title']} {news['content']}")
            similarity = self._calculate_similarity(query_keywords, news_keywords)

            scored_news.append({
                "news_id": news["news_id"],
                "title": news["title"],
                "content": news["content"],
                "similarity_score": similarity,
                "indexed_at": news["indexed_at"].isoformat(),
            })

        # 排序并返回 top_k
        scored_news.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_news[:top_k]

    def _extract_keywords(self, text: str) -> set:
        """提取关键词（简化实现）"""
        if not text:
            return set()

        # 简单分词：去除停用词后的字符序列
        stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

        # 提取2-6字的词组
        text = text.lower()
        words = set()
        for length in [2, 3, 4, 5, 6]:
            for i in range(len(text) - length + 1):
                word = text[i:i+length]
                if word not in stopwords and not word.isdigit():
                    words.add(word)

        return words

    def _calculate_similarity(self, keywords1: set, keywords2: set) -> float:
        """计算关键词重叠度"""
        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def check_incremental(
        self,
        current_news: Dict[str, Any],
        similar_news: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        判断增量属性

        Args:
            current_news: 当前新闻 {"title": ..., "content": ...}
            similar_news: 相似历史新闻列表

        Returns:
            增量判断结果
        """
        if not similar_news:
            return {
                "incremental_level": "unknown",
                "new_facts": [],
                "historical_known_facts": [],
                "judgment_basis": "历史上下文不足",
                "need_manual_review": True,
            }

        current_text = f"{current_news.get('title', '')} {current_news.get('content', '')}"
        current_keywords = self._extract_keywords(current_text)

        # 分析与每条相似新闻的关系
        known_facts = set()
        repetition_count = 0

        for news in similar_news:
            if news["similarity_score"] > 0.6:
                # 高度相似，检查是否重复
                news_text = f"{news.get('title', '')} {news.get('content', '')}"
                news_keywords = self._extract_keywords(news_text)

                # 找出已知事实
                overlap = current_keywords & news_keywords
                if len(overlap) > 5:
                    known_facts.update(overlap)

                if news["similarity_score"] > 0.8:
                    repetition_count += 1

        # 判断增量等级
        new_keywords = current_keywords - known_facts
        new_ratio = len(new_keywords) / len(current_keywords) if current_keywords else 0

        if repetition_count >= 3 or new_ratio < 0.2:
            incremental_level = "none"
        elif repetition_count >= 1 or new_ratio < 0.4:
            incremental_level = "low"
        elif new_ratio < 0.6:
            incremental_level = "medium"
        else:
            incremental_level = "high"

        return {
            "incremental_level": incremental_level,
            "new_facts": list(new_keywords)[:10],  # 最多10个
            "historical_known_facts": list(known_facts)[:10],
            "is_repetition": repetition_count >= 3,
            "new_ratio": round(new_ratio, 2),
            "similar_news_count": len(similar_news),
            "similarity_scores": [s["similarity_score"] for s in similar_news[:5]],
            "judgment_basis": f"新关键词比例: {new_ratio:.1%}, 相似新闻数: {len(similar_news)}, 高相似重复: {repetition_count}",
            "need_manual_review": incremental_level in ["none", "low"],
        }


# 全局单例
rag_service = RAGService()
