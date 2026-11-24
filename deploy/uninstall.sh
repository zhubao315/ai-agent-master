#!/usr/bin/env bash
# 卸载 ai-agent-master（仅删除本技能，不触碰其它技能）
set -euo pipefail
BASE="${AI_AGENT_BASE_URL:-https://192.168.1.3:8060}"
USER="${AI_AGENT_USER:?需要 AI_AGENT_USER}"
PASS="${AI_AGENT_PASSWORD:?需要 AI_AGENT_PASSWORD}"
DEVICE_ID="$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo probe-$$)"
JAR="$(mktemp)"; trap 'rm -f "$JAR"' EXIT
curl -ksS -c "$JAR" -H 'Content-Type: application/json' \
  --data-binary @<(python3 -c 'import json,sys;print(json.dumps({"userId":sys.argv[1],"password":sys.argv[2],"device":{"clientType":"browser","terminalId":sys.argv[3],"name":"Skill Installer","platform":"Linux","appVersion":""}}))' "$USER" "$PASS" "$DEVICE_ID") \
  "$BASE/api/auth/login" -o /dev/null
curl -ksS -b "$JAR" -X DELETE "$BASE/api/skillshub/private/ai-agent-master" -w '\nHTTP %{http_code}\n'
