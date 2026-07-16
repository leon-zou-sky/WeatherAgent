"""
Skill 6: 知识检索
支持两种模式：
1. 关键词匹配（兜底）
2. 向量检索（Milvus，优先）
"""

import csv
import logging
from pathlib import Path

from app.models.schemas import KnowledgeResult

logger = logging.getLogger(__name__)

# 配置
_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "weather_feedback_enriched_v3.csv"
_MILVUS_DB = str(Path(__file__).resolve().parent.parent.parent / "milvus_weather.db")
_COLLECTION = "weather_feedback"
_MODEL_PATH = str(Path(__file__).resolve().parent.parent.parent / "models" / "bge-large-zh-v1.5")

# 缓存
_kb_cache: list[dict] | None = None
_milvus_client = None
_embed_model = None


# ============ Embedding 模型 ============

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer(_MODEL_PATH)
            logger.info(f"[Knowledge] Embedding 模型加载成功: {_MODEL_PATH}")
        except Exception as e:
            logger.warning(f"[Knowledge] Embedding 模型加载失败: {e}")
    return _embed_model


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """批量生成 Embedding"""
    model = _get_embed_model()
    if model is None:
        return []
    return model.encode(texts, normalize_embeddings=True).tolist()


# ============ Milvus 向量检索 ============

def _get_milvus_client():
    global _milvus_client
    if _milvus_client is None:
        try:
            from pymilvus import MilvusClient
            _milvus_client = MilvusClient(_MILVUS_DB)
            logger.info(f"[Knowledge] Milvus 连接成功")
        except Exception as e:
            logger.warning(f"[Knowledge] Milvus 连接失败: {e}")
    return _milvus_client


def _vector_search(query: str, top_k: int = 3) -> list[KnowledgeResult]:
    """向量检索"""
    client = _get_milvus_client()
    model = _get_embed_model()
    if client is None or model is None:
        return []

    try:
        # 确保 Collection 已加载
        if not client.has_collection(_COLLECTION):
            return []
        client.load_collection(_COLLECTION)

        query_vec = model.encode([query], normalize_embeddings=True).tolist()
        results = client.search(
            collection_name=_COLLECTION,
            data=query_vec,
            limit=top_k,
            output_fields=["module", "problem_pattern", "problem_desc", "root_cause", "solution", "tags", "severity"],
        )

        items = []
        for hit in results[0]:
            entity = hit["entity"]
            items.append(
                KnowledgeResult(
                    content=f"[{entity['module']}][{entity['problem_pattern']}] {entity['problem_desc']}",
                    solution=entity["solution"],
                    score=round(hit["distance"], 4),
                )
            )
        return items
    except Exception as e:
        logger.warning(f"[Knowledge] 向量检索失败: {e}")
        return []


# ============ 关键词匹配（兜底） ============

def _load_csv() -> list[dict]:
    global _kb_cache
    if _kb_cache is not None:
        return _kb_cache

    if not _CSV_PATH.exists():
        _kb_cache = []
        return _kb_cache

    _kb_cache = []
    with open(_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            _kb_cache.append({
                "module": row.get("module", ""),
                "problem_pattern": row.get("problem_pattern", ""),
                "problem_desc": row.get("problem_desc", ""),
                "root_cause": row.get("root_cause", ""),
                "solution": row.get("solution", ""),
                "tags": row.get("tags", ""),
                "severity": row.get("severity", ""),
            })
    return _kb_cache


def _extract_keywords(text: str) -> list[str]:
    keywords = set()
    for w in text.split():
        if len(w) >= 2:
            keywords.add(w.lower())
    text_clean = text.replace(" ", "").lower()
    for n in (4, 3, 2):
        for i in range(len(text_clean) - n + 1):
            keywords.add(text_clean[i:i+n])
    return list(keywords)


_PATTERN_KEYWORDS = {
    "数据偏差": ["不准", "不对", "偏差", "误差", "偏高", "偏低", "偏大", "偏小", "不符", "不一致", "对不上"],
    "时效延迟": ["延迟", "不及时", "慢", "晚", "迟", "没更新", "更新慢"],
    "时空误差": ["位置", "定位", "落区", "时间", "早了", "晚了"],
    "认知偏差": ["不懂", "什么意思", "怎么算", "为啥", "为什么", "怎么看"],
    "体验缺陷": ["闪退", "卡顿", "耗电", "打不开", "崩溃", "bug"],
}


def _infer_pattern(query: str) -> str | None:
    for pattern, keywords in _PATTERN_KEYWORDS.items():
        if any(kw in query for kw in keywords):
            return pattern
    return None


def _calc_score(query: str, item: dict) -> float:
    score = 0.0
    query_kws = _extract_keywords(query)
    inferred_pattern = _infer_pattern(query)

    desc = item["problem_desc"].lower()
    desc_hits = sum(1 for kw in query_kws if kw in desc)
    score += min(desc_hits * 0.15, 0.30)

    tags = item["tags"].lower()
    tag_hits = sum(1 for kw in query_kws if kw in tags)
    score += min(tag_hits * 0.125, 0.25)

    pattern = item["problem_pattern"]
    if inferred_pattern and pattern == inferred_pattern:
        score += 0.20
    elif pattern in query:
        score += 0.15

    cause = item["root_cause"].lower()
    cause_hits = sum(1 for kw in query_kws if kw in cause)
    score += min(cause_hits * 0.05, 0.10)

    if item["module"] in query:
        score += 0.10

    severity = item.get("severity", "medium")
    severity_weight = {"high": 1.1, "medium": 1.0, "low": 0.9}.get(severity, 1.0)

    return min(score * severity_weight, 1.0)


def _keyword_search(query: str, top_k: int = 3) -> list[KnowledgeResult]:
    kb = _load_csv()
    if not kb:
        return []

    results = []
    for item in kb:
        score = _calc_score(query, item)
        if score > 0:
            results.append(
                KnowledgeResult(
                    content=f"[{item['module']}][{item['problem_pattern']}] {item['problem_desc']}",
                    solution=item["solution"],
                    score=score,
                )
            )

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:top_k]


# ============ 对外接口 ============

async def search_knowledge(query: str, top_k: int = 3) -> list[KnowledgeResult]:
    """
    检索相似案例
    优先用向量检索，失败则降级为关键词匹配
    """
    # 优先向量检索
    results = _vector_search(query, top_k)
    if results:
        logger.info(f"[Knowledge] 向量检索命中 {len(results)} 条")
        return results

    # 降级关键词匹配
    results = _keyword_search(query, top_k)
    logger.info(f"[Knowledge] 关键词匹配命中 {len(results)} 条")
    return results
