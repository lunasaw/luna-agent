# Python 工程化项目规范规则文档

版本：v1.0
适用范围：Python 应用/服务项目（Web/任务/CLI），支持长期迭代、可测试、可部署、可观测。
术语说明：

* **MUST**：必须遵守（硬性约束）
* **SHOULD**：应当遵守（强烈建议，允许少量例外但需说明）
* **MAY**：可以采用（可选项）

---

## 1. 总体目标与原则

### 1.1 目标

1. **可维护性**：明确分层、依赖方向可控、避免隐式副作用。
2. **可测试性**：业务逻辑可脱离外部系统进行单元测试；集成测试边界清晰。
3. **可部署性**：启动流程可复现；配置、日志、生命周期可控。
4. **可扩展性**：外部依赖（DB/缓存/MQ/HTTP）可替换；功能模块可插拔。
5. **可观测性**：日志统一、错误可追踪，便于生产排障。

### 1.2 核心架构原则

* **单一职责**：每个模块只承担一种职责。
* **显式依赖**：依赖通过参数/构造注入或容器注入，禁止隐式全局获取。
* **最小副作用**：导入不做重初始化；业务层不触碰环境与 I/O。
* **依赖方向单向**：domain 不依赖 adapters/framework；组装在应用入口完成。
* **分层隔离**：I/O 与业务规则隔离；异常与日志策略统一。

---

## 2. 仓库结构与模块职责

### 2.1 目录结构（MUST）

项目必须使用 `src/` 布局：

```
project/
  pyproject.toml
  README.md
  src/
    myapp/
      __init__.py
      __main__.py        # 可选：python -m myapp
      app.py             # 应用组装入口：create_app/main
      config.py          # 配置模型与加载
      logging.py         # 日志配置
      container.py       # 依赖组装/容器（可选但推荐）
      domain/            # 领域模型与业务规则（纯）
      services/          # 应用服务/用例编排
      adapters/          # 外部系统适配：DB/HTTP/MQ/Cache
      api/               # Web API 层（如 FastAPI/Flask）
      tasks/             # 异步任务/定时任务
      utils/             # 通用工具（严格准入，见 2.4）
  tests/
    unit/
    integration/
  scripts/
```

### 2.2 分层职责（MUST）

* **domain/**：纯业务规则、实体、值对象、领域服务、领域异常。

  * 禁止访问：环境变量、文件系统、网络、数据库、缓存、消息队列、框架对象。
* **services/**：用例编排与事务边界。

  * 可以依赖：domain 抽象与接口、adapters 的接口（通过注入）。
* **adapters/**：外部依赖实现（DB/Redis/HTTP/MQ）。

  * 禁止：直接耦合上层业务规则实现细节（应通过接口/协议对接）。
* **api/**：Web 路由与请求/响应映射、认证鉴权、输入校验、错误映射。
* **tasks/**：异步/定时任务入口，调用 services 用例。
* **app.py / container.py**：**唯一允许**完成“依赖组装”的位置（见第 3、6 章）。

### 2.3 包边界与导入规则（MUST）

* 禁止跨层“反向依赖”：

  * domain 不得 import services/adapters/api/tasks
  * services 不得 import api
  * adapters 不得 import api
* 允许依赖方向：

  * api/tasks → services → domain
  * adapters → domain（只允许依赖 domain 的接口/协议与模型）
  * app/container → 任何层（仅用于组装）

### 2.4 utils 准入规则（MUST）

`utils/` 仅允许放置：

* 与具体业务无关且被多个模块复用的纯函数/工具类；
* 不得引入框架对象；不得包含 I/O；不得变成“杂物间”。
  任何新工具函数加入 utils，必须满足：
* 至少被两个不同模块复用；
* 有单元测试；
* 有清晰命名与文档字符串。

---

## 3. 初始化与启动流程规范

### 3.1 `__init__.py` 限制（MUST）

`__init__.py` **只能**包含：

* `__version__` 等元数据；
* 轻量导出符号（不会触发副作用）。

`__init__.py` **禁止**：

* 读取环境变量；
* 初始化日志；
* 建立 DB/Redis/HTTP/MQ 连接或客户端；
* 创建线程池/进程池；
* 注册全局钩子或启动后台任务。

### 3.2 启动入口（MUST）

所有“应用启动逻辑”必须存在于以下之一：

* `app.py` 的 `create_app()` / `main()`
* `__main__.py`（可选）
* CLI 场景可在 `myapp/cli.py`，但必须调用 `app/container` 完成组装

### 3.3 启动顺序（SHOULD）

推荐顺序：

1. 加载配置（config）
2. 配置日志（logging）
3. 构建容器/依赖（container）
4. 注册路由/任务（api/tasks）
5. 启动生命周期（startup/shutdown hooks）

---

## 4. 全局变量与状态管理规范

### 4.1 全局变量定义（MUST）

* **允许**全局常量：不可变值、枚举、固定映射、正则、schema 定义等。
* **禁止**模块级可变状态与外部资源对象，例如：

  * DB session/engine、Redis client、HTTP session、MQ producer/consumer
  * 全局缓存 dict（除非明确为只读常量映射）

### 4.2 单例策略（SHOULD）

对“昂贵且可复用”的外部资源，允许使用“受控单例”，但必须满足：

1. 单例实例仅在 **container/app 初始化阶段**创建；
2. 通过依赖注入传递给使用方，禁止被业务模块通过 import 直接获取；
3. 必须提供关闭/清理方法，并由生命周期统一管理（见第 7 章）。

### 4.3 上下文状态（MUST）

* Request-scoped / Job-scoped 状态必须显式传递（参数或上下文对象），不得依赖隐式全局变量。
* 如使用 contextvars/thread-local，必须在架构文档中明确其生命周期、并发模型与清理策略，并配套测试。

---

## 5. 配置管理规范（config.py）

### 5.1 配置集中管理（MUST）

* 项目必须有 `config.py`，并提供**唯一**入口加载配置，例如 `load_config()`。
* 所有模块不得自行读取环境变量；环境变量读取必须集中在 `config.py`。

### 5.2 类型化配置（MUST）

* 配置必须具备明确字段、默认值、类型约束（可通过 dataclass/pydantic 等实现）。
* 配置对象在运行时应视为只读（immutability 优先）。

### 5.3 配置分层覆盖（SHOULD）

配置来源优先级建议（从低到高）：

1. 代码默认值
2. 配置文件（可选）
3. 环境变量
4. 启动参数（可选）

### 5.4 敏感信息（MUST）

* 密钥/凭证不得写入代码库与默认配置文件。
* 日志中不得输出明文敏感信息（token、password、secret、private key）。
* 必须支持通过环境变量注入敏感配置。

---

## 6. 依赖注入与引用传递规范（DI）

### 6.1 依赖传递方式（MUST）

业务代码（domain/services）必须通过以下方式获取依赖：

* 构造函数注入（优先）
* 方法参数注入
* 容器注入（container 提供对象装配）

禁止：

* 在业务层通过 import 引用某个全局 client 或“单例 getter”。

### 6.2 接口与实现隔离（SHOULD）

* domain/services 面向抽象（协议/接口）编程；
* adapters 提供具体实现；
* app/container 负责将实现绑定到抽象并注入。

### 6.3 注入边界（MUST）

* domain 不允许依赖 adapters 的具体实现类；
* services 可以依赖 domain 定义的接口类型；
* adapters 可以实现 domain 定义的接口类型，但不得反向耦合 services/api。

---

## 7. 生命周期与资源管理规范

### 7.1 资源生命周期（MUST）

对以下资源必须提供明确的创建与销毁：

* DB 连接池/会话工厂
* HTTP client/session
* Redis client
* MQ producer/consumer
* 线程池/进程池

### 7.2 统一关闭策略（MUST）

* 资源必须由 app/container 创建；
* 必须在 shutdown 阶段统一 close/shutdown；
* 禁止依赖解释器退出自动回收作为释放策略。

### 7.3 并发与安全（SHOULD）

* 多线程/多协程场景下，资源对象必须明确是否线程安全/协程安全；
* 若不安全，必须采用每请求/每任务实例化或使用池化策略；
* 必须在文档中明确并发模型（sync/async、多进程/多线程）。

---

## 8. 日志规范（logging.py）

### 8.1 统一日志入口（MUST）

* 项目必须提供 `logging.py`，并由启动入口调用一次进行全局配置。
* 禁止在业务代码中重复配置 logging handler/formatter。

### 8.2 日志内容要求（MUST）

* 所有日志必须包含：时间、级别、模块、消息；
* 对请求/任务必须包含关联标识（request_id / job_id / trace_id 至少一个）。
* 错误日志必须包含异常堆栈（exc_info）。

### 8.3 禁止行为（MUST）

* 禁止使用 `print()` 作为正式日志输出（开发临时允许，但不得合入主分支）。
* 禁止记录敏感字段（见 5.4）。

---

## 9. 异常与错误处理规范

### 9.1 异常分层（MUST）

* domain 层：抛出领域异常（表达业务规则失败）。
* adapters 层：捕获外部库异常并转换为适配器异常或统一错误类型。
* api/cli 层：将异常映射为 HTTP 响应/退出码，并输出统一错误格式。

### 9.2 禁止吞异常（MUST）

* 禁止 `except Exception: pass`。
* 任何捕获必须：

  * 记录必要信息（至少 debug 或 error，视场景），并
  * 重新抛出或返回明确的错误对象/结果。

### 9.3 错误码与可观测性（SHOULD）

* 对外接口（API/CLI）应提供稳定的错误码/错误类型；
* 错误响应应包含可追踪 ID（request_id/trace_id）。

---

## 10. API 层与输入输出边界（如有 Web）

### 10.1 责任边界（MUST）

API 层只做：

* 路由与协议适配（HTTP ↔ DTO）
* 鉴权/权限校验（可委托中间件）
* 输入校验与转换
* 调用 services 用例
* 异常映射与响应格式化

禁止：

* 在 API 层直接写业务规则；
* 在 API 层直接调用 adapters（必须经 services）。

### 10.2 DTO 与领域模型隔离（SHOULD）

* 请求/响应 DTO 与 domain 模型应解耦，避免 API 变更污染 domain。

---

## 11. 数据访问与外部系统适配（adapters）

### 11.1 Repository/Client 规范（MUST）

* 数据库访问必须封装在 repository/dao 类中，不得散落 SQL/ORM 调用。
* HTTP/MQ/Redis 必须有独立 client 封装统一超时、重试、熔断（如需要）。

### 11.2 超时与重试（MUST）

* 所有外部网络调用必须配置超时。
* 重试策略如启用，必须具备：

  * 最大重试次数
  * 指数退避或固定间隔
  * 不重试的错误类别（如 4xx 等）

---

## 12. 测试规范（tests/）

### 12.1 测试分层（MUST）

* `tests/unit/`：只测 domain/services，禁止真实外部依赖。
* `tests/integration/`：允许连接真实 DB/Redis 等，必须可开关（环境变量/标记）。

### 12.2 覆盖要求（SHOULD）

* domain 的关键规则与边界条件必须覆盖；
* services 的核心用例必须覆盖；
* adapters 的关键行为至少有集成测试或契约测试。

### 12.3 可重复性（MUST）

* 测试必须可重复运行，不依赖执行顺序；
* 不得依赖外部不稳定服务（除非明确是端到端测试并可跳过）。

---

## 13. 代码质量与风格规范

### 13.1 类型标注（SHOULD）

* services/domain 的公共函数与类方法应提供类型标注；
* 对外接口（API DTO、服务接口）必须类型明确。

### 13.2 命名与结构（MUST）

* 模块/包：小写下划线；
* 类：PascalCase；
* 函数/变量：snake_case；
* 常量：UPPER_SNAKE_CASE；
* 不允许无意义命名（data1、temp、foo）进入主分支。

### 13.3 函数复杂度（SHOULD）

* 单函数过长（>80 行）或圈复杂度过高必须拆分；
* services 用例应清晰表达业务流程，不混杂低层 I/O 细节。

### 13.4 文档字符串与注释（SHOULD）

* 对外暴露接口必须有 docstring；
* 复杂业务规则必须解释“为什么”，而非重复代码“做什么”。

---

## 14. 安全与合规基线

### 14.1 密钥管理（MUST）

* 任何密钥不得提交到仓库；
* 必须提供本地开发的安全注入方式（环境变量或本地忽略文件）。

### 14.2 日志与隐私（MUST）

* 禁止记录敏感信息；
* 如需记录用户标识，应脱敏或使用内部 ID。

### 14.3 依赖安全（SHOULD）

* 依赖版本必须锁定/可复现（pyproject + lock 方案）；
* 定期扫描高危依赖（在 CI 中执行为佳）。

---

## 15. 交付与运维约束（CI/CD 基线）

### 15.1 必须具备的自动化检查（MUST）

主分支合并前必须通过：

* 单元测试
* 静态检查（lint/format/type check 至少其中两类）
* 基础安全检查（至少依赖漏洞扫描或 secret scan 之一）

### 15.2 版本与变更（SHOULD）

* 对外接口变更必须记录在 CHANGELOG 或 release notes；
* 语义化版本（SemVer）建议采用。

---

## 16. 例外处理机制（MUST）

任何违反 MUST 规则的情况，必须满足：

1. 在 PR/变更说明中明确记录；
2. 提供替代方案或风险评估；
3. 设定回滚或补救计划；
4. 由技术负责人审批。

---

## 17. 启动检查清单（可直接用于项目初始化验收）

### 17.1 结构与边界

* [ ] 使用 src/ 布局
* [ ] domain/services/adapters/api/tasks 分层齐全且边界清晰
* [ ] 无反向依赖导入

### 17.2 初始化与全局变量

* [ ] `__init__.py` 无副作用
* [ ] 无模块级外部资源对象全局变量
* [ ] 依赖在 app/container 组装

### 17.3 配置与日志

* [ ] config.py 集中加载配置
* [ ] logging.py 统一配置日志
* [ ] 敏感字段不进入日志

### 17.4 生命周期

* [ ] 外部资源可关闭，shutdown 统一释放
* [ ] 并发模型与资源安全性明确

### 17.5 测试

* [ ] unit/integration 分层
* [ ] domain/services 有核心覆盖
* [ ] 集成测试可开关、可重复

---

## 18. 本规范的最低强制结论（摘要）

1. 初始化必须集中在 app/container，导入无副作用。
2. 禁止模块级全局可变状态与外部资源对象。
3. 所有依赖必须显式注入，业务层不读环境、不做 I/O。
4. 配置集中、日志统一、异常分层、资源可关闭。
5. 测试分层明确，domain/services 可在无外部依赖下稳定测试。
