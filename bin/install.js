#!/usr/bin/env node
/* ai-agent-master one-command installer.
 * Usage:
 *   ai-agent-master                 # install/upgrade into OpenCode skills dir
 *   ai-agent-master --check-only    # postinstall sanity check (no copy)
 *   ai-agent-master --uninstall     # remove installed skill
 * Env: OINK_SKILLS_DIR / OPENCODE_SKILLS_DIR to override target.
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const pkgRoot = path.resolve(__dirname, '..');
const src = pkgRoot;

function targets() {
  const env = process.env.OPENCODE_SKILLS_DIR || process.env.OINK_SKILLS_DIR;
  const list = env ? [env] : [
    path.join(os.homedir(), '.config', 'opencode', 'skills'),
    path.join(process.cwd(), '.opencode', 'skills'),
  ];
  return list;
}
function check() {
  if (!fs.existsSync(path.join(src, 'SKILL.md'))) throw new Error('SKILL.md missing in package');
  const txt = fs.readFileSync(path.join(src, 'SKILL.md'), 'utf8');
  if (!/^---\n[\s\S]*?\n---\n/.test(txt) || !/name:\s*ai-agent-master/.test(txt)) throw new Error('frontmatter invalid');
  return true;
}
function copyDir(a, b) {
  fs.mkdirSync(b, { recursive: true });
  for (const e of fs.readdirSync(a, { withFileTypes: true })) {
    const s = path.join(a, e.name), d = path.join(b, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else if (!e.name.startsWith('.install')) fs.copyFileSync(s, d);
  }
}
function main() {
  check();
  if (process.argv.includes('--check-only')) { console.log('ai-agent-master: package OK'); return; }
  const dests = targets();
  if (process.argv.includes('--uninstall')) {
    for (const d of dests) { const t = path.join(d, 'ai-agent-master'); if (fs.existsSync(t)) { fs.rmSync(t, { recursive: true, force: true }); console.log('removed', t); } }
    return;
  }
  const dir = dests.find(d => fs.existsSync(d)) || dests[0];
  const target = path.join(dir, 'ai-agent-master');
  copyDir(src, target);
  console.log('installed ai-agent-master ->', target);
  console.log('verify with: node', path.join(target, 'scripts/validate-skill/validate.py'));
}
try { main(); } catch (e) { console.error('ai-agent-master install failed:', e.message); process.exit(1); }
