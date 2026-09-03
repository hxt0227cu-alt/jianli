# Harness 工程化（自动评测 + 留痕）

> 本文件是 **AI 接手入口**之一：任意接手者（Codex / 下一 AI / 未来的你）读完即可在本项目跑通自动评测、看懂测试库约定、知道坑记录在哪。
> 配套强制约束见 `AGENTS.md`；版本/状态唯一源见 `docs/baseline.yml`；任务态见 `PROJECT_STATE.md`。
> 本文件仅描述**工程基础设施**，不改任何业务行为。

---

## 1. 这是什么

把"人工手动跑 pytest/ruff/mypy/前端 + 手填日志"变成一套可重复、可追溯、不靠人肉的脚手架：

| 组件 | 文件 | 作用 |
|------|------|------|
| 一键验证 | `scripts/verify.sh` | 加载并清洗本地 env → 建/复用隔离测试库 → alembic 升级 → pytest + ruff + mypy + 前端 build + Playwright；任何硬门禁失败均非零退出 |
| 测试库准备 | `apps/api/scripts/harness_setup_db.py` | 幂等建 `jianli_test` + 迁移 + Redis 探活 |
| 集中 fixtures | `apps/api/tests/conftest.py` | `ensure_test_schema`(autouse) / `test_settings` / `app_client` |
| 提交钩子 | `scripts/git-hooks/pre-commit`·`pre-push` | commit→`verify --quick`；push→`prepush.sh`（评测报告 + `verify --tc` + whitespace gate） |
| 钩子安装 | `scripts/install-hooks.sh` | 把 hook 源装进 `.git/hooks/`（源受版本控制，.git/hooks 不入库） |
| 开发日志 | `scripts/devlog.sh` | 自动聚合 git/TASK/坑，不手填 |
| 坑记录器 | `scripts/record_pit.py` | 仅在明确复盘任务中人工写入 `docs/devlog/pitfalls/`；verify 失败只写已忽略的 `_diag_verify.log` |

`validate_eval_report.py` 不只检查 JSON 结构：报告/套件 commit 必须可解析并保持祖先关系，且报告验证 commit 之后不得出现 API、Web、测试或门禁相关变更。报告自身可在验证提交之后单独更新，避免自引用；当前候选一旦变化，旧 `79/79` 会明确标为 historical 并阻断 pre-push。

**设计决策**：测试库复用 `docker-compose.dev.yml` 起隔离数据库（方案 A，零新依赖）；本地 git hook 与 GitHub Actions 共同执行门禁；坑固化=半自动（机器记录、AI 提建议、用户拍板提炼 Skill）。

---

## 2. 前置条件（必读）

1. **必须在 WSL 中运行**。项目 venv `apps/api/.venv` 是 **Linux 结构**（在 WSL 创建），Windows Git Bash 下 `bin/python` 不可解析；且 `pyproject` 要求 `>=3.12,<3.13`，Windows 侧 managed(3.13.12)/system(3.11.9) 均不匹配。所有评测脚本面向 WSL bash 编写；直接在非 WSL 运行 `verify.sh` 会非零失败，git hook 自身则会明确提示并跳过（不阻塞 Windows 侧提交）。
2. **docker-compose 服务可用**：`docker compose -f docker-compose.dev.yml up -d --pull never --wait --wait-timeout 60 postgres redis`（PG16/pgvector `127.0.0.1:55432` + Redis7 `127.0.0.1:63790`）。`prepush.sh` 会启动并等待已有缓存镜像健康，`verify.sh` 本身只连接复用，均不会隐式联网拉取。
3. **`apps/api/.env.local` 存在**（密钥仅运行时环境变量，gitignore）。脚本加载前会 `sed` 去 CRLF。

---

## 3. 怎么跑

```bash
# 全量（pytest + ruff + mypy + 前端 test/typecheck/build + Playwright）
bash scripts/verify.sh

# 提交前离线开发预检（跳过真实 RAG、前端与 Playwright，不是发布证据）
bash scripts/verify.sh --quick

# 完整发布门禁：真实 RAG + 三套迁移 + 前端 + Playwright
bash scripts/verify.sh --tc

# 只跑后端发布门禁（仍强制真实 RAG 与三套迁移，跳过前端）
bash scripts/verify.sh --tc --quick

# 在 quick 开发预检中显式加入真实语义 Provider
bash scripts/verify.sh --quick --external-rag
```

退出码：0=对应门禁通过；非 0=失败。机器原始失败摘要只追加到已忽略的 `_diag_verify.log`，不会因运行测试而修改受版本控制文档；需沉淀为 pitfalls 时另开治理任务。

### 门禁语义（harness 工程核心：失败必须如实暴露，绝不静默通过）

- **硬门禁（失败 → 退出码非 0）**：测试库就绪、`pytest`、三套迁移 TC（启用 `--tc` 时）、`ruff check`、`ruff format`（harness 自有文件）、`mypy`、`pnpm test`、`pnpm typecheck`、`pnpm build`、Playwright Chromium E2E。
- 默认全量或任意 `--tc` 入口都会先执行版本化评测报告新鲜度校验；旧报告不能只靠绕过 `prepush.sh` 获得“发布通过”。
- 单独 `--quick` 是离线开发预检：明确跳过真实 RAG、前端和 Playwright，退出成功也不得表述为发布通过。与 `--tc` 组合时仍强制执行真实 RAG 与迁移 TC。
- `ruff format --check` 仅作用于 harness 自有 Python 文件（`scripts/record_pit.py`、`apps/api/tests/conftest.py`、`apps/api/scripts/harness_setup_db.py`），**不强制存量 `app/**` 代码**达到 ruff format 标准（那些文件属本任务禁止修改路径，且历史未格式化）。`ruff check` 跑全量（存量代码 ruff-clean）。
- 缺失已声明依赖时立即失败；门禁不会联网自愈或悄悄修改 venv。
- `.env.local` 即使含真实 SMTP、Chat LLM 或飞书凭据，门禁也会先清洗并强制 `environment=test`、`email_mode=console`；这些外部通道只能走显式人工 smoke。
- 完整/`--tc` 发布门禁保留真实 Embedding 配置并强制执行四项 BGE-M3 冻结测试；缺配置、网络或额度异常直接失败且不重试。只有单独 `--quick` 的开发预检会明确 deselect，并打印“不可作为发布证据”。GitHub `rag-integration` 同样缺 Secret 即失败。

---

## 4. 测试库约定（重要）

| 用途 | 数据库 | Redis |
|------|--------|-------|
| 开发（人用手动） | `jianli_dev`（db 0） | db 0 |
| **harness 自动评测** | `jianli_test`（db 15） | db 15 |
| 认证冻结验收 | `jianli_auth_001_db` | db 15 |
| 迁移验收 TC（仅 `--tc`） | `jianli_tc_ops_002_db` / `jianli_tc_aiqa_001_db` / `jianli_tc_feishu_001_db` | — |

- `verify.sh` 把 `JIANLI_DATABASE_URL` 末段替换为 `jianli_test`、`JIANLI_REDIS_URL` 末段替换为 `/15`，复用同一 PG/Redis 实例，物理隔离。
- `harness_setup_db.py` 连维护库 `jianli_dev` 用 `CREATE DATABASE`（先查 `pg_database` 保证**幂等**），再 `alembic upgrade head`。
- **迁移验收测试**（`tests/migrations/*`）按模块分进程读取 `JIANLI_TEST_DATABASE_URL`，并分别断言 ops / aiqa / feishu 专用库名；常规 pytest 明确忽略迁移目录，`--tc` 再逐组执行，避免把“环境不匹配 skip”误报为通过。
- `conftest.ensure_test_schema`（autouse, session）只接受 loopback 上精确的 `jianli_test`（本地 55432；CI 才允许 5432）；同名远端目标 fail closed，且**绝不动** `jianli_dev` 或专用 migration TC 库。真正执行建库的 `harness_setup_db.py` 还会二次校验五个隔离库 allowlist 与 Redis db15。
- **保留真实依赖验证**：集成测试仍跑在真实 PG(pgvector)+Redis 上，不降级为 mock（符合 AGENTS.md 冻结 TC 精神）。

---

## 5. 集中 fixtures（`apps/api/tests/conftest.py`）

- `ensure_test_schema`（autouse, session）：幂等迁移测试库。
- `test_settings`（session）：`Settings.from_env()`（env 已是测试库）。
- `app_client`：`TestClient(create_app(test_settings))`，全挂载（auth+booking+admin+AI QA），真实 PG/Redis。**新集成测试优先用它**。
- 既有测试若自行定义 `client`/`app`/engine fixture，pytest 取最局部定义，**不受影响**。

新增测试示例：
```python
def test_something(app_client):
    resp = app_client.get("/pages/resume")
    assert resp.status_code == 200
```

---

## 6. git hook（本地自动评测）

```bash
bash scripts/install-hooks.sh   # 装 pre-commit / pre-push 到 .git/hooks/
```
- `pre-commit` → `verify.sh --quick`；`pre-push` → `prepush.sh`（启动缓存 PG/Redis、验证评测报告、运行 `verify.sh --tc` 与 whitespace gate）。
- 产品、测试、部署、CI、Compose、依赖清单及敏感忽略规则发生变化时触发；纯说明文档提交不阻塞。
- 非 WSL 时由 hook 明确提示并跳过（不阻塞 Windows 侧提交）；直接调用 `verify.sh` 仍会 fail closed，不能把错误平台当作门禁通过。
- 应急跳过：`JIANLI_SKIP_HOOK=1 git commit ...`。
- hook 源在 `scripts/git-hooks/`（受版本控制）；`.git/hooks/` 不入库。

---

## 7. 留痕：开发日志 & 坑记录

```bash
bash scripts/devlog.sh           # 输出到 stdout
bash scripts/devlog.sh --save    # 同时写 docs/devlog/DEVLOG-YYYY-MM-DD.md
```
失败原始摘要：verify 只写已忽略的 `_diag_verify.log`。需要沉淀复盘时，再由明确治理任务调用 `scripts/record_pit.py` 更新 `docs/devlog/pitfalls/`，避免测试执行越权改仓库。
**流程（半自动）**：机器如实记录现象/根因/修复/规避 → AI 复盘把值得的标记为 `skill_candidate` 并提议名称 → **用户拍板**是否提炼为 Skill（不全自动写 Skill）。

---

## 8. 已知运维坑（接手必看，详见 `docs/devlog/pitfalls/`）

- 项目 venv 为 WSL Linux 结构 → **评测只在 WSL 跑**（见 `jianli-wsl-verify`）。
- 本环境 Git Bash 的 `rm` 被 safe-delete 拦截 → **删文件走 `wsl rm -f`**（见 `windows-rm-via-wsl`）。
- `.env.local` 为 CRLF → 任何加载脚本先 `sed 's/\r$//'`（见 `source-env-strip-crlf`）。
- 缺失或版本不匹配的直接依赖 → 门禁按 `pyproject.toml` 精确 pin 逐项失败，并额外执行 `pip check`；要求重建 venv，绝不在验收过程中联网安装。当前本地复用 venv 与 CI 的 fresh install 只能称“命令集合对齐”，不能称运行环境完全同构。
- **前端 `apps/web/main.tsx` 预存语法错误（已解决）**：原 `TS1005: '}' expected'`（约 515–516 行）实为 504/505 两行超长单行 JSX（616/1057 字符）触发的 tsc 行长解析上限，代码本身合法（esbuild 可解析）。TASK-QA-CLEANUP-001 已将其拆分为多行 JSX，`pnpm typecheck` / `tsc --noEmit` 现均 0 错误；`pnpm build` 与 `pnpm test`(vitest v4 内部依赖 rolldown) 同源——二者仅在 WSL（rolldown 原生二进制 `@rolldown/binding-*` 齐备）下正常，本机原生 Git Bash 因缺失该原生二进制无法启动（vitest 报 `Cannot find native binding @rolldown/binding-wasm32-wasi`）。均属环境依赖问题，非代码缺陷；harness 目标运行环境为 WSL。
- Playwright Chromium 不存在时不会自动下载；联网窗口中一次性执行 `pnpm exec playwright install --with-deps chromium`，随后重跑 `pnpm exec playwright test` 或完整 `prepush.sh`。
