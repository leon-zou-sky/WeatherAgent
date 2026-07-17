"""
Agent 核心逻辑
负反馈分析流程：提取信息 → 查数据 → 对比分析 → 生成报告
指数分析流程：识别指数类型 → Function Calling → LLM 分析
"""

import json
import logging
import uuid
from datetime import datetime

from app.agent.prompts import SYSTEM_PROMPT, ANALYZE_PROMPT_TEMPLATE, INDEX_SYSTEM_PROMPT
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
from app.agent.index_functions import INDEX_FUNCTIONS, execute_index_function

logger = logging.getLogger(__name__)


class FeedbackAnalysisAgent:
    """负反馈分析 Agent"""

    # 指数相关关键词
    INDEX_KEYWORDS = ["指数", "穿衣", "运动", "紫外线", "中暑", "感冒", "舒适度", "出行",
                      "适宜", "不适宜", "闷热", "炎热", "寒冷"]

    def __init__(self):
        self.llm = get_llm_service()

    def _is_index_feedback(self, content: str) -> bool:
        """判断是否为指数相关反馈"""
        return any(kw in content for kw in self.INDEX_KEYWORDS)

    async def smart_analyze(self, feedback: FeedbackRequest) -> AnalysisResult:
        """
        智能分析：自动判断反馈类型，路由到不同处理流程

        - 指数相关 → Function Calling
        - 其他天气 → Skill
        """
        if self._is_index_feedback(feedback.content):
            logger.info(f"[Agent] 识别为指数反馈: {feedback.content[:30]}...")
            return await self.analyze_index(feedback)
        else:
            logger.info(f"[Agent] 识别为天气反馈: {feedback.content[:30]}...")
            return await self.analyze(feedback)

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

    async def analyze_index(self, feedback: FeedbackRequest) -> AnalysisResult:
        """
        分析指数相关反馈（使用 Function Calling）

        流程：
        1. LLM 识别指数类型 + 决定调用哪些 Function
        2. 执行 Function 获取数据
        3. LLM 分析原因生成报告
        """
        analysis_id = f"A{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
        location = feedback.location or "未知"
        time_str = feedback.time or datetime.now().strftime("%Y-%m-%d")
        content = feedback.content

        logger.info(f"[Agent] 指数分析 {feedback.feedback_id} | 位置={location}")

        # ---- Step 1: LLM 识别指数类型 + 调用 Function ----
        messages = [
            {"role": "system", "content": INDEX_SYSTEM_PROMPT},
            {"role": "user", "content": f"用户反馈: {content}\n位置: {location}\n时间: {time_str}\n\n请识别涉及的指数类型，并获取相关数据进行分析。"},
        ]

        # 第1次 LLM 调用：识别 + Function 选择
        llm_response = await self.llm.chat(messages, tools=INDEX_FUNCTIONS)

        # ---- Step 2: 执行 Function ----
        function_results = []
        if llm_response.get("tool_calls"):
            for tool_call in llm_response["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                logger.info(f"[Agent] 调用 Function: {func_name}({func_args})")

                result = await execute_index_function(func_name, func_args)
                function_results.append({
                    "tool_call_id": tool_call["id"],
                    "function": func_name,
                    "result": result,
                })

        # ---- Step 3: LLM 分析 + 生成报告 ----
        # 构建包含 Function 结果的消息
        analysis_messages = [
            {"role": "system", "content": INDEX_SYSTEM_PROMPT},
            {"role": "user", "content": f"用户反馈: {content}\n位置: {location}\n时间: {time_str}"},
        ]

        if function_results:
            # 添加 Function 调用和结果
            analysis_messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": llm_response.get("tool_calls", []),
            })
            for fr in function_results:
                analysis_messages.append({
                    "role": "tool",
                    "tool_call_id": fr["tool_call_id"],
                    "content": json.dumps(fr["result"], ensure_ascii=False),
                })

            analysis_messages.append({
                "role": "user",
                "content": "请根据以上数据，分析指数是否准确，如果不准确找出原因，并生成用户回复。输出JSON格式：{\"feedback_type\": \"...\", \"root_cause\": \"...\", \"reply_content\": \"...\"}",
            })
        else:
            analysis_messages.append({
                "role": "user",
                "content": "无法获取指数数据，请基于你的知识分析并回复用户。",
            })

        # 第2次 LLM 调用：生成分析报告
        final_response = await self.llm.chat(analysis_messages)

        # ---- Step 4: 组装结果 ----
        try:
            parsed = json.loads(final_response.get("content", "{}"))
        except (json.JSONDecodeError, TypeError):
            parsed = {}

        # 获取实况数据
        weather = await query_weather_data(location, time_str)

        result = AnalysisResult(
            analysis_id=analysis_id,
            feedback_type=parsed.get("feedback_type", "指数反馈"),
            problem_location="指数计算",
            root_cause=parsed.get("root_cause", "待分析"),
            actual_data=weather,
            meteorological_explanation=parsed.get("meteorological_explanation", ""),
            suggestion=parsed.get("suggestion", ""),
            reply_content=parsed.get("reply_content", ""),
        )

        logger.info(f"[Agent] 指数分析完成: {analysis_id}")
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
                f"- 天气现象: {weather.weather_zh}\n"
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
                f"风速{h.wind_speed}m/s 天气{h.weather_zh}"
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
