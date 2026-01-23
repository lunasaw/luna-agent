"""Agent 抽象基类 - 定义统一的 Agent 接口"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Agent 抽象基类

    定义统一的 Agent 接口，隐藏底层实现差异。
    支持多种 Agent 后端：OpenAI Agents SDK、Qwen-Agent 等。
    """

    @abstractmethod
    async def run(self, user_input: str, **kwargs) -> str:
        """运行 Agent

        Args:
            user_input: 用户输入
            **kwargs: 额外参数

        Returns:
            Agent 响应内容
        """
        pass

    @abstractmethod
    def add_tool(self, tool: Any) -> None:
        """添加工具

        Args:
            tool: 工具对象（格式取决于具体实现）
        """
        pass
