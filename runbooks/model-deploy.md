# 模型接入与模型服务变更

> 证据：`audit/architecture.md`、`audit/dependencies.md`、`content/docs/deploy-ops/local-model-deploy/_index.md`、`content/docs/deploy-ops/local-model-deploy/gpustack/_index.md`、`content/docs/deploy-ops/ops/troubleshooting/_index.md`。模型配置为变更，须审批；模型服务变更不得在已满负载的卡上新起测试负载（R7）。

## 1 适用版本
- Product 0.9.3；平台「模型管理」入口 `/pages/models-admin`、`/pages/my-models`。
- 本地模型网关（文档实测 2026-11-11）：统一入口 `http://192.168.1.3:808/v1`（外网 `219.142.87.233:808/v1`），五个统一模型名：`qwen3.8-flash-next`、`minimax-h3-image`、`qwen-image-2.1`、`moss-image`、`laya`。

## 2 操作环境
- 推理侧：Strata Qwen3.8-Flash-Next（`:18086` 集群 / `:18103` 独立，模型 `qwen3.8-flash-next-ud-iq3_xxs`，上下文 262144，共 10 槽位）、ComfyUI 生图（`:18188`、h3 独占 `:18198`）、OXR 文档解析（`:18094`，非 OpenAI 协议）、Laya（`:8900`，AUTHED）。
- **注意证据冲突**：审计（2026-11-24）记录平台默认模型仍为 `glm-5.3-flash-local` → `http://192.168.1.3:18087/v1`，且 `/api/health` 返回 `model:"glm-5.3-flash"`；模型文档（2026-11-11）则记 `:18087` / DeepSeek / GLM 已停用。当前实际生效链路**待确认**，以现网 `/api/health` 与模型管理页为准，不得凭任一侧单独下结论。

## 3 风险等级
- **中**：改平台模型目录会影响全部会话/智能体；改推理服务会影响多租户；GPU 多卡显存已高占用（部分 >47 GiB）。

## 4 前置条件
- 审批 + 维护窗口；已备份（至少日常 `backup`）；已记录当前模型 ID / Base URL / 默认模型 / 凭据归属。
- Key 只从 `/data/gpustack/keys-20261027.env`（0600）等受控位置由环境变量读取，禁止输出；`laya` 路由 AUTHED，其余四条 PUBLIC（无 Key 也 200，访问控制依赖 Caddy/防火墙）。
- 先在测试环境验证新模型可用性与回滚路径；不得在此机新启推理负载做压测（R7）。

## 5 需要检查的信息
- 平台当前默认模型与模型目录条目；`/api/health` 返回的 model 字段。
- 网关 `GET /v1/models` 返回的五个统一名；各后端 `/health`、`/v1/status`、槽位与显存。
- 模型 ID、Base URL、上下文（262144）、是否图片输入、`json_object` / `json_schema` 支持情况。

## 6 具体操作
1. 只读体检：先探网关与后端，确认目标模型名确实可用（**先统计再样本**）。
2. 平台侧在「模型管理」按现场配置填写 Base URL / Model ID / 凭据并选择默认模型；具体要求：模型 ID `qwen3.8-flash-next-local`、Base URL `http://192.168.1.3:808/v1`（统一网关）或 `http://192.168.1.3:18086/v1`（直连）、模型 `qwen3.8-flash-next`（网关）或 `qwen3.8-flash-next-ud-iq3_xxs`（直连）、上下文 262144。管理界面的精确点击路径**待确认**，需在测试环境验证后补充。
3. 验收：实际发送一条消息有输出、刷新后历史可重读；视觉模型另测图片输入；如需判断/分类能力再接 `laya`（带 Key）。
4. 保留旧条目为备用而非直接删除；确认无回指旧 `:18087` 的启用条目。

## 7 实际命令
```bash
GS=http://192.168.1.3:808/v1            # 外网换 219.142.87.233
curl -sS "$GS/models"                    # 期望五个统一模型名
curl -sS "$GS/chat/completions" -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.8-flash-next","messages":[{"role":"user","content":"你好"}],"max_tokens":64}'
curl -s http://127.0.0.1:18086/health
curl -s http://127.0.0.1:18103/v1/status
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader
# 平台默认模型：curl -kfsS https://192.168.1.3:8060/api/health
# laya 需 Key：仅从环境变量注入 Authorization: Bearer $KEY，勿回显
```

## 8 预期结果
- 网关 `/v1/models` 返回五个统一名；对话请求有输出；Strata 集群与独立实例健康；显存无异常增长。
- 平台实际发消息有输出且历史可重读；模型管理页保存成功；无 Key 出现在日志/文档。
- 生图铁律：H3 固定 6 步 / CFG=1、无负面提示；`qwen-image-2.1` 与 `moss-image` 仅 `/images/generations`（MOSS 的 `/edits` 返回 400）。

## 9 验收标准
- [ ] 对话 + 图片输入（如适用）真实调用通过；平台历史一致性通过。
- [ ] 与审计记录的默认模型差异已确认并记录（待确认项清零前不得宣称链路已切换）。
- [ ] 备份、审批、回滚点齐全；事件加固单元未受影响。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| 平台全部会话失败、指向 `:18087` | 该地址已停用；按本节改到 `:808` / `:18086`，先测试环境验证 |
| 网关 503 / `/v1/models` 缺名 | 查后端 Strata / shim / GPUStack 路由状态，必要时用直连备选（审计前先审批） |
| 生图 `/images/edits` 用错接口 | 仅 `minimax-h3-image` 支持 edits（multipart，第 1 张图为 `<Picture 1>`）；其余用 generations |
| Laya 401 | 补 `Authorization: Bearer`（Key 仅来自受控 env 文件） |
| 404（误用 `/chat/completions` 调生图） | 改 `/images/generations` / `/images/edits` |

## 11 回滚步骤
- 平台模型配置：改回变更前记录的 Base URL / Model ID / 默认模型（配置回退，非数据库迁移）。
- 推理服务：若曾切换权重 / 实例，使用各服务文档中记录的旧镜像与 compose 逐项切回；不得在本机新增测试负载。
- 涉及数据库结构变更（如历史 020→021）属于**数据库迁移**，与模型/应用回退分开：按备份与恢复通道独立执行（`restore` 替换不合并）。

## 12 操作记录
| 时间 | 变更前默认模型/Base URL | 变更后 | 审批人 | 真实调用结果 | 证据冲突处理 | 回滚点 |
|---|---|---|---|---|---|---|
| | | | | | | |
