# vLLM 集成指南

本指南介绍如何使用 vLLM 作为 LLM 后端运行 Work Agent，替代 OpenAI 官方 API。

## 为什么使用 vLLM？

- ✅ **本地部署**: 数据不出本地，保护隐私
- ✅ **成本节省**: 无需支付 OpenAI API 费用
- ✅ **高性能**: GPU 加速推理，支持 PagedAttention
- ✅ **兼容性**: 提供 OpenAI 兼容 API
- ✅ **开源模型**: 支持 Qwen、Llama、Mistral 等开源模型

## 前置要求

### 1. 硬件要求

- **GPU**: NVIDIA GPU (推荐 16GB+ 显存用于 7B 模型)
- **CPU**: 可选，性能较低
- **内存**: 推荐 32GB+ RAM

### 2. 软件依赖

```bash
# 安装 vLLM
pip install vllm

# 或使用 conda
conda install vllm -c conda-forge
```

## 快速开始

### 步骤 1: 启动 vLLM 服务

#### 方法 1: Python 命令

```bash
# 使用 Qwen2.5-7B-Instruct (推荐，支持 function calling)
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name Qwen/Qwen2.5-7B-Instruct \
    --enable-auto-tool-choice \
    --tool-call-parser hermes

# 其他支持 function calling 的模型
# - meta-llama/Llama-3.1-8B-Instruct
# - mistralai/Mistral-7B-Instruct-v0.3
# - NousResearch/Hermes-2-Pro-Llama-3-8B
```

**重要参数说明:**
- `--enable-auto-tool-choice`: 启用工具调用
- `--tool-call-parser hermes`: 使用 Hermes 格式解析工具调用
- `--served-model-name`: 模型名称（需与 Agent 配置一致）

#### 方法 2: Docker

```bash
# 拉取镜像
docker pull vllm/vllm-openai:latest

# 启动服务
docker run --gpus all -p 8000:8000 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen2.5-7B-Instruct \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

#### 验证服务

```bash
# 检查服务状态
curl http://localhost:8000/v1/models

# 测试 chat completions
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": "Hello"}]
    }'
```

### 步骤 2: 配置环境变量

编辑 `.env` 文件:

```bash
# vLLM 配置
OPENAI_API_KEY=EMPTY  # vLLM 不需要真实 key
OPENAI_API_BASE=http://localhost:8000/v1
AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct

# Weather API (如果要测试 weather tool)
WEATHER_API_KEY=your_weather_api_key
```

### 步骤 3: 运行 Agent

#### 使用测试脚本（推荐）

```bash
# 设置环境变量
export WEATHER_API_KEY=your_api_key

# 运行测试
.venv/bin/python scripts/test_vllm_agent.py

# 或指定参数
.venv/bin/python scripts/test_vllm_agent.py \
    --base-url http://localhost:8000/v1 \
    --model Qwen/Qwen2.5-7B-Instruct \
    --query "查询上海的天气"
```

#### 使用 CLI

```bash
# 激活虚拟环境
source .venv/bin/activate

# 列出工具
python -m work_agent list-tools

# 单次查询
python -m work_agent run "查询北京的天气"

# 交互模式
python -m work_agent repl
```

## 推荐模型

### 支持 Function Calling 的模型

| 模型 | 参数量 | 显存需求 | 推荐场景 |
|------|--------|----------|----------|
| Qwen/Qwen2.5-7B-Instruct | 7B | ~16GB | **推荐，中文效果好** |
| Qwen/Qwen2.5-14B-Instruct | 14B | ~28GB | 更强性能 |
| meta-llama/Llama-3.1-8B-Instruct | 8B | ~16GB | 英文场景 |
| mistralai/Mistral-7B-Instruct-v0.3 | 7B | ~16GB | 平衡选择 |
| NousResearch/Hermes-2-Pro-Llama-3-8B | 8B | ~16GB | 工具调用优化 |

### 模型选择建议

1. **中文场景**: 优先选择 Qwen 系列
2. **英文场景**: Llama 3.1 或 Mistral
3. **显存有限**: 7B-8B 模型
4. **追求性能**: 14B+ 模型或量化版本

## 高级配置

### 1. 性能优化

```bash
# 启用 GPU 加速
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --tensor-parallel-size 2 \  # 多 GPU 并行
    --gpu-memory-utilization 0.9 \  # GPU 显存利用率
    --max-model-len 4096 \  # 最大上下文长度
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

### 2. 量化模型（节省显存）

```bash
# 使用 4-bit 量化
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct-AWQ \
    --quantization awq \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

### 3. 批处理优化

```bash
# 增加批处理大小
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --max-num-batched-tokens 8192 \
    --max-num-seqs 256 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

### 4. 远程部署

如果 vLLM 服务部署在远程服务器:

```bash
# .env 配置
OPENAI_API_BASE=http://your-server-ip:8000/v1
```

## 故障排查

### 问题 1: 模型不支持 function calling

**错误信息**: `Tool calls are not supported for this model`

**解决方案**:
1. 使用支持 function calling 的模型（见推荐列表）
2. 确保启动时添加 `--enable-auto-tool-choice --tool-call-parser hermes`

### 问题 2: 显存不足

**错误信息**: `CUDA out of memory`

**解决方案**:
```bash
# 1. 使用量化模型
--quantization awq

# 2. 减少显存利用率
--gpu-memory-utilization 0.8

# 3. 减少上下文长度
--max-model-len 2048

# 4. 使用更小的模型
```

### 问题 3: 连接超时

**错误信息**: `Connection timeout`

**解决方案**:
```bash
# 1. 检查服务是否启动
curl http://localhost:8000/v1/models

# 2. 检查防火墙
sudo ufw allow 8000

# 3. 增加超时时间
# 在 config.py 中添加配置
```

### 问题 4: 工具调用格式错误

**症状**: Agent 无法正确调用工具

**解决方案**:
1. 尝试不同的 `--tool-call-parser`:
   - `hermes`
   - `mistral`
   - `llama3_json`
2. 检查模型是否真正支持 function calling
3. 查看 vLLM 日志了解详细错误

## 性能对比

| 后端 | 延迟 (首 token) | 吞吐量 | 成本 | 隐私 |
|------|----------------|--------|------|------|
| OpenAI API | ~200ms | 高 | 💰💰💰 | ⚠️ |
| vLLM (本地) | ~50ms | 很高 | 💰 (硬件) | ✅ |
| vLLM (远程) | ~100ms | 很高 | 💰💰 | ✅ |

## 生产部署建议

1. **使用负载均衡**: Nginx/HAProxy 分发请求到多个 vLLM 实例
2. **监控指标**: Prometheus + Grafana 监控 GPU 使用率、延迟等
3. **日志收集**: ELK/Loki 收集 vLLM 和 Agent 日志
4. **容器化**: Docker/K8s 部署，便于扩展
5. **备份方案**: 配置 OpenAI API 作为 fallback

## 示例：完整部署脚本

```bash
#!/bin/bash
# deploy_vllm.sh - 一键部署 vLLM Agent

set -e

echo "=== vLLM Agent 部署脚本 ==="

# 1. 检查 GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "错误: 未检测到 NVIDIA GPU"
    exit 1
fi

# 2. 安装 vLLM
pip install vllm -q

# 3. 下载模型（自动缓存到 ~/.cache/huggingface）
echo "下载模型..."
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct')"

# 4. 启动 vLLM 服务
echo "启动 vLLM 服务..."
nohup python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    > vllm.log 2>&1 &

VLLM_PID=$!
echo "vLLM 服务已启动 (PID: $VLLM_PID)"

# 5. 等待服务就绪
echo "等待服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/v1/models > /dev/null; then
        echo "✅ vLLM 服务就绪"
        break
    fi
    sleep 2
done

# 6. 配置 Agent
cat > .env << EOF
OPENAI_API_KEY=EMPTY
OPENAI_API_BASE=http://localhost:8000/v1
AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct
WEATHER_API_KEY=${WEATHER_API_KEY}
EOF

echo "✅ 部署完成！"
echo ""
echo "使用方法:"
echo "  python -m work_agent run '查询北京的天气'"
echo ""
echo "停止服务:"
echo "  kill $VLLM_PID"
```

## 参考资源

- [vLLM 官方文档](https://docs.vllm.ai/)
- [OpenAI 兼容 API](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
- [Function Calling 支持](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#tool-calling)
- [Qwen 模型](https://huggingface.co/Qwen)

## 常见问题

**Q: vLLM 和 OpenAI API 有什么区别？**

A: vLLM 是本地推理服务器，提供与 OpenAI 兼容的 API。优势是数据本地化、成本可控，劣势是需要自己维护硬件和服务。

**Q: 如何选择模型？**

A: 根据场景选择：
- 中文场景 → Qwen
- 英文场景 → Llama/Mistral
- 显存有限 → 7B 模型 + 量化
- 追求性能 → 14B+ 模型

**Q: 可以同时使用 OpenAI 和 vLLM 吗？**

A: 可以。通过修改 `OPENAI_API_BASE` 环境变量切换后端，或实现路由逻辑动态选择。

**Q: function calling 效果不好怎么办？**

A:
1. 确认模型真正支持 function calling
2. 尝试不同的 `--tool-call-parser`
3. 调整 prompt engineering
4. 使用专门优化过的模型（如 Hermes 系列）
