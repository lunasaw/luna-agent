"""CLI 冒烟测试（集成测试）"""

import os

import pytest

# 仅在设置 RUN_INTEGRATION=1 时运行
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Integration tests disabled (set RUN_INTEGRATION=1 to enable)",
)


def test_cli_import():
    """测试 CLI 模块可导入"""
    from work_agent.app import cli

    assert cli is not None


def test_config_load():
    """测试配置加载（需要有效 .env）"""
    # 跳过如果没有 API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from work_agent.config import load_config

    config = load_config()
    assert config.openai_api_key
    assert config.agent_model


def test_tool_registry_integration():
    """测试工具注册表集成"""
    from work_agent.adapters.tools._registry import ToolRegistry

    registry = ToolRegistry()
    tools = registry.load_tools()

    assert len(tools) >= 2  # 至少有 time_now 和 shell_echo
