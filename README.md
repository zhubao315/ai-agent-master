# ai-agent-master

<p align="center">
  <strong>AI-Agent 平台全生命周期运维技能</strong><br>
  真实审计 · 资源/GPU 评估 · 部署与升级回滚 · 故障诊断 · 原生 Skillshub 安装
</p>

<p align="center">
  <img alt="Skill" src="https://img.shields.io/badge/skill-ai--agent--master%20v1.0.0-7c3aed?style=flat-square">
  <img alt="Platform" src="https://img.shields.io/badge/platform-AI--Agent%200.9.3-2563eb?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-6b7280?style=flat-square">
</p>

## 一条命令安装

```bash
npm install -g github:zhubao315/ai-agent-master#skill-v1.0.0
ai-agent-master                      # 安装/升级到 ~/.config/opencode/skills
ai-agent-master --check-only         # 只校验
ai-agent-master --uninstall          # 卸载
```

免安装运行：`npx github:zhubao315/ai-agent-master#skill-v1.0.0`

提示词安装：

> 请从 GitHub 仓库 `zhubao315/ai-agent-master` 的 `skill-v1.0.0` 标签安装 `ai-agent-master` 技能到本机 OpenCode skills 目录，运行结构校验，并报告安装位置与验证结果。

## 能力

| 领域 | 内容 |
|---|---|
| 审计 | 8 份真实环境审计报告（平台/架构/服务/资源/依赖/风险/Skill Runtime） |
| 架构与资源 | 双 Docker 引擎、四服务、128 CPU / 499GiB / 7×RTX4090 基线、容量估算与置信度 |
| 模型与 Agent | 模型接入/加载失败切换、推理监控、Agent Runtime、工具调用/MCP、RAG 核查 |
| 运维 | 16 references + 10 runbooks（12 节结构）：部署、健康检查、模型部署、GPU 诊断、事件响应、性能调优、升级、回滚 |
| 自动化 | 只读机械脚本、结构/场景/兼容/安全测试、原生 Skillshub 安装脚本 |

## 真实验证状态

- ✅ 原生 Skillshub 上传成功、读回内容与本地 `SKILL.md` 逐字节一致、可发现、临时工作空间加载通过（临时空间已清理）。
- ⚠️ Agent 实际调用未通过：`/api/invoke` 返回 HTTP 400，根因是模型上游 `192.168.1.3:18087` 不可达（非 Skill 缺陷）；恢复后需复验。
- ⚠️ 9090 是文档站，产品实例在 38060/8060；仓库为独立技能仓库，不冒充产品源码仓库。

详见 `install-verification.md` 与 `manifest.yaml` 的 validation 段。

## 目录

```
SKILL.md / manifest.yaml / VERSION / CHANGELOG.md / README.md
audit/       8 份审计报告
references/  16 篇专业参考
runbooks/    10 个标准操作流程
scripts/     资源/服务/依赖采集 + 结构校验
tests/       结构/场景/兼容/安全
deploy/      install.sh / uninstall.sh / verify-install.sh
bin/         npm one-command installer
dist/        发布产物 + SHA256SUMS
```
