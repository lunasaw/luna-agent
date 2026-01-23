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


async def main() -> None:
    """测试 Weather 服务

    使用方法:
        python -m work_agent.adapters.external.services.weather_service
    """
    import asyncio
    import os

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 从环境变量读取配置
    api_key = os.getenv("WEATHER_API_KEY", "")
    base_url = os.getenv(
        "WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5"
    )

    if not api_key:
        print("❌ 错误: 未设置 WEATHER_API_KEY 环境变量")
        print("\n使用方法:")
        print("  export WEATHER_API_KEY=your_api_key")
        print("  python -m work_agent.adapters.external.services.weather_service")
        return

    print(f"🔧 配置信息:")
    print(f"  API Base URL: {base_url}")
    print(f"  API Key: {api_key[:10]}...{api_key[-4:]}\n")

    # 创建 API 客户端
    api_client = WeatherApiClient(
        base_url=base_url,
        api_key=api_key,
        timeout=10.0,
    )

    # 创建服务
    service = WeatherService(api_client)

    # 测试健康检查
    print("=== 健康检查 ===")
    try:
        is_healthy = await api_client.health_check()
        if is_healthy:
            print("✅ API 服务正常\n")
        else:
            print("❌ API 服务异常\n")
            return
    except Exception as e:
        print(f"❌ 健康检查失败: {e}\n")
        return

    # 测试查询多个城市
    print("=== 天气查询测试 ===\n")
    test_cities = [
        "Beijing",
        "Shanghai",
        "Tokyo",
        "New York",
        "London",
        "Paris",
    ]

    for city in test_cities:
        try:
            print(f"查询 {city}...")
            result = await service.get_weather_summary(city)
            print(result)
            print("-" * 50)
            # 避免请求过快
            await asyncio.sleep(0.5)
        except WeatherServiceError as e:
            print(f"❌ 查询 {city} 失败: {e}\n")
        except Exception as e:
            print(f"❌ 未知错误: {e}\n")

    print("\n✅ 测试完成")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
