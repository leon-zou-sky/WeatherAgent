"""
SQLAlchemy 数据库模型和连接管理
"""

from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, DateTime, JSON, Index, create_engine
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


# ============ Base ============

class Base(DeclarativeBase):
    pass


# ============ 分析记录表 ============

class AgentAnalysis(Base):
    __tablename__ = "agent_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), nullable=False, unique=True, comment="分析ID")
    feedback_id = Column(String(64), nullable=False, index=True, comment="反馈ID")
    feedback_type = Column(String(32), comment="问题类型")
    location = Column(String(128), comment="位置")
    time = Column(DateTime, comment="时间")
    problem_location = Column(String(32), comment="问题环节")
    root_cause = Column(Text, comment="问题根因")
    suggestion = Column(Text, comment="改进建议")
    reply_content = Column(Text, comment="回复内容")
    actual_data = Column(JSON, comment="实际数据")
    check_results = Column(JSON, comment="检查结果")
    status = Column(String(16), default="pending", index=True, comment="状态")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    __table_args__ = (
        Index("idx_feedback_id", "feedback_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
    )


# ============ 知识库表 ============

class AgentKnowledge(Base):
    __tablename__ = "agent_knowledge"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    problem_type = Column(String(32), index=True, comment="问题类型")
    problem_desc = Column(Text, comment="问题描述")
    root_cause = Column(Text, comment="问题根因")
    solution = Column(Text, comment="解决方案")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


# ============ 数据库连接 ============

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库 session"""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
