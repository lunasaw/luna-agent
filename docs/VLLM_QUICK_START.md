# vLLM Agent 快速开始

5 分钟内启动并测试 vLLM Agent。

## 步骤 1: 启动 vLLM 服务

### 选项 A: 使用脚本（推荐）

```bash
# 使用默认配置 (Qwen2.5-7B, 端口 8000)
./scripts/start_vllm.sh

# 或指定模型和端口
./scripts/start_vllm.sh "Qwen/Qwen2.5-7B-Instruct" 8000
```

### 选项 B: 手动启动

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

**等待服务启动**（首次运行会下载模型，需要几分钟）

验证服务:
```bash
curl http://localhost:8000/v1/models
```

## 步骤 2: 配置环境变量

```bash
# 方法 1: 修改 .env 文件
cat >> .env << EOF
OPENAI_API_KEY=EMPTY
OPENAI_API_BASE=http://localhost:8000/v1
AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct
WEATHER_API_KEY=6d27c25dd21584b70ea2ba700d64af7b
EOF

# 方法 2: 导出环境变量
export OPENAI_API_KEY=EMPTY
export OPENAI_API_BASE=http://localhost:8000/v1
export AGENT_MODEL=Qwen/Qwen2.5-7B-Instruct
export WEATHER_API_KEY=6d27c25dd21584b70ea2ba700d64af7b
```

## 步骤 3: 测试 Agent

### 使用测试脚本

```bash
# 在项目根目录执行
.venv/bin/python scripts/test_vllm_agent.py

# 或指定查询
.venv/bin/python scripts/test_vllm_agent.py --query "查询上海的天气"
```

### 使用 CLI

```bash
# 激活虚拟环境
source .venv/bin/activate

# 查看工具列表
python -m work_agent list-tools

# 单次查询
python -m work_agent run "查询北京的天气"

# 交互模式
python -m work_agent repl
```

## 预期输出

```
🔧 配置信息:
  API Base URL: http://localhost:8000/v1
  API Key: EMPTY

正在构建依赖容器...
✅ 成功加载 3 个工具

可用的工具:
  • shell_echo
  • get_current_time
  • get_city_weather

正在执行查询: 查询北京的天气
------------------------------------------------------------

============================================================
Agent 响应:
============================================================

🌤️ Beijing 天气情况:

温度: -0.06°C (体感: -3.44°C)
天气: 晴
湿度: 22%
气压: 1029 hPa
风速: 2.85 m/s

============================================================
```

## 常见问题

### Q1: 提示 "ModuleNotFoundError: No module named 'work_agent'"

**解决**: 确保在项目根目录 `/data/luna/luna-agent` 执行，并使用虚拟环境 Python:
```bash
cd /data/luna/luna-agent
.venv/bin/python scripts/test_vllm_agent.py
```

### Q2: 提示 "Connection refused"

**解决**: vLLM 服务未启动或地址错误
```bash
# 检查服务
curl http://localhost:8000/v1/models

# 检查进程
ps aux | grep vllm
```

### Q3: GPU 显存不足

**解决**: 使用量化模型或减少显存使用
```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --gpu-memory-utilization 0.7 \
    --max-model-len 2048
```

### Q4: 工具调用失败

**可能原因**:
1. 模型不支持 function calling
2. 未启用 `--enable-auto-tool-choice`
3. tool-call-parser 配置不正确

**解决**: 使用推荐的模型和配置（见启动命令）

## 下一步

- 📖 阅读 [完整 vLLM 集成指南](./VLLM_INTEGRATION.md)
- 🛠️ 开发自己的 [Agent Tools](./API_TO_TOOL_GUIDE.md)
- 🚀 了解 [生产部署](./VLLM_INTEGRATION.md#生产部署建议)

## 停止服务

```bash
# 如果是前台运行: Ctrl+C

# 如果是后台运行:
pkill -f vllm.entrypoints.openai.api_server
```
