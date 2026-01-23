#!/usr/bin/env python3
"""
完整的 DashScope Qwen Agent 接入示例

参考文档: https://help.aliyun.com/zh/model-studio/qwen-function-calling

此脚本演示如何使用阿里云 DashScope 的 Qwen 模型运行 Agent，
包括 function calling (工具调用) 功能。
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from work_agent.config import load_config
from work_agent.container import build_container, set_global_container
from work_agent.logging import configure_logging


def setup_dashscope_config():
    """配置 DashScope 环境变量"""

    # DashScope API 配置
    # 从环境变量读取，或使用默认值
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")

    if not dashscope_key:
        print("⚠️  警告: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("\n请设置环境变量:")
        print("  export DASHSCOPE_API_KEY=sk-your-api-key-here")
        print("\n或在 .env 文件中添加:")
        print("  DASHSCOPE_API_KEY=sk-your-api-key-here")
        print("\nAPI Key 获取地址:")
        print("  https://dashscope.console.aliyun.com/apiKey")
        sys.exit(1)

    # 设置 OpenAI 兼容配置
    # DashScope 提供 OpenAI 兼容的 API 端点
    os.environ["OPENAI_API_KEY"] = dashscope_key
    os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 选择模型 (支持 function calling 的模型)
    # qwen-plus: 通用场景，性能强（推荐）
    # qwen-turbo: 快速响应
    # qwen-max: 复杂任务，最强性能
    # qwen-long: 长文本处理
    model = os.getenv("AGENT_MODEL", "qwen-plus")
    os.environ["AGENT_MODEL"] = model

    print("🔧 DashScope 配置:")
    print(f"  API Base: https://dashscope.aliyuncs.com/compatible-mode/v1")
    print(f"  模型: {model}")
    print(f"  API Key: {dashscope_key[:10]}...{dashscope_key[-4:]}")
    print()


def test_basic_conversation(container):
    """测试基础对话功能"""
    print("=" * 60)
    print("测试 1: 基础对话")
    print("=" * 60)

    query = "你好，请介绍一下你自己"
    print(f"查询: {query}")
    print()

    result = container.agent_service.run_once(query)
    print(f"响应: {result}")
    print()


def test_tool_calling(container):
    """测试工具调用功能"""
    print("=" * 60)
    print("测试 2: 工具调用 (Function Calling)")
    print("=" * 60)

    # 测试时间工具
    query1 = "现在几点了？"
    print(f"查询 1: {query1}")
    print()

    result1 = container.agent_service.run_once(query1)
    print(f"响应: {result1}")
    print()

    # 测试天气工具（需要配置 WEATHER_API_KEY）
    weather_key = os.getenv("WEATHER_API_KEY", "")
    if weather_key:
        query2 = "查询北京的天气"
        print(f"查询 2: {query2}")
        print()

        result2 = container.agent_service.run_once(query2)
        print(f"响应: {result2}")
        print()
    else:
        print("⚠️  跳过天气查询测试 (未设置 WEATHER_API_KEY)")
        print("  提示: export WEATHER_API_KEY=your_key")
        print()


def test_multi_turn_conversation(container):
    """测试多轮对话"""
    print("=" * 60)
    print("测试 3: 多轮对话")
    print("=" * 60)

    # 注意: run_once 不保存对话历史
    # 如需多轮对话，使用 repl 模式或自行管理 session

    queries = [
        "我想了解一下北京的情况",
        "现在几点了？",
        "帮我查一下北京的天气",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n第 {i} 轮:")
        print(f"查询: {query}")
        print()

        result = container.agent_service.run_once(query)
        print(f"响应: {result[:200]}...")
        print()


def list_available_tools(container):
    """列出可用的工具"""
    print("=" * 60)
    print("可用的工具列表")
    print("=" * 60)

    tools = container.tools
    print(f"\n共 {len(tools)} 个工具:\n")

    for tool in tools:
        name = getattr(tool, "name", "unknown")
        description = getattr(tool, "description", "No description")
        print(f"  • {name}")
        print(f"    {description}")
        print()


def main():
    """主函数"""
    print("🚀 DashScope Qwen Agent 完整示例")
    print()

    # 1. 配置 DashScope
    setup_dashscope_config()

    # 2. 配置日志
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(log_level)

    # 3. 构建容器
    print("正在构建 Agent 容器...")
    config = load_config()
    container = build_container(config)
    set_global_container(container)
    print(f"✅ 容器构建成功，加载了 {len(container.tools)} 个工具")
    print()

    # 4. 列出可用工具
    list_available_tools(container)

    # 5. 运行测试
    try:
        # 基础对话
        test_basic_conversation(container)

        # 工具调用
        test_tool_calling(container)

        # 多轮对话
        test_multi_turn_conversation(container)

        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print()
        print("使用建议:")
        print("  1. 单次查询: python -m work_agent run '你的问题'")
        print("  2. 交互模式: python -m work_agent repl")
        print("  3. 查看工具: python -m work_agent list-tools")
        print()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
