"""## Weather API 客户端"""
import logging
from typing import Any

from work_agent.adapters.external.apis.base import BaseApiClient
from work_agent.utils.api_client import ApiResponse

logger = logging.getLogger(__name__)


class WeatherApiClient(BaseApiClient):
    """## Weather API 客户端封装

    职责：
    - 封装 Weather API 调用细节
    - 处理认证
    - 返回结构化数据
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: float = 30.0,
        retry_count: int = 2,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            retry_count=retry_count,
        )

        # OpenWeatherMap API 使用 appid 参数进行认证
        self.api_key = api_key

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            服务是否可用
        """
        try:
            # 使用一个简单的查询来检查 API 是否可用
            response = await self.client.get(
                "/weather",
                params={"q": "London", "appid": self.api_key},
            )
            return response.ok
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_weather(self, city: str, units: str = "metric") -> dict[str, Any]:
        """获取城市天气信息

        Args:
            city: 城市名称（中文或英文，如 "北京", "Beijing", "New York"）
            units: 单位系统（metric=摄氏度, imperial=华氏度, standard=开尔文）

        Returns:
            API 响应数据，包含天气详情

        Raises:
            ApiClientError: API 调用失败
        """
        logger.info(f"Fetching weather for city={city}, units={units}")

        response = await self.client.get(
            "/weather",
            params={"q": city, "appid": self.api_key, "units": units, "lang": "zh_cn"},
            raise_for_status=True,
        )

        return response.body
