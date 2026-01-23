"""工具转换器 - 在不同 Agent 框架之间转换工具格式"""

import asyncio
import inspect
import json
import logging
from typing import Any, Callable

from qwen_agent.tools.base import BaseTool, register_tool

logger = logging.getLogger(__name__)


class OpenAIToolWrapper(BaseTool):
    """OpenAI 工具包装器 - 将 OpenAI FunctionTool 转换为 Qwen-Agent BaseTool"""

    def __init__(self, openai_tool: Any):
        """初始化工具包装器

        Args:
            openai_tool: OpenAI FunctionTool 对象
        """
        self.openai_tool = openai_tool
        self._extract_tool_info()

    def _extract_tool_info(self):
        """从 OpenAI FunctionTool 提取工具信息"""
        # 获取工具函数
        if hasattr(self.openai_tool, 'on_invoke_tool'):
            # OpenAI Agents SDK FunctionTool 格式
            invoke_func = self.openai_tool.on_invoke_tool

            # 从闭包中提取原始实现函数
            # 闭包的第一个元素通常是 _on_invoke_tool_impl（真正的实现）
            original_func = None
            if hasattr(invoke_func, '__closure__') and invoke_func.__closure__:
                try:
                    # 获取第一个闭包变量（通常是实现函数）
                    first_cell = invoke_func.__closure__[0]
                    cell_content = first_cell.cell_contents
                    if callable(cell_content):
                        original_func = cell_content
                        logger.info(f"Found implementation function in closure: {getattr(cell_content, '__name__', 'unknown')}")
                except (AttributeError, ValueError, IndexError) as e:
                    logger.warning(f"Failed to extract function from closure: {e}")

            self.func = original_func if original_func else invoke_func
            self.name = self.openai_tool.name
            self.description = self.openai_tool.description
        elif hasattr(self.openai_tool, 'func'):
            self.func = self.openai_tool.func
            self.name = getattr(self.func, '__name__', 'unknown_tool')
            self.description = getattr(self.func, '__doc__', '') or f"Tool: {self.name}"
        elif callable(self.openai_tool):
            self.func = self.openai_tool
            self.name = getattr(self.func, '__name__', 'unknown_tool')
            self.description = getattr(self.func, '__doc__', '') or f"Tool: {self.name}"
        else:
            raise ValueError(f"Cannot extract function from tool: {self.openai_tool}")

        # 设置参数（Qwen-Agent 格式）
        self.parameters = []

        logger.info(f"Wrapped OpenAI tool: {self.name}")

    def call(self, params: str, **kwargs) -> str:
        """调用工具

        Args:
            params: JSON 格式的参数字符串
            **kwargs: 额外参数

        Returns:
            工具执行结果
        """
        try:
            # 解析参数
            if params:
                args_dict = json.loads(params) if isinstance(params, str) else params
            else:
                args_dict = {}

            logger.info(f"Calling tool {self.name} with params: {args_dict}")

            # 调用原始函数
            result = self.func(**args_dict)

            # 处理异步函数
            if inspect.iscoroutine(result):
                result = asyncio.run(result)

            return str(result)

        except Exception as e:
            error_msg = f"Tool {self.name} execution failed: {e}"
            logger.error(error_msg)
            return error_msg
