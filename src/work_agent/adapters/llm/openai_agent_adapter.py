"""OpenAI Agents SDK 适配器"""

import logging
import os
from typing import Any

from agents import Agent, Runner

from work_agent.adapters.llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OpenAIAgentAdapter(BaseAgent):
    """OpenAI Agents SDK 适配器

    使用 OpenAI 官方的 Agents SDK 实现 Agent 功能。
    支持 OpenAI API 和兼容的服务。
    """

    def __init__(self, model: str, instructions: str, api_key: str, api_base: str = None, timeout: float = 60.0):
        """初始化 OpenAI Agent

        Args:
            model: 模型名称（如 gpt-4o）
            instructions: 系统指令
            api_key: OpenAI API Key
            api_base: API 基础 URL（可选）
            timeout: 请求超时时间（秒）
        """
        self.model = model
        self.instructions = instructions

        # 配置环境变量（OpenAI Agents SDK 会读取）
        os.environ["OPENAI_API_KEY"] = api_key

        if api_base:
            os.environ["OPENAI_BASE_URL"] = api_base
            logger.info(f"Using custom API base: {api_base}")

        os.environ["OPENAI_TIMEOUT"] = str(timeout)
        logger.info(f"OpenAI client timeout: {timeout}s")

        # 创建 Agent 实例
        self.agent = Agent(
            name="work-agent",
            instructions=instructions,
            model=model,
            tools=[],
        )

        # 创建 Runner
        self.runner = Runner()

        logger.info(f"OpenAIAgentAdapter initialized with model: {model}")

    async def run(self, user_input: str, **kwargs) -> str:
        """运行 Agent

        Args:
            user_input: 用户输入
            **kwargs: 额外参数

        Returns:
            Agent 响应内容
        """
        logger.info(f"Running OpenAI Agent with input: {user_input[:50]}...")

        # 调用 Agent（runner.run 是 async 方法）
        response = await self.runner.run(self.agent, user_input)

        # 提取响应内容
        content = self._extract_response(response)

        logger.info(f"OpenAI Agent completed, response length: {len(content)}")
        return content

    def add_tool(self, tool: Any) -> None:
        """添加工具

        Args:
            tool: 工具对象（OpenAI 格式）
        """
        self.agent.tools.append(tool)
        logger.info(f"Tool added to OpenAI Agent, total tools: {len(self.agent.tools)}")

    def _extract_response(self, response: Any) -> str:
        """提取响应内容

        Args:
            response: Agent 响应对象

        Returns:
            响应文本内容
        """
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)
