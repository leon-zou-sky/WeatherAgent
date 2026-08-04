"""
API v1 路由汇总
"""

from fastapi import APIRouter

from app.api.v1.endpoints import alert_monitor, analysis, analyze

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(analyze.router)
api_router.include_router(analysis.router)
api_router.include_router(alert_monitor.router)
