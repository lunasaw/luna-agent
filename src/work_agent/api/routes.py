"""API 路由定义"""

import logging

from fastapi import APIRouter, HTTPException

from work_agent.adapters.observability.context import new_trace_id
from work_agent.api.dto import HealthResponse, RunRequest, RunResponse, ToolInfo
from work_agent.container import Container
from work_agent.domain.errors import AgentExecutionError

logger = logging.getLogger(__name__)


def create_router(container: Container) -> APIRouter:
    """
    创建路由（注入容器）

    Args:
        container: 依赖容器

    Returns:
        APIRouter: 路由实例
    """
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """健康检查"""
        return HealthResponse()

    @router.get("/tools", response_model=list[ToolInfo])
    def list_tools() -> list[ToolInfo]:
        """列出所有 tools"""
        tool_list = container.tool_registry.list_tools()
        return [ToolInfo(**tool) for tool in tool_list]

    @router.post("/run", response_model=RunResponse)
    def run_agent(request: RunRequest) -> RunResponse:
        """
        运行 Agent

        Args:
            request: 运行请求

        Returns:
            RunResponse: 运行响应

        Raises:
            HTTPException: 执行失败
        """
        trace_id = request.trace_id or new_trace_id()

        logger.info(
            f"API /run called: {request.user_input[:50]}...",
            extra={"trace_id": trace_id},
        )

        try:
            # 调用 service
            result = container.agent_service.run_once(
                user_input=request.user_input,
                trace_id=trace_id,
            )

            return RunResponse(
                content=result,
                trace_id=trace_id,
                success=True,
                error_message=None,
            )

        except AgentExecutionError as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    # 预留端点（未实现）
    @router.put("/config/instructions")
    def update_instructions() -> dict:
        """
        更新 Agent instructions（预留）

        TODO: 实现在线编辑 instructions 功能
        """
        return {"status": "not_implemented", "message": "Feature coming soon"}

    return router
