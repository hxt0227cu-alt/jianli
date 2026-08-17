# TASK-MAINT-GITIGNORE-001 忽略本地验证/构建临时产物

> 将 verify.sh / 前端 build / 评测脚本运行产生的临时产物加入 `.gitignore`，避免被误提交污染仓库历史。属仓库卫生（chore），不改变任何交付物或生产代码。

## 任务类型
- chore  # 仓库卫生：忽略规则、目录整理等非功能改动

## 目标
在 `.gitignore` 追加「本地验证 / 构建产物」分组，覆盖当前未跟踪的验证/构建临时文件：
- `_diag_verify.log`
- `scripts/_verify_rc.txt`
- `scripts/_verify_run*.log`
- `scripts/_tmp_test_parser.py`
- `scripts/fact_consistency_results.json`
- `tsconfig.tsbuildinfo`
- `apps/web/dist-check/`
- `typescript-typescript-win32-x64-7.0.2.tgz`

使 `git status` 不再把这些非交付产物列为未跟踪项；真实交付文件（如 `apps/web/public/resume.md`、`docs/page2-*.md`、`scripts/measure_cost.py`、`scripts/record_pit.py`）**不**在此任务范围内，保持未跟踪待单独归拢。

## 非目标（明确排除）
- 不提交任何真实交付文件
- 不改动生产业务代码、测试、配置语义
- 不新增/修改任务范围外的 `.gitignore` 条目

## 允许修改路径
- `.gitignore`
- 本任务单 `tasks/TASK-MAINT-GITIGNORE-001.md`

## change_budget
- max_files: 2
- 生产代码行数：0

## 验收标准
- `git status --porcelain` 中不再出现上述 8 个临时产物路径（已被忽略）
- 不引入新的未跟踪交付文件

## 状态
- status: completed
- 创建 commit: 43a76a155bd1797e383613871d2b2a790e8fce22
- verified_commit: 43a76a155bd1797e383613871d2b2a790e8fce22
- 验收：8 个临时产物路径现已全部被 .gitignore 覆盖，`git status` 不再列为未跟踪项
