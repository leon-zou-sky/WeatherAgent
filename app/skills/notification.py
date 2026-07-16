"""
Skill 7: 发送通知
发送通知给用户
"""

import logging

logger = logging.getLogger(__name__)


async def send_notification(user_id: str, content: str) -> bool:
    """
    发送通知给用户

    Args:
        user_id: 用户ID
        content: 通知内容

    Returns:
        bool: 是否发送成功
    """
    # TODO: 接入真实推送服务（APNs / 极光推送 / 自建推送）
    # Mock 实现：记录日志即视为成功

    logger.info(f"[Notification] 发送通知给用户 {user_id}: {content[:50]}...")
    return True
