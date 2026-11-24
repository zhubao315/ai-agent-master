# 服务与依赖清单

> **证据状态**：已验证（运行时 `docker ps` / `systemctl` / API 实测，2026-11-24）｜代码推导（随包文档 `architecture/system`、`dependencies.md` 审计）｜待确认（部分内部端口实际监听范围、ONLYOFFICE 内部库表）｜不适用（K8s 产品负载：未发现）。
>
> 生产默认只读；发现新服务或新依赖时先更新本文件再行动。

## 1. 主引擎常驻服务（已验证）

| 服务 | 内部端口 | 对外端口 | 职责 |
|---|---|---|---|
| edge (Caddy 2.11.9) | 80 | 8060 / 8061 / 8062 / 8063（8059 仅本机） | 唯一 HTTPS 入口、反代、TLS 终止 |
| ai-agent (Server) | 3190 | —（经 8060） | 对话、调度、Skills、模型路由 |
| docx-rewriter | 3191 | — | ONLYOFFICE 双网改写侧车，与 Server 同镜像 |
| onlyoffice | 80 | 经 8061 | 文档读写、转换 |
| quse-gateway | 3456 | 经 8062 | 浏览器实例注册表 + 命令总线（WS 拨入，非反代） |

健康检查实测：`GET https://192.168.1.3:8060/api/health` → 200 `{"ok":true,"profile":"assistant-v1","model":"glm-5.3-flash"...}`；License active（到期 2026-11-28）。

## 2. Sandbox 引擎侧（已验证 / 代码推导）

- systemd：`docker-sandbox.service`、`containerd-sandbox.service`、`ai-agent-sandbox-proxy.service`。
- socket：`/run/docker-sandbox/api/docker.sock`（只读挂入 Server）。
- 网络：`ai-agent-dev-a-next-sandbox-net`（172.30.240.0/24），网桥脚本 `/usr/local/libexec/ai-agent-sandbox-network`。
- Workspace / Browser Runtime 按需创建；`ai-agent-image base apply` 装入平台基础 `20261109.standard.2`（20 项共享软件）。

## 3. systemd 单元（已验证）

`ai-agent-hugo.service`（active，文档站）、`gdmp-site-hugo.service`（active）、`ai-agent-dev-a-next-maintain.service`（inactive，path 触发）、`ai-agent-incident-containment-20261115.service`（active/exited，**事件加固，勿停用**）、`site-certs-renew.service`（证书续期）。

## 4. 对外 / 宿主端口（已验证）

- 宿主 Caddy：9090（ai-agent 文档站）、9191（gdmp 文档站）、38060–38062（AI-Agent 产品）。
- 产品容器：edge 80/2019/443 等，server 3190，docx-rewriter 3191，quse 3456，onlyoffice 80/443。
- 本地模型网关 `:808`（GPUStack，见 `model-management.md`）——属模型层，非产品五容器。

## 5. 依赖关系（运行时实测，dependencies.md）

| 依赖方 → 被依赖方 | 机制 / 地址 | 状态 |
|---|---|---|
| 产品 → 模型服务 | 默认 `glm-5.3-flash-local` → `http://192.168.1.3:18087/v1`；外部 DeepSeek 经 api.deepseek.com | 已验证（审计时）； Docs 记载 `:18087` 于 11-05 停止 → **待确认** |
| 产品 → Sandbox | 经 `ai-agent-sandbox-proxy` 访问独立 socket；Workspace 用 `ai-agent-dev-a-next-sandbox-net` | 已验证 |
| 产品 → Quse Gateway | `http://quse-gateway:3456`（Sandbox Profile env `QUICKAI_GATEWAY_URL`） | 已验证 |
| 产品 → GDMP | Sandbox Profile env `GDMP_BASE_URL=http://192.168.1.23:8090`（跨机，GDMP 技能独立） | 已验证 |
| 产品 → ONLYOFFICE | edge → docx-rewriter:3191 → ai-agent:3190；browserUrl `https://192.168.1.3:38061`；字体卷独立 | 已验证 |
| 文档站 | Caddy 9090 → Hugo 1313；证书 `site-certs-renew.service` | 已验证 |
| 未发现 | 独立向量库、产品侧 Redis/MQ、K8s 产品负载（kubectl 仅 default context） | 已验证（未发现） |

## 6. 安全边界提示

- Quse Gateway 全部 REST 路由与 WS 通道**无认证**，安全依赖网络边界（限内网来源 3456/8062）——代码推导。
- 工具管理接口 `CUSTOM_TOOL_MANAGEMENT_DISABLED`（事件加固禁用），安装/运维不得依赖该 admin 接口——已验证。
- ONLYOFFICE 默认 `JWT_ENABLED=false`（模板默认，未逐项复核 → 代码推导）。
