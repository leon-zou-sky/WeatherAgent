"""
分析结果管理 API
支持查询历史、审核、状态流转
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.skills.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["分析结果"])


# ============ 请求模型 ============

class ReviewRequest(BaseModel):
    """审核请求"""
    analysis_id: str
    action: str  # approved / rejected
    reviewer: str
    comment: str = ""


class AnalysisQuery(BaseModel):
    """查询条件"""
    status: str = None
    location: str = None
    feedback_type: str = None
    start_date: str = None
    end_date: str = None
    page: int = 1
    page_size: int = 20


# ============ 接口 ============

@router.get("/list", summary="查询分析结果列表")
async def list_analysis(
    status: str = None,
    location: str = None,
    feedback_type: str = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    查询分析结果列表

    - **status**: 状态过滤（pending/approved/rejected/sent）
    - **location**: 位置过滤
    - **feedback_type**: 问题类型过滤
    - **page**: 页码
    - **page_size**: 每页数量
    """
    session = get_session()
    try:
        # 构建查询
        where_clauses = []
        params = {}

        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        if location:
            where_clauses.append("location LIKE :location")
            params["location"] = f"%{location}%"
        if feedback_type:
            where_clauses.append("feedback_type LIKE :ft")
            params["ft"] = f"%{feedback_type}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # 总数
        count_sql = f"SELECT COUNT(*) FROM analysis_result WHERE {where_sql}"
        total = session.execute(text(count_sql), params).fetchone()[0]

        # 分页查询
        offset = (page - 1) * page_size
        query_sql = f"""
            SELECT analysis_id, feedback_id, feedback_content, location,
                   feedback_type, root_cause, reply_content, status,
                   reviewer, review_time, created_at,
                   alert_type, alert_level, alert_time
            FROM analysis_result
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = page_size
        params["offset"] = offset

        rows = session.execute(text(query_sql), params).fetchall()

        results = []
        for r in rows:
            results.append({
                "analysis_id": r[0],
                "feedback_id": r[1],
                "feedback_content": r[2][:50] + "..." if r[2] and len(r[2]) > 50 else r[2],
                "location": r[3],
                "feedback_type": r[4],
                "root_cause": r[5][:100] + "..." if r[5] and len(r[5]) > 100 else r[5],
                "reply_content": r[6][:100] + "..." if r[6] and len(r[6]) > 100 else r[6],
                "status": r[7],
                "reviewer": r[8],
                "review_time": str(r[9]) if r[9] else None,
                "created_at": str(r[10]),
                "alert": {
                    "type": r[11],
                    "level": r[12],
                    "time": r[13],
                } if r[11] else None,
            })

        return {
            "code": 200,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "results": results,
            },
        }

    finally:
        session.close()


@router.get("/{analysis_id}", summary="查询单条分析结果详情")
async def get_analysis_detail(analysis_id: str):
    """
    查询单条分析结果详情

    - **analysis_id**: 分析ID
    """
    session = get_session()
    try:
        row = session.execute(text("""
            SELECT analysis_id, feedback_id, feedback_content, location,
                   user_id, source, feedback_type, root_cause,
                   meteorological_explanation, suggestion, reply_content,
                   actual_temp, actual_humidity, actual_wind_speed, feels_like,
                   status, reviewer, review_time, review_comment,
                   created_at, updated_at,
                   alert_type, alert_level, alert_time
            FROM analysis_result
            WHERE analysis_id = :aid
        """), {"aid": analysis_id}).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="分析结果不存在")

        return {
            "code": 200,
            "data": {
                "analysis_id": row[0],
                "feedback_id": row[1],
                "feedback_content": row[2],
                "location": row[3],
                "user_id": row[4],
                "source": row[5],
                "feedback_type": row[6],
                "root_cause": row[7],
                "meteorological_explanation": row[8],
                "suggestion": row[9],
                "reply_content": row[10],
                "actual_data": {
                    "temp": row[11],
                    "humidity": row[12],
                    "wind_speed": row[13],
                    "feels_like": row[14],
                },
                "alert": {
                    "type": row[21],
                    "level": row[22],
                    "time": row[23],
                } if row[21] else None,
                "status": row[15],
                "reviewer": row[16],
                "review_time": str(row[17]) if row[17] else None,
                "review_comment": row[18],
                "created_at": str(row[19]),
                "updated_at": str(row[20]),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询分析结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/review", summary="审核分析结果")
async def review_analysis(req: ReviewRequest):
    """
    审核分析结果

    - **analysis_id**: 分析ID
    - **action**: approved(通过) / rejected(驳回)
    - **reviewer**: 审核人
    - **comment**: 审核意见
    """
    if req.action not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="action 必须是 approved 或 rejected")

    session = get_session()
    try:
        # 查询是否存在
        row = session.execute(text("""
            SELECT status FROM analysis_result WHERE analysis_id = :aid
        """), {"aid": req.analysis_id}).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="分析结果不存在")

        if row[0] != "pending":
            raise HTTPException(status_code=400, detail=f"当前状态 {row[0]}，只能审核 pending 状态的记录")

        # 更新状态
        session.execute(text("""
            UPDATE analysis_result
            SET status = :status,
                reviewer = :reviewer,
                review_time = NOW(),
                review_comment = :comment,
                updated_at = NOW()
            WHERE analysis_id = :aid
        """), {
            "status": req.action,
            "reviewer": req.reviewer,
            "comment": req.comment,
            "aid": req.analysis_id,
        })
        session.commit()

        return {
            "code": 200,
            "message": f"审核成功: {req.action}",
            "data": {
                "analysis_id": req.analysis_id,
                "status": req.action,
                "reviewer": req.reviewer,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"审核失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{analysis_id}/send", summary="发送回复给用户")
async def send_reply(analysis_id: str):
    """
    将审核通过的回复发送给用户

    - **analysis_id**: 分析ID
    """
    session = get_session()
    try:
        row = session.execute(text("""
            SELECT status, reply_content, feedback_id
            FROM analysis_result WHERE analysis_id = :aid
        """), {"aid": analysis_id}).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="分析结果不存在")

        if row[0] != "approved":
            raise HTTPException(status_code=400, detail="只能发送已审核通过的结果")

        # TODO: 对接真实推送服务
        # send_notification(row[2], row[1])

        # 更新状态为已发送
        session.execute(text("""
            UPDATE analysis_result
            SET status = 'sent', updated_at = NOW()
            WHERE analysis_id = :aid
        """), {"aid": analysis_id})
        session.commit()

        return {
            "code": 200,
            "message": "发送成功",
            "data": {"analysis_id": analysis_id, "status": "sent"},
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/stats/summary", summary="统计概览")
async def get_stats():
    """获取分析结果统计概览"""
    session = get_session()
    try:
        # 各状态数量
        stats = session.execute(text("""
            SELECT status, COUNT(*) as cnt
            FROM analysis_result
            GROUP BY status
        """)).fetchall()

        # 今日新增
        today_count = session.execute(text("""
            SELECT COUNT(*) FROM analysis_result
            WHERE DATE(created_at) = CURDATE()
        """)).fetchone()[0]

        # 问题类型分布
        type_dist = session.execute(text("""
            SELECT feedback_type, COUNT(*) as cnt
            FROM analysis_result
            GROUP BY feedback_type
            ORDER BY cnt DESC
            LIMIT 10
        """)).fetchall()

        return {
            "code": 200,
            "data": {
                "status_distribution": {r[0]: r[1] for r in stats},
                "today_count": today_count,
                "type_distribution": {r[0]: r[1] for r in type_dist},
            },
        }

    finally:
        session.close()
