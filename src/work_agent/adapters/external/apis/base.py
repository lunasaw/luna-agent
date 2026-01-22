"""基础 API 客户端抽象类

提供统一的 API 客户端接口，所有 API 客户端应继承此基类。
"""
import logging
from abc import ABC, abstractmethod
from typing import Any

from work_agent.utils.api_client import ApiClient

logger = logging.getLogger(__name__)


class BaseApiClient(ABC):
    """API 客户端基类

    职责:
    - 提供统一的初始化接口
    - 封装通用的认证逻辑
    - 提供统一的错误处理模式
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retry_count: int = 2,
        retry_delay: float = 1.0,
        verify_ssl: bool = True,
    ) -> None:
        """初始化 API 客户端

        Args:
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
            retry_count: 失败重试次数
            retry_delay: 重试间隔（秒）
            verify_ssl: 是否验证 SSL 证书
        """
        self.base_url = base_url
        self.client = ApiClient(
            base_url=base_url,
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay,
            verify_ssl=verify_ssl,
        )
        logger.info(f"Initialized {self.__class__.__name__} with base_url={base_url}")

    def set_auth_token(self, token: str) -> None:
        """设置 Bearer Token 认证

        Args:
            token: 认证 token
        """
        self.client.set_bearer_token(token)
        logger.debug(f"Set auth token for {self.__class__.__name__}")

    def set_api_key(self, key_name: str, api_key: str) -> None:
        """设置 API Key（通过请求头）

        Args:
            key_name: API Key 的请求头名称（如 "X-API-Key"）
            api_key: API Key 值
        """
        self.client.set_header(key_name, api_key)
        logger.debug(f"Set API key '{key_name}' for {self.__class__.__name__}")

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查

        检查 API 服务是否可用。

        Returns:
            bool: 服务是否可用

        Note:
            子类应实现此方法，返回 True 表示服务正常
        """
        pass
