# 健康检查与日常巡检

> 证据：`audit/services.md`、`audit/resource-baseline.md`、`content/docs/deploy-ops/ops/daily/_index.md`、`content/docs/deploy-ops/deploy/main/_index.md` §6。本 runbook **只读**，不改变任何状态；发现异常转入 incident-response.md。

## 1 适用版本
- Product 0.9.3（主镜像 `20261121.1795273330-*`）；5 个容器全部 healthy/Up 为已知健康基线（2026-11-24 实测）。
- 文档站 9090 为 Hugo，不是产品入口；产品入口 38060（公网）/ 8060（内网）。

## 2 操作环境
- 主引擎 `default` + Sandbox 引擎 `ai-agent-sandbox`；`INSTANCE_CONFIG` 指向实例 `deployment.env`（现场 dev-a-next 对应 `/data/ai-agent-next`，路径以台账为准）。
- 健康端点：`/api/health`（核心，30s 一次、失败重试 3 次【合同】）、`/health`（Quse）、`/healthcheck`（ONLYOFFICE）。

## 3 风险等级
- **低（只读）**。注意：不得输出 License 私钥、Token、密码；巡检结果写入台账时排除凭据。

## 4 前置条件
- 已确认目标实例与端口（避免误查文档站 9090）；凭据只从环境变量读取，不落盘。
- 巡检频率：每日状态摘要 + 三探针；每周磁盘与镜像治理；每季度恢复演练。

## 5 需要检查的信息
- 部署状态：phase、pending、sandboxError、平台基础版本。
- 容器状态：主引擎 4–5 个容器、Sandbox 引擎 Workspace/系统软件容器。
- 资源：CPU / 内存 / 磁盘 `/` 与 `/data` / GPU 显存与利用率。
- License：审计时 `/api/license/status` 为 active（到期 2026-11-28，临期需提前跟进）。
- 日志：结构化单行 JSON，字段 `ts/level/component/event/outcome`、`requestId/invocationId/sessionId/turnId`、`durationMs`。

## 6 具体操作
1. 状态与容器清单 → 2. 三条健康探针 → 3. 双引擎 ID / 数据目录比对 → 4. 磁盘与 GPU → 5. 最近日志中的 error/warn → 6. License 与字体/双网专项（如启用）→ 7. 记录并对比基线。
- **统计先于样本**：先看 `status --json` 与计数，再按 `requestId` 串联单条日志。

## 7 实际命令
```bash
DOCKER_CONTEXT=default ai-agent-deploy status --config "$INSTANCE_CONFIG" --json
docker --context default ps --format '{{.Names}} {{.Status}}'
docker --context ai-agent-sandbox ps -a --format '{{.Names}} {{.Status}}'

curl -kfsS https://192.168.1.3:8060/api/health    # 200 {"ok":true,"profile":"assistant-v1",...}
curl -kfsS https://192.168.1.3:8062/health        # {"ok":true,"v":1}
curl -kfsS https://192.168.1.3:8061/healthcheck   # true

docker --context default info --format '{{.ID}} {{.DockerRootDir}}'
docker --context ai-agent-sandbox info --format '{{.ID}} {{.DockerRootDir}}'
DOCKER_CONTEXT=ai-agent-sandbox ai-agent-image base inspect --deployment <ID> --json

df -h /data /data/docker-sandbox
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
docker logs --tail 50 ai-agent-dev-a-next-server
```

## 8 预期结果
- `phase=installed`、`pending=null`、`sandboxError=null`；平台基础 `20261109.standard.2`（20 项）。
- 5 容器 Up/healthy；两引擎 ID 与 DockerRootDir 不同（`/data/docker` vs `/data/docker-sandbox`）。
- 三探针 200/true；License active；无新增 error 级事件。
- 资源基线（2026-11-24 实测，用于对比）：内存 499 GiB 总 / 408 GiB 已用；`/data` 1.8T 已用 1.3T（80%）；GPU 7× RTX 4090（每卡 49140 MiB），部分卡显存 >47 GiB、利用率 0%。

## 9 验收标准
- [ ] 状态、容器、探针、引擎隔离、License 五项全部符合预期。
- [ ] 与基线偏差已记录（尤其 `/data` 水位与 GPU 显存）；无敏感信息外泄。
- [ ] 异常项已附 `requestId` / `invocationId` 等追踪 ID，转入故障排查流程。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| 探针非 200 / phase 非 installed | 记录原始输出，按 incident-response.md 取证，不擅自重启 |
| 两引擎 ID 或数据目录相同 | 高优先级上报：Sandbox 未独立，禁止继续运行 Workspace |
| `/data` 水位接近 100% | 上报容量风险，清理只按交付包说明处理无引用旧镜像 |
| 仅看到文档站 9090 正常 | 不代表产品正常；必须单独探测 38060/8060 |

## 11 回滚步骤
- 本 runbook 为只读巡检，无需回滚；若巡检过程被误操作变更，按对应 runbook（restart / rollback）恢复，并执行一次完整验收。

## 12 操作记录
| 时间 | 状态 phase/pending | 三探针 | 引擎隔离 | `/data` 水位 | GPU 摘要 | 异常与追踪 ID |
|---|---|---|---|---|---|---|
| | | | | | | |
