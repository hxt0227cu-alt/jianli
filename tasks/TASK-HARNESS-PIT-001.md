# TASK-HARNESS-PIT-001 提交坑记录器 record_pit.py

> 将 harness「留痕」循环的坑记录器 `scripts/record_pit.py`（101 行）正式入库。该工具是 `TASK-HARNESS-001`（已关闭，commit=1d821f2）所定义的「机器记录 → AI 评审 → 人决策 → Skill 抽取」留痕闭环的工具补齐，此前因 HARNESS-001 已关闭而遗留未提交。

## 任务类型
- chore  # harness 工具补齐（非业务功能）

## 关联任务
- `TASK-HARNESS-001`：harness 验收门禁 + 钩子 + 坑记录体系（已关闭）。本任务提交其留痕闭环中的 `record_pit.py` 工具本体，不改动 HARNESS-001 已冻结的 verify.sh 主流程。

## 目标
将 `scripts/record_pit.py` 入库。该脚本以结构化、机器可读 + 人读方式记录踩坑（pitfalls），追加至：
- `docs/devlog/pitfalls/pitfalls.jsonl`（每行一个 JSON 对象，机器友好）
- `docs/devlog/pitfalls/pitfalls.md`（人读，最新追加在末尾）

仅 `--symptom` 必填，其余字段默认「（待分析）」，供失败自动记录后由 AI 评审阶段补全。

## 非目标（明确排除）
- 不改动 verify.sh 主流程、钩子、门禁逻辑
- 不改动其他 harness 组件
- 不新增运行时依赖（仅标准库 argparse / json / datetime / pathlib）

## 允许修改路径
- `scripts/record_pit.py`
- 本任务单 `tasks/TASK-HARNESS-PIT-001.md`

## change_budget
- max_files: 2
- 生产代码行数：≈101（工具脚本，非业务域）

## 验收标准
- `scripts/record_pit.py` 已入库，`python scripts/record_pit.py --help` 可正常打印用法
- 不引入未跟踪的真实交付文件

## 状态
- status: in_progress
- 创建 commit: （待提交）
- verified_commit: （待回填）
