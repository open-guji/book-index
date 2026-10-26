#!/usr/bin/env python3
"""去重方案 5b-乙（2026-10-26）：① 中華再造善本 Book 补 base_edition 指同 Work 同版本名的原本 Book；② Book 墓碑 work_id 仍是草稿 ID 的改指 keeper 的 work_id。

    python3 zhsy_tomb.py [--apply]

① 候选取 ai-team 5b-研/分档-2223组.tsv 判「中華再造善本影印对原本」的组，从当前树重核：组内活 Book 恰一个 ZHSY（zhsy_id）＋恰一个非 ZHSY，
   同 Work，ZHSY 一侧尚无带 book_id 的 base_edition。已有只写 name 的底本项则补 book_id，不另加一项。
② 全扫 Book，work_id 不在 Work/ 的墓碑，取 merged_into 所指 keeper 的 work_id。"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../..'))
TSV = os.environ.get('FENDANG', '/home/user/ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/5b-研/分档-2223组.tsv')
TODAY = '2026-10-26'
apply = '--apply' in sys.argv


def ld(i):
    h = glob.glob(os.path.join(ROOT, 'Book', i[-3], i[-2], i[-1], i + '-*.json')); assert len(h) == 1, (i, h)
    return json.load(open(h[0], encoding='utf-8')), h[0]


def save(p, j):
    j.pop('revision', None); j.pop('revised_at', None)
    j['revision'] = '%d.0.0' % (int(rev0.get(j['id'], '1.0.0').split('.')[0]) + 1); j['revised_at'] = TODAY
    if apply: open(p, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')


rev0 = {}; log = []
for r in [l.rstrip('\n').split('\t') for l in open(TSV, encoding='utf-8')][1:]:
    if '再造' not in r[3]: continue
    js = [x for x in (ld(i) for i in r[4].split(',')) if not x[0].get('merged_into')]
    z = [x for x in js if x[0].get('zhsy_id')]; o = [x for x in js if not x[0].get('zhsy_id')]
    if len(z) != 1 or len(o) != 1: log.append(['跳過', r[4], f'ZHSY {len(z)}／原本 {len(o)}']); continue
    (zj, zp), (oj, _) = z[0], o[0]
    if zj['work_id'] != oj['work_id']: log.append(['跳過', r[4], 'Work 已不同']); continue
    be = zj.get('base_edition') or []
    if any(b.get('book_id') for b in be): log.append(['跳過', r[4], '已有 book_id']); continue
    rev0[zj['id']] = zj.get('revision') or '1.0.0'
    item = next((b for b in be if b.get('role') == '底本'), None)
    if item: item['book_id'] = oj['id']
    else:
        be.append({'role': '底本', 'name': oj.get('edition'), 'book_id': oj['id'],
                   'note': '中華再造善本影印；同 Work 同版本名原本唯一（去重 5b-研／5b-乙）', 'source': '5b-乙 同Work同版本名'})
        zj['base_edition'] = be
    save(zp, zj); log.append(['補', zj['id'], oj['id'], zj.get('zhsy_id'), oj.get('edition')])
W = {f.split('-')[0] for d, _, fs in os.walk(os.path.join(ROOT, 'Work')) for f in fs if f.endswith('.json')}
for d, _, fs in os.walk(os.path.join(ROOT, 'Book')):
    for f in fs:
        if not f.endswith('.json'): continue
        p = os.path.join(d, f); j = json.load(open(p, encoding='utf-8'))
        if j.get('merged_into') and j.get('work_id') not in W:
            k, _ = ld(j['merged_into']); assert not k.get('merged_into') and k['work_id'] in W
            log.append(['墓碑', j['id'], j['work_id'], k['work_id']]); j['work_id'] = k['work_id']
            rev0[j['id']] = j.get('revision') or '1.0.0'; save(p, j)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zhsy_tomb-log.tsv')
if apply: open(out, 'w', encoding='utf-8').write('\n'.join('\t'.join(map(str, x)) for x in log) + '\n')
from collections import Counter; print(Counter(x[0] for x in log))
