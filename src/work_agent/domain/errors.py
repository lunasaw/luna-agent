"""领域异常"""


class DomainError(Exception):
    """领域层基础异常"""

    pass


class AgentExecutionError(DomainError):
    """Agent 执行错误"""

    pass


class ToolNotFoundError(DomainError):
    """Tool 未找到"""

    pass


class ConfigurationError(DomainError):
    """配置错误"""

    pass
