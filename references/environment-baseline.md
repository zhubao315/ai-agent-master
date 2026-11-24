# 环境基线

> **证据状态**：已验证（2026-11-24 实读 `nvidia-smi` / `free` / `df` / `docker ps` / `systemctl`，见 `audit/resource-baseline.md` 与 `audit/services.md`）｜代码推导（随包文档版本基线）｜待确认（内核小版本、驱动精确版本、License 后续状态）｜不适用（无）。
>
> 采集只读；禁止在基线上直接做变更。每次任务先复核，数据会漂移。

## 1. 主机资源（实测）

| 项 | 实测值 |
|---|---|
| 内核 | Linux 7.0.0-43-generic |
| CPU | 128 核 |
| 内存 | 总 499 GiB，已用 408 GiB，可用 91 GiB |
| GPU | 7× NVIDIA GeForce RTX 4090，每卡约 49140 MiB |
| 磁盘 `/` | 1.8T，已用 532G（32%），可用 1.2T |
| 磁盘 `/data` | 1.8T，已用 1.3T（**80%**），可用 343G |
| 容器运行时 | Docker + Docker Compose v5.5.1；独立 Sandbox 引擎 |

> `/data` 已用 80%，安装/备份/解包前必须复查余量（风险 R5）。

## 2. GPU 瞬时状态（实测）

每卡显存占用（MiB）：`52 / 27192 / 23926 / 47923 / 25140 / 46304 / 47891`；GPU 利用率 0%（采样瞬时）。部分卡 >47GB，高占用 → **不要在此机启动新推理负载做测试**（风险 R7）。

## 3. 产品运行时版本（已验证）

- 版本：**0.9.3**
- 主镜像：`ai-agent:20261121.1795273330-amd64`，源码 `3744b6aa…`
- 五容器：server/docx-rewriter 同主镜像；edge `caddy:2.11.9-alpine`；onlyoffice `onlyoffice-agent:9.4.0-session.16-r5-fonts3-amd64`；quse `quse-gateway:1.0.24-20260911.1789148529-amd64`
- 数据库迁移：`021_async_invocation_actor`（代码推导，随包文档）
- 平台基础：`20261109.standard.2`（20 项共享软件，代码推导）
- License：active，到期 2026-11-28（实测，需按当前日期复核）

## 4. 关键路径（已验证）

| 路径 | 用途 |
|---|---|
| `/data/ai-agent-next/runtime/db/ai-agent.sqlite` | AI-Agent 主库 |
| `/data/ai-agent-next/runtime/public-skills/records/*.json` | 23 条公共技能记录 |
| `/data/ai-agent-next/runtime/skillshub/users/me/myskills/<skillName>` | 私有技能安装位置（实测返回） |
| `/run/docker-sandbox/api/docker.sock` | Sandbox 引擎 socket |
| `/run/ai-agent/engine-id` | License 身份文件（代码推导） |
| `/usr/local/libexec/ai-agent-sandbox-network` | 沙箱网桥脚本 |

## 5. 状态单元（已验证）

- active/running：五产品容器、`ai-agent-hugo.service`、`gdmp-site-hugo.service`、`ai-agent-incident-containment-20261115.service`、双 Sandbox 引擎与代理。
- inactive：`ai-agent-dev-a-next-maintain.service`（path 单元触发）。

## 6. 证据边界

- 无产品源码仓库；版本/路径结论来自运行实例与随包文档，不是源码走读。
- 随包文档写 Caddy 为 `2.11.4-alpine`，运行时为 `2.11.9-alpine`，差异**待确认**（以运行时为准记录）。
- 默认模型 `glm-5.3-flash-local` / `http://192.168.1.3:18087/v1` 为审计时实测，但随包文档记该上游 11-05 停止 —— **待确认**，变更前须用 `/api/health` 和模型管理页复核。
