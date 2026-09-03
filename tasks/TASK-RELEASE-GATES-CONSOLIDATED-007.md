# TASK-RELEASE-GATES-CONSOLIDATED-007 发布门禁合并收口

> 状态：In Progress（2026-08-31）。用户已授权修复全部上线阻塞；本单合并承接 `TASK-RELEASE-GATES-002`、`TASK-RELEASE-GATE-ISOLATION-003`、`TASK-EXTERNAL-RAG-GATE-005` 与 `TASK-HARNESS-DOC-SYNC-004` 的重叠文件，原任务不得再分别宣称预算合规或独立关闭。

## 任务类型
- test / CI infrastructure（不改变产品行为）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/test/test-plan.md` §1、§2.9、§3、§4
- `AGENTS.md` §6～§9

## 目标
1. 让本地与 CI 的真实 PG/Redis、迁移、Python 质量、前端构建及浏览器检查失败可传播，禁止意外 skip/误绿。
2. 单独 `--quick` 明确为非发布离线预检；完整/`--tc`/CI 强制真实 Embedding 回归，缺配置或网络即失败。
3. 清洗 SMTP、Chat LLM 与飞书真实凭据；本地数据库/Redis 仅允许 WSL loopback 的开发 Compose 端口。
4. 修复 hook 推送范围、路径覆盖、安装漂移、换行与文档口径。

## 非目标
- 不宣称当前静态 Playwright 是浏览器+API+DB+Worker 的 L4 全链路。
- 不修改冻结 TC 断言、评测阈值、业务代码、API、DB schema、依赖或供应链策略。
- 不把历史 `79/79` 报告冒充当前候选验证结果。

## 允许修改路径
- `.github/workflows/agent-quality-gate.yml`
- `playwright.config.ts`
- `scripts/verify.sh`
- `scripts/prepush.sh`
- `scripts/git-hooks/pre-push`
- `docs/HARNESS.md`
- `docs/devlog/pitfalls/pitfalls.md`
- `docs/devlog/pitfalls/pitfalls.jsonl`
- `tasks/TASK-RELEASE-GATES-CONSOLIDATED-007.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `tests/**` 冻结断言、`apps/api/app/**` 业务实现、迁移、OpenAPI、需求/设计规范、依赖清单。

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；仅允许 loopback 开发 Compose 上的 `jianli_test`、`jianli_auth_001_db` 与 `jianli_tc_*` 隔离库。
- API：无。
- 依赖：无；不得在门禁中自动联网安装。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：恢复并收紧 approved 测试计划的执行语义。

## 功能验收
- 本地离线预检无新失败并明确非发布；完整/`--tc` 与 CI 不移除真实 Provider 回归。
- 三套迁移在独立数据库执行；前端 test/typecheck/build 与 Playwright 失败均传播。
- hook 使用真实 push range，受控源与安装副本一致。

## 安全与隐私验收
- 不输出 secret；SMTP/Chat LLM/飞书不被隐式调用。
- 本地 destructive 测试入口只接受 `127.0.0.1|localhost|::1` 且端口固定为 PG `55432`、Redis `63790`，初始库固定为 `jianli_dev` / Redis DB 0。

## 性能验收
- 不重复安装依赖或浏览器；真实 Provider 失败不自动重试。

## 变更预算
- max_files：10
- expected_prod_lines：0
- expected_test_lines：≤ 460
- expected_doc_lines：≤ 100

## 必须运行的测试命令
- `bash -n scripts/verify.sh scripts/prepush.sh scripts/git-hooks/pre-push`
- `bash scripts/verify.sh --quick`
- `bash scripts/verify.sh --tc --quick`（真实 Provider/WSL Docker 正常后）
- `pnpm test && pnpm typecheck && pnpm build`
- `pnpm exec playwright test`（Chromium 就绪后）
- `bash scripts/install-hooks.sh && cmp -s scripts/git-hooks/pre-push .git/hooks/pre-push`
- CI YAML 静态解析；远端 Actions 仅在 push 且 Secrets 配置后形成证据。

## 回滚方法
- 回退本任务列明的门禁与文档文件；无业务数据回滚。

## 强制停止条件
- 需要改变冻结断言/阈值、业务契约、DB schema、依赖、外部权限；或超出本合并预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：当前 Docker daemon 异常、Playwright Chromium/远端 CI/真实 L4 staging smoke 待外部环境
- 拆分说明：`apps/api/tests/conftest.py` 的测试库迁移安全守卫由 `TASK-HARNESS-DB-GUARD-015` 独立承接，不计入本任务预算。
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
