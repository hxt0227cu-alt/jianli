# TASK-REVIEW-BOOKING-001 预约创建独立审查

## 任务类型
- review

## 状态
- Planned；仅在 TASK-BOOKING-001 获得用户加密实施批准并产生固定实现 commit 后开始。

## 审查对象
- TASK-BOOKING-001 的最终固定实现 commit（待回填；审查不得以工作区浮动状态替代）。

## 审查范围
- 越界：新增 DB/API/依赖/鉴权/加密策略是否逐项位于 TASK-BOOKING-001 已批准章节。
- 实现真相：逐字段对照 migration `0001`～`0003`，不得用领域文档推断数据库实际存在。
- 事务：Company → Exception → Slot 升序锁；锁后复检；Appointment/3 Slot/2 Event/AuditLog 原子提交；事务内无外部调用。
- 并发：TC-APT-003 使用真实 PostgreSQL 两个独立连接，至少 10 轮，仅一方成功且失败方无副作用。
- 安全：Cookie/CSRF/Origin/RBAC、Redis fail closed、AES-GCM envelope/AAD/nonce、key ring、独立 HMAC、确认 token 绑定与过期、日志脱敏。
- 契约：只实现 approved OpenAPI 0.2；错误码/Problem media type/status 不漂移。
- 依赖：只新增用户批准的精确 `cryptography` 及必要传递依赖；无重复抽象、未使用代码或未来功能空壳。
- 测试：冻结 TC-APT-001～003、TC-AUTH-006/008、TC-SEC-001～004 未被改宽、skip 或 mock 化。

## 允许修改路径
- `tasks/TASK-REVIEW-BOOKING-001.md`（只回填审查证据）

## 禁止修改路径
- 所有生产代码、测试断言、migration、规范与 baseline；发现问题只报告给实现角色向前修正。

## 审查输出
- P0/P1/P2 findings（文件/行号/复现证据）；无发现时明确写 0。
- 固定被审查 commit、测试环境、命令与结果。
- 复核修正 commit 后给出 PASS/FAIL；不得代替用户批准加密或生产操作。

## 交付证据
- reviewed_commit：待回填
- reviewer：待建立独立审查窗口
- findings：待回填
- frozen tests：待回填
- result：Planned
