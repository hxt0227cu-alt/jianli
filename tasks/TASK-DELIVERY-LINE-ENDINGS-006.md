# TASK-DELIVERY-LINE-ENDINGS-006 Linux 交付脚本换行稳定性

> 状态：In Progress（2026-08-31）。上线前审查发现 Windows checkout 会把 Shell 脚本转成 CRLF，且关键入口缺 Git executable mode；用户已授权修复上线阻塞。

## 任务类型
- implementation（交付元数据修复）

## 基线与规范引用
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
- `docs/test/test-plan.md` TC-OPS-001、TC-OPS-003、TC-OPS-004

## 目标
- 用 `.gitattributes` 固定 Linux Shell/hook 为 LF、PowerShell 为 CRLF。
- 让 deploy/backup/restore/create-owner/certbot-init 与受控 pre-push hook 在 Linux clone 后具有可执行位。

## 非目标
- 不改变脚本行为、业务代码、依赖、API、数据库或权限策略。

## 允许修改路径
- `.gitattributes`
- `tasks/TASK-DELIVERY-LINE-ENDINGS-006.md`
- 上述脚本仅允许 Git file mode 从 `100644` 改为 `100755`

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：只保证批准的 Linux 运维入口在 Windows 工作区提交后仍可执行。

## 变更预算
- max_files：8
- expected_prod_lines：0
- expected_test_lines：0
- expected_doc_lines：≤45

## 验收
- `git check-attr eol -- scripts/deploy.sh deploy/certbot-init.sh` 均为 `lf`。
- `git ls-files --stage` 显示六个入口为 `100755`。
- WSL `bash -n` 全部通过；安装后的 `.git/hooks/pre-push` 与受控源一致。

## 回滚
- 回退 `.gitattributes`、任务单与 file mode；无数据回滚。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
