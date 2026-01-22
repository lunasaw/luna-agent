"""领域模型单元测试"""

import pytest

from work_agent.domain.models import AgentRequest, AgentResponse


def test_agent_request_creation():
    """测试 AgentRequest 创建"""
    request = AgentRequest(
        user_input="test input",
        trace_id="test_trace_id",
    )

    assert request.user_input == "test input"
    assert request.trace_id == "test_trace_id"
    assert request.session_id is None


def test_agent_response_creation():
    """测试 AgentResponse 创建"""
    response = AgentResponse(
        content="test response",
        trace_id="test_trace_id",
        tool_calls_count=2,
    )

    assert response.content == "test response"
    assert response.trace_id == "test_trace_id"
    assert response.tool_calls_count == 2
    assert response.success is True


def test_agent_response_immutability():
    """测试领域模型不可变性"""
    response = AgentResponse(
        content="test",
        trace_id="trace",
    )

    with pytest.raises(AttributeError):  # frozen dataclass
        response.content = "new content"  # type: ignore
