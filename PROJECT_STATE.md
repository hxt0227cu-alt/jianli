# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-07（SRS v1.0 生成并进入独立评审；status=review，未 approved）

---

## 当前阶段

分析设计阶段。编码准入未开放，由 `docs/baseline.yml` 的 `development_gate` 决定。SRS v1.0 已生成，当前处于**独立评审阶段（status=review，未 approved）**，不计入 baseline precedence 裁决。

---

## 当前任务

- 当前动作：评审 SRS v1.0（tasks/TASK-SRS-001.md）；未 approved，TASK 保持开启。
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

> 注：SRS v1.0 当前处于 review（未 approved），不计入 baseline precedence 裁决；经独立评审 approved 且完成需求—用例—SRS 追踪检查后，用例规约冻结为历史输入或 SRS 附录，再进入 UI 线框。

---

## 最后 verified commit（审计锚点）

Git 已初始化；审计锚点 = verified commit `adc7c8d3df42f0ecfb6dd846317ce6de04760cc5`（tag: gov-sync-001-verified；即治理收尾最终 commit，含 TASK-GOV-SYNC-001 关闭证据 + 全部治理文件 + 本锚点更新；机器锚点首选真实 SHA，tag 仅作人类别名；解析见 `git rev-parse gov-sync-001-verified`）。
本标签为 Review/Audit Mode（`AGENTS.md §9`）checkout 的快照——复盘时 AI 先 `git checkout gov-sync-001-verified`，再看其对应 approved specs，而非"读当前目录猜实现"。
本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
