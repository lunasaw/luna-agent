"""Agent 服务 - 用例编排层"""

import logging
from typing import Any

from work_agent.adapters.observability.context import new_trace_id
from work_agent.config import Config
from work_agent.domain.errors import AgentExecutionError
from work_agent.domain.models import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


class AgentService:
    """Agent 服务（用例编排）"""

    def __init__(self, agent: Any, runner: Any, config: Config):
        """
        初始化 Agent 服务

        Args:
            agent: Agent 实例（注入）
            runner: Runner 实例（注入）
            config: 配置对象（注入）
        """
        self.agent = agent
        self.runner = runner
        self.config = config

    def run_once(self, user_input: str, trace_id: str | None = None) -> str:
        """
        单次运行 Agent

        Args:
            user_input: 用户输入
            trace_id: 可选的 trace_id（用于外部传入）

        Returns:
            Agent 响应内容

        Raises:
            AgentExecutionError: 执行失败
        """
        trace_id = trace_id or new_trace_id()

        logger.info(
            f"Running agent with input: {user_input[:50]}...",
            extra={"trace_id": trace_id},
        )

        try:
            # 执行 Agent
            response = self.runner.run(self.agent, user_input)

            # 提取结果
            result_content = self._extract_response_content(response)

            logger.info(
                f"Agent completed successfully",
                extra={"trace_id": trace_id, "response_length": len(result_content)},
            )

            return result_content

        except Exception as e:
            logger.error(
                f"Agent execution failed: {e}",
                exc_info=True,
                extra={"trace_id": trace_id},
            )
            raise AgentExecutionError(f"Agent execution failed: {e}") from e

    def repl(self) -> None:
        """
        REPL 交互模式

        注意：此方法包含 I/O 仅用于 CLI 场景，API 模式不应调用
        """
        trace_id = new_trace_id()
        logger.info("Starting REPL mode", extra={"trace_id": trace_id})

        while True:
            try:
                # I/O 在 service 层是例外（仅限 CLI REPL 场景）
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ("quit", "exit", "q"):
                    break

                if not user_input:
                    continue

                # 调用 run_once
                response = self.run_once(user_input, trace_id)

                # 输出（CLI 场景）
                print(f"\nAgent: {response}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"REPL error: {e}", exc_info=True, extra={"trace_id": trace_id})
                print(f"\nError: {e}")

        logger.info("REPL mode ended", extra={"trace_id": trace_id})

    def _extract_response_content(self, response: Any) -> str:
        """
        提取响应内容（适配不同 SDK 版本）

        Args:
            response: Agent ��应对象

        Returns:
            响应内容字符串
        """
        # 尝试多种提取方式（兼容不同 SDK 版本）
        if isinstance(response, str):
            return response

        if hasattr(response, "content"):
            return str(response.content)

        if hasattr(response, "output"):
            return str(response.output)

        if hasattr(response, "messages") and response.messages:
            last_message = response.messages[-1]
            if hasattr(last_message, "content"):
                return str(last_message.content)

        # Fallback
        return str(response)
