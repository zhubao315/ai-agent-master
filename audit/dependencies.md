# 依赖关系（运行时实测）

- **产品实例 → 模型服务**：默认 `glm-5.3-flash-local` → `http://192.168.1.3:18087/v1`（本机推理服务）；外部 DeepSeek 模型经 api.deepseek.com。
- **产品实例 → Sandbox 引擎**：通过 `ai-agent-sandbox-proxy` 访问独立 Docker socket；Workspace 使用 `ai-agent-dev-a-next-sandbox-net`。
- **产品实例 → Quse Gateway**：`http://quse-gateway:3456`（Sandbox Profile env `QUICKAI_GATEWAY_URL`）。
- **产品实例 → GDMP**：Sandbox Profile env `GDMP_BASE_URL=http://192.168.1.23:8090`（跨机依赖，GDMP 技能独立，不混入本技能）。
- **产品实例 → ONLYOFFICE**：双网改写（edge → docx-rewriter:3191 → ai-agent:3190），browserUrl 固定 `https://192.168.1.3:38061`，字体卷独立。
- **文档站**：Caddy 9090 → Hugo 1313；证书由 `site-certs-renew.service` 管理。
- **未发现**：独立向量数据库、Redis/MQ（产品侧）、K8s 工作负载（kubectl 仅有 default context，无产品负载）。
