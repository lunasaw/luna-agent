"""类型工具（可选）"""

from typing import Any, TypeVar

T = TypeVar("T")


def safe_cast(value: Any, target_type: type[T], default: T) -> T:
    """
    安全类型转换

    Args:
        value: 原始值
        target_type: 目标类型
        default: 默认值

    Returns:
        转换后的值或默认值
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default
