# TASK-GOV-BASELINE-PRD-001 校正 PRD 基线版本锚点

> 状态：Closed（2026-08-26）

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5
- 基线 commit：`6f7bbc90503eb538ce7c65a22b5459bc3041852d`

## 精确规范引用（AI 只读取这些章节）
- `docs/baseline.yml` `artifacts.prd` / `artifacts.srs.based_on.prd`
- `docs/requirements/PRD.md` 文档版本记录 v2.3.4
- `docs/requirements/SRS.md` 文档状态与 `based_on` 头部
- `tasks/TASK-CR-VERIFY-CODE-001.md` 交付证据

## 需求来源
- 用户 2026-08-26 明确授权：仅将 `docs/baseline.yml` 的 PRD 当前版本从 2.3.3 校正为已批准的 2.3.4，并同步必要任务状态；无需求、API、数据库或代码行为变化。

## 目标
消除 `artifacts.prd.version=2.3.3` 与已批准 PRD v2.3.4、SRS v1.4 `based_on.prd=2.3.4` 之间的治理锚点冲突。

## 非目标（明确排除）
- 不改 PRD、SRS、OpenAPI、领域模型正文。
- 不改任何生产代码、测试、数据库或依赖。
- 不重新评审或改变已经批准的验证码需求。

## 允许修改路径
- `tasks/TASK-GOV-BASELINE-PRD-001.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- 除上述三项外的全部仓库文件。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：无。

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：仅修复唯一规范源中的过期版本号；被引用的 PRD v2.3.4 内容已由 `TASK-CR-VERIFY-CODE-001` 获用户批准并落于提交 `1d194db`。
- 分类：治理元数据 Bug 修复，不改变用户可观察行为。

## 功能验收
- `artifacts.prd.version` 为 `2.3.4` 且保持 `status: approved`。
- `artifacts.srs.based_on.prd` 与之相等。
- PRD 正文版本记录仍存在 v2.3.4，内容不变。

## 安全与隐私验收
- 不读取、记录或修改任何凭据与个人信息。

## 性能验收
- 不适用。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- PowerShell 字符串断言：baseline 当前 PRD 与 SRS `based_on.prd` 均为 2.3.4。
- `git diff --check -- docs/baseline.yml PROJECT_STATE.md tasks/TASK-GOV-BASELINE-PRD-001.md`

## 回滚方法
- 回滚本任务提交，恢复 `artifacts.prd.version=2.3.3`（仅在确认 v2.3.4 批准事实无效时执行）。

## 强制停止条件
- 若 PRD v2.3.4 未经用户批准或 `1d194db` 不含该版本正文，立即停止。
- 若需修改任何规范正文、代码、API、DB 或依赖，立即停止并拆分任务。
- 超过 3 个文件立即停止。

## 交付证据
- commit / PR：`a9526b5`（治理校正实现快照）。
- 修改文件清单：`docs/baseline.yml`、`PROJECT_STATE.md`、`tasks/TASK-GOV-BASELINE-PRD-001.md`。
- 测试命令及结果：PowerShell 字符串断言 → PRD current=2.3.4、SRS `based_on.prd`=2.3.4、PRD 正文 v2.3.4 记录存在；全部通过。`git diff --check` → 通过（仅 Git 行尾转换提示）。
- lint / typecheck：不适用（纯治理元数据）。
- DB 迁移验证：无。
- 验收证据：`docs/baseline.yml` `artifacts.prd.version=2.3.4` 且 `status=approved`；与 SRS v1.4 `based_on.prd=2.3.4` 一致。
- 变更预算实际值：3/3 文件；生产代码 0 行；测试代码 0 行，未超预算。
- 未解决风险：无。
- 是否偏离 TASK：否。
- 规范影响结论：none。
- spec_sync：clean。
- verified_commit：`a9526b5`。
- 关闭门禁：① 验证通过；② 规范影响 none；③ spec_sync=clean；④ verified_commit 已记录——全部满足。

## 关联
- 已批准变更任务：`TASK-CR-VERIFY-CODE-001`
- 后续任务：`TASK-AUTH-EMAIL-DELIVERY-001`
