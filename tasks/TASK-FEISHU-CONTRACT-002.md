# TASK-FEISHU-CONTRACT-002 实现 updateOwnerContactConfig（R13 open_id 配置入口）

> **状态：draft（待用户批准后实现）**
> 实现已批准 OpenAPI v0.3 的 `updateOwnerContactConfig`（CR-FEISHU-OPENID-001 已批准）：admin 配置候选人飞书 open_id，AES-256-GCM 加密落 `owner_contact_configs.candidate_feishu_open_id_ciphertext`，解锁 R13 候选人飞书消息真发。

## 任务类型
- implementation  # 实现：功能编码（后端端点 + 前端输入框 + 测试）

## 基线版本与基线 commit
- baseline：SRS 1.3 / 领域模型 1.1.5 / architecture 0.2 / security 0.1 / OpenAPI **0.3**（均 approved，取自 `docs/baseline.yml`）
- 基线 commit：<本任务创建时 master HEAD，待回填>

## 精确规范引用（AI 只读取这些章节）
- `docs/api/openapi.yaml` §`/admin/owner-contact-config`（operationId=`updateOwnerContactConfig`，契约真相源）
- `docs/design/domain-model.md` §6.1（`uq_active_owner_admin`：至多一个未删除 owner_admin；运行不变量）
- `docs/design/domain-model.md` §6.12（`candidate_feishu_open_id_ciphertext`：AES 密文、收件人解析链路）
- `docs/design/security.md`（AES-256-GCM 字段加密 AAD 约定、owner_admin RBAC、CSRF）
- 既有实现参考：`apps/api/app/admin/router.py`（`admin_owner` CSRF 模式）+ `apps/api/app/appointments/crypto.py`（FieldCipher 加解密）

## 需求来源
- R13（双通道提醒，UC-12）+ 已批准 CR-FEISHU-OPENID-001

## 目标
1. **后端**：`PUT /admin/owner-contact-config` 端点（owner_admin + CSRF），对唯一活跃 owner_admin 的 `owner_contact_configs` 行 upsert `candidate_feishu_open_id_ciphertext`（AES-256-GCM，AAD=`owner_contact_configs`/`candidate_feishu_open_id_ciphertext`/config 行 id）；无活跃 owner_admin → default Error + 运维告警（不任选顶替，领域模型 §6.1）
2. **前端**：admin 页加候选人飞书 open_id 输入框（保存调新端点）
3. **测试**：真实 PG/Redis 集成测试（配置成功 upsert / 加密落库可解密回读 / 无 owner_admin 报错 / 非 owner_admin 403）

## 非目标（明确排除）
- 不改 R13 消息发送语义、不改 worker 投递链（已闭环）
- 不新增其它配置字段（candidate_phone_ciphertext 等后续再说）
- 不新增公开（非 admin）端点、不改其它契约 operation
- 不做 open_id 格式远程校验（飞书 API 校验属可选增强，本轮不做）

## 允许修改路径
- `apps/api/app/admin/router.py`（新增端点 + `OwnerContactConfigInput` 模型）
- `apps/api/app/admin/models.py`（请求/响应 pydantic 模型）
- `apps/api/app/appointments/service.py`（或 admin service：`update_owner_contact_config` 方法——含 FieldCipher 加密 + upsert SQL；**优先新增方法不重构既有逻辑**）
- `apps/api/app/auth/repository.py`（如需 `find_active_owner_admin` 复用——已有 `_find_active_owner_admin` 在 worker.py，抽到共享位置或复制到 admin 侧时评估复用）
- `apps/api/tests/admin/test_owner_contact_config.py`（新测试）
- `apps/web/main.tsx` / admin 视图组件（飞书 open_id 输入框；若 admin 前端在 `apps/web/` 单文件则内联）
- `tasks/TASK-FEISHU-CONTRACT-002.md`（本任务单）

## 禁止修改路径
- `docs/**`（契约/规范已批准，实现不改；OpenAPI v0.3 只读）
- `apps/api/migrations/**`（无新迁移；0001 已建表）
- `apps/api/app/notifications/**`（worker/feishu/email 已闭环不动）
- `apps/api/app/aiqa/**`、`apps/api/app/appointments/router.py`（预约公开端点）

## 已批准的 DB / API / 依赖变更
- **API**：`updateOwnerContactConfig`（OpenAPI v0.3，已批准）
- **DB**：无新迁移（`owner_contact_configs` 0001 已建，含 `candidate_feishu_open_id_ciphertext` 列）
- **依赖**：无新增（复用 httpx/FieldCipher/既有栈）

## 规范影响评估（spec impact）
- behavior_change：**true**（新增用户可观察行为）——但**已走 CR 前置**（CR-FEISHU-OPENID-001 已批准，OpenAPI v0.3 approved）
- affected_specs：openapi=none（实现已批准 v0.3）/ srs=none / domain_model=none / security=none / test_plan=none
- reason：契约先行已批准，本任务仅实现，规范不因本任务过期
- 分类：**已批准行为的实现 → 不需要改规范；更新测试/交付证据即可**

## 功能验收
- 配置成功：`PUT /admin/owner-contact-config {"candidate_feishu_open_id":"ou_xxx"}` → 200 `{"configured": true}`；再次 PUT 更新值 → 行更新（upsert）
- 加密落库：`candidate_feishu_open_id_ciphertext` 为 AES 密文（非明文），可经 FieldCipher 解密回读原文
- 无活跃 owner_admin → default Error（500 语义）+ 日志告警，不静默成功
- 非 owner_admin 角色调用 → 403
- 未登录/无效会话 → 401；写操作无 CSRF → 403

## 安全与隐私验收
- open_id 明文仅请求体传输，落库 AES-256-GCM；日志脱敏（不打印 open_id）
- owner_admin RBAC + CSRF（同现有 admin 写端点）
- 复用既有 FieldCipher（密钥环/AAD 约定不变）

## 性能验收
- 单行 upsert，无外部调用（无网络往返），P95 无压力

## 变更预算（change_budget）
- max_files：6
- expected_prod_lines：≤ 180（router 端点 + service 方法 + models）
- expected_test_lines：≤ 250

## 必须运行的测试命令
- `pytest tests/admin/test_owner_contact_config.py -v`（WSL 真实 PG/Redis）
- `pytest tests/test_feishu.py tests/test_worker.py -v`（回归，不破坏既有 8 passed）
- `ruff check apps/api` / `mypy apps/api` / `python -m py_compile` 改动文件
- 前端：`npm run build`（WSL，若改前端）

## 回滚方法
- 移除 admin router 端点注册 + 前端输入框（无迁移、无数据依赖；已写入的密文保留无副作用）

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 契约与实现不一致（如响应码/字段偏离 OpenAPI v0.3）→ 停止
- 需要新迁移/依赖/公开端点 → 停止报告
- 超出 change_budget → 拆任务

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<待提交后回填>
- 修改文件清单：<与「允许修改路径」逐一对照>
- 测试命令及结果：<命令> → <pass/fail 数>
- lint / typecheck：<结果>
- DB 迁移验证：无
- 验收证据：<配置成功响应 + 密文落库核对 + 前端输入框截图>
- 变更预算实际值：<max_files / 生产行数 / 测试行数>
- 未解决风险：<或「无」>
- 是否偏离 TASK：<否 / 偏离项及原因>
- 规范影响结论：none
- spec_sync：clean
- verified_commit：<待提交后回填>
- **关闭门禁（四条件）**：① 测试通过；② 规范影响 none；③ spec_sync clean；④ verified_commit 真实 sha。

## 关联
- Change Request：`docs/change-requests/CR-FEISHU-OPENID-001.md`（已批准）
- 前置：OpenAPI v0.3 approved；候选人 open_id=`[open_id已脱敏]`（用户，真连验证用）
- 完成后：R13 候选人飞书消息端到端真连验证（TASK-FEISHU-001 遗留风险闭合）
