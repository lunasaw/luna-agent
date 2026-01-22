"""领域模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgentRequest:
    """Agent 请求"""

    user_input: str
    trace_id: str
    session_id: Optional[str] = None


@dataclass(frozen=True)
class AgentResponse:
    """Agent 响应"""

    content: str
    trace_id: str
    tool_calls_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
