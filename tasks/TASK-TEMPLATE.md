# TASK-XXX <任务标题>

> 复制本模板为 `tasks/TASK-<序号>.md`，作为 AI **仓库变更**的唯一范围约束。无任务单不得写入仓库，包括文档、设计、测试和代码变更。
> 本模板为通用骨架，**不绑定任何具体功能**（如预约/登录/RAG/UI）；每个任务按实际填写。

## 任务类型
- documentation  # 文档：PRD / 用例 / SRS / 设计说明 / 测试计划等
- design         # 设计：UI 线框 / 架构 / ADR / 安全设计
- implementation # 实现：功能编码
- test           # 测试：单元 / 集成 / 验收
- migration      # 迁移：数据库 schema 变更

## 基线版本与基线 commit
- baseline：PRD <ver> / 用例规约 <ver> / 领域模型 <ver>（取自 `docs/baseline.yml`）
- 基线 commit：<仓库未初始化 Git 时写「repository_not_initialized」；初始化后回填真实 commit hash>

## 精确规范引用（AI 只读取这些章节）
- <PRD §x.x / 用例 §x.x / 领域模型 §x.x / ADR-00x / OpenAPI operationId / TC-xxx>

## 需求来源
- <需求规则，如 R8, R10, R12, UC-08>

## 目标
<一句话：本任务要交付什么>

## 非目标（明确排除）
- <明确排除项，如飞书同步 / 邮件发送 / Agent 自动预约 / 非本任务范围>

## 允许修改路径
- <模块 / 文件清单，如 appointment service / appointment repository / appointment 集成测试>

## 禁止修改路径
- <本任务不得触碰的文件 / 模块 / 表>

## 已批准的 DB / API / 依赖变更
- <若任务含 schema 变更，列出已 approved 的迁移；否则写「无」>

## 规范影响评估（spec impact，每个代码 TASK 必填）
> 核心问题：**"这次代码变更，会不会让规范过期？"** 不允许代码写完后再问 AI "该改什么文档"。
- behavior_change：<true / false（本次变更是否改变用户可观察行为）>
- affected_specs：
  - srs：<none / update / change_request_required>
  - domain_model：<none / update / change_request_required>
  - openapi：<none / update / change_request_required>
  - security：<none / update / change_request_required>
  - test_plan：<none / update>
- reason：<一句话说明；三类判定见下方分类>
- 分类（与 `AGENTS.md §9` 一致）：
  - **代码重构**（行为未变）→ 不需要改 SRS；更新测试/交付证据即可
  - **Bug 修复使代码重新符合现有 SRS** → 不需要改 SRS；更新测试/交付证据
  - **真正改变用户可观察行为** → 不允许直接改代码；先 Change Request → 更新并 approve 规范 → 再创建 implementation TASK
  - 判定为 change_request_required 时，本 TASK 不得继续，须先走变更流程

## 功能验收
- <前置条件满足时成功>
- <异常路径预期>

## 安全与隐私验收
- <加密字段 / 权限 / 审计要求>

## 性能验收
- <P95 / 并发 / 行数等量化阈值>

## 变更预算（change_budget）
- max_files：<上限，超则拆任务>
- expected_prod_lines：<预计生产代码行>
- expected_test_lines：<预计测试代码行>

## 必须运行的测试命令
- <如 pytest / npm test / 迁移 up-down 验证>

## 回滚方法
- <DB 迁移 down / 特性开关 / 配置回退>

## 强制停止条件（与 `AGENTS.md §2` 一致）

判定口径：**看变更是否已在本任务单「已批准的 DB / API / 依赖变更」中列明，而不是看变更类型本身。**

- **可继续**：变更已在上述章节逐项列明，**且**其依据工件（ADR / OpenAPI / 领域模型 / 安全设计）在 `docs/baseline.yml` 中为 `approved`（ADR 为 `accepted`）。
- **必须立即停止并报告（不得自行决定）**：出现任何**未在该章节列明**的变化，包括但不限于
  - 新增外部依赖（npm / pip 包）；
  - 新增或修改数据库表、字段、索引、迁移；
  - 新增或修改公开 API / SSE 事件 / 契约字段；
  - 改变加密、密钥、鉴权或权限策略；
  - 实现任务范围外的功能（含 `deferred` 延后项）；
  - 现有代码与领域模型不一致；
  - 需求、用例、接口三者之间存在冲突。
- **其余硬停条件**（与变更列明与否无关）：超出 `change_budget`（`max_files` / 行数）→ 拆任务；冻结验收测试失败 → 停止，不得改断言或跳过。

停止时输出：触发条目 + 冲突证据（文件与章节）+ 建议的 Change Request 或拆分方案。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<commit sha 或 PR 链接>
- 修改文件清单：<实际改动文件，与「允许修改路径」逐一对照>
- 测试命令及结果：<命令> → <pass/fail 数；冻结验收测试须逐条列出 TC 编号与结果>
- lint / typecheck：<结果>
- DB 迁移验证：<up / down 是否通过；无迁移写「无」>
- 验收证据：<截图 或 接口响应样例 或 日志片段（敏感字段须脱敏）>
- 变更预算实际值：<max_files 实际 / 生产行数 / 测试行数，与预算对照>
- 未解决风险：<或「无」>
- 是否偏离 TASK：<否 / 偏离项及原因>
- 规范影响结论：<none / updated / change_request_required（须与「规范影响评估」一致）>
- spec_sync：<clean / dirty（下游工件与上游 based_on 是否一致；dirty 不得关闭）>
- verified_commit：<真实 commit sha；本任务验证所基于的 commit 锚点，也是审计模式 checkout 的快照>
- **关闭门禁（四条件全满足方可关闭）**：① 测试通过；② 规范影响已处理（none/updated 或已走 Change Request）；③ spec_sync = clean；④ verified_commit 已记录真实 sha。任一不满足→任务不得关闭，从根源杜绝"代码改了文档忘改"。

## 关联
- Change Request：<若有>
- 测试任务：<TC-XXX>
