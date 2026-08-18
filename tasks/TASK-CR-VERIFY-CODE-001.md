# TASK-CR-VERIFY-CODE-001 注册邮箱验证改 6 位数字码（Change Request）

> **状态：draft（CR 草案，待用户批准）**
> 核心：注册邮箱验证从「邮件链接 token」改为「6 位数字验证码」。
> **为什么必须走 CR**：① OpenAPI `verifyEmail` 请求体字段变更（TokenRequest→VerifyCodeRequest）= 公开 API 契约变更；② PRD §8.6 邮件模板为「内容基线已确认」（改验证方式文案=改变含义）；③ UI 线框 U5 验证交互形态变化。三处均触发 AGENTS §9.4 Spec Impact Gate（改变用户可观察行为 → 先 CR 更新规范 → 批准 → 再实现）。

## 任务类型
- change-request  # 规范变更 + 后续实现预告（本任务只改规范，不写业务代码）

## 基线版本与基线 commit
- baseline：SRS 1.2 / PRD 2.3.3 / OpenAPI 0.3 / UI 线框 1.0（取自 `docs/baseline.yml`）
- 基线 commit：`dc25488`（本任务创建时 master HEAD）

## 需求来源（用户指令 = CR 发起）
- 用户 2026-08-18：「验证码是邮件链接？改成数字码」
- 规格佐证（说明数字码形态本就在已批准规格内，本 CR 是让实现/契约与规格对齐）：
  - PRD §5 限频表：「邮箱验证码 有效期 10 分钟；错误最多 5 次；注册（同邮箱发验证码）60 秒内 1 次、每小时每邮箱最多 3 次」
  - PRD 注册需求：「需邮箱验证（发送验证邮件 / 验证码）」——两形态均允许
  - SRS §5.6：「邮箱验证码（10 分钟有效、错误≤5）」

## 现状核对（实现真相，代码/契约说了算）
| 项 | 规格要求 | 当前实现 | 差异 |
|---|---|---|---|
| 注册验证形态 | PRD/SRS 允许验证码 | **邮件链接 token**（POST /auth/verify-email 收 token）| 实现选型偏离可选形态 |
| 验证 TTL | SRS/PRD：**10 分钟** | `VERIFICATION_TTL = timedelta(hours=24)` | **实现 24h > 规格 10 分钟**（顺带修正）|
| 错误次数上限 | PRD：**错误≤5 次** | 无计数（链接形态天然无重试）| 数字码需补 |
| 发码限频 | PRD：60s/1 次、每小时≤3 | 链接形态无发码限频 | 数字码需补 |
| 找回密码 | SRS：邮箱验证码 | **重置链接 token**（同样偏离）| 见下方「范围选项」 |

## 变更工件（本 CR 批准后执行）
1. **`docs/api/openapi.yaml`**（v0.3 → v0.4）：
   - `verifyEmail` 请求体：`TokenRequest{token}` → `VerifyCodeRequest{code: string, pattern: ^\d{6}$}`
   - 新增错误响应：验证码无效/过期 → `422 INVALID_VERIFY_CODE`（或复用 SRS 现有语义，CR 定稿）；错误超 5 次 → 失效需重发（`429 RATE_LIMITED` 或新增 `VERIFY_ATTEMPTS_EXCEEDED`，CR 定稿）
   - `requestPasswordReset` / `confirmPasswordReset`：按范围选项 A/B 决定是否同步改数字码
2. **`docs/requirements/PRD.md` §8.6**：邮件模板文案「点击链接验证」→「6 位验证码 + 10 分钟有效」（内容基线变更，仅经本 CR 批准后执行）
3. **`docs/design/ui-wireframe.md` U5**：验证页交互「点链接自动验证」→「输入 6 位验证码 + 重发入口（60s 冷却）」；若范围含找回，同步更新 U5/U6
4. **`docs/requirements/SRS.md`** §3.3 / §5.6：明确注册验证=邮箱数字码（10 分钟 / 错误≤5 / 发码限频），并修正 TTL 表述与实现一致；错误语义定稿

## 范围选项（请用户在批准时一并指定）
- **A（推荐，最小范围）**：仅注册验证改数字码；找回密码维持链接形态
- **B（彻底对齐）**：注册验证 + 找回密码**都**改数字码（两者 SRS/PRD 规格均为「验证码」，实现同为链接——一并修正消除两处偏离）
- 影响差异：A 只动 verify-email 契约；B 还动 reset 契约 + 前端找回页

## 非目标
- 不改登录方式（密码登录，验证码不用于登录——PRD 决策#14 不变）
- 不加短信 / 图形滑块（可选增强，不在本次）
- 不新增 DB 表（验证码存现有 verification_tokens 表，加 expires_at 对齐 + attempts 计数列——**若需新列则属 DB 变更，将在实现 TASK 中单列审批**）

## 规范影响评估（spec impact）
- behavior_change：**true**（验证交互形态变化：链接→数字码输入）
- affected_specs：openapi（verifyEmail 契约）、prd（§8.6 文案）、ui_wireframe（U5）、srs（§3.3/§5.6 语义与错误码）
- reason：AGENTS §9.4——改变用户可观察行为，必须先更新并批准规范，再实现

## 交付证据（本 CR 关闭前必须填写）
- commit：<规范更新提交 sha>
- 修改文件清单：<openapi/prd/ui_wireframe/srs 逐一列>
- 用户批准记录：<批准消息/时间>
- 下游实现 TASK：<批准后创建 TASK-AUTH-VERIFY-CODE-001（后端 code 生成/校验/限频 + 前端输码页 + 测试）>
- 未解决风险：无（实现细节留实现 TASK）

## 关联
- 后续实现 TASK：TASK-AUTH-VERIFY-CODE-001（批准后建）
- 并行：TASK-ADMIN-AVAIL-UI-001（时段设置 UI，独立不阻塞）
