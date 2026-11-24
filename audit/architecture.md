# 架构审计

## 已验证架构（来自运行实例与随包文档）

- **部署形态**：同宿主双 Docker 引擎。主引擎（`default`）跑 edge / ai-agent / onlyoffice / quse-gateway；Sandbox 引擎（`docker-sandbox.service` + `containerd-sandbox.service`，socket `/run/docker-sandbox/api/docker.sock`）跑 Workspace / Browser 运行时；边界代理 `ai-agent-sandbox-proxy.service` 控制 sandbox socket 访问。
- **产品边缘**：容器内 Caddy `:8060`（HTTP）/ `:8443` 等；宿主 Caddy `:38060–38062` 反代到 edge。
- **文档站**：Hugo + oink v1.5.1，systemd `ai-agent-hugo.service` 监听 1313，宿主 Caddy 9090 反代。
- **模型层**：本地模型网关（实测默认 `glm-5.3-flash-local`，base `http://192.168.1.3:18087/v1`），另有 DeepSeek 等外部模型；GPU 为 7× RTX 4090（48GB）。推理框架具体类型（vLLM/SGLang/其他）**待确认**（无源码、未读推理容器启动参数）。
- **工具/集成**：Quse Gateway（命令总线，`1.0.24-20260911.1789148529`）、原生 MCP、扩展工具 ZIP（browser/webSearch/generateImage 等 8 个）、Skillshub（23 个公共技能）。
- **数据层**：AI Agent 主库 SQLite（`/data/ai-agent-next/runtime/db/ai-agent.sqlite`）、工具扩展库 `tool-extensions.sqlite`、ONLYOFFICE 自带 PostgreSQL/Redis/RabbitMQ（容器卷）。
- **知识/RAG**：**未发现独立向量数据库或 RAG 服务**；平台提供文件/知识类工具，但向量索引、Embedding、Rerank 服务未在运行清单中发现 → **不适用/待确认**（不创建虚构配置）。

## 代码级架构

**受阻**：无产品后端源码仓库（见 platform-audit.md）。以上结论来自运行实例、API、随包 OpenAPI 与文档，标注为「已验证（运行时）」或「代码推导」，非源码走读。
