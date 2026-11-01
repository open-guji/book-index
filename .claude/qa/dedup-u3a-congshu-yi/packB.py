#!/usr/bin/env python3
"""轨 B：无候选的名字 → 新建人物复核包（每个 名×朝代 一条）。python3 packB.py <cand 目录> <包目录> [每包名数=60]"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); QA = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(QA, 'entity-governance-1025')]
import egov  # noqa: E402
src, out = sys.argv[1], sys.argv[2]; PER = int(sys.argv[3]) if len(sys.argv) > 3 else 60
os.makedirs(out, exist_ok=True)
people = egov.load_people()
live = {k: v[1] for k, v in people.items() if not v[1].get('merged_into')}
pn = [(k, d['primary_name']) for k, d in live.items()]
rows = [json.loads(l) for l in open(os.path.join(src, 'slots.jsonl'), encoding='utf-8')]
BROKEN = re.compile(r'[□〓\[\]【】&;；,，、 -]|\?|？|⿰|⿱|（|）|\(|\)')
by = collections.defaultdict(list)
for r in rows:
    if r['cands']: continue
    n = r['norm']
    if n == '失譯' or BROKEN.search(n) or re.search(r'(局|館|社|院|監|部|處|廳|衙門|公司|書莊|堂|藥房|會|所)$', n): continue
    by[(n, r['dyn'] or '')].append(r)
items = []
for (n, dy), rs in sorted(by.items(), key=lambda x: -len(x[1])):
    sim = [(k, p) for k, p in pn if len(n) >= 2 and p != n and (n in p or (len(p) >= 2 and p in n))][:6]
    items.append({'name': n, 'dyn': dy, 'sim': ['%s=%s(%s)' % (k, p, live[k].get('dynasty')) for k, p in sim], 'more': max(0, len(rs) - 6),
                  'works': [{'k': r['id'], 'title': r['title'], 'role': r['role'], 'sec': r['section'][:16], 'ai': r['author_info'], 'sum': r['sum']} for r in rs[:6]]})
print('组', len(items), '作品', sum(len(v) for v in by.values()))
for i in range(0, len(items), PER):
    with open(os.path.join(out, 'B-%02d.jsonl' % (i // PER + 1)), 'w', encoding='utf-8') as f:
        for it in items[i:i + PER]: f.write(json.dumps(it, ensure_ascii=False) + '\n')
