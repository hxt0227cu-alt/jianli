# TASK-PYTHON-LOCK-SYNC-009 Python 已批准依赖锁同步

> 状态：In Progress（2026-08-31）。上线审查发现 requirements.lock 漏掉 pyproject 中两个既有 runtime pin；用户已授权修复上线阻塞。

## 任务类型
- dependency metadata maintenance

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / architecture 0.6 / security 0.5 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`

## 精确规范引用
- `docs/test/test-plan.md` §1、§2.9
- `apps/api/pyproject.toml` `[project].dependencies`

## 目标
- 将已批准且已在 pyproject/Dockerfile 使用的 `python-multipart==0.0.20`、`pypdf==6.15.0` 补入 Python 版本锁。

## 非目标
- 不升级/新增依赖，不生成 hash lock，不引入扫描器，不修改应用或构建行为。

## 允许修改路径
- `apps/api/requirements.lock`
- `tasks/TASK-PYTHON-LOCK-SYNC-009.md`

## 禁止修改路径
- pyproject、Dockerfile、应用、测试、API、DB、规范与其他依赖清单。

## 已批准的 DB / API / 依赖变更
- DB：无。API：无。依赖集合与版本：无变化，仅补齐既有 pin 的锁文件记录。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：依赖元数据与已批准实现对齐。

## 功能验收
- pyproject 的所有 `==` 直接依赖均在 requirements.lock 中具有相同版本。

## 安全与隐私验收
- 不读取/写入 secret；不联网解析或升级包。

## 性能验收
- 不适用（元数据同步）。

## 变更预算
- max_files：2
- expected_prod_lines：0
- expected_doc_lines：≤80

## 必须运行的测试命令
- Python 标准库解析：pyproject 直接 pin 是 requirements.lock 子集。
- `git diff --check -- apps/api/requirements.lock`

## 回滚方法
- 回退两条锁记录与任务单。

## 强制停止条件
- 需要改变版本/依赖集合、联网解析、修改构建行为或超出预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：锁文件无 hashes；供应链扫描/SBOM/digest pin 仍未实现
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
