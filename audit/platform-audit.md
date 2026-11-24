# AI-Agent 平台审计（Phase 1）

> 审计时间：2026-11-24；审计人：OpenCode Agent；生产环境默认只读。
> 状态标记：**已验证**（实测/实读）、**代码推导**（由文档或配置推导）、**待确认**（需授权/证据）、**不适用**。

## 目标站点识别

| 项 | 结果 | 状态 |
|---|---|---|
| 任务书目标 `https://219.142.87.233:9090/` | **Hugo 文档站**，Caddy `:9090` → `127.0.0.1:1313`（`ai-agent-hugo.service`） | 已验证 |
| AI-Agent 产品 UI 实际入口 | `https://219.142.87.233:38060` → 容器内 edge `:8060`；内网 `https://192.168.1.3:8060` | 已验证 |
| 结论 | **9090 不是产品后台，是文档站**；技能安装/加载的实际目标必须是产品实例（38060/8060），不是 9090 | 已验证 |

## 源码仓库审计

| 项 | 结果 | 状态 |
|---|---|---|
| `/oc/ai-agent-site` | Git 仓库，remote `https://ghproxy.net/https://github.com/zhubao315/ai-agent.git`，分支 main，HEAD `c0100f4` | 已验证 |
| 远端可达性 | `git ls-remote` 成功，远端 main = `c0100f4…` | 已验证 |
| 仓库内容 | **仅 Hugo 文档站**（content/data/layouts/static），无产品后端源码、无 Dockerfile/Compose/Helm/CI 产品流水线 | 已验证 |
| 产品后端源码 | **未取得**。本机仅存产品运行实例与发布介质，无源码仓库 | 待确认/受阻 |

> 影响：任务书要求的「源码级架构审计、代码 Diff→Skill 更新、在产品仓库内加 `.github/workflows`」在当前仓库**无法按原文实施**。不得伪造源码结论；后续只能在文档站仓库内做「文档侧 Skill 发布流水线」，或等待取得真实产品源码仓库。

## 平台功能与版本（实测）

- 产品版本：**0.9.3**（主镜像 `ai-agent:20261121.1795273330-amd64`，源码 `3744b6aa…`）——容器内实际运行版本，已验证。
- 管理入口：`/pages/*` 系列页面（studio、workbench、admin-portal、models-admin、tools-admin、sandbox-admin、skills-hub、skills-editor、skillshub-portal 等），已通过 `docker exec` 列目录验证。
- 登录：管理员账号 `me` 会话 API `/api/auth/login` 实测 200；审计中未输出任何密码/Token。
- 四服务 + 侧车：`ai-agent-dev-a-next-{server,edge,onlyoffice,quse-gateway,docx-rewriter}`，全部 healthy/running（见 services.md）。
- ONLYOFFICE 已升级到 `9.4.0-session.16-r5-fonts3-amd64`（与 0.9.3 发布一致）。

## 审计结论

1. 目标站点 9090 是文档站，**不是**可安装 Skill 的产品后台；需用户确认安装目标。
2. 产品源码仓库缺失，代码级 Diff/CI 集成受阻，不能声称完成。
3. 产品实例运行 0.9.3，具备丰富管理 API（见 skill-runtime-audit.md），具备原生 Skill 能力。
