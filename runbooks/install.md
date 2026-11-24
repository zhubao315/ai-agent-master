# 安装技能（Skillshub 原生 SKILL.md）

> 证据：`audit/skill-runtime-audit.md`、`audit/platform-audit.md`、`README.md`、`content/docs/user-guide/features/tools/_index.md`。生产默认只读，安装属写入操作，须审批后在测试环境往返验证通过再上生产。

## 1 适用版本
- Product **0.9.3**（主镜像 `ai-agent:20261121.1795273330-amd64`）；平台原生 Skillshub 支持标准 Agent Skills 的 `SKILL.md`（含 `name` + `description` YAML frontmatter）。
- 已验证：`POST /api/skillshub/private/upload`（JSON `content` 或 multipart ZIP）往返成功；无 frontmatter 的纯文本被拒（400）。

## 2 操作环境
- 目标必须是**产品实例**：公网 `https://219.142.87.233:38060` / 内网 `https://192.168.1.3:8060`。
- `9090` 是 Hugo 文档站，**不是**安装目标（R1）；不得把技能装到文档站。
- 技能包内 `deploy/install.sh`、`verify-install.sh`、`uninstall.sh`；凭据仅从 `AI_AGENT_BASE_URL` / `AI_AGENT_USER` / `AI_AGENT_PASSWORD` 环境变量读取。

## 3 风险等级
- **中**：向产品实例写入私有技能；不触碰数据库迁移，不替代平台自带功能。
- 实例处于事件加固：`ai-agent-incident-containment-20261115.service` active，禁止停用；`CUSTOM_TOOL_MANAGEMENT_DISABLED` 使自定义工具管理接口返回 403，安装流程不得依赖该接口（R3/R4）。

## 4 前置条件
- 已取得变更审批与维护窗口；`/data` 已用约 80%，先确认余量（R5）。
- 目标版本与 manifest `compatibility.verified_version` 一致；先在测试环境做上传→读取→删除往返（R6）。
- 凭据不写入任何文件、日志或聊天记录；Token 的获取方式**待确认**（审计中登录 API 返回 200 但未输出 Token 格式）。

## 5 需要检查的信息
- `/api/health` 返回的实例版本与 profile；现有 23 个公共技能清单（`/api/skillshub/public`）。
- 待装技能的 `skillName` 是否唯一；`SKILL.md` frontmatter 是否含 `name` / `description`。
- 安装落点（实测）：`/data/ai-agent-next/runtime/skillshub/users/me/myskills/<skillName>`。

## 6 具体操作
1. 测试环境先做无损往返：JSON `{"content":"<SKILL.md 全文>","overwrite":true}` 上传 → `GET /api/skillshub/private/{skillName}` 逐字节比对 → `DELETE` 清理（历史探针 `format-probe-20261124` 已删除）。
2. 生产安装优先用技能自带脚本（脚本内部处理鉴权），再跑验证脚本。
3. 若手工走 API：以 multipart ZIP 或 JSON `content` 调用 `POST /api/skillshub/private/upload`；鉴权头写法**待确认**，需在测试环境验证后补充。
4. 安装后必须做一次**真实调用**验收——发现技能 ≠ Agent 会调用（审计标明「仍需验证」）；调用方式**需在测试环境验证后补充**。

## 7 实际命令
```bash
export AI_AGENT_BASE_URL=https://192.168.1.3:8060   # 或 38060；不是 9090
export AI_AGENT_USER=me
export AI_AGENT_PASSWORD='<仅从受控环境注入，不落盘>'

./deploy/install.sh
./deploy/verify-install.sh
```
API 形态（仅记录已验证端点，鉴权占位）：
```bash
# POST /api/skillshub/private/upload
#   JSON: {"content":"<SKILL.md 全文>","overwrite":true}
#   or multipart ZIP；$AUTH_HEADER 获取方式 待确认
curl -fsS -X POST "$AI_AGENT_BASE_URL/api/skillshub/private/upload" \
  -H "$AUTH_HEADER" -H 'Content-Type: application/json' \
  -d "{\"content\":\"<SKILL.md 全文>\",\"overwrite\":true}"          # 待确认
curl -fsS "$AI_AGENT_BASE_URL/api/skillshub/private/<skillName>" -H "$AUTH_HEADER"
```

## 8 预期结果
- 上传返回 `200 ok`；`GET` 返回 `content` 且与上传的 `SKILL.md` 逐字节一致。
- 私有技能出现在 `skills-hub` / `skills-editor` / `skillshub-portal` 页面；23 个公共技能数量不变。
- 无凭据、无密码写入日志或文档；未触发 403 `CUSTOM_TOOL_MANAGEMENT_DISABLED`。

## 9 验收标准
- [ ] `verify-install.sh` 通过；私有技能可读、内容一致。
- [ ] 在授权环境完成一次真实会话调用（当前为遗留不确定性，未做不得宣称「已可调用」）。
- [ ] 操作前后 `/api/skillshub/public` 计数一致；事件加固单元仍 active。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| 400「请提供SKILL.md frontmatter」 | 补 `name` + `description` YAML frontmatter，重新上传 |
| 403 `CUSTOM_TOOL_MANAGEMENT_DISABLED` | 属实例级安全策略，不重试保存、不改账号权限，按事件加固流程上报 |
| 装到 9090 或 404 | 改指产品实例 38060/8060 |
| 安装失败且状态有 `pending` | 用同一份介质/参数重跑，不删数据目录（安装纪律见部署手册） |

## 11 回滚步骤
- 单个技能：`DELETE /api/skillshub/private/{skillName}` → 200；或 `./deploy/uninstall.sh`。
- 只删除本次新增的私有技能，不触碰 23 个公共技能；回滚后复查公共技能计数与页面可用。

## 12 操作记录
| 时间 | 目标实例 | skillName | 审批人 | 上传返回 | 读取比对 | 真实调用 | 回滚点 |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
