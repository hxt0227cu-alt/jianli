# TASK-EVAL-REPORT-FRESHNESS-008 版本化评测报告新鲜度门禁

> 状态：In Progress（2026-08-31）。上线审查发现 `79/79` 只校验 JSON 结构，相关代码/测试/语料变化后仍会误绿；用户已授权修复上线阻塞。

## 任务类型
- test / governance infrastructure

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / SRS 1.9 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`

## 精确规范引用
- `docs/test/test-plan.md` §1、§3、§4
- `TASK-AIQA-EVAL-CI-001`

## 目标
- 校验报告及套件 SHA 均可解析，且套件 SHA 是报告验证 SHA 的祖先。
- 报告验证 SHA 必须是当前候选祖先；其后任何 API/Web/测试/门禁相关改动（含未跟踪文件）均判报告陈旧。
- `latest.json` 自身与任务/说明文档允许作为验证后的证据提交，避免自引用 commit。

## 非目标
- 不重生成或篡改当前 `79/79`；未真实复验前不更新报告 SHA/计数。
- 不修改业务、评测断言/阈值、API、DB、依赖或页面展示。

## 允许修改路径
- `scripts/validate_eval_report.py`
- `docs/HARNESS.md`
- `tasks/TASK-EVAL-REPORT-FRESHNESS-008.md`

## 禁止修改路径
- `apps/web/evals/latest.json`、业务/测试/迁移/依赖/规范文件。

## 已批准的 DB / API / 依赖变更
- DB：无。API：无。依赖：无；仅 Python 标准库与 Git。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：防止历史评测报告冒充当前候选证据。

## 功能验收
- 当前旧报告因相关路径已变化而明确失败；结构损坏或不可解析 SHA 仍失败。
- 在临时干净 Git fixture 中，验证提交之后只更新 `latest.json` 时可通过，相关代码变化时失败。

## 安全与隐私验收
- 只输出相对路径和 commit，不读取或打印 secret/报告禁用字段内容。

## 性能验收
- 只执行有界 Git 元数据查询，不运行测试或联网。

## 变更预算
- max_files：3
- expected_test_lines：≤90
- expected_doc_lines：≤15

## 必须运行的测试命令
- `python scripts/validate_eval_report.py`（当前候选预期陈旧失败）
- 临时 Git fixture：fresh PASS / relevant change FAIL
- `ruff check scripts/validate_eval_report.py && mypy`（mypy 全 app 由合并门禁覆盖）

## 回滚方法
- 回退校验器与说明；不改报告数据。

## 强制停止条件
- 需要更改公开报告 schema/计数、冻结评测、依赖或超出预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：当前报告保持 historical，须在最终候选提交后真实重跑并生成证据提交
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
