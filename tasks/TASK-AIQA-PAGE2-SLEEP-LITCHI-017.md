# TASK-AIQA-PAGE2-SLEEP-LITCHI-017：页面二 sleep 补全 + litchi 新增 tab

## 背景与目标

前端 `apps/web/main.tsx` 的 projects 对象目前只有 jianli（完整 4 步）+ sleep（3 行占位），litchi 无 tab。用户要求：

1. **sleep 补全**为完整项目介绍，按 jianli 的"4 步演进结构"（背景与问题 / 架构与选型 / Agent 与 RAG / 工程化与证据）写；量化数字必须来自已入库真实语料（content.py chunks + CORPUS taiyizhi.md），不新编。
2. **litchi 新增为"项目 03"**，同样按 4 步演进结构；素材取自 content.py litchi chunks + CORPUS litchi.md（90.4 分、8 模块、Spring Boot 3.2、四段受控 Agent、Milvus/Neo4j、RAG 荔枝问答）。
3. **同步更新**：`type ProjectId` 加 `'litchi'`、tab 渲染加"项目 03 · litchi"、ChatPanel 项目上下文加 litchi 分支；`ProjectInfo` 结构保持不变。
4. 前端 tsc/build 必须通过（WSL 跑）。
5. 项目 01/02 现有内容不改（sleep 占位替换除外——这是任务本身）。

## 素材来源（全部已入库，不新编）

- sleep：content.py `sleep202603_an` chunk（AI 睡眠健康 Agent 平台）+ CORPUS `taiyizhi.md`（84 例 7 类细分 / 审批绕过 0% / 10 注入 0 越权 / 4 隐私 0 泄露 / 18720 重平衡 lag 0·12.6s / dbt 56289→56218 / 67/84 漂移 / LangGraph 双协调器 / 5 微服务 9 层 / 四端形态 / WakeNet·MultiNet）。
- litchi：content.py `litchi` chunks（90.4 分、8 模块、Spring Boot 3.2/Vue3/YOLOv8、四段受控 Agent、Milvus+Neo4j、qwen2.5:0.5b、诚实局限）+ CORPUS `litchi.md`（12,622 行/11,076 行/21 views/14 表/49 接口/60 条评测/并发压测未达标/YOLOv8 降级链/observability）。

## 诚实边界（必须保留在文案中）

- sleep：Temporal 持久化路径仅单元/静态证据（本地确定性评测跑 local）；无真机板级验证（ADR-005）。
- litchi：并发压测 200 并发仅 19% 成功、P95 15.18s 未达标（按时间边界停止、报告如实保留）；Agent 单表 JSON 快照未拆表；BM25+RRF 与模型 rerank 未完成；数据平台为可部署模板未生产验证。

## 非目标

- 不动 content.py / CORPUS / 后端 / 其它页面；不动 jianli 现有内容；不新增 CSS（`purple` accent 已存在）。
- 前端门禁（tsc + vite build）由用户 WSL 验证（原生 Windows Git Bash 缺 rolldown win32 二进制会跳过）。

## 允许路径（max_files = 3）

- `apps/web/main.tsx`（ProjectId + projects 对象 + ChatPanel context + tab 渲染）
- `tasks/TASK-AIQA-PAGE2-SLEEP-LITCHI-017.md`
- （视验证结果：`PROJECT_STATE.md` 收口时更新）

## 变更预算

- main.tsx：ProjectId 1 处、projects 对象 sleep 替换 + litchi 新增、ChatPanel context 1 处、tab 渲染 1 处
- TASK 文件：新建

## 验证计划（用户 WSL）

1. `cd apps/web && npx tsc -b`（类型门禁）
2. `npm run build`（vite build，预期 ✓ built）
3. 页面功能：三个 tab 可切换、sleep/litchi 各 4 步可播放、右侧问答按项目过滤

## 交付证据

- commit / PR：`3e22085`（实现提交，2 文件 154+/7-）
- 修改文件清单：apps/web/main.tsx、tasks/TASK-AIQA-PAGE2-SLEEP-LITCHI-017.md
- 测试命令及结果：**PASS — 用户 WSL 2026-08-18 19:29 `npm run build` ✓ built in 21.73s**（build 脚本 = `tsc -b && vite build`，类型门禁与构建全通过；独立 `npx tsc -b --force` 报 tsconfig not found 为 npx 参数解析问题，不影响官方门禁）
- verified_commit：`3e22085`

## 关闭门禁

- [x] 代码改动完成（ProjectId 加 'litchi' / projects sleep 4 步补全 + litchi 03 新增 / ChatPanel context 三分支 / tab 加"项目 03 · litchi"；数字全部来自 content.py chunks + CORPUS taiyizhi.md/litchi.md，诚实边界保留）
- [ ] 用户 WSL tsc + vite build 通过
- [ ] 页面功能抽查（三 tab 切换 / 4 步播放 / 右侧问答按项目过滤）
- [ ] 提交 + verified_commit 回填 + PROJECT_STATE 同步
