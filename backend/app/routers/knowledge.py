"""
知识库管理 API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import KnowledgeConcept
from app.schemas.analysis import KnowledgeConceptCreate
from app.services.knowledge_service import knowledge_base, ConceptMatch

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/concepts", response_model=List[dict])
def get_concepts():
    """获取所有内置概念"""
    concepts = []
    for name, data in knowledge_base.concepts.items():
        concepts.append({
            "name": name,
            "type": data.get("type"),
            "stocks_count": len(data.get("stocks", [])),
            "keywords": data.get("keywords", []),
            "description": data.get("description"),
        })
    return concepts


@router.get("/concepts/{concept_name}", response_model=dict)
def get_concept(concept_name: str):
    """获取指定概念详情"""
    concept = knowledge_base.concepts.get(concept_name)
    if not concept:
        raise HTTPException(status_code=404, detail="概念不存在")
    return {
        "name": concept_name,
        **concept,
    }


@router.post("/concepts")
def create_concept(
    concept: KnowledgeConceptCreate,
    db: Session = Depends(get_db),
):
    """创建自定义概念（持久化到数据库）"""
    try:
        # 保存到数据库
        db_concept = KnowledgeConcept(
            concept_name=concept.concept_name,
            concept_type=concept.concept_type,
            parent_concept=concept.parent_concept,
            related_stocks=concept.related_stocks,
            keywords=concept.keywords,
            description=concept.description,
        )
        db.add(db_concept)
        db.commit()

        # 同时添加到内存知识库
        knowledge_base.add_concept(concept.concept_name, {
            "type": concept.concept_type,
            "parent": concept.parent_concept,
            "stocks": concept.related_stocks,
            "keywords": concept.keywords,
            "description": concept.description,
        })

        return {"message": "概念创建成功", "name": concept.concept_name}

    except Exception as e:
        logger.error(f"创建概念失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match/stocks", response_model=List[dict])
def match_stocks(
    keywords: str = Query(..., description="逗号分隔的关键词"),
    candidates: Optional[str] = Query(None, description="逗号分隔的候选个股"),
):
    """
    根据关键词匹配个股

    Args:
        keywords: 关键词，多个用逗号分隔
        candidates: 候选个股列表，多个用逗号分隔
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    candidate_list = [c.strip() for c in candidates.split(",") if c.strip()] if candidates else None

    matches = knowledge_base.match_stocks(keyword_list, candidate_list)

    return [
        {
            "stock": m["stock"],
            "concept": m["concept"],
            "relevance_score": round(m["relevance_score"], 2),
            "matched_keywords": m["matched_keywords"],
        }
        for m in matches
    ]


@router.get("/match/concepts", response_model=List[dict])
def match_concepts(
    keywords: str = Query(..., description="逗号分隔的关键词"),
):
    """
    根据关键词匹配概念

    Args:
        keywords: 关键词，多个用逗号分隔
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    matches = knowledge_base.find_concepts(keyword_list)

    return [
        {
            "concept_name": m.concept_name,
            "concept_type": m.concept_type,
            "relevance_score": round(m.relevance_score, 2),
            "matched_keywords": m.matched_keywords,
            "related_stocks": m.related_stocks,
        }
        for m in matches
    ]


@router.get("/stocks/{concept_name}", response_model=List[str])
def get_concept_stocks(concept_name: str):
    """获取指定概念的个股列表"""
    stocks = knowledge_base.get_concept_stocks(concept_name)
    if not stocks:
        raise HTTPException(status_code=404, detail="概念不存在或无相关个股")
    return stocks


@router.get("/search")
def search_knowledge(
    q: str = Query(..., description="搜索关键词"),
    type: Optional[str] = Query(None, description="概念类型过滤"),
):
    """
    搜索知识库

    Args:
        q: 搜索关键词
        type: 概念类型过滤 (sector/industry/stock)
    """
    # 简单实现：搜索概念名称和关键词
    q_lower = q.lower()
    results = []

    for name, data in knowledge_base.concepts.items():
        if type and data.get("type") != type:
            continue

        # 名称匹配
        name_match = q_lower in name.lower()

        # 关键词匹配
        keywords = data.get("keywords", [])
        keyword_match = any(q_lower in kw.lower() for kw in keywords)

        # 个股匹配
        stocks = data.get("stocks", [])
        stock_match = any(q_lower in s.lower() for s in stocks)

        if name_match or keyword_match or stock_match:
            results.append({
                "name": name,
                "type": data.get("type"),
                "match_type": "name" if name_match else ("keyword" if keyword_match else "stock"),
                "stocks_count": len(stocks),
                "keywords": keywords[:5],  # 只返回前5个关键词
            })

    return results


@router.get("/db/concepts", response_model=List[dict])
def get_db_concepts(db: Session = Depends(get_db)):
    """从数据库获取自定义概念"""
    concepts = db.query(KnowledgeConcept).all()
    return [
        {
            "id": c.id,
            "concept_name": c.concept_name,
            "concept_type": c.concept_type,
            "parent_concept": c.parent_concept,
            "related_stocks": c.related_stocks,
            "keywords": c.keywords,
            "description": c.description,
            "hit_count": c.hit_count,
        }
        for c in concepts
    ]


@router.delete("/db/concepts/{concept_id}")
def delete_db_concept(concept_id: int, db: Session = Depends(get_db)):
    """删除数据库中的概念"""
    concept = db.query(KnowledgeConcept).filter(KnowledgeConcept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="概念不存在")

    db.delete(concept)
    db.commit()

    return {"message": "概念已删除"}
