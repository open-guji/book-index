#!/usr/bin/env python3
"""方志-并：由 clusters.py 的 clusters.json 与逐簇核对结论 verdict*.jsonl 生成 apply_batch 用的 batch.json。

    python3 mkbatch.py <卷宗目录> <批次目录> [--only cid,cid…] [--skip 批次目录,…] [--limit N]

只收 verdict 为 SAME（全簇）或 PARTIAL（只并 merge 所列）的簇；keeper_ok=false 的簇按 reason 里给出的 id 换 keeper
（须在簇内，且须另在 verdict 的 keeper 字段写明），否则跳过报出。evidence 写脚本初判＋核对理由。
"""
import argparse, glob, json, os, sys
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--only'); ap.add_argument('--skip', default=''); ap.add_argument('--limit', type=int)
a = ap.parse_args()
D = {c['cid']: c for c in json.load(open(os.path.join(a.src, 'clusters.json'), encoding='utf-8'))}
def rd(i): return json.load(open(glob.glob(f"Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json")[0], encoding='utf-8'))
V = {}
for f in sorted(glob.glob(os.path.join(a.src, 'verdict*.jsonl'))):
    for l in open(f, encoding='utf-8'):
        if l.strip():
            v = json.loads(l); V[v['cid']] = v
ADJ = json.load(open(os.path.join(a.src, 'keeper调整与暂缓.json'), encoding='utf-8'))
print('载入簇 %d，核对结论 %d，keeper 调整 %d，暂缓 %d' % (len(D), len(V), len(ADJ['keeper']), len(ADJ['hold'])))
if not D or not V: sys.exit('载入为 0，停')
done = set()
for s in filter(None, a.skip.split(',')):
    done |= {g['case_id'] for g in json.load(open(os.path.join(s, 'batch.json'), encoding='utf-8'))['groups']}
only = set(a.only.split(',')) if a.only else None
groups, skipped = [], []
for cid in sorted(D):
    c, v = D[cid], V.get(cid)
    if cid in done or (only and cid not in only): continue
    if not v or v['verdict'] not in ('SAME', 'PARTIAL'): continue
    if cid in ADJ['hold']: skipped.append((cid, ADJ['hold'][cid])); continue
    adj = ADJ['keeper'].get(cid, {})
    keeper = adj.get('keeper', c['keeper'])
    if not v.get('keeper_ok', True) and not adj: skipped.append((cid, 'keeper 待定')); continue
    if v['verdict'] == 'PARTIAL' and not adj.get('losers'): losers = [i for i in v.get('merge') or [] if i in c['members'] and i != keeper]
    else: losers = adj.get('losers') or [i for i in c['members'] if i != keeper]
    if (keeper not in c['members'] and not adj.get('external')) or not losers: skipped.append((cid, '无可并')); continue
    docs = {i: rd(i) for i in [keeper] + losers}
    if any(d.get('merged_into') for d in docs.values()): skipped.append((cid, '已有成员是墓碑（别的单元并过）')); continue
    def br(i):
        d = docs[i]; au = '、'.join('%s%s' % (x.get('name'), x.get('role') or '') for x in d.get('authors') or []) or '—'
        src = '/'.join(dict.fromkeys(x.get('source') for x in d.get('indexed_by') or [])) or '无著录（故宫等）'
        return '《%s》%s（%s）' % (d['title'], au, src)
    labs = '；'.join(sorted(set(l for k, l in c['pairs'].items() if all(x in [keeper] + losers for x in k.split('|'))))) or '（keeper 为簇外总目条，题名多「重修／新修」未入同题组）'
    ev = '方志同修次重出：%s ← %s。脚本初判 %s。逐簇核对：%s' % (br(keeper), '、'.join(br(l) for l in losers), labs, v['reason'])
    notes = {}
    for l in losers:
        p = glob.glob(f"Work/{l[-3]}/{l[-2]}/{l[-1]}/{l}-*.json")[0]; d = json.load(open(p, encoding='utf-8'))
        notes[l] = {k: d[k] for k in ('description', 'ai_note') if d.get(k)}
    groups.append(dict(case_id=cid, cluster_id='方志-' + cid, type='work', keeper=keeper, losers=losers,
                       keeper_source='研-方志 fangzhi_judge.py ＋ 方志-并 clusters.py（%s）' % c['group'],
                       evidence=ev, rule='去重方案研-方志：同一修次重出（A 同人／B 同年同卷，逐簇子 agent 核）B 档证据并',
                       why=ev, loser_original_notes=notes))
    if a.limit and len(groups) >= a.limit: break
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('入批 %d 簇、被并 %d 条；跳过 %s' % (len(groups), sum(len(g['losers']) for g in groups), skipped))
