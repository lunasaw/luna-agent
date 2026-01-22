"""Agent 工厂 - 构建 OpenAI Agents SDK Agent"""

import logging
from typing import Any

from openai.agents import Agent

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


def build_agent(config: Config, tools: list[Any]) -> Agent:
    """
    构建 Agent 实例

    Args:
        config: 配置对象
        tools: 工具列表

    Returns:
        Agent: Agent 实例
    """
    logger.info(f"Building agent with model: {config.agent_model}")
    logger.info(f"Agent tools count: {len(tools)}")

    agent = Agent(
        name="work-agent",
        instructions=DEFAULT_INSTRUCTIONS,
        model=config.agent_model,
        tools=tools,
    )

    logger.info("Agent built successfully")
    return agent
