# 阿里云 DashScope (Qwen) 集成指南

## 验证结果

✅ **完全支持 OpenAI Agents SDK！**

### 测试结果

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 基础对话 | ✅ 支持 | 正常返回对话响应 |
| Function Calling | ✅ 支持 | OpenAI 标准格式 |
| 流式 Function Calling | ✅ 支持 | 支持流式工具调用 |
| Agent 兼容性 | ✅ 完全兼容 | 可直接用于 OpenAI Agents SDK |

### 工具调用示例

当询问"北京现在的天气怎么样？"时，模型正确返回了工具调用：

```json
{
  "tool_calls": [
    {
      "index": 0,
      "id": "call_9b52146a8814460b9ca5c0",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"北京\"}"
      }
    }
  ]
}
```

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件：

```bash
# 阿里云 DashScope (Qwen)
OPENAI_API_KEY=sk-b46122eafe3c4193affa84f75cac88e2
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
AGENT_MODEL=qwen-plus

# Weather API (如果要测试 weather tool)
WEATHER_API_KEY=your_weather_api_key
```

### 2. 测试 Agent

```bash
# 方法 1: 使用 CLI
python -m work_agent run "查询北京的天气"

# 方法 2: 使用测试脚本
.venv/bin/python scripts/test_vllm_agent.py \
    --base-url https://dashscope.aliyuncs.com/compatible-mode/v1 \
    --model qwen-plus \
    --api-key sk-b46122eafe3c4193affa84f75cac88e2 \
    --query "查询上海的天气"

# 方法 3: 交互模式
python -m work_agent repl
```

### 3. 验证工具列表

```bash
python -m work_agent list-tools
```

预期输出：
```
=== Available Tools ===

  • shell_echo
    安全的文本回显（仅用于演示，禁止执行命令）

  • get_current_time
    获取当前时间

  • get_city_weather
    获取指定城市的天气信息
```

## 可用模型

阿里云 DashScope 提供多个 Qwen 模型：

| 模型名称 | 说明 | Function Calling | 适用场景 |
|---------|------|-----------------|----------|
| `qwen-plus` | Qwen 大模型（推荐） | ✅ 支持 | 通用场景，性能强 |
| `qwen-turbo` | Qwen 快速模型 | ✅ 支持 | 快速响应 |
| `qwen-max` | Qwen 最强模型 | ✅ 支持 | 复杂任务 |
| `qwen-long` | 长文本模型 | ✅ 支持 | 长文档处理 |

### 切换模型

```bash
# 在 .env 中修改
AGENT_MODEL=qwen-max  # 使用最强模型
AGENT_MODEL=qwen-turbo  # 使用快速模型
```

## 完整配置示例

### .env 文件

```bash
# 阿里云 DashScope
OPENAI_API_KEY=sk-b46122eafe3c4193affa84f75cac88e2
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
AGENT_MODEL=qwen-plus

# Weather API
WEATHER_API_KEY=6d27c25dd21584b70ea2ba700d64af7b

# 日志级别
LOG_LEVEL=INFO

# Session 后端
SESSION_BACKEND=memory
```

### 测试脚本

```python
#!/usr/bin/env python3
"""测试 DashScope Qwen Agent"""

import os
from work_agent.config import load_config
from work_agent.container import build_container, set_global_container

# 配置环境变量
os.environ["OPENAI_API_KEY"] = "sk-b46122eafe3c4193affa84f75cac88e2"
os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
os.environ["AGENT_MODEL"] = "qwen-plus"
os.environ["WEATHER_API_KEY"] = "your_weather_key"

# 加载配置并构建容器
config = load_config()
container = build_container(config)
set_global_container(container)

# 运行查询
result = container.agent_service.run_once("查���北京的天气")
print(result)
```

## 性能对比

| 提供商 | 模型 | 延迟 | Function Calling | 中文能力 | 成本 |
|--------|------|------|-----------------|----------|------|
| 阿里云 DashScope | qwen-plus | ~500ms | ✅ 优秀 | ✅✅✅ 非常强 | 💰💰 适中 |
| OpenAI | gpt-4o | ~200ms | ✅ 优秀 | ✅✅ 良好 | 💰💰💰 较高 |
| vLLM (本地) | Qwen2.5-7B | ~50ms | ✅ 良好 | ✅✅✅ 非常强 | 💰 硬件成本 |

## 优势

### 1. 中文能力强
- Qwen 是专门针对中文优化的模型
- 中文理解和生成能力优秀
- 适合中文 Agent 场景

### 2. Function Calling 支持完善
- 完全兼容 OpenAI 标准
- 支持流式和非流式调用
- 工具调用准确率高

### 3. 成本可控
- 按量计费，成本透明
- 比 OpenAI GPT-4 更便宜
- 提供免费额度

### 4. 国内访问快
- 服务器在国内
- 无需代理
- 延迟低

## 注意事项

### 1. API Key 安全

⚠️ **不要在代码中硬编码 API key！**

```bash
# ✅ 正确 - 使用环境变量
export OPENAI_API_KEY=sk-your-key-here

# ❌ 错误 - 硬编码
api_key = "sk-b46122eafe3c4193affa84f75cac88e2"
```

### 2. 计费说明

- 按 token 数量计费
- 不同模型价格不同
- 建议设置月度预算限制

### 3. 速率限制

- 免费版有 QPS 限制
- 付费版可申请提高限制
- 建议实现重试机制

## 故障排查

### 问题 1: 401 Unauthorized

**原因**: API key 无效或过期

**解决**:
```bash
# 检查 API key 是否正确
echo $OPENAI_API_KEY

# 重新获取 API key
# 访问: https://dashscope.console.aliyun.com/apiKey
```

### 问题 2: 模型不支持

**错误**: `Model 'xxx' is not supported`

**解决**: 使用支持的模型名称
```bash
# 支持的模型
AGENT_MODEL=qwen-plus   # 推荐
AGENT_MODEL=qwen-turbo
AGENT_MODEL=qwen-max
```

### 问题 3: 工具调用失败

**症状**: Agent 不调用工具

**检查**:
1. 确认使用的是 qwen-plus/max/turbo 等支持 function calling 的模型
2. 检查 tool 定义是否正确
3. 查看日志了解具体错误

## 与其他方案对比

### DashScope vs OpenAI

| 特性 | DashScope (Qwen) | OpenAI (GPT-4o) |
|------|------------------|-----------------|
| 中文能力 | ✅✅✅ 非常强 | ✅✅ 良好 |
| Function Calling | ✅ 支持 | ✅ 支持 |
| 访问速度（国内） | ✅ 快 | ⚠️ 需代理 |
| 成本 | 💰💰 适中 | 💰💰💰 较高 |
| 生态 | 🔄 发展中 | ✅✅✅ 成熟 |

### DashScope vs vLLM 本地

| 特性 | DashScope | vLLM 本地 |
|------|-----------|----------|
| 部署难度 | ✅ 简单（无需部署） | ⚠️ 需要 GPU |
| 成本 | 💰💰 按量付费 | 💰 硬件成本 |
| 性能 | ✅ 稳定 | ✅✅ 更快 |
| 数据隐私 | ⚠️ 上云 | ✅ 本地 |
| 维护 | ✅ 无需维护 | ⚠️ 需要维护 |

## 推荐使用场景

### ✅ 适合使用 DashScope

1. **中文 Agent 应用**
   - 中文对话、问答
   - 中文工具调用
   - 中文内容生成

2. **快速开发原型**
   - 无需部署模型
   - 快速验证想法
   - 降低开发门槛

3. **中小规模应用**
   - 日调用量 < 100万
   - 成本可控
   - 国内用户为主

### ⚠️ 考虑其他方案

1. **超大规模应用**
   - 日调用量 > 1000万
   - 考虑 vLLM 本地部署

2. **极高隐私要求**
   - 敏感数据处理
   - 必须本地部署
   - 使用 vLLM

3. **多语言混合**
   - 英文为主
   - 考虑 OpenAI GPT-4

## 示例代码

### 完整示例：天气查询 Agent

```python
#!/usr/bin/env python3
"""DashScope Qwen 天气查询 Agent"""

import os
from work_agent.config import load_config
from work_agent.container import build_container, set_global_container
from work_agent.logging import configure_logging

def main():
    # 配置
    os.environ["OPENAI_API_KEY"] = "sk-b46122eafe3c4193affa84f75cac88e2"
    os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    os.environ["AGENT_MODEL"] = "qwen-plus"
    os.environ["WEATHER_API_KEY"] = "your_weather_key"

    configure_logging("INFO")

    # 构建 Agent
    config = load_config()
    container = build_container(config)
    set_global_container(container)

    # 测试查询
    queries = [
        "查询北京的天气",
        "上海今天天气怎么样？",
        "现在几点了？",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")

        result = container.agent_service.run_once(query)
        print(result)

if __name__ == "__main__":
    main()
```

## 获取 API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 进入 [API Key 管理](https://dashscope.console.aliyun.com/apiKey)
4. 创建新的 API Key
5. 复制 API Key 到 `.env` 文件

## 参考资源

- [DashScope 官方文档](https://help.aliyun.com/zh/dashscope/)
- [Qwen 模型介绍](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction)
- [Function Calling 文档](https://help.aliyun.com/zh/dashscope/developer-reference/use-qwen-by-calling-api)
- [OpenAI 兼容 API](https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope/)

## 总结

✅ **阿里云 DashScope (Qwen) 完全支持 OpenAI Agents SDK**

**推荐使用**:
- 中文 Agent 应用首选
- 性价比高
- 无需复杂部署
- Function calling 支持完善

**配置简单**:
```bash
OPENAI_API_KEY=sk-your-dashscope-key
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
AGENT_MODEL=qwen-plus
```

立即开始使用 DashScope Qwen 构建你的 Agent 应用！
