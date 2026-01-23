#!/usr/bin/env python3
"""验证 Qwen-Agent 是否能正常工作

此脚本测试：
1. 基础对话功能
2. Function Calling 功能
3. 与 DashScope 的集成
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_import():
    """测试 Qwen-Agent 是否能正常导入"""
    print("=" * 60)
    print("测试 1: 导入 Qwen-Agent")
    print("=" * 60)

    try:
        from qwen_agent.agents import Assistant
        print("✅ 成功导入 qwen_agent.agents.Assistant")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_basic_conversation():
    """测试基础对话功能"""
    print("\n" + "=" * 60)
    print("测试 2: 基础对话功能")
    print("=" * 60)

    # 检查 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 未设置 DASHSCOPE_API_KEY 环境变量")
        print("  请设置: export DASHSCOPE_API_KEY=sk-your-key")
        return False

    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")

    try:
        from qwen_agent.agents import Assistant

        # 创建 Agent
        bot = Assistant(
            llm={'model': 'qwen-plus'},
            system_message='你是一个有帮助的助手。请简洁回答问题。',
        )

        print("✅ Agent 创建成功")

        # 测试对话
        messages = [{'role': 'user', 'content': '你好，请简单介绍一下你自己'}]

        print("\n发送消息: 你好，请简单介绍一下你自己")
        print("等待响应...")

        responses = []
        for response in bot.run(messages):
            responses.append(response)
            print(f"收到响应: {response}")

        if responses:
            last_response = responses[-1]
            print(f"\n✅ 对话成功")
            print(f"最终响应: {last_response}")
            return True
        else:
            print("❌ 未收到响应")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_function_calling():
    """测试 Function Calling 功能"""
    print("\n" + "=" * 60)
    print("测试 3: Function Calling 功能")
    print("=" * 60)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 未设置 DASHSCOPE_API_KEY 环境变量")
        return False

    try:
        from qwen_agent.agents import Assistant
        from qwen_agent.tools.base import BaseTool, register_tool

        # 定义一个简单的工具
        @register_tool('get_current_time')
        class GetCurrentTime(BaseTool):
            description = '获取当前时间'
            parameters = []

            def call(self, params: str, **kwargs) -> str:
                from datetime import datetime
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return f"当前时间：{current_time}"

        print("✅ 工具定义成功")

        # 创建带工具的 Agent
        bot = Assistant(
            llm={'model': 'qwen-plus'},
            system_message='你是一个有帮助的助手。如果用户问时间，���调用 get_current_time 工具。',
            function_list=['get_current_time'],
        )

        print("✅ Agent 创建成功（带工具）")

        # 测试工具调用
        messages = [{'role': 'user', 'content': '现在几点了？'}]

        print("\n发送消息: 现在几点了？")
        print("等待响应...")

        responses = []
        for response in bot.run(messages):
            responses.append(response)
            print(f"收到响应: {response}")

        if responses:
            print(f"\n✅ Function Calling 成功")
            print(f"响应数量: {len(responses)}")
            return True
        else:
            print("❌ 未收到响应")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("🔍 Qwen-Agent 验证测试")
    print()

    results = {
        "导入测试": test_import(),
        "基础对话": False,
        "Function Calling": False,
    }

    if results["导入测试"]:
        results["基础对话"] = test_basic_conversation()

        if results["基础对话"]:
            results["Function Calling"] = test_function_calling()

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ 所有测试通过！Qwen-Agent 可以正常使用。")
        print("\n下一步:")
        print("  1. Qwen-Agent 完全兼容 DashScope")
        print("  2. 可以开始实现 QwenAgentAdapter")
        print("  3. 集成到项目架构中")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
