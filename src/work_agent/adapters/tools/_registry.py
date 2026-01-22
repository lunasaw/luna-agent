"""Tool 注册表 - 自动发现与注册机制"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Tool 注册表（自动发现）"""

    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def load_tools(self) -> list[Any]:
        """
        自动扫描并加载所有 tools

        Returns:
            list[Any]: 工具列表

        Raises:
            SystemExit: 发现 tool name 冲突时 fail-fast
        """
        tools_dir = Path(__file__).parent
        package_name = "work_agent.adapters.tools"

        logger.info(f"Scanning tools directory: {tools_dir}")

        # 扫描所有 .py 文件
        for module_info in pkgutil.iter_modules([str(tools_dir)]):
            module_name = module_info.name

            # 跳过私有模块和 __init__
            if module_name.startswith("_") or module_name == "__init__":
                continue

            full_module_name = f"{package_name}.{module_name}"

            try:
                # 动态导入
                module = importlib.import_module(full_module_name)

                # 查找 get_tool() 函数
                if not hasattr(module, "get_tool"):
                    logger.warning(
                        f"Tool module '{module_name}' missing get_tool() function, skipped"
                    )
                    continue

                # 获取 tool
                tool = module.get_tool()

                # 检查 name 冲突
                tool_name = getattr(tool, "name", module_name)
                if tool_name in self.tools:
                    logger.error(
                        f"Tool name conflict detected: '{tool_name}' "
                        f"(from {module_name} and {self.tools[tool_name]['module']})"
                    )
                    raise RuntimeError(f"Tool name conflict: {tool_name}")

                # 注册
                self.tools[tool_name] = {
                    "tool": tool,
                    "module": module_name,
                }

                logger.info(f"Loaded tool: {tool_name} (from {module_name})")

            except Exception as e:
                logger.error(
                    f"Failed to load tool from '{module_name}': {e}",
                    exc_info=True,
                    extra={"module": module_name},
                )
                # 继续加载其他 tools（可选：改为 fail-fast）
                continue

        logger.info(f"Total tools loaded: {len(self.tools)}")

        # 返回 tool 对象列表
        return [item["tool"] for item in self.tools.values()]

    def get_tool(self, name: str) -> Any | None:
        """
        根据名称获取 tool

        Args:
            name: Tool 名称

        Returns:
            Tool 对象或 None
        """
        item = self.tools.get(name)
        return item["tool"] if item else None

    def list_tools(self) -> list[dict[str, str]]:
        """
        列出所有 tools 的元信息

        Returns:
            list[dict]: [{name, description, module}, ...]
        """
        result = []
        for name, item in self.tools.items():
            tool = item["tool"]
            description = getattr(tool, "description", "No description")
            result.append(
                {
                    "name": name,
                    "description": description,
                    "module": item["module"],
                }
            )
        return result
