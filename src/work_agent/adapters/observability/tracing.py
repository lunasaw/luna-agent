"""Tracing 配置与集成（预留）"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_tracing_enabled = False


def configure_tracing(enabled: bool = False) -> None:
    """
    配置 tracing（预留接口）

    当前为本地模式，仅输出日志。
    未来可对接：
    - OpenTelemetry
    - Langfuse
    - LangSmith
    - Custom backend

    Args:
        enabled: 是否启用 tracing
    """
    global _tracing_enabled
    _tracing_enabled = enabled

    if enabled:
        logger.info("Tracing enabled (local mode)")
        # TODO: 对接外部 tracing backend
    else:
        logger.debug("Tracing disabled")


def is_tracing_enabled() -> bool:
    """
    检查 tracing 是否启用

    Returns:
        bool: 是否启用
    """
    return _tracing_enabled


def trace_event(event_name: str, metadata: Optional[dict] = None) -> None:
    """
    记录 trace 事件（预留）

    Args:
        event_name: 事件名称
        metadata: 事件元数据
    """
    if not _tracing_enabled:
        return

    logger.info(
        f"Trace event: {event_name}",
        extra={
            "event_name": event_name,
            "metadata": metadata or {},
        },
    )
