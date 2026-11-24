# Agent Runtime 与技能

> **证据状态**：已验证（Skillshub API 真实往返测试、运行时路径实测，2026-11-24，见 `audit/skill-runtime-audit.md`）｜代码推导（随包文档 `features/skillshub`、`features/tools`、`architecture/system`）｜待确认（Agent 是否能在会话/Workspace 中实际调用已安装技能；技能内脚本执行边界）｜不适用（源码级 Runtime 走读）。
>
> 生产只读。安装/卸载技能须审批；写操作先 diff/dry-run，再确认。

## 1. Skillshub 原生能力（已验证）

- 23 个公共技能：`GET /api/skillshub/public` 实测；管理端 `GET /api/admin/skills` 当前 items 为空。
- UI 页面：`skills-hub` / `skills-editor` / `skillshub-portal`。
- 存储：`/data/ai-agent-next/runtime/public-skills/records/*.json`（23 条）、`public-skill-repos/`（23 目录，实测空）、`admin-resources/skills/`（空）。
- 记录字段：`id/name/title/description/ownerUserId/source/contentHash/createdAt/updatedAt`（公共详情不返回正文）。

## 2. 原生 SKILL.md 支持（决定性结论，已验证）

- 实测往返：`POST /api/skillshub/private/upload`（JSON `{"content":"<SKILL.md 全文>","overwrite":true}`）→ 200；`GET /api/skillshub/private/{skillName}` 返回 content 且逐字节一致；`DELETE` → 200。
- 带 `name` + `description` YAML frontmatter 的标准 SKILL.md 被接受；无 frontmatter 纯文本被拒（400「请提供SKILL.md frontmatter」）。
- 临时技能 `format-probe-20261124` 已删除；现有 23 个公共技能未改动。
- **结论**：平台原生支持标准 Agent Skills 格式 SKILL.md（解析在 API/服务端完成），无需适配层。
- 安装位置（实测返回）：`/data/ai-agent-next/runtime/skillshub/users/me/myskills/<skillName>`。

## 3. 管理 API（来自 0.9.3 随包 OpenAPI，已验证存在）

- `POST /api/skillshub/private/upload`（multipart ZIP 或 JSON `content`）
- `POST /api/admin/skills`、`PUT/DELETE /api/admin/skills/{skillName}`
- `POST /api/runtime-workspaces/{id}/skills/install|upload`
- `GET/PUT /api/skillshub/private/{skillName}`、`POST .../publish`

## 4. 调用链（代码推导）

- 入口 `POST /api/invoke`（`ait_` Bearer Token，AJV strict 校验）→ materialization 隔离工作区 → Sandbox 引擎 `docker create`（cap-drop ALL + 资源限额 + label 合同）→ `docker exec` 执行 → 模型工具循环（≤512 步）→ SSE / 同步 JSON → 轮次快照落盘。
- Server 与 Workspace/Browser 之间**无 HTTP 调用**，全部经 Sandbox 引擎 Docker API（create/exec）。
- 异步任务：SQLite 队列（并发 8，lease 15min，attempt 计数），记录保留 30 天（代码推导）。

## 5. 工具与 MCP（代码推导）

- 扩展工具 ZIP：browser / webSearch / generateImage / inspectImage / publishUrl / webFetch / rg / desktopBrowser（8 个）；MCP 自 0.8.8 起改为原生配置（HTTP streamable-http / Workspace stdio），旧 `mcp.zip` 退出。
- 工具包只能在**服务器本机停服维护**（`manage-tools.product.mjs`）；网页「工具管理」只做参数配置与展示排序。
- **现场禁用**：`CUSTOM_TOOL_MANAGEMENT_DISABLED` —— `GET /api/admin/tools/extensions` 与 `GET /api/admin/tools/mcp/settings` 返回 403（2026-11-15 事件加固），扩展工具排序 / MCP 编辑入口不可用；Workspace 内已启用工具调用不受影响。安装流程不得依赖该接口，也不要反复重试保存。
- 渐进工具加载（0.8.8）：先注入核心工具，模型用 `loadTools` 发现其余工具；不改变工具策略与允许名单。

## 6. 必须完成的验收（待确认）

- **发现 ≠ 调用**：技能安装后必须做一次真实会话/Workspace 调用验收，才能声称「可用」。
- 技能内引用脚本的执行边界未验证，不得假定可在服务端任意执行 shell。
- CLI 同步：`ai-agent skillshub private diff / push --dry-run / pull --force --yes`（写操作先看差异；CLI 只管当前用户私有空间）。
