#!/usr/bin/env python3
"""去重方案部分 2.3：按 plan23.py 的 plan.json 新建人物 Entity，并把对应 Work 作者位的 entity_id 指过去。

    python3 apply23.py <plan.json> <台账目录> [--share i/n] [--start N --count M | --pick 名单.txt] [--apply]

不加 --apply 只核对、印计划。逐位重验：Work 非墓碑、作者位名未变、尚无 entity_id；任一位不合则整组跳过。
id 用 mintid.py（车道 dedup23＝machine 2035）。Work 只设 authors[slot].entity_id，别的不动（同 2.2 apply_attach.py）。"""
import argparse, collections, datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
sys.path.insert(0, QA)
import jio, mintid  # noqa: E402

TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-7))).strftime('%Y-%m-%d')   # 洛杉矶日期（夏令时）
ap = argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('out')
ap.add_argument('--start', type=int, default=0); ap.add_argument('--count', type=int); ap.add_argument('--pick')
ap.add_argument('--share', help='分份并行：i/n，只取 int(md5(名).hexdigest(),16) %% n == i 的组（同名不同朝代的组同在一份）')
ap.add_argument('--apply', action='store_true')
a = ap.parse_args()
plan = json.load(open(a.plan, encoding='utf-8'))
print('载入计划 %d 组' % len(plan)); assert plan
if a.share:
    import hashlib
    si, sn = map(int, a.share.split('/'))
    plan = [g for g in plan if int(hashlib.md5(g['name'].encode('utf-8')).hexdigest(), 16) % sn == si]
    print('分份 %d/%d：%d 组' % (si, sn, len(plan)))
if a.pick:
    want = [l.rstrip('\n').split('\t') for l in open(a.pick, encoding='utf-8') if l.strip()]
    key = {(g['name'], g['dynasty'] or ''): g for g in plan}
    groups = [key[(w[0], w[1] if len(w) > 1 else '')] for w in want]
else:
    groups = plan[a.start:a.start + a.count] if a.count else plan[a.start:]

ok, skipped = [], []
cache = {}   # 同一 Work 可有多个新建作者位：同一份内存对象，最后各写一次（b01 首版曾因逐组读写互相覆盖，丢 723 位）
def load(rel):
    if rel not in cache: cache[rel] = jio.load(rel)
    return cache[rel]
for g in groups:
    bad = None; docs = []
    for s in g['slots']:
        p = os.path.join(jio.ROOT, s['path'])
        if not os.path.exists(p): bad = '文件已不在 ' + s['path']; break
        d, fmt = load(s['path'])
        au = (d.get('authors') or [None] * (s['slot'] + 1))[s['slot']] if len(d.get('authors') or []) > s['slot'] else None
        if d.get('merged_into'): bad = 'Work 已成墓碑 ' + s['id']; break
        if not isinstance(au, dict) or au.get('name') != s['name'] or au.get('entity_id'): bad = '作者位已变 %s#%d' % (s['id'], s['slot']); break
        docs.append((s, d, fmt))
    if bad: skipped.append((g['name'], g['dynasty'], bad)); continue
    ok.append((g, docs))
print('可执行 %d 组，跳过 %d 组' % (len(ok), len(skipped)))
for r in skipped[:20]: print('  跳过', *r)

lane = {1: 'dedup23乙', 2: 'dedup23丙'}.get(si if a.share and sn == 3 else 0, 'dedup23')   # 三份各用一车道，免并行同秒撞号
ids = mintid.mint('Entity', lane, len(ok)) if a.apply else ['(待鑄%d)' % i for i in range(len(ok))]
ledger = []
for (g, docs), eid in zip(ok, ids):
    titles = []
    for s, _, _ in docs:
        if s['title'] and s['title'] not in titles: titles.append(s['title'])
    tl = '、'.join('《%s》' % t for t in titles[:3]) + ('等 %d 部' % len(titles) if len(titles) > 3 else '')
    note = ('去重方案部分 2.3（%s）據正式庫 Work 作者位新建：%s之責任者「%s」（%d 個作者位，朝代「%s」），按名＋朝代聚合；庫中無同名人物條。'
            '《中國古籍總目》person_uri 一名一號，只作溯源，非同人證據。' % (TODAY, tl, g['name'], len(docs), g['dynasty'] or '無'))
    rec = {'schema_version': 1, 'id': eid, 'type': 'entity', 'subtype': 'people', 'primary_name': g['name']}
    if g['dynasty']:
        rec['dynasty'] = g['dynasty']; rec['dynasty_basis'] = '據《中國古籍總目》責任者著錄'
    if g['cbdb']:
        c = g['cbdb']
        rec['external_ids'] = {'cbdb_id': c['id'], 'cbdb_match': 'auto', 'cbdb_source': 'name_exact+dy_match+unique（去重部分2.3，CBDB 20260919）'}
        note += 'CBDB 同名同朝代唯一（%d，%s%s），按 B 檔採信，未逐條核生卒。' % (c['id'], c['dy'] or '', '，指數年 %s' % c['iy'] if c['iy'] else '')
    elif g.get('cbdb_cand'):
        note += 'CBDB 有同名同朝代一人（%d），未經時地核對，暫不寫 cbdb_id。' % g['cbdb_cand']
    elif g['cbdb_n'] >= 2:
        note += 'CBDB 有同名同朝代 %d 人，未採。' % g['cbdb_n']
    if len(docs) >= 2:
        note += '如見同名異人，可按作者位拆出。'
    if g['uris']:
        rec['description'] = {'sources': [{'name': '中國古籍總目', 'type': 'url', 'details': 'http://data.library.sh.cn/entity/person/' + u} for u in g['uris']]}
    rec['ai_note'] = note
    rec['review'] = {'status': 'unreviewed'}
    rec['revision'] = '1.0.0'; rec['revised_at'] = TODAY
    rel = mintid.path_for(eid, g['name'], 'Entity') if a.apply else None
    if a.apply:
        os.makedirs(os.path.dirname(os.path.join(jio.ROOT, rel)), exist_ok=True)
        assert not os.path.exists(os.path.join(jio.ROOT, rel))
        jio.save(rel, rec, (2, '\n'))
        for s, d, fmt in docs:
            d['authors'][s['slot']]['entity_id'] = eid
    ledger.append({'entity_id': eid, 'path': rel, 'name': g['name'], 'dynasty': g['dynasty'], 'cbdb_id': g['cbdb'] and g['cbdb']['id'],
                   'slots': [{'work_id': s['id'], 'path': s['path'], 'slot': s['slot'], 'title': s['title'], 'role': s['role']} for s, _, _ in docs]})

if a.apply:
    touched = {s['path'] for x in ledger for s in x['slots']}
    for rel in touched: jio.save(rel, *cache[rel])
    miss = 0
    for x in ledger:   # 写后逐位复核
        for s in x['slots']:
            if jio.load(s['path'])[0]['authors'][s['slot']].get('entity_id') != x['entity_id']: miss += 1
    print('写回 Work %d 部；复核作者位缺 entity_id：%d' % (len(touched), miss)); assert miss == 0
os.makedirs(a.out, exist_ok=True)
if a.apply:
    json.dump(ledger, open(os.path.join(a.out, 'created.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'skipped.tsv'), 'w', encoding='utf-8') as f:
        f.write('name\tdynasty\treason\n' + ''.join('%s\t%s\t%s\n' % r for r in skipped))
print('新建 %d 个人物 Entity，挂 %d 个作者位，写 cbdb_id %d%s' % (len(ledger), sum(len(x['slots']) for x in ledger),
      sum(1 for x in ledger if x['cbdb_id']), '' if a.apply else '（乾跑）'))
