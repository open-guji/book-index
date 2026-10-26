#!/usr/bin/env python3
"""从已实施（未合）的本批里撤出若干组：这些组涉及的 Work／Book 文件恢复为基线原样，promotions 从基线按余下各组重做，
batch.json／merges.json 去掉这些组，index/ 恢复基线后由 update_index.py＋refresh_index_forced.py 重刷。
用于与他线 PR 撞同一 Work 时只撤撞的组（不手解 JSON）。用法：drop_groups.py <批次目录> <基线 rev> <keeper 或任一成员 id>…"""
import json, os, subprocess, sys, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
B, BASE, keys = sys.argv[1], sys.argv[2], set(sys.argv[3:])
def git(*a, **k): return subprocess.check_output(['git', '-c', 'core.quotePath=false', *a], cwd=ROOT, text=True, **k)
bj, mj = os.path.join(B, 'batch.json'), os.path.join(B, 'merges.json')
batch, merges = json.load(open(bj)), json.load(open(mj))
drop = [g for g in batch['groups'] if keys & {g['keeper'], *g['losers']}]
ids = {i for g in drop for i in [g['keeper'], *g['losers']]}
files = []
for rel in git('diff', '--name-only', BASE, '--', 'Work', 'Book').split('\n'):
    if not rel: continue
    if rel.startswith('Work/') and os.path.basename(rel)[:12] in ids: files.append(rel); continue
    if rel.startswith('Book/'):
        wids = set()
        for src in ('base', 'cur'):
            try:
                d = json.loads(git('show', f'{BASE}:{rel}')) if src == 'base' else json.load(open(os.path.join(ROOT, rel)))
                wids.add(d.get('work_id'))
            except Exception: pass
        if wids & ids: files.append(rel)
git('checkout', BASE, '--', *files)
keep = [g for g in batch['groups'] if g not in drop]
mp = {l: g['keeper'] for g in keep for l in g['losers']}
git('checkout', BASE, '--', 'promotions', 'index')
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'promotions', '*.json'))):
    t = open(f, encoding='utf-8').read(); o = t
    for l, k in mp.items():
        t = t.replace('"production_id": "%s"' % l, '"production_id": "%s"' % k)
    if t != o: open(f, 'w', encoding='utf-8').write(t); n += 1
batch['groups'] = keep
merges['merges'] = [m for m in merges['merges'] if m['cluster_id'] not in {g['cluster_id'] for g in drop}]
json.dump(batch, open(bj, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(merges, open(mj, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
dl = os.path.join(B, '撤出组.tsv')
with open(dl, 'a', encoding='utf-8') as f:
    for g in drop: f.write('%s\t%s\t%s\t与他线 PR 撞同一 Work，撤出待下轮从 main 重算\n' % (g['cluster_id'], g['keeper'], ','.join(g['losers'])))
print('撤出', len(drop), '组；恢复文件', len(files), '；promotions 重做', n, '；余', len(keep), '组')
