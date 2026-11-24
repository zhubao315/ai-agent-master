# 故障排查索引

> **证据状态**：已验证（现场服务清单、风险登记册、健康接口实测）｜代码推导（随包文档 `ops/troubleshooting`、模型网关排障表、`architecture/system` 错误码）｜待确认（现场具体告警/日志、默认模型上游存活）｜不适用（RAG/向量库类故障——现网无此服务）。
>
> 生产只读；先汇总后样本。重启/切换/迁移需审批，先看 `runbooks/incident-response.md`。

## 1. 定位顺序（已验证的环境事实）

1. 目标搞错？9090 是文档站，产品是 38060/8060（风险 R1）。
2. 五容器状态：`docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'`。
3. 健康检查：`curl -kfsS https://<ip>:8060/api/health`（实测 200）。
4. 双引擎：`systemctl is-active docker-sandbox containerd-sandbox ai-agent-sandbox-proxy docker`。
5. 资源：`nvidia-smi`、`df -h /data /`、`free -h`（`/data` 已 80%）。
6. 事件加固：`systemctl is-active ai-agent-incident-containment-20261115.service`（勿停用）。

## 2. 容器 / 端口类（代码推导，随包文档）

- 容器起不来：`docker logs ai-agent-<实例>-server`；`ss -tlnp | grep -E ':(8060|8061|8062|8063)'`；`df -h /data/ai-agent`。
- 端口冲突：改 `deployment.env` 中 `AI_AGENT_PUBLIC_PORT` / `ONLYOFFICE_PUBLIC_PORT` / `QUSE_PUBLIC_PORT` / `BROWSER_PREVIEW_PUBLIC_PORT`，改后重新 apply；五端口必须互不相同。
- 权限：`chmod -R 755 /data/ai-agent/`、`chown -R root:root /data/ai-agent/`（变更需审批）。
- SSL/ACME：查域名解析与 80/443 出网；自定义证书放 `/data/ai-agent/generated/caddy/`；证书续期 `site-certs-renew.service`。
- 安装报 `target Image is unavailable after archive load`：经典 overlay2 与 containerd 的 IMAGE ID 不同，属镜像存储后端问题（见 FAQ 部署篇）。

## 3. 模型 / 推理类（代码推导，随包文档）

| 现象 | 排查 |
|---|---|
| 对话全失败 | 默认 `glm-5.3-flash-local` 指 `:18087` 可能已停（**待确认**）；改指 `:808`/`:18086`，见 `model-management.md` |
| 网关 401 | Key 错误或路由是 authed；public 路由不会 401 |
| 有 key 仍 403 | authed 路由上 key 的 `allowed_model_names` 不含该模型 |
| 别的模型的 key 也能用 | 该路由 public，`allowed_model_names` 不生效 |
| 路由 504 / 超时 | 上游地址与实际 bind 不匹配；或并发槽位满（Strata 槽位=2） |
| 路由 5xx 但模型名存在 | `ready_targets=0`（托管副本 0）；注意 ready_targets 不随上游存活变化 |
| target 被覆盖 | `add-targets` 全量替换，须一次传全部 |
| 改访问策略没生效 | `PUT` 不接受 `access_policy`，走 `POST .../access` |
| 外部 provider 不通 | `0.0.0.0` 映射用 `172.17.0.1`，只 bind 回环/内网用该内网地址 |
| 经网关空 body / 400 | 自建 shim 未处理 `Transfer-Encoding: chunked` |
| Laya `/v1/analyze` 404 | 网关不透传，直连 `:8900` |

## 4. 事件加固相关（已验证）

- 工具管理页扩展工具排序 / MCP 编辑入口不可用，API 返回 `403 CUSTOM_TOOL_MANAGEMENT_DISABLED`：这是实例级安全策略（2026-11-15 事件），不是账号权限或 License 问题；Workspace 内已启用工具调用不受影响。**不要反复重试保存**，需恢复时按事件加固流程走审批。
- containment 单元 active/exited 属预期，不要擅自停用。

## 5. 迁移/升级后常见坑（代码推导）

- 新内核启动即 `image is not supported`：旧 `workspace-profiles.json` 含 `image` 等旧字段，需清理。
- 进 Studio 报「数据结构不符合要求」：工作区记录未补新字段（如 `workspace.json` 缺 `name`）。
- `config-port` 报 edge 未就绪：docx-rewriter 侧车未运行导致健康检查失败，先起侧车再切端口。
- 迁移后功能找不到数据：`runtime/**` 旧绝对路径未改写。

## 6. 升级受阻 / 能力缺失

- 无产品源码仓库 → 源码级 Diff、CI 集成无法完成（风险 R2），如实报告「受阻」。
- 未发现向量/RAG 服务 → RAG 类故障不适用（见 `rag-operations.md`）。
