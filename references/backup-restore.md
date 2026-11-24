# 备份与恢复

> **证据状态**：已验证（现场主库路径与 `/data` 水位实测）｜代码推导（随包文档 `ops/daily`、`why-dual-engine`、`manual-upgrade`、`config/upgrade`）｜待确认（现场备份目录实际内容与 manifest、备份任务是否配置）｜不适用（Workspace 可写层与 Agent 镜像的备份——改用导出包）。
>
> 生产只读默认；恢复/迁移需审批。禁止手工 `tar` 数据根目录代替正式备份通道。

## 1. 核心原则（代码推导）

- 用部署工具正式通道：`ai-agent-deploy backup` / `restore`，**不要手工 tar 数据根**。
- 全量档 `--full-backup` = 配置 + 项目 + 数据库 + 工具 + 服务数据；**Workspace 可写层与 Agent Docker 镜像不进备份**，改用 Agent 导出包（`agent.json` / `workspace.zip` / `environment.delta.tar`）。
- `restore` 是**全量替换、不合并**；演练在无业务写入的实例进行。
- 备份目录与交付包**分机存放**；保留策略：最近 7 天。

## 2. 备份类型与命令（代码推导）

```bash
# 日常：只备份数据库与配置，不中断服务
DOCKER_CONTEXT=default ai-agent-deploy backup --config "$INSTANCE_CONFIG"

# 全量：配置+项目+数据库+工具+服务数据；会暂停服务与运行中的 Workspace，结束自动恢复
DOCKER_CONTEXT=default ai-agent-deploy backup --full-backup --config "$INSTANCE_CONFIG"

# 恢复（替换不合并）
DOCKER_CONTEXT=default ai-agent-deploy restore /data/ai-agent/backups/<备份目录> \
  --image-root /data/ai-agent/backups/<备份目录> --config "$INSTANCE_CONFIG"
```

- 备份路径：`${AI_AGENT_DATA_ROOT}/backups/<产品版本>-<UTC 时间戳>/`，附 `manifest.json`（逐文件 sha256）。
- `apply` 默认自动备份 SQLite；`--full-backup` 保存实例数据；`--no-backup` 明确跳过（三者互斥）。
- 升级前必做一次 `--full-backup` 并记录输出路径（见 `upgrade-guide.md`）。

## 3. 现场数据对象（已验证路径 / 代码推导归属）

| 对象 | 位置 / 方式 |
|---|---|
| AI-Agent 主库 SQLite | `/data/ai-agent-next/runtime/db/ai-agent.sqlite`（已验证）；容器卷 `<ID>-sqlite-data` |
| 工具扩展库 | `tool-extensions.sqlite`（随运行时） |
| 技能 | `/data/ai-agent-next/runtime/public-skills/records/*.json`、`runtime/skillshub/users/.../myskills/`（已验证） |
| ONLYOFFICE | 卷 `postgresql` / `rabbitmq` / `redis` / `fonts`（保留卷不重建） |
| Quse / 导出物 / Caddy | quse-gateway-data、exports、caddy-data 卷或目录 |
| 平台基础 | `platform-base-20261109.standard.2` 归档单独保留 |

## 4. 迁移场景的停服一致副本（代码推导）

- 迁移前**停写**：先停旧实例再停新实例；SQLite 用停服一致副本，含 WAL 时一并处理。
- 不要只复制一个 `ai-agent.sqlite` 就判定成功；旧绝对路径、容器 ID、profile schema、工作区记录字段需按 `manual-upgrade` 做三处适配。
- `Docker commit` **不保存**项目目录与 Volume。

## 5. 风险与纪律

- R5：`/data` 已用 80%（343G 可用），全量备份/解包前必须查余量；备份目录与交付包分机存放。
- GPUStack 另有一套：状态与内嵌 Postgres 在 `gpustack-data` 卷，权重目录（随包文档 `/nfs/data/models`）独立备份（见 `gpu-management.md`）。
- 数据库无冗余，故障恢复依赖备份：随包文档给出 RTO 30 分钟以内、实测 18 分钟（代码推导/文档实测，非本机演练）。
- 恢复演练前确认无业务写入；恢复后核对项目、配置、模型、Workspace、字体与工具。
