# TASK-FACTORY-FIX-001 修复 create_app 在 runtime=None 时 appointments 未绑定

> 修复 `app/factory.py` 中 `appointments` 变量作用域缺陷：默认配置（无 auth）下
> `create_app` 触发 `UnboundLocalError`，导致 `tests/aiqa/test_aiqa.py` 整模块 11 例 ERROR。

## 任务类型
- bugfix

## 基线版本与基线 commit
- 基线 commit：`054e36b`（见 `git rev-parse HEAD`）

## 精确规范引用
- `app/factory.py` `create_app`（line 95 赋值 / line 110 引用）

## 需求来源
- 用户 2026-08-22 指令「先修复」（指 TASK-AIQA-AGENT-CRUD-001 交付证据中标注的
  `factory.py:110` `UnboundLocalError` 既有缺陷）。

## 根因
- `appointments` 仅在 `if runtime is not None:` 分支内赋值（line 95）。
- 当 `config.auth_configured=False`（默认 `Settings()`，无 env）时 `runtime=None`，
  `appointments` 永不绑定；line 110 `booking_service=appointments` 触发 `UnboundLocalError`。
- 影响：`tests/aiqa/test_aiqa.py` 在 collection/setup 阶段整模块抛 `UnboundLocalError`
  （11 例 ERROR，修复前）。

## 修复
- 在 `if runtime is not None:` 前初始化 `appointments = booking_runtime`（尊重显式入参；
  默认 `None`）。`runtime=None` 时 `appointments=None`，aiqa runtime 以
  `booking_service=None` 构建，与 DB-free 公开问答预期一致，**无行为回归**。

## 非目标（明确排除）
- 不改变「auth 未配置时不挂载预约/管理员 HTTP 路由」的既有行为。
- 不改变 `build_aiqa_runtime` 签名或 booking 集成语义。
- 不新增依赖 / schema / 公开 API。

## 允许修改路径
- `app/factory.py`

## 禁止修改路径
- 其它模块；auth/appointments/aiqa 行为不变。

## 已批准的 DB / API / 依赖变更
- 无 schema / API / 依赖变更。

## 规范影响评估
- behavior_change：**false**（纯缺陷修复，可观察行为不变）。
- affected_specs：none。
- reason：修复变量作用域 bug，不改任何契约。

## 功能验收
- `pytest tests/aiqa/test_aiqa.py -v` → **13 passed**（修复前 11 ERROR + 2 passed）。
- DB-free 全量子集无回归。
- 真栈（PG+Redis）层：`tests/aiqa/test_agent_crud.py` / `test_agent_booking.py` 4 个
  gated 用例转为实跑通过（用户 WSL 验收）。

## 安全与隐私验收
- 无加密/AAD/角色枚举变更。

## 性能验收
- `create_app` 仅多一次变量初始化，无额外 IO。

## 变更预算
- max_files：1（factory.py）；expected lines ~+1 / -0。

## 必须运行的测试命令
- `pytest tests/aiqa/test_aiqa.py -q`
- `ruff check app/factory.py`

## 回滚方法
- `git revert` 本任务提交即可，无 DB 迁移依赖。

## 强制停止条件
- 出现未列明变更 → 立即停报。

## 交付证据（任务关闭前必须填写）
- commit / PR：`7142212`（fix(api): 修复 create_app 在 runtime=None 时 appointments 未绑定）
- 修改文件清单：
  - `apps/api/app/factory.py`（line 94 前新增 `appointments = booking_runtime` 初始化）
- 测试命令及结果：
  - 本地 managed-Python `pytest tests/aiqa/test_aiqa.py -q` → **13 passed**（修复前 11 ERROR）✅
  - `ruff check app/factory.py` → **All checks passed** ✅
- lint / typecheck：ruff 全绿 ✅
- DB 迁移验证：无（无 schema 变更）
- 验收证据：DB-free `test_aiqa.py` 13 例全过；真栈层 gated 用例（test_agent_crud ×2 + test_agent_booking ×2）已用户 WSL 实跑全绿（2026-08-22）。
- 变更预算实际值：max_files 1 → 实际 1 ✅
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none（纯 bugfix）
- spec_sync：clean
- verified_commit：`7142212`
- 关闭门禁：① 测试通过 ✅（本地 + WSL 真栈全绿）；② 规范影响 none ✅；③ spec_sync=clean ✅；
  ④ verified_commit 已回填 ✅。

## 关联
- 前置发现：TASK-AIQA-AGENT-CRUD-001 交付证据中标注的 `factory.py:110` 既有缺陷。
