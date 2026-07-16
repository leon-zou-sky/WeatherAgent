"""
API 路由：负反馈分析
支持单条分析和批量分析
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import text

from app.agent.core import get_agent
from app.models.schemas import (
    FeedbackRequest,
    BatchAnalyzeRequest,
    AnalysisResponse,
    BatchAnalysisResponse,
    AnalysisQueryResponse,
    AnalysisResult,
)
from app.skills.db import get_session

logger = logging.getLogger(__name__)


def _save_analysis_result(feedback: FeedbackRequest, result: AnalysisResult):
    """保存分析结果到数据库"""
    session = get_session()
    try:
        session.execute(text("""
            INSERT INTO analysis_result
            (analysis_id, feedback_id, feedback_content, location, user_id, source,
             feedback_type, root_cause, meteorological_explanation, suggestion, reply_content,
             actual_temp, actual_humidity, actual_wind_speed, feels_like,
             alert_type, alert_level, alert_time,
             status, created_at, updated_at)
            VALUES
            (:analysis_id, :feedback_id, :feedback_content, :location, :user_id, :source,
             :feedback_type, :root_cause, :meteorological_explanation, :suggestion, :reply_content,
             :actual_temp, :actual_humidity, :actual_wind_speed, :feels_like,
             :alert_type, :alert_level, :alert_time,
             'pending', NOW(), NOW())
        """), {
            "analysis_id": result.analysis_id,
            "feedback_id": feedback.feedback_id,
            "feedback_content": feedback.content,
            "location": feedback.location,
            "user_id": feedback.user_id,
            "source": feedback.source,
            "feedback_type": result.feedback_type,
            "root_cause": result.root_cause,
            "meteorological_explanation": result.meteorological_explanation,
            "suggestion": result.suggestion,
            "reply_content": result.reply_content,
            "actual_temp": result.actual_data.temperature if result.actual_data else None,
            "actual_humidity": result.actual_data.humidity if result.actual_data else None,
            "actual_wind_speed": result.actual_data.wind_speed if result.actual_data else None,
            "feels_like": result.feels_like.feels_like if result.feels_like else None,
            "alert_type": result.alert_data.alert_type if result.alert_data else None,
            "alert_level": result.alert_data.alert_level if result.alert_data else None,
            "alert_time": result.alert_data.alert_time if result.alert_data else None,
        })
        session.commit()
        logger.info(f"分析结果已保存: {result.analysis_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"保存分析结果失败: {e}")
    finally:
        session.close()

router = APIRouter(prefix="/agent", tags=["Agent"])

# 批量任务存储（生产环境建议用 Redis）
batch_store: dict[str, dict] = {}


async def _process_batch(batch_id: str, feedbacks: list[FeedbackRequest]):
    """后台处理批量分析"""
    agent = get_agent()
    results = []
    completed = 0
    failed = 0

    for feedback in feedbacks:
        try:
            result = await agent.analyze(feedback)
            results.append(result.model_dump())
            completed += 1

            # 保存到数据库
            _save_analysis_result(feedback, result)

        except Exception as e:
            logger.error(f"批量分析失败: {feedback.feedback_id}, error: {e}")
            failed += 1
            results.append({
                "feedback_id": feedback.feedback_id,
                "error": str(e),
            })

        # 更新进度
        batch_store[batch_id] = {
            "batch_id": batch_id,
            "total": len(feedbacks),
            "completed": completed,
            "failed": failed,
            "status": "processing" if completed + failed < len(feedbacks) else "completed",
            "results": results,
            "created_at": batch_store[batch_id].get("created_at"),
            "updated_at": datetime.now().isoformat(),
        }

    logger.info(f"批量分析完成: {batch_id}, 成功: {completed}, 失败: {failed}")


@router.post("/analyze", response_model=AnalysisResponse, summary="分析单条负反馈")
async def analyze_feedback(request: FeedbackRequest):
    """
    分析单条负反馈

    - **feedback_id**: 反馈ID
    - **content**: 反馈内容
    - **time**: 反馈时间（可选）
    - **location**: 位置（可选）
    - **user_id**: 用户ID（可选）
    - **source**: 来源（可选）
    """
    agent = get_agent()
    result = await agent.analyze(request)

    # 保存到数据库
    _save_analysis_result(request, result)

    return AnalysisResponse(code=200, message="success", data=result)


@router.post("/batch-analyze", response_model=BatchAnalysisResponse, summary="批量分析负反馈")
async def batch_analyze(request: BatchAnalyzeRequest, background_tasks: BackgroundTasks):
    """
    批量分析负反馈（异步处理）

    - **feedbacks**: 反馈列表
    """
    batch_id = f"B{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"

    # 初始化批量任务
    batch_store[batch_id] = {
        "batch_id": batch_id,
        "total": len(request.feedbacks),
        "completed": 0,
        "failed": 0,
        "status": "processing",
        "results": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # 启动后台任务
    background_tasks.add_task(_process_batch, batch_id, request.feedbacks)

    return BatchAnalysisResponse(
        code=200,
        message="批量分析任务已提交",
        data={
            "batch_id": batch_id,
            "total": len(request.feedbacks),
            "status": "processing",
        },
    )


@router.get("/batch/{batch_id}", summary="查询批量分析进度")
async def get_batch_status(batch_id: str):
    """
    查询批量分析任务状态

    - **batch_id**: 批次ID
    """
    if batch_id not in batch_store:
        return {"code": 404, "message": "批次不存在"}

    batch = batch_store[batch_id]
    return {
        "code": 200,
        "message": "success",
        "data": {
            "batch_id": batch["batch_id"],
            "total": batch["total"],
            "completed": batch["completed"],
            "failed": batch["failed"],
            "status": batch["status"],
            "progress": f"{batch['completed'] + batch['failed']}/{batch['total']}",
            "created_at": batch["created_at"],
            "updated_at": batch["updated_at"],
        },
    }


@router.get("/batch/{batch_id}/results", summary="获取批量分析结果")
async def get_batch_results(batch_id: str):
    """
    获取批量分析结果

    - **batch_id**: 批次ID
    """
    if batch_id not in batch_store:
        return {"code": 404, "message": "批次不存在"}

    batch = batch_store[batch_id]
    return {
        "code": 200,
        "message": "success",
        "data": {
            "batch_id": batch["batch_id"],
            "status": batch["status"],
            "total": batch["total"],
            "completed": batch["completed"],
            "failed": batch["failed"],
            "results": batch["results"],
        },
    }


@router.get("/analysis/{analysis_id}", response_model=AnalysisQueryResponse, summary="查询分析结果")
async def get_analysis(analysis_id: str):
    """
    根据分析ID查询分析结果

    - **analysis_id**: 分析ID
    """
    # TODO: 从数据库查询分析结果
    return AnalysisQueryResponse(
        code=200,
        message="success",
        data=AnalysisResult(
            analysis_id=analysis_id,
            feedback_type="待查询",
            root_cause="待查询",
        ),
    )
