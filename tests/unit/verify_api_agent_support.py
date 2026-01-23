#!/usr/bin/env python3
"""测试自定义 API 是否支持 Agent function calling

此脚本测试自定义 API 端点是否支持 OpenAI Agents SDK 的 function calling 功能。

使用方法:
    # 方式 1: 使用环境变量（推荐，安全）
    export TEST_API_URL=https://api.example.com/v1/chat/completions
    export TEST_API_KEY=your_api_key_here
    export TEST_API_MODEL=gpt-5
    python tests/unit/verify_api_agent_support.py

    # 方式 2: 从 test_chat.py 读取配置
    # 编辑脚本，取消注释相关代码段
"""

import json
import logging
import os
import sys
from pathlib import Path

import requests

# 直接定义测试配置（从 test_chat.py 提取）
# ⚠️ 安全提示: 不要在这里硬编码真实的 API key！
# 请使用环境变量或从配置文件读取

# 方式 1: 从环境变量读取（推荐）
# export TEST_API_KEY=your_api_key
# export TEST_API_URL=https://api.example.com/v1/chat/completions

# 方式 2: 从 test_chat.py 读取（需要安装 pandas）
# 取消下面的注释来使用:
# try:
#     current_dir = Path(__file__).parent
#     sys.path.insert(0, str(current_dir))
#     import test_chat
#     CHANNELS = test_chat.CHANNELS
# except ImportError:
#     CHANNELS = []

# 示例配置（使用环境变量）
CHANNELS = [
    {
        "name": os.getenv("TEST_API_NAME", "test_api"),
        "api_url": os.getenv("TEST_API_URL", ""),
        "api_key": os.getenv("TEST_API_KEY", ""),
        "weight": 70,
        "timeout": 60,
        "model": os.getenv("TEST_API_MODEL", "gpt-4o"),
        "degraded_check": "GPT",
        "use_system_role": False,
    },
]

# 过滤掉空配置
CHANNELS = [ch for ch in CHANNELS if ch["api_url"] and ch["api_key"]]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_basic_chat(api_url: str, api_key: str, model: str) -> bool:
    """测试基础对话功能

    Returns:
        bool: 是否支持基础对话
    """
    logger.info("=" * 60)
    logger.info("测试 1: 基础对话功能")
    logger.info("=" * 60)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "你好，请简单回复"}
        ],
        "stream": False,
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            logger.error(f"❌ HTTP 状态码: {response.status_code}")
            logger.error(f"响应: {response.text}")
            return False

        # 尝试解析 JSON
        try:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"✅ 基础对话成功")
            logger.info(f"响应: {content[:100]}...")
            return True
        except json.JSONDecodeError:
            # 可能是 SSE 格式，尝试解析流式响应
            logger.info("检测到流式响应格式，尝试解析...")
            content = parse_sse_response(response.text)
            if content:
                logger.info(f"✅ 基础对话成功 (流式)")
                logger.info(f"响应: {content[:100]}...")
                return True
            else:
                logger.error("❌ 无法解析响应")
                return False

    except Exception as e:
        logger.error(f"❌ 请求失败: {e}")
        return False


def parse_sse_response(text: str) -> str:
    """解析 SSE 格式的响应

    Args:
        text: SSE 格式文本

    Returns:
        str: 提取的内容
    """
    content = ""
    for line in text.split('\n'):
        if line.startswith('data: '):
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                delta = data.get("choices", [{}])[0].get("delta", {})
                content += delta.get("content", "")
            except json.JSONDecodeError:
                continue
    return content


def test_function_calling(api_url: str, api_key: str, model: str) -> dict:
    """测试 function calling 功能

    Returns:
        dict: 测试结果
            {
                "supported": bool,
                "format": str | None,  # "openai", "hermes", etc.
                "details": str
            }
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试 2: Function Calling 支持")
    logger.info("=" * 60)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 定义一个简单的工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定城市的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，如北京、上海"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "北京现在的天气怎么样？"}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "stream": False,
    }

    result = {
        "supported": False,
        "format": None,
        "details": ""
    }

    try:
        logger.info("发送 function calling 请求...")
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            result["details"] = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.warning(f"❌ HTTP 状态码: {response.status_code}")
            logger.warning(f"可能不支持 function calling")
            return result

        # 尝试解析 JSON 或 SSE
        try:
            data = response.json()
        except json.JSONDecodeError:
            # 尝试解析 SSE 格式
            logger.info("检测到流式响应，解析 SSE 格式...")
            data = parse_sse_to_message(response.text)
            if not data:
                result["details"] = "无法解析响应格式"
                logger.error("❌ 无法解析 SSE 响应")
                return result

        logger.info("✅ 请求成功，分析响应...")

        # 检查响应格式
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {}) or choice.get("delta", {})

        # 检查 OpenAI 格式的 tool_calls
        if "tool_calls" in message:
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                result["supported"] = True
                result["format"] = "openai"
                result["details"] = f"检测到 {len(tool_calls)} 个工具调用"

                logger.info("✅ 支持 OpenAI 格式的 function calling")
                logger.info(f"工具调用: {json.dumps(tool_calls, ensure_ascii=False, indent=2)}")
                return result

        # 检查是否有 function_call (旧格式)
        if "function_call" in message:
            result["supported"] = True
            result["format"] = "openai_legacy"
            result["details"] = "使用旧版 function_call 格式"
            logger.info("✅ 支持 OpenAI 旧版 function calling 格式")
            return result

        # 检查响应内容
        content = message.get("content", "")
        if content:
            result["details"] = f"未检测到工具调用，仅返回文本: {content[:100]}"
            logger.warning("⚠️  API 接受了 tools 参数但未返回工具调用")
            logger.warning(f"响应内容: {content[:200]}")

        return result

    except Exception as e:
        result["details"] = f"请求异常: {str(e)}"
        logger.error(f"❌ 测试失败: {e}")
        return result


def parse_sse_to_message(text: str) -> dict:
    """将 SSE 格式转换为消息格式

    Args:
        text: SSE 格式文本

    Returns:
        dict: 消息字典
    """
    # 收集所有 delta
    deltas = []
    for line in text.split('\n'):
        if line.startswith('data: '):
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                if "choices" in data and data["choices"]:
                    delta = data["choices"][0].get("delta", {})
                    deltas.append(delta)
            except json.JSONDecodeError:
                continue

    # 合并 deltas
    merged = {"content": "", "role": "assistant"}
    tool_calls_parts = {}

    for delta in deltas:
        # 合并 content
        if "content" in delta:
            merged["content"] += delta["content"]

        # 合并 role
        if "role" in delta:
            merged["role"] = delta["role"]

        # 合并 tool_calls
        if "tool_calls" in delta:
            for tc in delta["tool_calls"]:
                idx = tc.get("index", 0)
                if idx not in tool_calls_parts:
                    tool_calls_parts[idx] = {
                        "id": tc.get("id", ""),
                        "type": tc.get("type", "function"),
                        "function": {"name": "", "arguments": ""}
                    }

                if "id" in tc:
                    tool_calls_parts[idx]["id"] = tc["id"]
                if "type" in tc:
                    tool_calls_parts[idx]["type"] = tc["type"]
                if "function" in tc:
                    func = tc["function"]
                    if "name" in func:
                        tool_calls_parts[idx]["function"]["name"] += func["name"]
                    if "arguments" in func:
                        tool_calls_parts[idx]["function"]["arguments"] += func["arguments"]

    if tool_calls_parts:
        merged["tool_calls"] = [tool_calls_parts[i] for i in sorted(tool_calls_parts.keys())]

    return {"choices": [{"message": merged}]} if merged else {}


def test_streaming_function_calling(api_url: str, api_key: str, model: str) -> bool:
    """测试流式 function calling

    Returns:
        bool: 是否支持流式 function calling
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试 3: 流式 Function Calling")
    logger.info("=" * 60)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "获取当前时间",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ]

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "现在几点了？"}
        ],
        "tools": tools,
        "stream": True,
    }

    try:
        logger.info("发送流式 function calling 请求...")
        response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)

        if response.status_code != 200:
            logger.warning(f"❌ HTTP {response.status_code}")
            return False

        has_tool_call = False
        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})

                    if "tool_calls" in delta:
                        has_tool_call = True
                        logger.info(f"检测到流式工具调用: {delta.get('tool_calls')}")

                except json.JSONDecodeError:
                    continue

        if has_tool_call:
            logger.info("✅ 支持流式 function calling")
            return True
        else:
            logger.warning("⚠️  未检测到流式工具调用")
            return False

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


def generate_report(channel_name: str, results: dict) -> None:
    """生成测试报告

    Args:
        channel_name: 渠道名称
        results: 测试结果
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"测试报告: {channel_name}")
    logger.info("=" * 60)

    logger.info(f"基础对话: {'✅ 支持' if results['basic_chat'] else '❌ 不支持'}")

    fc_result = results['function_calling']
    if fc_result['supported']:
        logger.info(f"Function Calling: ✅ 支持 ({fc_result['format']})")
        logger.info(f"  详情: {fc_result['details']}")
    else:
        logger.info(f"Function Calling: ❌ 不支持")
        logger.info(f"  详情: {fc_result['details']}")

    logger.info(f"流式 Function Calling: {'✅ 支持' if results['streaming_fc'] else '⚠️  未检测到'}")

    logger.info("")
    logger.info("Agent 兼容性评估:")

    if results['basic_chat'] and fc_result['supported']:
        logger.info("✅ 该 API 可以用于 OpenAI Agents SDK")
        logger.info("建议配置:")
        logger.info("  OPENAI_API_BASE=<该 API 的 URL>")
        logger.info("  OPENAI_API_KEY=<该 API 的 Key>")
        logger.info("  AGENT_MODEL=<该 API 的模型名>")
    elif results['basic_chat']:
        logger.warning("⚠️  该 API 支持基础对话但不支持 function calling")
        logger.warning("无法用于需要工具调用的 Agent 场景")
        logger.warning("建议使用支持 function calling 的 API 或模型")
    else:
        logger.error("❌ 该 API 连基础对话都不支持")

    logger.info("=" * 60)


def main():
    """主函数"""
    logger.info("🔍 API Agent 支持验证工具")
    logger.info("")

    if not CHANNELS:
        logger.error("❌ 未找到任何配置的渠道")
        logger.error("请检查 tests/unit/test_chat.py 中的 CHANNELS 配置")
        return

    logger.info(f"找到 {len(CHANNELS)} 个渠道配置")
    logger.info("")

    # 测试每个渠道
    for i, channel_cfg in enumerate(CHANNELS, 1):
        channel_name = channel_cfg.get("name", f"channel_{i}")
        api_url = channel_cfg.get("api_url")
        api_key = channel_cfg.get("api_key")
        model = channel_cfg.get("model", "gpt-5")

        logger.info(f"\n{'='*60}")
        logger.info(f"测试渠道 {i}/{len(CHANNELS)}: {channel_name}")
        logger.info(f"API URL: {api_url}")
        logger.info(f"Model: {model}")
        logger.info(f"{'='*60}")

        if not api_url or not api_key:
            logger.error("❌ 缺少 API URL 或 API Key，跳过")
            continue

        # 执行测试
        results = {
            "basic_chat": test_basic_chat(api_url, api_key, model),
            "function_calling": test_function_calling(api_url, api_key, model),
            "streaming_fc": False,
        }

        # 只有基础对话成功才测试流式
        if results["basic_chat"] and results["function_calling"]["supported"]:
            results["streaming_fc"] = test_streaming_function_calling(api_url, api_key, model)

        # 生成报告
        generate_report(channel_name, results)


if __name__ == "__main__":
    main()
