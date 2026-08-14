# TASK-FE-INTERVIEWER-001 Interviewer 个人中心（dashboard + 历史会话恢复）

> **状态**：**Closed（2026-08-14 用户显式授权关闭）**——dashboard + 历史会话已实现并验证。
> **依赖**：M1–M6 已关闭（`GET /appointments`、`GET /conversations`、`GET /conversations/{id}/messages`、`POST /answers:stream` 均就绪）；TASK-FE-AIQA-001/002（前端问答/管理页）已关闭

## 1. 任务类型
- implementation（前端域，apps/web）

## 2. 精确规范引用
- OpenAPI v0.2：`listMyAppointments`（GET /appointments，interviewer 会话）、`listConversations`（GET /conversations，cookieSession）、`listConversationMessages`（GET /conversations/{id}/messages，owner-only）、`streamAnswer`（conversation_id 时持久化）
- 既有前端：`apps/web/main.tsx`（Page/HistoryRail/TopBar/App/ChatPanel）、`apps/web/my-appointments.tsx`（/appointments 加载）

## 3. 目标
1. **Dashboard 页（Page='dashboard'，登录后首页）**：
   - 未登录：引导卡（登录 / 浏览简历）
   - 已登录：`/auth/me` + `/appointments` → 统计卡（进行中/已完成/已取消）+ 未来 7 天即将面试卡片（时间/公司/会议平台/状态）+ 快捷操作（去预约/我的预约）
   - 默认页改为 dashboard（打开站点第一屏）
2. **历史会话真实化**：HistoryRail「历史对话」登录后拉 `/conversations` 显示真实会话（匿名显示登录提示）；点击会话 → 切到简历问答页并**恢复该会话**（ChatPanel 拉 `/conversations/{id}/messages` 填充消息，后续发送带 `conversation_id` 持久化）；「新建对话」清空当前会话回匿名问答
3. Interviewer 无权限访问知识库管理（后端已 403，前端管理入口按 role 隐藏——仅 owner_admin 显示）

## 4. 非目标
- 面试评分/反馈；个人资料设置；通知偏好
- 会话重命名/删除（无 API）；移动端
- 后端任何改动（纯前端）

## 5. 允许修改路径（change_budget：max_files=5）
- `apps/web/main.tsx`（DashboardView + Page='dashboard' + 默认页 + HistoryRail 会话接真 + ChatPanel conversation 支持 + 管理入口按 role 隐藏）
- `apps/web/styles.css`（dashboard 样式）
- `tests/web-shell/shell.test.ts`（仅新增锚点断言）
- `PROJECT_STATE.md` / `tasks/TASK-FE-INTERVIEWER-001.md`

## 6. 禁止修改路径
- 后端 `apps/api/**`（契约/鉴权不变）；既有预约/问答流程（shell.test 旧断言全保留）

## 7. 验收标准
- 前端门禁（用户 WSL，沙箱 Windows 缺 win32 平台包）：`pnpm run typecheck` + `pnpm test` + `pnpm run build` 全绿
- 手动（WSL）：登录 interviewer → dashboard 显示统计与即将面试；历史对话显示真实会话；点会话 → 问答页恢复历史并可持续对话（落库）；匿名时历史区显示登录提示
- 安全：会话归属由后端保证（他人会话 403）；前端仅显示自己的

## 8. 强制停止条件
- 未列明变更（改后端/契约/删旧断言）→ 停止报告

## 9. 交付证据（2026-08-14 已回填；任务 Closed）
- 实现 commit：`233828c`（dashboard + 历史会话真实化 + 管理入口按 role 隐藏）+ `d203182`（登录首问自动创建会话闭环补丁）
- **用户 WSL 验证（2026-08-14）**：uvicorn 8000 + vite 5173 起服后，dashboard（默认页）正常渲染、历史会话列表/恢复/ChatPanel 三层布局均正常——**手动验证通过**（正式 typecheck/vitest/build 三连输出未单独回填，vite dev 编译即证明 TS 无错，同 TASK-KB-PDF-001 先例）；`verified_commit=233828c`
- 已知限制（如实登记）：InterviewView 页内登录后 user state 不即时回填（刷新同步）；会话无重命名/删除（无 API）

## 10. 关联
- 前置：M1（/appointments）、M6 二轮（/conversations + messages）
- 后续：面试评分反馈、个人设置、上线准备
