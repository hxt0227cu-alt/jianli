# TASK-ARCH-001 产出架构设计与 ADR review 草案（阶段 2 设计工件）

> 架构草案任务。本任务**仅产出 review 草案**，不代签 approved；密码哈希算法不在本阶段裁定（留《安全设计》ADR）；不修改 SRS、不新增错误码、不提前进入安全设计/OpenAPI/测试计划/编码。

## 任务类型
- design         # 架构设计 + ADR（review 草案）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / SRS 1.1（approved）/ UI 线框 1.0（approved）/ AI 治理 1.0.1（均取自 `docs/baseline.yml`；SRS 为行为唯一源）
- 基线 commit：38b102a91b3d8f0447de36791e67ae342be9e1f4（UI 线框 v1.0 批准锚点；当前最新验证锚点）

## 精确规范引用（AI 只读取这些章节）
- SRS v1.1：§2.3（运行环境/部署约束）/ §3.5（预约创建）/ §3.6（原子改期·取消）/ §3.7（owner 强制取消）/ §3.8（飞书视图·双通道提醒·通知可靠性）/ §4.2（软件接口行为）/ §4.3（SSE·通知可靠性行为）/ §5（非功能：性能/安全/隐私/可用性/备份/限频）/ §6.2（状态模型）/ §7（权限矩阵）/ §8（错误码表）
- 领域模型 v1.1.4：§2（实体清单）/ §5（状态机）/ §6.6（Appointment·部分唯一索引）/ §6.7（AppointmentSlot·行锁）/ §6.9（AvailabilityOverride）/ §6.11（NotificationEvent Outbox）/ §6.12（NotificationDelivery）/ §6.14（知识库索引版本与原子切换）/ §6.15（AuditLog）
- PRD v2.3.3：§4.5（网格规则）/ §4.6（通知可靠性失败矩阵）/ §5（非功能·成本·备份）/ §8.4（账号隔离·验证码用途）/ §8.7（加密·密钥）/ §8.9（权限矩阵）/ §8.12（错误码）

## 需求来源
- 架构须支撑：R8/R10/R11/R12/R14/R14a/R14b/R16/R18/R19/R21/R22/R24/R26 等全部功能与非功能需求（见 SRS §10 追踪矩阵）

## 目标
产出架构设计 review 草案（docs/design/architecture.md），覆盖：
1. 系统边界与模块划分；
2. Web 前端、后端、数据库、RAG、SSE、Outbox/通知消费者的部署和调用关系；
3. 预约创建、原子改期、owner 强制取消的事务边界；
4. 多实例 SSE 一致性与断线全量恢复方案；
5. NotificationEvent/NotificationDelivery 重试、死信、退信回写与人工重发；
6. 知识库热更新与索引原子切换；
7. 腾讯云部署、备份恢复、日志监控与故障降级；
8. 需要独立裁定的 ADR 清单。

## 非目标（明确排除）
- **不选择密码哈希算法**（SRS §6.3 明确留《安全设计》ADR 裁定；若与 PRD §8.7 BCrypt 不一致须先走 Change Request）。
- 不修改 SRS 业务内容；不新增错误码（含不自行新增 AUTH_EXPIRED 关联）。
- 不定义 REST URL / OpenAPI / SSE 载荷字段（留《接口契约》）。
- 不写前端/后端代码；不做《安全设计》《测试计划》。
- 不进入架构/ADR 之外的下游阶段。

## 允许修改路径
- docs/design/architecture.md        # 本任务主交付物（架构 review 草案）
- docs/baseline.yml                   # architecture.status: pending→review（反映草案产出）
- PROJECT_STATE.md                    # 同步架构阶段态
- tasks/TASK-ARCH-001.md              # 本任务单自身回填

## 禁止修改路径
- PRD / 用例规约 / 领域模型 / SRS 业务内容
- 任何代码文件、数据库迁移脚本、OpenAPI / SSE 契约
- 安全设计 / 测试计划 工件

## 已批准的 DB / API / 依赖变更
- 无（本任务纯设计；物理 Schema 以领域模型 §6 为准，不改）

## 功能验收
- 架构草案逐节覆盖目标 8 项；模块划分与已批准领域模型实体（§2）一一对应
- 事务边界设计满足 SRS §3.5/§3.6/§3.7 + 领域模型 §6.6/§6.7/§6.11 并发不变量
- SSE 方案满足 SRS §4.3（≤2s 到达、多实例一致、断线全量恢复）与 §5.4 降级
- 通知可靠性满足 SRS §3.8/§4.3 + 领域模型 §6.11/§6.12（Outbox/重试≤3/死信/退信回写/人工重发）
- 知识库热更新满足 SRS §3.2 R24 + 领域模型 §6.14（原子切换、删除即禁检索）
- 部署/备份/监控/降级满足 SRS §2.3/§5.4/§5.5（腾讯云、RPO≤24h RTO≤4h、SLO≥99.5%）

## 安全与隐私验收
- 敏感字段 AES-256 逐列加密、密钥 Secret Manager 轮换≤90 天（SRS §5.2/§6.3/PRD §8.7）
- 账号隔离（面试官 vs admin 同表分域）、记住我令牌哈希（SRS §5.2/§7）
- 红格隐私遮挡、日志脱敏（SRS §5.3/§6.3）
- **密码哈希算法不在本阶段裁定**（留安全 ADR）

## 性能验收
- 满足 SRS §5.1 量化阈值（首字≤3s、API≤500ms、预约提交≤1.5s、SSE≤2s、热更新分档 SLA）

## 变更预算（change_budget）
- max_files：4（architecture.md / baseline.yml / PROJECT_STATE.md / 本任务单）
- expected_prod_lines：架构正文为主
- expected_test_lines：0

## 必须运行的测试命令
- 无（设计任务）；交付前执行全仓一致性 Grep 校验（模块↔实体映射、事务边界引用）

## 回滚方法
- 初始化 Git 后使用 git restore/revert；本任务不产生迁移

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「允许修改路径」列明，而不是看变更类型本身。**
- **可继续**：变更已在「允许修改路径」列明且为设计性质，依据工件（SRS/领域模型/UI）在 `docs/baseline.yml` 为 `approved`。
- **必须立即停止并报告**：出现任何未在「允许修改路径」列明的变化，包括新增/修改数据库表/字段/索引（超出领域模型已批准范围）、新增/修改公开 API、改变加密/鉴权/权限策略、修改 SRS 业务内容、自行选择密码哈希算法、自行新增错误码、实现任务范围外功能（含 deferred 延后项）。

## 交付证据（review 草案，不关闭）
- commit / PR：<回填 G1>
- 修改文件清单：<回填，与「允许修改路径」对照>
- 测试命令及结果：全仓一致性 Grep 校验（模块↔实体映射 / 事务边界引用）→ <回填>
- lint / typecheck：不适用（设计任务）
- DB 迁移验证：无
- 验收证据：<架构草案 8 节覆盖 + ADR 清单 + 开放项>
- 变更预算实际值：<max_files 实际>
- 未解决风险：AUTH_EXPIRED 语义冲突（SRS §3.3 关联限频 vs §8 定义登录过期）登记为「OpenAPI 设计前必须裁定」开放项；架构阶段不裁定、不新增错误码、不修改 SRS
- 是否偏离 TASK：否
- 规范影响结论：none（纯架构设计，不改业务行为；依据均 approved）
- spec_sync：clean（上游 SRS/DM/UI 均 approved 且 based_on 未变）
- verified_commit：<回填 G1>
- **关闭门禁（四条件全满足方可关闭）**：① 测试通过；② 规范影响已处理（none）；③ spec_sync = clean；④ verified_commit 已记录真实 sha。**本任务保持 review，待用户独立评审批准 architecture 后方可关闭。**

## 关联
- Change Request：无（AUTH_EXPIRED 冲突建议升 Change Request，但不得在本任务内裁定）
- 测试任务：无（设计）
