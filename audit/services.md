# 真实服务清单（2026-11-24 实测）

## 容器（主引擎）
| 容器 | 镜像 | 状态 |
|---|---|---|
| ai-agent-dev-a-next-server | ai-agent:20261121.1795273330-amd64 | Up 2 days (healthy) |
| ai-agent-dev-a-next-docx-rewriter | ai-agent:20261121.1795273330-amd64 | Up 2 days (healthy) |
| ai-agent-dev-a-next-edge | caddy:2.11.9-alpine | Up 4 days |
| ai-agent-dev-a-next-onlyoffice | onlyoffice-agent:9.4.0-session.16-r5-fonts3-amd64 | Up 2 days (healthy) |
| ai-agent-dev-a-next-quse-gateway | quse-gateway:1.0.24-20260911.1789148529-amd64 | Up 4 days (healthy) |

## systemd 单元（相关）
`docker-sandbox.service`、`containerd-sandbox.service`、`ai-agent-sandbox-proxy.service`、`ai-agent-hugo.service`（active）、`gdmp-site-hugo.service`（active）、`ai-agent-dev-a-next-maintain.service`（inactive，path 单元触发）、`ai-agent-incident-containment-20261115.service`（active/exited）。

## 网络/端口
- 宿主 Caddy：9090（ai-agent 文档站）、9191（gdmp 文档站）、38060–38062（AI-Agent 产品）。
- 产品容器：edge 80/2019/443 等，server 3190，docx-rewriter 3191，quse 3456，onlyoffice 80/443。
- 沙箱网络：`ai-agent-dev-a-next-sandbox-net`（172.30.240.0/24），网桥脚本 `/usr/local/libexec/ai-agent-sandbox-network`。

## 健康检查实测
`GET https://192.168.1.3:8060/api/health` → 200，`{"ok":true,"profile":"assistant-v1","model":"glm-5.3-flash"...}`；License active（到期 2026-11-28）。
