"""Tool 脚手架生成器

用于快速生成 API Tool 的模板代码
"""
import os
from pathlib import Path


def generate_api_client_template(api_name: str, output_dir: str = ".") -> str:
    """生成 API 客户端模板

    Args:
        api_name: API 名称（如 "weather", "github"）
        output_dir: 输出目录

    Returns:
        生成的文件路径
    """
    class_name = "".join(word.capitalize() for word in api_name.split("_"))

    template = f'''"""## {class_name} API 客户端"""
import logging
from typing import Any

from work_agent.adapters.external.apis.base import BaseApiClient
from work_agent.utils.api_client import ApiResponse

logger = logging.getLogger(__name__)


class {class_name}ApiClient(BaseApiClient):
    """## {class_name} API 客户端封装

    职责：
    - 封装 {class_name} API 调用细节
    - 处理认证
    - 返回结构化数据
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: float = 30.0,
        retry_count: int = 2,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            retry_count=retry_count,
        )

        # 配置认证（根据实际 API 修改）
        if api_key:
            self.set_api_key("X-API-Key", api_key)
            # 或使用 Bearer Token: self.set_auth_token(api_key)

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            服务是否可用
        """
        try:
            # TODO: 实现实际的健康检查逻辑
            response = await self.client.get("/health")
            return response.ok
        except Exception as e:
            logger.error(f"Health check failed: {{e}}")
            return False

    async def example_method(self, param: str) -> dict[str, Any]:
        """示例方法（请根据实际 API 修改）

        Args:
            param: 参数示例

        Returns:
            API 响应数据

        Raises:
            ApiClientError: API 调用失败
        """
        logger.info(f"Calling example_method with param={{param}}")

        response = await self.client.get(
            "/example/endpoint",
            params={{"q": param}},
            raise_for_status=True,
        )

        return response.body
'''

    output_path = Path(output_dir) / f"{api_name}_api.py"
    output_path.write_text(template, encoding="utf-8")
    return str(output_path)


def generate_service_template(api_name: str, output_dir: str = ".") -> str:
    """生成服务层模板

    Args:
        api_name: API 名称
        output_dir: 输出目录

    Returns:
        生成的文件路径
    """
    class_name = "".join(word.capitalize() for word in api_name.split("_"))

    template = f'''"""## {class_name} 业务服务层"""
import logging
from typing import Any

from work_agent.adapters.external.apis.{api_name}_api import {class_name}ApiClient
from work_agent.domain.errors import DomainError
from work_agent.utils.api_client import ApiClientError

logger = logging.getLogger(__name__)


class {class_name}ServiceError(DomainError):
    """## {class_name} 服务异常"""
    pass


class {class_name}Service:
    """## {class_name} 业务服务

    职责：
    - 业务逻辑编排
    - 数据转换和格式化
    - 异常转换（API 异常 → 领域异常）
    """

    def __init__(self, api_client: {class_name}ApiClient) -> None:
        self.api = api_client

    async def example_business_method(self, param: str) -> str:
        """示例业务方法（格式化输出）

        Args:
            param: 参数示例

        Returns:
            格式化的结果字符串

        Raises:
            {class_name}ServiceError: 操作失败
        """
        try:
            logger.info(f"Executing example_business_method with param={{param}}")

            # 调用 API
            data = await self.api.example_method(param)

            # 格式化输出（示例）
            result = f"✅ 操作成功\\n"
            result += f"数据: {{data}}\\n"

            return result

        except ApiClientError as e:
            logger.error(f"API call failed: {{e}}", exc_info=True)
            raise {class_name}ServiceError(f"操作失败: {{e}}") from e
'''

    output_path = Path(output_dir) / f"{api_name}_service.py"
    output_path.write_text(template, encoding="utf-8")
    return str(output_path)


def generate_tool_template(api_name: str, output_dir: str = ".") -> str:
    """生成 Tool 模板

    Args:
        api_name: API 名称
        output_dir: 输出目录

    Returns:
        生成的文件路径
    """
    class_name = "".join(word.capitalize() for word in api_name.split("_"))
    tool_name = api_name

    template = f'''"""## {class_name} Tool - Agent 可调用的工具"""
from typing import Any
from agents import function_tool

# 延迟初始化模式（从容器获取服务）
_service = None


def _get_service():
    """获取 {class_name} 服务实例（从容器注入）"""
    global _service
    if _service is None:
        from work_agent.container import get_{api_name}_service
        _service = get_{api_name}_service()
    return _service


@function_tool
async def {tool_name}_example_tool(param: str) -> str:
    """
    ## 示例工具函数

    TODO: 修改此处的描述，让 LLM 理解这个工具的功能

    Args:
        param: 参数描述

    Returns:
        返回值描述

    Examples:
        - {tool_name}_example_tool("test")
    """
    # 参数校验
    if not param or not param.strip():
        return "错误: 参数不能为空"

    # 调用服务层
    service = _get_service()
    return await service.example_business_method(param)


def get_tool() -> Any:
    """暴露工具供自动发现"""
    # 单个工具: return {tool_name}_example_tool
    # 多个工具: return [{tool_name}_example_tool, another_tool]
    return {tool_name}_example_tool
'''

    output_path = Path(output_dir) / f"{api_name}_tool.py"
    output_path.write_text(template, encoding="utf-8")
    return str(output_path)


def generate_full_scaffold(api_name: str, project_root: str = ".") -> dict[str, str]:
    """生成完整的 API Tool 脚手架

    Args:
        api_name: API 名称（如 "weather", "github"）
        project_root: 项目根目录

    Returns:
        生成的文件路径字典
    """
    paths = {}

    # 确保目录存在
    apis_dir = Path(project_root) / "src/work_agent/adapters/external/apis"
    services_dir = Path(project_root) / "src/work_agent/adapters/external/services"
    tools_dir = Path(project_root) / "src/work_agent/adapters/tools"

    for dir_path in [apis_dir, services_dir, tools_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # 生成文件
    paths["api"] = generate_api_client_template(api_name, str(apis_dir))
    paths["service"] = generate_service_template(api_name, str(services_dir))
    paths["tool"] = generate_tool_template(api_name, str(tools_dir))

    print(f"✅ 已生成 {api_name} 的完整脚手架:")
    for key, path in paths.items():
        print(f"  - {key}: {path}")

    print(f"\n📝 下一步:")
    print(f"  1. 在 config.py 中添加 {api_name} 的配置项")
    print(f"  2. 在 .env.example 中添加环境变量示例")
    print(f"  3. 实现 {paths['api']} 中的 API 调用逻辑")
    print(f"  4. 实现 {paths['service']} 中的业务逻辑")
    print(f"  5. 完善 {paths['tool']} 中的工具描述和参数")
    print(f"  6. 在 container.py 中注册服务")
    print(f"  7. 编写测试: tests/unit/test_{api_name}_api.py")

    return paths


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python scaffold_generator.py <api_name> [project_root]")
        print("示例: python scaffold_generator.py weather /path/to/project")
        sys.exit(1)

    api_name = sys.argv[1]
    project_root = sys.argv[2] if len(sys.argv) > 2 else "."

    generate_full_scaffold(api_name, project_root)
