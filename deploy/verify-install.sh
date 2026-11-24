#!/usr/bin/env bash
# 验证安装：读取技能内容并与本地 SKILL.md 比对，再做一次版本兼容检查
set -euo pipefail
BASE="${AI_AGENT_BASE_URL:-https://192.168.1.3:8060}"
USER="${AI_AGENT_USER:?需要 AI_AGENT_USER}"
PASS="${AI_AGENT_PASSWORD:?需要 AI_AGENT_PASSWORD}"
DEVICE_ID="$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo probe-$$)"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
JAR="$(mktemp)"; REMOTE="$(mktemp)"; trap 'rm -f "$JAR" "$REMOTE"' EXIT
curl -ksS -c "$JAR" -H 'Content-Type: application/json' \
  --data-binary @<(python3 -c 'import json,sys;print(json.dumps({"userId":sys.argv[1],"password":sys.argv[2],"device":{"clientType":"browser","terminalId":sys.argv[3],"name":"Skill Verifier","platform":"Linux","appVersion":""}}))' "$USER" "$PASS" "$DEVICE_ID") \
  "$BASE/api/auth/login" -o /dev/null
curl -ksS -b "$JAR" "$BASE/api/skillshub/private/ai-agent-master" > "$REMOTE"
python3 - "$REMOTE" "$SKILL_DIR/SKILL.md" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
c=r.get('content','')
local=open(sys.argv[2],encoding='utf-8').read()
print('found:',r.get('ok'),'name:',r.get('skillName'))
print('content matches local SKILL.md:',c==local)
sys.exit(0 if r.get('ok') and c==local else 1)
PY
curl -ksS -b "$JAR" "$BASE/api/health" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("health ok:",d.get("ok"),"model:",d.get("model"))'
