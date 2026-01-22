"""配置管理 - 唯一读取环境变量的位置"""

import sys
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """应用配置（类型安全）"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI 配置
    openai_api_key: str = Field(..., description="OpenAI API Key")

    # Agent 配置
    agent_model: str = Field(default="gpt-4o", description="Agent 模型名称")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")

    # 可观测性
    enable_tracing: bool = Field(default=False, description="是否启用 tracing")

    # Session 后端
    session_backend: Literal["memory", "sqlite"] = Field(
        default="memory",
        description="会话存储后端",
    )

    # API 配置
    api_host: str = Field(default="0.0.0.0", description="API 监听地址")
    api_port: int = Field(default=8000, description="API 监听端口")


def load_config() -> Config:
    """
    加载配置并进行启动时校验

    Returns:
        Config: 配置对象

    Raises:
        SystemExit: 配置错误时退出
    """
    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("\nPlease check your .env file or environment variables.", file=sys.stderr)
        print("Required: OPENAI_API_KEY", file=sys.stderr)
        sys.exit(1)

    # 额外校验
    if not config.openai_api_key or config.openai_api_key == "sk-your-api-key-here":
        print("Error: OPENAI_API_KEY not found or using placeholder value", file=sys.stderr)
        print("Please set a valid API key in .env file or environment", file=sys.stderr)
        sys.exit(1)

    return config
