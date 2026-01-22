"""通用 HTTP API 客户端

提供基础的 HTTP 请求功能，支持 GET, POST, PUT, PATCH, DELETE 等方法，
支持 JSON body, form data, query params 等多种请求格式。
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from typing import Any, TypeVar
from urllib.parse import urlencode, urljoin

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class HttpMethod(str, Enum):
    """HTTP 请求方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ContentType(str, Enum):
    """请求内容类型"""

    JSON = "application/json"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    TEXT = "text/plain"
    XML = "application/xml"


@dataclass
class ApiResponse:
    """API 响应封装"""

    status_code: int
    headers: dict[str, str]
    body: Any
    raw_text: str = ""

    @property
    def ok(self) -> bool:
        """请求是否成功 (2xx 状态码)"""
        return 200 <= self.status_code < 300

    @property
    def status(self) -> HTTPStatus | None:
        """获取 HTTP 状态枚举"""
        try:
            return HTTPStatus(self.status_code)
        except ValueError:
            return None

    def json(self) -> Any:
        """获取 JSON 响应体"""
        return self.body if isinstance(self.body, (dict, list)) else None

    def text(self) -> str:
        """获取文本响应体"""
        return self.raw_text


@dataclass
class ApiClientConfig:
    """API 客户端配置"""

    base_url: str = ""
    timeout: float = 30.0
    default_headers: dict[str, str] = field(default_factory=dict)
    retry_count: int = 0
    retry_delay: float = 1.0
    verify_ssl: bool = True


class ApiClientError(Exception):
    """API 客户端异常基类"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ConnectionError(ApiClientError):
    """连接错误"""

    pass


class TimeoutError(ApiClientError):
    """超时错误"""

    pass


class HttpError(ApiClientError):
    """HTTP 错误响应"""

    def __init__(self, message: str, status_code: int, response: ApiResponse) -> None:
        super().__init__(message, status_code)
        self.response = response


T = TypeVar("T")


class ApiClient:
    """通用 HTTP API 客户端

    支持同步和异步请求，支持多种请求格式。

    使用示例:
        # 基础用法
        client = ApiClient(base_url="https://api.example.com")

        # GET 请求带 query params
        response = await client.get("/users", params={"page": 1, "limit": 10})

        # POST 请求带 JSON body
        response = await client.post("/users", json={"name": "test", "email": "test@example.com"})

        # PUT 请求
        response = await client.put("/users/1", json={"name": "updated"})

        # DELETE 请求
        response = await client.delete("/users/1")

        # 表单提交
        response = await client.post("/login", data={"username": "test", "password": "123"})

        # 自定义请求头
        response = await client.get("/protected", headers={"Authorization": "Bearer token"})
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
        verify_ssl: bool = True,
    ) -> None:
        """初始化 API 客户端

        Args:
            base_url: 基础 URL，所有请求路径都将相对于此 URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
            retry_count: 失败重试次数
            retry_delay: 重试间隔（秒）
            verify_ssl: 是否验证 SSL 证书
        """
        self.config = ApiClientConfig(
            base_url=base_url.rstrip("/") if base_url else "",
            timeout=timeout,
            default_headers=headers or {},
            retry_count=retry_count,
            retry_delay=retry_delay,
            verify_ssl=verify_ssl,
        )
        self._session: Any = None

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        """构建完整 URL

        Args:
            path: 请求路径
            params: 查询参数

        Returns:
            完整 URL
        """
        if self.config.base_url:
            url = urljoin(self.config.base_url + "/", path.lstrip("/"))
        else:
            url = path

        if params:
            # 过滤 None 值并编码参数
            filtered_params = {k: v for k, v in params.items() if v is not None}
            if filtered_params:
                query_string = urlencode(filtered_params, doseq=True)
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}{query_string}"

        return url

    def _merge_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        """合并默认请求头和自定义请求头

        Args:
            headers: 自定义请求头

        Returns:
            合并后的请求头
        """
        merged = dict(self.config.default_headers)
        if headers:
            merged.update(headers)
        return merged

    async def _request_with_httpx(
        self,
        method: HttpMethod,
        url: str,
        headers: dict[str, str],
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> ApiResponse:
        """使用 httpx 发送请求"""
        import httpx

        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        ) as client:
            response = await client.request(
                method=method.value,
                url=url,
                headers=headers,
                json=json,
                data=data,
                files=files,
            )

            try:
                body = response.json()
            except Exception:
                body = response.text

            return ApiResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=body,
                raw_text=response.text,
            )

    async def _request_with_aiohttp(
        self,
        method: HttpMethod,
        url: str,
        headers: dict[str, str],
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> ApiResponse:
        """使用 aiohttp 发送请求"""
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(ssl=self.config.verify_ssl)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # 处理文件上传
            form_data = None
            if files:
                form_data = aiohttp.FormData()
                if data:
                    for key, value in data.items():
                        form_data.add_field(key, str(value))
                for key, file_info in files.items():
                    if isinstance(file_info, tuple):
                        filename, content = file_info[0], file_info[1]
                        content_type = file_info[2] if len(file_info) > 2 else "application/octet-stream"
                        form_data.add_field(key, content, filename=filename, content_type=content_type)
                    else:
                        form_data.add_field(key, file_info)

            async with session.request(
                method=method.value,
                url=url,
                headers=headers,
                json=json,
                data=form_data if files else data,
            ) as response:
                raw_text = await response.text()
                try:
                    import json as json_module

                    body = json_module.loads(raw_text)
                except Exception:
                    body = raw_text

                return ApiResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=body,
                    raw_text=raw_text,
                )

    async def _request_with_urllib(
        self,
        method: HttpMethod,
        url: str,
        headers: dict[str, str],
        json_data: Any = None,
        data: dict[str, Any] | None = None,
    ) -> ApiResponse:
        """使用 urllib 发送请求（无外部依赖备选方案）"""
        import json as json_module
        import ssl
        import urllib.request

        # 准备请求数据
        body_bytes: bytes | None = None
        if json_data is not None:
            body_bytes = json_module.dumps(json_data).encode("utf-8")
            headers["Content-Type"] = ContentType.JSON.value
        elif data:
            body_bytes = urlencode(data).encode("utf-8")
            headers["Content-Type"] = ContentType.FORM.value

        request = urllib.request.Request(
            url=url,
            data=body_bytes,
            headers=headers,
            method=method.value,
        )

        # SSL 上下文
        ssl_context = None
        if not self.config.verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        def do_request() -> ApiResponse:
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.config.timeout,
                    context=ssl_context,
                ) as response:
                    raw_text = response.read().decode("utf-8")
                    try:
                        body = json_module.loads(raw_text)
                    except Exception:
                        body = raw_text

                    return ApiResponse(
                        status_code=response.status,
                        headers=dict(response.headers),
                        body=body,
                        raw_text=raw_text,
                    )
            except urllib.error.HTTPError as e:
                raw_text = e.read().decode("utf-8") if e.fp else ""
                try:
                    body = json_module.loads(raw_text)
                except Exception:
                    body = raw_text
                return ApiResponse(
                    status_code=e.code,
                    headers=dict(e.headers) if e.headers else {},
                    body=body,
                    raw_text=raw_text,
                )

        # 在线程池中运行同步请求
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, do_request)

    async def request(
        self,
        method: HttpMethod | str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 HTTP 请求

        Args:
            method: HTTP 方法
            path: 请求路径
            params: URL 查询参数
            headers: 请求头
            json: JSON 请求体
            data: 表单数据
            files: 上传文件
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象

        Raises:
            ConnectionError: 连接失败
            TimeoutError: 请求超时
            HttpError: HTTP 错误响应（当 raise_for_status=True）
        """
        if isinstance(method, str):
            method = HttpMethod(method.upper())

        url = self._build_url(path, params)
        merged_headers = self._merge_headers(headers)

        last_error: Exception | None = None
        attempts = self.config.retry_count + 1

        for attempt in range(attempts):
            try:
                # 选择可用的 HTTP 库
                if HTTPX_AVAILABLE:
                    response = await self._request_with_httpx(
                        method, url, merged_headers, json, data, files
                    )
                elif AIOHTTP_AVAILABLE:
                    response = await self._request_with_aiohttp(
                        method, url, merged_headers, json, data, files
                    )
                else:
                    # 使用内置 urllib（不支持文件上传）
                    if files:
                        raise ApiClientError(
                            "文件上传需要安装 httpx 或 aiohttp: pip install httpx"
                        )
                    response = await self._request_with_urllib(
                        method, url, merged_headers, json, data
                    )

                if raise_for_status and not response.ok:
                    raise HttpError(
                        f"HTTP {response.status_code}: {response.raw_text[:200]}",
                        response.status_code,
                        response,
                    )

                return response

            except (HttpError, ApiClientError):
                raise
            except asyncio.TimeoutError as e:
                last_error = TimeoutError(f"请求超时: {url}")
                if attempt < attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
            except Exception as e:
                error_msg = str(e)
                if "connect" in error_msg.lower() or "connection" in error_msg.lower():
                    last_error = ConnectionError(f"连接失败: {url} - {error_msg}")
                else:
                    last_error = ApiClientError(f"请求失败: {url} - {error_msg}")
                if attempt < attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)

        if last_error:
            raise last_error
        raise ApiClientError(f"请求失败: {url}")

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 GET 请求

        Args:
            path: 请求路径
            params: URL 查询参数
            headers: 请求头
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象
        """
        return await self.request(
            HttpMethod.GET,
            path,
            params=params,
            headers=headers,
            raise_for_status=raise_for_status,
        )

    async def post(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 POST 请求

        Args:
            path: 请求路径
            params: URL 查询参数
            headers: 请求头
            json: JSON 请求体
            data: 表单数据
            files: 上传文件
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象
        """
        return await self.request(
            HttpMethod.POST,
            path,
            params=params,
            headers=headers,
            json=json,
            data=data,
            files=files,
            raise_for_status=raise_for_status,
        )

    async def put(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 PUT 请求

        Args:
            path: 请求路径
            params: URL 查询参数
            headers: 请求头
            json: JSON 请求体
            data: 表单数据
            files: 上传文件
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象
        """
        return await self.request(
            HttpMethod.PUT,
            path,
            params=params,
            headers=headers,
            json=json,
            data=data,
            files=files,
            raise_for_status=raise_for_status,
        )

    async def patch(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | None = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 PATCH 请求

        Args:
            path: 请求路径
            params: URL 查询参数
            headers: 请求头
            json: JSON 请求体
            data: 表单数据
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象
        """
        return await self.request(
            HttpMethod.PATCH,
            path,
            params=params,
            headers=headers,
            json=json,
            data=data,
            raise_for_status=raise_for_status,
        )

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 DELETE 请求

        Args:
            path: 请求路���
            params: URL 查询参数
            headers: 请求头
            json: JSON 请求体（部分 API 需要）
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象
        """
        return await self.request(
            HttpMethod.DELETE,
            path,
            params=params,
            headers=headers,
            json=json,
            raise_for_status=raise_for_status,
        )

    async def head(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raise_for_status: bool = False,
    ) -> ApiResponse:
        """发送 HEAD 请求

        Args:
            path: 请求路径
            params: URL 查询参数
            headers: 请求头
            raise_for_status: 是否在非 2xx 响应时抛出异常

        Returns:
            ApiResponse 响应对象
        """
        return await self.request(
            HttpMethod.HEAD,
            path,
            params=params,
            headers=headers,
            raise_for_status=raise_for_status,
        )

    def set_header(self, key: str, value: str) -> None:
        """设置默认请求头

        Args:
            key: 请求头名称
            value: 请求头值
        """
        self.config.default_headers[key] = value

    def set_bearer_token(self, token: str) -> None:
        """设置 Bearer Token 认证

        Args:
            token: 认证 Token
        """
        self.set_header("Authorization", f"Bearer {token}")

    def set_basic_auth(self, username: str, password: str) -> None:
        """设置 Basic Auth 认证

        Args:
            username: 用户名
            password: 密码
        """
        import base64

        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.set_header("Authorization", f"Basic {credentials}")
