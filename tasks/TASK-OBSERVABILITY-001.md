# TASK-OBSERVABILITY-001 OpenTelemetry + Prometheus/Grafana 实现

> **状态：In Progress（2026-08-27）**

## 任务类型
- implementation
- test
- infrastructure

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.3 / security 0.2 / test-plan 0.9
- 基线 commit：`b1dbad2`

## 精确规范引用
- `docs/adr/ADR-OBS-001.md`
- `docs/design/architecture.md §3 / §9.3`
- `docs/design/security.md §11–§12`
- `docs/test/test-plan.md TC-OPS-010`

## 需求来源
- 已批准 `TASK-CR-OBSERVABILITY-001`。

## 目标
实现可关闭的 API/AIQA 指标与 Trace 埋点、内部 metrics、Collector/Prometheus/Grafana Compose 和预置看板。

## 非目标
- 不新增业务 DB/API、公开 Grafana、日志平台、外部告警或前端业务页面。

## 允许修改路径
- `tasks/TASK-OBSERVABILITY-001.md`
- `apps/api/pyproject.toml`
- `apps/api/requirements.lock`
- `apps/api/Dockerfile`
- `apps/api/app/config.py`
- `apps/api/app/factory.py`
- `apps/api/app/observability.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/tests/test_observability.py`
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `deploy/nginx.conf`
- `deploy/nginx-https.conf.template`
- `deploy/observability/prometheus.yml`
- `deploy/observability/otel-collector.yml`
- `deploy/observability/grafana/provisioning/datasources/prometheus.yml`
- `deploy/observability/grafana/provisioning/dashboards/provider.yml`
- `deploy/observability/grafana/dashboards/agent-overview.json`
- `PROJECT_STATE.md`

## 禁止修改路径
- migrations、OpenAPI、领域模型、工具权限、Prompt、既有冻结测试。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：内部 `/internal/metrics`，不进入公开 OpenAPI，Nginx 404。
- 依赖：`prometheus-client==0.26.0`、`opentelemetry-sdk==1.44.0`、`opentelemetry-exporter-otlp-proto-http==1.44.0` 及锁定传递依赖。
- 基础设施：Prometheus/Grafana/OTel Collector Compose 服务与配置。

## 规范影响评估
- behavior_change：true（仅内部运维面）
- affected_specs：architecture/security/test-plan 已由上游 CR 更新；SRS/domain/openapi none。
- reason：实现已批准的内部可观测面，不改变公开业务行为。

## 功能验收
- 可观测关闭时 metrics 404；开启后低基数 HTTP/AIQA/token/tool 指标可抓取。
- OTLP endpoint 可选；未配置或 Collector 不可用不改变业务返回。
- Compose 配置含 Collector、Prometheus、Grafana；Grafana 预置数据源与 Agent 看板。

## 安全与隐私验收
- 指标/Span 无问题、回答、Prompt、知识原文、PII、密钥、高基数 ID 或异常正文。
- 两份 Nginx 配置均拒绝 `/internal/metrics`；Grafana/Prometheus 仅绑定 localhost 或容器私网。

## 性能验收
- 指标记录不新增 DB/网络调用；OTLP 使用 BatchSpanProcessor；主请求不等待导出。

## 变更预算
- max_files：19
- expected_prod_lines：650
- expected_test_lines：140

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. pytest tests/test_observability.py tests/aiqa/test_agent_lab.py tests/aiqa/test_aiqa.py -q`
- `cd apps/api && ruff check app tests/test_observability.py && mypy app`
- `docker compose -f docker-compose.dev.yml config`
- `docker compose -f docker-compose.prod.yml config`（使用测试 env）
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；删除 Compose 服务即可，无数据迁移。

## 强制停止条件
- 需要 DB/公开 OpenAPI/额外依赖、暴露公网 metrics/Grafana 或超 19 文件时停止。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：待回填

## 关联
- Change Request：`TASK-CR-OBSERVABILITY-001`
- 验收：TC-OPS-010
