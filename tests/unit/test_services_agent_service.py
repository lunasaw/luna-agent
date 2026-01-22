"""Agent Service 单元测试"""

from unittest.mock import MagicMock

import pytest

from work_agent.config import Config
from work_agent.services.agent_service import AgentService


@pytest.fixture
def mock_agent():
    """Mock Agent"""
    return MagicMock()


@pytest.fixture
def mock_runner():
    """Mock Runner"""
    runner = MagicMock()
    runner.run.return_value = "test response"
    return runner


@pytest.fixture
def mock_config():
    """Mock Config"""
    return MagicMock(spec=Config)


def test_run_once_success(mock_agent, mock_runner, mock_config):
    """测试成功运行一次"""
    service = AgentService(
        agent=mock_agent,
        runner=mock_runner,
        config=mock_config,
    )

    result = service.run_once("test input")

    assert "test response" in result
    mock_runner.run.assert_called_once()


def test_run_once_with_custom_trace_id(mock_agent, mock_runner, mock_config):
    """测试使用自定义 trace_id"""
    service = AgentService(
        agent=mock_agent,
        runner=mock_runner,
        config=mock_config,
    )

    result = service.run_once("test input", trace_id="custom_trace_id")

    assert result is not None
    mock_runner.run.assert_called_once()
