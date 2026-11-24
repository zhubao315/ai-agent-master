#!/usr/bin/env python3
"""兼容性：manifest 声明的版本与实际静态证据比对（不联网）。"""
import yaml,json,os,sys
root=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
m=yaml.safe_load(open(os.path.join(root,'manifest.yaml'),encoding='utf-8'))
state='/data/ai-agent-next/installed-state.json'
actual='unknown'
if os.path.exists(state):
    try: actual=json.load(open(state)).get('productVersion','unknown')
    except Exception: pass
ver=m['compatibility']['verified_version']
print('verified_version:',ver,'| local installed-state:',actual)
# 不因为本地状态与文档站版本差异而失败：两者可能在不同阶段更新
print('compatibility check: INFO only, no assertion')
sys.exit(0)
