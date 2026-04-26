"""
Prompt 引擎服务
管理所有模块化 Prompt 模板，支持动态渲染
"""
import os
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.config import settings

# Prompt 模板目录
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptEngine:
    """模块化 Prompt 管理引擎"""

    def __init__(self):
        self.templates: Dict[str, str] = {}
        self._load_templates()

    def _load_templates(self):
        """加载所有 Prompt 模板"""
        template_files = [
            "master.txt",
            "classification.txt",
            "importance.txt",
            "incremental.txt",
            "expectation.txt",
            "sentiment.txt",
            "mapping.txt",
            "case_study.txt",
            "counter_cases.txt",
        ]

        for filename in template_files:
            template_path = PROMPTS_DIR / filename
            if template_path.exists():
                template_name = filename.replace(".txt", "")
                with open(template_path, "r", encoding="utf-8") as f:
                    self.templates[template_name] = f.read()

    def get_template(self, name: str) -> Optional[str]:
        """获取指定模板"""
        return self.templates.get(name)

    def render(self, template_name: str, **kwargs) -> str:
        """
        渲染模板，替换变量

        用法:
            prompt = engine.render("master",
                                  title="新闻标题",
                                  content="新闻内容")
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # 替换变量
        rendered = template
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, (dict, list)):
                # 对于复杂类型，转换为格式化字符串
                formatted_value = self._format_complex_value(value)
                rendered = rendered.replace(placeholder, formatted_value)
            else:
                rendered = rendered.replace(placeholder, str(value))

        return rendered

    def _format_complex_value(self, value: Any) -> str:
        """格式化复杂类型值"""
        if isinstance(value, dict):
            parts = []
            for k, v in value.items():
                parts.append(f"- {k}: {v}")
            return "\n".join(parts) if parts else "(无)"
        elif isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                return json.dumps(value, ensure_ascii=False, indent=2)
            return "\n".join(f"- {item}" for item in value) if value else "(无)"
        return str(value) if value else "(无)"

    def build_master_prompt(
        self,
        title: str,
        content: str,
        source: str = "",
        pub_time: str = "",
        similar_news: List[Dict] = None,
        market_context: Dict = None,
        candidate_objects: List[str] = None,
    ) -> str:
        """构建总控 Prompt"""
        return self.render(
            "master",
            title=title,
            content=content,
            source=source,
            pub_time=pub_time,
            similar_news=self._format_complex_value(similar_news or []),
            market_context=self._format_complex_value(market_context or {}),
            candidate_objects=self._format_complex_value(candidate_objects or []),
        )

    def build_classification_prompt(
        self,
        title: str,
        content: str,
        source: str = "",
        keywords: List[str] = None,
    ) -> str:
        """构建分类 Prompt"""
        return self.render(
            "classification",
            title=title,
            content=content,
            source=source,
            keywords=self._format_complex_value(keywords or []),
        )

    def build_importance_prompt(
        self,
        facts: Dict,
        news_type: str,
        publisher: str = "",
        impact_scope: str = "",
        key_data: str = "",
        market_background: str = "",
    ) -> str:
        """构建重要性评分 Prompt"""
        return self.render(
            "importance",
            facts=self._format_complex_value(facts),
            news_type=news_type,
            publisher=publisher,
            impact_scope=impact_scope,
            key_data=key_data,
            market_background=market_background,
        )

    def build_incremental_prompt(
        self,
        current_news: Dict,
        similar_news_history: List[Dict] = None,
        historical_known_facts: List[str] = None,
    ) -> str:
        """构建增量识别 Prompt"""
        return self.render(
            "incremental",
            current_news=self._format_complex_value(current_news),
            similar_news_history=self._format_complex_value(similar_news_history or []),
            historical_known_facts=self._format_complex_value(historical_known_facts or []),
        )

    def build_expectation_prompt(
        self,
        news_facts: Dict,
        market_expectation: str = "",
        historical_data: str = "",
        market_reaction: str = "",
    ) -> str:
        """构建预期差分析 Prompt"""
        return self.render(
            "expectation",
            news_facts=self._format_complex_value(news_facts),
            market_expectation=market_expectation,
            historical_data=historical_data,
            market_reaction=market_reaction,
        )

    def build_sentiment_prompt(
        self,
        news_facts: Dict,
        affected_objects: List[Dict] = None,
        industry_background: str = "",
        policy_direction: str = "",
    ) -> str:
        """构建利好/利空判断 Prompt"""
        return self.render(
            "sentiment",
            news_facts=self._format_complex_value(news_facts),
            affected_objects=self._format_complex_value(affected_objects or []),
            industry_background=industry_background,
            policy_direction=policy_direction,
        )

    def build_mapping_prompt(
        self,
        keywords: List[str],
        local_concept_base: Dict = None,
        candidate_objects: List[str] = None,
    ) -> str:
        """构建板块/个股映射 Prompt"""
        return self.render(
            "mapping",
            keywords=self._format_complex_value(keywords),
            local_concept_base=self._format_complex_value(local_concept_base or {}),
            candidate_objects=self._format_complex_value(candidate_objects or []),
        )

    def build_case_study_prompt(
        self,
        current_title: str,
        current_content: str,
        examples: List[Dict] = None,
    ) -> str:
        """构建案例库 Prompt (Few-shot)"""
        return self.render(
            "case_study",
            current_title=current_title,
            current_content=current_content,
            examples=self._format_complex_value(examples or []),
        )

    def build_counter_cases_prompt(
        self,
        analysis_result: Dict,
    ) -> str:
        """构建反例库检查 Prompt"""
        return self.render(
            "counter_cases",
            analysis_result=self._format_complex_value(analysis_result),
        )


# 全局单例
prompt_engine = PromptEngine()
