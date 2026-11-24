# GPU 与显存诊断

> 证据：`audit/resource-baseline.md`、`audit/architecture.md`、`audit/risk-register.md` R7、`content/docs/deploy-ops/local-model-deploy/_index.md`。本 runbook **只读**；基于 2026-11-24 与 2026-11-11 实测基线做对比，不在本机启动新推理负载做测试（R7）。

## 1 适用版本
- 宿主：Linux 7.0.0-43-generic，128 核，499 GiB 内存；NVIDIA 驱动 + Container Toolkit 已装（模型文档前提）。
- 本机 7× RTX 4090，每卡 49140 MiB；模型侧：Strata（对话）、ComfyUI（生图）、OXR（解析）、Laya（CPU）、GPUStack 网关 `:808`。
- **推理框架具体类型（vLLM/SGLang/其他）待确认**：审计未取得推理容器启动参数，不做源码级断言。

## 2 操作环境
- 资源基线（2026-11-24）：显存占用 52 / 27192 / 23926 / 47923 / 25140 / 46304 / 47891 MiB，GPU 利用率 0%；`/data` 1.8T 已用 1.3T（80%）。
- GPU 归属（2026-11-11 实测）：GPU0–3 Strata 集群 `:18086`、GPU6 Strata 独立 `:18103`、GPU4 ComfyUI+OXR、GPU5 H3 独占 `:18198`（46.3 GiB 常驻）。

## 3 风险等级
- **低（只读）**，但误解读数会导致错误变更：多卡显存已高占用，任何“清显存/重启推理容器”动作都必须审批，且不在本 runbook 授权范围内。

## 4 前置条件
- 只读巡检无需变更审批；若诊断结论导向重启 / 切换权重 / 清理进程，另走审批、`restart.md` 或 `model-deploy.md`，并先备份。
- Key 只从 `/data/gpustack/keys-20261027.env`（0600）等受控位置读取；禁止把 Key、Token 打进日志。

## 5 需要检查的信息
- 每卡显存占用、利用率、温度/功耗；按进程归属显存（`nvidia-smi` 进程口径）。
- 推理服务健康：Strata `/health`、`/v1/status`（engine/model/concurrency）、ComfyUI `/system_stats`、shim `:18189/:18199/:18200`、OXR `:18094/openapi.json`、Laya `:8900/v1/models`。
- 网关路由：`/v1/models` 五个统一名、各路由 ready targets（路由与 target 查询需临时 admin 会话，写法**待确认**）。
- 宿主内存：`free -h`；ComfyUI 三套权重宿主内存驻留约 51.4 GiB，内存不足会变成反复读盘。

## 6 具体操作
1. 先看汇总：`nvidia-smi` 总览 + `docker stats` 容器内存，确认是否异常增长。
2. 再看服务：逐端口健康探针；只有探针失败才看对应容器日志（统计先于样本）。
3. 对比基线：与 7 卡占用表逐卡比对，标出变化 >10 GiB 的卡。
4. 判断边界：区分显存被推理权重常驻占用与异常泄漏；不擅自 `kill` 或重启推理容器。
5. 需要容量结论时，说明前提、假设与置信度；当前缺乏推理并发/量化/KV Cache 配置，无法给出置信容量模型（资源基线注明）。

## 7 实际命令
```bash
nvidia-smi
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
free -h
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'strata|comfyui|oxr|gpustack|inference'

curl -s http://127.0.0.1:18086/health
for p in 18100 18101 18102 18104; do
  printf '%s %s\n' "$p" "$(curl -s -m 4 http://127.0.0.1:$p/v1/status | jq -r '[.engine,.model,.concurrency.serving]|join(" ")')"
done
curl -s http://127.0.0.1:18103/v1/status
for p in 18189 18199 18200; do printf '%s %s\n' "$p" "$(curl -s -m 5 http://127.0.0.1:$p/health | head -c 60)"; done
curl -s http://127.0.0.1:18188/system_stats | tr ',' '\n' | grep -E 'comfyui_version'
curl -s http://127.0.0.1:18094/openapi.json >/dev/null && echo oxr-ok
curl -s http://127.0.0.1:8900/v1/models

set -a; . /data/gpustack/keys-20261027.env 2>/dev/null; set +a    # 仅内存读取，勿回显
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:808/v1/models
# $KEY 的变量名以受控 env 文件实际键名为准（待确认），不得回显或写入台账
```

## 8 预期结果
- 7 张卡状态可被 `nvidia-smi` 全部识别；利用率与占用可与基线对比。
- 五个统一模型名在网关可见；Strata 集群 4 实例 + 独立实例、三个生图 shim、OXR、Laya 均健康。
- 无新进程占用显存；`/data` 水位未因日志/缓存异常上涨。

## 9 验收标准
- [ ] 逐卡读数、服务健康、网关路由三项记录完整，并与基线差异已标注。
- [ ] 结论注明证据状态（已验证 / 待确认），未把「未读启动参数」的框架类型当事实。
- [ ] 未执行任何重启、清显存、切权重动作；无敏感信息输出。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| `nvidia-smi` 无输出 / 缺卡 | 查驱动与 Container Toolkit，上报，不在本 runbook 内改驱动 |
| 某 shim 探针失败 | 查对应 systemd 单元（`qwen-image-api` / `h3-image-api` / `moss-image-api`），转入 incident-response.md |
| Strata 单实例掉线 | nginx 集群有 least_conn 自动切换；记录后上报，必要时按各服务文档回退，不新起实例 |
| 显存持续高占用但利用率 0% | 多为权重常驻（正常），结合 `/v1/status` 判断，不视为泄漏直接清理 |
| 宿主内存紧张 | 生图权重驻留约 51.4 GiB；按容量流程评估，不做临时压测 |

## 11 回滚步骤
- 本 runbook 只读，无需回滚。
- 若曾按诊断建议做变更：按 `restart.md` / `model-deploy.md` 的回滚步骤恢复；涉及镜像/权重切换用旧镜像归档与原 compose，数据库变更与镜像回退分开处理。

## 12 操作记录
| 时间 | 7 卡显存摘要 | 异常卡号 | 服务探针结果 | 与基线差异 | 结论/证据状态 | 是否触发变更 |
|---|---|---|---|---|---|---|
| | | | | | | |
