#!/usr/bin/env python3
"""结构测试：目录、frontmatter、manifest、版本一致性、引用完整性。"""
import os,re,sys,yaml
root=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
errors=[]
req=['SKILL.md','manifest.yaml','VERSION','CHANGELOG.md','README.md',
     'deploy/install.sh','deploy/uninstall.sh','deploy/verify-install.sh',
     'scripts/validate-skill/validate.py']
req+= [f'references/{n}.md' for n in ['platform-architecture','services-and-dependencies','environment-baseline','resource-assessment','gpu-management','model-management','inference-operations','agent-runtime','rag-operations','deployment-guide','performance-optimization','troubleshooting','upgrade-guide','rollback-guide','backup-restore','security-guide']]
req+= [f'runbooks/{n}.md' for n in ['install','deploy','restart','health-check','model-deploy','gpu-diagnosis','incident-response','performance-tuning','upgrade','rollback']]
for p in req:
    if not os.path.exists(os.path.join(root,p)): errors.append('missing '+p)
s=open(os.path.join(root,'SKILL.md'),encoding='utf-8').read()
m=re.match(r'^---\n(.*?)\n---\n',s,re.S)
if not m: errors.append('no frontmatter')
else:
    fm=yaml.safe_load(m.group(1)); 
    if fm.get('name')!='ai-agent-master': errors.append('bad name')
    if not fm.get('description'): errors.append('no description')
man=yaml.safe_load(open(os.path.join(root,'manifest.yaml'),encoding='utf-8'))
if man.get('skill_version')!=open(os.path.join(root,'VERSION')).read().strip(): errors.append('version mismatch')
# referenced files exist
for ref in set(re.findall(r'(?:references|runbooks)/[a-z-]+\.md',s)):
    if not os.path.exists(os.path.join(root,ref)): errors.append('broken ref '+ref)
print('structure:', 'PASS' if not errors else 'FAIL '+str(errors))
sys.exit(1 if errors else 0)
