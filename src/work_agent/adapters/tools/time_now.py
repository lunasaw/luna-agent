"""时间查询工具（示例 - 无网络依赖）"""

from datetime import datetime, timezone
from typing import Any

from agents import function_tool


@function_tool
def get_current_time(timezone_name: str = "UTC") -> str:
    """
    获取当前时间

    Args:
        timezone_name: 时区名称（当前仅支持 UTC）

    Returns:
        当前时间字符串（ISO 8601 格式）
    """
    # 简化实现：仅支持 UTC
    now = datetime.now(timezone.utc)
    return now.isoformat()


def get_tool() -> Any:
    """暴露 tool 供自动发现"""
    return get_current_time
