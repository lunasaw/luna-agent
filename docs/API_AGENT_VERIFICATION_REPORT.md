# API Agent 支持验证报告

## 测试日期
2026-01-23

## 被测试 API
- **名称**: xychatai (示例)
- **URL**: https://api.xychatai.com/chatgpt/v1/chat/completions
- **模型**: gpt-5

> ⚠️ **安全提示**: 测试报告中不包含真实的 API key。如需测试，请使用环境变量配置。

## 测试结果

### 1. 基础对话功能
- **状态**: ✅ **支持**
- **详情**: API 成功响应了简单的对话请求
- **响应示例**: "好的。请问你希望我用中文还是英文回复？..."

### 2. Function Calling 支持
- **状态**: ❌ **不支持**
- **详情**: API 接受了 `tools` 参数，但没有返回工具调用（tool_calls），而是直接返回了文本回复
- **响应行为**: 模型直接回答"没有联网能力"而不是调用提供的 `get_weather` 工具

### 3. 流式 Function Calling
- **状态**: ⚠️  **未检测到**
- **原因**: 基础 function calling 不支持，因此未测试流式

## Agent 兼容性评估

### ❌ 不兼容 OpenAI Agents SDK

**原因**:
1. 该 API 虽然使用 OpenAI 兼容的 chat completions 格式
2. 但底层模型 **不支持 function calling (工具调用)**
3. OpenAI Agents SDK 严重依赖 function calling 功能来实现工具的调用

### 技术分析

该 API 的行为表明：
- 接受标准 OpenAI API 格式（包括 `tools` 参数）
- 但底层模型不理解或不执行工具调用
- 当提供工具定义时，模型选择直接回答而非调用工具

这是因为：
- 该 API 可能使用的是不支持 function calling 的模型
- 或者 API 网关层面没有正确实现 function calling 的代理

## 对比：支持 Function Calling 的 API

一个支持 function calling 的 API 响应应该包含：

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "id": "call_xxx",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"city\": \"北京\"}"
        }
      }]
    }
  }]
}
```

而当前 API 返回的是：

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "我这边没有直接联网获取...（纯文本回复）"
    }
  }]
}
```

## 建议

### 如果你想使用 OpenAI Agents SDK:

#### 方案 1: 使用支持 Function Calling 的 API（推荐）

**官方 OpenAI API:**
```bash
OPENAI_API_KEY=sk-your-real-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
AGENT_MODEL=gpt-4o
```

**vLLM 本地部署:**
```bash
# 启动 vLLM
./scripts/start_vllm.sh

# 配置
OPENAI_API_KEY=EMPTY
OPENAI_API_BASE=http://localhost:8000/v1
AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct
```

支持 Function Calling 的开源模型：
- Qwen/Qwen2.5-7B-Instruct ✅
- Qwen/Qwen2.5-14B-Instruct ✅
- meta-llama/Llama-3.1-8B-Instruct ✅
- mistralai/Mistral-7B-Instruct-v0.3 ✅
- NousResearch/Hermes-2-Pro-Llama-3-8B ✅

#### 方案 2: 仅用于基础对话（不推荐）

如果你只需要简单的对话而不需要工具调用，可以：
1. 移除所有 tools 定义
2. 不使用 OpenAI Agents SDK
3. 直接使用 requests 或 openai 库调用

#### 方案 3: 联系 API 提供商

询问 API 提供商：
1. 是否支持 function calling / tool use
2. 如果支持，需要哪些特殊配置
3. 是否有支持 function calling 的模型可用

## 测试脚本使用

验证其他 API 是否支持 Agent 功能：

```bash
# 使用环境变量配置（推荐，安全）
export TEST_API_URL=https://your-api.com/v1/chat/completions
export TEST_API_KEY=your_api_key_here
export TEST_API_MODEL=gpt-4o

# 运行测试
.venv/bin/python tests/unit/verify_api_agent_support.py
```

**安全提示**:
- ⚠️ 不要在代码中硬编码 API key
- ✅ 使用环境变量
- ✅ 或从 `.env` 文件读取（确保 `.env` 在 `.gitignore` 中）

## 参考文档

- [vLLM 集成指南](../../docs/VLLM_INTEGRATION.md)
- [vLLM 快速开始](../../docs/VLLM_QUICK_START.md)
- [OpenAI Function Calling 文档](https://platform.openai.com/docs/guides/function-calling)
- [支持 Function Calling 的模型列表](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#tool-calling)

## 结论

**该 API (xychatai) 不能直接用于 OpenAI Agents SDK**，因为它不支持 function calling 功能。

建议：
1. ✅ 使用 OpenAI 官方 API
2. ✅ 或使用 vLLM 本地部署支持 function calling 的开源模型
3. ❌ 不建议使用当前测试的 API 用于 Agent 场景
