# 升级（0.9.2(.x) → 0.9.3，两步升级）

> 证据：`content/docs/deploy-ops/config/upgrade/_index.md` §零、`content/docs/deploy-ops/deploy/tools/_index.md`、`content/docs/deploy-ops/deploy/special/{fonts,https-dualnet}/_index.md`、`content/docs/deploy-ops/xinchuang/tencentos4-arm64-offline-install/_index.md`。升级为高风险变更：审批 + 维护窗口 + 全量备份 + 每步验收；数据库迁移与应用升级分开。

## 1 适用版本
- 目标 Product **0.9.3**：主镜像 `20261121.1795273330-<arch>`（源提交 `3744b6aa…`）；ONLYOFFICE `9.4.0-session.16-r5-fonts3`；Caddy `2.11.4-alpine`、Quse `1.0.24-20260911.1789148529`、平台基础 `20261109.standard.2`（20 项）均沿用。
- CLI 沿用 Image 0.5.52 / Deploy 0.6.20 / Software 0.8.0 / 客户端 0.2.42；数据库沿用 `021_async_invocation_actor`（**本次无新迁移、通常无需 SQLite 回退**）。
- 0.9.2.1 安全补丁与 Sandbox 修复 `733142e97` **已并入 0.9.3**，不再单独打补丁。
- 旧版本须先进入对应基线：0.9.1 → 0.9.2、0.9.0 → 0.9.1（020→021 迁移）、0.8.8 → 0.9.0 等，按升级手册历史路径分段执行。

## 2 操作环境
- 同宿主双引擎；操作在主引擎执行单服务镜像替换；两步之间各自保留验收与回退点。
- 项目名 / `--compose-file` / `--env-file` 的唯一权威来源是 `<AI_AGENT_DATA_ROOT>/installed-state.json` 的 `target`，按原顺序传齐全部文件，**不使用 `--fast`**。

## 3 风险等级
- **高**：会重建容器；双网定制的 `DOCX_SERVER_URL` 等覆盖键与 `apply` 校验冲突；字体列表缓存会丢；`/data` 已用 80%，备份空间需先确认（R5）。

## 4 前置条件
- 审批、维护窗口、活动任务结束；`ai-agent-deploy backup --full-backup --config "$INSTANCE_CONFIG"` 完成并校验 manifest。
- 介质按架构下载（amd64 产品 tar 3,693,957,120 B `6ff7cc8c…` / arm64 3,681,361,920 B `886a9cfa…`），`.tar.sha256` 与包内 `SHA256SUMS`（227 项）全部 OK。
- 记录当前主镜像、ONLYOFFICE 镜像、数据库版本、运行中任务、共用镜像的侧车、`installed-state.json` 的 `target`。
- **dry-run**：先在不承载业务的实例演练完整两步；TencentOS Server 4 离线介质仍停在 0.8.8 基线，须取 0.9.3 滚动介质，不能当作已到 0.9.3。

## 5 需要检查的信息
- `status --json`、`base inspect --deployment <ID> --json`、容器实际镜像标签。
- `installed-state.json` 的 `target.projectName` / `projectDirectory` / `composeFiles` / `envFiles`。
- 若启用双网改写 / 中文字体：确认覆盖键与同步脚本路径（`${AI_AGENT_DATA_ROOT}/rewriter/reapply-docx-dualnet.sh`、`${AI_AGENT_DATA_ROOT}/fonts/sync-onlyoffice-cjk-fonts.sh` 已在文档验证）。
- `${AI_AGENT_DATA_ROOT}/maintenance/post-deploy.sh`：用户给出的 `/data/ai-agent-next/maintenance/post-deploy.sh` 路径**待确认**，文档仅记载 `/data/ai-agent-dev-a/maintenance/post-deploy.sh`。

## 6 具体操作
1. 备份与记录 → 2. 取介质校验 → 3. **第一步**单服务更新 `ai-agent` 主镜像（传齐四份 Compose + 一份 ENV）→ 4. 验收主服务（健康、数据库版本、Sandbox 停止确认后台复核、审计在 HTTP 监听后恢复）→ 5. **第二步**同组 Compose/ENV 只替换 `onlyoffice` 到 fonts3，**保留数据卷与字体卷**（`ai-agent-<ID>-onlyoffice-{postgresql,rabbitmq,redis,fonts}` 不动）→ 6. 字体验收（18 名称 / 32 文件，含宋体标点）→ 7. 按需更新技能 ZIP → 8. 双网定制先移出覆盖键再 `apply`、恢复后重应用 → 9. 清理介质并登记台账。
- 两个服务**绝不放进同一次 `apply`**；各自用本次归档与操作号回退。

## 7 实际命令
```bash
DOCKER_CONTEXT=default ai-agent-deploy backup --full-backup --config "$INSTANCE_CONFIG"
python3 - "$INSTANCE_ROOT/installed-state.json" <<'PY'
import json,pathlib,shlex,sys
t=json.loads(pathlib.Path(sys.argv[1]).read_text())["target"]
print("--project-name",shlex.quote(t["projectName"]),"\\")
print("--project-directory",shlex.quote(t["projectDirectory"]),"\\")
for f in t["composeFiles"]: print("--compose-file",shlex.quote(f),"\\")
for f in t["envFiles"]: print("--env-file",shlex.quote(f),"\\")
PY
# 第一步：主镜像
DOCKER_CONTEXT=default ai-agent-image apply \
  --image "$DELIVERY/images/<arch>/ai-agent/20261121.1795273330-<arch>.tar" \
  --project-name <项目名> --project-directory <实例根> \
  --compose-file <原顺序全部 compose> --env-file <原 env> --service ai-agent --json
# 第二步：ONLYOFFICE fonts3（同一组 Compose/ENV，保留数据与字体卷）
DOCKER_CONTEXT=default ai-agent-image apply \
  --image "$DELIVERY/images/<arch>/onlyoffice/<fonts3 镜像 tar>" \
  --project-name <项目名> --project-directory <实例根> \
  --compose-file <原顺序全部 compose> --env-file <原 env> --service onlyoffice --json
DOCKER_CONTEXT=default ai-agent-deploy status --config "$INSTANCE_CONFIG" --json
```
`<fonts3 镜像 tar>` 实际文件名以包内 `images/<arch>/` 交付为准（待确认列表时勿手拼）。

## 8 预期结果
- 主服务健康、数据库仍为 `021_async_invocation_actor`；`status --json` 四服务就绪。
- ONLYOFFICE 为 fonts3；字体在编辑器内可选 **18 名称 / 32 文件**（含宋体标点）；如卷内缺字体才按 `update/onlyoffice.html` 重跑字体脚本。
- 双网实例：edge → docx-rewriter:3191 → ai-agent:3190 路由恢复，内外网入口 200/302；事件加固单元仍 active。

## 9 验收标准
- [ ] 两步各自验收通过；三探针、登录、模型实际发消息、Office 三格式编辑保存重开均通过。
- [ ] 原项目 / Agent / Workspace / 私有安装保留；`me` 密码未被修改；字体与双网（如启用）已重应用。
- [ ] 保留本次旧镜像归档与操作号，回退路径可执行；未完成项登记。

## 10 失败处理
| 现象 | 处置 |
|---|---|
| `ai-agent.env key is product-managed: DOCX_SERVER_URL` | 双网覆盖键冲突：备份后临时清空 env → apply → 恢复 → `reapply-docx-dualnet.sh` + 字体同步 |
| 字体列表未更新 / 中文字体消失 | 容器 recreate 丢失缓存，重跑 `${AI_AGENT_DATA_ROOT}/fonts/sync-onlyoffice-cjk-fonts.sh` |
| `finish the pending operation with the same image combination` | 用同一份介质/组合跑完 pending，不换参数 |
| 组合升级提示可能降级 | `apply --release` 不自动包含现场独立升级版本；先核对 from→to，单服务优先 |
| 升级中断 | 保留现场，修因后重跑同一命令；不删数据目录 |

## 11 回滚步骤
- 两服务**各自单独回退**：`ai-agent-image rollback --image <该服务旧镜像>` 配合同一组 Compose / ENV；主镜像回退不影响 ONLYOFFICE，反之亦然。
- **数据库与镜像分开**：0.9.2(.x) → 0.9.3 数据库未变，通常无需 SQLite 回退；只有回退到 0.9.1 及更早才须恢复升级前 SQLite 快照（走 `restore`，替换不合并）。
- 回退后重跑双网重应用与字体同步，并执行 health-check.md 全部探针；确认验收后再清理传输介质。

## 12 操作记录
| 时间 | 原版本→目标 | 备份目录 | 第一步结果 | 第二步结果 | 字体/双网验收 | 审批人 | 回退点 |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
