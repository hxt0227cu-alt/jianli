# TASK-RELEASE-GATES-002 上线前本地与 CI 门禁收口

> 状态：In Progress（2026-08-31）。用户在上线前全量测试后明确要求修复门禁阻塞；真实栈环境隔离与扩展覆盖因预算拆至 `TASK-RELEASE-GATE-ISOLATION-003`。

## 任务类型
- implementation / test（测试基础设施与 CI 缺陷修复，不改变产品契约）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/test/test-plan.md` §1、TC-OPS-002、TC-OPS-003、TC-SEC-007
- `.github/workflows/agent-quality-gate.yml`
- 冻结复现：全量 pytest 中 `tests/auth/test_email_delivery.py::test_smtp_failure_is_best_effort_and_logs_no_sensitive_values`

## 需求来源
- 正式发布不能把真实栈 skip、迁移库名错配、前端 build 软失败或未执行 Playwright 当作门禁通过。

## 目标
1. 消除 pytest 全量运行的 logger 全局状态污染，不改冻结邮件断言。
2. 让 `verify.sh --tc` 为 ops/aiqa/feishu 三组迁移分别准备并使用正确数据库，并让常规真实栈门禁实际执行预约、管理员、认证、Agent CRUD、Worker 与飞书用例。
3. 让前端 production build 与 Playwright E2E 成为明确硬门禁，并给缺浏览器提供可操作错误。
4. 扩大 pre-push/CI 路径与测试覆盖，避免基础设施变更绕过门禁。

## 非目标
- 不修改邮件发送业务语义、日志脱敏规则或产品 UI。
- 不在本任务下载浏览器、漏洞库或推送远端。
- 默认门禁不得读取本地真实 SMTP、LLM、Embedding、Reranker 或飞书凭据，也不得隐式调用外部 Provider。

## 允许修改路径
- `apps/api/tests/conftest.py`
- `scripts/verify.sh`
- `scripts/prepush.sh`
- `scripts/git-hooks/pre-push`
- `.github/workflows/agent-quality-gate.yml`
- `playwright.config.ts`
- `tasks/TASK-RELEASE-GATES-002.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- 冻结测试断言文件
- 业务实现、迁移、OpenAPI、依赖清单

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；仅创建/重建 `jianli_test`、`jianli_auth_001_db` 与三组 `jianli_tc_*` 专用测试数据库。
- API：无。
- 依赖：无新项目依赖；使用仓库已存在的 `@playwright/test` 和 CI 运行环境。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：仅修复门禁编排和测试隔离，使其达到 approved test-plan。

## 功能验收
- 全量 DB-free pytest 不再因测试顺序导致邮件日志用例失败。
- `--tc` 三组迁移数据库名与各冻结测试一致且均可单独失败传播。
- 本地/CI 显式注入真实栈测试 URL 与互异测试密钥，核心数据库用例不得因缺少环境变量被静默 skip（真实 SMTP 除外）。
- `pnpm build`、`pnpm exec playwright test` 失败时门禁非零。
- CI 安装 Chromium 后执行现有两条 Playwright 用例。

## 安全与隐私验收
- 测试输出不打印 secret；测试数据库只能使用 `jianli_test`、冻结认证用例指定的 `jianli_auth_001_db` 或 `jianli_tc_*` 名称。
- 本地 `.env.local` 即使含真实凭据，门禁也会先清洗外部 Provider/通知凭据并强制 `environment=test`、`email_mode=console`。

## 性能验收
- 门禁脚本不重复下载依赖；本地浏览器缺失时快速失败并提示一次性安装命令。

## 变更预算
- max_files：8
- expected_prod_lines：0
- expected_test_lines：≤ 260

## 必须运行的测试命令
- `PYTHONPATH=. pytest -q -ra`（DB-free 环境）
- 三组 migration pytest
- `bash -n scripts/verify.sh scripts/prepush.sh scripts/git-hooks/pre-push`
- `pnpm test && pnpm typecheck && pnpm build`
- `pnpm exec playwright test`（浏览器就绪后）

## 回滚方法
- 回退 harness/CI 文件；无数据与业务回滚。

## 强制停止条件
- 需要修改冻结测试断言、引入新 npm/pip 依赖或降低门禁。
- 超出变更预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：Playwright 浏览器下载需要用户网络配合
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
