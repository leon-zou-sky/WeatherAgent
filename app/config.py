"""
应用配置管理
使用 pydantic-settings 从环境变量和 .env 文件加载配置
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- 应用配置 ----
    app_name: str = "WeatherAgent"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ---- 数据库配置 ----
    db_host: str = "localhost"
    db_port: int = 3307
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "weather"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_database_url(self) -> str:
        """同步连接（downloader 用 pymysql）"""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    # ---- 北京局数据源 ----
    bj_api_key: str = "cWpHF7pzPYGpBg9S"

    # ---- Redis 配置 ----
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        pwd = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{pwd}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ---- 豆包大模型配置 (火山引擎 Ark) ----
    ark_api_key: str = ""                    # Ark 控制台获取的 API Key
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"  # Ark 接口地址
    ark_model_endpoint: str = ""             # 推理接入点 ID，如 ep-20240xxx-xxxxx

    # ---- Milvus 配置 ----
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "knowledge_base"

    # ---- Embedding 模型 ----
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ---- 外部服务 ----
    weather_api_url: str = ""
    alert_api_url: str = ""
    notification_api_url: str = ""


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
