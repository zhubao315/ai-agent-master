# 安装与验证报告（2026-11-24）

## 环境
- 目标：产品实例 `https://192.168.1.3:8060`（公网 38060）；**不是** 9090 文档站。
- 平台版本：0.9.3，构建 `20261121.1795273330`，实测容器全部健康。
- 安装方式：原生 Skillshub API（`deploy/install.sh`，凭据仅环境变量）。

## 已验证（PASS）
| 项 | 证据 |
|---|---|
| 上传安装 | `POST /api/skillshub/private/upload` → 200，`skillName=ai-agent-master` |
| 内容一致 | `GET /api/skillshub/private/ai-agent-master` 的 content 与本地 `SKILL.md` 逐字节一致（verify-install.sh 输出 True） |
| 安装落点 | `/data/ai-agent-next/runtime/skillshub/users/me/myskills/ai-agent-master/SKILL.md` |
| 可发现 | `/api/skillshub/private` 列表 25 项，包含 `ai-agent-master` |
| 可被工作空间加载 | 创建临时工作空间 `verify-aiagentmaster-20261124` 并通过 `initialSkills` 安装；`/skills/status` 返回 `ai-agent-master`、`syncToPrivateState: synced`、`contentHash` 与私有库一致 |
| 清理 | 临时工作空间已删除；格式探针技能已删除；现有 23 个公共技能未改动 |

## 受阻（NOT VERIFIED）
- **Agent 实际调用**：在临时工作空间用 `POST /api/invoke` 发起真实任务，返回 HTTP 400「模型服务调用失败：无法连接到目标服务」。
- 根因：平台默认模型 `glm-5.3-flash-local` 的上游 `http://192.168.1.3:18087/v1` 连接被拒（实测 `curl` 000），而 `:808` 返回 401；这是模型服务环境问题，**不是 Skill 缺陷**。
- 处置：模型服务恢复后重跑 `/api/invoke` 并保留响应证据，再把 manifest 的 `validation.agent_invocation` 改为 verified。在此之前不得宣称「智能体已按技能完成实际任务」。

## 结论
技能已真实安装、可发现、可被工作空间加载；**AI 实际调用尚未验证**，原因已定位到模型上游。按任务书纪律，该项如实标记为受阻。
