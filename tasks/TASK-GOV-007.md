# TASK-GOV-007 ruff / mypy 门禁 repo 级绿化（M1–M4 跨域，追认登记）

> 向前治理修正：`ruff check .` 与 `mypy` 两个工具门禁自 M1 起从未在 repo 级绿过（首次批量运行报 115 个 ruff error、随后 16 个 mypy error），其修复跨越 M1/M2/M3/M4 四个里程碑的文件，**不属于任何单一功能任务的授权路径**。
> 本任务**追认登记**已发生的两次先行提交（`665a067`、`b01acaf`）并承载第三次收口提交，如实记录路径逐条计数。不重写历史、不改 baseline、不改任何运行时行为契约。

## 任务类型
- governance（工具门禁绿化 / 无功能变更）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2（均 approved）；development_gate 全放行
- 基线 commit：`b77931e`（TASK-M4 功能实现快照，本任务在其之上收口）

## 缘起（如实记录，不美化）
1. 用户本机 WSL 首次运行验证批处理 `ruff check . && mypy && pytest ...` → ruff 报 **115 error** 且退出非 0，`&&` 短路导致 mypy / pytest **根本没有执行**。
2. 经 `git log` 核实，115 个 error 中绝大多数是 **M1–M3 既有债务**（`appointments/service.py`、`appointments/sse.py`、`notifications/worker.py`、`tests/appointments/*` 最后修改于 `8391208` / `da93ca2` / `69d4cee`），仅少数来自 M4 的 `auth/*`。
3. 修复分三次提交发生，**前两次未先建任务单**（`665a067`、`b01acaf`）——构成任务范围账目缺口，本任务追认登记，历史不重写。
4. ruff 归零后 mypy 暴露 **16 个 error**（3 个文件），本任务第三次提交收口。

## 授权范围（允许修改路径，按路径逐条计数）
1. `apps/api/pyproject.toml`                        # ruff ignore / per-file-ignores 配置
2. `apps/api/app/appointments/service.py`           # E501 折行 + RowMapping 类型标注
3. `apps/api/app/appointments/sse.py`               # `typing.AsyncIterator`→`collections.abc`、I001
4. `apps/api/app/auth/repository.py`                # lint
5. `apps/api/app/auth/runtime.py`                   # lint
6. `apps/api/app/auth/service.py`                   # B904 异常链 / I001 / E501
7. `apps/api/app/notifications/email.py`            # I001 + 缺失类型注解 + SMTP 凭据窄化
8. `apps/api/app/notifications/worker.py`           # I001 / F541 / RUF100
9. `apps/api/app/worker.py`                         # I001 + database_url 窄化
10. `apps/api/tests/appointments/test_management.py` # 未用 import / 折行 / UP041 / SIM105 / RUF059
11. `apps/api/tests/appointments/test_sse.py`        # 同上 + 去失效 noqa
12. `tasks/TASK-GOV-007.md`                          # 本任务单（新建）

## 禁止修改路径（越界即停）
- `docs/**`（baseline / SRS / OpenAPI / 安全设计 / 测试计划：门禁绿化不得触碰规范）
- `apps/api/migrations/**`（无 schema 变更）
- `apps/api/app/appointments/crypto.py`、`appointments/runtime.py`（加密/密钥策略不变）
- 任何断言逻辑 / 冻结 TC 断言

## 目标
使 `ruff check .` 与 `mypy` 在 `apps/api` 下 repo 级退出码为 0，从而让验证批处理能够继续执行到 `pytest`；**不改变任何用户可观察行为**。

## 非目标
- 不修 pytest 失败（若有，归属对应功能任务）
- 不放宽 lint 规则集以掩盖真实缺陷（`select` 不缩小；仅对**确证误报**加 ignore 并写明理由）
- 不改公开 API / 迁移 / 加密策略 / 冻结 TC 断言

## 规则放宽的逐条理由（必须可审计）
- `ignore = ["RUF001", "RUF003"]`：本项目为中文项目，全角标点在中文字符串/注释中是**正确写法**，该两条规则会把每条中文字面量误报为"歧义 Unicode 字符"。属确证误报。
- `per-file-ignores "tests/**" = ["F811"]`：pytest 夹具靠**参数名注入**，`from .test_booking import real_stack` 后再作参数名会触发 F811「重定义」误报。改夹具结构风险高于加 ignore。属确证误报。
- 其余 113 个 ruff error 与 16 个 mypy error **全部按真实修复处理**，未加任何 ignore。

## mypy 修复的类型学结论（防后人重复踩坑）
- `RowMapping` **不兼容** `dict[str, Any]`，也**不兼容** `Mapping[str, Any]`（`Mapping` 键类型不变，而 `RowMapping` 的键类型不是 `str`）。`.mappings()` 结果的正确标注是 `sqlalchemy.RowMapping` 本身。
- `_load_owned_for_write` 原标注 `-> dict[str, Any]` 与实际返回 `.mappings().first()` 不符，属**标注错误**；已改为 `-> RowMapping`，下游 `_reschedule` / `_patch_details` 的 `row` 参数同步统一。
- 密文列在 SQL 中 nullable 而领域模型要求 `str`：写路径恒填充，故用 `cast(str, ...)` 在读路径窄化（**零运行时行为变化**），并就地注释。**收窄 schema 需要迁移=人工审批**，不在本任务范围 → 列为未解决风险。
- `EmailSender.__init__` 原把 `smtp_host/user/password` 以 `str | None` 存字段，导致 `smtplib.login/SMTP()` 类型不符。已在构造期校验并以 `str` 存储；**全部调用点（`auth/runtime.py:42`、`notifications/worker.py:102`）均已由 `Settings.notification_configured` 守卫**，故该 `raise` 在实际路径不可达，且把"凭据缺失"的失败点从 send 中途提前到构造期。
- `worker.py` 的 `create_engine(config.database_url)`：`notification_configured` 已隐含 `database_url` 非空，但 mypy 不能穿透 property 窄化 → 改用局部变量显式窄化，语义等价。

## ruff isort 分组结论（本轮踩坑三次，务必记住）
- `app.*` 属 **first-party** section，`.` 相对导入属 **local-folder** section，二者必须**分成两个块并用空行隔开**（绝对在前、相对在后）。
- 手动在同一块内调换顺序永远修不对 I001；正解是 `ruff check . --fix` 让工具确定性重排。

## 变更预算（change_budget）
- max_files：12（上列 11 个源/配置/测试路径 + 本任务单）
- expected_prod_lines：~90（含三次提交累计；纯 lint/类型标注，无逻辑变更）
- expected_test_lines：~55（仅 lint 清理，未改任何断言）

## 必须运行的测试命令
- `cd apps/api && ruff check .`（期望 `All checks passed!` / exit 0）
- `cd apps/api && mypy`（期望 0 error）
- 回归：`pytest`（本任务不引入逻辑变更，既有 53 passed 不得下降）

## 回滚方法
- 纯 lint/类型标注，无迁移；回滚 = `git revert` 本任务三个 commit

## 强制停止条件
- 需要改断言 / skip 测试才能让门禁绿 → 立即停止（说明门禁暴露的是真实缺陷，须归入功能任务）
- 需要改 schema / 迁移 / 加密策略 → 立即停止（人工审批项）
- 需要缩小 ruff `select` 规则集 → 立即停止

## 交付证据（关闭前一次写全）
- commit / PR：
  1. `665a067` — ruff 主体绿化（M4 + M1–M3 扫尾），11 文件
  2. `b01acaf` — 4 处 I001 手动修正（**顺序判断错误，未修净**，1 处残留）
  3. `<本次提交 sha>` — ruff `--fix` 写回 + mypy 16 error 收口，4 文件
- 修改文件清单（三次提交并集，按路径逐条计数）：**11 个唯一源/配置/测试路径**（见「授权范围」1–11）+ 本任务单 = 12
- 测试命令及结果：
  - `ruff check .` → `All checks passed!`（exit 0）— 已在 Windows 侧独立 venv 复核
  - `mypy` → 仅剩 2 条 `cryptography` `import-untyped`，属**复核环境缺 `py.typed` 标记的环境噪声**（用户 WSL 环境无此项）；代码侧 16 error 全清
  - `pytest` → **本任务未运行**（门禁短路修复后由 TASK-M4 的验证批处理执行）
- lint / typecheck：见上
- DB 迁移验证：无（无 schema 变更）
- 验收证据：门禁退出码 0；无逻辑 diff（三次提交均不含行为变更）
- 变更预算实际值：max_files=12，实际 12 路径，未超预算
- 未解决风险：
  1. **密文列 SQL nullable 与领域模型 `str` 必填不一致**（`meeting_platform_ciphertext` / `meeting_number_ciphertext` / `contact_ciphertext` 在 migration 0002 为 nullable）。当前以 `cast` 窄化，属**已知latent 不一致**；收窄需迁移（人工审批）→ 建议另开 TASK。
  2. mypy 未覆盖 `tests/**`（`files = ["app"]`），测试代码无类型保障。
- 是否偏离 TASK：**是（已发生，如实登记）**——`665a067`、`b01acaf` 两次提交在**无任务单**的情况下先行发生，本任务追认承载其范围；历史不重写。
- 规范影响结论：none（纯工具门禁与类型标注，不改任何 approved 规范、不改用户可观察行为）
- spec_sync：clean
- verified_commit：`<待用户 WSL 环境复核 ruff+mypy 后回填>`
- 关闭门禁：① `ruff check .` exit 0 ② `mypy` 0 error（用户 WSL 权威环境）③ `pytest` 回归不下降 ④ verified_commit 记录真实 sha

## 关闭结论
- **未关闭（Open）**。等待用户在 WSL 权威环境复核 `ruff check . && mypy` 双绿并跑通 `pytest` 回归后，方可回填 `verified_commit` 并关闭。AI 不得自行判定通过。

## 关联
- 上游：TASK-M1 / TASK-M2 / TASK-M3（既有 lint 债务来源）、TASK-M4（触发首次 repo 级门禁运行）
- 下游：TASK-M4 验证批处理（`pytest tests/auth/test_account_lifecycle.py`）→ 回填 M4 交付证据并关闭
- 建议新开：密文列 nullable 收窄迁移任务（人工审批项）
