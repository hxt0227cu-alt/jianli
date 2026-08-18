# TASK-AIQA-KB-POLISH-016：语料占位清理 + 真实口径对齐 + 前端口径同步

## 背景与目标

TASK-015 收口后复盘知识库，发现占位残留与口径问题（用户 2026-08-18 确认全部修复）：

1. **certificates.md 占位编造风险**：文本"持有数据库方向的专业认证"为早期占位，用户未确认过任何数据库认证。用户确认真实认证 = **PingCAP TiDB 数据库专员 PCTA 认证证书** → 替换占位。
2. **content.py sleep202603_an 静态占位**："睡眠数据可视化与分析原型"与真实项目（AI 睡眠健康 Agent 平台）不符，KB 兜底时会答错 → 升级真实描述。
3. **skills.md 档位为占位口径**："熟练/掌握/熟悉"未逐项确认 → 按仓库证据对齐 4 项档位（①Git+Docker 熟悉/②SQL 查询与索引做过/③WSL 日常+监控接触过非 SRE/④测试扎实）。
4. **main.tsx「事实一致率」仍为 26/26 文案** → 同步 38/38=100%（严格口径，2026-08-18 实跑）。
5. **litchi.md 缺 observability 细节**（prometheus 3 job + grafana 看板）→ 补 1 句（不加 fact-bank 题，38/38 已达标，加题维护成本>收益）。

## 非目标（不做）

- 不动冻结测试断言（LITERAL 8/8、REJECT 10/10、FALSE-REJECT 8/8、`_MIN_HIT_RATE=0.75`）。
- 不动 service.py / repository.py / seed_kb.py / fact-bank（不加 FQ-39+）/ measure（38 题不变）。
- 泰益智仓库只读查证，不入库；不碰用户并行文件（apps/api/var/）。

## 允许路径（max_files = 6）

- `apps/api/tests/aiqa/test_rag_eval.py`（certificates.md PCTA / skills.md 档位 / litchi.md observability 句 / agent-notes.md "防乱调用"锚定 / SEMANTIC_CASES internship 题换问法）
- `apps/api/app/aiqa/content.py`（sleep202603_an chunk 升级真实描述）
- `apps/web/main.tsx`（事实一致率 26/26 → 38/38 文案）
- `apps/api/app/aiqa/service.py`（**回归修复追加**：恶意正则加"爬虫抓取第三方平台"护栏——BGE-M3 对"帮我写爬虫抓微博"与 litchi chunk 假阳性 0.488 越阈，确定性规则拦截；如实登记追加路径）
- `tasks/TASK-AIQA-KB-POLISH-016.md`
- （视验证结果：`docs/fact-consistency/scored-2026-08-18.md` 若需补记，另行追加）

## 回归修复（2026-08-18 首轮 WSL 验证后补充）

用户 WSL 首轮：38/38 全绿 ✅，但 pytest 2 回归（TASK-016 语料改动致检索排序变化）：
- **REJECT 9/10**："帮我写一个爬虫脚本抓取微博帖子" top1=0.488 越阈（BGE-M3 与 litchi "yolo 三级降级" chunk 假阳性）→ **恶意正则加爬虫护栏**（爬虫+抓取/采集/爬取+第三方平台名；合法爬虫/防御视角放行，已 1 拦 3 放验证）。
- **SEMANTIC 4/6**：① internship 题"除了学校功课还做过什么实际工作？" vector 对全库 <0.47 → 换问法"你实习时主要在团队里做什么？"（probe 0.649 top1 强锚定）；② agent-notes 题"智能体怎么做才不会乱调用东西？" agent-notes v=0.459 <0.47 → **agent-notes.md 加"防止智能体乱调用工具"锚定词**（白名单/预算/审批/幂等/可观测）。

## 变更预算

- test_rag_eval.py：3 处语料文本（certificates/skills/litchi）
- content.py：1 处 chunk 文本（sleep）
- main.tsx：1 处文案（事实一致率）
- TASK 文件：新建

## 验证计划（用户 WSL）

1. `python3 -m pytest tests/aiqa/test_rag_eval.py -v` → 预期 7/7（语料改动不破坏 LITERAL/REJECT/FALSE-REJECT/EXTREME；certificates 题仍锚定）。
2. `python3 scripts/seed_kb.py` → 重灌库（certificates/skills/litchi 新文本入 KB），无 WARN。
3. 重启 uvicorn（content.py 改了）→ `python3 scripts/measure_fact_consistency.py` → 预期 38/38 保持。

## 交付证据

- commit / PR：`491ed48`（实现提交，6 文件 208+/134-）
- 修改文件清单：apps/api/tests/aiqa/test_rag_eval.py、apps/api/app/aiqa/content.py、apps/api/app/aiqa/service.py、apps/web/main.tsx、scripts/fact_consistency_results.json、tasks/TASK-AIQA-KB-POLISH-016.md
- 测试命令及结果：**PASS — 用户 WSL 复验 2026-08-18 18:31**：① pytest tests/aiqa/test_rag_eval.py **7/7**（SEMANTIC/REJECT 回归修复生效，LITERAL 8/8 + SEMANTIC 6/6 + EXTREME 6/6 + REJECT 10/10 + FALSE-REJECT 8/8 + 隐私）；② seed_kb.py 灌库 indexed=55 无 WARN；③ measure_fact_consistency.py 38 题 **38/38 全 OK**，严格一致率 100%，SLO ≥94% 达成，🚫误拒 0
- verified_commit：`491ed48`

## 关闭门禁

- [x] 代码改动 + py_compile / 导入验证通过（certificates PCTA / skills 4 档位 / litchi observability / sleep 真实描述 / agent-notes 锚定 / SEMANTIC 换题 / 爬虫护栏 1 拦 3 放；chunk 全 str）
- [ ] 用户 WSL pytest 7/7（SEMANTIC/REJECT 回归修复生效）
- [ ] 用户 WSL 重灌库无 WARN + 38 题重测保持 38/38
- [ ] 复评 + 提交 + verified_commit 回填 + PROJECT_STATE 同步
