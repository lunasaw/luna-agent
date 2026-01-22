"""依赖注入容器 - 唯一允许组装依赖的位置"""

import logging
from dataclasses import dataclass
from typing import Any

from work_agent.adapters.llm.agent_factory import build_agent
from work_agent.adapters.llm.runner_factory import build_runner
from work_agent.adapters.observability.context import new_trace_id
from work_agent.adapters.observability.tracing import configure_tracing
from work_agent.adapters.tools._registry import ToolRegistry
from work_agent.config import Config
from work_agent.services.agent_service import AgentService

logger = logging.getLogger(__name__)


@dataclass
class Container:
    """依赖容器（持有所有依赖）"""

    config: Config
    logger: logging.Logger
    tool_registry: ToolRegistry
    tools: list[Any]
    agent: Any
    runner: Any
    agent_service: AgentService
    _resources: list[Any]  # 需要关闭的资源


def build_container(config: Config) -> Container:
    """
    构建依赖容器

    Args:
        config: 配置对象

    Returns:
        Container: 依赖容器
    """
    logger.info("Building dependency container", extra={"trace_id": new_trace_id()})

    # 1. 配置 tracing
    configure_tracing(enabled=config.enable_tracing)

    # 2. 加载 tools
    tool_registry = ToolRegistry()
    tools = tool_registry.load_tools()
    logger.info(f"Loaded {len(tools)} tools")

    # 3. 构建 Agent
    agent = build_agent(config, tools)

    # 4. 构建 Runner
    runner = build_runner(config)

    # 5. 构建 Services
    agent_service = AgentService(
        agent=agent,
        runner=runner,
        config=config,
    )

    # 6. 记录需要关闭的资源
    resources: list[Any] = []
    if hasattr(runner, "close"):
        resources.append(runner)

    logger.info("Container built successfully")

    return Container(
        config=config,
        logger=logger,
        tool_registry=tool_registry,
        tools=tools,
        agent=agent,
        runner=runner,
        agent_service=agent_service,
        _resources=resources,
    )


def shutdown_container(container: Container) -> None:
    """
    关闭容器并释放资源

    Args:
        container: 依赖容器
    """
    logger.info("Shutting down container")

    for resource in container._resources:
        try:
            if hasattr(resource, "close"):
                resource.close()
            elif hasattr(resource, "shutdown"):
                resource.shutdown()
        except Exception as e:
            logger.error(f"Error closing resource: {e}", exc_info=True)

    logger.info("Container shutdown complete")
