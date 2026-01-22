"""上下文管理 - trace_id/request_id 生成与传递"""

import uuid
from contextvars import ContextVar
from typing import Optional

# 使用 contextvars 存储 trace_id（线程安全）
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def new_trace_id() -> str:
    """
    生成新的 trace_id

    Returns:
        str: trace_id（格式：req_<uuid>）
    """
    trace_id = f"req_{uuid.uuid4().hex[:16]}"
    _trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> Optional[str]:
    """
    获取当前上下文的 trace_id

    Returns:
        str | None: trace_id 或 None
    """
    return _trace_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """
    设置当前上下文的 trace_id

    Args:
        trace_id: trace_id 字符串
    """
    _trace_id_var.set(trace_id)


def clear_trace_id() -> None:
    """清除当前上下文的 trace_id"""
    _trace_id_var.set(None)
