# 回退（应用镜像回退与数据库恢复分离）

> 证据：`content/docs/deploy-ops/deploy/tools/_index.md` §升级指南/单组件、`content/docs/deploy-ops/config/upgrade/_index.md` §零、`content/docs/deploy-ops/deploy/main/_index.md` §3.3、`content/docs/deploy-ops/deploy/special/{fonts,https-dualnet}/_index.md`。回退为高风险变更：审批 + 先备份 + dry-run 预演；**镜像回退不恢复数据库**。

## 1 适用版本
- 由 0.9.3 回退到 0.9.2(.x)：主镜像 `20261121.1795273330-<arch>` → 上一版主镜像（0.9.2 `20261119.1795072437`；0.9.2.1 补丁 `20261119.1795087705` 已被 0.9.3 纳入，不单独回退补丁）。
- ONLYOFFICE `9.4.0-session.16-r5-fonts3` → 上一版 `9.4.0-session.16-r5`（如现场需要）。
- 数据库：0.9.2(.x)↔0.9.3 均为 `021_async_invocation_actor`，**无新迁移**；回退到 0.9.1 及更早需同时恢复升级前 SQLite 快照（历史 0.9.1 曾 020→021、0.8.8 曾 019→020）。

## 2 操作环境
- 主引擎 `default`；`rollback` 与 `apply` 共用参数集：`--image` 为回退目标镜像，`--service` 选服务（`ai-agent` / `onlyoffice` / `edge` / `quse-gateway`）。
- 项目名、全部 `--compose-file`（四份）与 `--env-file` 以 `installed-state.json` 的 `target` 为准，保持原顺序；**不使用 `--fast`**。

## 3 风险等级
- **高**：回退会重建容器；只回镜像不回数据会造成状态错配；双网 / 字体 / 工具 / 技能各有独立回退面；`/data` 80% 水位影响备份与恢复空间（R5）。

## 4 前置条件
- 明确回退触发条件与审批；已保留本次升级的**旧镜像归档、操作号、配置文件备份**，且回退目标支持 `/run/ai-agent/engine-id` 只读挂载。
- 回退前再做一次 `backup --full-backup`（如空间允许），确认 manifest；活动任务结束。
- **dry-run** 在测试实例演练参数集；生产默认只读，未经审批不得执行。

## 5 需要检查的信息
- 当前镜像标签与各服务回退目标标签；`status --json` 的 `state.target`（composeFiles / env / projectName）。
- 备份目录与 `--image-root`（备份记录对应的服务镜像）；Sandbox 引擎中**完全相同**的平台基础（0.9.3 沿用 `20261109.standard.2`）。
- 字体卷 `ai-agent-<ID>-onlyoffice-fonts` 与双网 `rewriter/reapply-docx-dualnet.sh`（均已在文档验证）；用户给出的 `/data/ai-agent-next/maintenance/post-deploy.sh` **待确认**。

## 6 具体操作
1. 定界：确认是应用镜像问题、数据问题还是配置/字体/双网问题，分别制定回退项。
2. 主镜像回退：`ai-agent-image rollback --image <旧镜像> --service ai-agent`，参数与原 apply 一致。
3. ONLYOFFICE 回退（如需）：**单独一次** `rollback --service onlyoffice`，保留数据与字体卷；回退后重跑字体同步脚本，字体校验回到相应版本（0.9.3 fonts3 为 18 名称 / 32 文件）。
4. 数据回退（**仅当需要**）：停止写入，走 `ai-agent-deploy restore <备份目录> --image-root <镜像目录> --config "$INSTANCE_CONFIG"`（**替换不合并**），与镜像回退分开记录。
5. 双网实例：回退/重建后重跑 `reapply-docx-dualnet.sh`，再重同步中文字体；有 path 单元触发的 post-deploy 脚本时确认其实际路径后再决定是否执行。
6. 全量验收；确认稳定后再清理临时介质。

## 7 实际命令
```bash
DOCKER_CONTEXT=default ai-agent-deploy status --config "$INSTANCE_CONFIG" --json
DOCKER_CONTEXT=default ai-agent-deploy backup --full-backup --config "$INSTANCE_CONFIG"
# 主镜像回退（参数集取自 installed-state.json 的 target）
DOCKER_CONTEXT=default ai-agent-image rollback \
  --image /data/handoffs/<旧主镜像归档>/20261119.1795072437-<arch>.tar \
  --project-name <项目名> --project-directory <实例根> \
  --compose-file <原顺序全部 compose> --env-file <原 env> --service ai-agent --json
# ONLYOFFICE 单独回退（如需）
DOCKER_CONTEXT=default ai-agent-image rollback \
  --image /data/handoffs/<旧 ONLYOFFICE 归档>/<旧镜像 tar> \
  --project-name <项目名> --project-directory <实例根> \
  --compose-file <原顺序全部 compose> --env-file <原 env> --service onlyoffice --json
# 数据回退（仅需要时，独立方案）
DOCKER_CONTEXT=default ai-agent-deploy restore /absolute/backup-directory \
  --image-root /absolute/saved-images --config "$INSTANCE_CONFIG"
${AI_AGENT_DATA_ROOT}/rewriter/reapply-docx-dualnet.sh
${AI_AGENT_DATA_ROOT}/fonts/sync-onlyoffice-cjk-fonts.sh
```
`<旧镜像 tar>` 精确文件名**待确认**，以保留的归档与操作记录为准，不凭印象拼。

## 8 预期结果
- 各服务回到目标镜像且健康；`status --json` 无 pending；三探针 200。
- 若执行了 `restore`：数据与备份清单一致；项目 / Agent / Workspace / 私有安装按备份时点恢复（后续写入会被舍弃，须提前告知）。
- 字体、双网路由恢复；事件加固单元仍 active。

## 9 验收标准
- [ ] 镜像版本、数据库版本分别核对并记录；未把「镜像回退」当作「数据回退」。
- [ ] 真实业务冒烟（登录、发消息、Office 编辑保存、Workspace / Preview）通过。
- [ ] 审批、备份、dry-run、回滚点齐全；未完成项登记。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| 镜像回退后业务仍异常 | 可能是数据/配置问题；不要连续换镜像，先取证（incident-response.md） |
| 回退到 0.9.1 及更早但未恢复 SQLite | 按备份通道恢复升级前快照；这会舍弃快照后写入，须审批 |
| 字体消失 / 编辑页 API 加载失败 | 重跑字体同步脚本与 `reapply-docx-dualnet.sh` |
| 缺少旧镜像归档或不匹配平台基础 | 停止回退，上报；`restore` 要求备份记录里的镜像与 Sandbox 中完全相同的平台基础 |
| `down -v` 误删卷 | **禁止**该操作；改从全量备份走 `restore` |

## 11 回滚步骤
- 回退失败需重做升级时，使用本次保留的 0.9.3 镜像归档与原参数集按 upgrade.md 两步重新 apply。
- 若已执行 `restore`，再次 `restore` 到升级后备份点；每次恢复都重新校验 manifest，不做手工 `tar` 覆盖。
- 复跑 health-check.md 全部探针与业务冒烟；记录最终状态与遗留不确定性。

## 12 操作记录
| 时间 | 回退范围（镜像/数据/字体/双网） | 目标版本 | 审批人 | 备份目录 | 验收结论 | 遗留项 |
|---|---|---|---|---|---|---|
| | | | | | | |
