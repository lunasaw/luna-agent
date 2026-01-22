"""LLM 模型与 Provider 抽象"""

from dataclasses import dataclass
from enum import Enum


class ModelProvider(str, Enum):
    """模型提供商"""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass(frozen=True)
class ModelConfig:
    """模型配置"""

    provider: ModelProvider
    model_name: str
    api_key: str
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


def get_model_config(model_name: str, api_key: str) -> ModelConfig:
    """
    根据模型名称推断配置

    Args:
        model_name: 模型名称
        api_key: API Key

    Returns:
        ModelConfig: 模型配置
    """
    # 当前仅支持 OpenAI，后续可扩展
    provider = ModelProvider.OPENAI

    return ModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
    )
