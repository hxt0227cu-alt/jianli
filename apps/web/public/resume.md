# [姓名已脱敏]

> 本文件是网站公开 PDF 简历的文字镜像。简历采用压缩表达；涉及实现状态、评测口径和证据边界的技术追问，以站内 canonical RAG 语料为准。

年龄：22 · 电话：[手机号已脱敏]（微信同号）· 邮箱：[邮箱已脱敏] · 政治面貌：中共党员

毕业院校：[学校已脱敏] · 专业：计算机科学与技术（专业排名 3/153）

CSDN 博客：https://blog.csdn.net/m0_73429744?spm=1000.2115.3001.5343

## 个人简介

聚焦业务落地的 AI-Agent 全栈工程师。熟悉 Agent Runtime 编排、Tool Calling、RAG 工程化、Human-in-the-Loop 审批、LLM 评测与安全治理、Harness 工程实践；拥有医疗 IoT、农业 B2B2C、企业预约多场景实战，具备团队协作与独立全链路开发经验。

## 实习经历

### 泰益智医疗科技（广州）有限公司｜AI 全栈开发工程师（2025.12-2026.06）

CTO 带教，承担全职工程师工作，负责 AI Agent 平台云端后端核心模块，对接 IoT 硬件团队，支撑高风险睡眠健康业务。

- 基于 LangGraph、Temporal 实现 Agent 状态图编排，配置任务预算熔断、持久化重试恢复；改造为异步准入模型，100 并发压测 HTTP P95 由 1347ms 降至 229ms，全部请求执行成功。
- 搭建 RAG 与上下文工程，实现 pgvector 向量检索、租户知识域隔离；落地工具白名单、人工审批、注入防护，84 条工程回归用例全量通过，审批绕过率 0。
- 参与 MQTT-Kafka-ClickHouse 遥测链路建设，完成故障注入验证，实现事件 0 丢失 0 重复；推进 Harness 工程治理，落地 CI 门禁、供应链安全扫描，GitOps 完成端到端容器交付。

## 项目经历

### Jianli｜AI Agent 问答与面试预约系统（独立开发，2026.08）

业务场景：企业预约业务，解决并发抢占、权限管控。

技术栈：Python、PostgreSQL、pgvector、Redis、React、SSE。

- 自研 Agent 执行循环，实现工具编排、RBAC 权限、有界上下文管理，依托行锁与幂等机制解决预约超卖，SSE 流式输出工具执行轨迹。
- 搭建混合检索 RAG 链路和 BGE-M3 向量知识库；构建多套评测集，事实一致性 100%，越界拒答率提升至 100%；完善安全防护与自动化测试，完成容器化部署与消息通知链路。

### Litchi Copilot｜荔枝农技 AI Agent 协同平台（优秀毕设｜独立开发，2025.06-2026.05）

业务场景：B2B2C 农技服务闭环。

技术栈：Java 17、Spring Boot 3.2、Vue 3、Milvus、Neo4j、Docker、Prometheus。

- 自研 Agent Runtime，实现状态机生命周期、Checkpoint 持久化、最多 4 步工具规划、RBAC 工具权限管控，高危操作强制人工审批。
- 构建 RAG + 知识图谱链路，支持多格式文档解析、混合召回；封装 YOLO 图像病害诊断服务；自建 60 条评测数据集，完成自动化测试与稳定性回归；独立完成核心业务接口、21 个业务页面开发。

### 大数据红火蚁精准防控机器人｜国家级大创（第一负责人・优秀结题，2024.05-2025.04）

- 牵头国家级创新创业项目，统筹团队完成硬件集成、野外业务测试、业务数据集构建和模型验证，项目获评优秀结题。

## 荣誉与证书

- 证书：TiDB-PCTA、CET-4；备考软考高级（系统架构师，10 月考试）。
- 荣誉：国家励志奖学金、国家级大创立项（第一负责人）、挑战杯 A 类路演资格、校级奖学金、优秀毕业生。

## 专业技能

- AI-Agent & LLM：Agent Runtime、状态编排、Tool Calling、RAG 全链路、混合检索、Prompt/Context Engineering、Human-in-the-Loop、LLM 评测、Agent 安全护栏、Model Gateway。
- 后端与数据：Java（Spring Boot）、Python、TypeScript（NestJS）、SQL；PostgreSQL、MySQL、Redis；Milvus、Neo4j、pgvector；Kafka、ClickHouse、RBAC、事务幂等。
- 前端：Vue 3、React、TypeScript。
- 云原生：Docker、Helm、GitOps（ArgoCD）、GitHub Actions、Prometheus/Grafana；了解 K8s、Flink、dbt。
