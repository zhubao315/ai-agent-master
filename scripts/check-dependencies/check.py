#!/usr/bin/env python3
"""机械检查依赖与版本漂移（只读；不输出密钥）。"""
import json,subprocess,os
def run(cmd):
    try: return subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT,text=True,timeout=30).strip()
    except Exception as e: return ""
state="/data/ai-agent-next/installed-state.json"
d={"installed_state":None,"images":[],"checked_at":__import__('datetime').datetime.now().astimezone().isoformat(timespec="seconds")}
if os.path.exists(state):
    try:
        j=json.load(open(state)); d["installed_state"]={"productVersion":j.get("productVersion"),"pending":j.get("pending")}
    except Exception: pass
d["images"]=run("docker ps --filter name=ai-agent-dev-a-next --format '{{.Names}}: {{.Image}}' 2>/dev/null").splitlines()
d["health_endpoint"]="https://192.168.1.3:8060/api/health (需会话/网络策略验证，本脚本不携带凭据)"
print(json.dumps(d,ensure_ascii=False,indent=2))
