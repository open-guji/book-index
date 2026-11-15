#!/usr/bin/env python3
"""第三輪（車道 a11-sjj-members）：用戶新口徑下補建古人著作的民國／昭和等排印本 Book、外國線和刻本／日本排印本 Book，並補挂。

用法：build3.py [--apply]；決策在 decisions3.py。
"""
import argparse, csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, os.path.join(BI, 'build')); sys.path.insert(0, HERE)
import mintid, v2common as V, decisions3 as D
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); A = ap.parse_args()
TODAY = '2026-11-15'; LANE = 'a11-sjj-members'
CNAME = {'lunyu': ('無求備齋論語集成', '8rle3p1lu1vk'), 'laozi2': ('無求備齋老子集成續編', '8rle3p1lu1vn'), 'laolie': ('無求備齋老列莊三子集成補編', '8rle3p1lu1vo')}
CINII = lambda n: {'id': n, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + n}
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def wtitle(wid):
    import glob
    p = glob.glob(os.path.join(BI, 'Work', wid[-3], wid[-2], wid[-1], wid + '-*.json'))
    if p: return json.load(open(p[0], encoding='utf-8'))['title']
    import pickle
    I = pickle.load(open('/tmp/sjj3/idx.pkl', 'rb'))
    return next(w['title'] for w in I['Work'] if w['id'] == wid)
bids = mintid.mint('Book', LANE, len(D.ITEMS)) if A.apply else ['dryb%06d' % i for i in range(len(D.ITEMS))]
files = {}; log = {}
for it, bid in zip(D.ITEMS, bids):
    title = wtitle(it['work']); ed = it['edition']
    if it['coll']:
        cn, cid = CNAME[it['coll']]
        v = '、'.join(it['vols'][r] for r in it['rows'])
        ed = '%s（%s影印，%s）' % (ed, cn, v)
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': title, 'work_id': it['work'], 'edition': ed}
    if it['etype']: d['edition_type'] = it['etype']
    d['sources'] = [CINII(n) for n in it['ncids']]
    d['ai_note'] = '2026-11-15 十三經縱向補全·第三輪（用戶新口徑：古人著作的民國／昭和等排印本、日本重刊本亦建 Book）：據 CiNii Books %s 著錄。%s。底本信息取自 CiNii 注記，未核原書。' % ('、'.join(it['ncids']), it['note'])
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    if it['coll']:
        d['contained_in'] = [{'id': cid, 'volume_index': v}]
    fn = '%s-%s%s.json' % (bid, title, re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、]', '', it['edition'])[:24])
    files['Book/%s/%s/%s/%s' % (bid[-3], bid[-2], bid[-1], fn)] = d
    for r in it['rows']: log[r] = ('新建 Book 並挂入丛編', bid)
print('Book 新建', len(files), '挂接', len(D.ATTACH))
for p in files: print(p)
if not A.apply: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
import glob
att = {}
for a in D.ATTACH:
    p = glob.glob(os.path.join(BI, 'Book', a['book'][-3], a['book'][-2], a['book'][-1], a['book'] + '-*.json'))[0]
    raw = open(p, encoding='utf-8').read(); d = json.loads(raw); fmt = V.detect_format(raw, d)
    cid = CNAME[a['coll']][1]; cil = d.setdefault('contained_in', [])
    if not any(c['id'] == cid for c in cil):
        cil.append({'id': cid, 'volume_index': a['vol']})
        x, y, z = (int(t) for t in (d.get('revision') or '1.0.0').split('.')); d['revision'] = '%d.%d.0' % (x, y + 1); d['revised_at'] = TODAY
        open(p, 'w', encoding='utf-8').write(V.dump(d, fmt))
    att[a['book']] = os.path.relpath(p, BI); log[a['row']] = ('挂入既有 Book', a['book'])
# 台賬
p = os.path.join(BI, '.claude/qa/sjj-collections/members-todo.tsv')
rr = list(csv.reader(open(p, encoding='utf-8'), delimiter='\t'))
if len(rr[0]) < 16: rr[0] = rr[0][:14] + ['第三輪處理（2026-11-15 sjj-members3）', '第三輪 id']
for i, r in enumerate(rr[1:], 2):
    r += [''] * (16 - len(r))
    if i in log: r[14], r[15] = log[i][0] + '（新口徑：古人著作之近現代版本亦建 Book）', log[i][1]
with open(p, 'w', encoding='utf-8', newline='') as f:
    csv.writer(f, delimiter='\t', lineterminator='\n').writerows(rr)
json.dump({'book': {d['id']: p_ for p_, d in files.items()}, 'attach': att}, open(os.path.join(HERE, 'result3_b1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已寫')
