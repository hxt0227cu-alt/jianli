# TASK-SRS-001 生成 SRS v1.0（含第六轮复评治理微补丁 + TASK 启动前补丁）

> 复制本模板为 `tasks/TASK-SRS-001.md`，作为 AI **仓库变更**的唯一范围约束。无任务单不得写入仓库，包括文档、设计、测试和代码变更。

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.2 / AI 治理 1.0.1（取自 `docs/baseline.yml`；版本如下，评审状态以 baseline.yml 为准）
- 基线 commit：gov-sync-001-verified（治理收尾完成后的真实 clean 快照标签；SRS v1.0 基于此 commit 生成）

## 精确规范引用（AI 只读取这些章节）
- PRD v2.3.3 精确规范引用：§1 项目背景 / §2 需求目标：全部 R1–R26（含 R14a、R14b）/ §3 业务场景 / §4 功能需求 / §5 非功能需求 / §6 验收标准 / §8.2 / §8.3 / §8.4 / §8.6 / §8.7 / §8.9 / §8.10 / §8.11 / §8.12 / §8.13；明确不读取 §8.1 / §8.5 / §8.8 / §8.14
- 用例规约 v1.7.2：UC-01–UC-23、需求—用例追踪矩阵
- 领域模型 v1.1.2：§1 范围与逻辑/物理边界 / §2 领域实体清单 / §5 状态机规范 / §6 实体字段语义与并发约束 / §7 数据层权限支撑 / §8 关键业务不变量 / §9 数据留存与清理
- baseline.yml：precedence / development_gate / mvp_hard_rules

## 需求来源
- 第六轮复评结论 + 收尾补丁验收反馈（4 项治理残留 P0-1/P0-2/P0-3/P1-1 + 可选 P1-2 + TASK 模板调整 + 正式 SRS TASK 要求）
- TASK 启动前验收：需求范围扩至 R1–R26、领域模型章节号修正、AGENTS 加入允许路径、SRS 状态流转、真实交付证据规则

## 目标
基于已批准 PRD、用例规约、领域模型生成 SRS v1.0；并先完成 4 项治理微补丁（用例规约去硬编码状态、PRD 去旧准入结论与硬编码版本、baseline precedence 标识统一、PROJECT_STATE 去重），使 `docs/baseline.yml` 成为唯一规范源且无漂移。

## 非目标（明确排除）
- 不做 UI 线框设计
- 不做架构选型 / ADR 编写
- 不做接口路径 / OpenAPI 设计
- 不新增产品需求
- 不修改 PRD 业务需求与领域模型实体 / 不变量（仅限治理措辞一致性）
- 不开始功能编码 / 数据库迁移

## 允许修改路径
- AGENTS.md                       # 仅修正 §0 上下文读取句（SRS approved 后改读 SRS）+ §1 任务驱动表述（与 TASK 模板一致：无任务单不得写入仓库），不改其他
- docs/requirements/use-cases.md   # 仅删除硬编码 `review` 状态（P0-1）+ 对齐冻结句为"SRS approved 后冻结"（对齐 PROJECT_STATE），不改业务内容
- docs/requirements/PRD.md          # 仅删除尾部旧 v2.3 准入结论（P0-2）、§8.11 去硬编码版本（P1-2），不改业务需求（微补丁已完成）
- docs/baseline.yml                 # precedence 标识统一（P0-3）+ precedence 注释 + SRS 状态流转；微补丁已完成
- PROJECT_STATE.md                  # 真正去重（P1-1）+ 用例冻结时机（P0-7）；微补丁已完成
- tasks/TASK-TEMPLATE.md            # 适用范围 + 任务类型 + 基线 commit 指引（对齐 repository_not_initialized；P1 模板调整，已完成）
- docs/requirements/SRS.md          # 新建 SRS v1.0（本任务主交付物）
- tasks/TASK-SRS-001.md             # 本任务单自身回填交付证据

## 禁止修改路径
- PRD 业务需求 R1–R26（含 R14a、R14b）语义
- 领域模型实体、属性、关系、状态机、业务不变式、并发约束
- docs/experiments/deferred/l2-persona-training.md
- docs/references/agent-engineering-frameworks.md
- 任何代码文件、数据库迁移、OpenAPI / SSE 契约

## 已批准的 DB / API / 依赖变更
- 无（本任务纯文档 / 治理，不含 schema / API / 依赖变更）

## 功能验收
- SRS v1.0 覆盖 PRD 全部功能需求 R1–R26 与用例规约行为，追踪矩阵完整（需求 → 用例 → SRS 节）
- 治理微补丁落地后，全仓 Grep 无残留 `review` 硬编码 / `待复评` / 旧 v2.3 准入结论 / `accepted_adr` / `security_design`
- 创建 SRS.md 后，将 baseline 中 srs 更新为 version: "1.0" / status: review
- WorkBuddy 不得自行把 SRS 标为 approved；只有用户或独立评审确认通过后，才能将 srs.status 改为 approved
- SRS 在 review 状态时不参与规范冲突裁决

## 安全与隐私验收
- 不引入新敏感字段；不改动既有加密 / 密钥 / 鉴权策略
- SRS 复用领域模型既有加密与访问控制不变式，不降格

## 性能验收
- 不适用（纯文档）；SRS 中非功能量化阈值沿用 PRD §5 非功能需求

## 变更预算（change_budget）
- max_files：8（含本任务单）
- expected_prod_lines：SRS 正文为主，治理补丁为小幅删改
- expected_test_lines：0

## 必须运行的测试命令
- 无（文档任务）；交付前执行全仓一致性 Grep 校验

## 回滚方法
- 修改前保留原文件副本/patch，初始化 Git 后使用 git restore/revert；本任务不产生迁移

## 强制停止条件（与 `AGENTS.md §2` 一致）

判定口径：**看变更是否已在本任务单「允许修改路径」列明，而不是看变更类型本身。**

- **可继续**：变更已在「允许修改路径」列明且为治理 / 文档性质，依据工件在 `docs/baseline.yml` 为 `approved`。
- **必须立即停止并报告（不得自行决定）**：出现任何未在「允许修改路径」列明的变化，包括但不限于
  - 新增外部依赖（npm / pip 包）；
  - 新增或修改数据库表、字段、索引、迁移；
  - 新增或修改公开 API / SSE 事件 / 契约字段；
  - 改变加密、密钥、鉴权或权限策略；
  - 修改 PRD 业务需求或领域模型实体 / 不变量；
  - 实现任务范围外的功能（含 `deferred` 延后项）；
  - 改动 Agent / AI Infra 参考文件。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<任务完成后回填；仓库未初始化 Git 时为 repository_not_initialized>
- 修改文件清单：<任务完成后回填>
- 测试命令及结果：<任务完成后粘贴实际命令和输出>
- lint / typecheck：<任务完成后回填；文档任务为不适用>
- DB 迁移验证：<任务完成后回填；本任务无迁移>
- 验收证据：<任务完成后回填；SRS v1.0 文件 + Grep 校验输出 + 用户/独立评审通过记录>
- 变更预算实际值：<任务完成后回填>
- 未解决风险：<任务完成后回填>
- 是否偏离 TASK：<任务完成后回填>

## 阶段性证据
- 治理微补丁（上轮）全仓 Grep：通过（无 `待复评` / `accepted_adr` / `security_design` / 旧 v2.3 准入结论 / 硬编码 `review` / `approved` 重复 残留）
- TASK 启动前补丁（本轮）：范围扩至 R1–R26、领域模型章节号修正、AGENTS 加入允许路径、SRS 状态流转写入、交付证据清空为回填占位 → <任务完成后回填验证>

## 关联
- Change Request：无
- 测试任务：无（文档）
