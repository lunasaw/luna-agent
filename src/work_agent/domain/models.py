"""领域模型"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRequest:
    """Agent 请求"""

    user_input: str
    trace_id: str
    session_id: str | None = None


@dataclass(frozen=True)
class AgentResponse:
    """Agent 响应"""

    content: str
    trace_id: str
    tool_calls_count: int = 0
    success: bool = True
    error_message: str | None = None
