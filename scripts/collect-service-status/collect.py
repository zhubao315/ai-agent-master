#!/usr/bin/env python3
"""机械采集服务状态（只读）。"""
import json,subprocess,datetime
def run(cmd):
    try: return subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT,text=True,timeout=30).strip()
    except Exception as e: return f"unavailable: {e}"
d={"collected_at":datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
d["containers"]=run("docker ps --filter name=ai-agent-dev-a-next --format '{{.Names}}\\t{{.Image}}\\t{{.Status}}' 2>/dev/null")
d["systemd_units"]=run("systemctl list-units --type=service --all 2>/dev/null | grep -iE 'ai-agent|docker-sandbox|containerd-sandbox|hugo' | head -20")
d["listeners"]=run("ss -ltnp 2>/dev/null | grep -E ':8060|:38060|:9090' | head -10")
print(json.dumps(d,ensure_ascii=False,indent=2))
