# 性能调优与容量评估

> 证据：`audit/resource-baseline.md`、`audit/architecture.md`、`audit/risk-register.md` R7、`content/docs/deploy-ops/deploy/main/_index.md` §4.2、`content/docs/deploy-ops/deploy/capacity/ops/_index.md`、`content/docs/deploy-ops/deploy/tools/_index.md`。调优属变更：须审批、测试环境验证、先备份再改；本机不新增测试负载（R7）。

## 1 适用版本
- Product 0.9.3；配置入口：`${AI_AGENT_DATA_ROOT}/config/ai-agent.env`（由 `config-agent KEY=VALUE` 维护，`KEY=default` 恢复出厂）、`onlyoffice.env`、`quse-gateway.env`；`deployment.env` 改动需重新 `apply`。
- 端口/探针合同：`/api/health` 每 30s、失败重试 3 次；quse `/health`；onlyoffice `/healthcheck`。

## 2 操作环境
- 同宿主双引擎；组件建议配额（工具指南）：Server 2 核/4 GB，OnlyOffice 2 核/4 GB（建议 ≥2 GB，压测后 ≥4 GB），Quse 0.5 核/512 MB，Edge 0.5 核/256 MB，Browser Runtime 1 核/2 GB，Workspace Sandbox 2 核/4 GB。
- 资源基线（2026-11-24）：128 核、499 GiB 内存（已用 408 GiB，可用 91 GiB）、`/data` 1.8T 已用 80%、GPU 7×4090 多卡显存 >47 GiB 且利用率 0%。

## 3 风险等级
- **中**：参数默认值是【合同】值；错误调整会导致会话中断、沙箱失控或内存争抢；高水位环境下放大效应明显。

## 4 前置条件
- 审批 + 变更单；备份当前 env 文件（`cp -a ... .bak-$(date +%Y%m%d-%H%M%S)`）与状态快照。
- 先在测试环境压测/验证；**不在此机启动新推理负载做测试**（R7）；容量结论必须列明前提、假设与置信度。
- 生产默认只读；改后需重启对应容器才生效（见 restart.md）。

## 5 需要检查的信息
- 当前 env 覆盖值（不要凭印象）：`config-show --config "$INSTANCE_CONFIG"`、`cat ai-agent.env`。
- 关键默认【合同】：`PORT/HOST=3190/0.0.0.0`、`AUTH_SESSION_TTL_MS=21600000`（6h，续期窗 1h）、`MAX_AGENT_STEPS=512`、`SANDBOX_DEFAULT_ENABLED=true`、`SANDBOX_DEFAULT_CPUS/MEMORY/PIDS_LIMIT=1/1g/128`、`SANDBOX_DEFAULT_IDLE_TTL_MS=300000`、`AI_AGENT_ASYNC_INVOCATION_CONCURRENCY=8`、`..._LEASE_MS=900000`、`..._JOB_RETENTION_DAYS=30`、`FILE_EXPLORER_UPLOAD_MAX_BYTES=32MB`。
- 参考性能数据（容量页实测）：100 并发混合浏览 P95 412ms / TPS 186 / 错误率 0；200 并发只读 P95 638ms / QPS 423；目标：浏览每域 100 并发 P95 ≤500ms、管理接口 200 并发只读 P95 ≤800ms。

## 6 具体操作
1. 建基线：记录 `/api/health`、三探针、`status --json`、错误率、`durationMs` 分布、资源水位。
2. 阶梯并发找拐点与最大持续容量（在测试实例进行），对照上表目标。
3. 仅在确有证据时改参数：沙箱限额、空闲回收、异步并发/租约/保留期、上传上限等；一次只改一类，便于归因。
4. 改后重启对应容器，复跑探针与业务冒烟；对比前后 P95 / 错误率 / 资源曲线。
5. 无法在只读与安全边界内验证时，输出「受阻/待确认」，不上生产。

## 7 实际命令
```bash
DOCKER_CONTEXT=default ai-agent-deploy status --config "$INSTANCE_CONFIG" --json
DOCKER_CONTEXT=default ai-agent-deploy config-show --config "$INSTANCE_CONFIG"
grep -vE '^\s*(#|$)' "${AI_AGENT_DATA_ROOT}/config/ai-agent.env"
curl -kfsS https://192.168.1.3:8060/api/health
curl -kfsS https://192.168.1.3:8062/health
free -h
df -h /data /data/docker-sandbox
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
docker logs --tail 100 ai-agent-dev-a-next-server
# 修改（测试环境验证后、审批通过再执行；Exact CLI 交互以现场 config-agent --help 为准，待确认）：
# config-agent AI_AGENT_ASYNC_INVOCATION_CONCURRENCY=8 --config "$INSTANCE_CONFIG"
```
> 具体 `config-agent` 参数名/调用形式在文档中仅说明「由 config-agent 子命令维护」，命令行精确语法**待确认**，需在测试环境验证后补充，不得直接照抄占位符上生产。

## 8 预期结果
- 基线可复现；调优后 P95 / 错误率满足或接近目标且不牺牲稳定性；资源水位（尤其 `/data` 与内存）不恶化。
- 每次改动可回溯到备份文件与审批单；无凭据进入 env 备份文件外泄。

## 9 验收标准
- [ ] 有前后对比数据（P95、错误率、资源曲线）与置信度说明。
- [ ] 业务冒烟通过；三条探针与 `status --json` 正常；未触碰事件加固单元。
- [ ] 测试环境已验证、生产审批已完成、回滚点已记录。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| 调参后错误率/延迟上升 | 用 `.bak-<时间戳>` 恢复 env，重启对应容器，回到基线 |
| 内存/磁盘水位恶化 | 立即停止测试，按容量流程清理无引用旧镜像（遵守交付包规则） |
| GPU 利用率低但显存满 | 多为权重常驻，按 gpu-diagnosis.md 判断，不新起负载“验证” |
| 无法给出置信容量 | 记录缺失前提（并发、量化、KV Cache 策略），标注待确认，不输出臆测数字 |

## 11 回滚步骤
- 配置回退：恢复备份的 `*.env`，重启对应容器；`deployment.env` 变更需重新 `apply`（使用原 compose/env 顺序）。
- 镜像层变更不在本 runbook 授权范围：按 `rollback.md` 用 `ai-agent-image rollback --image <旧镜像>`；**镜像回退不恢复数据库**，数据库迁移/恢复另走备份恢复通道。

## 12 操作记录
| 时间 | 基线指标 | 调整项 | 审批人 | 测试环境结果 | 生产前后对比 | 回滚点 |
|---|---|---|---|---|---|---|
| | | | | | | |
