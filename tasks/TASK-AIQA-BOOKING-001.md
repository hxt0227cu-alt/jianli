# TASK-AIQA-BOOKING-001：面试官对话自主预约（路线 B）

- 状态：`implemented`（2026-08-20 验收通过：前端 tsc EXIT=0、单测+real-stack 12 passed、ruff 全绿）
- 设计文档：`docs/design/agent-autonomous-booking.md`（状态见文末「实现回执」）
- 创建：2026-08-19；完成：2026-08-20
- **决策已落**：D1=A（缺信息→`needs_info` 追问、不改 `AppointmentDraft`）；D2=默认无 HITL（真正自主）；D3=固定 90min 仅解析起点。

## 目标
已登录面试官用自然语言说时间，agent 自主调用 预约域 `booking_service` 直接建预约，回显确认卡片。不绕过/不改写 预约域 既有强约束。

## 范围（单一工件，跨两域但同一功能）
- **aiqa 域（新增/改）**：
  - `apps/api/app/aiqa/service.py`：新增 `_run_booking_tool()`；Phase1 工具白名单加 `request_interview_booking`；Phase1→Phase2 间按 outcome 推 `booking_frame`；RBAC 检查（principal None/非 interviewer → forbidden）。
  - `apps/api/app/aiqa/sse.py`：新增 `booking_frame()` + 4 个 `urn:jianli:booking:*` 类型。
  - `apps/api/app/aiqa/models.py`（如需）：工具参数 pydantic schema。
- **前端（新增/改）**：
  - `apps/web/main.tsx`：对话流渲染 `booking:confirmed` 卡片。
  - `apps/web/appointment.css`：确认卡样式。
- **测试（新增）**：
  - `apps/api/tests/aiqa/test_agent_booking.py`：单元 + real-stack 集成。

## 不改动（明确边界）
- `apps/api/app/appointments/**` 的 schema/校验/去重/令牌逻辑：**零改动**（D1 选 A 时）。
- 日历/选时 UI、登录流、飞书通道：不碰。
- 若 D1 选 B-relax，则 `appointments/models.py` + `service.py` 的 `AppointmentDraft` 校验需纳入**独立 CR + 新 TASK**，不在本 TASK。

## 待用户拍板（阻塞编码）
- **D1**：缺公司/联系人时 —— A 追问(推荐,不改 Draft) / B-relax(放宽 Draft,跨域CR)。
- **D2**：默认无 HITL 确认（已定，用户选真正自主）。
- **D3**：时长固定 90min，仅解析起点。

## 门禁（验收前必过）
- `pnpm exec tsc --noEmit`（前端）→ **EXIT=0 通过**
- `pytest apps/api/tests/aiqa/test_agent_booking.py`（单元+集成，WSL real-stack）→ **12 passed（10 单元 + 2 real-stack 端到端）**
- 浏览器 E2E：登录面试官 → 对话补信息 → 卡片确认 → 我的预约可见 → 收邮件。**待用户手动验收**（Worker 需运行）。

## 偏差登记（实现中实测与设计的差异 / 测试抓到的真实 bug）
1. **`app/aiqa/service.py` 缺 import**：`_run_booking_tool` 用到 `datetime`/`timedelta`/`UTC` 但原文件未 import（仅 import 校验 + 属性检查漏掉真实调用路径）。已补 `from datetime import datetime, timedelta, timezone, UTC`。
2. **`preview()` 返回值误用**：原写 `token, _ = booking.preview(...)`，但真实 `preview()` 返回 `AppointmentPreview` 对象（不可解包）→ 改为 `preview = await asyncio.to_thread(booking.preview, ...)` 后取 `preview.confirmation_token`。**测试抓到的真实调用 bug。**
3. **`BookingService` 前向引用 F821**：`"BookingService"` 带引号 + `from __future__ import annotations` 时 ruff 仍报未定义 → 改为真正 `from app.appointments.service import BookingService, LOCAL_TIME, Slot` 并去掉引号。
4. **RUF002 非 ASCII 字符**：docstring 里的 `×`（3×30min）触发告警 → 改为 `3 x 30min`。
5. **实现细节（非 bug，记录以供 TASK/文档对齐）**：
   - slot 解析复用 `booking_service.slot_snapshot(principal, week_offset)`（非设计文档 §3.2 写的裸 SQL），按目标周窗口取快照后过滤连续 3 个 `available` 起点；维持「不改 appointments 域」边界。
   - `create()` 返回的 `start_at/end_at` 为 **UTC** isoformat（14:00 Asia/Shanghai = 06:00 UTC）；前端按 `Asia/Shanghai` 本地化展示。单测断言已按 UTC 解析对齐。
   - contact 串格式为 `f"{salutation}{last_name} {phone}"`（称谓与姓之间**无空格**，如 `TeacherZhang 138...`）；UI 线框 §4 写的 `salutation + 空格 + last_name` 与实际不符，已以代码产物为准修正测试断言。
6. **real-stack 约定**：`test_agent_booking.py` 的 2 个真实栈用例用 `pytestmark_integration` + `skipif`（守护 env `JIANLI_BOOKING_TEST_DATABASE_URL` / `JIANLI_BOOKING_TEST_REDIS_URL`）。普通 `pytest` 无该 env 时自动 skip；带 env 时需专用 DB + Redis。验证用临时库 `jianli_booking_test_db`（已 drop）。

## 改动文件清单（max_files/允许路径核对）
- 新增：`apps/api/tests/aiqa/test_agent_booking.py`
- 改：`apps/api/app/aiqa/service.py`、`apps/api/app/aiqa/sse.py`、`apps/api/app/aiqa/runtime.py`、`apps/api/app/factory.py`、`apps/web/main.tsx`、`apps/web/appointment.css`
- 未改：`apps/api/app/appointments/**`（零改动，符合边界）。

## baseline 治理冲突与收口（重要）
- **冲突**：`docs/baseline.yml` 原 `deferred` 将 `agent_auto_booking` 标「PRD 决策#14 明文禁止」、`mvp_hard_rules[0]` 写「大模型只负责问答，不自动写预约」；本 TASK 实现正与之冲突。
- **收口**：经 `TASK-CR-AIQA-BOOKING-001`（2026-08-20 用户批准推翻禁止）同步 baseline——移除 deferred 条目、修订硬规则第 1 条（加 RBAC 守卫的面试官专用写工具例外）、新增 `agent_tools` 注册块登记 `request_interview_booking`。提交顺序遵循先 `docs(spec)` 后 `feat` 先例。

## 关联
- 复用：`TASK-AGENT-TOOLS-002`（工具机制）、预约域 preview/create/令牌/去重。
- 依赖需求 #2/#4（登录流、tab 权限）已落地。
