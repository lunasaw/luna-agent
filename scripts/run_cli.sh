#!/usr/bin/env bash
# CLI 运行脚本（可选）

set -e

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 运行 CLI
python -m work_agent "$@"
