# Harness 工程化（自动评测 + 留痕）

> 本文件是 **AI 接手入口**之一：任意接手者（Codex / 下一 AI / 未来的你）读完即可在本项目跑通自动评测、看懂测试库约定、知道坑记录在哪。
> 配套强制约束见 `AGENTS.md`；版本/状态唯一源见 `docs/baseline.yml`；任务态见 `PROJECT_STATE.md`。
> 本文件仅描述**工程基础设施**，不改任何业务行为。

---

## 1. 这是什么

把"人工手动跑 pytest/ruff/mypy/前端 + 手填日志"变成一套可重复、可追溯、不靠人肉的脚手架：

| 组件 | 文件 | 作用 |
|------|------|------|
| 一键验证 | `scripts/verify.sh` | 加载 env → 确保 `python-multipart` → 建/复用测试库 → alembic 升级 → pytest + ruff + mypy + 前端；硬门禁失败如实非零退出，存量问题仅上报 |
| 测试库准备 | `apps/api/scripts/harness_setup_db.py` | 幂等建 `jianli_test` + 迁移 + Redis 探活 |
| 集中 fixtures | `apps/api/tests/conftest.py` | `ensure_test_schema`(autouse) / `test_settings` / `app_client` |
| 提交钩子 | `scripts/git-hooks/pre-commit`·`pre-push` | commit→verify --quick；push→全量 verify |
| 钩子安装 | `scripts/install-hooks.sh` | 把 hook 源装进 `.git/hooks/`（源受版本控制，.git/hooks 不入库） |
| 开发日志 | `scripts/devlog.sh` | 自动聚合 git/TASK/坑，不手填 |
| 坑记录器 | `scripts/record_pit.py` | verify 失败时结构化追加到 `docs/devlog/pitfalls/` |

**设计决策（用户 2026-08-17 确认）**：测试库复用 `docker-compose.dev.yml` 起独立 `jianli_test`（方案 A，零新依赖）；不做 GitHub 远端、走本地 git hook；坑固化=半自动（机器记录、AI 提建议、用户拍板提炼 Skill）。

---

## 2. 前置条件（必读）

1. **必须在 WSL 中运行**。项目 venv `apps/api/.venv` 是 **Linux 结构**（在 WSL 创建），Windows Git Bash 下 `bin/python` 不可解析；且 `pyproject` 要求 `>=3.12,<3.13`，Windows 侧 managed(3.13.12)/system(3.11.9) 均不匹配。所有评测脚本面向 WSL bash 编写；非 WSL 环境 hook 会自动跳过（不阻塞提交）。
2. **docker-compose 服务常驻**：`docker compose -f docker-compose.dev.yml up -d`（PG16/pgvector `127.0.0.1:55432` + Redis7 `127.0.0.1:63790`）。**harness 不重建容器**，只连接复用。
3. **`apps/api/.env.local` 存在**（密钥仅运行时环境变量，gitignore）。脚本加载前会 `sed` 去 CRLF。

---

## 3. 怎么跑

```bash
# 全量（pytest + ruff + mypy + 前端 typecheck/test/build）
bash scripts/verify.sh

# 提交前（ruff + mypy + pytest，跳过前端，快）
bash scripts/verify.sh --quick

# 额外准备 jianli_tc_ops_002_db 并跑迁移验收测试
bash scripts/verify.sh --tc
```

退出码：0=硬门禁全过；非 0=有硬门禁失败（失败会在 `docs/devlog/pitfalls/` 留结构化记录）。

### 门禁语义（harness 工程核心：失败必须如实暴露，绝不静默通过）

- **硬门禁（失败 → 退出码非 0）**：测试库就绪、`pytest`、`ruff check`、`ruff format`（harness 自有文件）、`mypy`、`pnpm test`（前端单测）。
- **已知存量问题（仅上报、不阻断）**：`pnpm typecheck` / `pnpm build`。当前 `apps/web/main.tsx` 存在**预存语法错误**（`TS1005: '}' expected`，约 515–516 行），属历史债务、非 harness 缺陷，见下方「已知问题」。harness 如实上报，不假装通过，也不让它阻塞后端评测。
- `ruff format --check` 仅作用于 harness 自有文件（`scripts/record_pit.py`、`apps/api/tests/conftest.py`、`apps/api/scripts/harness_setup_db.py`），**不强制存量 `app/**` 代码**达到 ruff format 标准（那些文件属本任务禁止修改路径，且历史未格式化）。`ruff check` 跑全量（存量代码 ruff-clean）。
- 缺失的已声明依赖 `python-multipart` 会由 `verify.sh` 自检并安装到 venv（WSL venv 历史缺口），不阻塞。

---

## 4. 测试库约定（重要）

| 用途 | 数据库 | Redis |
|------|--------|-------|
| 开发（人用手动） | `jianli_dev`（db 0） | db 0 |
| **harness 自动评测** | `jianli_test`（db 15） | db 15 |
| 迁移验收 TC（仅 `--tc`） | `jianli_tc_ops_002_db` | — |

- `verify.sh` 把 `JIANLI_DATABASE_URL` 末段替换为 `jianli_test`、`JIANLI_REDIS_URL` 末段替换为 `/15`，复用同一 PG/Redis 实例，物理隔离。
- `harness_setup_db.py` 连维护库 `jianli_dev` 用 `CREATE DATABASE`（先查 `pg_database` 保证**幂等**），再 `alembic upgrade head`。
- **迁移验收测试**（`tests/migrations/*`）读独立变量 `JIANLI_TEST_DATABASE_URL` 且断言库名为 `jianli_tc_ops_002_db`；不设该变量时它们 `skip`。`--tc` 会准备该库并导出变量，使它们运行。
- `conftest.ensure_test_schema`（autouse, session）仅在 `JIANLI_DATABASE_URL` 含 `test` 时迁移，**绝不动** `jianli_dev` 或 `jianli_tc_ops_002_db`。
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
- `pre-commit` → `verify.sh --quick`；`pre-push` → 全量 `verify.sh`。
- **仅当本次改动 `apps/` 时才评测**，文档/README 提交不阻塞。
- 非 WSL 自动跳过（不阻塞 Windows 侧提交）。
- 应急跳过：`JIANLI_SKIP_HOOK=1 git commit ...`。
- hook 源在 `scripts/git-hooks/`（受版本控制）；`.git/hooks/` 不入库。

---

## 7. 留痕：开发日志 & 坑记录

```bash
bash scripts/devlog.sh           # 输出到 stdout
bash scripts/devlog.sh --save    # 同时写 docs/devlog/DEVLOG-YYYY-MM-DD.md
```
坑记录：verify 失败自动调 `scripts/record_pit.py` 追加到 `docs/devlog/pitfalls/`（`pitfalls.jsonl` 机器可读 + `pitfalls.md` 人读）。
**流程（半自动）**：机器如实记录现象/根因/修复/规避 → AI 复盘把值得的标记为 `skill_candidate` 并提议名称 → **用户拍板**是否提炼为 Skill（不全自动写 Skill）。

---

## 8. 已知运维坑（接手必看，详见 `docs/devlog/pitfalls/`）

- 项目 venv 为 WSL Linux 结构 → **评测只在 WSL 跑**（见 `jianli-wsl-verify`）。
- 本环境 Git Bash 的 `rm` 被 safe-delete 拦截 → **删文件走 `wsl rm -f`**（见 `windows-rm-via-wsl`）。
- `.env.local` 为 CRLF → 任何加载脚本先 `sed 's/\r$//'`（见 `source-env-strip-crlf`）。
- 缺失已声明依赖 `python-multipart` → `verify.sh` 自检并 `pip install`（WSL venv 历史缺口；缺它 pytest 在路由注册阶段报 `Form data requires "python-multipart"`），见 `python-multipart-missing-in-venv`。
- **前端 `apps/web/main.tsx` 预存语法错误**（`TS1005: '}' expected`，约 515–516 行）→ `pnpm build`/`typecheck` 恒红，属历史债务、非 harness 缺陷；`verify.sh` 仅上报不阻断，`pnpm test`(vitest) 仍正常。该问题独立于本 harness，需单独 TASK 修复。
