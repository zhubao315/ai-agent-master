# 重启操作（服务 / 引擎 / 容器）

> 证据：`content/docs/deploy-ops/deploy/{main,single-instance}/_index.md`、`audit/services.md`、`content/docs/deploy-ops/deploy/special/fonts/_index.md`、`content/docs/DEPLOYMENT.md`。生产默认只读；重启属变更，须审批并先确认影响范围。

## 1 适用版本
- Product 0.9.3（`ai-agent:20261121.1795273330-*`）；主引擎 5 容器：`ai-agent-dev-a-next-{server,edge,onlyoffice,quse-gateway,docx-rewriter}`（名称中的实例 ID 以现场为准）。
- systemd：`docker-sandbox.service`、`containerd-sandbox.service`、`ai-agent-sandbox-proxy.service`、`ai-agent-hugo.service`；`ai-agent-incident-containment-20261115.service`（active/exited，禁止停用）。

## 2 操作环境
- 同宿主双引擎；主服务容器挂载 Sandbox socket 目录（`/run/docker-sandbox/api`），`RuntimeDirectoryPreserve=yes` 保证 Sandbox 重启后无需重建主服务。
- 文档站 `ai-agent-hugo.service` 监听 1313，宿主 Caddy 9090 反代；产品入口 38060/8060。

## 3 风险等级
- **中～高**：`systemctl restart docker` 在无 live-restore 时会中断现有容器；重启 Sandbox 需证明主引擎不受影响；Sandbox 引擎曾出现重启循环需先 `reset-failed`。

## 4 前置条件
- 审批、低峰窗口；确认无活动任务/长任务；已做日常 `backup`（库+配置，不中断）。
- 记录基线：主引擎 MainPID、`docker0` ifindex、容器 ID、当前健康探针结果。
- **dry-run / 预演**：先核对命令作用对象（context / 单元名 / 容器名），必要时在测试环境演练；不得停止事件加固单元。

## 5 需要检查的信息
- `systemctl is-active` 各单元；`docker ps` 主引擎与 Sandbox 引擎容器清单（含 `label=com.docker.compose.project=...`）。
- 当前镜像与容器 ID：`docker inspect ai-agent-<ID>-server --format '{{.Config.Image}}'`。
- 项目启动参数以 `<AI_AGENT_DATA_ROOT>/installed-state.json` 的 `target` 为准（composeFiles / envFiles / projectName），不凭印象拼。

## 6 具体操作
1. 只重启单个应用容器：`docker stop` → `docker start`（保留容器与数据）；`apply` 类操作会自行停止替换，无需预先停。
2. 重启 Sandbox 引擎（两轮独立重启试验）：每轮后核对主引擎 MainPID 与 `docker0` ifindex，并实际调用一次主服务。
3. **restart 与 recreate 区分**：`docker restart` 保留可写层，`AllFonts.js` 不丢；recreate（镜像/配置变更）会退回镜像默认，须重跑字体同步与双网重应用脚本。
4. 文档站内容变更通常只需 `systemctl reload caddy`；模板/资源变更后先 `make build` 再 reload（仅在文档站维护场景）。

## 7 实际命令
```bash
# 基线
systemctl show docker.service --property MainPID --value
cat /sys/class/net/docker0/ifindex
docker --context default ps --format '{{.Names}} {{.Status}}'
docker --context ai-agent-sandbox ps -a --format '{{.Names}} {{.Status}}'

# 单应用容器重启（server 为例，edge/onlyoffice/quse-gateway/docx-rewriter 同理）
docker --context default stop ai-agent-<ID>-server
docker --context default start ai-agent-<ID>-server

# Sandbox 引擎两轮独立重启（首次建立双引擎布局必做）
for i in 1 2; do
  sudo systemctl restart docker-sandbox.service
  test "$(systemctl show docker.service --property MainPID --value)" = "$main_pid_before"
  test "$(cat /sys/class/net/docker0/ifindex)" = "$main_bridge_before"
done
# 重启循环时：systemctl stop docker-sandbox.service → reset-failed → 修网桥 → start
```

## 8 预期结果
- 容器恢复 healthy/Up；三条探针 200；`status --json` 仍 `phase=installed`、`pending=null`。
- 两轮 Sandbox 重启后主引擎 MainPID 与 `docker0` ifindex **均未变**；停止 Sandbox 期间主站、登录、License 与静态 Preview 仍可用；恢复后 Workspace ID、私有安装与文件保持。
- 事件加固单元仍 active；无凭据输出。

## 9 验收标准
- [ ] 健康检查与业务冒烟（实际发一条消息 / 打开文档）通过。
- [ ] 容器 ID 未被无意替换；有字体/双网定制时同步脚本已重跑（路径 `${AI_AGENT_DATA_ROOT}/fonts/sync-onlyoffice-cjk-fonts.sh`、`${AI_AGENT_DATA_ROOT}/rewriter/reapply-docx-dualnet.sh`）。
- [ ] `/data/ai-agent-next/maintenance/post-deploy.sh` 路径**待确认**：文档仅记载 `/data/ai-agent-dev-a/maintenance/post-deploy.sh`（站点侧、path 单元自动监听），勿在未确认实例上执行。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| Sandbox 单元反复重启 | `stop` → `reset-failed` → 检查两个网桥是否被预建 → `start` |
| 主引擎容器网络中断、`docker0` 消失 | 检查 Sandbox 是否用了 `bridge:none`/地址池，按部署手册改回命名网桥 |
| 重启后字体消失 | recreate 导致列表缓存丢失，重跑字体同步脚本 |
| 编辑页报「加载 ONLYOFFICE API 失败」 | 重跑 `reapply-docx-dualnet.sh` |
| 事件加固单元被误停 | 立即上报并按加固流程恢复，不擅自继续变更 |

## 11 回滚步骤
- 单容器：`docker stop` 后 `docker start` 原容器（ID 不变）；若已 recreate，用 `ai-agent-image rollback --image <旧镜像>`（同参数集，见 rollback.md），**数据库不随镜像回滚**。
- 不可逆重启前已做备份；恢复失败时按 `ai-agent-deploy restore <备份目录>` 走正式恢复通道（替换不合并）。

## 12 操作记录
| 时间 | 对象（单元/容器/引擎） | 审批人 | 基线 MainPID/ifindex | 重启后核对 | 业务冒烟 | 备注 |
|---|---|---|---|---|---|---|
| | | | | | | |
