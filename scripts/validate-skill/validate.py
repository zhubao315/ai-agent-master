#!/usr/bin/env python3
"""机械校验：目录完整性、frontmatter、manifest/VERSION 一致性。不做语义判断。"""
import os,re,sys,yaml
root=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
errs=[]
def chk(p):
    if not os.path.exists(os.path.join(root,p)): errs.append('missing '+p)
for p in ['SKILL.md','manifest.yaml','VERSION','CHANGELOG.md','README.md',
          'references/platform-architecture.md','runbooks/install.md','deploy/install.sh','deploy/uninstall.sh','deploy/verify-install.sh']:
    chk(p)
s=open(os.path.join(root,'SKILL.md'),encoding='utf-8').read()
m=re.match(r'^---\n(.*?)\n---\n',s,re.S)
if not m: errs.append('SKILL.md frontmatter missing')
else:
    fm=yaml.safe_load(m.group(1))
    for k in ('name','description'):
        if k not in fm: errs.append('frontmatter missing '+k)
    if fm.get('name')!='ai-agent-master': errs.append('name mismatch')
man=yaml.safe_load(open(os.path.join(root,'manifest.yaml'),encoding='utf-8'))
if man.get('skill_version')!=open(os.path.join(root,'VERSION')).read().strip(): errs.append('version mismatch')
print('validate-skill:', 'OK' if not errs else 'FAIL: '+'; '.join(errs))
sys.exit(1 if errs else 0)
