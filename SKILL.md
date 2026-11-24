---
name: ai-agent-master
description: AI-Agent 平台（https://219.142.87.233:9090/ 文档站，产品实例 38060/8060）专属全生命周期运维技能。当任务涉及该平台的架构识别、资源与 GPU 评估、部署、模型与推理运维、Agent Runtime 与工具调用诊断、RAG 核查、性能优化、健康检查、故障排查、版本升级、回滚、备份恢复或安全审计时使用。所有结论必须基于真实运行环境证据，禁止编造服务、命令或版本；生产变更默认只读并需审批。
---

# ai-agent-master

## 1. 技能定位

AI-Agent 平台的专业运维技能：以真实运行环境为事实源，提供资源评估、部署、故障诊断、性能优化、升级回滚与安全审计的工作流指导。它不替代平台自带功能，也不假定未经验证的架构。

## 2. 适用范围

- 文档站：`https://219.142.87.233:9090/`（Hugo + oink，仅文档，**不是产品后台**）。
- 产品实例：`https://219.142.87.233:38060/`（公网）、`https://192.168.1.3:8060/`（内网）。
- 已验证平台版本：**Product 0.9.3**（主镜像 `20261121.1795273330`，ONLYOFFICE `9.4.0-session.16-r5-fonts3`）。
- 不适用场景：GDMP 无代码平台（请用 gdmp-master）；未取得证据的其他产品版本。

## 3. 触发条件

用户提到：ai-agent 的部署/升级/回滚/健康检查/沙箱/GPU/显存/模型/推理/Agent 工具调用/MCP/字体/双网改写/事件加固/资源评估/容量规划/故障诊断/备份恢复/版本兼容。

## 4. 工作原则

1. **证据优先**：先审计再判断；每个结论标注「已验证 / 代码推导 / 待确认 / 不适用」。
2. **只读默认**：生产环境默认只读；任何重启、切换、迁移、变更必须取得明确审批。
3. **统计先于样本**：先看汇总/计数/分布，再看单条日志。
4. **dry-run 优先**：高风险操作先预演，再执行，最后验收。
5. **不编造**：无源码仓库时不得声称完成源码级审计；无 Runtime 证据时不得声称 Skill 已被 AI 执行。
6. **最小权限**：不读取/输出密钥、Token、密码及个人数据；凭据只从环境变量读取。

## 5. 环境识别步骤

1. 读取 `manifest.yaml` 的 `compatibility.verified_version`，与实例实际版本比较（`/api/health`、容器镜像标签、`installed-state.json`）。
2. 版本不兼容 → 停止高风险操作，提示当前兼容版本与升级入口。
3. 按 `references/environment-baseline.md` 采集资源（GPU 用 `nvidia-smi`，容器用 docker CLI，服务用 systemctl）。
4. 按 `references/services-and-dependencies.md` 确认服务边界；发现新服务/新依赖时先更新参考文档再行动。

## 6. 工作流程

- **评估**：`references/resource-assessment.md` → 输出最小/推荐/生产规格与置信度。
- **部署**：`runbooks/install.md` → `runbooks/deploy.md` → `runbooks/health-check.md`。
- **模型/推理**：`references/model-management.md`、`references/inference-operations.md`、`runbooks/model-deploy.md`。
- **Agent/工具**：`references/agent-runtime.md`、`runbooks/incident-response.md`。
- **性能**：`references/performance-optimization.md`、`runbooks/performance-tuning.md`。
- **升级/回滚**：`references/upgrade-guide.md`、`references/rollback-guide.md`、`runbooks/upgrade.md`、`runbooks/rollback.md`。
- **安全/备份**：`references/security-guide.md`、`references/backup-restore.md`。

## 7. Reference 加载规则

入口文件只保留判断逻辑。只有任务确实需要时才读取对应 `references/*.md`；一次任务最多加载 2–3 份。涉及具体操作再加载 `runbooks/*.md`。所有 reference 必须标注证据状态；标注「待确认」的段落不得作为操作依据。

## 8. 安全约束

- 禁止浏览器直连服务器文件系统、禁止在文档/脚本中硬编码凭据、禁止绕过平台权限。
- 禁止未经备份执行不可逆迁移；数据库迁移与应用回滚分别制定方案。
- 平台「自定义工具管理」在本实例被事件加固禁用（`CUSTOM_TOOL_MANAGEMENT_DISABLED`），不得依赖该接口。
- 事件加固单元 `ai-agent-incident-containment-20261115.service` 处于 active，不要擅自停用。

## 9. 输出标准

结论包含：环境事实（含证据状态）、风险等级、操作前提、具体命令（来自 runbook）、验收标准、回滚方案、遗留的不确定性。资源与容量估算必须列明前提、假设与置信度。

## 10. 完成条件

任务完成需同时满足：证据已记录、操作有审批、验收已执行、回滚方案已给出、manifest 兼容性已校验；若任一条件不满足，明确报告「未完成/受阻」而非宣称成功。
