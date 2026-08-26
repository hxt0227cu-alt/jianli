# TASK-TEST-WEB-RESUME-001 简历 PDF iframe 冻结测试同步

> 状态：Blocked by implementation mismatch（2026-08-26）。当前 master 使用 `<embed>` 且保留占位文案；用户要求本任务仅更新测试以验收“当前真实 iframe”，两者不一致。

## 任务类型
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / SRS 1.5 / UI 1.0
- 基线 commit：`31d3ee9`

## 精确规范引用
- 用户于 2026-08-26 对 TASK-TEST-WEB-RESUME-001 的显式批准
- `tests/web-shell/shell.test.ts` PDF 占位断言

## 目标
删除过期的 PDF 占位断言，冻结真实 `/resume.pdf` iframe 与可访问标题；其他断言完全保持。

## 非目标
- 不修改 `apps/web/main.tsx`、样式、PDF 文件或其他业务代码。
- 不删除、skip、放宽其他断言。

## 允许修改路径
- `tests/web-shell/shell.test.ts`
- `tasks/TASK-TEST-WEB-RESUME-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/web/` 与全部后端、规范、依赖文件

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- spec_sync：clean

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：≤20

## 必须运行的测试命令
- `npm test`
- `npm run typecheck`
- `npm run build`

## 强制停止条件与当前证据
- 当前 `apps/web/main.tsx` 为 `<embed className="resume-embed" src="/resume.pdf" ...>`，并包含 `PDF 简历将在这里显示`。
- `stash@{0}` 才包含 `PdfView` 与 `<iframe ... title="简历 PDF">`。
- 只修改冻结测试会制造必然失败；恢复 iframe 又超出本任务明确非目标，故等待用户批准独立最小实现修复。

## 交付证据
- commit / PR：待解除阻塞
- 修改文件清单：当前仅任务单
- 测试命令及结果：未运行（实现前置不满足）
- lint / typecheck：未运行
- DB 迁移验证：无
- 未解决风险：当前 master 与用户所述“真实 PDF iframe”不一致
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 关闭门禁：Blocked
