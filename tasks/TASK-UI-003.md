# TASK-UI-003 UI 线框内容修正（v1.1 行为对齐，消除误导实现的表述）

> 向前内容修正：UI 线框（ui-wireframe.md）当前依据已批准 SRS **v1.1**（`00e125c`，行为唯一源，含退信 Bounce 行为）与领域模型 v1.1.4（approved），但存在 8 处会**误导实现**（implementation-misleading）的表述，须在执行用户评审批准 UI 前一次性修正。本任务**执行中、未关闭**，待用户评审实际线框后授权批准 UI（`baseline.ui_wireframe.status` 仍 `pending`）。不新建页面、不扩展需求、不批准 UI、不推进下游。

## 任务类型
- design         # UI 线框（低保真文本线框，纯文档表述纠偏）

## 基线版本与基线 commit
- baseline：SRS 1.1（approved @ `00e125c`）/ 领域模型 1.1.4（approved @ `f537296`）/ PRD 2.3.3 / 用例规约 1.7.2（取自 `docs/baseline.yml`）
- 基线 commit：`00e125c`（SRS v1.1 批准锚点）；TASK-UI-002 已执行并关闭（`266a773`），A6/A7 失败三态 + 退信(Bounce) 线框已同步

## 精确规范引用（AI 只读取这些章节）
- SRS v1.1：§3.3（登录注册异常/限频，错误码 §8）、§3.4（网格 PRD §4.5，7 列周一–周日）、§3.5（预约创建：点绿→冲突校验→弹表单；R26 确认函→面试官注册邮箱）、§3.8（R13 双通道提醒=候选人飞书+邮箱；退信存 channel_metadata）、§6.2（DeliveryStatus 枚举，退信不属枚举）、§8（错误码 `AUTH_EXPIRED`=登录过期）
- PRD v2.3.3：§4.5（网格精确规则）、§4.6（通知可靠性）

## 需求来源
- R13（双通道提醒=候选人）/ R26（确认函→面试官注册邮箱）/ R20（注册验证流程）

## 目标
一次性修正 ui-wireframe.md 中 8 处会误导实现的表述，使其与已批准 SRS v1.1 行为一致；不改变用户可观察行为设计意图，仅纠偏错误表述。

## 非目标（明确排除）
- 不新增页面/组件、不扩展需求、不修改 SRS/PRD/用例规约/领域模型业务内容
- 不批准 UI（不改 `baseline.ui_wireframe.status`）、不推进架构/安全/OpenAPI/SSE/测试计划/编码

## 允许修改路径
- docs/design/ui-wireframe.md        # 本任务主交付物（8 处内容修正）
- tasks/TASK-UI-003.md               # 本任务单自身回填交付证据
- tasks/TASK-UI-001.md               # 标注本任务承接的 8 项后续内容修正（TASK-UI-002 退信缺口已闭合）
- PROJECT_STATE.md                   # 同步 TASK-UI-003 条目

（max_files=4，change_budget 见下）

## 禁止修改路径
- SRS / PRD / 用例规约 / 领域模型业务内容（仅引用，不改）
- docs/baseline.yml（不得改 `ui_wireframe.status`）
- 任何代码文件、数据库迁移、OpenAPI / SSE 契约

## 已批准的 DB / API / 依赖变更
- 无（本任务纯设计表述纠偏，不含 schema / API / 依赖变更）

## MP-1 修正点（8 处，逐条对应 SRS v1.1）
1. **A6 筛选拆分**：投递状态 `failed` / `retry_scheduled` / `dead_letter`；退信 `全部 / 是 / 否`。退信**不得**作为 `DeliveryStatus` 选项（SRS §6.2）。
2. **U9 分开两类通知**：预约确认函 → 面试官注册邮箱；新预约事件 → 飞书+邮箱提醒候选人。不得写"确认函通过飞书+邮箱双通道发送"（SRS §3.5 R26 / §3.8 R13）。
3. **U3 日历**：周一至周日 7 个独立日期列，不得合并周六、周日为"周末"一列（PRD §4.5 / SRS §3.4）。
4. **红色图例**：改为"已预约/不可约"，覆盖 `booked` / `owner_locked` / `unavailable`（SRS §6.2）。
5. **U3 交互**：点绿 → 高亮同列后续 2 格为黄 → 冲突校验通过 → 直接弹 U7；删除"再次点击黄格才弹表单"（SRS §3.5）。
6. **U4 错误提示**：凭证错误 / 限频锁按普通错误提示呈现；`AUTH_EXPIRED` 仅用于登录会话过期（除非 approved SRS §8 另定义其他错误码）。
7. **U5 一次邮箱验证流程**：发送验证码 → 输入并校验验证码 → 注册成功；删除"注册成功后再次发送验证邮件"（SRS §3.3）。
8. **文档顶部行为依据**：统一为已批准 SRS v1.1，并标明 TASK-UI-002 退信缺口已闭合。

## 功能验收
- Grep 复核 A6 筛选：投递状态仅含 `failed`/`retry_scheduled`/`dead_letter`，退信为独立筛选（全部/是/否），无"退信"混入状态枚举
- U9 无"飞书+邮箱双通道发送确认函"表述；确认函→面试官注册邮箱、新事件→候选人飞书+邮箱
- U3 日历 7 列（周一…周日），无"周末"合并列
- 红色图例 = 已预约/不可约
- U3 交互：点绿→冲突校验→直接弹 U7（无"点黄弹表单"）
- U4 无 `AUTH_EXPIRED` 用于凭证错误/限频
- U5 单次验证流程，无"注册后再次发送验证邮件"
- 文档顶部 = 已批准 SRS v1.1 且标注退信缺口闭合

## 安全与隐私验收
- 无新增隐私字段暴露；语义色与 SRS §6.2 一致
- `AUTH_EXPIRED` 仅会话过期，不泄露凭证错误细节

## 性能验收
- N/A（静态低保真线框修正，不产生新运行时要求）

## 变更预算（change_budget）
- max_files：4（ui-wireframe.md / TASK-UI-003.md / TASK-UI-001.md / PROJECT_STATE.md）
- expected_prod_lines：线框 8 处修正
- expected_test_lines：0

## 必须运行的测试命令
- 全仓一致性 Grep 校验（8 处修正落地）；纯文档，无 lint/typecheck/DB 迁移

## 回滚方法
- git restore/revert 本任务提交；纯文档，无迁移

## 强制停止条件（与 AGENTS.md §2 一致）
- **可继续**：MP-1 已列 8 处为已知目标，不触发启动即硬停。
- **必须立即停止并报告**：发现 MP-1 已列范围之外的 ui-wireframe.md 不一致，或任何超出"允许修改路径"的修改（含改 baseline、改 SRS、建页面）。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：c0f58290a49ab052a3a79262d3a2a01611108fe7（TASK-UI-003 内容修正快照 G1）
- 修改文件清单：docs/design/ui-wireframe.md（8 处修正）/ tasks/TASK-UI-003.md（本任务单）/ tasks/TASK-UI-001.md（标注承接）/ PROJECT_STATE.md（TASK-UI-003 条目）—— 与「允许修改路径」一致，max_files=4
- 测试命令及结果：全仓 Grep 复核 8 处修正（A6 筛选拆分 / U9 两类通知 / U3 七列 / 红图例 / U3 交互 / U4 AUTH_EXPIRED / U5 单次验证 / 文档顶部 v1.1）→ pass（无残留错误表述）
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：A6 筛选「[投递状态 failed/retry_scheduled/dead_letter] [退信 全部/是/否]」；U9「预约确认函已发送至面试官注册邮箱」+「新预约事件已通过飞书+邮箱提醒候选人」；U3 周一…周日 7 列 + 「冲突校验通过→直接弹预约表单(U7)」；U4「AUTH_EXPIRED 仅用于登录会话过期」；U5「发送验证码→输入并校验验证码→注册成功」
- 变更预算实际值：max_files=4，实际 4 文件，未超预算
- 未解决风险：SRS §3.3 异常流将「限频→提示稍后（AUTH_EXPIRED/EMAIL_UNVERIFIED）」与 §8 错误码表「AUTH_EXPIRED=登录过期」存在内部不一致；属 SRS 范围、非本任务修改路径，已另行提示用户（不影响本任务 8 处修正正确性）
- 是否偏离 TASK：<否>
- 规范影响结论：none（纯设计表述纠偏，不改行为）
- spec_sync：clean
- verified_commit：c0f58290a49ab052a3a79262d3a2a01611108fe7（TASK-UI-003 内容修正快照 G1；非自指）

## 关闭门禁（四条件全满足方可关闭）
① 测试通过（Grep 复核 8 处修正）② 规范影响 none ③ spec_sync=clean ④ verified_commit 真实 sha。状态：Closed（UI 线框 8 处内容修正已落地；`baseline.ui_wireframe.status` 仍 pending，待用户评审批准；本任务不代签 UI）。

## 关联
- 上游：TASK-UI-002（退信缺口已闭合，本任务承接 8 项后续内容修正）；SRS v1.1（`00e125c`）
- Change Request：无
- 测试任务：无（设计）
