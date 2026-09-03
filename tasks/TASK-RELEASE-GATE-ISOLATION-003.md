# TASK-RELEASE-GATE-ISOLATION-003 真实栈门禁与外部凭据隔离

> 状态：In Progress（2026-08-31）。由 TASK-RELEASE-GATES-002 在合并审查中因预算边界拆出；用户已授权全部上线修复。

## 任务类型
- test / CI infrastructure

## 基线与引用
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
- `docs/test/test-plan.md` §1、TC-OPS-002、TC-OPS-003、TC-SEC-007

## 目标
1. 本地与 CI 明确执行预约、管理员、认证、AIQA、Worker、飞书、Agent CRUD 的真实 PG/Redis 用例。
2. 默认门禁清洗 `.env.local` 的 SMTP/LLM/Embedding/Reranker/飞书真实凭据，禁止隐式外调、计费或发信。
3. 增加冻结认证用例要求的独立测试库；修正 WSL Git diff 与已安装 hook 漂移。
4. 快速门禁明确报告前端/Playwright 被跳过，不把 skip 写成通过。

## 非目标
- 不执行真实 SMTP/LLM/飞书 smoke；它们是显式人工发布验证。
- 不改业务代码、冻结断言、依赖或产品契约。

## 允许修改路径
- `scripts/verify.sh`
- `scripts/prepush.sh`
- `scripts/git-hooks/pre-push`
- `.github/workflows/agent-quality-gate.yml`
- `tasks/TASK-RELEASE-GATE-ISOLATION-003.md`

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；允许 `jianli_test`、`jianli_auth_001_db` 与 `jianli_tc_*` 测试库。
- API：无。
- 依赖：无；门禁不得自行联网安装缺失依赖。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：只修复测试覆盖、隔离与执行一致性。

## 变更预算
- max_files：5
- expected_prod_lines：0
- expected_test_lines：≤150

## 验收
- 全量真实栈除显式外部 provider smoke 外无意外 skip；三组迁移独立通过。
- 即使 `.env.local` 有真实 key，默认门禁也不会外调或发信。
- CI 使用合法 test/console 配置和互异测试密钥。
- hook 覆盖业务、测试、部署与供应链路径，已安装副本与受控源一致。

## 必须运行
- `bash -n scripts/verify.sh scripts/prepush.sh scripts/git-hooks/pre-push`
- `bash scripts/verify.sh --tc --quick`
- `bash scripts/install-hooks.sh && cmp -s scripts/git-hooks/pre-push .git/hooks/pre-push`
- CI YAML 静态解析；远端 Actions 待 push 后执行。

## 回滚
- 回退本任务门禁编排；无数据回滚。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：Playwright 浏览器与远端 CI 需要网络
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
