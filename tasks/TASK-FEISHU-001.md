# TASK-FEISHU-001 飞书通道：R14 多维表格完整视图同步 + R13 候选人双通道提醒（feishu 侧）

> **状态：draft（草案，待用户评审后批准实现）**
> 依据已批准 SRS v1.3 §3.8（R13/R14/R21）+ 领域模型 v1.1.5 §6.12（NotificationDelivery）+ architecture v0.2 §6（飞书通道）。实现的是已批准 MVP 行为，**非新需求，无需 Change Request**。

## 任务类型
- implementation # 实现：功能编码
- migration      # 迁移：数据库 schema 变更（0008）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / architecture 0.2 / security 0.1（取自 `docs/baseline.yml`）
- 基线 commit：`41afe59`（本任务创建时 master HEAD）

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.8（R13 双通道提醒 / R14 飞书完整视图 / R21 同步失败告警）、§4.2（错误码 `FEISHU_SYNC_FAIL`）
- `docs/design/domain-model.md` §6.12（`NotificationDelivery` 全 12 列 + `uq_delivery_attempt` 唯一索引 + delivery_purpose 语义与收件人解析链路 + 事件类型→投递目的完整映射）
- `docs/design/domain-model.md` §6.1（`uq_active_owner_admin` 部分唯一索引 + 运行不变量）
- `docs/design/architecture.md` §6（通知 Outbox 消费者、双通道独立重试不互兜底、事务内禁外部调用、Txn D/W、幂等键、CAS 写回、`FEISHU_SYNC_FAIL` 告警）
- `docs/design/security.md`（AES-256-GCM 字段加密、SMTP/飞书凭证仅运行时环境变量）

## 需求来源
- R13（双通道提醒，UC-12）：新预约/修改(改时间)/取消事件实时推送候选人**飞书+邮箱**；面试前 10 分钟临近提醒（R18/UC-14）
- R14（飞书完整视图，UC-11）：系统 DB 为唯一真相源，预约变更实时/近实时同步至飞书多维表格（全公司明文：公司/平台/会议号/HR联系方式/备注/时段/状态）；同步失败邮件告警候选人+飞书任务重试（R21）
- R21（飞书同步失败告警，UC-11/UC-12/UC-21）

## 目标
一期交付「飞书通道」两条路径（R14+R13，用户 2026-08-18 选定一起做）：
1. **R14 多维表格同步**：预约创建/改期/取消 → 实时同步写飞书多维表格「面试预约台账（jianli）·预约记录」（`base_token=Z3TubDheZaYpfcsySDecWqXcnlg`，`table_id=tbl6439HzzrFfW4Y`），行 upsert 幂等（`channel_metadata.feishu_record_id`），取消后行状态同步为 `cancelled`。
2. **R13 候选人双通道提醒（feishu 侧）**：`appointment_created/rescheduled/cancelled/reminder_due` → 候选人（owner_admin）`email` + `feishu` 两行独立投递（收件人 = 活跃 owner_admin → `OwnerContactConfig.candidate_feishu_open_id_ciphertext` 解密）。

## 非目标（明确排除）
- **不实现候选人侧"飞书消息内容超链接/交互卡片"**（MVP 仅文本消息；按钮交互 UI 未在 SRS 定义）。
- **不实现飞书→系统的回写**（多维表格只读展示，不可从飞书改预约——MVP 硬规则"后台不提供直接删除预约入口"精神一致）。
- 不实现微信 WorkBuddy 助理（`deferred`）。
- 不改 SMTP 邮件既有路径（M3/M4 已交付，仅复用）。
- 不新增 `feishu` 之外的第三方通道。

## 允许修改路径
- `apps/api/migrations/versions/0008_notification_deliveries.py`（新迁移，表结构出自领域模型 §6.12）
- `apps/api/app/config.py`（新增 `JIANLI_FEISHU_*` 配置项，仅运行时可覆盖）
- `apps/api/app/notifications/feishu.py`（新模块：tenant_access_token 获取/缓存、多维表格行 upsert、候选人文本消息）
- `apps/api/app/notifications/worker.py`（消费 `NotificationDelivery`：按 `delivery_purpose`+`channel` 分发；email 走既有 `EmailSender`，feishu 走新适配器；失败置 `failed`/`retry_scheduled` + `FEISHU_SYNC_FAIL` 邮件告警）
- `apps/api/app/notifications/email.py`（如需要新增 `FEISHU_SYNC_FAIL` 告警模板，仅新增渲染分支）
- `apps/api/app/auth/repository.py` 或 `app/notifications/` 内（owner_admin 收件人解析 + `candidate_feishu_open_id_ciphertext` 解密读取；**不新增明文字段**）
- `apps/api/tests/test_feishu.py`（新测试）+ 既有 `tests/test_worker.py` 扩展（fake feishu sender 断言双通道独立投递）
- `tasks/TASK-FEISHU-001.md`（本任务单）

## 禁止修改路径
- `apps/api/app/appointments/**`（预约业务事务不动，飞书同步只经 Outbox 事件消费）
- `apps/api/app/aiqa/**`、`apps/api/app/admin/**`、`apps/web/**`
- `docs/**`（含 SRS/领域模型/架构/安全/OpenAPI）——本任务不改任何规范工件
- `apps/api/migrations/versions/0001~0007`（已有迁移只读）

## 已批准的 DB / API / 依赖变更
- **DB 迁移 0008 `notification_deliveries`**：表结构 = 领域模型 v1.1.5 §6.12 已批准（id UUID PK / event_id UUID FK / delivery_purpose enum[candidate_notification,interviewer_confirmation,interviewer_cancellation] / channel enum[feishu,email] / event_version int / attempt_no int / status enum[queued,sending,succeeded,failed,retry_scheduled,dead_letter] / channel_metadata jsonb / provider_message_id / next_retry_at / last_error / created_at）+ `uq_delivery_attempt` 唯一索引 `(event_id, delivery_purpose, channel, event_version, attempt_no)`。可逆迁移 up→down→up。
- **依赖变更（需用户批准）**：`httpx` 从 dev extra 提升为运行时 `dependencies`（飞书 HTTP 客户端；AIQA gateway 已惰性导入 httpx，提升为 runtime 后同时满足飞书适配器与既有网关，版本锁定 `httpx==0.28.1`）。**理由**：飞书通道是生产功能，运行时环境（无 dev extra）必须能发起 HTTPS 调用；当前 httpx 仅在 dev extra，生产部署会 ImportError。
- **API / 契约变更**：无（飞书同步走既有 Worker 内部消费，不新增公开端点/SSE 帧）。
- **加密策略变更**：无（沿用 AES-256-GCM；`candidate_feishu_open_id_ciphertext` 字段已在 0001 建表，仅新增读取路径）。

## 规范影响评估（spec impact）
- behavior_change：**false**（实现的是已批准 SRS §3.8 R13/R14/R21 行为——"属 approved MVP 行为，非未来扩展"，用户可观察行为从"无飞书"变为"有飞书"，是向规范收敛而非偏离；不改变任何已定义语义/错误码/契约）
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：已批准需求从延后转实现，规范不因本任务过期。
- 分类：**代码重构级（实现已批准行为）→ 不需要改 SRS；更新测试/交付证据即可**

## 功能验收
- **R14**：经 API 创建预约 → Outbox 事件 → Worker 消费 → 多维表格出现新行（公司/时段/会议平台/会议号/联系人/电话/备注/状态=active）；改期 → 行更新为新时段；取消 → 行状态变 cancelled。重复投递（重试/重启）不产生重复行（幂等）。
- **R13**：候选人（owner_admin）在飞书收到预约创建/改期/取消/临近提醒文本消息；`email` 与 `feishu` 独立投递，单通道失败不影响另一通道。
- **失败路径**：飞书 API 不可达/超时 → `NotificationDelivery.status=failed` 或 `retry_scheduled` → 邮件告警 `FEISHU_SYNC_FAIL` 送达候选人；恢复后重试成功。
- 无活跃 owner_admin 或 `candidate_feishu_open_id_ciphertext` 为 NULL → feishu 通道失败 + 告警，email 通道照常（领域模型 §6.1/§6.12 不变量）。

## 安全与隐私验收
- 飞书 App ID/App Secret 仅运行时环境变量（`JIANLI_FEISHU_APP_ID`/`JIANLI_FEISHU_APP_SECRET`），**绝不写入源码/文档/记忆**。
- `candidate_feishu_open_id_ciphertext` 仅按访问控制解密用于收件人解析，**不落明文、不入日志**。
- 多维表格行含 SRS R14 明文清单字段（公司/平台/会议号/HR 联系方式/备注）——此为已批准"飞书日常视图"语义（候选人本人可见）；站点页面与 API 不因此解密外泄。
- 日志脱敏：不记录 open_id、会议号、电话明文。

## 性能验收
- 事务内禁止外部调用（架构 §6 硬性）：飞书调用全部在 `COMMIT` 之后经 Worker 发起，预约提交 P95 ≤1.5s 不受影响。
- 飞书调用超时上限 10–30s（远小于 5min 租约，避免 `sending` 被误回收）；token 缓存复用（TTL 内不重复换取）。
- 单事件双通道两行独立投递，互不阻塞。

## 变更预算（change_budget）
- max_files：8
- expected_prod_lines：≤ 550（feishu.py 适配器 + worker 分发 + config + 迁移 + 告警模板）
- expected_test_lines：≤ 400（test_feishu.py 真实/桩 + test_worker.py 双通道扩展）

## 必须运行的测试命令
- `pytest tests/test_feishu.py tests/test_worker.py -v`（WSL 真实 PostgreSQL/Redis；feishu 桩 sender + 真 SMTP 可选）
- 迁移验证：`alembic upgrade head && alembic downgrade -1 && alembic upgrade head`（WSL 真实 PG）
- `ruff check apps/api` / `mypy apps/api`
- `python -m py_compile` 新增/修改文件

## 回滚方法
- `alembic downgrade 0007`（删 `notification_deliveries`，无业务数据依赖）
- 移除 `JIANLI_FEISHU_*` 环境变量 + 关闭 Worker feishu 分支 = 功能降级回"仅邮件"，预约业务不受影响（双通道独立）。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 未列明的依赖/表/字段/契约变更 → 停止并报告（如：飞书需要新增 SDK 而非 httpx）。
- 飞书 API 幂等令牌不可用导致无法防重 → 停止，改走"以 `feishu_record_id` 存在即更新"方案并记录（架构 §6.6 已预判）。
- 超出 change_budget → 拆任务（R14 与 R13 可拆为两个独立 TASK）。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<待提交后回填>
- 修改文件清单：<与「允许修改路径」逐一对照>
- 测试命令及结果：<命令> → <pass/fail 数>
- lint / typecheck：<结果>
- DB 迁移验证：<up → down 0007 → up，真实 PG>
- 验收证据：<多维表格实际行截图/记录 + 飞书消息回执；敏感字段脱敏>
- 变更预算实际值：<max_files / 生产行数 / 测试行数，与预算对照>
- 未解决风险：<或「无」>
- 是否偏离 TASK：<否 / 偏离项及原因>
- 规范影响结论：none
- spec_sync：clean
- verified_commit：<待提交后回填>
- **关闭门禁（四条件全满足方可关闭）**：① 测试通过；② 规范影响 none；③ spec_sync clean；④ verified_commit 真实 sha。

## 关联
- Change Request：无（已批准 R13/R14/R21 的实现）
- 前置外部依赖：飞书自建应用（App ID=`[飞书AppID已脱敏]`，权限已开；App Secret 待用户提供，仅运行时 env）
- 多维表格：base_token=`Z3TubDheZaYpfcsySDecWqXcnlg` / table_id=`tbl6439HzzrFfW4Y`（2026-08-18 已建模板，字段经用户确认）
- 相关既有：`TASK-M3-WORKER-SMTP-TEST`（SMTP 真发信已闭合，本任务复用 Outbox/EmailSender）
