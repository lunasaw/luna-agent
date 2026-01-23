#!/bin/bash
# 快速启动 vLLM 服务的脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
MODEL=${1:-"Qwen/Qwen2.5-7B-Instruct"}
PORT=${2:-8000}
HOST=${3:-"0.0.0.0"}

echo -e "${GREEN}=== vLLM 服务启动脚本 ===${NC}"
echo ""
echo "配置:"
echo "  模型: $MODEL"
echo "  端口: $PORT"
echo "  主机: $HOST"
echo ""

# 检查 GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}错误: 未检测到 NVIDIA GPU${NC}"
    echo "如果使用 CPU 运行，性能会很慢"
    read -p "是否继续？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查 vLLM 是否安装
if ! python -c "import vllm" &> /dev/null; then
    echo -e "${YELLOW}vLLM 未安装，正在安装...${NC}"
    pip install vllm
fi

# 启动服务
echo -e "${GREEN}正在启动 vLLM 服务...${NC}"
echo ""

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host "$HOST" \
    --port "$PORT" \
    --served-model-name "$MODEL" \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --gpu-memory-utilization 0.9

# 注意: 脚本会在前台运行，Ctrl+C 停止服务
