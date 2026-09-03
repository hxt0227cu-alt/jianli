# Contributing

欢迎对本项目提交 Issue、改进建议与 Pull Request。为保证质量与可审计性，本项目采用**任务驱动 + 双角色审查 + 门禁收口**的治理流程，请遵循以下约定。

## 行为准则

- 保持建设性、尊重他人；
- 所有讨论默认使用简体中文（代码、命令、契约字段可保留英文）；
- 涉及安全问题的报告请走 [SECURITY.md](SECURITY.md) 私密渠道，勿公开披露。

## 开发流程（任务驱动）

1. **先有任务，再改代码。** 本仓库遵循「无任务单不得修改仓库」的硬约束。提交变更前，先在 `tasks/` 下按 `tasks/TASK-TEMPLATE.md` 创建任务单，明确：目标 / 非目标 / 允许与禁止修改路径 / 已批准的 DB·API·依赖变更 / 变更预算 / 验收标准。
2. **规格先行。** 改变用户可观察行为的变更，必须先走 Change Request 更新并 approve 规范（`docs/baseline.yml` 为唯一真相源），再创建实现任务；规格变更、测试期望变更与业务实现**不得在同一提交中混做**。
3. **双角色审查。** 实现与审查分离：实现者只做任务范围内改动；审查者独立核查越界、新依赖、重复实现、安全边界、测试真实覆盖。
4. **测试先锁定。** 先固定冻结验收测试（契约 / 安全 / 缺陷复现 / TC 用例），实现过程不得改宽断言、不得用 mock 降级集成、不得 skip 绕过。
5. **证据收口。** 任务完成后回填任务单「交付证据」章节（commit / 测试结果 / 迁移验证 / 门禁实际值），未填写完整不视为完成。

## 提交规范

- 分支命名：`<domain>/<task-id>`（如 `codex/task-booking-001`）；
- 提交信息：`<type>(<scope>): <summary>`（type：feat / fix / test / docs / refactor / chore），中文或英文均可；
- 一个提交只做一件事，保持可回溯。

## 质量门禁（提交前自检）

```bash
# 后端
cd apps/api
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest -q

# 前端
cd apps/web
pnpm typecheck && pnpm test && pnpm build

# 迁移校验（需真实 PG）
JIANLI_TEST_DATABASE_URL=... python -m pytest tests/migrations -v
```

CI 串行门禁 `backend-agent → rag-integration → web-delivery` 见 `.github/workflows/agent-quality-gate.yml`。

## 数据与密钥红线

- **严禁**提交任何真实密钥、API Key、授权码、`.env*`（`.env.prod.example` 模板除外）、个人联系方式与平台凭据；
- 涉及数据库、鉴权、加密、外部通知、Prompt 与工具权限、基础设施的变更默认需人工审批；
- 提交前请运行一次敏感信息扫描（可参考仓库 CI 中的密钥扫描步骤）。

## 文档

- 项目当前状态见 `PROJECT_STATE.md`，规范唯一真相源见 `docs/baseline.yml`；
- AI 编码协作的完整约束见 `AGENTS.md`（对人工贡献者同样适用）。
