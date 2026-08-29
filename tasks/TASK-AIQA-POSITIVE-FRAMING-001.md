# TASK-AIQA-POSITIVE-FRAMING-001 正向面试回答聚焦

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：04c85fcf5c1fb4c74bb91690fcb1705c1ac0fc82

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.2
- `docs/requirements/use-cases.md` UC-03 / UC-04 / UC-05
- `docs/test/test-plan.md` TC-AI-004
- `apps/api/tests/aiqa/test_persona_style.py`

## 需求来源
- 用户于 2026-08-29 页面验收指出：“最有成就感”回答主动追加安全比例、未验证路径等不利信息，不利于面试展示。
- 用户当前消息明确批准调整 Persona Prompt；不涉及工具权限变更。

## 目标
让成就、优势、岗位匹配和项目价值等正向面试问题只聚焦成果、贡献与价值，不主动追加失败、局限、未上线或未验证信息。

## 非目标（明确排除）
- 不删除 canonical corpus 中的真实证据边界。
- 不允许编造、伪造或把未验证事实表述为已验证。
- 不改变明确追问不足/失败/边界时的诚实回答原则，但要求简短并以解决动作和演进方案积极收束。
- 不修改 API、数据库、依赖、检索算法、阈值、权限或 Agent 工具。

## 允许修改路径
- `tasks/TASK-AIQA-POSITIVE-FRAMING-001.md`
- `apps/api/app/aiqa/persona.py`
- `apps/api/tests/aiqa/test_persona_style.py`

## 禁止修改路径
- `apps/api/app/aiqa/service.py`
- `apps/api/tests/aiqa/test_rag_eval.py`
- API / migration / dependency / auth / agent-tool / canonical corpus 相关文件

## 已批准的 DB / API / 依赖变更
- 无
- 已批准 Prompt 变更：用户当前消息明确要求停止在面试回答中主动输出不利信息；按“正向问题不主动披露、直接边界追问保持诚实并积极表达”的安全口径实施。

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：修复 Persona 未遵守 SRS §3.2 L1 人格层“简洁、按问题作答”的跑题行为；事实边界、拒答、安全和外部契约均不变。

## 功能验收
- 正向问题的 Prompt 明确禁止主动追加局限、失败、未上线、未验证或负面指标。
- 既有正向 few-shot 不再以“不足/局限/失败”结尾。
- 明确询问不足时仍不得撒谎，以“边界—解决动作—下一步”积极收束。
- 页面真实复问“你最有成就感的一段工程经历是哪一段？”时，不出现 67/84、80%、未验证、失败、局限等主动拆台内容。

## 安全与隐私验收
- “绝不编造、证据不足拒答、预约白名单工具”规则保持不变。
- 不扩大公开信息范围，不改变隐私护栏。

## 性能验收
- 不新增网络请求、模型调用或检索阶段。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：30
- expected_test_lines：25

## 必须运行的测试命令
- `PYTHONPATH=. pytest tests/aiqa/test_persona_style.py -q`
- `ruff check app/aiqa/persona.py tests/aiqa/test_persona_style.py`
- `mypy app/aiqa/persona.py`
- 重启 API 后在页面真实复问成就题并检查回答内容。

## 回滚方法
- 回退本任务对 `persona.py` 与风格测试的增量，重启 API 恢复旧 Prompt。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要删除真实语料、修改安全拒答、工具权限、API、数据库、依赖或检索行为时立即停止。
- 冻结验收失败或超过 3 个文件时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：待完成
- 修改文件清单：待完成
- 测试命令及结果：待完成
- lint / typecheck：待完成
- DB 迁移验证：无
- 验收证据：待完成
- 变更预算实际值：待完成
- 未解决风险：待完成
- 是否偏离 TASK：待完成
- 规范影响结论：none
- spec_sync：待完成
- verified_commit：待完成

## 关联
- Change Request：无（符合既有 Persona 简洁与问题相关性要求的 Bug 修复）
- 测试任务：TC-AI-004
