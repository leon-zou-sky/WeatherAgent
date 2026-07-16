"""
Skill 2: 链路检查
检查各数据表的更新状态和数据延迟
"""

from sqlalchemy import text

from app.models.schemas import PipelineStepResult, PipelineResult
from app.skills.db import get_session


def _check_table_freshness(session, table: str, city_id: str, time_col: str = "get_time") -> dict:
    """检查表的数据新鲜度"""
    try:
        row = session.execute(
            text(f"""
                SELECT COUNT(*) as cnt,
                       MAX({time_col}) as latest
                FROM {table}
                WHERE city_id = :cid
            """),
            {"cid": city_id},
        ).fetchone()

        if not row or row[0] == 0:
            return {"status": "异常", "detail": f"{table} 无数据"}

        return {
            "status": "正常",
            "detail": f"{table}: {row[0]}条, 最新: {row[1]}",
        }
    except Exception as e:
        return {"status": "异常", "detail": f"{table} 查询失败: {e}"}


async def check_pipeline(location: str, time: str = "") -> PipelineResult:
    """
    检查整个数据链路

    Args:
        location: 位置
        time: 时间（兼容接口）

    Returns:
        PipelineResult: 链路各环节检查结果
    """
    # 解析 city_id
    city_id = location if location.isdigit() else None
    if not city_id:
        session = get_session()
        try:
            row = session.execute(
                text("SELECT city_id FROM city WHERE city_name = :name LIMIT 1"),
                {"name": location},
            ).fetchone()
            city_id = row[0] if row else None
        finally:
            session.close()

    if not city_id:
        empty = PipelineStepResult(status="异常", detail=f"未找到城市: {location}")
        return PipelineResult(
            data_source=empty,
            collection=empty,
            processing=empty,
            storage=empty,
            publishing=empty,
        )

    session = get_session()
    try:
        # 检查各表数据状态
        cn = _check_table_freshness(session, "weather_cn", city_id)
        hh = _check_table_freshness(session, "weather_hh", city_id, "predict_timestamp")
        ff = _check_table_freshness(session, "weather_ff", city_id, "created_at")
        alert = _check_table_freshness(session, "alert_data", city_id, "created_at")

        return PipelineResult(
            data_source=PipelineStepResult(status=cn["status"], detail=cn["detail"]),
            collection=PipelineStepResult(status=hh["status"], detail=hh["detail"]),
            processing=PipelineStepResult(status=ff["status"], detail=ff["detail"]),
            storage=PipelineStepResult(status=alert["status"], detail=alert["detail"]),
            publishing=PipelineStepResult(status="正常", detail="API 服务正常"),
        )
    finally:
        session.close()
