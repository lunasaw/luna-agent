# DashScope Function Calling 支持分析

## 文档来源

基于官方文档：`/data/luna/luna-agent/docs/FUNCTION_CALL.md`

## 核心发现

### 1. DashScope 支持的是什么？

**DashScope 支持标准的 OpenAI Chat Completions API + Function Calling**

从文档第 74-88 行可以看到：

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
```

使用的是标准的 `OpenAI` 客户端，而不是任何特殊的 Agents SDK。

### 2. Function Calling 的工作流程

根据文档第 8-30 行描述的工作原理：

1. **发起第一次模型调用** - 应用程序向大模型发送用户问题和工具清单
2. **接收工具调用指令** - 模型返回 JSON 格式的工具调用信息
3. **在应用端运行工具** - 应用程序执行工具并获取结果
4. **发起第二次模型调用** - 将工具结果添加到上下文，再次调用模型
5. **接收最终响应** - 模型整合信息，生成自然语言回复

**关键点：这是手动的、多步骤的流程，需要应用程序自己管理循环。**

### 3. 使用的 API 端点

从文档第 122-128 行的示例代码：

```python
def get_response(messages):
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        tools=tools,
    )
    return completion
```

**使用的端点：`/v1/chat/completions`**

这是标准的 OpenAI Chat Completions API，不是 Agents API。

### 4. 手动工具调用循环

从文档第 131-164 行的完整示例：

```python
messages = [{"role": "user", "content": USER_QUESTION}]
response = get_response(messages)
assistant_output = response.choices[0].message
messages.append(assistant_output)

# 如果不需要调用工具，直接输出内容
if assistant_output.tool_calls is None:
    print(f"无需调用天气查询工具，直接回复：{assistant_output.content}")
else:
    # 进入工具调用循环
    while assistant_output.tool_calls is not None:
        tool_call = assistant_output.tool_calls[0]
        # 执行工具
        tool_result = get_current_weather(arguments)
        # 构造工具返回信息
        tool_message = {"role": "tool", "tool_call_id": tool_call_id, "content": tool_result}
        messages.append(tool_message)
        # 再次调用模型
        response = get_response(messages)
        assistant_output = response.choices[0].message
        messages.append(assistant_output)
```

**关键特征：**
- 应用程序需要自己实现 `while` 循环
- 应用程序需要手动执行工具函数
- 应用程序需要手动管理 messages 数组
- 每次工具调用都需要再次调用 `chat.completions.create()`

## OpenAI Agents SDK vs DashScope Function Calling

### OpenAI Agents SDK 的工作方式

```python
from agents import Agent, Runner

agent = Agent(
    name="work-agent",
    instructions="...",
    model="gpt-4o",
    tools=tools,
)

runner = Runner()
response = await runner.run(agent, user_input)  # 自动处理所有循环
```

**特征：**
- 使用 `agents` SDK（不是标准的 `openai` SDK）
- 调用 `runner.run()` 自动处理整个工具调用循环
- 内部使用 `/v1/responses` 等 Agents API 端点
- 不需要手动管理 messages 或循环

### 关键区别对比

| 特性 | DashScope Function Calling | OpenAI Agents SDK |
|------|---------------------------|-------------------|
| SDK | 标准 `openai` SDK | 专用 `agents` SDK |
| API 端点 | `/v1/chat/completions` | `/v1/responses` 等 |
| 工具调用循环 | 手动实现 `while` 循环 | 自动处理 |
| Messages 管理 | 手动管理 | 自动管理 |
| 工具执行 | 应用程序手动执行 | SDK 自动调用 |
| 代码复杂度 | 较高（需要自己写循环） | 较低（一行调用） |

## 最终结论

### DashScope 是否支持 OpenAI Agents SDK？

**❌ 不支持**

**原因：**

1. **API 端点不兼容**
   - DashScope 只实现了 `/v1/chat/completions` 端点
   - OpenAI Agents SDK 需要 `/v1/responses` 等 Agents API 专用端点
   - 这是两套完全不同的 API

2. **架构设计不同**
   - DashScope 的 Function Calling 是"手动模式"
   - OpenAI Agents SDK 是"自动模式"
   - 无法通过配置让 Agents SDK 使用 Chat Completions API

3. **实际测试结果**
   - 运行 `examples/dashscope_example.py` 时出现 404 错误
   - 错误位置：`openai/resources/responses/responses.py`
   - 说明 Agents SDK 尝试访问 DashScope 不存在的端点

### DashScope 支持什么？

**✅ 完全支持 Function Calling**

DashScope 完全支持标准的 OpenAI Function Calling 功能：
- ✅ 工具定义（tools 参数）
- ✅ 工具调用指令（tool_calls 返回）
- ✅ 并行工具调用（parallel_tool_calls）
- ✅ 强制工具调用（tool_choice）
- ✅ 流式输出（stream=True）
- ✅ 多轮对话

**但需要手动实现工具调用循环。**

## 解决方案

### 方案 1：重构为手动 Function Calling（推荐）

**不使用 OpenAI Agents SDK，按照 DashScope 官方文档的方式实现。**

**优点：**
- ✅ 完全兼容 DashScope
- ✅ 使用 Qwen 模型（中文能力强）
- ✅ 成本可控
- ✅ 国内访问快
- ✅ 代码可控性���

**缺点：**
- ⚠️ 需要重构现有代码
- ⚠️ 需要手动实现工具调用循环
- ⚠️ 代码复杂度增加

**实现要点：**
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 手动实现工具调用循环
while assistant_output.tool_calls is not None:
    # 1. 解析工具调用
    # 2. 执行工具
    # 3. 添加结果到 messages
    # 4. 再次调用模型
    pass
```

### 方案 2：使用 OpenAI 官方 API

**继续使用 OpenAI Agents SDK，但切换到 OpenAI 官方 API。**

**优点：**
- ✅ 无需重构代码
- ✅ 完全兼容 Agents SDK
- ✅ 功能最完整

**缺点：**
- ❌ 需要 OpenAI API Key
- ❌ 国内访问需要代理
- ❌ 成本较高
- ❌ 中文能力不如 Qwen

**配置：**
```bash
OPENAI_API_KEY=sk-your-openai-key
# 不设置 OPENAI_API_BASE，使用默认
AGENT_MODEL=gpt-4o
```

### 方案 3：使用 vLLM 本地部署

**使用 vLLM 部署 Qwen 模型，验证是否支持 Agents API。**

**优点：**
- ✅ 本地部署，数据隐私
- ✅ 响应快
- ✅ 长期成本低

**缺点：**
- ❌ 需要 GPU 硬件
- ❌ 需要验证 vLLM 是否支持 Agents API
- ❌ 部署和维护成本

**需要验证：**
vLLM 是否实现了 `/v1/responses` 等 Agents API 端点。

## 推荐方案

### 基于你的需求

如果你希望：
- 使用 DashScope Qwen 模型（中文能力强）
- 成本可控
- 国内访问快

**推荐：方案 1 - 重构为手动 Function Calling**

### 实施步骤

1. **保留现有的工具定义**
   - 工具函数不需要改动
   - 工具描述（tools 数组）不需要改动

2. **重构 AgentService**
   - 移除对 OpenAI Agents SDK 的依赖
   - 使用标准的 `openai.OpenAI` 客户端
   - 实现手动的工具调用循环

3. **参考 DashScope 官方示例**
   - 按照 `/data/luna/luna-agent/docs/FUNCTION_CALL.md` 的示例实现
   - 使用 `while` 循环处理工具调用

## 总结

### 核心结论

**DashScope 完全支持 Function Calling，但不支持 OpenAI Agents SDK。**

这是因为：
- DashScope 实现的是标准的 Chat Completions API
- OpenAI Agents SDK 需要专用的 Agents API 端点
- 这是两套不同的 API 架构

### 术语澄清

- **"OpenAI 兼容"** ≠ **"OpenAI Agents SDK 兼容"**
- **"支持 Function Calling"** ≠ **"支持 Agents SDK"**

很多 LLM 服务商声称"OpenAI 兼容"，通常指的是兼容 Chat Completions API，而不是完整的 Agents API。

### 下一步

需要决定采用哪个方案：
1. **方案 1**：重构为手动 Function Calling（推荐，兼容 DashScope）
2. **方案 2**：切换到 OpenAI 官方 API（无需重构，但成本高）
3. **方案 3**：使用 vLLM 本地部署（需要验证兼容性）

---

**文档创建时间**：2026-01-23
**基于**：DashScope 官方 Function Calling 文档分析
