# 模型管理

> **证据状态**：已验证（审计 API `/api/health` 与随包 OpenAPI、模型管理页文档，2026-11-24）｜代码推导（随包文档 `local-model-deploy`、`features/models`）｜待确认（默认模型上游 `:18087` 是否仍存活；Skill 真实调用验收）｜不适用（源码级模型路由审计）。
>
> 生产只读。Token 属敏感信息，不读取、不输出、不入库；只从环境变量读取。

## 1. 产品模型目录（Global Admin）

- 入口：管理员「模型管理」页；workspace / Studio / Invocation / CLI 只引用目录中的 `modelId`，不各自保存 provider/baseUrl/token——代码推导。
- `GET /api/admin/models` 可核对现场目录与 `defaultModel`（已验证文档口径）。
- `modelId` 全局唯一、不含大写字母；保存时会写完整配置（无「留空表示不修改」）。
- 字段：modelId、provider、model、baseUrl、Thinking Profile、默认档位、Token、可选 `autoCompactTokenLimit`、支持图片输入。
- 自动压缩阈值：Token 口径，最小 32,000；留空继承全局默认 160,000；从下一轮对话生效。

## 2. 审计实测的默认模型（已验证，但需复核）

- 审计与随包文档均记录 `dev-a-next` 默认模型为 `glm-5.3-flash-local`，`is_default=1`，Base URL `http://192.168.1.3:18087/v1`。
- `GET /api/health` 返回 `model:"glm-5.3-flash"...`。
- **冲突**：随包文档 `local-model-deploy` 记载 `:18087`（Maya / DeepSeek / GLM）上游已于 2026-11-05 停止，建议改指 `qwen3.8-flash-next`。
- **处置**：该上游存活状态标 **待确认**。任何模型配置变更前，用 `/api/health` + 模型管理页「测试模型」实测，不凭印象改。

## 3. 本地模型网关（代码推导，随包文档 2026-11-11）

统一入口 `http://192.168.1.3:808/v1`（GPUStack，外网 `219.142.87.233:808/v1`），五个统一模型名：

| 统一模型名 | 方法 | 鉴权 |
|---|---|---|
| `qwen3.8-flash-next` | `/v1/chat/completions` | PUBLIC（免 Key） |
| `minimax-h3-image` | `/v1/images/generations`、`/v1/images/edits` | PUBLIC |
| `qwen-image-2.1` | `/v1/images/generations` | PUBLIC |
| `moss-image` | `/v1/images/generations`（仅文生图） | PUBLIC |
| `laya` | `/v1/chat/completions` | AUTHED（必须带 Key） |

- 直连备选（网关异常时排障）：对话 `:18086` / `:18103`；生图 shim `:18189`/`:18199`/`:18200`；决策 `:8900`；文档解析 OXR `:18094`（非 OpenAI 协议，不走网关）。
- Key 只在 `laya` 与 `GET /v1/models` 必要；PUBLIC 路由不校验 Key，`allowed_model_names` 不生效。
- API Key 存放 `/data/gpustack/keys-20261027.env`（0600，勿入库、勿外传）。

## 4. 工具模型与图片模型（代码推导）

- 图片识别（`inspectImage`）与图片生成（`generateImage`）在「工具管理」配置，不在模型管理页；`generateImage` 支持多候选 + 默认，图生图需填完整 `/v1/images/edits` 地址。
- 外部模型可经 api.deepseek.com 等；DeepSeek 官方 / llama.cpp / MTPLX 等 Thinking Profile 有部署约束，按文档说明选择，不按名字猜。

## 5. 变更纪律

- 改模型前确认没有 workspace / 脚本 / 外部调用仍引用旧 `modelId`。
- 模型测试会触发真实调用；失败不等于页面错误，先看 token/baseUrl/模型名/权限。
- 现场 `CUSTOM_TOOL_MANAGEMENT_DISABLED` 禁止依赖自定义工具 admin 接口；模型与工具配置分开处理。
