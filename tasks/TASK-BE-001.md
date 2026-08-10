# TASK-BE-001 FastAPI 后端工程骨架

## 任务类型
- implementation

## 会话开始上下文

基线：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5
任务：TASK-BE-001
目标：交付可启动、可测试、可静态检查的 FastAPI 模块化单体骨架及独立 Worker 入口。
非目标：业务接口、公开健康检查 API、数据库/迁移、Redis、鉴权、加密、通知、LLM、云资源。
允许修改：`apps/api/**`。
预计变更：不超过 18 个文件；生产代码不超过 350 行；测试代码不超过 180 行。
验收测试：本任务骨架 smoke 测试；TC-OPS-003 仅登记后续部署任务覆盖，本任务不新增未在 OpenAPI v0.1 中定义的健康检查接口。
输出语言：简体中文。

## 基线版本与基线 commit
- PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 / UI 1.0 / architecture 0.2 / security 0.1 / OpenAPI 0.1 / test_plan 0.1（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`511b02dd292d0b993bb2257de2109b6447d841cd`

## 精确规范引用
- `docs/adr/ADR-IMPL-001.md` §1、§2、§4、§5
- `docs/api/openapi.yaml`：仅用于确认本任务不得新增公开 operation/path
- `docs/test/test-plan.md`：TC-OPS-003（仅记录后续部署覆盖边界）

## 需求来源
- ADR-IMPL-001 的 Python 模块化单体、API/Worker 独立入口、精确依赖和工程门禁决策。

## 目标
- 在 `apps/api/` 建立 Python 3.12 FastAPI 工程骨架，包含应用工厂、环境配置加载、结构化日志基础、API 进程入口、Worker 进程入口和最小自动化测试。
- 锁定本任务直接依赖与传递依赖的精确版本，并提供可重复安装入口。

## 非目标
- 不实现 `auth`、`appointments`、`notifications`、`knowledge`、`ai`、`admin` 业务行为或空壳业务类。
- 不新增任何公开 HTTP/SSE path；尤其不新增 `/health/live`、`/health/ready`。TC-OPS-003 的健康检查契约留后续 OpenAPI/部署任务。
- 不连接 PostgreSQL、pgvector、Redis；不创建 Alembic migration。
- 不实现 BCrypt、Cookie/CSRF、AES/HMAC、RBAC、限频、SMTP/IMAP、飞书、DeepSeek/OpenAI 或云基础设施。

## 允许修改路径
- `apps/api/pyproject.toml`
- `apps/api/requirements.lock`
- `apps/api/README.md`
- `apps/api/app/**`
- `apps/api/tests/**`

## 禁止修改路径
- `docs/**`、`PROJECT_STATE.md`、`tasks/**`（除本任务交付证据）
- `apps/web/**`、根目录前端配置与锁文件
- `migrations/**`、`infra/**`、`.github/**`
- `C:\Users\hxt02\Desktop\sleep202603-an\**`

## 已批准的 DB / API / 依赖变更
- DB：无；禁止数据库连接、schema、migration、表、字段或索引变更。
- API/SSE：无；FastAPI 应用可以启动，但 `app.routes` 不得包含项目自定义公开 path。
- 运行时直接依赖：仅 FastAPI、Uvicorn、Pydantic；版本必须精确锁定，依据 accepted 的 ADR-IMPL-001。
- 测试/门禁直接依赖：仅 pytest、pytest-asyncio、HTTPX、Ruff、mypy；版本必须精确锁定，依据 accepted 的 ADR-IMPL-001。
- 允许上述包解析出的必要传递依赖进入 `requirements.lock`；禁止引入 SQLAlchemy、Alembic、psycopg、pgvector、redis、bcrypt、cryptography、OpenAI SDK、PyMuPDF、python-docx、pytesseract 或未列明包。
- 依赖安装仅限本地开发环境，不执行付费、云端或不可逆操作。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：仅建立已批准技术栈的工程骨架，不提供任何用户可观察业务行为或公开 API。

## 功能验收
- Python 3.12 环境可按锁文件重复安装。
- 应用工厂可创建 FastAPI 实例，应用 title/version 来自配置，且不注册项目自定义公开路由。
- 配置可从环境变量读取，默认值适合本地开发；未知敏感值不得写入日志。
- API 入口可完成启动 smoke；Worker 入口可启动、记录一次结构化启动日志并正常退出，不含轮询或外部副作用。

## 安全与隐私验收
- 仓库中无密钥、密码、Cookie、Token、用户 PII 或真实外部服务地址。
- 结构化日志不输出完整环境变量或配置对象；测试覆盖敏感字段不被序列化。
- 不实现或改变鉴权、加密、限频、通知及 Prompt/工具权限。

## 性能验收
- N/A：骨架不提供业务请求路径；应用工厂与 Worker smoke 应在普通本地环境快速完成，不设置新的产品性能承诺。

## 变更预算
- max_files：18
- expected_prod_lines：350
- expected_test_lines：180

## 必须运行的测试命令
- 使用锁文件在隔离环境安装依赖
- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy app`
- API 应用导入/启动 smoke
- Worker 入口执行 smoke

## 回滚方法
- `git revert` 本任务实现提交，或删除本任务新增的 `apps/api/`；无数据库和外部状态回滚。

## 强制停止条件
- 需要新增未在“已批准的 DB / API / 依赖变更”逐项列明的包、公开 API/SSE path、DB 结构或 migration。
- 需要实现鉴权、加密、限频、通知、LLM、云资源或业务模块。
- 锁文件不能由声明的直接依赖可重复生成，或冻结测试/门禁失败。
- 超出 `max_files` 或代码行数预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：公开健康检查契约与 TC-OPS-003 完整覆盖留后续 OpenAPI/部署任务。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open

## 关联
- 独立审查：TASK-REVIEW-BE-001
- 后续任务：数据库基础与 migration（须单独人审）；业务模块实现任务。

