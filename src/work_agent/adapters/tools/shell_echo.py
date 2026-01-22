"""Shell Echo 工具（安全示例 - 仅 echo，禁止命令执行）"""

from openai.agents import function_tool


@function_tool
def shell_echo(text: str) -> str:
    """
    安全的文本回显（仅用于演示，禁止执行命令）

    Args:
        text: 要回显的文本

    Returns:
        回显的文本（带前缀）
    """
    # 安全检查：禁止特殊字符
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
    if any(char in text for char in dangerous_chars):
        return "Error: Input contains dangerous characters. Echo aborted."

    return f"[ECHO] {text}"


def get_tool():
    """暴露 tool 供自动发现"""
    return shell_echo
