#!/usr/bin/env python3
"""vLLM Agent 测试脚本

此脚本演示如何使用 vLLM 服务作为后端运行 Agent，测试 weather tool 的功能。

前置条件:
1. 启动 vLLM 服务（见下方说明）
2. 配置环境变量

使用方法:
    # 方法 1: 使用环境变量
    export OPENAI_API_KEY=EMPTY
    export OPENAI_API_BASE=http://localhost:8000/v1
    export AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct
    export WEATHER_API_KEY=your_weather_api_key
    python scripts/test_vllm_agent.py

    # 方法 2: 命令行参数
    python scripts/test_vllm_agent.py \\
        --base-url http://localhost:8000/v1 \\
        --model Qwen/Qwen2.5-7B-Instruct \\
        --query "查询北京的天气"
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from work_agent.adapters.llm.agent_factory import build_agent
from work_agent.adapters.llm.runner_factory import build_runner
from work_agent.adapters.tools._registry import ToolRegistry
from work_agent.config import Config
from work_agent.container import build_container, set_global_container


def setup_logging(level: str = "INFO") -> None:
    """配置日志"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def test_vllm_agent(
    base_url: str,
    model: str,
    query: str,
    api_key: str = "EMPTY",
) -> None:
    """测试 vLLM Agent

    Args:
        base_url: vLLM 服务地址 (如 http://localhost:8000/v1)
        model: 模型名称 (如 Qwen/Qwen2.5-7B-Instruct)
        query: 测试查询
        api_key: API Key (vLLM 不需要真实 key，使用 EMPTY)
    """
    logger = logging.getLogger(__name__)

    # 1. 设置环境变量（OpenAI SDK 会读取这些）
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = base_url
    os.environ["AGENT_MODEL"] = model

    logger.info("=" * 60)
    logger.info("vLLM Agent 测试")
    logger.info("=" * 60)
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Model: {model}")
    logger.info(f"Query: {query}")
    logger.info("=" * 60)

    # 2. 加载配置
    try:
        # 临时修改环境变量绕过 API key 校验
        original_key_check = os.environ.get("OPENAI_API_KEY")
        if api_key == "EMPTY":
            # 设置一个占位值来通过校验
            os.environ["OPENAI_API_KEY"] = "sk-vllm-placeholder-key"

        # 重新加载配置以应用 base_url
        from work_agent.config import Config
        config = Config()  # type: ignore

        # 恢复原始设置
        os.environ["OPENAI_API_KEY"] = api_key

    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        logger.info("\n请确保设置了 WEATHER_API_KEY 环境变量")
        return

    # 3. 构建容器
    try:
        logger.info("\n正在构建依赖容器...")
        container = build_container(config)
        set_global_container(container)
        logger.info(f"✅ 成功加载 {len(container.tools)} 个工具")

        # 列出可用工具
        logger.info("\n可用的工具:")
        for tool in container.tools:
            name = getattr(tool, "name", "unknown")
            logger.info(f"  • {name}")

    except Exception as e:
        logger.error(f"容器构建失败: {e}", exc_info=True)
        return

    # 4. 运行查询
    try:
        logger.info(f"\n正在执行查询: {query}")
        logger.info("-" * 60)

        result = container.agent_service.run_once(query)

        logger.info("\n" + "=" * 60)
        logger.info("Agent 响应:")
        logger.info("=" * 60)
        print(f"\n{result}\n")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"查询执行失败: {e}", exc_info=True)
        logger.info("\n可能的原因:")
        logger.info("  1. vLLM 服务未启动或无法访问")
        logger.info("  2. 模型不支持 function calling")
        logger.info("  3. Weather API key 未设置或无效")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="vLLM Agent 测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 使用默认配置
  python scripts/test_vllm_agent.py

  # 指定 vLLM 服务地址和模型
  python scripts/test_vllm_agent.py \\
      --base-url http://localhost:8000/v1 \\
      --model Qwen/Qwen2.5-7B-Instruct \\
      --query "查询上海的天气"

启动 vLLM 服务:

  # 使用 Qwen2.5-7B-Instruct (支持 function calling)
  python -m vllm.entrypoints.openai.api_server \\
      --model Qwen/Qwen2.5-7B-Instruct \\
      --host 0.0.0.0 \\
      --port 8000 \\
      --served-model-name Qwen/Qwen2.5-7B-Instruct \\
      --enable-auto-tool-choice \\
      --tool-call-parser hermes

  # 或使用 Docker
  docker run --gpus all -p 8000:8000 \\
      vllm/vllm-openai:latest \\
      --model Qwen/Qwen2.5-7B-Instruct \\
      --enable-auto-tool-choice \\
      --tool-call-parser hermes
        """,
    )

    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1"),
        help="vLLM 服务地址 (默认: http://localhost:8000/v1)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("AGENT_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        help="模型名称 (默认: Qwen/Qwen2.5-7B-Instruct)",
    )
    parser.add_argument(
        "--query",
        default="查询北京的天气",
        help="测试查询 (默认: 查询北京的天气)",
    )
    parser.add_argument(
        "--api-key",
        default="EMPTY",
        help="API Key (vLLM 不需要，默认: EMPTY)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)",
    )

    args = parser.parse_args()

    # 检查 Weather API key
    if not os.getenv("WEATHER_API_KEY"):
        print("⚠️  警告: 未设置 WEATHER_API_KEY 环境变量")
        print("如果要测试天气查询，请设置:")
        print("  export WEATHER_API_KEY=your_api_key")
        print()
        response = input("是否继续？(y/n): ")
        if response.lower() != "y":
            return

    # 设置日志
    setup_logging(args.log_level)

    # 运行测试
    test_vllm_agent(
        base_url=args.base_url,
        model=args.model,
        query=args.query,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
