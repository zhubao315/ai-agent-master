# Skill Runtime 审计（决定性结论）

## 原生能力（已验证）

- 产品有 **Skillshub** 模块：23 个公共技能（`/api/skillshub/public` 实测），管理端 `/api/admin/skills`（当前 items 为空），UI 页面 `skills-hub` / `skills-editor` / `skillshub-portal`。
- 存储位置：`/data/ai-agent-next/runtime/public-skills/records/*.json`（23 条记录）、`public-skill-repos/`（23 个目录，实测为空）、`admin-resources/skills/`（空）。
- 管理 API（来自 0.9.3 随包 OpenAPI，已验证存在）：
  - `POST /api/skillshub/private/upload`（multipart ZIP 或 JSON `content`）
  - `POST /api/admin/skills`、`PUT/DELETE /api/admin/skills/{skillName}`
  - `POST /api/runtime-workspaces/{id}/skills/install|upload`
  - `GET/PUT /api/skillshub/private/{skillName}`、`POST .../publish`
- 技能记录字段：`id/name/title/description/ownerUserId/source/contentHash/createdAt/updatedAt`（公共详情接口不返回正文）。

## 关键结论（已通过真实往返验证，2026-11-24）

- 在容器 `/app/src` 中 grep `SKILL.md` 的 JS/MJS 源码无命中；但**这不影响平台通过 API 层解析 SKILL.md frontmatter**。
- **实测往返**：`POST /api/skillshub/private/upload`（JSON `{"content":"<SKILL.md 全文>","overwrite":true}`）→ `200 ok`；`GET /api/skillshub/private/{skillName}` 返回 `content` 且与上传内容逐字节一致；`DELETE /api/skillshub/private/{skillName}` → 200。临时技能 `format-probe-20261124` 已删除，未改动现有 23 个公共技能。
- 无 frontmatter 的纯文本被拒（400「请提供SKILL.md frontmatter」）；带 `name` + `description` YAML frontmatter 的标准 SKILL.md 被接受。
- **结论：平台原生支持标准 Agent Skills 格式的 SKILL.md**（解析在 API/服务端完成），可走原生安装路径，无需适配层。
- 安装位置（实测返回）：`/data/ai-agent-next/runtime/skillshub/users/me/myskills/<skillName>`。

## 仍需验证

- Agent 是否能在会话/Workspace 中**实际调用**已安装技能（发现 ≠ 调用）——安装后必须做一次真实调用验收。
- 技能内引用脚本的执行边界（平台工具权限），不得假定可在服务端任意执行 shell。
