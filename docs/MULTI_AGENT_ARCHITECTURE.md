# 多 Agent 后端架构设计

## 设计目标

支持多种 Agent 实现，通过配置选择使用哪个后端：

1. **OpenAI Agents SDK** - 用于 OpenAI 官方 API
2. **Qwen-Agent** - 用于 DashScope / Qwen 模型
3. **手动 Function Calling** - 用于任何支持标准 Chat Completions API 的服务

## 架构设计

### 1. Agent 抽象层

定义统一的 Agent 接口，隐藏底层实现差异：

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """Agent 抽象基类"""

    @abstractmethod
    async def run(self, user_input: str, **kwargs) -> str:
        """
        运行 Agent

        Args:
            user_input: 用户输入
            **kwargs: 额外参数

        Returns:
            Agent 响应
        """
        pass

    @abstractmethod
    def add_tool(self, tool: Any) -> None:
        """添加工具"""
        pass
```

### 2. 具体实现类

#### 2.1 OpenAI Agents SDK 实现

```python
from agents import Agent as OpenAIAgent, Runner
from work_agent.adapters.llm.base_agent import BaseAgent

class OpenAIAgentAdapter(BaseAgent):
    """OpenAI Agents SDK 适配器"""

    def __init__(self, model: str, instructions: str):
        self.agent = OpenAIAgent(
            name="work-agent",
            model=model,
            instructions=instructions,
            tools=[],
        )
        self.runner = Runner()

    async def run(self, user_input: str, **kwargs) -> str:
        response = await self.runner.run(self.agent, user_input)
        return self._extract_response(response)

    def add_tool(self, tool: Any) -> None:
        self.agent.tools.append(tool)

    def _extract_response(self, response: Any) -> str:
        # 提取响应内容的逻辑
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)
```

#### 2.2 Qwen-Agent 实现

```python
from qwen_agent.agents import Assistant
from work_agent.adapters.llm.base_agent import BaseAgent

class QwenAgentAdapter(BaseAgent):
    """Qwen-Agent 适配器"""

    def __init__(self, model: str, instructions: str):
        self.agent = Assistant(
            llm={'model': model},
            system_message=instructions,
            function_list=[],
        )

    async def run(self, user_input: str, **kwargs) -> str:
        messages = [{'role': 'user', 'content': user_input}]
        responses = []
        for response in self.agent.run(messages):
            responses.append(response)
        # 提取最后的响应
        return responses[-1]['content'] if responses else ""

    def add_tool(self, tool: Any) -> None:
        self.agent.function_list.append(tool)
```

### 3. 配置管理

在 `config.py` 中添加 Agent 后端选择配置：

```python
from typing import Literal

class Config(BaseSettings):
    # ... 现有配置 ...

    # Agent 后端配置
    agent_backend: Literal["openai", "qwen", "manual"] = Field(
        default="openai",
        description="Agent 后端类型：openai（OpenAI Agents SDK）、qwen（Qwen-Agent）、manual（手动实现）"
    )
```

### 4. Agent 工厂

使用工厂模式根据配置创建对应的 Agent 实例：

```python
from work_agent.config import Config
from work_agent.adapters.llm.base_agent import BaseAgent
from work_agent.adapters.llm.openai_agent_adapter import OpenAIAgentAdapter
from work_agent.adapters.llm.qwen_agent_adapter import QwenAgentAdapter

def build_agent(config: Config, tools: list) -> BaseAgent:
    """
    根据配置构建 Agent 实例

    Args:
        config: 配置对象
        tools: 工具列表

    Returns:
        BaseAgent: Agent 实例
    """
    logger.info(f"Building agent with backend: {config.agent_backend}")

    if config.agent_backend == "openai":
        agent = OpenAIAgentAdapter(
            model=config.agent_model,
            instructions=DEFAULT_INSTRUCTIONS,
        )
    elif config.agent_backend == "qwen":
        agent = QwenAgentAdapter(
            model=config.agent_model,
            instructions=DEFAULT_INSTRUCTIONS,
        )
    else:
        raise ValueError(f"Unsupported agent backend: {config.agent_backend}")

    # 添加工具
    for tool in tools:
        agent.add_tool(tool)

    logger.info(f"Agent built successfully with {len(tools)} tools")
    return agent
```

### 5. 使用示例

#### 5.1 使用 OpenAI Agents SDK

```bash
# .env 配置
AGENT_BACKEND=openai
OPENAI_API_KEY=sk-your-openai-key
AGENT_MODEL=gpt-4o
```

#### 5.2 使用 Qwen-Agent + DashScope

```bash
# .env 配置
AGENT_BACKEND=qwen
DASHSCOPE_API_KEY=sk-your-dashscope-key
AGENT_MODEL=qwen-plus
```

## 方案优势

### 统一接口

- 应用层代码不需要关心底层使用哪个 Agent 实现
- 通过配置即可切换不同的后端
- 便于测试和维护

### 灵活性

- 可以根据场景选择最合适的 Agent 后端
- OpenAI API：功能最完整，适合生产环境
- Qwen-Agent：中文能力强，成本可控，国内访问快
- 手动实现：最大灵活性，适合特殊需求

### 可扩展性

- 未来可以轻松添加新的 Agent 后端
- 例如：Claude、Gemini、本地 vLLM 等

## 实施步骤

### 第一阶段：基础架构

1. 创建 `BaseAgent` 抽象类
2. 保留现有的 `OpenAIAgentAdapter`
3. 添加配置项 `agent_backend`
4. 修改 `build_agent` 工厂函数

### 第二阶段：Qwen-Agent 集成

1. 安装 Qwen-Agent：`pip install qwen-agent`
2. 实现 `QwenAgentAdapter` 类
3. 适配工具格式（OpenAI 格式 → Qwen-Agent 格式）
4. 测试 DashScope 集成

### 第三阶段：测试和优化

1. 编写单元测试
2. 测试不同后端的切换
3. 性能对比和优化
4. 更新文档

## 工具格式适配

不同 Agent 框架的工具格式可能不同，需要适配：

### OpenAI 格式
```python
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气",
        "parameters": {...}
    }
}
```

### Qwen-Agent 格式
需要根据 Qwen-Agent 的实际要求进行转换。

---

**文档创建时间**：2026-01-23
**设计目标**：支持多种 Agent 后端，通过配置灵活切换

