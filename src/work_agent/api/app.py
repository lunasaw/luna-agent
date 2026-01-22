"""FastAPI 应用（可选依赖）"""

import logging
from typing import Any

from fastapi import FastAPI

from work_agent.api.routes import create_router
from work_agent.container import Container

logger = logging.getLogger(__name__)


def create_api_app(container: Container) -> FastAPI:
    """
    创建 FastAPI 应用

    Args:
        container: 依赖容器

    Returns:
        FastAPI: 应用实例
    """
    app = FastAPI(
        title="Work Agent API",
        description="工程化 AI Agent API",
        version="0.1.0",
    )

    # 挂载路由
    router = create_router(container)
    app.include_router(router)

    logger.info("FastAPI app created")
    return app
