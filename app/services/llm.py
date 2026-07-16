"""
LLM 服务
通过火山引擎 Ark 平台调用豆包大模型（OpenAI 兼容接口）
"""

import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """豆包大模型 LLM 服务（通过 Ark 平台）"""

    def __init__(self):
        settings = get_settings()
        self.model = settings.ark_model_endpoint  # 推理接入点 ID
        self._client = AsyncOpenAI(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
        )

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """
        调用豆包大模型进行对话

        Args:
            messages: 消息列表
            tools: Function Calling 工具定义（可选）
            temperature: 温度参数

        Returns:
            LLM 响应 {"role": "assistant", "content": "..."}
        """
        logger.info(f"[LLM] 调用模型 {self.model}，消息数: {len(messages)}")

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools

        try:
            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            # 处理 Function Calling 响应
            if message.tool_calls:
                logger.info(
                    f"[LLM] 模型请求调用工具: "
                    f"{[tc.function.name for tc in message.tool_calls]}"
                )

            result = {
                "role": "assistant",
                "content": message.content or "",
            }

            # 如果有 tool_calls，一并返回
            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

            logger.info(f"[LLM] 模型响应成功，内容长度: {len(result['content'])}")
            return result

        except Exception as e:
            logger.error(f"[LLM] 调用失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        await self._client.close()


# 全局单例
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
