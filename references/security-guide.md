# 安全与事件加固

> **证据状态**：已验证（事件中该项单元 active、API 403 与 `CUSTOM_TOOL_MANAGEMENT_DISABLED` 实测，2026-11-24，见 `audit/risk-register.md`、`audit/services.md`、随包 `features/tools`）｜代码推导（随包文档 `architecture/system`、`ops/daily`、工具/Quse 边界说明）｜待确认（现场网络边界规则、账号与 License 当前状态、事件详情）｜不适用（源码级安全审计——无源码仓库）。
>
> 生产只读默认。最小权限：不读取/输出密钥、Token、密码及个人数据；凭据只从环境变量读取。

## 1. 现网事件加固状态（已验证）

- `ai-agent-incident-containment-20261115.service`：active/exited —— 2026-11-15 安全事件仍在边界加固，**不要擅自停用**；变更需审批。
- `CUSTOM_TOOL_MANAGEMENT_DISABLED`：`GET /api/admin/tools/extensions` 与 `GET /api/admin/tools/mcp/settings` 返回 HTTP 403（实例级安全策略），扩展工具排序 / MCP 服务编辑入口不可用。
  - 不是账号权限或 License 问题；Workspace 内已启用工具（网页搜索、Browser、图片工具等）调用不受影响。
  - 安装/运维流程**不得依赖**该 admin 接口；不要反复重试保存；需恢复时按事件加固流程走审批。
- 审计未输出任何密码 / Token。

## 2. 网络边界（代码推导）

- 入口收敛：Caddy Edge 唯一对外 HTTPS 入口（8060 主站 / 8061 ONLYOFFICE / 8062 Quse / 8063 Preview），8059 HTTP 仅本机。
- Quse Gateway 全部 REST 路由与 WS 通道**无认证**，安全完全依赖网络边界 → 限内网来源访问 3456/8062。
- 工具 ZIP 自 0.7.3 起只能在服务器本机停服维护；HTTP 与远程 `ai-admin` 不再提供安装/更新/卸载（只保留只读 `tools list`）。
- 根证书自 0.8.6 起离线分发，`/crt/` 在线下载关停为 404；证书续期由 `site-certs-renew.service` 管理。
- 本地模型网关 `:808` 有 4 条 PUBLIC 路由不校验 Key → 对外暴露面取决于 Caddy/防火墙（见 `inference-operations.md`）。
- API Key 文件 `/data/gpustack/keys-20261027.env`（0600）：勿入库、勿外传。

## 3. 沙箱安全边界（代码推导）

- 故障域下沉到引擎级：Workspace / Browser 在独立 Sandbox 引擎，用户代码、逃逸尝试、OOM 不冲击主引擎控制面。
- Server 仅经**只读挂入**的 Sandbox socket（`/run/docker-sandbox/api`）跨引擎 create/exec；v0.7.3 起主引擎 socket 不再挂入 Server，改只读身份文件 `/run/ai-agent/engine-id`。
- 沙箱容器 `--cap-drop ALL` + 资源限额 + label 合同；隔离不可用时明确失败，**不回退本机**。
- Browser：动作白名单 default-deny（27 项），`eval`/`upload`/`download`/`cookies` 封死；密码输入不落快照；空闲 10 分钟退出。
- 私有文件通道逐请求校验成员权限（0.9.1 起）。

## 4. 账号 / 凭据（已验证 + 代码推导）

- 管理员 `me` 会话 API `/api/auth/login` 实测 200；审计中未输出任何密码/Token。
- 0.8.6 起 `install` 强制为 `me` 设置初始化密码；`ai-agent-deploy reset-super` 本地恢复（需搭配 ≥0.8.6 镜像）。
- `POST /api/invoke` 用 `ait_` Bearer Token + SHA-256 哈希库存，AJV strict 校验；失败 401/422。
- 模型 Token 在管理页只在编辑弹层遮罩展示；导出 JSON 含完整 Token，妥善保存；截图/文档/沟通不暴露真实 Token。
- MCP 本人凭据只存当前用户自己的 Token/请求头，**不随 Workspace 或 Agent 复制**。

## 5. 审计与合规

- SQLite 记录操作审计事件（`015_init_audit`），v0.9.3 将审计恢复移到 HTTP 监听启动后（仅补齐启动前中断记录）——代码推导。
- License active，到期 2026-11-28（实测，需按当前日期复核）；License 绑定主引擎身份文件。

## 6. 禁止事项

- 不绕过平台权限、不在文档/脚本硬编码凭据、不浏览器直连服务器文件系统。
- 不擅自停用事件加固单元、不依赖被禁用的自定义工具 admin 接口。
- 无源码仓库 → 不声称完成源码级安全审计（风险 R2）；无证据的安全结论标**待确认**。
