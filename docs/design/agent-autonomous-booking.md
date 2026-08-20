# 设计文档：面试官通过对话自主预约（路线 B）

- 关联 TASK：`tasks/TASK-AIQA-BOOKING-001.md`（状态：`implemented`）
- 范围：AIQA agent（aiqa 域）新增写工具，调用 预约域 `booking_service` 直接建预约；前端对话页新增预约确认卡片。
- 设计日期：2026-08-19；实现完成：2026-08-20

---

## 1. 背景与目标

当前 agent 只有一个只读工具 `search_knowledge`（service.py:162 `_SEARCH_TOOLS`）。预约必须人手动在「预约」tab 选 3 个 slot、填公司/联系人、确认。

本设计让**已登录面试官**在对话里说一句「我想预约下周三下午两点的面试」，agent 自主完成：解析时间 → 解析可用 slot → 调用 `booking_service.preview/create` → 回显确认卡片。

目标（可量化）：
- G1 已登录面试官用自然语言说出时间，agent 能解析并建预约，无需离开对话页。
- G2 解析不到/冲突/未登录/非面试官，agent 给出**明确、不崩溃**的回执。
- G3 复用现有 预约域 强约束（3×30min 连续、同一本地日、RBAC、令牌、幂等），**不绕过、不改写其校验**。

非目标（本期不做）：
- 不改预约域 `AppointmentDraft` 的结构与校验（除非选 B-relax，见 §6）。
- 不做日历/选时 UI 的改造（那仍是人操作入口，保留）。
- 飞书通道 R13/R14 联动沿用既有 notification_events，无需改。

---

## 2. 用例规约

### UC-1 自然语言预约（主成功路径）
- 参与者：已登录 interviewer
- 前置：`principal.role == "interviewer"`，目标日期窗口已被 owner 在「时段设置」物化为 `available` slot。
- 步骤：
  1. 用户：「预约下周三下午两点」
  2. agent Phase1 调 `request_interview_booking`（start=解析出的本地时间 14:00）
  3. 工具 RBAC 通过 → 解析 3 个连续 slot（14:00/14:30/15:00）→ 业务字段若齐全则 `preview`+`create`
  4. 成功 → 推 `booking:confirmed` 帧（数据取自 `create()` 返回，非模型生成）+ Phase2 生成确认话术
- 后置：DB 新增 active 预约，3 slot 变 `booked`，notification_events 写入（Worker 发确认函）。

### UC-2 信息不全 → 追问（关键分支）
- 触发：自然语言只含时间，缺 `company_name`/`meeting_platform`/`contact_*`。
- 步骤：工具返回 `needs_info`（缺字段列表）→ Phase2 模型用自然语言一次性追问 → 用户补答 → 下一轮工具带齐字段 → 走 UC-1。
- 不降级为「随便填默认值」，保证数据完整（见 §6 决策点）。

### UC-3 时段未开放/已被占
- 触发：解析出的 3 slot 非全 `available`。
- 工具返回 `failed`（原因 + 可选邻近可约时段）→ 模型道歉并给出建议，不建预约。

### UC-4 未登录 / 非面试官
- 触发：`principal is None` 或 `role != "interviewer"`。
- 工具返回 `forbidden` → 模型引导「请先登录面试官账号」（呼应需求 #2/#4 的登录流）。

### UC-5 重复说同一句（幂等）
- 触发：slot 已 `booked`（同用户刚约过或他人占）。
- `_validate_slots` 抛 `SLOT_TAKEN` → 工具捕获 → 回执「该时段已被预约」。不重复建。

### UC-6 解析失败（歧义/格式）
- 触发：「下周三」相对今天算错、或「两点」无法映射。
- 工具返回 `needs_info`（要求澄清日期/时间）→ 模型追问，不臆测。

---

## 3. 领域模型与接口设计

### 3.1 agent 工具注册（aiqa 域）
在 `_SEARCH_TOOLS` 旁新增 `request_interview_booking`（写工具）。Phase1 的 `tools=` 同时含两者，`tool_choice=auto`，由模型决定调哪个。

工具 schema（模型产出参数）：
```
request_interview_booking:
  target_date: string  "YYYY-MM-DD"        # 模型把"下周三" relative 到今天(Asia/Shanghai)算出
  start_time: string   "HH:MM"             # 本地时，"两点"→"14:00"
  company_name:    string?   # 自然语言有则给，无则省略
  meeting_platform: string?  # 如"腾讯会议/飞书/Zoom"，无则省略
  meeting_number:   string?  # 会议号，无则省略
  contact_last_name:   string?
  contact_salutation:  string?
  contact_phone:      string?
```
> 时长固定 90 分钟（=3 slot）。模型只需给起点；工具自动 padding 14:00→14:00/14:30/15:00。

### 3.2 工具执行（aiqa 域内，进程内调用 booking_service）
`apps/api/app/aiqa/service.py` 新增 `_run_booking_tool(arguments, principal)`：
1. **RBAC**：`if principal is None or principal.role != "interviewer": return forbidden`
2. **解析 slot**：`SELECT id,start_at,end_at,status FROM appointment_slots WHERE DATE(start_at AT TIME ZONE 'Asia/Shanghai')=:d AND status='available' ORDER BY start_at`，取 `start_time` 起连续 3 个（start, +30, +60）。不足 3 个可用 → `failed`。
   - 时区统一用 `LOCAL_TIME = Asia/Shanghai`（service.py:41），与预约域一致。
3. **业务字段齐性检查**：若 `company_name/meeting_platform/meeting_number/contact_last_name/contact_salutation/contact_phone` 任一缺失 → 返回 `needs_info`（列缺失项）。**不填默认值**。
4. **建预约**：`draft = AppointmentDraft(slot_ids=[...3], company_name=..., ...)` → `tok, exp = booking_service.preview(principal, draft)` → `appt = booking_service.create(principal, draft, tok)`。
   - `booking_service` 内部已做：`_validate_slots`（3 连续/同本地日/30min/available）、`FOR UPDATE` 行锁、`updated.rowcount != 3 → RuntimeError`、令牌校验、company 指纹去重。**agent 全部复用，不重造**。
   - 注意：`booking_service` 内部**不校验角色**（角色校验在 router 的 `require_role`），故步骤 1 的 RBAC 必须在工具内补做。
5. **异常映射**：`AuthError`(SLOT_TAKEN/OWNER_LOCKED/CONFIRM_EXPIRED) → `failed`（带原因）；`IntegrityError` → `failed`（"系统繁忙"）；其它 → `failed`。
6. 返回结构化结果 dict：`{outcome: confirmed|needs_info|failed|forbidden, ...}`。

### 3.3 SSE 帧（新增类型，复用既有帧机制）
在 `apps/api/app/aiqa/sse.py` 现有 `tool_calls_frame/delta_frame/...` 旁新增：
- `booking_frame(seq, outcome, payload, trace_id)`，`type`：
  - `urn:jianli:booking:confirmed` → payload: `{start_at, end_at, company_name, meeting_platform, contact, appointment_id}`
  - `urn:jianli:booking:needs_info` → payload: `{missing: [...]}`
  - `urn:jianli:booking:failed` → payload: `{reason, suggestions?}`
  - `urn:jianli:booking:forbidden` → payload: `{reason}`
- 调度（service.py）：Phase1 后 `if name == "request_interview_booking": result = await self._run_booking_tool(...)`，按 `result.outcome` 推对应 `booking_frame`，再进 Phase2 让模型生成话术（确认/追问/道歉）。

### 3.4 存储
**不改任何表**。`appointment_slots` / `appointments` / `companies` / `notification_events` 全部复用。agent 只新增「调用」，不新增持久化结构。

### 3.5 前端（apps/web/main.tsx + appointment.css）
对话流新增一种消息卡片：预约确认卡（显示时间/公司/平台/会议号/联系人 + 「去我的预约查看」链接）。`needs_info/failed/forbidden` 由模型自然语言覆盖，不强制卡片（可选轻提示）。无新增路由/tab。

---

## 4. UI 线框（文本）

```
[用户] 预约下周三下午两点的面试
[助手] （booking:confirmed 卡片）
        ✅ 已为你预约
        时间：2026-08-26 周三 14:00 – 15:30（北京时间）
        公司：<company>   平台：<platform>   会议号：<number>
        联系人：<salutation><last_name> <phone>
        [查看我的预约]
        （话术）已提交，确认函将发到你的邮箱。如需改时间可在「我的预约」取消重约。
```
`needs_info` 时无需卡片，模型直接问：「可以的～请补充：贵公司名称、面试平台（如腾讯会议）、及联系电话？」

---

## 5. 非功能量化
- 时延：新增 1 次 LLM 调用（Phase2 生成话术），预约本身纯 DB 操作（<100ms）。端到端 < 8s（受 LLM 主导）。
- 安全：RBAC 强制；slot 原子性由 DB 行锁 + `rowcount==3` 保证；令牌 `preview→create` 复用，无中间态泄露。
- 幂等：slot 变 `booked` 后重说 → `SLOT_TAKEN` 优雅回执，不重建。
- 可观测：`answer_completed` 日志已含 `grounded/offtopic/model`；新增 `booking_outcome` 字段（confirmed/needs_info/failed/forbidden）便于评测。
- 不越权：agent 写工具仅 `interviewer` 可触发；`owner_admin` 触发返回 forbidden。

---

## 6. 待拍板设计决策（阻塞编码）

**D1 — 缺公司/联系人时如何填（核心）：**
- **A（推荐，数据完整）**：工具返回 `needs_info`，模型追问一次，用户补答后建。不改 `AppointmentDraft`。✅ 与现有校验/去重/加密完全一致。
- **B-relax（零追问）**：放宽 `AppointmentDraft` 让这些字段对 agent 可选，缺失时由 principal 推导（contact=principal.email 作 last_name? 不可靠；company=邮箱域名?）。⚠️ 会存低质量/占位数据，且改动 预约域 schema + 校验，属跨域变更，需独立 CR。
- 用户定。

**D2 — 是否要用户侧「最终确认」按钮（HITL）：**
- 用户选了「真正自主」，默认**不弹确认**，模型直接建 + 回显卡片。「我的预约」页可取消作为安全阀。
- 若日后要 HITL，本设计已预留 `needs_info` 机制可扩展为 `await_confirm`。

**D3 — 时长固定 90min 的口径：** 模型只解析起点，「两点」= 14:00 起 90 分钟。如用户说「约一小时」本期不支持（仅 90min 槽），工具返回 `needs_info` 澄清。

---

## 7. 测试计划
- **单元（pytest，aiqa + appointments）**：
  - 日期解析：相对「下周三」相对 2026-08-19 → 08-26；时区边界。
  - slot 解析：给定日 14:00 起取连续 3 available；不足 3 → failed；中间有 booked → failed。
  - 字段齐性：缺 company → needs_info；齐全 → 进 preview/create（mock booking_service）。
  - RBAC：principal=None → forbidden；owner_admin → forbidden；interviewer → 通过。
  - 异常映射：SLOT_TAKEN/OWNER_LOCKED/CONFIRM_EXPIRED → failed(原因)；IntegrityError → failed。
  - 帧：confirmed 帧 payload 来自 `create()` 返回（非模型生成）。
- **集成（real-stack pytest，WSL）**：seed 一段 available slot → 用测试 interviewer principal → 调 `_run_booking_tool` → 断言 appointments 新增 active、3 slot `booked`、notification_events 有行；重复调 → SLOT_TAKEN 优雅。
- **E2E 验收（浏览器）**：登录面试官 → 对话「约下周三 14:00」→ 补公司/电话 → 卡片确认 → 「我的预约」可见 → 收确认邮件（Worker 跑着）。

---

## 8. 实现回执（2026-08-20）

### 8.1 验收结果
- 前端 `tsc --noEmit`：**EXIT=0**。
- `pytest apps/api/tests/aiqa/test_agent_booking.py`：**12 passed（10 单元 + 2 real-stack 端到端）**，ruff 全绿。
- 浏览器 E2E：待用户手动验收（需 Worker 运行以收确认邮件）。

### 8.2 与设计的偏差（详见 TASK 偏差登记）
- slot 解析复用 `booking_service.slot_snapshot(principal, week_offset)`（而非 §3.2 的裸 SQL），维持「不改 appointments 域」边界。
- `create()` 返回 `start_at/end_at` 为 UTC isoformat，前端按 `Asia/Shanghai` 本地化展示。
- contact 串格式 `f"{salutation}{last_name} {phone}"`（称谓与姓间无空格），UI 线框 §4 的 `salutation + 空格 + last_name` 以代码产物为准。
- 测试抓到 2 个真实 bug（service.py 缺 `datetime`/`timedelta`/`UTC` import；`preview()` 误按元组解包）已修复，证明单元+real-stack 测试有效。

### 8.3 改动文件（ appointments 域零改动）
- aiqa：`app/aiqa/service.py`、`sse.py`、`runtime.py`
- 装配：`app/factory.py`
- 前端：`apps/web/main.tsx`、`apps/web/appointment.css`
- 测试：`tests/aiqa/test_agent_booking.py`（新增）
```
