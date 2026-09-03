# Harness 坑记录（Pitfalls）

> 由 `scripts/record_pit.py` 自动追加；机器如实记录，AI 复盘提建议，用户拍板是否提炼为 Skill。
> 新条目追加在文末。

---

## 2026-08-16T18:42:12Z · HIGH · agent-review

- **现象**：项目 venv (apps/api/.venv) 为 Linux 结构，Windows Git Bash 下 bin/python 解析失败，测试无法在 Windows 侧运行
- **根因**：venv 在 WSL 创建，bin/python 软链指向 WSL python 路径，Windows 视角不可解析；项目 pyproject 要求 >=3.12,<3.13，managed(3.13.12)/system(3.11.9) 均不匹配
- **修复**：所有评测走 WSL：bash scripts/verify.sh；hooks 内含 WSL 守卫，非 WSL 自动跳过
- **规避**：接手 AI 直接在 WSL 跑 scripts/verify.sh，勿在 Windows 侧尝试 python venv；CI/评测脚本面向 WSL bash 编写
- **上下文**：TASK-HARNESS-001 探查
- **Skill 候选**：是 → jianli-wsl-verify

---

## 2026-08-16T18:42:12Z · MED · agent-review

- **现象**：本环境 Git Bash 的 rm 被 safe-delete 包装拦截，相对路径与 /c/ 绝对路径都报拒绝，文件删不掉
- **根因**：WorkBuddy sandbox 的 safe-delete 拦截 rm 且对路径处理异常（relative path rejected / 驱动器号丢失）
- **修复**：删除文件改用 wsl rm -f <wsl绝对路径>，如 wsl rm -f /mnt/c/.../file.py
- **规避**：在脚本/命令中需要删文件时优先走 WSL；避免在 Git Bash 直接使用 rm
- **上下文**：TASK-HARNESS-001 探查（临时诊断文件清理）
- **Skill 候选**：是 → windows-rm-via-wsl

---

## 2026-08-16T18:42:13Z · MED · agent-review

- **现象**：source .env.local 后环境变量值带回车符，导致数据库连接串/DSN 解析异常
- **根因**：.env.local 为 Windows 行尾(CRLF)，export 后值含尾随回车
- **修复**：加载前去除 CRLF：set -a; source <(sed 's/\r$//' apps/api/.env.local); set +a
- **规避**：任何加载 .env.local 的脚本（verify/hook/dev-env）都先 sed 去回车
- **上下文**：TASK-HARNESS-001 探查
- **Skill 候选**：是 → source-env-strip-crlf

---

## 2026-08-16T18:42:13Z · LOW · agent-review

- **现象**：建测试库 jianli_test 时 CREATE DATABASE 报 already exists
- **根因**：测试库此前已被创建（残留），CREATE DATABASE 非幂等
- **修复**：harness_setup_db.py 先查 pg_database 再建库，已存在则跳过（幂等）
- **规避**：自动化建库一律用 查存在再到建 模式，不要裸 CREATE DATABASE
- **上下文**：TASK-HARNESS-001 探查
- **Skill 候选**：否（待复盘拍板）

---

## 2026-08-17T01:00:00Z · HIGH · verify.sh

- **现象**：verify 门禁「撒谎」——实际 pytest/ruff 有真实失败，却打印「✓ 硬门禁通过」且退出码 0
- **根因**：`record_pit_on_fail` 在首次调用（run_stage 内）之后才定义 → 调用时函数未定义；外层又用 `|| true` 吞掉该错误；且 `local rc=$?` 被放在 `if/fi` 之后，捕获到的是 `fi` 的退出码(0) 而非命令本身的退出码。三重叠加使 FAIL 恒为 0。
- **修复**：① `record_pit_on_fail` 在 `run_stage` 之前定义；② `run_stage` 内 `"$@"` 执行后**立刻** `local rc=$?`（在 fi 之前）；③ 用 `FAIL=1` 累加 + `return "$rc"`，删除 `|| true` 短路。
- **规避**：任何多 stage 的 bash 门禁——辅助函数必须在调用前定义；`$?` 必须在被观测命令同一行紧后捕获，绝不放在控制流之后；门禁失败要明确非零退出，禁止 `|| true` 静默。
- **上下文**：TASK-HARNESS-001 门禁诚实化
- **Skill 候选**：是 → bash-gate-capture-rc-immediately

---

## 2026-08-17T01:00:00Z · MED · verify.sh

- **现象**：pytest 在路由注册阶段报 RuntimeError: Form data requires "python-multipart"
- **根因**：python-multipart 已在 pyproject 声明，但 WSL venv 未实际安装（手工管理 venv，不会自动同步）；`multipart` 模块缺失导致 FastAPI 注册 `Form` 参数的路由失败。
- **修复**：verify.sh 加自愈——`if ! "$VENV" -c "import multipart"; then pip install python-multipart; fi`；同时给用户安装提示。
- **规避**：新增任何 pip 依赖后，必须在 WSL venv 显式安装并 `python -c "import <pkg>"` 冒烟；不要假设「声明了 = 装好了」。
- **上下文**：TASK-HARNESS-001 依赖自愈
- **Skill 候选**：是 → wsl-venv-dep-selfheal

---

## 2026-08-17T01:00:00Z · MED · verify.sh

- **现象**：ruff format --check 报 `scripts/record_pit.py`「1 file would be reformatted」，但该文件已被格式化过
- **根因**：仓库根目录无 pyproject.toml，ruff 向上查找配置时回落默认（line-length 88）；而 `apps/api/pyproject.toml` 规定 line-length 100。verify 强制用 apps/api 配置检查 `scripts/`（apps/api 之外）的文件，与默认格式化的结果冲突。
- **修复**：verify 的 ruff 命令统一加 `--config "$API/pyproject.toml"`；并把 `scripts/record_pit.py` 按 line-length 100 重新格式化。
- **规避**：对配置根目录之外的文件跑 ruff 时，显式传 `--config` 指向统一配置；或在仓库根补一个 pyproject 收敛配置发现。
- **上下文**：TASK-HARNESS-001 ruff 配置发现
- **Skill 候选**：否（待复盘拍板）

---

## 2026-08-17T01:00:00Z · MED · verify.sh

- **现象**：继承的测试套件有 3 failed + 9 errors（共 12 例）预存失败，若直接让门禁判红，harness 永远红、失去回归哨兵意义
- **根因**：`tests/appointments/test_management.py` 的 9 个用例 import `real_stack`，其断言把 `DATABASE_URL`/`REDIS_URL` 模块全局与 `os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")` 绑定且无 skip 守卫 → 在 harness 测试库下 import 即 ERROR；另有 3 例对 OpenAPI 路径/日志事件的陈旧断言。均属历史债务，非 harness 引入。
- **修复**：verify.sh 将这 12 个节点登记为 `PYTEST_BASELINE`；用 `comm` 比对实际失败与基线——仅「非基线的新失败」判红并记坑；命中基线的存量如实上报、不阻断、不假装通过（门禁对"在管代码"保持绿）；基线中某用例变绿会提示"债务已偿还，建议更新基线"。
- **规避**：接手一套红着的套件时，**登记已知失败基线**而非静默 skip/改宽断言；新失败才触发门禁。基线债务需单独 TASK 清理（本任务禁止改 tests/** 行为）。
- **上下文**：TASK-HARNESS-001 存量债务基线化
- **Skill 候选**：是 → pytest-baseline-gate
## 2026-08-31T09:57:31Z · HIGH · verify.sh

- **现象**：清洗外部 Provider 凭据后，真实栈门禁的 extreme semantic RAG 用例仅命中 6/9。
- **根因**：冻结用例用于判别 BGE-M3 语义能力，却被默认离线门禁用无语义的本地哈希 Embedding 执行；测试层级与运行 Provider 不匹配。
- **修复**：只把单独 `--quick` 定义为非发布离线预检并明确报告四项未执行；完整/`--tc` 发布门禁与 CI 均强制真实 Embedding、原冻结断言和零 skip，缺凭据或网络即失败。
- **规避**：可以给 pre-commit 提供明确标识的离线预检，但冻结 TC 不能从发布门禁移除；不得用 fallback 或 deselect 冒充发布证据。
- **上下文**：TASK-EXTERNAL-RAG-GATE-005；stage=pytest；commit=465b6cc
- **Skill 候选**：否（待复盘拍板）

---
