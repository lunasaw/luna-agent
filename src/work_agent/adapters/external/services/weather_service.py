"""## Weather 业务服务层"""
import logging
from typing import Any

from work_agent.adapters.external.apis.weather_api import WeatherApiClient
from work_agent.domain.errors import DomainError
from work_agent.utils.api_client import ApiClientError

logger = logging.getLogger(__name__)


class WeatherServiceError(DomainError):
    """## Weather 服务异常"""
    pass


class WeatherService:
    """## Weather 业务服务

    职责：
    - 业务逻辑编排
    - 数据转换和格式化
    - 异常转换（API 异常 → 领域异常）
    """

    def __init__(self, api_client: WeatherApiClient) -> None:
        self.api = api_client

    async def get_weather_summary(self, city: str) -> str:
        """获取天气摘要

        Args:
            city: 城市名称（中文或英文）

        Returns:
            格式化的天气信息字符串

        Raises:
            WeatherServiceError: 操作失败
        """
        try:
            logger.info(f"Fetching weather summary for city={city}")

            # 调用 API
            data = await self.api.get_weather(city)

            # 提取数据
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            desc = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]

            # 格式化输出
            result = f"🌤️ {city} 天气情况:\n\n"
            result += f"温度: {temp}°C (体感: {feels_like}°C)\n"
            result += f"天气: {desc}\n"
            result += f"湿度: {humidity}%\n"
            result += f"气压: {pressure} hPa\n"
            result += f"风速: {wind_speed} m/s\n"

            return result

        except ApiClientError as e:
            logger.error(f"Failed to fetch weather: {e}", exc_info=True)
            raise WeatherServiceError(f"获取天气失败: {e}") from e
