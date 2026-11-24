# 部署与安装导引

> **证据状态**：已验证（现场五容器、双引擎、端口与版本实测）｜代码推导（随包文档 `deploy/prepare`、`deploy/main`、`deploy/single-instance`、`manual-upgrade`）｜待确认（现场 `installed-state.json` 的具体 compose/env 顺序、介质存放路径）｜不适用（源码构建部署——无产品源码仓库）。
>
> 生产只读默认；安装/迁移需审批与维护窗口。具体逐步命令以 runbook 与交付包官方文档为准。

## 1. 先识别目标（关键）

- 9090 = Hugo 文档站，**不是**安装目标；技能/产品安装目标是 38060/8060（已验证）。
- 当前实例已是 0.9.3（主镜像 `20261121.1795273330`，commit `3744b6aa`），五容器健康，**不需要重装**；本文件仅用于理解部署形态与迁移前置。

## 2. 交付形态（代码推导）

- 0.6.x 起：**四服务镜像 + 平台基础归档**，同宿主双引擎；镜像随产品 tar 交付，**不从 registry 拉取**，用 `install`/`apply` 按 `release.json` 导入。
- 主引擎 `compose.product.yaml` 只编排 edge / ai-agent / onlyoffice / quse-gateway；docx-rewriter 为双网改写侧车，与 Server 同镜像。
- Sandbox 引擎由 `config-sandbox` 配置 socket 目录 `/run/docker-sandbox/api` 与网络 `ai-agent-<ID>-sandbox-net`；平台基础 `20261109.standard.2` 经 `ai-agent-image base apply` 装入。
- v0.8.2 起 amd64 与 arm64 **均为完整产品包**，归档独立不可混用。

## 3. 标准新装顺序（代码推导，占位符按现场替换）

```bash
sha256sum -c ai-agent-product-0.9.3-linux-amd64.tar.sha256   # 外层校验
tar -xf ai-agent-product-0.9.3-linux-amd64.tar && cd 0.9.3
sha256sum -c SHA256SUMS                                       # 包内逐文件校验
DOCKER_CONTEXT=default ai-agent-deploy config-init --deployment-id <ID> --data-root <ROOT>
DOCKER_CONTEXT=default ai-agent-deploy config-sandbox --config "$CFG" \
  --socket-dir /run/docker-sandbox/api --network "ai-agent-$ID-sandbox-net"
DOCKER_CONTEXT=default ai-agent-deploy install --release "$DELIVERY/release.json" --config "$CFG"
DOCKER_CONTEXT=default ai-agent-deploy status --config "$CFG" --json   # phase=installed
```

- CLI：Image 0.5.52 / Deploy 0.6.20 / Software 0.8.0 / 客户端与共享 CLI 0.2.42（随 0.9.3）。
- 工具 ZIP 需**单独停服导入**（`manage-tools.product.mjs`）；全新安装默认不带扩展工具。
- 五个对外端口必须互不相同（8060–8063 + 8059 本机）；修改后重新 apply。

## 4. 前置条件（代码推导）

- 宿主：Docker API ≥1.48 + containerd 2.x + Compose v2 + Node 22；两套 containerd/dockerd + 独立网络与 iptables。
- 模型层另需 NVIDIA 驱动 + NVIDIA Container Toolkit（见 `gpu-management.md`）。
- `/data` 已用 80% → 安装/解包/备份前检查余量（风险 R5）。

## 5. 旧环境迁移（代码推导）

- 旧单引擎/旧启动布局**无自动一键迁移**；走 `manual-upgrade`：全量备份 → 建双引擎新实例 → 停写迁移 SQLite（`ai-agent.sqlite`）+ runtime（排除 `db`）+ ONLYOFFICE/Quse/Caddy 数据 → 三处适配（改写旧绝对路径、清理 sandbox profile 旧字段、补 `workspace.json` 的 `name` 等）→ `config-port` 切端口 → 验收 → 退役旧实例（`docker update --restart=no`，禁止全局 `docker prune`）。
- 仅换镜像**不能**撤销工具/数据库/共享软件变更；回退须同时恢复旧镜像、数据库与配置。

## 6. 验收要点

四服务 healthy；`curl -k https://<ip>:8060/api/health` 200；License active；模型/工具/Workspace 保留；端口按合同；磁盘与 GPU 水位正常。

## 7. 纪律

不在 docs 仓库伪造产品 CI/源码流水线（风险 R2）；不在生产做未审批变更；安装流程不得依赖 `CUSTOM_TOOL_MANAGEMENT_DISABLED` 的 admin 接口。
