# Work Agent - 日常工作助理 Agent

基于 OpenAI Agents SDK 的工程化 Agent 项目脚手架，遵循严格的 Python 工程化规范。

## 特性

- ✅ 严格分层架构（domain/services/adapters/api）
- ✅ 依赖注入（DI）与资源生命周期管理
- ✅ 插件化 tools 体系（自动发现与注册）
- ✅ 模型可扩展（配置化 provider/model）
- ✅ 可观测性（结构化日志、trace_id、tracing）
- ✅ CLI 与 API 双模式（API 可选依赖）
- ✅ 测试分层（unit/integration）

## 快速开始

### 0. 环境要求

- Python 3.10+ （推荐 Python 3.11+）
- uv 或 pip 包管理工具

### 1. 安装依赖

本项目使用 `uv` 作为包管理工具。

```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 并填入你的 API Key
# OPENAI_API_KEY=sk-your-key-here
```

**⚠️ 安全提示：**
- `.env` 文件已在 `.gitignore` 中，切勿提交真实 API Key
- 生产环境通过环境变量或密钥管理服务注入

### 3. 运行 CLI

#### 列出所有可用 tools

```bash
python -m work_agent list-tools
```

#### 单次运行

```bash
python -m work_agent run "现在几点了？"
```

#### 交互模式（REPL）

```bash
python -m work_agent repl
```

退出：输入 `quit` 或 `exit`

### 4. 运行测试

```bash
# 运行单元测试（不依赖外部服务）
pytest tests/unit -v

# 运行所有测试（包括集成测试，需要真实 API Key）
RUN_INTEGRATION=1 pytest -v

# 查看覆盖率
pytest --cov=work_agent --cov-report=html
```

### 5. 代码质量检查

```bash
# 格式化代码
ruff format .
black .

# Lint 检查
ruff check .

# 类型检查
mypy src/work_agent

# 一键运行所有检查
ruff check . && black --check . && mypy src/work_agent && pytest tests/unit
```

### 6. 安装 pre-commit hooks（推荐）

```bash
uv pip install pre-commit
pre-commit install
```

## API 模式（可选）

### 安装 API 依赖

```bash
uv pip install -e ".[api]"
```

### 启动 API 服务

```bash
python -m work_agent serve --port 8000
```

### 可用端点

- `GET /health` - 健康检查
- `GET /tools` - 列出所有 tools
- `POST /run` - 执行 Agent 任务
  ```json
  {
    "user_input": "现在几点了？",
    "trace_id": "optional-trace-id"
  }
  ```

### 查看 API 文档

访问 http://localhost:8000/docs

## 如何新增一个 Tool

### 步骤 1：创建 tool 文件

在 `src/work_agent/adapters/tools/` 下创建新文件，例如 `weather.py`：

```python
"""天气查询工具"""
from typing import Any
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息

    Args:
        city: 城市名称（如：北京、上海）

    Returns:
        天气信息字符串
    """
    # 这里只是示例，实际应调用天气 API
    return f"{city}的天气：晴天，温度 25℃"

# 必须暴露以便自动发现
def get_tool() -> Any:
    return get_weather
```

### 步骤 2：自动发现

无需手动注册！重启 CLI 即可：

```bash
python -m work_agent list-tools
# 你会看到新增的 get_weather
```

### Tool 开发规范

1. **必须有类型标注**：所有参数必须有类型提示
2. **必须有文档字符串**：描述功能、参数、返回值
3. **暴露 `get_tool()` 函数**：返回 tool 实例
4. **遵循命名规���**：文件名 snake_case，函数名动词开头
5. **无副作用**：导入时不得执行 I/O 或读取环境变量
6. **安全优先**：禁止执行危险操作（如任意命令执行）

## 可观测性

### 结构化日志

所有日志包含以下字段：
- `timestamp`: ISO 8601 时间戳
- `level`: 日志级别
- `module`: 模块名称
- `trace_id`: 请求追踪 ID
- `message`: 日志消息

### 启用 Tracing

编辑 `.env`：

```bash
ENABLE_TRACING=true
```

当前 tracing 为本地模式，所有 trace 信息会输出到日志。

### 查看 trace_id

每次运行都会生成唯一 trace_id：

```bash
python -m work_agent run "hello"
# 日志中会显示：trace_id=req_abc123...
```

在 REPL 模式中，每轮对话使用同一个 trace_id。

### 外部 Tracing 集成（预留）

`adapters/observability/tracing.py` 已预留接口，可对接：
- OpenTelemetry
- Langfuse
- LangSmith
- Custom tracing backend

## 模型配置

### 使用 OpenAI API（默认）

编辑 `.env`：

```bash
OPENAI_API_KEY=sk-your-key-here
AGENT_MODEL=gpt-4o  # 默认
# 或切换到其他模型
AGENT_MODEL=gpt-4o-mini
```

### 使用 vLLM 本地部署（推荐）

vLLM 支持本地运行开源模型，无需调用 OpenAI API。

**快速开始:**

```bash
# 1. 启动 vLLM 服务
./scripts/start_vllm.sh

# 2. 配置环境变量
export OPENAI_API_KEY=EMPTY
export OPENAI_API_BASE=http://localhost:8000/v1
export AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct

# 3. 测试 Agent
.venv/bin/python scripts/test_vllm_agent.py
```

**优势:**
- ✅ 数据不出本地，保护隐私
- ✅ 无需支付 API 费用
- ✅ GPU 加速，高性能推理
- ✅ 支持 Qwen、Llama、Mistral 等开源模型

**详细文档:**
- [vLLM 快速开始](docs/VLLM_QUICK_START.md) - 5 分钟上手
- [vLLM 完整指南](docs/VLLM_INTEGRATION.md) - 高级配置和生产部署

### 支持的 Provider

当前支持：
- ✅ OpenAI API（官方）
- ✅ vLLM（本地部署，OpenAI 兼容）
- 🔄 Azure OpenAI（修改 `OPENAI_API_BASE`）
- 🔄 其他 OpenAI 兼容服务

## 视图层扩展路线

当前 API 为骨架，后续可扩展：

1. **在线编辑 Instructions**
   - `PUT /config/instructions` 端点已预留
   - 支持动态修改 Agent 系统提示词

2. **运行记录查看**
   - 存储历史会话（SQLite/PostgreSQL）
   - 展示工具调用轨迹与中间结果

3. **Web UI 集成**
   - React/Vue 前端展示对话界面
   - Gradio/Streamlit 快速原型
   - 工具列表可视化管理

4. **Prompt 模板管理**
   - 多模板切换（工作/生活/研究）
   - 模板版本控制

## 项目结构说明

```
src/work_agent/
├── domain/          # 纯领域模型（无外部依赖）
├── services/        # 用例编排（依赖注入）
├── adapters/        # 外部适配器
│   ├── llm/        # LLM 相关（Agent/Runner 工厂）
│   ├── tools/      # 工具插件（自动发现）
│   └── observability/  # 可观测性
├── api/            # API 视图层（DTO 解耦）
├── tasks/          # 任务入口（调用 services）
└── utils/          # 通用工具（最小化）
```

### 依赖方向规则

```
API/Tasks → Services → Domain
          ↘         ↗
            Adapters
```

- **domain**: 不依赖任何外部层
- **services**: 可依赖 domain，通过接口依赖 adapters
- **adapters**: 可依赖 domain，不得依赖 services
- **api/tasks**: 只能调用 services，不得直接调用 adapters

## 故障排查

### 问题：`OPENAI_API_KEY not found`

**解决方案**：
1. 确认 `.env` 文件存在且在项目根目录
2. 检查环境变量格式：`OPENAI_API_KEY=sk-...`（无引号）
3. 或直接导出：`export OPENAI_API_KEY=sk-...`

### 问题：Tool 未被发现

**解决方案**：
1. 确认文件在 `src/work_agent/adapters/tools/` 下
2. 文件名不以 `_` 开头（除 `_registry.py`）
3. 必须暴露 `get_tool()` 函数
4. 检查 `--list-tools` 输出的错误日志

### 问题：测试失败

**解决方案**：
1. 单元测试失败：检查 mock 配置
2. 集成测试失败：确认设置了 `RUN_INTEGRATION=1` 且 API Key 有效
3. 查看详细日志：`pytest -vv --log-cli-level=DEBUG`

## 开发指南

### 添加新 Service

```python
# src/work_agent/services/new_service.py
from work_agent.domain.models import SomeModel

class NewService:
    def __init__(self, dependency):
        self.dependency = dependency

    def execute(self, input_data: str) -> SomeModel:
        # ���例���排逻辑
        pass
```

在 `container.py` 中注册：

```python
def build_container(config):
    # ...
    new_service = NewService(dependency=some_adapter)
    return Container(..., new_service=new_service)
```

### 添加新 Adapter

```python
# src/work_agent/adapters/external/new_adapter.py
class NewAdapter:
    def __init__(self, config):
        self.config = config

    def fetch_data(self) -> dict:
        # 外部系统调用
        pass
```

### 运行特定测试

```bash
# 运行单个测试文件
pytest tests/unit/test_tool_registry.py -v

# 运行特定测试函数
pytest tests/unit/test_tool_registry.py::test_load_tools_success -v

# 运行匹配模式的测试
pytest -k "registry" -v
```

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！

在提交代码前，请确保：
1. 通过所有测试：`pytest`
2. 通过代码质量检查：`ruff check . && black --check .`
3. 通过类型检查：`mypy src/work_agent`
4. 遵循项目规范文档
