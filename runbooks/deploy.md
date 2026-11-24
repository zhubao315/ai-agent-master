# 产品新实例部署（0.9.3 同宿主双引擎）

> 证据：`content/docs/deploy-ops/deploy/{main,prepare,single-instance,tools}/_index.md`、`audit/{architecture,resource-baseline,risk-register}.md`。生产默认只读；新装为高风险写入，须审批、先 dry-run、备份后再执行不可逆步骤。

## 1 适用版本
- Product **0.9.3**：主镜像 `20261121.1795273330-amd64`（源提交 `3744b6aa…`）；ONLYOFFICE `9.4.0-session.16-r5-fonts3`；Caddy `2.11.4-alpine`；Quse `1.0.24-20260911.1789148529`；数据库 `021_async_invocation_actor`。
- CLI：Image 0.5.52 / Deploy 0.6.20 / Software 0.8.0；平台基础 `20261109.standard.2`（20 项）；客户端与共享 CLI 0.2.42。
- TencentOS Server 4 离线介质**仍为 0.8.8 基线**（内含 0.9.0 主程序包），没有 0.9.3 离线介质；需按升级路径另行更新主镜像。

## 2 操作环境
- 一台 Linux 宿主、两个**独立 dockerd**：主引擎 `default`（socket `/var/run/docker.sock`）跑 edge / ai-agent / onlyoffice / quse-gateway；Sandbox 引擎 socket `/run/docker-sandbox/api/docker.sock` 跑 Workspace，独立 containerd `/run/containerd-sandbox/containerd.sock`。
- 示例变量：`DELIVERY=/data/handoffs/0.9.3`、`INSTANCE_ID=ai9059`、`INSTANCE_ROOT=/data/ai-agent-$INSTANCE_ID`、`INSTANCE_CONFIG=$INSTANCE_ROOT/config/deployment.env`；端口方案 9059–9063（示例，可整体平移）。

## 3 风险等级
- **高**：会写 daemon.json / systemd 单元 / 双引擎网络；改 `data-root` 或存储后端会让现有容器「幽灵化」；`/data` 已用 80%，空间紧张（R5）；事件加固期间变更需审批（R4）。

## 4 前置条件
- 明确审批与维护窗口；新装只在**空机或专用数据盘**上改 `daemon.json`，有业务实例只补 drop-in，不改 `data-root` / 存储后端。
- 介质架构与主机一致（`x86_64`→amd64，`aarch64`→arm64）；`.tar.sha256` 与包内 `SHA256SUMS`（227 项）全部 OK。
- 五个基础端口空闲、Sandbox 子网不与现有网络重叠、主引擎有 `DOCKER-USER` 链；Docker API ≥ 1.48、Compose v2、Node ≥ 22。
- **先跑 `--check-only` / `--dry-run`**；失败保留现场，修正后重跑同一条 `install`，不删数据目录重来。

## 5 需要检查的信息
- `uname -m`、`df -h /data`、`free -h`、`ss -tlnp`、`ip -4 route`。
- `docker --context default info --format '{{.ID}} {{.DockerRootDir}} {{.Driver}}'`；Sandbox 同命令；两引擎 ID / DockerRootDir 必须不同。
- `release.json`（四服务组合唯一输入【合同】，禁止浮动标签）、`installed-state.json` 的 `target`。

## 6 具体操作
1. 环境检查（§2）→ 数据盘/主 Docker/Node+CLI → 交付包校验。
2. 创建独立 Sandbox 引擎（containerd-sandbox + docker-sandbox + 网桥/网络脚本，网桥名 ≤15 字符）；Docker 29.x **禁止** `bridge:none` / 地址池。
3. 仅在 Sandbox 引擎 `base apply` 平台基础；主引擎 `config-init` / `config-sandbox` / `install`。
4. 初始化：根证书信任、License active、`me` 密码登录、模型可用、8 个工具 ZIP 停服导入、字体（18 名称 / 32 文件）；如启用双网改写，`apply` 后重跑 `rewriter/reapply-docx-dualnet.sh` 与字体同步脚本。
5. 验收并登记环境台账（引擎、目录、端口、介质版本、未完成项）。

## 7 实际命令
```bash
# ① 只体检，不改动（dry-run 等价动作）
bash ai-agent-new-instance.sh --instance-id ai9059 --ip <部署IP> \
  --delivery /data/handoffs/0.9.3 --check-only
# ② 交付包校验
sha256sum -c ai-agent-product-0.9.3-linux-amd64.tar.sha256
(cd "$DELIVERY" && sha256sum -c SHA256SUMS)      # 227 项
# ③ 平台基础（Sandbox 引擎）
DOCKER_CONTEXT=ai-agent-sandbox ai-agent-image base apply \
  --file "$DELIVERY/platform/amd64/platform-base-20261109.standard.2-amd64.tar" \
  --base-image "$DELIVERY"/images/amd64/ai-agent-sandbox/*.tar \
  --deployment "$INSTANCE_ID" --runtime-root "$INSTANCE_ROOT/runtime"
# ④ 配置 + 安装（主引擎）
DOCKER_CONTEXT=default ai-agent-deploy config-init --deployment-id "$INSTANCE_ID" --data-root "$INSTANCE_ROOT"
DOCKER_CONTEXT=default ai-agent-deploy config-sandbox --config "$INSTANCE_CONFIG" \
  --socket-dir /run/docker-sandbox/api --network "ai-agent-$INSTANCE_ID-sandbox-net"
DOCKER_CONTEXT=default ai-agent-deploy install --release "$DELIVERY/release.json" --config "$INSTANCE_CONFIG"
DOCKER_CONTEXT=default ai-agent-deploy status --config "$INSTANCE_CONFIG" --json
```

## 8 预期结果
- `status --json`：`state.phase=installed`、`state.pending=null`、`sandboxError=null`；平台基础 `base inspect` 返回 20 项。
- 主引擎 4 个常驻容器 healthy/Up；Sandbox 引擎有 Workspace / 系统软件查询容器；两引擎 ID 与数据目录不同。
- 三条探针：`/api/health` 200、`/health` `{"ok":true,"v":1}`、`/healthcheck` `true`。

## 9 验收标准
- [ ] 容器与健康探针全绿；License active；`me` 可登录；模型实际发消息有输出。
- [ ] 扩展工具可见并实际调用一次；字体在 Office 中可选（18 名称 / 32 文件）。
- [ ] Sandbox 独立重启两轮：主引擎 MainPID 与 `docker0` ifindex 不变（只比名称不足以证明隔离）。
- [ ] 测试资源清理；未完成项与台账登记完整。

## 10 失败处理
| 报错 | 处置 |
|---|---|
| `"name" not a valid ifname` | 网桥名 >15 字符，改 `ai-sb-<ID前8位>` / `ai-sx-<ID前8位>` |
| `failed to check bridge interface existence` | 网桥须由 `ExecStartPre` 在 dockerd 之前预建（Docker 29.6+） |
| `Not enough software volume space for installation.` | Sandbox `data-root` 所在文件系统需 ≥≈9 GiB，迁到大盘 |
| 「系统软件查询 Sandbox 不可用」 | 平台基础未装或装错引擎；确认 `DOCKER_CONTEXT=ai-agent-sandbox` |
| 安装中断 | 保留现场，修正后重跑同一条 `install`；有 `pending` 必须用同一份 `release.json` |

## 11 回滚步骤
- 全新安装未成功：先修原因重跑 `install`（不是删库重装）；脚本阶段可重入，引擎失败先 `systemctl stop docker-sandbox*.service` → `reset-failed` → 重跑。
- 不可逆清理（删除实例目录 / 卷）前必须 `backup --full-backup` 并取得审批；**禁止 `down -v`**；完整卸载命令路径**待确认**，需在测试环境验证后补充。
- 数据库迁移与应用回滚分别制定方案；本场景新装不产生跨版本迁移。

## 12 操作记录
| 时间 | 实例 ID | 架构 | 介质/版本 | 审批人 | dry-run 结果 | 验收结论 | 未完成项 |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
