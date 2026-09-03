# TASK-HARNESS-DOC-SYNC-004 发布门禁文档同步

> 状态：In Progress（2026-08-31）。上线前审查确认 `docs/HARNESS.md` 仍描述旧的软 build、自动安装依赖、单迁移库与仅 apps 路径触发规则；用户已授权修复。

## 任务类型
- documentation（实现现状同步）

## 基线与引用
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
- `docs/test/test-plan.md` §1、TC-OPS-002、TC-OPS-003、TC-SEC-007
- `scripts/verify.sh`、`scripts/prepush.sh`、`scripts/git-hooks/pre-push`

## 目标
- 让 Harness 接手文档准确描述当前硬门禁、测试库隔离、外部凭据清洗、Playwright 和 hook 范围。

## 非目标
- 不修改脚本、测试、业务、依赖、API 或数据库。

## 允许修改路径
- `docs/HARNESS.md`
- `tasks/TASK-HARNESS-DOC-SYNC-004.md`

## 已批准的 DB / API / 依赖变更
- DB：无。API：无。依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：只同步实现真相，不改变门禁行为。

## 变更预算
- max_files：2
- expected_doc_lines：≤55

## 验收
- 文档不再声称自动安装依赖、build 软失败、单迁移库或仅 apps 路径触发。
- 文档列出 Playwright 缺浏览器时的显式联网命令，并区分真实外部通道人工 smoke。

## 回滚
- 回退文档与任务单；无数据回滚。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：不适用
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
