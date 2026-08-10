# TASK-SEC-001 安全设计与 ADR review 草案

> 承载 architecture v0.2 批准后的安全设计。只产出 review 草案，不代签 approved，不进入 OpenAPI、测试计划或编码。

## 任务类型
- design

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 / UI 1.0 / architecture 0.2（均 approved）
- architecture approval_commit：`da3f6fc`

## 精确规范引用
- SRS §2.4 / §3.2 / §3.3 / §3.8 / §4.2 / §4.3 / §5.2 / §5.3 / §5.6 / §6.3 / §7 / §8
- PRD §8.4 / §8.7 / §8.9
- domain-model §1 / §6.1-§6.4 / §6.12 / §7
- architecture §1.1 / §6 / §7 / §9.1 / §10 ADR-ARCH-005~008 / §11

## 需求来源
- R2 / R7 / R9 / R16 / R19 / R20 / R21 / R26

## 目标
- 产出密码、会话、加密密钥、鉴权授权、限频、退信入口、LLM/RAG、日志审计和部署安全的唯一推荐方案与验收边界。

## 非目标
- 不修改已批准 SRS、领域模型、UI 或架构；不定义 REST/SSE Schema；不写代码或迁移；不购买云资源。

## 允许修改路径
- docs/design/security.md
- docs/baseline.yml
- tasks/TASK-SEC-001.md
- PROJECT_STATE.md

## 禁止修改路径
- docs/requirements/**
- docs/design/architecture.md / domain-model.md / ui-wireframe.md
- 任何代码、迁移、OpenAPI、测试计划

## 已批准的 DB / API / 依赖变更
- DB：无新增表/字段/索引；使用既有 User/AuthSession/token/AuditLog/NotificationDelivery 字段。
- API：无，本任务不定义公开契约。
- 依赖候选：Redis 仅用于跨实例限频计数；IMAP/SMTP/飞书/DeepSeek 均为已知外部集成。正式采用须由用户批准 security v0.1 后才对实现生效。

## 规范影响评估
- behavior_change：false
- affected_specs：SRS/domain_model/architecture 均 none；OpenAPI/test_plan 待下游吸收
- reason：将已批准安全行为落实为实现约束，不扩产品功能。

## 验收
- ADR-SEC-001~004 各有唯一推荐、理由、失败策略和重裁条件。
- 密码、令牌、Cookie、CSRF/CORS、RBAC、字段加密、密钥轮换、限频、退信、Prompt Injection、上传和日志边界完整。
- 不在文档、Git、日志写入任何真实密钥。

## 变更预算
- max_files：4
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 一致性检查：四个 ADR、baseline review 状态、无真实密钥、无未批准 Schema/API。

## 回滚方法
- `git revert` 本任务提交；无迁移、无运行时变更。

## 强制停止条件
- 需要新增未列明表/字段/API/依赖；与 SRS/架构冲突；将 security 标为 approved；开始编码。

## 交付证据
- commit / PR：`119d35f`（security v0.1 review 草案快照）
- 修改文件清单：docs/design/security.md / docs/baseline.yml / tasks/TASK-SEC-001.md / PROJECT_STATE.md
- 测试命令及结果：四项 ADR、敏感词/密钥边界、baseline security=0.1/review、未新增 Schema/API 检查 → pass
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：docs/design/security.md §1-§13
- 变更预算实际值：max_files=4，实际 4 文件，未超预算
- 未解决风险：外部 SMTP/IMAP、飞书、DeepSeek 与云 Secret Manager 配置待上线确认；security approval 尚未生成
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`119d35f`
- 状态：Review

## 关联
- 上游：TASK-ARCH-003
- 下游：OpenAPI/SSE 契约、测试计划
