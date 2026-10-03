#!/usr/bin/env python3
"""X2 候选（overview 项目进展/古籍目录/进度/X2-分类扩展候选/）落库。

按协调者裁定（overview #113，09-28）只吸收三档：
  千頃堂書目 高置信 -> classification，basis=S
  明史藝文志 高置信 -> classification，basis=S
  國史經籍志 低置信（只到部）-> 只写 l1，basis=C
中/低置信到类、依据二（同作者）、依据三（题名关键词）一律不写。

用法：
  python3 .claude/qa/s1/ingest_x2.py check    # 只读校验：词表、与现有 classification 冲突
  python3 .claude/qa/s1/ingest_x2.py write [--bucket 千頃堂書目|明史藝文志|國史經籍志] [--limit N]
"""
import argparse, csv, json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vocab

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OVERVIEW = os.environ.get('OVERVIEW_ROOT', '/home/user/overview')
CSV_PATH = os.path.join(OVERVIEW, '项目进展/古籍目录/进度/X2-分类扩展候选/out/S-catalog-candidates.csv')

TARGET_BUCKETS = {
    ('S-千頃堂書目', '高'): ('S', '千頃堂書目', True),   # (basis, source, keep_l2)
    ('S-明史藝文志', '高'): ('S', '明史藝文志', True),
    ('S-國史經籍志', '低'): ('C', '國史經籍志', False),
}


def load_rows():
    rows = list(csv.DictReader(open(CSV_PATH, encoding='utf-8-sig')))
    out = []
    for r in rows:
        key = (r['依据'], r['置信'])
        if key not in TARGET_BUCKETS:
            continue
        basis, source, keep_l2 = TARGET_BUCKETS[key]
        out.append({'work_id': r['work_id'], 'title': r['title'], 'l1': r['l1'],
                     'l2': r['l2'] if keep_l2 else '', 'l3': r['l3'] if keep_l2 else '',
                     'basis': basis, 'source': source, 'bucket': r['依据']})
    return out


def _fmt_of(raw, d):
    for ind in (2, 1, 4):
        for nl in ('\n', ''):
            if raw == json.dumps(d, ensure_ascii=False, indent=ind) + nl:
                return ind, nl
    return 2, '\n'


def index_paths():
    idx = {}
    for f in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
        wid = os.path.basename(f).split('-', 1)[0]
        idx[wid] = f
    return idx


def check():
    V = vocab.load_vocab()
    rows = load_rows()
    paths = index_paths()
    bad_vocab, already, missing = [], [], []
    for r in rows:
        c = {'l1': r['l1'], 'l2': r['l2'], 'l3': r['l3'], 'l4': ''}
        if not vocab.valid_classification(c, V):
            bad_vocab.append(r)
        p = paths.get(r['work_id'])
        if not p:
            missing.append(r); continue
        d = json.load(open(p, encoding='utf-8'))
        if d.get('classification'):
            already.append(r)
    print('候选总数', len(rows))
    print('词表校验不过', len(bad_vocab))
    for r in bad_vocab[:10]: print('  ', r)
    print('book-index 查无此 id', len(missing))
    for r in missing[:10]: print('  ', r)
    print('与现有 classification 冲突（已分类，不覆盖）', len(already))
    for r in already[:10]: print('  ', r)
    if already:
        json.dump(already, open(os.path.join(HERE, 'out', 'x2_skip_already_classified.json'), 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=1)
    return rows, paths, {r['work_id'] for r in already} | {r['work_id'] for r in bad_vocab} | {r['work_id'] for r in missing}


def write(bucket_name=None, limit=None):
    rows, paths, skip_ids = check()
    if bad := [r for r in rows if r['work_id'] in skip_ids]:
        print(f'（写入将跳过上面 {len(bad)} 条不合格/冲突的候选）')
    items = [r for r in rows if r['work_id'] not in skip_ids]
    if bucket_name:
        items = [r for r in items if bucket_name in r['bucket']]
    if limit:
        items = items[:limit]
    n = 0
    for r in items:
        p = paths[r['work_id']]
        raw = open(p, encoding='utf-8').read()
        d = json.loads(raw)
        if d.get('classification'):
            continue
        d['classification'] = {'l1': r['l1'], 'l2': r['l2'], 'l3': r['l3'], 'l4': '',
                                'basis': r['basis'], 'source': r['source']}
        fmt = _fmt_of(raw, json.loads(raw))
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=fmt[0]) + fmt[1])
        n += 1
    print(f'写入 {n} 条' + (f'（{bucket_name}）' if bucket_name else '（全部目标桶）'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['check', 'write'])
    ap.add_argument('--bucket', default=None)
    ap.add_argument('--limit', type=int, default=None)
    a = ap.parse_args()
    if a.cmd == 'check':
        check()
    else:
        write(a.bucket, a.limit)
