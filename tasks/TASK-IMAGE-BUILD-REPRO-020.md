# TASK-IMAGE-BUILD-REPRO-020 生产镜像构建输入可复现

> 状态：In Progress（2026-08-31）。从超预算的运维合并任务中按文件边界拆出；只处理构建上下文、精确 runtime closure 与 API/Web 镜像配方。

## 任务类型
- implementation / build infrastructure（不改变产品行为）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`

## 精确规范引用
- `docs/design/architecture.md` §9.1、§9.3
- `docs/design/security.md` §9、§12
- `docs/test/test-plan.md` TC-OPS-003、TC-OPS-004、TC-SEC-007

## 目标
1. API 镜像消费精确的生产 runtime dependency closure，使用 `--no-deps` 与 `pip check` 防止构建期漂移或不完整依赖图。
2. Web 镜像在隔离 build stage 使用 frozen pnpm lock 构建，再只复制静态产物到 Nginx runtime stage。
3. 根/API build context 排除 Git、虚拟环境、测试产物、运行数据、env、凭据和私钥；canonical seed 脚本显式进入 API 镜像。

## 非目标
- 不改变依赖集合/版本、业务、API、DB、权限、运行拓扑或供应链扫描策略。
- 不在本机首次拉取镜像/包；镜像 digest 与 CI 扫描由独立供应链任务承接。

## 允许修改路径
- `.dockerignore`
- `apps/api/.dockerignore`
- `apps/api/Dockerfile`
- `apps/api/requirements.runtime.lock`
- `deploy/Dockerfile.nginx`
- `tasks/TASK-IMAGE-BUILD-REPRO-020.md`

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：不新增或升级；只把 `pyproject.toml` 已批准的 15 个直接依赖及其精确传递闭包写入 production-only lock。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：使现有交付内容可重复构建，不改变用户可观察行为。

## 验收
- 15 个 `pyproject.toml` runtime exact pins 在 runtime lock 中精确一致；lock 无 dev 工具；现有环境 `pip check` 无破损依赖。
- Dockerfile 只消费 runtime lock/frozen pnpm lock，构建上下文不包含 `.env.local`、`.git`、`.venv`、`node_modules`、运行卷、备份和私钥。
- 首次联网窗口用 `docker build --pull` 构建 API/Web，容器以非 root 运行并完成 import/Nginx smoke；当前离线仅记录静态验证，不伪造镜像通过。
- `git diff --check`。

## 变更预算
- max_files：6
- expected_prod_lines：≤170
- expected_test_lines：0
- expected_doc_lines：≤80

## 回滚与强制停止
- 回滚：回退本任务六个文件；无数据回滚。
- 停止：依赖集合/版本变化、需要新包、业务/API/DB 变化、冻结验收失败或超预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用（构建/锁一致性验证代替）
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：首次联网镜像构建与 runtime smoke
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
