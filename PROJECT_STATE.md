# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-06（第六轮复评收尾完成）

---

## 当前阶段

分析设计阶段。编码准入未开放，由 `docs/baseline.yml` 的 `development_gate` 决定。复评收尾补丁已完成，下一步进入 SRS。

---

## 当前任务

- 当前动作：创建并执行 SRS 文档任务（tasks/TASK-SRS-001.md）。
- 具体版本与评审状态见 `docs/baseline.yml`。

---

## 本周阻塞

- 待确认项（PRD §8.2，不阻塞设计但阻塞上线）：SMTP / 域名 / 备案、飞书授权、人格素材、知识库文件。
- 网易 163 邮箱授权码等密钥**绝不写入任何文档 / 记忆 / 配置文件**，仅存运行时环境变量或 Secret Manager。

---

## 下一步（评审推荐顺序，仍编码前）

```
SRS v1.0 → UI 线框 → 架构与 ADR → 安全设计 → OpenAPI/SSE 合同 → 测试计划 → 开发准入评审 → 功能编码
```

> 注：SRS v1.0 经评审 approved，且完成需求—用例—SRS 追踪检查后，用例规约才冻结为历史输入或 SRS 附录，不再双向维护。

---

## 最后 verified commit（审计锚点）

尚未进入编码阶段，值为 `repository_not_initialized`（仓库未初始化 Git）。
编码启动并初始化 Git 后，此处记录**每次通过 CI / 任务关闭时**的真实 commit hash，作为 Review/Audit Mode（`AGENTS.md §9`）checkout 的快照——复盘时 AI 先 checkout 该 commit，再看其对应 approved specs，而非"读当前目录猜实现"。
本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
