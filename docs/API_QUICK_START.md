# API 转 Tool 快速入门

本指南帮助您在 5 分钟内将一个 API 脚本转换为 Agent Tool。

## 方式一：使用脚手架生成器（推荐）

### 1. 生成代码模板

```bash
# 在项目根目录执行
python scripts/scaffold_generator.py weather

# 或指定项目路径
python scripts/scaffold_generator.py github /data/luna/luna-agent
```

这将生成：
- `src/work_agent/adapters/external/apis/weather_api.py` - API 客户端
- `src/work_agent/adapters/external/services/weather_service.py` - 业务服务
- `src/work_agent/adapters/tools/weather_tool.py` - Agent 工具

### 2. 配置环境变量

编辑 `.env`:

```bash
# Weather API
WEATHER_API_KEY=your_api_key_here
WEATHER_API_BASE_URL=https://api.openweathermap.org/data/2.5
WEATHER_API_TIMEOUT=10.0
```

编辑 `config.py`，添加配置类:

```python
class Config(BaseSettings):
    # ... 现有配置 ...

    # Weather API
    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_api_timeout: float = 10.0
```

### 3. 实现 API 逻辑

打开生成的 `weather_api.py`，实现具体的 API 调用：

```python
async def get_weather(self, city: str) -> dict[str, Any]:
    """获取城市天气"""
    response = await self.client.get(
        "/weather",
        params={"q": city, "units": "metric"},
        raise_for_status=True,
    )
    return response.body
```

### 4. 实现业务逻辑

打开生成的 `weather_service.py`，格式化输出：

```python
async def get_weather_summary(self, city: str) -> str:
    """获取天气摘要"""
    try:
        data = await self.api.get_weather(city)

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]

        return f"🌤️ {city} 天气:\n温度: {temp}°C\n状况: {desc}"

    except ApiClientError as e:
        raise WeatherServiceError(f"获取天气失败: {e}") from e
```

### 5. 完善 Tool 描述

打开生成的 `weather_tool.py`，修改工具描述：

```python
@function_tool
async def get_city_weather(city: str) -> str:
    """
    获取指定城市的天气信息

    查询城市的实时天气，包括温度、湿度、天气状况等。

    Args:
        city: 城市名称（中文或英文，如 "北京", "Beijing", "New York"）

    Returns:
        格式化的天气信息字符串

    Examples:
        - get_city_weather("北京")
        - get_city_weather("Shanghai")
        - get_city_weather("Tokyo")
    """
    service = _get_service()
    return await service.get_weather_summary(city)
```

### 6. 注册到容器

编辑 `container.py`:

```python
from work_agent.adapters.external.apis.weather_api import WeatherApiClient
from work_agent.adapters.external.services.weather_service import WeatherService

@dataclass
class Container:
    # ... 现有字段 ...
    weather_service: WeatherService | None = None

def build_container(config: Config) -> Container:
    # ... 现有代码 ...

    # 构建 Weather 服务
    weather_service = None
    if config.weather_api_key:
        weather_api = WeatherApiClient(
            base_url=config.weather_api_base_url,
            api_key=config.weather_api_key,
            timeout=config.weather_api_timeout,
        )
        weather_service = WeatherService(weather_api)

    return Container(
        # ... 现有参数 ...
        weather_service=weather_service,
    )

# 添加全局获取函数
def get_weather_service() -> WeatherService:
    if _global_container is None or _global_container.weather_service is None:
        raise RuntimeError("Weather service not initialized")
    return _global_container.weather_service
```

### 7. 测试

```bash
# 验证 tool 被发现
python -m work_agent list-tools

# 测试功能
python -m work_agent run "查询北京的天气"
```

## 方式二：手动创建（了解底层）

如果您想完全理解整个流程，请参考：
- [完整指南](./docs/API_TO_TOOL_GUIDE.md) - 详细的步骤说明
- [示例代码](./src/work_agent/adapters/tools/time_now.py) - 简单工具示例

## 核心概念

### 三层架构

```
┌─────────────────────┐
│  Tool Layer         │  ← Agent 调用入口（薄封装）
│  weather_tool.py    │
└──────────┬──────────┘
           │ 调用
┌──────────▼──────────┐
│  Service Layer      │  ← 业务逻辑 + 数据格式化
│  weather_service.py │
└──────────┬──────────┘
           │ 使用
┌──────────▼──────────┐
│  API Layer          │  ← 纯 API 调用（可复用）
│  weather_api.py     │
└─────────────────────┘
```

### 依赖注入流程

```
Config → Container → API Client → Service → Tool
  ↑                                           ↓
 .env                                      Agent 调用
```

### 文件位置

- **API 客户端**: `adapters/external/apis/xxx_api.py`
- **业务服务**: `adapters/external/services/xxx_service.py`
- **数据模型**: `adapters/external/models/xxx.py` (可选)
- **Tool**: `adapters/tools/xxx_tool.py`
- **测试**: `tests/unit/test_xxx_api.py`

## 常见 API 类型

### REST API with JSON

```python
# API 客户端
async def create_user(self, name: str, email: str) -> dict:
    response = await self.client.post(
        "/users",
        json={"name": name, "email": email},
        raise_for_status=True,
    )
    return response.body
```

### REST API with Query Params

```python
async def search(self, keyword: str, limit: int = 10) -> list:
    response = await self.client.get(
        "/search",
        params={"q": keyword, "limit": limit},
        raise_for_status=True,
    )
    return response.body["results"]
```

### API with Header Authentication

```python
def __init__(self, base_url: str, api_key: str, **kwargs):
    super().__init__(base_url, **kwargs)
    self.set_api_key("X-API-Key", api_key)
```

### API with Bearer Token

```python
def __init__(self, base_url: str, token: str, **kwargs):
    super().__init__(base_url, **kwargs)
    self.set_auth_token(token)
```

### API with Form Data

```python
async def upload(self, file_path: str) -> dict:
    with open(file_path, "rb") as f:
        response = await self.client.post(
            "/upload",
            files={"file": ("filename.txt", f, "text/plain")},
            raise_for_status=True,
        )
    return response.body
```

## 调试技巧

### 1. 查看日志

```bash
LOG_LEVEL=DEBUG python -m work_agent run "your query"
```

### 2. 测试 API 客户端

```python
# tests/unit/test_weather_api.py
import pytest
from work_agent.adapters.external.apis.weather_api import WeatherApiClient

@pytest.mark.asyncio
async def test_weather_api():
    client = WeatherApiClient("https://api.example.com", "fake_key")
    # Mock 和测试
```

### 3. Tool 未被发现

检查：
- 文件名不以 `_` 开头
- 文件在 `adapters/tools/` 目录
- 有 `get_tool()` 函数
- `get_tool()` 返回了 function_tool 装饰的函数

### 4. 容器注入失败

确认：
- 在 `container.py` 的 `Container` 类中添加了字段
- 在 `build_container()` 中实例化了服务
- 在 tool 中调用了正确的 `get_xxx_service()` 函数
- 在 `app.py` 中调用了 `set_global_container(container)`

## 最佳实践

1. **API 客户端保持纯粹** - 只负责 HTTP 调用，不做业务逻辑
2. **Service 层处理业务** - 数据转换、格式化、异常转换
3. **Tool 层薄封装** - 只做参数校验和调用 Service
4. **使用 Pydantic 验证** - API 响应用 Pydantic Model 验证
5. **完善的 Docstring** - LLM 依赖 docstring 理解工具功能
6. **错误处理** - API 异常转为领域异常，提供友好错误消息
7. **日志记录** - 关键操作记录日志，便于调试
8. **单元测试** - Mock API 响应，测试业务逻辑

## 检查清单

在完成后确认：

- [ ] 生成了三个文件（api, service, tool）
- [ ] 配置添加到 `config.py` 和 `.env`
- [ ] API 客户端实现了具体逻辑
- [ ] Service 层有格式化输出
- [ ] Tool 有详细的 docstring
- [ ] 容器中注册了服务
- [ ] `python -m work_agent list-tools` 能看到新工具
- [ ] 测试通过：`python -m work_agent run "测试查询"`
- [ ] 敏感信息在 `.env` 中，不在代码中

## 下一步

- 阅读 [完整 API 转 Tool 指南](./docs/API_TO_TOOL_GUIDE.md)
- 参考 [CLAUDE.md](./CLAUDE.md) 了解项目架构
- 查看 [RULE.md](./RULE.md) 了解工程规范
