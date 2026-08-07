# TASK-SRS-001 生成 SRS v1.0（含第六轮复评治理微补丁 + TASK 启动前补丁）

> 复制本模板为 `tasks/TASK-SRS-001.md`，作为 AI **仓库变更**的唯一范围约束。无任务单不得写入仓库，包括文档、设计、测试和代码变更。

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.2 / AI 治理 1.0.1（取自 `docs/baseline.yml`；版本如下，评审状态以 baseline.yml 为准）
- 基线 commit：d7510254a9e900fab06ebc5216cd2dd68bd2eef2（治理完全收口的最终 commit；SRS v1.0 基于此 commit 生成。`gov-sync-001-verified` 为 TASK-GOV-SYNC-001 的 verified snapshot 标签、当前指向 `adc7c8d3…`，不表示 SRS baseline，二者不得混用）

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
- docs/requirements/SRS-大纲-吸收映射.md   # 【已记录偏离·临时工件】本轮误建，不在原允许路径（原仅 docs/requirements/SRS.md 为主交付物）；仅临时授权删除——其大纲与映射已吸收进 SRS.md，确认后删除，不形成第二份需求工件（详见「是否偏离 TASK」）

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
- commit / PR：`ed926ca`（TASK 机械收口：基线锚点去错误 tag 注释 + P0-2 偏离记录）/ `b7ef847`（SRS v1.0 正文 + baseline srs→1.0/review）/ `9b3102c`（删除临时草案 SRS-大纲-吸收映射.md）/ `bdba9f4`（review correction）/ `8794aea`（小范围收口，含已记录的 domain-model.md 越界）/ `97e44d4`（证据回填）/ **`d166992`（2026-08-08 SRS impact review：based_on→1.1.4 + §6.3 改写 + 四处版本引用同步 + spec_sync→clean）**；**`26ae844`（SRS v1.0 批准锚点 / approval_commit）**；**`06798a2`（TASK-SRS-001 关闭快照 / verified_commit）**；SRS 现已 approved（26ae844）/ Closed（06798a2），本任务已关闭。
- 修改文件清单（**累计去重 6 个**，按 `git show --stat` 逐提交核对）：
  1. `tasks/TASK-SRS-001.md` — 本任务单（锚点注释修正 / 偏离记录 / 证据回填 / spec_sync 流转 / impact review 记录）
  2. `docs/requirements/SRS.md` — v1.0 正文新建 + review correction + 小范围收口 + **本轮 impact review 文字同步（§6.3 + 四处版本引用）**
  3. `docs/baseline.yml` — `srs`→1.0/review；**本轮 `srs.based_on.domain_model` 1.1.3→1.1.4**
  4. `PROJECT_STATE.md` — review 态同步（`bdba9f4`）
  5. `docs/requirements/SRS-大纲-吸收映射.md` — 误建后删除（**已记录偏离**，见「是否偏离 TASK」）
  6. `docs/design/domain-model.md` — **越界改动（`8794aea`）**，已由 TASK-DM-001 独立追认承载，本任务不再重复主张其成果
- 测试命令及结果：全文一致性 Grep 校验（见「验收证据」）；非执行测试
- lint / typecheck：不适用（文档任务）
- DB 迁移验证：不适用（本任务无迁移）
- 验收证据：① R1–R26 覆盖检查（全部映射到 SRS 节）；② UC-01–23 覆盖检查；③ SRS 内部交叉引用检查；④ 与领域模型 v1.1.2 不变量冲突检查（无新增/冲突）；⑤ deferred/非目标越界检查（未新增功能/未扩 MVP）；Grep 校验无 `review` 硬编码残留。
- 变更预算实际值：`max_files` = 8（含本任务单）；**实际累计去重 6 个文件**（5 处改动 + 1 处删除，清单见上），**未超预算**。本轮 impact review 未引入新文件——所触 3 个文件（`docs/baseline.yml` / `docs/requirements/SRS.md` / `tasks/TASK-SRS-001.md`）均已在既有清单内且在「允许修改路径」内。
  - 账目说明：此前记为"≈ 4 文件改动 + 1 删除"为**估算且偏低**，遗漏 `PROJECT_STATE.md`（`bdba9f4`）与越界的 `docs/design/domain-model.md`（`8794aea`）。现按 `git show --stat` 逐提交核实改为 6，避免重演 TASK-DM-002 的账目偏差。
- 未解决风险：无（范围内已闭环）。SRS 现已 approved，参与 baseline precedence 裁决（srs 高于 PRD/用例规约，行为唯一源生效）；PRD §8.2 外部依赖（SMTP/域名/飞书授权/知识库文件/时间线）仍待确认，不阻塞设计但阻塞对应集成验收/上线（范围外开放项，不阻塞本任务关闭）；UI 线框冻结、架构/安全/OpenAPI/测试计划 pending 为下游阶段，非本任务范围。
- 是否偏离 TASK：是——误建临时文件 docs/requirements/SRS-大纲-吸收映射.md，超出本任务原允许路径（仅 docs/requirements/SRS.md 为主交付物）。该偏离已如实记录；其大纲与映射已吸收进 SRS.md，确认后删除该临时文件，后续仅维护唯一正式工件 SRS.md（不形成第二份需求工件）。其余改动（baseline 锚点去错误 tag 注释、baseline.yml srs=review、SRS 正文）均在授权范围内
- 规范影响结论（两类，须分开读，不得互相顶替）：
  1. **本任务自身改动 → 对其他规范的影响**：`none`。本任务产出为 SRS 正文与治理收口，不改业务行为、不新增实体/接口/状态迁移；SRS 由 review→approved 属状态推进，不影响 PRD / 领域模型 / OpenAPI / 安全设计。
  2. **上游 domain_model 1.1.3→1.1.4 → 对本任务工件（SRS）的影响**：**`需文字同步、不改变用户可观察行为`（明确不是 none）**。SRS §6.3 原括注"领域模型 §6.1 记为 Argon2id"在 v1.1.4 后已成事实性错误，必须改写；另有四处上游版本引用需同步。已于 2026-08-08 impact review 中处理完毕（详见「阶段性证据」末条）。按 `AGENTS.md §9.4` 分类，属"不改变用户可观察行为"，**不触发 Change Request**。
- spec_sync：**clean**（2026-08-08：上游 `domain_model` v1.1.4 已获用户明确批准（独立锚点 `f537296`），本任务据此执行 SRS impact review 并完成全部文字同步——`baseline.srs.based_on.domain_model` 1.1.3→**1.1.4**；SRS §6.3 过期的「领域模型 §6.1 记为 Argon2id」描述已修正；SRS 顶部 based_on / §1.1 / §1.3 / §6 标题四处上游版本引用同步至 1.1.4。`based_on` 与 `artifacts` 现一致，机器门禁不再报 needs impact check。**影响结论记为「需文字同步、不改变用户可观察行为」，未记为 none**——详见「阶段性证据」末条。SRS 已于 26ae844 获批；spec_sync=clean 与批准状态均已闭环。）
- approval_commit：`26ae8440c89ed680341ee1c6cecb036b27b224ec`（本回合单一用途提交，仅推进 baseline `srs.status` review→approved；**不得复用旧误批准锚点 173cf9b6ffdf75acc4802398644ba67fb06f6cf6**）
- verified_commit：`06798a2815d60a50caebe3ce6582553531be8dea`（`06798a2`，SRS 关闭快照：含 SRS approved + spec_sync=clean + 本任务 Closed + PROJECT_STATE 同步的完整验证快照；与 approval_commit `26ae844` 分离，避免自引用）

## 关闭结论（SRS v1.0 独立评审批准，2026-08-08 正式关闭）

任务于 SRS 独立评审通过后正式关闭（用户 2026-08-08 指令：「我独立评审通过并批准 SRS v1.0」；AI 不代签）。关闭门禁四条件逐项复核：

1. **测试通过**：纯文档/治理变更，无代码/测试；一致性 Grep 校验通过（无 `review` 硬编码残留 / 无 `待复评` / 无违规 `PRD §8.5` 引用 / 活动规范正文无 `purge_before` 残留字段）。
2. **规范影响已处理**：规范影响结论 = none（纯文档收口，不改业务行为）；SRS 由 review→approved 是状态推进，不影响其他规范。
3. **spec_sync = clean**：SRS based_on = prd 2.3.3 / use_cases 1.7.2 / domain_model 1.1.4，上游版本未变且均为 approved（1.1.4 于 `f537296` 批准）；R1–R26 / UC-01–23 双向追踪完整，无 impact check 需求（2026-08-08 impact review：需文字同步、不改变用户可观察行为，已处理且 spec_sync=clean）。
4. **真实 verified_commit**：`06798a2815d60a50caebe3ce6582553531be8dea`（`06798a2`，SRS 关闭快照：含 SRS approved + spec_sync=clean + 本任务 Closed + PROJECT_STATE 同步的完整验证快照）。

其他治理账目收正确认：
- 批准锚点（approval_commit）= 单一用途提交 `26ae8440c89ed680341ee1c6cecb036b27b224ec`：仅推进 baseline `srs.status` review→approved；**不得复用旧误批准锚点 173cf9b6ffdf75acc4802398644ba67fb06f6cf6**（该锚点为 2026-08-07 误批准，已作废历史，仍保留但不复用）。
- 基线 commit = `d7510254…`（SRS 启动前基线，未被完成态覆盖）。
- SRS 内容收口 commit 链：b7ef847（正文）→ bdba9f4（review correction）→ 8794aea（小范围收口）→ 97e44d4（TASK 证据回填）→ d166992（impact review）→ 26ae844（批准锚点 / approval_commit）→ 06798a2（关闭快照 / verified_commit）。
- TASK-SRS-001 关闭后，用例规约冻结为历史输入（SRS 行为唯一源生效；precedence 中 srs 高于 use_cases/prd）。

状态：Closed（2026-08-08）。

## 阶段性证据
- 治理微补丁（上轮）全仓 Grep：通过（无 `待复评` / `accepted_adr` / `security_design` / 旧 v2.3 准入结论 / 硬编码 `review` / `approved` 重复 残留）
- TASK 启动前补丁（本轮）：范围扩至 R1–R26、领域模型章节号修正、AGENTS 加入允许路径、SRS 状态流转写入、交付证据清空为回填占位 → <任务完成后回填验证>
- SRS 启动机械收口（本轮）：P0-1 已修正——基线 commit 保留真实 SHA `d7510254…`，删除其错误 `(tag: gov-sync-001-verified)` 注释（`gov-sync-001-verified` 为治理任务标签、指向 `adc7c8d3…`，不表示 SRS baseline）；P0-2 已记录偏离——误建 `SRS-大纲-吸收映射.md` 超出原允许路径，仅临时授权删除，其大纲/映射已吸收进 SRS.md 并删除该临时文件；六项结构问题按用户结论直接执行，未再询问
- SRS review correction（用户独立评审反馈，本轮）：修复 P0-1 基线 commit 措辞（顶部/页脚「本文件生成 commit」→「SRS 输入基线 commit」，明确 `d7510254` 为启动前基线、正文于 `b7ef847` 生成）；P0-2 同步 `PROJECT_STATE.md` 至 review 态（当前阶段/当前任务/下一步/最后更新）；P0-3 §1.1 与 §10 页脚「行为唯一源」改为「approved 后成为」，并新增 §1.1 状态机所有权迁移（ownership transition）条款、§1.4/§6.2 对齐；P1-1 删除 SRS 内复制的 deferred 六项清单；P1-2 删除违规 `PRD §8.5` 引用（腾讯云→§4 系统集成、成本→§5 非功能需求）；§4.3「中心化通道广播」改为一致性/有序恢复行为约束（机制留 ADR）；§3.8「Outbox 事件表」软化为「可靠持久化的业务事件（Outbox 模式）」。SRS 仍 `status=review`，未 approved，TASK 保持开启；关闭证据（规范影响结论/spec_sync/verified_commit）待独立评审通过后补。（review correction commit：`bdba9f4`）

- SRS 小范围收口（用户第二轮独立评审反馈，本轮）：按用户清单做最小范围修正——不扩需求、不重写、不动 baseline 状态（srs 仍 review）。① 密码哈希算法冲突（#1）：SRS §6.3 不再预选算法，改「由《安全设计》ADR 裁定」，标注 PRD §8.7(BCrypt) 与领域模型 §6.1(Argon2id) 冲突待安全设计；领域模型 §1 存储策略 + §6.1 同步加「待安全设计裁定」标注（保留 Argon2id 占位、不改 approved 状态）。② 通知失败态缺失（#2）：SRS §6.2 NotificationEvent 生命周期补 `failed`（进入 Delivery 重试/死信），与领域模型 §5 对齐。③ 手动重发限频不可验收（#3）：SRS §5.6 补可测阈值「同账号每 10 分钟≤5 次、每小时≤20（待评审确认，先按此验收）」。④ 领域模型编码门禁表述错误（#4）：§10 末尾改引用 baseline `development_gate` 全 10 项门禁，纠正「仅接口契约+测试计划通过」误述。⑤ 两处文档缺陷（#5）：SRS §5.3 裸 `§8.6`→`PRD §8.6`；领域模型 §9 `purge_before`→`purge_after` 改名痕迹清除。SRS 仍 `status=review`，未 approved，TASK 保持开启；关闭证据（规范影响结论/spec_sync/verified_commit）待独立评审 approved 后补。（closeout commit：8794aea）

- 误批准回退与修正（2026-08-07，用户纠偏）：上轮误将 srs.status 置 approved 并关闭本 TASK、启动 UI 线框；用户明确当时授权仅为「先完成领域模型独立任务、升版、impact review 后再批准 SRS」，未授权直接批准。现按用户 7 步指令向前修正（不重写 Git 历史）：① baseline srs.status 恢复 review；② 本 TASK 重新打开、spec_sync 改 dirty（记录 8794aea 改 domain-model.md 超出本 TASK 允许路径）；原关闭结论（line 107–121）作废；③ 新建 TASK-DM-001 对 domain-model.md 升版并评审密码算法裁定边界/门禁引用/字段清理；④ SRS based_on 更新至新 domain_model 版本 + impact review；⑤ 删除 SRS §5.6「待评审确认」字样（用户已确认阈值：同账号每 10 分钟≤5、每小时≤20）；⑥ 上述完成后由用户独立评审批准 SRS（AI 不代签）；⑦ TASK-UI-001 与 ui-wireframe.md 标记基线无效、不得评审。

- SRS impact review（领域模型 1.1.2→1.1.3，2026-08-07）：上游 domain_model 升版触发基于 based_on 的 impact check。评估范围 = TASK-DM-001 的 3 类修改对 SRS 行为的影响：① 密码算法裁定边界（domain §1/§6.1）—— SRS §6.3 已声明「由《安全设计》ADR 明确、不预选算法」，与领域模型一致，无冲突；② 门禁引用（domain §10）—— 改引用 baseline `development_gate` 全 10 项，不影响 SRS 行为；③ 字段清理（domain §9 purge 改名痕迹）—— SRS 不定义物理表，无行为影响。结论：**impact = none**，SRS 无需改业务内容，仅将 based_on 的 domain_model 由 1.1.2 同步至 1.1.3。spec_sync 由 dirty 转 clean。待用户独立评审批准 SRS（baseline srs.status: review→approved）后，本 TASK 方可关闭。

- 领域模型状态回退与 spec_sync 再置 dirty（2026-08-07，用户纠偏第 2/4 步）：上轮将 domain_model 1.1.3 误置 approved、TASK-DM-001 spec_sync 误置 clean、并据以将本 TASK spec_sync 转 clean。现按用户指令向前修正——baseline `domain_model.status` 回退 review；TASK-DM-001 spec_sync 改 dirty（pending downstream impact review）；本 TASK（TASK-SRS-001）spec_sync 由 clean 重新置 dirty，明确"domain_model 1.1.3 未经用户明确批准前，不得宣称 SRS based_on 已正式同步"。SRS §1.1 机械残留的"v1.1.2"更正为"v1.1.3"。待用户批准领域模型后，再由本 TASK 重新执行 impact review 并视情况转 clean。

- 领域模型批准与 SRS impact review 收口（2026-08-08，用户明确批准 domain_model 1.1.3）：执行治理 ⑥⑦ 步骤——① baseline `domain_model.status` 置 approved（锚点 f64b6de）；② TASK-DM-001 补 verified_commit=f64b6de 并关闭（e216d01）；③ baseline `srs.based_on.domain_model` 由 1.1.2 同步至 1.1.3；④ 重做 impact review：上游 domain_model 1.1.3 的 3 类修改（密码算法裁定边界 §1/§6.1 / 门禁引用 §10 / 字段清理 §9）均不改实体、不变量、状态机——与 SRS §6.3「待安全设计裁定」一致、§10 门禁引用与 baseline `development_gate` 全 10 项一致、§9 字段清理不影响 SRS 行为；结论 **impact = none**，SRS 无需改业务内容；⑤ spec_sync 由 dirty 转 clean。SRS 仍 status=review，**未代签 approved**——待用户独立评审批准后生成新 verified_commit 并关闭本 TASK（关闭结论维持"已作废"记录仅作历史，新关闭结论待 SRS 批准后写）。

- 领域模型版本取代与 spec_sync 回退 dirty（2026-08-08，用户评审指令第 1/5/9 步）：用户指出 **v1.1.3 已在 `f64b6de` 正式批准，`236d302` 又改了其规范正文**——同一版本号不得对应批准前后两份内容，且**不得以"避免 SRS based_on 连锁变更"为由复用 1.1.3**。故：① TASK-DM-001 恢复为**历史已关闭**（f64b6de 保留为旧版 1.1.3 真实批准锚点，注明已被取代，不否认历史批准）；② 新建 **TASK-DM-002** 承载密码算法中性化并升版 **domain_model v1.1.4**（baseline: 1.1.4 / review）；③ `baseline.srs.based_on.domain_model` **有意保留 1.1.3**，使机器门禁（based_on ≠ current）正确显示上游已变更、需 impact review；④ 本 TASK `spec_sync` 由 clean 回退 **dirty**。**待办（待用户批准 domain_model v1.1.4 后执行）**：SRS impact review —— 将 `based_on.domain_model` 更新为 1.1.4；修正 SRS §6.3「（当前 PRD §8.7 记为 BCrypt、领域模型 §6.1 记为 Argon2id，二者冲突待安全设计裁定）」中已过期的 Argon2id 描述（1.1.4 起领域模型不预选算法，且新增 ADR 与 PRD §8.7 冲突须走规范影响/变更评审的条款）；**影响结论不得记为 none**，记为「需文字同步、不改变用户可观察行为」；完成后 spec_sync 转 clean。SRS 仍 `status=review`，**待用户独立评审批准，AI 不代签**。

- **SRS impact review（领域模型 1.1.3 → 1.1.4，2026-08-08 执行完毕）**：触发条件 = `baseline.srs.based_on.domain_model`(1.1.3) ≠ `artifacts.domain_model`(1.1.4)，机器门禁报 needs impact check。上游 v1.1.4 已于独立批准锚点 `f537296` 获用户明确批准，本任务据此执行。

  **评估范围**：TASK-DM-002 在 v1.1.4 引入的两类修改。

  | 上游修改 | 是否改变用户可观察行为 | 对 SRS 的处理 |
  |---|---|---|
  | ① 密码算法中性化（domain §1 存储策略 / §2.3 类图 / §4 ER 图 / §6.1 字段表共 4 处清除 Argon2id 实现指向） | **否** —— 领域模型自 v1.1.3 起即声明"算法待《安全设计》ADR 裁定"，SRS §6.3 亦一贯声明"SRS 不预选算法"。系统对外行为（登录校验、密码找回、token 存储）不因算法未定而改变；算法最终落点仍在《安全设计》ADR。 | **需文字同步**：§6.3 原括注"领域模型 §6.1 记为 Argon2id"在 1.1.4 后已成**事实性错误**（领域模型不再记任何算法），必须删除并改写。 |
  | ② 新增/收紧冲突升级条款（ADR 拟选算法与 PRD §8.7 BCrypt 不一致 → 须先经 Change Request 更新并批准受影响规范，规范同步完成前不得实现） | **否** —— 属规范变更治理流程约束，不产生新的系统功能、接口、错误码或状态迁移。 | **需文字同步**：§6.3 补入同口径约束，避免 SRS 与领域模型出现流程口径分歧。 |

  **结论：`需文字同步、不改变用户可观察行为`（明确 ≠ none）。** 理由：SRS 正文确有**过期描述**（§6.3 的 Argon2id 归属陈述已与 v1.1.4 不符），记为 none 将等同于宣称"SRS 无需任何改动"，与事实不符；但该同步**不改变任何用户可观察行为**，因此按 `AGENTS.md §9.4` 分类**不触发 Change Request**，也不需重做需求评审。

  **实际改动**：① `docs/baseline.yml` — `srs.based_on.domain_model` 1.1.3→1.1.4（含注释更新）；② `docs/requirements/SRS.md` — §6.3 改写 + 顶部 based_on / §1.1 / §1.3 / §6 标题四处版本引用同步；③ 本任务单 — spec_sync dirty→clean 与本条记录。**未改动**：需求编号、行为约束、错误码、状态机、非功能阈值、追踪矩阵。

  **下游连带**：本 impact review 完成且 spec_sync=clean，构成 **TASK-DM-002** 的关闭前置（其 spec_sync 据此转 clean）。**SRS 自身仍 `status=review`，批准权在用户，AI 不代签；本任务不关闭。**

## 关联
- Change Request：无（本轮 impact 为文字同步级，按 `AGENTS.md §9.4` 不触发变更流程）
- 上游任务：TASK-DM-001（domain_model v1.1.3，已关闭，锚点 `f64b6de`）→ **TASK-DM-002（domain_model v1.1.4，已批准，锚点 `f537296`）**
- 测试任务：无（文档）
