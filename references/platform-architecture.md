# 平台架构（AI-Agent Product 0.9.3）

> **证据状态**：已验证（运行实例、Caddyfile、systemd 实测，2026-11-24）｜代码推导（站点随包文档 `architecture/system`、`architecture/why-dual-engine`）｜待确认（推理框架具体类型、源码级结构）｜不适用（产品源码走读）。
>
> 生产默认只读。本文件只描述已观测形态，不对未取得证据的组件下定论。

## 1. 目标识别（最容易踩的坑）

| 访问对象 | 实际是什么 | 证据 |
|---|---|---|
| `https://219.142.87.233:9090/` | **Hugo 文档站**（oink v1.5.1），宿主 Caddy `:9090` → `127.0.0.1:1313`，systemd `ai-agent-hugo.service` | 已验证 |
| `https://219.142.87.233:38060/` | AI-Agent 产品 UI 公网入口 → 容器内 edge `:8060` | 已验证 |
| `https://192.168.1.3:8060/` | AI-Agent 产品内网入口；`GET /api/health` 实测 200 | 已验证 |

> **结论**：9090 不是产品后台，技能安装/加载必须以 38060/8060 为目标。把 9090 当安装目标是最常见的误判（风险 R1）。

## 2. 部署形态：同宿主双 Docker 引擎

- **主引擎**（`default`）：跑 edge / ai-agent / onlyoffice / quse-gateway / docx-rewriter；`docker compose` 静态编排。
- **Sandbox 引擎**：`docker-sandbox.service` + `containerd-sandbox.service`，socket `/run/docker-sandbox/api/docker.sock`；跑 Workspace Sandbox 与 Browser Runtime，由 Server 经只读挂入的 socket 按 `idle-ttl` 动态 create/exec/回收（非静态编排）。
- **边界代理**：`ai-agent-sandbox-proxy.service` 控制 Sandbox socket 访问（已验证）。
- v0.7.3 起主引擎 socket 不再挂入 Server，改只读身份文件 `/run/ai-agent/engine-id`（License 用）——代码推导（随包文档）。

## 3. 五容器（主引擎，2026-11-24 实测）

| 容器 | 镜像 | 状态 |
|---|---|---|
| `ai-agent-dev-a-next-server` | `ai-agent:20261121.1795273330-amd64` | Up (healthy) |
| `ai-agent-dev-a-next-docx-rewriter` | `ai-agent:20261121.1795273330-amd64` | Up (healthy) |
| `ai-agent-dev-a-next-edge` | `caddy:2.11.9-alpine`（运行时实测；随包文档写 `2.11.4-alpine`，**待确认**） | Up |
| `ai-agent-dev-a-next-onlyoffice` | `onlyoffice-agent:9.4.0-session.16-r5-fonts3-amd64` | Up (healthy) |
| `ai-agent-dev-a-next-quse-gateway` | `quse-gateway:1.0.24-20260911.1789148529-amd64` | Up (healthy) |

当前构建：**0.9.3 / 20261121.1795273330，源码 `3744b6aa…`**，运行时已验证。

## 4. 分层职责（代码推导）

- **接入层**：Caddy Edge 统一 HTTPS 入口（8060 主站 / 8061 ONLYOFFICE / 8062 Quse / 8063 Preview，8059 HTTP 仅本机）。
- **应用层**：AI-Agent Server（内部 `:3190`）承载对话、调度、Skills 引擎；`POST /api/invoke` 为调用入口。
- **服务层**：ONLYOFFICE 文档、Quse Gateway 命令总线（内部 `:3456`，WS 拨入）、Sandbox 内的 Browser/Workspace。
- **调用链**：用户 → Caddy → Server →（OpenAI-compatible）模型 API；Server 经 Sandbox 引擎 docker exec 操作 Workspace/Browser（非 HTTP）。

## 5. 数据层

- 主库 SQLite：`/data/ai-agent-next/runtime/db/ai-agent.sqlite`（已验证）。
- 工具扩展库：`tool-extensions.sqlite`（随运行时存在）。
- ONLYOFFICE 自带 PostgreSQL / Redis / RabbitMQ（容器卷，已验证存在；具体库表未审计 → 待确认）。
- 会话真相以文件系统分层存储（索引 / 权威轮次 / 恢复态 / 压缩态）——代码推导。

## 6. 知识 / RAG

**未发现独立向量数据库或 RAG 服务**：向量索引、Embedding、Rerank 服务均不在运行清单中 → **不适用/待确认**。平台有文件/知识类工具，但不得据此虚构向量库配置。

## 7. 审计边界

无产品后端源码仓库（`/oc/ai-agent-site` 仅 Hugo 文档站），代码级架构走读**受阻**。以上结论来自运行实例、API、随包 OpenAPI 与文档，非源码走读。
