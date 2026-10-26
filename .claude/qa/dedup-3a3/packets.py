#!/usr/bin/env python3
"""3a-3：把待核对切成核查包（每包 N 对，JSONL），供子 agent 逐条判。

    python3 packets.py <scan_dir> <out_dir> [--size 100] [--cls 候选,候选-一侧无作者,...]
"""
import argparse, csv, glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def load(i):
    hits = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))
    return json.load(open(hits[0], encoding='utf-8'))

def brief(d):
    desc = d.get('description')
    if isinstance(desc, dict): desc = desc.get('text')
    return {'id': d['id'], 'title': d.get('title'), 'additional_titles': d.get('additional_titles'),
            'authors': [{k: a.get(k) for k in ('name', 'role', 'dynasty', 'entity_id')} for a in d.get('authors') or [] if isinstance(a, dict)],
            'dynasty': d.get('dynasty'), 'juan_count': d.get('juan_count'), 'subtype': d.get('subtype'),
            'description': (desc or '')[:300],
            'indexed_by': [{k: (ib.get(k) or '')[:260] for k in ('source', 'title_info', 'author_info', 'section', 'summary', 'note') if ib.get(k)}
                           for ib in d.get('indexed_by') or [] if isinstance(ib, dict)][:5],
            'n_indexed_by': len(d.get('indexed_by') or []),
            'contained_in': d.get('contained_in')}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('scan'); ap.add_argument('out'); ap.add_argument('--size', type=int, default=100)
    ap.add_argument('--cls', default='候选,候选-一侧无作者,候选-仅additional_titles,X-仅AT无同作者,X-泛题')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    want = a.cls.split(',')
    hits = {}
    for h in csv.DictReader(open(os.path.join(a.scan, 'hits.tsv'), encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE):
        hits.setdefault(tuple(sorted((h['src'], h['dst']))), []).append(h)
    rows = [r for r in csv.DictReader(open(os.path.join(a.scan, 'pairs.tsv'), encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE) if r['cls'] in want]
    rows.sort(key=lambda r: (want.index(r['cls']), r['a']))
    n = 0
    for k in range(0, len(rows), a.size):
        n += 1
        with open(os.path.join(a.out, 'p%02d.jsonl' % n), 'w', encoding='utf-8') as f:
            for r in rows[k:k + a.size]:
                hs = hits[(r['a'], r['b'])]
                ev = [{'in_work': h['src'], 'field': h['field'], 'mark': h['mark'], 'alias': h['alias_raw'], 'context': h['context']}
                      for h in hs if not h['field'].startswith('additional_titles')][:4]
                ev += [{'in_work': h['src'], 'field': 'additional_titles', 'alias': h['alias_raw']} for h in hs if h['field'].startswith('additional_titles')][:2]
                f.write(json.dumps({'pair': '%s|%s' % (r['a'], r['b']), 'cls': r['cls'], 'evidence': ev,
                                    'A': brief(load(r['a'])), 'B': brief(load(r['b']))}, ensure_ascii=False) + '\n')
    print('对', len(rows), '包', n)

if __name__ == '__main__':
    main()
