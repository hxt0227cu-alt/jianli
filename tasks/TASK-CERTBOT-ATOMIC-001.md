# TASK-CERTBOT-ATOMIC-001 HTTPS 配置原子切换

> 状态：In Progress（2026-08-31）。上线审查发现证书脚本未继承生产 Compose/env 路径，且在 `nginx -t` 前覆盖运行配置；用户已授权修复。

## 任务类型
- implementation（运维可靠性修复）

## 基线与引用
- baseline：PRD 2.3.6 / architecture 0.6 / security 0.5 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
- `docs/design/security.md` §6、§12；`docs/test/test-plan.md` TC-OPS-003

## 目标
- 证书命令与部署使用同一 `COMPOSE_FILE` / `JIANLI_ENV_FILE`。
- HTTPS 配置切换后先 `nginx -t`；校验、reload 或信号中断失败时自动恢复旧配置。

## 非目标
- 不签发本机证书、不修改 TLS 策略、域名需求、API、DB 或依赖。

## 允许修改路径
- `deploy/certbot-init.sh`
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-CERTBOT-ATOMIC-001.md`

## 已批准的 DB / API / 依赖变更
- DB：无。API：无。依赖：无；复用 Compose/Certbot/Nginx。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：修复 approved HTTPS 运维步骤的失败回滚。

## 变更预算
- max_files：3
- expected_prod_lines：≤55
- expected_doc_lines：≤8

## 验收
- 自定义 env/compose 路径贯穿 certbot、nginx test 与 reload。
- `nginx -t` 或 reload 失败、INT/TERM/HUP 时保留旧的有效配置；成功后无 `.next`/`.previous` 残留。
- `bash -n deploy/certbot-init.sh` 通过。

## 回滚
- 回退脚本、文档与任务单；证书卷不删除。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：真实签发需域名 DNS 与公网 80/443
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
