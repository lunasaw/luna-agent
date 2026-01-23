"""Agent 工厂 - 根据配置构建不同的 Agent 后端"""

import logging
from typing import Any

from work_agent.adapters.llm.base_agent import BaseAgent
from work_agent.adapters.llm.openai_agent_adapter import OpenAIAgentAdapter
from work_agent.adapters.llm.qwen_agent_adapter import QwenAgentAdapter
from work_agent.config import Config

logger = logging.getLogger(__name__)

# Agent 默认指令
DEFAULT_INSTRUCTIONS = """你是一个日常工作助理 Agent。

你的职责：
1. 理解用户的需求和问题
2. 使用可用的工具（tools）来完成任务
3. 提供清晰、结构化的回答

工作准则：
- 必要时调用工具，但不要过度使用
- 如果不确定，明确说明不确定性并询问需要的信息
- 输出应简洁、有条理
- 禁止臆测或编造信息
- 遇到错误时，解释原因并提供建议

请始终保持专业、友好、高效。
"""


def build_agent(config: Config, tools: list[Any]) -> BaseAgent:
    """
    根据配置构建 Agent 实例

    Args:
        config: 配置对象
        tools: 工具列表

    Returns:
        BaseAgent: Agent 实例（OpenAI 或 Qwen 后端）
    """
    # 获取后端类型（默认为 openai）
    backend = getattr(config, 'agent_backend', 'openai')

    logger.info(f"Building agent with backend: {backend}")
    logger.info(f"Agent model: {config.agent_model}")
    logger.info(f"Agent tools count: {len(tools)}")

    # 根据后端类型创建对应的 Agent
    if backend == "openai":
        agent = OpenAIAgentAdapter(
            model=config.agent_model,
            instructions=DEFAULT_INSTRUCTIONS,
            api_key=config.openai_api_key,
            api_base=config.openai_api_base,
            timeout=config.agent_timeout,
        )
    elif backend == "qwen":
        agent = QwenAgentAdapter(
            model=config.agent_model,
            instructions=DEFAULT_INSTRUCTIONS,
            api_key=config.dashscope_api_key,
        )
    else:
        raise ValueError(f"Unsupported agent backend: {backend}")

    # 添加工具
    for tool in tools:
        agent.add_tool(tool)

    logger.info(f"Agent built successfully with {len(tools)} tools")
    return agent
