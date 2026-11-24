# GPU 管理

> **证据状态**：已验证（`nvidia-smi` 实测 7×RTX4090 与各卡显存，2026-11-24）｜代码推导（随包文档 `local-model-deploy` 的 GPU 分配表、GPUStack 部署文档）｜待确认（推理框架具体类型 vLLM/SGLang/其他；驱动精确版本；容器启动参数）｜不适用（在现机新增推理负载做测试——风险 R7）。
>
> 生产只读默认。GPU 显存采样会漂移，操作前重新 `nvidia-smi`。

## 1. 硬件与瞬时占用（已验证）

- 7× NVIDIA GeForce RTX 4090，每卡约 49140 MiB。
- 实测显存（MiB）：`52 / 27192 / 23926 / 47923 / 25140 / 46304 / 47891`；利用率 0%。
- 多卡 >47GB（权重常驻），空闲卡之间不均衡 → 不要假设「有空闲卡可加实例」。

## 2. GPU 归属（代码推导，随包文档 2026-11-11 拓扑）

| GPU | 用途 |
|---|---|
| 0–3 | Strata 集群 `18100/18101/18102/18104`（各 ~47 GiB） |
| 4 | ComfyUI（Qwen/MOSS/h3 共用）+ OXR 文档解析；空闲约 21.4 GiB，h3 生成时整卡 ~47 GiB |
| 5 | ComfyUI MiniMax-H3-Image 独占 `:18198`（~46.3 GiB 常驻） |
| 6 | Strata 独立实例 `:18103`（~47 GiB） |

> 这是随包文档记录的拓扑，与 11-24 实测显存占用未必一一对应 → 跨源对照时标**待确认**。

## 3. 只读采集命令（已验证可用）

```bash
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'strata|comfyui|oxr|gpustack|inference'
```

## 4. GPUStack 纳管（代码推导，随包文档）

- GPUStack v2.3.0：容器 `gpustack`（主控 + 网关 `:808`，内嵌 Postgres）/ `gpustack-worker`（GPU 节点）；镜像 `gpustack/gpustack`，worker `quay.io/gpustack/gpustack:v2.3.0`。
- 依赖 NVIDIA 驱动 + NVIDIA Container Toolkit，`--gpus all`；模型权重放独立大盘（文档示例 `/nfs/data/models`）。
- `:808/healthz` → `ok`；`docker exec gpustack gpustack version` 查版本。
- 升级/迁移前先备份 `gpustack-data` 卷（含内嵌 Postgres 与网关配置），权重目录独立备份。

## 5. 约束与风险

- R7：多卡显存已高占用，**不得在此机启动新推理负载做测试**；任何压测需独立批准与窗口。
- 生图权重靠宿主内存换入换出，内存不足会反复读盘（随包文档）；宿主内存 499GiB 已用 408GiB。
- 推理框架类型（vLLM / SGLang / llama.cpp 等）在产品侧的具体使用**待确认**：无源码、未读推理容器启动参数，不得声称已审计。

## 6. 决策准则

只报告观测值；「能否再加模型/副本」的答复必须附前提（显存、并发、量化、KV Cache）与置信度，缺一即回答「待确认」。
