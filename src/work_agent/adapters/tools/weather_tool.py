"""## Weather Tool - Agent 可调用的工具"""
from typing import Any
from agents import function_tool

# 延迟初始化模式（从容器获取服务）
_service = None


def _get_service():
    """获取 Weather 服务实例（从容器注入）"""
    global _service
    if _service is None:
        from work_agent.container import get_weather_service
        _service = get_weather_service()
    return _service


@function_tool
async def get_city_weather(city: str) -> str:
    """
    获取指定城市的天气信息

    查询城市的实时天气，包括温度、湿度、天气状况、气压、风速等详细信息。
    支持中文和英文城市名称查询。

    Args:
        city: 城市名称（中文或英文，如 "北京", "Beijing", "New York", "Shanghai"）

    Returns:
        格式化的天气信息字符串，包含温度、体感温度、天气状况、湿度、气压、风速

    Examples:
        - get_city_weather("北京")
        - get_city_weather("Shanghai")
        - get_city_weather("Tokyo")
        - get_city_weather("New York")
    """
    # 参数校验
    if not city or not city.strip():
        return "错误: 城市名称不能为空"

    # 调用服务层
    service = _get_service()
    return await service.get_weather_summary(city)


def get_tool() -> Any:
    """暴露工具供自动发现"""
    return get_city_weather
