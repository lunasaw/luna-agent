"""Runner 工厂 - 构建 OpenAI Agents SDK Runner"""

import logging
from typing import Any

from agents import Runner

from work_agent.config import Config

logger = logging.getLogger(__name__)


def build_runner(config: Config) -> Any:
    """
    构建 Runner 实例

    Args:
        config: 配置对象

    Returns:
        Runner 实例或封装对象
    """
    logger.info(f"Building runner with backend: {config.session_backend}")

    # 创建 Runner（不需要 client 参数）
    runner = Runner()

    logger.info("Runner built successfully")
    return runner
