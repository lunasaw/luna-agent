"""应用组装与 CLI 入口"""

import sys

import typer

from work_agent.config import load_config
from work_agent.container import build_container, shutdown_container
from work_agent.logging import configure_logging

app = typer.Typer(
    name="work-agent",
    help="工程化 AI Agent - 日常工作助理",
    add_completion=False,
)


@app.command()
def run(user_input: str) -> None:
    """
    单次运行 Agent

    Args:
        user_input: 用户输入的问题或指令
    """
    container = None
    try:
        # 1. 加载配置
        config = load_config()

        # 2. 配置日志
        configure_logging(config.log_level)

        # 3. 构建容器
        container = build_container(config)

        # 4. 执行运行
        result = container.agent_service.run_once(user_input)

        # 5. 输出结果
        typer.echo(f"\n{result}\n")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        if container:
            shutdown_container(container)


@app.command()
def repl() -> None:
    """
    交互式 REPL 模式
    """
    container = None
    try:
        # 1. 加载配置
        config = load_config()

        # 2. 配置日志
        configure_logging(config.log_level)

        # 3. 构建容器
        container = build_container(config)

        # 4. 启动 REPL
        typer.echo("=== Work Agent REPL ===")
        typer.echo("输入 'quit' 或 'exit' 退出\n")

        container.agent_service.repl()

    except KeyboardInterrupt:
        typer.echo("\n\nBye!")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        if container:
            shutdown_container(container)


@app.command(name="list-tools")
def list_tools() -> None:
    """
    列出所有可用的 tools
    """
    container = None
    try:
        # 1. 加载配置
        config = load_config()

        # 2. 配置日志（静默模式）
        configure_logging("ERROR")

        # 3. 构建容器（仅需 tool_registry）
        container = build_container(config)

        # 4. 列出 tools
        typer.echo("\n=== Available Tools ===\n")
        tools = container.tools
        if not tools:
            typer.echo("No tools found.")
            return

        for tool in tools:
            name = getattr(tool, "name", "unknown")
            description = getattr(tool, "description", "No description")
            typer.echo(f"  • {name}")
            typer.echo(f"    {description}\n")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        if container:
            shutdown_container(container)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="API host"),
    port: int = typer.Option(8000, help="API port"),
) -> None:
    """
    启动 API 服务（需要安装 api 依赖）
    """
    try:
        from work_agent.api.app import create_api_app
    except ImportError:
        typer.echo(
            "Error: API dependencies not installed. Run: uv pip install -e '.[api]'",
            err=True,
        )
        sys.exit(1)

    try:
        # 1. 加载配置
        config = load_config()

        # 2. 配置日志
        configure_logging(config.log_level)

        # 3. 构建容器
        container = build_container(config)

        # 4. 创建 FastAPI app
        api_app = create_api_app(container)

        # 5. 启动服务
        import uvicorn

        typer.echo(f"Starting API server at http://{host}:{port}")
        uvicorn.run(api_app, host=host, port=port)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


def cli() -> None:
    """主 CLI 入口"""
    app()


if __name__ == "__main__":
    cli()
