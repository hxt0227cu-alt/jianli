# TASK-CR-OBSERVABILITY-001 OpenTelemetry + Prometheus/Grafana 变更请求

> **状态：Approved / Closed（2026-08-27，用户已显式全权批准）**

## 任务类型
- architecture
- security
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.2 / security 0.1 / test-plan 0.8
- 基线 commit：`fd6c3c8`

## 精确规范引用
- `docs/design/architecture.md §3 / §9.3`
- `docs/design/security.md §11–§12`
- `docs/test/test-plan.md §2.8–§2.9`
- `docs/adr/ADR-OBS-001.md`

## 需求来源
- 用户要求作品具备 Agent 开发岗竞争力，并批准 OpenTelemetry + Prometheus/Grafana 可观测闭环。

## 目标
批准 API/AIQA 的低基数指标、OTLP Trace、内部 Prometheus 抓取面与 Grafana 看板部署。

## 非目标
- 不新增 DB/API 业务契约、日志平台、云托管监控、通知告警或前端业务页面。
- 不采集 Prompt、问题原文、回答、知识片段、工具参数/结果或预约 PII。

## 允许修改路径
- `tasks/TASK-CR-OBSERVABILITY-001.md`
- `docs/adr/ADR-OBS-001.md`
- `docs/design/architecture.md`
- `docs/design/security.md`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- 应用/测试/部署代码、依赖清单、OpenAPI、领域模型。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：新增仅容器私网可抓取的内部 `/internal/metrics`，不进入公开 OpenAPI，Nginx 必须拒绝公网访问。
- 依赖：批准 `prometheus-client==0.26.0`、`opentelemetry-sdk==1.44.0`、`opentelemetry-exporter-otlp-proto-http==1.44.0` 及其锁定传递依赖。
- 基础设施：批准 Prometheus、Grafana、OpenTelemetry Collector 三个 Docker Compose 服务及版本化配置/看板。

## 批准决策
- 指标标签只使用固定枚举或规范化 route；禁止 user_id、conversation_id、trace_id、问题、文档名、异常文本等高基数/敏感标签。
- OTLP 仅在配置 endpoint 时启用；未配置时使用 no-op，不影响主请求。
- Trace 采集 HTTP、AIQA 编排与工具阶段；只允许阶段、结果、白名单工具名、模型名、token 数和耗时等客观属性。
- Prometheus 直连 API 容器私网抓取；Nginx 对 `/internal/metrics` 返回 404；Grafana 只读展示请求量、延迟、grounded/offtopic/error、token 与工具调用。
- 采集/导出失败不得使问答失败；不得在指标或 span 中记录异常正文。

## 功能验收
- TC-OPS-010 覆盖 metrics 内容、低基数标签、OTLP 开关、Nginx 隔离和 Compose 配置渲染。

## 安全与隐私验收
- 指标与 Trace 不含 TC-SEC-004 禁止字段；公网无法访问内部 metrics。

## 性能验收
- 可观测关闭时近似 no-op；开启时不新增业务 DB/LLM 调用，指标记录为进程内操作。

## 变更预算
- max_files：7
- expected_prod_lines：180
- expected_test_lines：0

## 必须运行的测试命令
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`。

## 强制停止条件
- 若需 DB/公开 OpenAPI/认证策略变化、额外依赖或超 7 文件，停止拆分。

## 交付证据
- commit / PR：`b1dbad2`
- 修改文件清单：本任务允许的 7 个路径
- 测试命令及结果：`git diff --check` 通过
- lint / typecheck：文档任务不适用
- DB 迁移验证：无
- 验收证据：ADR-OBS-001 accepted；architecture 0.3 / security 0.2 / test-plan 0.9 / baseline approved 同步
- 变更预算实际值：7 文件 / 148 新增 / 11 删除，未超预算
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：`b1dbad2`

## 关联
- 下游：`TASK-OBSERVABILITY-001`
