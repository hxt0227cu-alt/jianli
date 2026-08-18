# TASK-AIQA-PERSONA-STYLE-019：L1 人格层 persona 风格更新（用户风格样本）

## 背景与目标

`apps/api/app/aiqa/persona.py` 的 `_SYSTEM_PROMPT` 目前风格只写"简洁、具体、真诚"（设计方推断）。用户 2026-08-18 提供真实沟通风格样本（权威），需转化为 persona 提示词 + few-shot 示例：

1. **通用沟通范式**：结构先行结论前置（结论→上下文→动作/方案→结果/收获→反思）；客观陈述少情绪化形容词（不用"超级难/压力巨大/特别成功/很离谱"，用"存在明显瓶颈/资源约束较强/指标提升 XX%/存在协作流程缺陷"）；边界清晰知之为知之（"这块我目前接触不多，但我理解核心逻辑是…后续我计划通过 XX 方式补齐"）；节奏可控分段表达（90~180 秒口述节奏）。
2. **技术岗偏好**（AI 全栈/Agent 方向）：区分「做了什么」和「学到什么」；主动讲踩坑、取舍、权衡；绑定指标、约束条件、技术选型理由。
3. **few-shot 示例**：8-12 组问答对，用 jianli/sleep/litchi/竞赛/方法论真实素材构造，体现"结论前置 + 客观陈述 + 踩坑取舍 + 指标绑定"；量化数字全部来自 content.py chunks / CORPUS / fact-bank，零新编。
4. 新增风格断言测试（`tests/aiqa/test_persona_style.py`）：persona 指令含风格关键词、few-shot 数量 8-12、情绪词负例（超级难/压力巨大/特别成功/很离谱等）、示例数字可溯源（抽查子串存在于 CORPUS/content.py）。
5. 既有约束不变：第一人称、绝不编造、越界拒答、不执行工具调用、基于【已知资料】与【硬性事实卡】、不沿用上一轮推断。

## 非目标

- 不动 service.py 检索/护栏/域过滤；不动 fact-bank（38/38 不扩题）；persona 只改风格强化，事实约束全部保留。
- 在线回答风格断言不做硬断言（LLM 输出不稳定，避免 flaky）；风格验证以静态断言 + 用户 WSL measure 38/38 回归为准。

## 允许路径（max_files = 4）

- `apps/api/app/aiqa/persona.py`（_SYSTEM_PROMPT 风格强化 + STYLE_FEW_SHOT + 注入）
- `apps/api/tests/aiqa/test_persona_style.py`（新建风格断言测试）
- `tasks/TASK-AIQA-PERSONA-STYLE-019.md`
- （视验证结果：`PROJECT_STATE.md` 收口时更新）

## 验证计划（用户 WSL）

1. `python3 -m pytest tests/aiqa/test_persona_style.py -v` → 风格断言全过
2. `python3 -m pytest tests/aiqa/test_rag_eval.py -v` → 7/7（persona 改动不影响检索评测）
3. 重启 uvicorn → `python3 scripts/measure_fact_consistency.py` → 38/38 保持（风格强化后回答措辞变化但事实不变）

## 交付证据

- commit / PR：（提交后回填）
- 修改文件清单：apps/api/app/aiqa/persona.py、apps/api/tests/aiqa/test_persona_style.py、tasks/TASK-AIQA-PERSONA-STYLE-019.md
- 测试命令及结果：（用户 WSL 复验后回填）
- verified_commit：（收口后回填）

## 关闭门禁

- [x] persona 风格改写完成：_SYSTEM_PROMPT 强化（结论前置/客观陈述/知之为知之/分段表达/技术岗偏好做了什么vs学到什么/踩坑取舍/指标绑定）+ STYLE_FEW_SHOT 12 组（数字全部来自 CORPUS/content.py，零新编）+ build_system_prompt 注入
- [x] 风格断言测试通过（本地 5/5：风格指令 11 词 / few-shot 数量 12 / 情绪词负例 9 词 / 结论前置 / 数字可溯源 10 项）
- [ ] 用户 WSL：风格测试 + pytest 7/7 + measure 38/38
- [ ] 提交 + verified_commit 回填 + PROJECT_STATE 同步
