#!/usr/bin/env bash
# ai-agent-master 原生安装：通过产品 Skillshub API 上传 SKILL.md
# 凭据只从环境变量读取：AI_AGENT_BASE_URL / AI_AGENT_USER / AI_AGENT_PASSWORD
set -euo pipefail
BASE="${AI_AGENT_BASE_URL:-https://192.168.1.3:8060}"
USER="${AI_AGENT_USER:?需要 AI_AGENT_USER}"
PASS="${AI_AGENT_PASSWORD:?需要 AI_AGENT_PASSWORD}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONTENT_FILE="$SKILL_DIR/SKILL.md"
DEVICE_ID="$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo probe-$$)"
JAR="$(mktemp)"; trap 'rm -f "$JAR" /tmp/ai-agent-skill-login.json' EXIT

curl -ksS -c "$JAR" -H 'Content-Type: application/json' \
  --data-binary @<(python3 -c 'import json,sys;print(json.dumps({"userId":sys.argv[1],"password":sys.argv[2],"device":{"clientType":"browser","terminalId":sys.argv[3],"name":"Skill Installer","platform":"Linux","appVersion":""}}))' "$USER" "$PASS" "$DEVICE_ID") \
  "$BASE/api/auth/login" -o /dev/null

python3 - "$CONTENT_FILE" "$JAR" "$BASE" <<'PY'
import json,sys,urllib.request,http.cookiejar
content=open(sys.argv[1],encoding='utf-8').read()
jar=http.cookiejar.MozillaCookieJar(sys.argv[2]); jar.load(ignore_discard=True,ignore_expires=True)
opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=__import__('ssl')._create_unverified_context()),urllib.request.HTTPCookieProcessor(jar))
req=urllib.request.Request(sys.argv[3]+'/api/skillshub/private/upload',data=json.dumps({'content':content,'overwrite':True}).encode(),headers={'Content-Type':'application/json'},method='POST')
with opener.open(req,timeout=30) as r: print(r.read().decode()[:500])
PY
