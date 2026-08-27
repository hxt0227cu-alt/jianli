# TASK-CI-PUSH-READINESS-001 GitHub Actions 容量友好型发布门禁

> **状态：Implemented / Awaiting GitHub repository target（2026-08-27，verified_commit=`ae612a6`）**

## 任务类型
- ci
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / test-plan 1.2
- 基线 commit：`e5263f8`

## 精确规范引用
- `docs/requirements/SRS.md §3.2` CI 门禁
- `docs/test/test-plan.md TC-AI-011/013/014、TC-OPS-010`
- `.github/workflows/agent-quality-gate.yml`

## 目标
- 将三个 GitHub-hosted job 串联为最多一个并发 runner，避免账户容量受限时一次 push 同时申请三个 runner，同时保留冻结检查名。
- 提供与远端步骤同构、绝不执行 push 的本地预检入口。

## 非目标
- 不执行 push；不改变产品行为、DB/API/依赖/Prompt/工具/权限。

## 允许修改路径
- `tasks/TASK-CI-PUSH-READINESS-001.md`
- `.github/workflows/agent-quality-gate.yml`
- `scripts/prepush.sh`
- `PROJECT_STATE.md`

## 禁止修改路径
- 应用代码、测试断言、依赖锁、迁移、产品规范。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false；仅执行拓扑与本地验证入口改变，门禁覆盖不降低。

## 功能、安全与性能验收
- 单次 workflow run 保留三个冻结检查名，但通过 `needs` 严格串行，任意时刻至多一个 runner；`timeout-minutes` 防止失控执行。
- 保留 PostgreSQL/Redis 真栈、迁移、Agent/Trace/Cache/Breaker、RAG、Ruff/Mypy、评测报告和 Web test/typecheck/build。
- 本地脚本不包含 `git push`、GitHub token、生产密钥或外部写操作。

## 变更预算
- max_files：4
- expected_prod_lines：180
- expected_test_lines：40

## 必须运行的测试命令
- `bash -n scripts/prepush.sh`
- YAML 解析检查
- `bash scripts/prepush.sh`
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`。

## 交付证据
- commit / PR：实现 `ae612a6`；本证据回填见后续提交；未 push
- 修改文件清单：4 个（workflow、prepush 脚本、任务单、PROJECT_STATE）
- 测试命令及结果：`bash scripts/prepush.sh` → pass；Agent/Trace/Resilience 40 passed；真实 PG/Redis RAG 4 passed / 1 expected xfail；Web 1 passed + typecheck/build pass；评测报告 79/79
- lint / typecheck：Ruff pass；Mypy 52 source files / 0 errors；TypeScript pass
- DB 迁移验证：隔离测试库 `alembic upgrade head` pass，无新迁移
- 验收证据：YAML 解析确认 `backend-agent → rag-integration → web-delivery`；三个 job 通过 `needs` 严格串行，timeout 20/20/15 分钟；脚本最终输出 `pre-push quality gate passed; no push was performed`
- 变更预算实际值：4 files，143 insertions / 1 deletion
- 未解决风险：本地 Git 无 remote；GitHub 账号已登录，但现有仓库仅 `sleep` 与 `RAG-graduation`，无可无歧义匹配的 jianli 仓库。需用户指定现有 URL 或决定创建仓库的名称/可见性后才能配置 remote
- 是否偏离 TASK：否
- spec_sync：clean
- verified_commit：`ae612a6`
