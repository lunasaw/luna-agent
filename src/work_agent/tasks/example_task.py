"""示例任务（可选）"""

import logging

from work_agent.services.agent_service import AgentService

logger = logging.getLogger(__name__)


def run_example_task(agent_service: AgentService) -> str:
    """
    示例任务：调用 agent_service

    Args:
        agent_service: Agent 服务（注入）

    Returns:
        str: 任务结果
    """
    logger.info("Running example task")

    result = agent_service.run_once("现在几点了？")

    logger.info("Example task completed")
    return result
