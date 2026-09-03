# TASK-NODE-LOCK-SYNC-010 Web 直接依赖与 pnpm 工具链锁定

> 状态：In Progress（2026-08-31）。上线审查发现 `package.json` 直接依赖均使用 `latest`，且 CI/生产 pnpm 主版本不一致；用户已授权修复全部上线阻塞。

## 任务类型
- dependency metadata / build reproducibility
## 基线版本与基线 commit
- baseline：PRD 2.3.6 / SRS 1.9 / architecture 0.6 / security 0.5 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`
## 精确规范引用
- `docs/test/test-plan.md` §1、§2.9 / TC-OPS-004、TC-SEC-007、§4
- `pnpm-lock.yaml` 根 importer
## 目标
- 将 `package.json` 的既有直接依赖从 `latest` 对齐为当前 lock 已解析的精确版本，不升级或增删包。
- 增加 `packageManager=pnpm@9.15.9`，与生产 Web 构建镜像一致；CI 同步使用 9.15.9。
- 同步 lock 根 importer 的 specifier，使 `--frozen-lockfile` 保持可用。
## 非目标
- 不联网解析、安装或升级依赖；不新增扫描器、SBOM 工具、Action 或业务代码。
- 不改变 Node 运行时主版本、前端行为或测试断言。
## 允许修改路径
- `package.json`
- `pnpm-lock.yaml`
- `.github/workflows/agent-quality-gate.yml`（仅 pnpm 版本）
- `tasks/TASK-NODE-LOCK-SYNC-010.md`
## 禁止修改路径
- `apps/**`、测试代码、Dockerfile、API、DB、规范与其他 CI 步骤。
## 已批准的 DB / API / 依赖变更
- DB：无。API：无。
- 依赖集合与解析版本：无变化；仅把 lock 中现有版本写回 manifest/specifier。
- 构建工具：pnpm 统一为现有生产值 9.15.9。
## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：依赖元数据与同一不可变 Web 制品构建工具对齐。
## 验收
- package.json 每个 direct dependency/devDependency 均为精确 semver，且等于 lock importer 的解析版本。
- lock importer 不含 `specifier: latest`；CI 与 `packageManager`/生产镜像均为 pnpm 9.15.9。
- `pnpm install --frozen-lockfile --offline`（缓存允许时）、test/typecheck/build 通过。
## 变更预算
- max_files：4
- expected_prod_lines：≤20
- expected_test_lines：0
- expected_doc_lines：≤60
## 回滚
- 回退本任务四个路径；不删除 node_modules 或缓存。
## 强制停止条件
- 需要改变解析版本/依赖集合、联网获取包、修改业务或超出预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 变更预算实际值：待回填
- 未解决风险：镜像/Action digest 与漏洞扫描/SBOM 仍由供应链任务承接
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
