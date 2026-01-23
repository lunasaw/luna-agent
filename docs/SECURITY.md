# 安全最佳实践

## API Key 安全管理

### ⚠️ 永远不要做的事

1. **不要在代码中硬编码 API key**
   ```python
   # ❌ 错误示例
   api_key = "sk-1234567890abcdef"
   openai_api_key = "sk-proj-xxx"
   ```

2. **不要提交 API key 到 git**
   - 即使在私有仓库中也不要提交
   - 历史记录会永久保留
   - 一旦推送就很难完全删除

3. **不要在日志中打印 API key**
   ```python
   # ❌ 错误示例
   logger.info(f"Using API key: {api_key}")
   ```

### ✅ 推荐的做法

#### 1. 使用环境变量

```python
import os

# ✅ 正确示例
api_key = os.getenv("OPENAI_API_KEY")
weather_key = os.getenv("WEATHER_API_KEY")
```

```bash
# 在命令行设置
export OPENAI_API_KEY=your_key_here

# 或在 .env 文件中（确保 .env 在 .gitignore 中）
echo "OPENAI_API_KEY=your_key_here" >> .env
```

#### 2. 使用配置文件（不提交到 git）

```python
# config.py
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    openai_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",  # 从 .env 读取
        env_file_encoding="utf-8",
    )
```

```.gitignore
# 确保 .gitignore 包含
.env
.env.local
*.key
secrets/
```

#### 3. 使用密钥管理服务

生产环境推荐：
- AWS Secrets Manager
- Azure Key Vault
- Google Cloud Secret Manager
- HashiCorp Vault

#### 4. 日志安全

```python
# ✅ 脱敏后的日志
def mask_api_key(key: str) -> str:
    if len(key) > 8:
        return f"{key[:4]}...{key[-4:]}"
    return "***"

logger.info(f"Using API key: {mask_api_key(api_key)}")
# 输出: Using API key: sk-1...ef45
```

## 如果 API Key 已经泄漏

### 立即行动清单

1. **撤销（Revoke）泄漏的 key**
   - 立即前往 API 提供商控制台
   - 删除或禁用泄漏的 key
   - 生成新的 key

2. **从 git 历史中移除（如果已提交）**

   ```bash
   # 方法 1: 使用 git-filter-repo（推荐）
   pip install git-filter-repo
   git-filter-repo --path path/to/file --invert-paths

   # 方法 2: 修改最近的提交
   git commit --amend  # 修改文件
   git push --force-with-lease

   # 方法 3: 使用 BFG Repo-Cleaner
   brew install bfg  # macOS
   bfg --replace-text passwords.txt repo.git
   ```

3. **强制推送覆盖远程历史**
   ```bash
   git push --force-with-lease
   ```

   ⚠️ **警告**: 这会修改 git 历史，需要通知协作者

4. **通知相关人员**
   - 告知团队成员
   - 更新部署环境的配置

5. **审查访问日志**
   - 检查是否有异常 API 调用
   - 查看账单是否有异常

## 项目中的安全实践

### 配置文件示例

**`.env.example`** (可以提交):
```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here
WEATHER_API_KEY=your-weather-key-here
```

**`.env`** (不提交，包含真实值):
```bash
OPENAI_API_KEY=sk-proj-real-key-xxxxx
WEATHER_API_KEY=real-weather-key-yyyy
```

**`.gitignore`**:
```
.env
.env.local
.env.*.local
*.key
secrets/
credentials.json
```

### 代码审查检查点

在 PR 审查时检查：
- [ ] 没有硬编码的 API key
- [ ] 敏感配置使用环境变量
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 日志中的敏感信息已脱敏
- [ ] 测试代码中使用 mock 而非真实 key

### Pre-commit Hook

安装 pre-commit 检查：

```bash
# 安装 pre-commit
pip install pre-commit

# 添加到 .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

# 安装 hooks
pre-commit install
```

## 本项目的安全配置

### 已保护的文件

- `.env` - 包含在 `.gitignore`
- `.env.local` - 包含在 `.gitignore`
- `.claude/settings.local.json` - 包含在 `.gitignore`

### 环境变量清单

必需的环境变量：
```bash
# OpenAI/vLLM
OPENAI_API_KEY=xxx
OPENAI_API_BASE=xxx  # 可选

# Weather API
WEATHER_API_KEY=xxx

# 测试用
TEST_API_KEY=xxx
TEST_API_URL=xxx
```

### 安全测试

使用验证脚本测试 API 时：

```bash
# ✅ 正确 - 使用环境变量
export TEST_API_KEY=your_key
.venv/bin/python tests/unit/verify_api_agent_support.py

# ❌ 错误 - 不要在脚本中硬编码
```

## 参考资源

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [git-filter-repo 文档](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [OWASP 敏感数据泄露](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)

## 紧急联系方式

如果发现安全问题：
1. 立即撤销泄漏的凭证
2. 在 GitHub 创建 Security Advisory
3. 联系项目维护者

---

**记住**: 安全是持续的过程，而不是一次性的任务。始终保持警惕！
