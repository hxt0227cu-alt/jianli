# TASK-GOV-SYNC-001 固化"事实来源路由 + spec impact + verified commit + based_on"治理模型

> 复制本模板为 `tasks/TASK-GOV-SYNC-001.md`，作为 AI **仓库变更**的唯一范围约束。无任务单不得写入仓库，包括文档、设计、测试和代码变更。

## 任务类型
- documentation  # 纯治理文件变更，不产产品功能、不改业务需求、不改领域模型、不写功能代码

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.2 / AI 治理 1.0.1（取自 `docs/baseline.yml`；版本如下，评审状态以 baseline.yml 为准）
- 基线 commit：repository_not_initialized（任务启动时的真实历史事实：仓库尚未初始化 Git；任务完成态由 verified_commit 记录，不得被完成态覆盖——否则审计会变成"任务基于自身完成后的快照开始"，时间因果倒置）

## 精确规范引用（AI 只读取这些章节）
- baseline.yml：artifacts / precedence / development_gate（仅读取，本次扩展 artifacts 的 based_on 约定）
- AGENTS.md：现有 §0–§8（本次新增 §9）
- TASK-TEMPLATE.md：现有全部章节（本次扩展 规范影响评估 + 交付证据）
- PROJECT_STATE.md：全文（本次澄清"最后 verified commit"锚点语义）
- TASK-SRS-001.md：仅第 65 行性能验收的 PRD 章节号修正（§4 → §5）

## 需求来源
- 用户提案（2026-08-07）：从"规范谁说了算"升级到"规范/代码/运行谁说了算"，将真相拆为四类，用 based_on / spec impact / verified commit 把同步变成结构门禁而非人工 Grep。

## 目标
将"事实来源路由 + spec impact gate + verified commit + based_on 依赖锚点"固化进现有四个治理文件（baseline.yml / TASK-TEMPLATE.md / AGENTS.md / PROJECT_STATE.md），并修掉 TASK-SRS-001 中遗留的 PRD §4→§5 章节错位。使后续"上游版本变化→下游 impact review""代码改行为→先 Change Request"成为结构强制，而非靠人工对齐。

## 非目标（明确排除）
- 不新增产品功能 / 不启动 SRS 正文 / 不启动接口设计
- 不修改 PRD 业务需求与领域模型实体 / 不变量（仅治理措辞与章节引用一致性）
- 不写功能代码 / 数据库迁移 / OpenAPI 契约
- 不新增治理文档（不建 DOC-SYNC.md / CODE-STATE.md 之类新漂移源）；只增强四个现有文件
- 本任务不实现自动 checker 脚本（based_on 机器门禁的脚本留作后续可选项，本次仅定义数据模型与规则）

## 允许修改路径
- docs/baseline.yml            # 为 srs 增加 based_on 锚点（prd/use_cases/domain_model 当前已批准版本）+ 顶部注释说明"依赖变化→需 impact review，不自动判废"
- tasks/TASK-TEMPLATE.md       # 新增「## 规范影响评估（spec impact）」章节 + 扩展「交付证据」含 规范影响结论 / spec_sync / verified_commit + 关闭门禁四条件
- AGENTS.md                    # 新增 §9「事实来源路由与复盘模式」：四类真相 / 禁止用文档推断实现 / Review-Audit Mode 三栏 / spec impact gate 三分类
- PROJECT_STATE.md             # 澄清「最后通过测试的 commit」= 最后 verified commit（审计锚点）；repository_not_initialized 直到 Git 初始化
- tasks/TASK-SRS-001.md        # 第 65 行性能验收「PRD §4」→「PRD §5 非功能需求」（修复用户指出的具体错位）
- （仓库操作）初始化 Git 并做首个 baseline commit，仅纳入已批准治理/文档/设计工件；附 .gitignore 排除 .env / 密钥 / node_modules；提交前校验无密钥内容进入版本库
- tasks/TASK-GOV-SYNC-001.md   # 本任务单自身：重新打开后回填修复 P0-1/P0-2（允许路径含自身、max_files 6→7、交付证据实际 7）
- AGENTS.md（语言规则）# 实际新增「交互输出语言」SSOT 与 §5 输出语言确认，超出原授权 AGENTS §9 内容范围；本回合独立复核接受为治理补充（偏离已如实记录于交付证据，未伪造"未偏离"）

## 禁止修改路径
- PRD 业务需求 R1–R26 语义
- 领域模型实体、属性、关系、状态机、业务不变式、并发约束
- docs/experiments/deferred/l2-persona-training.md
- docs/references/agent-engineering-frameworks.md
- 任何功能代码文件、数据库迁移、OpenAPI / SSE 契约

## 已批准的 DB / API / 依赖变更
- 无（本任务纯治理/文档，不含 schema / API / 依赖变更；Git 初始化不引入业务依赖）

## 功能验收
- baseline.yml 的 srs 条目含 based_on 锚点，且顶部注释写清 impact-review 语义
- TASK-TEMPLATE.md 含 规范影响评估 章节 + 交付证据含 spec_sync / verified_commit + 关闭门禁四条件
- AGENTS.md §9 含四类真相路由 + 禁止用文档推断实现 + Review-Audit Mode + spec impact gate 三分类
- PROJECT_STATE.md 的 commit 锚点语义已澄清
- TASK-SRS-001 第 65 行引用 PRD §5（非 §4）
- 全仓 Grep 校验：无残留"PRD §4 非功能"错位、无新增状态副本漂移
- 仓库已初始化 Git，首个 commit 已生成，且 .gitignore 生效、无密钥入库

## 安全与隐私验收
- 不引入新敏感字段；git 首个 commit 不含任何密钥 / .env / 授权码（含网易 163 授权码等）

## 性能验收
- 不适用（纯治理文档）；不涉及运行时性能

## 变更预算（change_budget）
- max_files：7（含本任务单本身；含新增 .gitignore）
- expected_prod_lines：治理补丁为主，小幅增改
- expected_test_lines：0

## 必须运行的测试命令
- 无（文档任务）；交付前执行全仓一致性 Grep 校验 + `git log` 确认首个 commit

## 回滚方法
- 修改前保留原文件副本/patch，初始化 Git 后使用 git restore/revert；本任务不产生迁移

## 强制停止条件（与 `AGENTS.md §2` 一致）

判定口径：**看变更是否已在本任务单「已批准的 DB / API / 依赖变更」章节中逐项列明，而不是看变更类型本身。**

- **可继续**：变更已在「允许修改路径」列明且为治理 / 文档性质，依据工件在 `docs/baseline.yml` 为 `approved`。
- **必须立即停止并报告（不得自行决定）**：出现任何未在「允许修改路径」列明的变化，包括但不限于
  - 新增外部依赖（npm / pip 包）；
  - 新增或修改数据库表、字段、索引、迁移；
  - 新增或修改公开 API / SSE 事件 / 契约字段；
  - 改变加密、密钥、鉴权或权限策略；
  - 修改 PRD 业务需求或领域模型实体 / 不变量；
  - 实现任务范围外的功能（含 `deferred` 延后项）；
  - 改动 Agent / AI Infra 参考文件；
  - 把密钥 / 授权码写入版本库或任何文档。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：adc7c8d3df42f0ecfb6dd846317ce6de04760cc5（tag: gov-sync-001-verified）
- 修改文件清单：baseline.yml / TASK-TEMPLATE.md / AGENTS.md / PROJECT_STATE.md / TASK-SRS-001.md / .gitignore / tasks/TASK-GOV-SYNC-001.md（本任务单自身，重新打开回填修复）（仓库操作：git init + 治理收尾最终 commit，打标签 gov-sync-001-verified）
- 测试命令及结果：不适用（纯文档/治理）；全仓 Grep 校验通过（无残留 "PRD §4 非功能"、无新增状态副本漂移）
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：Grep 输出 + `git log` 最终 commit + 标签 gov-sync-001-verified + AGENTS §9 / 规范影响评估章节已落地 + 交互输出语言规则（SSOT）已落地（注：该语言规则超出原授权 §9，属已接受治理偏离，见「是否偏离 TASK」）
- 变更预算实际值：max_files 7 / 实际 7（baseline.yml, TASK-TEMPLATE.md, AGENTS.md, PROJECT_STATE.md, TASK-SRS-001.md, .gitignore, tasks/TASK-GOV-SYNC-001.md）；prod 0 / test 0
- 未解决风险：无
- 是否偏离 TASK：是——新增 AGENTS「交互输出语言」SSOT 与 §5 输出语言确认，超出原授权 AGENTS §9 内容范围；经本次独立复核接受为治理补充，不涉及产品行为。另：P0-1/P0-2 收尾修复（允许路径含自身、max_files 7、交付证据实际 7、verified_commit 真实 SHA）属本 TASK 重开范围，不计入偏离。
- 规范影响结论：none（纯治理变更，不改业务行为）
- spec_sync：clean
- verified_commit：adc7c8d3df42f0ecfb6dd846317ce6de04760cc5（tag: gov-sync-001-verified；治理收尾最终 commit；非 baseline commit b2b6ac8）

## 关闭结论（关闭门禁复核 — 2026-08-07）

任务于治理收尾回合正式关闭。关闭门禁四条件逐项复核：

1. **测试通过**：纯文档/治理变更，无代码/测试；全仓 Grep 校验通过（无残留 "PRD §4 非功能"、无新增状态副本漂移）。
2. **规范影响已处理**：规范影响结论 = none（纯治理变更，不改业务行为）；baseline.yml 中 srs 等 stage-1..4 仍为 pending，未越权推进。
3. **spec_sync = clean**：仅固化既有治理模型于四个文件，无规范间冲突。
4. **真实 verified_commit**：`adc7c8d3df42f0ecfb6dd846317ce6de04760cc5`（tag: gov-sync-001-verified），非 tag 占位、非 baseline commit b2b6ac8。

其他治理账目收正确认：
- 基线 commit = `repository_not_initialized`（任务启动真实历史，未被完成态覆盖）。
- verified_commit = 真实 SHA（C-commit clerical 回填；V-commit 因自引用悖论曾暂填 tag 名，已纠正）。
- 偏离记录真实：是否偏离 TASK = 是（AGENTS「交互输出语言」SSOT + §5 确认超出原授权 §9，经独立复核接受为治理补充，不删规则不伪造）。
- TASK-SRS-001 基线 commit 本轮未改（防自引用），待 SRS 正式开始时以治理收口最终 SHA 回填。

状态：已关闭（Closed）。

## 阶段性证据
- 任务创建后由用户确认范围，再执行补丁。

## 关联
- Change Request：无
- 测试任务：无（文档）
