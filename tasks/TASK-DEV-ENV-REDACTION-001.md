# TASK-DEV-ENV-REDACTION-001 本地环境输出脱敏

> 状态：In Progress（2026-08-31）。上线门禁日志审查发现 `dev-env.sh` 会输出含 userinfo 的完整数据库 URL；用户已授权修复。

## 任务类型
- implementation（日志安全缺陷修复）

## 基线与引用
- baseline：PRD 2.3.6 / SRS 1.9 / security 0.5 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
- `docs/design/security.md` §9、`docs/test/test-plan.md` TC-SEC-007

## 目标
- 开发环境加载成功时只显示数据库名、SMTP host 与加密配置状态，不输出 URL authority/userinfo。

## 非目标
- 不改变 env 生成、加载、默认值或凭据策略。

## 允许修改路径
- `scripts/dev-env.sh`
- `tasks/TASK-DEV-ENV-REDACTION-001.md`

## 已批准的 DB / API / 依赖变更
- DB：无。API：无。依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：仅收紧终端诊断输出。

## 变更预算
- max_files：2
- expected_prod_lines：≤8

## 验收
- `source scripts/dev-env.sh` 输出不含 `://`、`@` 或数据库密码，仍能确认数据库名与配置状态。
- `bash -n scripts/dev-env.sh` 通过。

## 回滚
- 回退输出脱敏与任务单；无数据回滚。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
