"""Qwen-Agent 适配器 - 用于 DashScope / Qwen 模型"""

import logging
import os
from typing import Any

from qwen_agent.agents import Assistant

from work_agent.adapters.llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QwenAgentAdapter(BaseAgent):
    """Qwen-Agent 适配器

    使用 Qwen-Agent 框架实现 Agent 功能。
    支持 DashScope API 和 Qwen 系列模型。
    """

    def __init__(self, model: str, instructions: str, api_key: str):
        """初始化 Qwen-Agent

        Args:
            model: 模型名称（如 qwen-plus, qwen-turbo）
            instructions: 系统指令
            api_key: DashScope API Key
        """
        self.model = model
        self.instructions = instructions
        self.function_list = []

        # 配置环境变量（Qwen-Agent 会读取 DASHSCOPE_API_KEY）
        os.environ["DASHSCOPE_API_KEY"] = api_key
        logger.info("DashScope API key configured")

        # 创建 Assistant 实例
        self.agent = Assistant(
            llm={'model': model},
            system_message=instructions,
            function_list=self.function_list,
        )

        logger.info(f"QwenAgentAdapter initialized with model: {model}")

    async def run(self, user_input: str, **kwargs) -> str:
        """运行 Agent

        Args:
            user_input: 用户输入
            **kwargs: 额外参数

        Returns:
            Agent 响应内容
        """
        logger.info(f"Running Qwen-Agent with input: {user_input[:50]}...")

        # 构造消息格式
        messages = [{'role': 'user', 'content': user_input}]

        # 调用 Agent（Qwen-Agent 的 run 是同步方法）
        responses = []
        for response in self.agent.run(messages):
            responses.append(response)
            logger.debug(f"Received response chunk: {response}")

        # 提取最后的响应内容
        if responses:
            last_response = responses[-1]
            # 响应格式可能是字典或字符串
            if isinstance(last_response, dict):
                content = last_response.get('content', '')
            else:
                content = str(last_response)

            logger.info(f"Qwen-Agent completed, response length: {len(content)}")
            return content
        else:
            logger.warning("No response received from Qwen-Agent")
            return ""

    def add_tool(self, tool: Any) -> None:
        """添加工具

        Args:
            tool: 工具对象（需要是 Qwen-Agent 兼容的格式）
        """
        # Qwen-Agent 使用 function_list
        # 工具需要是 BaseTool 的子类或工具名称字符串
        self.function_list.append(tool)

        # 重新创建 Agent 实例以更新工具列表
        self.agent = Assistant(
            llm={'model': self.model},
            system_message=self.instructions,
            function_list=self.function_list,
        )

        logger.info(f"Tool added to Qwen-Agent, total tools: {len(self.function_list)}")
