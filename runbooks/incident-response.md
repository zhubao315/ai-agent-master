# 事件响应与故障排查

> 证据：`audit/risk-register.md` R3/R4、`audit/services.md`、`content/docs/deploy-ops/deploy/main/_index.md` §6.2、`content/docs/deploy-ops/ops/{daily,troubleshooting}/_index.md`、`content/docs/user-guide/features/tools/_index.md`。生产默认只读；变更须审批、先 dry-run、备份后执行。

## 1 适用版本
- Product 0.9.3；事件加固单元 `ai-agent-incident-containment-20261115.service` 处于 **active/exited**，是现场安全边界，**不得擅自停用**。
- 加固影响：管理端 `GET /api/admin/tools/extensions` 与 `GET /api/admin/tools/mcp/settings` 返回 403、`errorCode: CUSTOM_TOOL_MANAGEMENT_DISABLED`；Workspace 内已启用工具的调用不受影响。

## 2 操作环境
- 产品入口 38060/8060；文档站 9090（不要混用）。主引擎 + Sandbox 引擎；日志为 stdout 结构化单行 JSON。
- 追踪字段：`requestId`（响应头 `X-Request-Id`）、`invocationId`、`sessionId`、`turnId`；`durationMs` 为出站调用耗时（SLA 数据源）。

## 3 风险等级
- **高（事件期间）**：涉及安全边界、自定义工具管理禁用、跨机依赖（模型 / GDMP / ONLYOFFICE 双网）；只读取证优先，任何恢复动作需审批。

## 4 前置条件
- 已确认事件窗口、影响面与上报路径；已记录当前 `status --json`、容器 ID、探针结果作为现场。
- 不要在 403 页面上反复重试保存；不要改账号/License 权限去“绕过”加固。
- 需要恢复操作时先备份（日常 `backup` 不中断；全量 `backup --full-backup` 会暂停服务与 Workspace）。

## 5 需要检查的信息
- 用户可感知症状：登录、会话/智能体调用、Office 编辑保存、Workspace、Preview、模型输出。
- 平台状态：phase / pending / sandboxError；5 容器 healthy；License active（审计时到期 2026-11-28）。
- 依赖边界：模型服务（当前链路待确认，见 model-deploy.md）、Quse `http://quse-gateway:3456`、Sandbox socket、ONLYOFFICE 双网（edge → docx-rewriter:3191 → ai-agent:3190）、GDMP `http://192.168.1.23:8090`（跨机，独立）。
- 日志按级别/组件/事件/outcome 汇总后，再按四级 ID 串联单条链路。

## 6 具体操作
1. **证据固化**（只读）：保存状态、探针、资源、日志片段；先统计错误分布，再取样本。
2. **范围判定**：区分平台侧、模型侧、Sandbox/Workspace 侧、文档侧、跨机依赖侧；用探针逐层缩小（见 health-check.md / gpu-diagnosis.md）。
3. **对照已知边界**：403 `CUSTOM_TOOL_MANAGEMENT_DISABLED`、加固单元 active、`/data` 80% 水位、GPU 高占用——这些是已知事实，不作为根因臆测。
4. **缓解**：需要重启走 restart.md；需要模型切换走 model-deploy.md；不在事件期间做版本升级。
5. **升级上报**：无法在只读范围内定位，或需要停用/绕过加固时，立即上报，不自行处置。

## 7 实际命令
```bash
DOCKER_CONTEXT=default ai-agent-deploy status --config "$INSTANCE_CONFIG" --json
systemctl is-active ai-agent-incident-containment-20261115.service
systemctl is-active docker-sandbox.service containerd-sandbox.service ai-agent-sandbox-proxy.service
docker --context default ps --format '{{.Names}} {{.Status}}'
docker --context ai-agent-sandbox ps -a --format '{{.Names}} {{.Status}}'
curl -kfsS https://192.168.1.3:8060/api/health
curl -kfsS https://192.168.1.3:8062/health
curl -kfsS https://192.168.1.3:8061/healthcheck
df -h /data /data/docker-sandbox
ss -tlnp | grep -E ':(8060|8061|8062|8063)\b'
docker logs --tail 100 ai-agent-dev-a-next-server
# 按 requestId 串联（X-Request-Id 来自响应头）：
# docker logs ai-agent-dev-a-next-server 2>&1 | grep '<requestId>'     # 不输出到外部系统
```

## 8 预期结果
- 现场证据可复核：状态、探针、单元状态、容器清单、错误分布与追踪 ID 齐全。
- 故障被定位到某一层（平台 / 模型 / Sandbox / 文档 / 跨机），或明确记录「受阻、需上报」。
- 事件加固单元保持 active；无密码 / Token / 个人数据外泄。

## 9 验收标准
- [ ] 症状、时间线、证据状态（已验证 / 待确认）与影响面记录完整。
- [ ] 每个缓解动作都有审批、dry-run 结论、回滚点；业务恢复经真实调用验证（不是仅看容器 healthy）。
- [ ] 未完成项显式标注，不宣称「已彻底解决」。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| 403 `CUSTOM_TOOL_MANAGEMENT_DISABLED` | 实例级安全策略，非权限/License 问题；停止重试，按加固流程上报 |
| 编辑页「加载 ONLYOFFICE API 失败」 | 双网定制未重应用 → `${AI_AGENT_DATA_ROOT}/rewriter/reapply-docx-dualnet.sh`（路径已验证），并重同步中文字体 |
| 保存/下载失败但能打开 | ONLYOFFICE 回调被 SSRF 拦截，检查 `ALLOW_PRIVATE_IP_ADDRESS` / `ALLOW_META_IP_ADDRESS`（见 FAQ） |
| 「系统软件查询 Sandbox 不可用」 | 平台基础未装或装错引擎，见 deploy.md / install-troubleshooting |
| `target Image is unavailable after archive load` | overlay2 与 containerd 的 IMAGE ID 差异，见 FAQ 部署安装项 |
| Sandbox 反复重启 | `stop` → `reset-failed` → 修网桥 → `start`（见 restart.md） |

## 11 回滚步骤
- 任何缓解变更（重启、模型配置、单服务镜像）先留旧值与备份，按对应 runbook 回滚；`ai-agent-image rollback` 只回镜像。
- **数据库迁移与应用回滚分别制定方案**：需要数据回退时用 `ai-agent-deploy restore <备份目录> --image-root <镜像目录>`（替换不合并），不得与镜像回退混为一谈。
- 回滚后复跑 health-check.md 全部探针与业务冒烟。

## 12 操作记录
| 时间 | 症状 | 影响面 | 追踪 ID | 定位层级 | 缓解动作/审批人 | 业务恢复验证 |
|---|---|---|---|---|---|---|
| | | | | | | |
