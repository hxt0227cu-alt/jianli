# TASK-KB-JIANLI-TECHNICAL-DEPTH-008 Jianli 源码级技术追问语料

## 任务类型
- implementation
- test
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`2eec60f23655233c19e4ed5a21f73062b0e595e3`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §7` 冻结验收测试
- `AGENTS.md §9` Fact Source Routing / Review Mode
- `docs/fact-consistency/fact-bank.md` Jianli 事实组
- `TC-AIQA-RAG-EVAL`（`apps/api/tests/aiqa/test_rag_eval.py`）
- `docs/api/sse.md §3`

## 需求来源
- 用户明确要求对 Jianli 执行与 Litchi/Sleep 相同的源码取证和技术知识库升级。

## 目标
按源码→测试→迁移/配置→运行证据顺序核验当前实现，在不增加 canonical corpus 20 篇总数的前提下，将现有 7 篇 Jianli 文档升级为可回答调用链、事务并发、检索排序、Agent 工具、安全韧性、观测评测和证据边界的技术追问语料。

## 非目标（明确排除）
- 不修改 Litchi、Sleep、个人资料语料或页面展示。
- 不修改业务代码、API、SSE、数据库、迁移、依赖、权限、Prompt、工具白名单、检索算法、分块算法或评测阈值。
- 不把规范设计、未运行 GitHub Actions、未完成容器 smoke 或正式域名部署写成已实现运行事实。
- 不公开密钥、邮箱验证码、预约 PII、日志原文、Prompt、知识原文、绝对路径或内部标识。

## 允许修改路径
- `tasks/TASK-KB-JIANLI-TECHNICAL-DEPTH-008.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `apps/api/app/aiqa/content.py`
- `docs/fact-consistency/fact-bank.md`

## 禁止修改路径
- 上述清单之外全部文件。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：仅深化作品集事实语料和等价检索验收，不改变运行逻辑或对外契约。

## 功能验收
- canonical corpus 保持 20 篇，七个 Jianli 文件名不变。
- 覆盖问答/SSE 调用链、混合检索与 RRF/阈值、Agent 工具循环与 RBAC、预约事务并发、通知 Outbox、缓存/熔断、可观测性、评测 CI 和失败复盘。
- 每项事实区分源码实现、测试证据、运行证据和未完成边界。
- 新增 Jianli 技术追问检索用例，不删除或放宽既有命中、拒答、误拒与隐私断言。
- 正式重灌库后 20 篇 canonical 全部 active + indexed。

## 安全与隐私验收
- 不写入问题/回答/Prompt/知识原文、预约 PII、密钥、高基数 ID、日志正文或绝对路径。
- `answer.trace` 明确为脱敏执行事实，不表述为模型思维链。

## 性能验收
- 不改变检索阈值、top-k、分块参数或任何既有测试门槛。
- 真实 BGE-M3 冻结门禁全部通过；新增 Jianli 技术问题稳定引用目标文档。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：120
- expected_test_lines：320

## 必须运行的测试命令
- 真实 PG/Redis/BGE-M3：`PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `ruff check app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `mypy app/aiqa/content.py`
- `python -m compileall -q app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `python scripts/seed_kb.py` 并核对 canonical active/indexed 数量。
- 真实模型复验 Jianli 源码级技术追问和证据边界。

## 回滚方法
- Git revert 本任务提交，并使用上一版本 `scripts/seed_kb.py` 重新灌入 canonical corpus。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 任一冻结断言下降、需要修改任务外文件、需要 API/DB/依赖/权限/阈值变化或超过预算时立即停止报告。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`ee5b70f`（本地 commit；未创建 PR）
- 修改文件清单：本任务单、`apps/api/tests/aiqa/test_rag_eval.py`、`apps/api/app/aiqa/content.py`、`docs/fact-consistency/fact-bank.md`
- 测试命令及结果：
  - 真实 PG/Redis/BGE-M3 全套：`PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q` → `7 passed in 119.84s`
  - Jianli 深度语义追问：`test_rag_semantic_hit_cases -q -s` → `20/20`，`avg-rank 1.6`，`1 passed`
  - 正式灌库：`python scripts/seed_kb.py` → canonical `20/20 active + indexed`
  - 真实 DeepSeek V4 Flash 抽检：检索词 fallback、并发抢 Slot、CI 运行边界均 `HTTP 200`、`grounded=true`，首引对应 Jianli 文档；并发回答明确区分行锁与部分唯一索引，CI 回答明确无远端 Actions run
- lint / typecheck：`ruff check ...` → pass；`mypy app/aiqa/content.py` → 0 error；`compileall` → pass
- DB 迁移验证：无
- 验收证据：七篇 Jianli canonical 文件名不变；新增八条源码级语义追问；事实库新增 FQ-51~58；未删除或放宽既有拒答、隐私、误拒断言；真实检索与模型回答均区分实现证据和待上线边界
- 变更预算实际值：4 文件；业务静态语料 `+39/-32`，测试/语料 `+68/-42`，事实文档 `+42/-2`，任务治理文件 `+104`；未超过 `max_files=4`
- 未解决风险：每次正式重灌采用软删，当前 historical 为 212 行；不占 canonical 20 篇 active 限额，但长期清理策略属于后续数据库维护任务。远端 Actions、正式域名和完整观测栈 smoke 仍为已如实披露的上线验收项
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：not_required（无需求、API、领域模型或安全契约变化）
- verified_commit：`ee5b70f`

## 关联
- Change Request：无
- 上游任务：`TASK-KB-JIANLI-FOUNDATION-005`
- 测试任务：TC-AIQA-RAG-EVAL
