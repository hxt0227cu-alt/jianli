# TASK-RELEASE-REPAIR-001 上线前完整修复与本地验收

> 状态：In Progress（2026-08-26）。用户明确授权处理当前已识别的全部发布修复，不限于最小 PDF 测试改动。

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.6 / SRS 1.5 / OpenAPI 0.6
- 基线 commit：`ac0f087`

## 精确规范引用
- `docs/requirements/PRD.md` §4.9.1
- `docs/requirements/SRS.md` 已批准的认证、AIQA、管理端行为
- `docs/api/openapi.yaml` 现有 operationId（只消费，不修改契约）
- `TASK-ADMIN-QA-OBSERVABILITY-001`
- `TASK-AUTH-RESEND-001`
- `TASK-SLOT-MATERIALIZE-001`
- `TASK-TEST-WEB-RESUME-001`
- 用户于 2026-08-26 对“所有当前发布修复”的显式授权

## 需求来源
- 上线前硬阻塞清理、真实 PDF iframe 验收、管理端客观可观测性、人格诚实性、全量代码门禁和 WSL 本地演示。

## 目标
完整修复当前已识别的发布问题：恢复经过审查的前端体验与 PDF iframe，保留客观管理端指标，改善数字分身口语表达且不得隐藏局限，修通全量 lint/typecheck/test，并给出可复现的 WSL 本地验收入口。

## 非目标
- 不新增产品需求、公开 API、数据库 schema、外部依赖或第三方基础设施。
- 不恢复 `quality_score` 或任何主观硬编码质量评分。
- 不加入“主动隐藏项目局限”的人格门控。
- 不安装或使用 Docker Desktop；Docker 仅使用 WSL Ubuntu-24.04 内原生 Docker。
- 不执行生产域名、DNS、证书和真实生产数据迁移。

## 允许修改路径
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`
- `apps/api/app/aiqa/content.py`
- `apps/api/app/aiqa/persona.py`
- `apps/api/app/aiqa/retrieval.py`
- `apps/api/tests/aiqa/test_aiqa.py`
- `apps/api/tests/aiqa/test_persona_style.py`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `scripts/seed_kb.py`
- `scripts/dev-env.sh`
- `tasks/TASK-RELEASE-REPAIR-001.md`
- `tasks/TASK-TEST-WEB-RESUME-001.md`
- `tasks/TASK-ADMIN-QA-OBSERVABILITY-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- 数据库迁移、公开 API 契约、依赖清单、鉴权/加密策略。
- `apps/web/public/resume.pdf`（本任务不猜测两个二进制版本谁更新；保留当前已追踪版本）。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false（恢复已批准/已有行为，修复展示、测试与工程门禁）
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：当前实现与已批准任务及真实 iframe 验收不一致；本任务使实现回到批准基线，并进行非契约 UI/措辞修复。

## 功能验收
- 简历页使用 `/resume.pdf` 的可访问 iframe，并在加载前显示提示。
- 非问答页面不展示无效聊天栏；登录态刷新与退出可正常工作。
- 管理端仅展示 `grounded`、`citations_count`、`latency_ms` 等客观事实，不出现 `quality_score`。
- 数字分身保持口语化、证据优先，遇到局限类问题如实回答且不得主动藏拙。
- 全量 Ruff、Mypy、前端测试/typecheck/build 与相关真实数据库回归通过。

## 安全与隐私验收
- 不打印验证码、不放宽 CSRF/RBAC/限频，不输出密钥。
- 管理端与会话可观测字段沿用现有 owner_admin 权限边界。

## 性能验收
- 本任务不改变性能 SLO；前端构建产物成功，后端回归无新增慢路径。

## 变更预算
- max_files：16
- expected_prod_lines：≤650
- expected_test_lines：≤160

## 必须运行的测试命令
- `cd apps/api && .venv/Scripts/python.exe -m ruff check .`
- `cd apps/api && .venv/Scripts/python.exe -m mypy app`
- `cd apps/api && .venv/Scripts/python.exe -m pytest tests/aiqa tests/auth tests/admin tests/appointments/test_slot_materializer.py -q`
- 在 WSL 原生 Docker 提供 PG/Redis 后运行相关真实栈测试。
- `npm test`
- `npm run typecheck`
- `npm run build`
- 启动 `scripts/dev-env.sh` 并完成浏览器本地烟测。

## 回滚方法
- `git revert` 本任务实现提交；无数据库迁移需要回滚。

## 强制停止条件
- 若需新增依赖、DB/API/鉴权变化，立即停止并单独走 Change Request。
- 若遇网络问题，按用户要求停止并报告，不长时间盲目重试。
- 若超过变更预算或冻结验收仍失败，停止并拆分。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无新增迁移；既有迁移回归待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 关闭门禁：In Progress

## 关联
- `TASK-ADMIN-QA-OBSERVABILITY-001`
- `TASK-TEST-WEB-RESUME-001`
