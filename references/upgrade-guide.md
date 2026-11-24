# 升级指南

> **证据状态**：已验证（现场 0.9.3 运行版本与五容器镜像，2026-11-24）｜代码推导（随包文档 `config/upgrade`、`manual-upgrade`、`architecture/system` 版本基线）｜待确认（现场 `installed-state.json` 的 compose/env 顺序、介质路径与当前活动任务）｜不适用（源码级 Diff→Skill 自动更新——无源码仓库）。
>
> 生产只读默认；升级需审批 + 维护窗口 + 全量备份。以下为导引，逐步命令以 runbook 与官方更新手册为准。

## 1. 当前状态与升级目标（已验证）

- 现场已运行 **0.9.3**（主镜像 `20261121.1795273330-amd64`，源码 `3744b6aa…`，ONLYOFFICE `9.4.0-session.16-r5-fonts3`）。**升级前必须先核对现场版本**，不要把本文件误当作「尚未升级」的指令。
- 0.9.3 相对 0.9.2 的变化（代码推导）：主程序刷新 + 纳入 0.9.2.1 安全补丁与 Sandbox 修复 `733142e97`；Sandbox 停止确认改为后台复核、不再阻塞新请求；审计恢复移到 HTTP 监听启动之后；ONLYOFFICE fonts3（字体 18 名称/32 文件，含宋体标点）；Windows 11 x64 新装介质；技能 `agent-builder.zip` / `skill-creator.zip` 更新。
- 数据库沿用 `021_async_invocation_actor`，**无新迁移**；平台基础沿用 `20261109.standard.2`（20 项）；CLI Image 0.5.52 / Deploy 0.6.20 / Software 0.8.0 / 客户端与共享 0.2.42 均不变。

## 2. 标准路径：0.9.2(.x) → 0.9.3（代码推导）

**分两步，不把两个服务放同一次 apply**（各自留验收与回退点）：

1. **备份并记录**：`ai-agent-deploy backup --full-backup --config "$INSTANCE_CONFIG"`；记录主镜像、ONLYOFFICE 镜像、数据库版本、活动任务、`installed-state.json` 的 `target`（composeFiles / env / project name）；等任务结束。
2. **取介质校验**：下载对应架构完整包与 `.sha256`，外层 `sha256sum -c` 后解包，包内 `sha256sum -c SHA256SUMS`（0.9.3 为 227 项）。
3. **第一步：`ai-agent-image apply` 只换主服务**（四份 Compose + 一份 ENV 按原顺序传齐，**不用 `--fast`**）：
   ```bash
   DOCKER_CONTEXT=default ai-agent-image apply \
     --image "$DELIVERY/images/<arch>/ai-agent/20261121.1795273330-<arch>.tar" \
     --project-name <项目名> --project-directory <实例根> \
     --compose-file <原顺序全部 compose> --env-file <原 env> --service ai-agent --json
   ```
4. **验收主服务**：核对镜像/健康/数据库版本；确认 Sandbox 停止确认后台复核、审计启动后恢复。
5. **第二步：单独换 ONLYOFFICE**（同一组 Compose/ENV，只替换 `onlyoffice` 服务，**保留数据与字体卷**）：字体校验 18 名称 / 32 文件；字体脚本只在缺字体时按 `update/onlyoffice.html` 重跑。
6. **按需更新技能**：停主服务后导入 `agent-builder.zip` / `skill-creator.zip`；工具 ZIP 与共享软件目录不变。
7. **回退**：两服务各自单独回退，见 `rollback-guide.md`。

## 3. 关键纪律（代码推导）

- 项目名 / Compose / ENV 必须从 `<DATA_ROOT>/installed-state.json` 的 `target` 取，**不要凭印象拼**；`--compose-file` 按原顺序传全部，漏一份启动前配置比对会拒绝。
- 停服务用 `docker compose ... stop`（保留容器），**不要 `down -v`**。
- `ai-agent-deploy apply --release` 用完整 release 组合，**不会自动包含现场独立升级过的版本** → 有现场独立升级时可能误降级，慎用。
- 旧 MCP ZIP 自动退出、原生 MCP 配置独立管理；`webServer → publishUrl` 改名须与 ZIP/Agent 包一起迁移。
- 顺序：先更新镜像，再更新 ZIP（反了会被镜像覆盖）→ 工具管理确认加载 → 改参数 → 测试 Workspace 验证。

## 4. 其他历史路径（代码推导，仅在现场版本落后时使用）

0.9.1→0.9.2（含 020→021 之前的基线）、0.9.0→0.9.1（020→021 迁移）、0.8.8→0.9.0、0.8.6/0.8.7→0.8.8 等，见随包 `config/upgrade` 文档，按序逐级进入基线，**不跳级**。0.2.x/旧布局迁移走 `manual-upgrade`（无自动一键迁移）。

## 5. 不可完成项（已验证）

无产品源码仓库 → 任务书中的「源码级 Diff → Skill 更新」「在产品仓库加 CI」在当前仓库无法按原文实施（风险 R2），如实报告受阻，不在 docs 仓库伪造产品流水线。
