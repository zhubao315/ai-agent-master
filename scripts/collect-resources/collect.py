#!/usr/bin/env python3
"""机械采集资源基线（只读、无敏感信息）。"""
import json,subprocess,shutil,datetime
def run(cmd):
    try: return subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT,text=True,timeout=30).strip()
    except Exception as e: return f"unavailable: {e}"
d={"collected_at":datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
d["kernel"]=run("uname -sr"); d["cpu_cores"]=run("nproc")
d["memory"]=run("free -h | head -2")
d["gpu"]=run("nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader 2>/dev/null || echo unavailable")
d["disk"]=run("df -h / /data 2>/dev/null")
d["docker"]=run("docker ps --format '{{.Names}}\\t{{.Image}}\\t{{.Status}}' 2>/dev/null | head -40")
print(json.dumps(d,ensure_ascii=False,indent=2))
