"""数据传输对象（DTO）- 与 domain 解耦"""

from typing import Optional

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """运行 Agent 请求"""

    user_input: str = Field(..., min_length=1, description="用户输入")
    trace_id: Optional[str] = Field(None, description="可选的 trace_id")


class RunResponse(BaseModel):
    """运行 Agent 响应"""

    content: str = Field(..., description="Agent 响应内容")
    trace_id: str = Field(..., description="trace_id")
    success: bool = Field(default=True, description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")


class ToolInfo(BaseModel):
    """Tool 信息"""

    name: str
    description: str
    module: str


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = "ok"
    version: str = "0.1.0"
