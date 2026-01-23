# DashScope 与 OpenAI Agents SDK 兼容性问题

## 问题发现

在测试 DashScope Qwen API 与 OpenAI Agents SDK 集成时，发现了一个关键的兼容性问题。

### 错误信息

```
openai.NotFoundError: Error code: 404
File: openai/resources/responses/responses.py, line 2480, in create
```

## 根本原因

**DashScope 的 "OpenAI 兼容" 并不完全兼容 OpenAI Agents SDK**

### 两种不同的 API

1. **OpenAI Chat Completions API** (标准 API)
   - 端点: `/v1/chat/completions`
   - 用途: 基础对话和 function calling
   - DashScope 支持: ✅ **完全支持**

2. **OpenAI Agents API** (新版 Agents API)
   - 端点: `/v1/responses` (或类似)
   - 用途: OpenAI Agents SDK 专用
   - DashScope 支持: ❌ **不支持**

### 验证结果

| 测试项 | 结果 | 说明 |
|--------|------|------|
| 标准 Chat Completions | ✅ 成功 | curl 测试通过 |
| Function Calling | ✅ 成功 | 返回正确的 tool_calls |
| OpenAI Agents SDK | ❌ 失败 | 404 错误，缺少 responses 端点 |

## 技术细节

### OpenAI Agents SDK 的工作方式

OpenAI Agents SDK 不是简单地调用 `/chat/completions` 端点，而是使用了一套专门的 Agents API：

```python
# Agents SDK 内部调用
await self._client.responses.create(...)  # 这个端点 DashScope 没有
```

### DashScope 的实现

DashScope 的 "OpenAI 兼容模式" 只实现了：
- `/v1/chat/completions` - 标准对话
- `/v1/embeddings` - 文本嵌入
- 等标准端点

但**没有实现** OpenAI Agents API 的专用端点。

## 解决方案

### 方案 1: 使用 OpenAI 官方 API ✅ 推荐

```bash
# .env 配置
OPENAI_API_KEY=sk-your-openai-key
# 不设置 OPENAI_API_BASE，使用默认的 OpenAI API
AGENT_MODEL=gpt-4o
```

**优点**:
- 完全兼容 OpenAI Agents SDK
- 功能最完整
- 稳定可靠

**缺点**:
- 需要 OpenAI API key
- 国内访问需要代理
- 成本较高

### 方案 2: 使用 vLLM 本地部署 ⚠️ 需验证

```bash
# 启动 vLLM
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --served-api-name qwen-7b

# .env 配置
OPENAI_API_KEY=dummy
OPENAI_API_BASE=http://localhost:8000/v1
AGENT_MODEL=qwen-7b
```

**注意**: 需要验证 vLLM 是否支持 Agents API 端点。

### 方案 3: 重构为标准 Chat Completions ⚠️ 需要开发

不使用 OpenAI Agents SDK，直接使用标准的 Chat Completions API + 手动实现 tool calling 逻辑。

**实现思路**:
1. 调用 `/chat/completions` 获取响应
2. 检查是否有 `tool_calls`
3. 执行工具调用
4. 将结果返回给模型
5. 循环直到完成

**优点**:
- 可以使用任何支持 function calling 的 API
- 包括 DashScope、通义千问等

**缺点**:
- 需要重写 agent 逻辑
- 失去 Agents SDK 的高级功能
- 开发和维护成本高

### 方案 4: 使用其他兼容的 LLM 服务

寻找完全兼容 OpenAI Agents API 的其他服务商。

## 更新文档

### DASHSCOPE_INTEGRATION.md 需要更正

之前的文档声称 DashScope "完全支持 OpenAI Agents SDK"，这是**错误的**。

**正确的说法**:
- ✅ DashScope 支持 OpenAI Chat Completions API
- ✅ DashScope 支持 Function Calling
- ❌ DashScope **不支持** OpenAI Agents SDK

## 推荐方案

### 对于生产环境

**推荐使用 OpenAI 官方 API**:
- 最稳定可靠
- 功能最完整
- 与 Agents SDK 完美兼容

### 对于开发测试

**推荐使用 vLLM 本地部署**:
- 成本低
- 响应快
- 数据隐私
- 需要先验证 Agents API 兼容性

### 对于中文场景且不需要 Agents SDK

**可以考虑重构为标准 API**:
- 使用 DashScope 的 Chat Completions API
- 手动实现 tool calling 循环
- 适合简单的 Agent 场景

## 总结

**关键发现**: "OpenAI 兼容" ≠ "OpenAI Agents SDK 兼容"

很多 LLM 服务商声称 "OpenAI 兼容"，但通常只是指兼容标准的 Chat Completions API，并不包括 Agents API。

在选择 LLM 服务时，需要明确区分：
1. **Chat Completions API 兼容** - 基础对话和 function calling
2. **Agents API 兼容** - 完整的 Agents SDK 支持

DashScope 属于前者，不属于后者。

## 下一步行动

1. ✅ 已修复 async/await 问题
2. ✅ 已发现 DashScope 不兼容 Agents SDK
3. ⬜ 选择合适的解决方案
4. ⬜ 更新相关文档
5. ⬜ 测试选定的方案

## 参考

- [OpenAI Agents SDK 文档](https://github.com/openai/openai-agents-sdk)
- [DashScope OpenAI 兼容文档](https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope/)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
