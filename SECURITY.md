# Security Policy

## Reporting a Vulnerability

发现安全问题时，**请不要**通过公开 Issue 披露。

请将问题通过以下任一私密渠道提交：

- GitHub Security Advisory（本仓库 → Security → Report a vulnerability）
- 或通过仓库维护者的公开联系方式私下联系

请包含以下信息以便快速复现与定位：

- 影响模块（auth / appointments / aiqa / notifications / admin）
- 复现步骤与最小样例（POC）
- 影响的版本 / commit
- 预期的安全边界 vs 实际行为

我们将尽快确认并在修复后同步致谢。

## Security Posture

本项目在设计上采用纵深防御，且仓库治理对安全边界实行**只收紧、不放宽**的硬约束：

| 领域 | 机制 |
|------|------|
| 凭据管理 | 所有密钥（HMAC / 字段加密 / API Key / SMTP / 飞书）运行时注入，不入库；仓库仅含脱敏模板 |
| 数据保护 | 敏感字段 AES-256-GCM 逐列加密；公司名指纹去重；字段加密密钥环支持轮换 |
| 认证与会话 | 邮箱验证码、密码哈希、记住我令牌哈希存储、CSRF 令牌、登录/注册限频 |
| 授权 | RBAC（visitor / interviewer / owner_admin），Agent 工具白名单 + 服务端校验，越权 403 |
| 输入防护 | CORS 白名单、Origin/Referer 校验、Prompt 注入防护、上传类型与大小限制（10MB）、恶意文件拒收 |
| 模型边界 | 无依据拒答（offtopic），模型不得越权调用白名单外工具，不编造个人经历 |
| 供应链 | CI 依赖漏洞扫描、锁定文件（requirements.lock / pnpm-lock.yaml）、镜像精简 |
| 审计 | 关键写操作同事务写审计日志；Outbox 投递幂等、失败可重试可回收 |

## Security-sensitive Change Gate

涉及以下范围的变更默认要求人工审批，且不得通过普通 PR 绕过：

- 数据库迁移
- 认证 / 鉴权 / 加密策略
- 外部通知（SMTP / 飞书）
- Prompt 与 Agent 工具权限
- 基础设施（部署 / 网络 / 凭据注入）

详见 [docs/design/security.md](docs/design/security.md) 与 [docs/baseline.yml](docs/baseline.yml)。

## 已知边界（Known Limitations）

- 公开问答限频为进程内固定窗口实现，多实例部署需迁移至 Redis（见 `docs/api/sse.md`）。
- 知识库对象存储为本地磁盘，生产环境建议挂载或替换为 S3/COS 后端。
