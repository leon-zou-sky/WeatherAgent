"""
FastAPI 应用入口
气象负反馈分析 Agent 服务
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"🚀 {settings.app_name} 启动中...")
    logger.info(f"📍 环境: {settings.app_env}")
    logger.info(f"🔧 调试模式: {settings.app_debug}")

    # TODO: 初始化数据库连接池
    # TODO: 初始化 Redis 连接
    # TODO: 初始化 Milvus 连接

    yield

    # TODO: 清理资源
    logger.info(f"🛑 {settings.app_name} 关闭中...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="气象负反馈智能分析 Agent - 自动分析用户反馈，定位数据链路问题",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.app_debug,
    )

    # 注册路由
    app.include_router(api_router)

    # 健康检查
    @app.get("/health", tags=["系统"])
    async def health_check():
        return {"status": "ok", "service": settings.app_name}

    return app


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
