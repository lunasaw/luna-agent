"""日志配置 - 统一日志初始化"""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（简化版，可扩展为 JSON）"""

    def format(self, record: logging.LogRecord) -> str:
        # 基础格式化
        base = super().format(record)

        # 追加结构化字段
        extras = []
        if hasattr(record, "trace_id"):
            extras.append(f"trace_id={record.trace_id}")
        if hasattr(record, "tool_name"):
            extras.append(f"tool={record.tool_name}")

        if extras:
            return f"{base} | {' '.join(extras)}"
        return base


def configure_logging(level: str = "INFO") -> None:
    """
    配置全局日志（只调用一次）

    Args:
        level: 日志级别（DEBUG/INFO/WARNING/ERROR）
    """
    # 设置根日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 清除现有 handlers（防止重复）
    root_logger.handlers.clear()

    # 创建控制台 handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)

    # 设置格式化器
    formatter = StructuredFormatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(formatter)

    # 添加到根 logger
    root_logger.addHandler(console_handler)

    # 调整第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称（通常使用 __name__）

    Returns:
        Logger 实例
    """
    return logging.getLogger(name)
