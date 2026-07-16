"""
Agent 核心逻辑
负反馈分析流程：提取信息 → 查数据 → 对比分析 → 生成报告
"""

import json
import logging
import uuid
from datetime import datetime

from app.agent.prompts import SYSTEM_PROMPT, ANALYZE_PROMPT_TEMPLATE
from app.models.schemas import (
    FeedbackRequest,
    AnalysisResult,
)
from app.services.llm import get_llm_service
from app.skills import (
    query_weather_data,
    query_hourly_data,
    query_forecast_data,
    query_alert_data,
    calculate_feels_like,
    search_knowledge,
)

logger = logging.getLogger(__name__)


class FeedbackAnalysisAgent:
    """负反馈分析 Agent"""

    def __init__(self):
        self.llm = get_llm_service()

    async def analyze(self, feedback: FeedbackRequest) -> AnalysisResult:
        """
        分析单条负反馈

        流程：
        1. 提取关键信息（位置、时间、问题描述）
        2. 查实况 + 逐时 + 逐天数据
        3. 计算体感温度
        4. 检索知识库
        5. 调 LLM 生成分析报告
        """
        analysis_id = f"A{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
        location = feedback.location or "未知"
        time_str = feedback.time or datetime.now().strftime("%Y-%m-%d")
        content = feedback.content

        logger.info(f"[Agent] 开始分析 {feedback.feedback_id} | 位置={location} 时间={time_str}")

        # ---- Step 1: 查数据 ----
        weather = await query_weather_data(location, time_str)
        hourly = await query_hourly_data(location, hours=24)
        forecast = await query_forecast_data(location, days=7)
        alert = await query_alert_data(location, time_str)

        logger.info(
            f"[Agent] 数据收集完成: 实况={'有' if weather.temperature else '无'} "
            f"逐时={len(hourly)}条 逐天={len(forecast)}条 预警={'有' if alert.has_alert else '无'}"
        )

        # ---- Step 2: 计算体感温度 ----
        feels_like = None
        if weather.temperature is not None:
            feels_like = await calculate_feels_like(
                temperature=weather.temperature,
                humidity=weather.humidity or 50.0,
                wind_speed=weather.wind_speed or 3.0,
            )
            logger.info(f"[Agent] 体感温度: {feels_like.feels_like}℃ ({feels_like.comfort})")

        # ---- Step 3: 检索知识库 ----
        knowledge = await search_knowledge(content)
        logger.info(f"[Agent] 检索到 {len(knowledge)} 条相关知识")

        # ---- Step 4: 调 LLM 分析 ----
        prompt = ANALYZE_PROMPT_TEMPLATE.format(
            feedback_id=feedback.feedback_id,
            content=content,
            time=time_str,
            location=location,
            user_id=feedback.user_id or "未知",
            source=feedback.source or "未知",
        )

        # 组装数据摘要给 LLM
        data_summary = self._build_data_summary(
            weather, hourly[:6], forecast[:3], alert, feels_like, knowledge
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{prompt}\n\n{data_summary}"},
        ]

        llm_response = await self.llm.chat(messages)

        # ---- Step 5: 组装结果 ----
        result = self._build_result(
            analysis_id, feedback, weather, feels_like, alert, llm_response
        )

        logger.info(f"[Agent] 分析完成: {analysis_id}")
        return result

    def _build_data_summary(
        self, weather, hourly, forecast, alert, feels_like, knowledge
    ) -> str:
        """组装数据摘要供 LLM 分析"""
        parts = []

        # 实况
        if weather.temperature is not None:
            parts.append(
                f"## 实况数据\n"
                f"- 温度: {weather.temperature}℃\n"
                f"- 体感温度: {weather.real_feel}℃\n"
                f"- 湿度: {weather.humidity}%\n"
                f"- 风速: {weather.wind_speed}m/s {weather.wind_dir}\n"
                f"- 天气ID: {weather.weather_id}\n"
                f"- 能见度: {weather.visibility}m\n"
                f"- 更新时间: {weather.update_time}"
            )

        # 体感温度
        if feels_like:
            parts.append(
                f"## 体感分析\n"
                f"- 计算体感温度: {feels_like.feels_like}℃\n"
                f"- 舒适度: {feels_like.comfort}\n"
                f"- 说明: {feels_like.description}"
            )

        # 逐时（取最近6小时）
        if hourly:
            hh_lines = [
                f"  {h.predict_time}: {h.temperature}℃ 湿度{h.humidity}% "
                f"风速{h.wind_speed}m/s 天气{h.weather_id}"
                for h in hourly
            ]
            parts.append(f"## 逐时预报（最近6小时）\n" + "\n".join(hh_lines))

        # 逐天（取最近3天）
        if forecast:
            ff_lines = [
                f"  {f.predict_date}: {f.temp_low}~{f.temp_high}℃ "
                f"白天{f.weather_day} 夜间{f.weather_night}"
                for f in forecast
            ]
            parts.append(f"## 逐天预报（最近3天）\n" + "\n".join(ff_lines))

        # 预警
        if alert.has_alert:
            parts.append(
                f"## 预警信息\n"
                f"- 类型: {alert.alert_type}\n"
                f"- 等级: {alert.alert_level}\n"
                f"- 时间: {alert.alert_time}"
            )

        # 知识库
        if knowledge:
            kn_lines = [
                f"  [{k.score:.2f}] {k.content} → {k.solution}"
                for k in knowledge
            ]
            parts.append(f"## 相关知识\n" + "\n".join(kn_lines))

        return "\n\n".join(parts)

    def _build_result(
        self, analysis_id, feedback, weather, feels_like, alert, llm_response
    ) -> AnalysisResult:
        """组装最终分析结果"""
        # 解析 LLM 输出
        try:
            parsed = json.loads(llm_response.get("content", "{}"))
        except (json.JSONDecodeError, TypeError):
            parsed = {}

        return AnalysisResult(
            analysis_id=analysis_id,
            feedback_type=parsed.get("feedback_type", "未知"),
            problem_location=parsed.get("problem_location", "待分析"),
            root_cause=parsed.get("root_cause", "待分析"),
            actual_data=weather,
            feels_like=feels_like,
            alert_data=alert if alert.has_alert else None,
            meteorological_explanation=parsed.get("meteorological_explanation", ""),
            suggestion=parsed.get("suggestion", ""),
            reply_content=parsed.get("reply_content", ""),
        )


# 全局单例
_agent: FeedbackAnalysisAgent | None = None


def get_agent() -> FeedbackAnalysisAgent:
    """获取 Agent 单例"""
    global _agent
    if _agent is None:
        _agent = FeedbackAnalysisAgent()
    return _agent
