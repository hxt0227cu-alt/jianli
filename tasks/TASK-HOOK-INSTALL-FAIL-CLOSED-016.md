# TASK-HOOK-INSTALL-FAIL-CLOSED-016 Git hook 安装原子失败

> 状态：In Progress（2026-08-31）。上线门禁审查发现 hook 安装器在复制/权限/缺源失败后仍可能返回 0。

## 基线与范围
- baseline：PRD 2.3.6 / SRS 1.9 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`
- 引用：`AGENTS.md` §7～§8、`docs/test/test-plan.md` §1/§4
- 允许修改：`scripts/install-hooks.sh`、本任务单。
- DB/API/依赖变更：无。

## 目标与非目标
- 任一目录创建、复制、chmod、源缺失、内容或可执行位验证失败均非零退出。
- 通过 `git rev-parse --git-path hooks` 支持普通 clone、worktree 与 `core.hooksPath`。
- 安装器自身在 Linux clone 中记录为 `100755`；受控 `pre-commit` 源可保持普通文件，安装时统一赋予执行位。
- 不改变 hook 触发范围、测试内容、业务、API、DB 或依赖。

## 禁止修改路径
- 除上述两个允许路径外的业务、测试、部署、规范、依赖与 Git 配置。

## 规范影响评估
- behavior_change：false；affected_specs：none；仅修复门禁安装 fail-open。

## 验收与预算
- `bash -n scripts/install-hooks.sh`
- `bash scripts/install-hooks.sh`
- `cmp -s scripts/git-hooks/pre-commit .git/hooks/pre-commit && test -x .git/hooks/pre-commit`
- `cmp -s scripts/git-hooks/pre-push .git/hooks/pre-push && test -x .git/hooks/pre-push`
- `git ls-files --stage scripts/install-hooks.sh` 显示 `100755`
- max_files：2；expected_test_lines：≤25；expected_doc_lines：≤45。

## 安全与性能验收
- 不跟随仓库外任意用户输入路径；目标路径仅来自当前 Git 仓库配置。
- 仅复制两个小型 hook，无网络、数据库或可感知性能影响。

## 强制停止条件
- 需要修改 hook 内容、业务契约、依赖、Git 全局配置或超出预算。

## 回滚与交付证据
- 回滚：回退安装器；已安装副本可重新执行旧安装器覆盖。
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：Shell 语法代替，待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
