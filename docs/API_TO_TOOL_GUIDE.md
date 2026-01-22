# API 脚本转 Tool 接入指南

本文档说明如何将外部 API 脚本转换为 Agent Tool 的完整流程和基础工作。

## 一、整体架构设计

### 1.1 三层结构

```
API 定义层 (adapters/external/apis/)
    ↓ 使用 ApiClient
业务封装层 (adapters/external/services/)
    ↓ 注入到
Tool 暴露层 (adapters/tools/)
    ↓ 自动发现
Agent 调用
```

### 1.2 设计原则

- **API 定义层**：纯 API 调用逻辑，可复用，可单独测试
- **业务封装层**：业务逻辑处理，数据转换，错误处理
- **Tool 层**：薄封装，只负责参数校验和调用业务层

## 二、基础工作清单

### 2.1 必须完成的基础设施

#### ✅ 已完成

1. ✅ 通用 HTTP 客户端 (`utils/api_client.py`)
2. ✅ Tool 自动发现机制 (`adapters/tools/_registry.py`)
3. ✅ 配置管理系统 (`config.py`)
4. ✅ 日志系统 (`logging.py`)

#### 🔧 需要补充

1. **API 配置管理** - 集中管理 API endpoints、keys、超时等
2. **API 客户端工厂** - 为不同 API 创建配置好的 client 实例
3. **统一错误处理** - API 异常 → 领域异常的转换
4. **响应数据模型** - Pydantic models 用于数据验证
5. **缓存机制**（可选）- 减少重复 API 调用
6. **限流机制**（可选）- 避免触发 API rate limit

### 2.2 目录结构规划

```
src/work_agent/
├── adapters/
│   ├── external/
│   │   ├── apis/              # 【新增】API 客户端定义
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # 基础 API 客户端抽象
│   │   │   ├── github_api.py  # 示例：GitHub API
│   │   │   └── weather_api.py # 示例：天气 API
│   │   ├── services/          # 【新增】业务服务封装
│   │   │   ├── __init__.py
│   │   │   ├── github_service.py
│   │   │   └── weather_service.py
│   │   └── models/            # 【新增】响应数据模型
│   │       ├── __init__.py
│   │       ├── github.py
│   │       └── weather.py
│   └── tools/
│       ├── github_tool.py     # 【新增】GitHub tool
│       └── weather_tool.py    # 【新增】天气 tool
├── domain/
│   └── errors.py              # 【补充】API 相关异常
└── config.py                  # 【补充】API 配置
```

## 三、实现步骤（完整示例）

### 步骤 1：扩展配置系统

在 `config.py` 中添加 API 配置：

```python
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # ... 现有配置 ...

    # API 配置
    github_api_token: str = ""
    github_api_base_url: str = "https://api.github.com"
    github_api_timeout: float = 30.0

    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_api_timeout: float = 10.0

    # 通用 API 配置
    api_retry_count: int = 2
    api_retry_delay: float = 1.0
    enable_api_cache: bool = False
```

### 步骤 2：定义响应数据模型

创建 `adapters/external/models/github.py`：

```python
"""GitHub API 响应数据模型"""
from pydantic import BaseModel, Field

class GitHubRepo(BaseModel):
    """GitHub 仓库信息"""
    id: int
    name: str
    full_name: str
    description: str | None = None
    stargazers_count: int = Field(alias="stargazers_count")
    forks_count: int = Field(alias="forks_count")
    html_url: str

    class Config:
        populate_by_name = True

class GitHubUser(BaseModel):
    """GitHub 用户信息"""
    login: str
    id: int
    name: str | None = None
    bio: str | None = None
    public_repos: int = 0
    followers: int = 0
    html_url: str
```

### 步骤 3：创建 API 客户端

创建 `adapters/external/apis/github_api.py`：

```python
"""GitHub API 客户端"""
import logging
from typing import Any

from work_agent.utils.api_client import ApiClient, ApiResponse
from work_agent.adapters.external.models.github import GitHubRepo, GitHubUser

logger = logging.getLogger(__name__)

class GitHubApiClient:
    """GitHub API 客户端封装

    职责：
    - 封装 GitHub API 调用细节
    - 处理认证
    - 返回结构化数据
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        retry_count: int = 2,
    ) -> None:
        self.client = ApiClient(
            base_url=base_url,
            timeout=timeout,
            retry_count=retry_count,
        )
        if token:
            self.client.set_bearer_token(token)
        self.client.set_header("Accept", "application/vnd.github+json")

    async def get_user(self, username: str) -> GitHubUser:
        """获取用户信息

        Args:
            username: GitHub 用户名

        Returns:
            GitHubUser 对象

        Raises:
            ApiClientError: API 调用失败
        """
        logger.info(f"Fetching GitHub user: {username}")

        response = await self.client.get(
            f"/users/{username}",
            raise_for_status=True,
        )

        return GitHubUser(**response.body)

    async def get_repo(self, owner: str, repo: str) -> GitHubRepo:
        """获取仓库信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            GitHubRepo 对象
        """
        logger.info(f"Fetching GitHub repo: {owner}/{repo}")

        response = await self.client.get(
            f"/repos/{owner}/{repo}",
            raise_for_status=True,
        )

        return GitHubRepo(**response.body)

    async def search_repos(
        self,
        query: str,
        sort: str = "stars",
        limit: int = 10,
    ) -> list[GitHubRepo]:
        """搜索仓库

        Args:
            query: 搜索关键词
            sort: 排序方式 (stars, forks, updated)
            limit: 返回数量限制

        Returns:
            GitHubRepo 列表
        """
        logger.info(f"Searching GitHub repos: {query}")

        response = await self.client.get(
            "/search/repositories",
            params={
                "q": query,
                "sort": sort,
                "per_page": limit,
            },
            raise_for_status=True,
        )

        items = response.body.get("items", [])
        return [GitHubRepo(**item) for item in items[:limit]]
```

### 步骤 4：创建业务服务层

创建 `adapters/external/services/github_service.py`：

```python
"""GitHub 业务服务层"""
import logging
from typing import Any

from work_agent.adapters.external.apis.github_api import GitHubApiClient
from work_agent.adapters.external.models.github import GitHubRepo, GitHubUser
from work_agent.domain.errors import DomainError
from work_agent.utils.api_client import ApiClientError

logger = logging.getLogger(__name__)

class GitHubServiceError(DomainError):
    """GitHub 服务异常"""
    pass

class GitHubService:
    """GitHub 业���服务

    职责：
    - 业务逻辑编排
    - 数据转换和格式化
    - 异常转换（API 异常 → 领域异常）
    """

    def __init__(self, api_client: GitHubApiClient) -> None:
        self.api = api_client

    async def get_user_summary(self, username: str) -> str:
        """获取用户摘要信息（格式化为可读文本）

        Args:
            username: GitHub 用户名

        Returns:
            格式化的用户信息文本

        Raises:
            GitHubServiceError: 获取失败
        """
        try:
            user = await self.api.get_user(username)

            summary_parts = [
                f"👤 GitHub 用户: {user.login}",
                f"📝 简介: {user.bio or '无'}",
                f"📦 公开仓库: {user.public_repos}",
                f"👥 粉丝数: {user.followers}",
                f"🔗 主页: {user.html_url}",
            ]

            return "\n".join(summary_parts)

        except ApiClientError as e:
            logger.error(f"Failed to fetch user {username}: {e}")
            raise GitHubServiceError(f"无法获取用户信息: {e}") from e

    async def search_popular_repos(
        self,
        keyword: str,
        language: str | None = None,
        limit: int = 5,
    ) -> str:
        """搜索热门仓库（格式化输出）

        Args:
            keyword: 搜索关键词
            language: 编程语言过滤
            limit: 返回数量

        Returns:
            格式化的仓库列表
        """
        try:
            # 构建查询
            query = keyword
            if language:
                query += f" language:{language}"

            repos = await self.api.search_repos(query, limit=limit)

            if not repos:
                return f"未找到与 '{keyword}' 相关的仓库"

            # 格式化输出
            result_parts = [f"🔍 找到 {len(repos)} 个热门仓库:\n"]

            for i, repo in enumerate(repos, 1):
                result_parts.append(
                    f"{i}. {repo.full_name}\n"
                    f"   ⭐ {repo.stargazers_count:,} | "
                    f"🍴 {repo.forks_count:,}\n"
                    f"   📄 {repo.description or '无描述'}\n"
                    f"   🔗 {repo.html_url}\n"
                )

            return "\n".join(result_parts)

        except ApiClientError as e:
            logger.error(f"Failed to search repos: {e}")
            raise GitHubServiceError(f"搜索仓库失败: {e}") from e
```

### 步骤 5：创建 Tool 层

创建 `adapters/tools/github_tool.py`：

```python
"""GitHub Tool - Agent 可调用的工具"""
from typing import Any
from agents import function_tool

# 注意：这里需要从 container 获取已注入的 service
# 为了自动发现，我们使用延迟初始化模式

_service = None

def _get_service():
    """获取 GitHub 服务实例（从容器注入）"""
    global _service
    if _service is None:
        # 这里需要从容器获取，实际实现见步骤 6
        from work_agent.container import get_github_service
        _service = get_github_service()
    return _service

@function_tool
async def search_github_repos(
    keyword: str,
    language: str = "",
    limit: int = 5,
) -> str:
    """
    搜索 GitHub 热门仓库

    根据关键词搜索 GitHub 上的热门仓库，可按编程语言过滤。
    返回仓库名���、���标数、Fork 数、描述和链接。

    Args:
        keyword: 搜索关键词（如 "machine learning", "web framework"）
        language: 编程语言过滤（可选，如 "Python", "JavaScript"）
        limit: 返回仓库数量，默认 5 个，最多 10 个

    Returns:
        格式化的仓库列表字符串

    Examples:
        - search_github_repos("deep learning", "Python", 5)
        - search_github_repos("react components")
    """
    # 参数校验
    if limit < 1 or limit > 10:
        return "错误: limit 必须在 1-10 之间"

    service = _get_service()
    return await service.search_popular_repos(
        keyword=keyword,
        language=language or None,
        limit=limit,
    )

@function_tool
async def get_github_user_info(username: str) -> str:
    """
    获取 GitHub 用户信息

    查询指定 GitHub 用户的个人信息，包括简介、仓库数、粉丝数等。

    Args:
        username: GitHub 用户名

    Returns:
        格式化的用户信息字符串

    Examples:
        - get_github_user_info("torvalds")
        - get_github_user_info("gvanrossum")
    """
    service = _get_service()
    return await service.get_user_summary(username)

def get_tool() -> Any:
    """暴露多个工具（返回列表）"""
    return [search_github_repos, get_github_user_info]
```

### 步骤 6：容器注入配置

修改 `container.py`：

```python
from dataclasses import dataclass
from work_agent.config import Config
from work_agent.adapters.external.apis.github_api import GitHubApiClient
from work_agent.adapters.external.services.github_service import GitHubService

@dataclass
class Container:
    # ... 现有字段 ...
    github_service: GitHubService | None = None

def build_container(config: Config) -> Container:
    # ... 现有代码 ...

    # 构建 GitHub 服务
    github_service = None
    if config.github_api_token:
        github_api = GitHubApiClient(
            base_url=config.github_api_base_url,
            token=config.github_api_token,
            timeout=config.github_api_timeout,
            retry_count=config.api_retry_count,
        )
        github_service = GitHubService(github_api)

    return Container(
        # ... 现有参数 ...
        github_service=github_service,
    )

# 全局容器（用于 tool 延迟获取）
_global_container: Container | None = None

def set_global_container(container: Container) -> None:
    global _global_container
    _global_container = container

def get_github_service() -> GitHubService:
    if _global_container is None or _global_container.github_service is None:
        raise RuntimeError("GitHub service not initialized")
    return _global_container.github_service
```

### 步骤 7：环境变量配置

在 `.env` 中添加：

```bash
# GitHub API
GITHUB_API_TOKEN=ghp_your_token_here
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_API_TIMEOUT=30.0

# 通用 API 配置
API_RETRY_COUNT=2
API_RETRY_DELAY=1.0
ENABLE_API_CACHE=false
```

## 四、测试策略

### 4.1 单元测试（API 客户端）

```python
# tests/unit/test_github_api.py
import pytest
from unittest.mock import AsyncMock, patch
from work_agent.adapters.external.apis.github_api import GitHubApiClient

@pytest.mark.asyncio
async def test_get_user():
    client = GitHubApiClient("https://api.github.com", "fake_token")

    # Mock ApiClient
    with patch.object(client.client, 'get') as mock_get:
        mock_get.return_value = AsyncMock(
            body={
                "login": "testuser",
                "id": 123,
                "public_repos": 10,
                "followers": 100,
                "html_url": "https://github.com/testuser",
            }
        )

        user = await client.get_user("testuser")
        assert user.login == "testuser"
        assert user.public_repos == 10
```

### 4.2 集成测试（真实 API）

```python
# tests/integration/test_github_integration.py
import pytest
import os

@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_real_api():
    token = os.getenv("GITHUB_API_TOKEN")
    if not token:
        pytest.skip("GITHUB_API_TOKEN not set")

    from work_agent.adapters.external.apis.github_api import GitHubApiClient

    client = GitHubApiClient("https://api.github.com", token)
    user = await client.get_user("torvalds")

    assert user.login == "torvalds"
    assert user.public_repos > 0
```

## 五、最佳实践

### 5.1 错误处理

```python
# 在 Service 层统一处理 API 异常
try:
    result = await self.api.some_method()
except ApiClientError as e:
    logger.error(f"API call failed: {e}", exc_info=True)
    # 转换为领域异常
    raise DomainServiceError(f"操作失败: {e}") from e
```

### 5.2 日志记录

```python
# 在关键节点记录日志
logger.info(f"Calling API: {endpoint}", extra={
    "trace_id": get_trace_id(),
    "params": params,
})
```

### 5.3 缓存支持

```python
from functools import lru_cache
import hashlib

class CachedGitHubService:
    @lru_cache(maxsize=100)
    async def get_user_cached(self, username: str) -> str:
        return await self.get_user_summary(username)
```

### 5.4 限流保护

```python
import asyncio
from collections import deque
from time import time

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.timestamps = deque()

    async def acquire(self):
        now = time()
        # 移除过期时间戳
        while self.timestamps and self.timestamps[0] < now - self.period:
            self.timestamps.popleft()

        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            await asyncio.sleep(sleep_time)

        self.timestamps.append(time())
```

## 六、常见问题

### Q1: Tool 中如何获取配置？
A: 通过容器注入，在 tool 中通过全局容器获取已配置的 service 实例。

### Q2: 同步 API 如何处理？
A: 使用 `asyncio.to_thread()` 或 `loop.run_in_executor()` 包装同步调用。

### Q3: 如何处理 API 认证？
A: 在 API 客户端初始化时配置，通过 `set_bearer_token()` 或 `set_basic_auth()` 设置。

### Q4: 如何测试不影响真实 API？
A: 使用 `unittest.mock` 或 `pytest-mock` mock API 客户端的返回值。

## 七、检查清单

在完成 API 转 Tool 后，确认以下事项：

- [ ] API 配置已添加到 `config.py` 和 `.env.example`
- [ ] API 客户端实现了错误处理和超时
- [ ] 响应数据有 Pydantic 模型验证
- [ ] Service 层有完整的日志记录
- [ ] Tool 有详细的 docstring（LLM 可理解）
- [ ] 参数类型标注完整
- [ ] 单元测试覆盖主要逻辑
- [ ] 集成测试可选运行（环境变量控制）
- [ ] 敏感信息（API key）不在代码中
- [ ] 遵循 RULE.md 规范（无副作用、依赖注入）

## 八、快速命令

```bash
# 测试 tool 是否被发现
python -m work_agent list-tools

# 测试单个 tool
python -m work_agent run "搜索 Python 的 web 框架"

# 运行单元测试
pytest tests/unit/test_github_api.py -v

# 运行集成测试（需要 API key）
GITHUB_API_TOKEN=xxx RUN_INTEGRATION=1 pytest tests/integration/ -v
```
