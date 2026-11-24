# 推理服务运维

> **证据状态**：已验证（GPU 与容器实测、模型网关端口实调记录见随包文档）｜代码推导（随包文档 `local-model-deploy/gpustack` 的路由表、调用与排障）｜待确认（产品侧推理框架类型与启动参数；现场 Key 与路由最新状态）｜不适用（源码级推理链路审计）。
>
> 只读默认；压测需审批。此文描述**本地模型网关**，不是产品五容器内部推理实现。

## 1. 网关入口（代码推导，随包文档）

- GPUStack 统一网关 `:808/v1`；`/healthz` → `ok`；`GET /v1/models` 需 Key。
- 五个统一模型名与调用方法见 `model-management.md`。对话走 `/v1/chat/completions`，生图走 `/v1/images/generations` 与 `/v1/images/edits`（multipart，可透传）。
- 生图响应为 `{"data":[{"b64_json":"…"}]}`，须解码落盘，不要打印到终端。

## 2. 健康与性能验收（代码推导）

```bash
curl -s http://127.0.0.1:808/healthz                       # ok
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:808/v1/models
curl -sS http://127.0.0.1:808/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.8-flash-next","messages":[{"role":"user","content":"你好"}],"max_tokens":64}'
```

- 判定：模型列表含目标模型；单请求 200 且 `choices` 正常；流式逐块返回；不存在模型名应 404 而非静默回落。
- 随包文档整链路验收脚本：`python3 /data/strata-infer/tests/gpustack-route-20261008/run-tests.py`。
- 实测参考（2026-11-11，随包文档）：`qwen3.8-flash-next` 0.58s 出词；`minimax-h3-image` 1024² 8.1s、`/edits` 14.5s；`qwen-image-2.1` 512²/16 步 4.0s（换权重后 76.2s）；`moss-image` 512²/8 步 10.1s；`laya` 0.32s。
- 吞吐受同机其他负载影响可达 ±30%，只作量级比较，不是 SLA。

## 3. 关键运维坑（代码推导）

- `qwen3.8-flash-next` 经网关由 `strata-cluster`（:18086，weight 80）+ `strata-gpu6`（:18103，weight 20）聚合；集群实例只 bind 内网 → 必须用 `192.168.1.3`，`172.17.0.1` 不可达。
- `POST /v2/model-routes/{id}/add-targets` 是**全量替换**，必须一次传全部 target；建议用 Web UI。
- `PUT /v2/model-routes/{id}` 不接受 `access_policy`；改访问策略走 `POST .../access`。
- `ready_targets` 不随上游存活变化，**不能当健康依据**。
- Laya 原生 `/v1/analyze` 不透传（404），只能直连 `:8900`；OXR `:18094` 非 OpenAI 协议，不挂路由。
- 自建 OpenAI 兼容 shim 必须处理 `Transfer-Encoding: chunked`，否则经网关会出现空 body / 400。

## 4. 用量统计（代码推导）

- GPUStack 自动记录请求数、prompt/completion/缓存 token，维度含模型路由/Provider/模型/用户/API Key/日期。
- `GET /v2/usage/summary`、`POST /v2/usage/breakdown`、`GET /v2/dashboard/usage`；表 `model_usages`；Web UI Usage 页。
- 路由层只记用量，**不记请求/生成内容**（messages、生成文本）。

## 5. 维护操作（代码推导，需审批）

```bash
docker logs -f gpustack
docker logs -f gpustack-worker
docker restart gpustack gpustack-worker   # 生产变更，需审批
```

升级/迁移前备份 `gpustack-data` 卷与权重目录 `/nfs/data/models`。

## 6. 风险边界

- 4 条 PUBLIC 路由不校验 Key → `:808` 的暴露面取决于 Caddy/防火墙；对外网开放 :808 等于开放对话与三个生图模型。
- 风险 R7：多卡显存高占用，不在此机起新推理负载做测试；任何并发压测需独立审批窗口。
- 产品侧实际使用的推理框架与参数**待确认**（无源码、未读推理容器启动参数）。
