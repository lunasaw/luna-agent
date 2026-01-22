"""Tool Registry 单元测试"""


from work_agent.adapters.tools._registry import ToolRegistry


def test_load_tools_success():
    """测试工具加载成功"""
    registry = ToolRegistry()
    tools = registry.load_tools()

    assert len(tools) > 0
    assert all(hasattr(tool, "name") for tool in tools)


def test_list_tools():
    """测试列出工具"""
    registry = ToolRegistry()
    registry.load_tools()

    tool_list = registry.list_tools()

    assert len(tool_list) > 0
    assert all("name" in tool for tool in tool_list)
    assert all("description" in tool for tool in tool_list)


def test_get_tool_existing():
    """测试获取存在的工具"""
    registry = ToolRegistry()
    registry.load_tools()

    # 假设 get_current_time 存在
    tool = registry.get_tool("get_current_time")
    assert tool is not None


def test_get_tool_nonexisting():
    """测试获取不存在的工具"""
    registry = ToolRegistry()
    registry.load_tools()

    tool = registry.get_tool("nonexistent_tool")
    assert tool is None
