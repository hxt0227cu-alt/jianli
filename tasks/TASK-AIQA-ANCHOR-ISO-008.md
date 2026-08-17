# TASK-AIQA-ANCHOR-ISO-008 多轮锚点隔离（Prompt 加固）

> 承接外部评审（DeepSeek②"多轮幻觉链裸奔"）的真增益：当前多轮仅为有界回填
> （`_MAX_HISTORY_MESSAGES=6`）+ 每轮重注入硬性事实卡重锚；但 LLM 仍可能沿用上一轮
> 自身生成的推断/总结，形成错误传播。本任务在 system prompt 加"锚点隔离"指令，
> 强制每轮独立基于本轮检索证据与事实卡作答，不继承上一轮推理。

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：5c0e4cc

## 精确规范引用
- SRS §（知识库问答）：范围内命中率≥90%、越界拒答率≥95%、事实编造=零容忍
- `app/aiqa/persona.py` `_SYSTEM_PROMPT` / `build_system_prompt`
- `app/aiqa/service.py` `_MAX_HISTORY_MESSAGES` / `_load_history`

## 需求来源
- 外部评审 DeepSeek②（多轮幻觉链防护）；SRS 事实零容忍要求

## 目标
在 system prompt 增加"锚点隔离"规则：历史轮次仅供理解上下文，本轮回答必须完全基于
本轮【已知资料】检索证据与【硬性事实卡】事实，不得引用/延续/依赖上一轮生成的任何推断、
总结或结论；证据不足按越界拒答，而非沿用上一轮说法。

## 非目标
- 不做历史摘要（长对话摘要已在 `_MAX_HISTORY_MESSAGES` 注释中标为 out of scope）
- 不改检索/路由逻辑、不改 API/SSE 契约、不改阈值

## 允许修改路径
- `apps/api/app/aiqa/persona.py`（`_SYSTEM_PROMPT` 增加多轮锚点隔离段落）

## 禁止修改路径
- `service.py` 检索/路由/`_load_history` 逻辑
- 任何 API / SSE / DB / 加密 / 鉴权变更

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估
- behavior_change：true（收紧多轮忠实度，但属对既有"事实零容忍"要求的强化，非新增用户可观察契约）
- affected_specs：srs none / domain_model none / openapi none / security none / test_plan none
- reason：纯 prompt 层加固，不改变接口/契约/可观察行为边界；SRS 已要求事实零容忍，本任务使实现更贴合该要求。
- 分类：Bug 修复使代码重新符合现有 SRS（多轮忠实度是 SRS 零容忍的应有之义）→ 不需要改 SRS。

## 功能验收
- 单轮行为不变（无历史时指令为 no-op）
- 多轮：上一轮植入的错误推断在下一轮不被继承（验证用例：turn1 含错误前提，turn2 追问应基于检索/事实卡纠正，而非沿用）

## 安全与隐私验收
- 不改变鉴权/加密；prompt 不泄露系统内部

## 性能验收
- 仅增加 system prompt 文本，无额外检索/调用；延迟影响可忽略

## 变更预算
- max_files：1
- expected_prod_lines：~4（一段 prompt 文本）
- expected_test_lines：0（多轮忠实度验证走手动/脚本，不新增冻结 TC）

## 必须运行的测试命令
- `$PY -m pytest tests/aiqa/test_aiqa.py -q`（DB-free 回归，确认路由/拒答未退化）
- 多轮忠实度：手动用 `scripts/measure_cost.py` 或 curl 两轮对话验证（真 LLM）

## 回滚方法
- 回退 `persona.py` 单段 prompt 文本即可

## 强制停止条件
- 若出现任何未列明的 API/DB/加密变更 → 停止并报告

## 交付证据（关闭前填写）
- commit / PR：
- 修改文件清单：
- 测试命令及结果：
- lint / typecheck：
- DB 迁移验证：无
- 验收证据：
- 变更预算实际值：
- 未解决风险：
- 是否偏离 TASK：
- 规范影响结论：none
- spec_sync：clean
- verified_commit：
- 关闭门禁：①②③④ 全满足方可关闭
