"""
CSV 数据导入 Milvus
用法: python -m app.skills.milvus_loader
"""

import csv
from pathlib import Path

from pymilvus import MilvusClient, DataType

# 配置
_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "weather_feedback_enriched_v3.csv"
_MILVUS_DB = str(Path(__file__).resolve().parent.parent.parent / "milvus_weather.db")
_COLLECTION = "weather_feedback"
_EMBEDDING_DIM = 1024  # BGE-large-zh-v1.5 维度


def _get_client() -> MilvusClient:
    return MilvusClient(_MILVUS_DB)


def _build_embed_text(row: dict) -> str:
    """拼接文本用于 Embedding"""
    parts = [
        row.get("problem_desc", ""),
        row.get("root_cause", ""),
        row.get("solution", ""),
        row.get("tags", ""),
    ]
    return " ".join(p for p in parts if p)


def create_collection(client: MilvusClient):
    """创建 Collection"""
    # 如果已存在则删除
    if client.has_collection(_COLLECTION):
        client.drop_collection(_COLLECTION)
        print(f"已删除旧 Collection: {_COLLECTION}")

    schema = client.create_schema(auto_id=True, enable_dynamic_field=False)

    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("module", DataType.VARCHAR, max_length=32)
    schema.add_field("problem_pattern", DataType.VARCHAR, max_length=32)
    schema.add_field("problem_desc", DataType.VARCHAR, max_length=512)
    schema.add_field("root_cause", DataType.VARCHAR, max_length=512)
    schema.add_field("solution", DataType.VARCHAR, max_length=512)
    schema.add_field("tags", DataType.VARCHAR, max_length=128)
    schema.add_field("severity", DataType.VARCHAR, max_length=16)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=_EMBEDDING_DIM)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )

    client.create_collection(
        collection_name=_COLLECTION,
        schema=schema,
        index_params=index_params,
    )
    print(f"✅ Collection 创建成功: {_COLLECTION}")


def load_csv(client: MilvusClient, embed_fn):
    """加载 CSV 并写入 Milvus"""
    if not _CSV_PATH.exists():
        print(f"❌ CSV 文件不存在: {_CSV_PATH}")
        return

    rows = []
    with open(_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"读取 CSV: {len(rows)} 条")

    # 批量生成 Embedding
    texts = [_build_embed_text(row) for row in rows]
    print("生成 Embedding 中...")
    embeddings = embed_fn(texts)

    # 组装数据
    data = []
    for i, row in enumerate(rows):
        data.append({
            "module": row.get("module", ""),
            "problem_pattern": row.get("problem_pattern", ""),
            "problem_desc": row.get("problem_desc", ""),
            "root_cause": row.get("root_cause", ""),
            "solution": row.get("solution", ""),
            "tags": row.get("tags", ""),
            "severity": row.get("severity", ""),
            "embedding": embeddings[i],
        })

    # 批量写入
    client.insert(collection_name=_COLLECTION, data=data)
    print(f"✅ 写入 {len(data)} 条到 Milvus")


def init_milvus(embed_fn):
    """初始化 Milvus：建表 + 导入数据"""
    client = _get_client()
    try:
        create_collection(client)
        load_csv(client, embed_fn)
    finally:
        client.close()


if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer

    model_path = str(Path(__file__).resolve().parent.parent.parent / "models" / "bge-large-zh-v1.5")
    print(f"加载 Embedding 模型: {model_path}")
    model = SentenceTransformer(model_path)

    def embed_fn(texts):
        return model.encode(texts, normalize_embeddings=True).tolist()

    init_milvus(embed_fn)
