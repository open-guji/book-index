#!/usr/bin/env python3
"""第二輪（車道 a11-sjj-members）：處理 members-todo.tsv 中仍「未處理」的行。

口徑（用戶 2026-11-15）：近現代學者著作不錄；民國讀本不錄；外國 1912 前著作錄；選本單卷不另立（作全集 Work 下一個版本）。
決策表在 decisions2.py（人工逐行判定）；本腳本只負責：按決策建 Work／Book、給既有 Book 補挂 contained_in、寫台賬。
用法：build2.py --idx idx.pkl --batch 1|2|3 [--apply]
"""
import argparse, collections, csv, json, os, pickle, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
import mintid
sys.path.insert(0, os.path.join(BI, 'build'))
import v2common as V  # noqa: E402
import decisions2 as D2

ap = argparse.ArgumentParser(); ap.add_argument('--idx', required=True); ap.add_argument('--batch', type=int, required=True); ap.add_argument('--apply', action='store_true')
A = ap.parse_args()
TODAY = '2026-11-15'; LANE = 'a11-sjj-members'
IDS = json.load(open(os.path.join(BI, '.claude/qa/sjj-collections/ids.json'), encoding='utf-8'))
COLL = {'無求備齋論語集成': 'lunyu', '無求備齋老子集成初編': 'laozi1', '無求備齋老子集成續編': 'laozi2', '無求備齋孟子十書': 'mengzi10', '無求備齋老列莊三子集成補編': 'laolie'}
ROOT = {'lunyu': 'd59f1iopaku8', 'laozi': 'd59ezkx8dt6o', 'mengzi': 'd59ezajwvda8', 'zhuang': 'd59fy1y0aqde', 'lie': 'd59ezahwgb9c'}
REL = {'C': 'contains_text_of', 'S': 'studies'}
CINII = lambda n: {'id': n, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + n}
EDO = '江戶時代'

I = pickle.load(open(A.idx, 'rb'))
rows = list(csv.reader(open(os.path.join(BI, '.claude/qa/sjj-collections/members-todo.tsv'), encoding='utf-8'), delimiter='\t'))
HEAD, body = rows[0], rows[1:]
WID = {w['id']: w for w in I['Work']}
BW = collections.defaultdict(list)
for b in I['Book']:
    if not b['mg']: BW[b['wid']].append(b)
CID = {c['id']: c['title'] for c in I['Collection']}
edtxt = lambda b: b['ed'] or ''
cititle = lambda b: ' '.join(CID.get(c['id'], '') for c in (b['ci'] or []))

def vol_of(r):
    v = r[4] or ''
    m = re.search(r'第\s*(\d+(?:\s*[-—ー]\s*\d+)?)\s*函', v + ' ' + r[5])
    if m and COLL[r[0]] != 'laolie': return '第%s函' % re.sub(r'\s', '', m.group(1))
    if COLL[r[0]] == 'laolie' and re.match(r'^[\d\-, ]+$', v): return '第%s冊' % re.sub(r'\s', '', v)
    return None
def etype(b):
    if re.search(r'活字', b): return '活字本'
    if re.search(r'石印', b): return '石印本'
    if re.search(r'套印', b): return '套印本'
    if re.search(r'鈔|抄|寫本', b): return '抄本'
    if re.search(r'排印|鉛印', b): return '鉛印本'
    if re.search(r'刊|刻|版', b): return '刻本'
    return None

log = {}   # row -> (act, ids)
def setlog(r, act, ids=''):
    if r in log:
        a0, i0 = log[r]; log[r] = (a0 + '；' + act, (i0 + ' / ' + ids) if (i0 and ids) else (i0 or ids))
    else: log[r] = (act, ids)

# 0. 展開決策（一行可含多書）
decs = []   # (row, dec)
for r, d in sorted(D2.DEC.items()):
    if D2.batch_of(r) != A.batch: continue
    for x in (d if isinstance(d, list) else [d]): decs.append((r, x))
# 1. 新建 Work（按 key；本批 NB 用到才建）
keys = []; key_rows = collections.defaultdict(list)
for r, dec in decs:
    if dec[0] == 'NB':
        if dec[1] not in keys: keys.append(dec[1])
        key_rows[dec[1]].append(r)
mint_w = mintid.mint('Work', LANE, len(keys)) if (A.apply and keys) else ['dryw%08d' % i for i in range(len(keys))]
wid_by_key = dict(zip(keys, mint_w))
wfiles = {}; pairs = []; newworks = set()
for k in keys:
    d = D2.NEWWORK[k]; wid = wid_by_key[k]; rs = sorted(set(key_rows[k])); row = rows[rs[0] - 1]
    al = []
    for n, role, dyn in d['authors']:
        a = {'name': n, 'role': role}
        if dyn: a['dynasty'] = dyn
        al.append(a)
    dyn0 = al[0].get('dynasty')
    ncids = ';'.join(rows[x - 1][1] for x in rs)
    near = [w for w in I['Work'] if not w['mg'] and norm(w['title']) == norm(d['title'])]
    note = ('2026-11-15 十三經縱向補全·第二輪（無求備齋成員補建）：據 CiNii Books 合冊子記錄 %s（%s・%s）著錄（一條記錄含多書，拆開後單書），庫內無同題同撰人 Work 而新建。'
            '題名、責任者、朝代取自該目，未覆核原書；責任者未逐一考證' % (ncids, row[0], vol_of(row) or '')) + \
           ('；庫內另有同題異撰人 Work %s，非同書另立' % '、'.join(w['id'] for w in near[:6]) if near else '') + '。'
    w = {'schema_version': 1, 'id': wid, 'type': 'work', 'title': d['title'], 'authors': al}
    if dyn0: w['dynasty'] = dyn0
    w['related_works'] = [{'id': ROOT[d['root']], 'relation': REL[d['rel']]}]
    w['sources'] = [CINII(rows[x - 1][1]) for x in rs]
    w['ai_note'] = note; w['revision'] = '1.0.0'; w['revised_at'] = TODAY
    if dyn0 == EDO:
        w['period_upper'] = 'qing'; w['period_upper_basis'] = '撰人為日本江戶時代人，與清並行；歧而未決，無論何解皆不晚於 qing'
    pth = 'Work/%s/%s/%s/%s-%s.json' % (wid[-3], wid[-2], wid[-1], wid, d['title'])
    wfiles[pth] = w
    for x in near: pairs.append((wid, x['id'], '無求備齋成員補建（第二輪）：同題異撰人另立（%s／%s），非同書' % ('、'.join(a['name'] for a in al), '、'.join(a[0] for a in x['au']) or '未署')))

# 2. 判 Book 操作
ops = []   # (row, wid, base, extra)
attaches = {}
for r, dec in decs:
    row = rows[r - 1]
    if dec[0] == 'S': setlog(r, '未處理：' + dec[1]); continue
    if dec[0] == 'A':
        b = next((x for x in I['Book'] if x['id'] == dec[1]), None)
        assert b, dec
        cid = IDS[COLL[row[0]]]
        if any(c['id'] == cid for c in (b['ci'] or [])): setlog(r, '已挂'); continue
        attaches.setdefault(b['id'], dict(book=b, items=[]))['items'].append(dict(collection=cid, volume_index=vol_of(row), row=r))
        setlog(r, '挂入既有 Book', b['id']); continue
    if dec[0] == 'B':   # ('B', wid_or_key, base[, extra])
        ops.append((r, dec[1], dec[2], dec[3] if len(dec) > 3 else {}))
    if dec[0] == 'AUTO':   # ('AUTO', wid, base)：自動比對既有 Book
        _, wid, base = dec[:3]
        bs = BW.get(wid, [])
        e1 = [b for b in bs if ed_match(base, edtxt(b)) >= 0.9]
        c1 = [b for b in bs if ed_match(base, cititle(b)) >= 0.9]
        weak = [b for b in bs if 0.3 <= max(ed_match(base, edtxt(b)), ed_match(base, cititle(b))) < 0.9]
        cid = IDS[COLL[row[0]]]
        pick = e1 if len(e1) == 1 else (c1 if (not e1 and len(c1) == 1) else None)
        if pick:
            b = pick[0]
            if any(c['id'] == cid for c in (b['ci'] or [])): setlog(r, '已挂'); continue
            attaches.setdefault(b['id'], dict(book=b, items=[]))['items'].append(dict(collection=cid, volume_index=vol_of(row), row=r))
            setlog(r, '挂入既有 Book', b['id']); continue
        if e1 or c1: setlog(r, '未處理：注記底本「%s」與庫內 Book 吻合不止一個（%s）' % (base, '、'.join(b['id'] for b in (e1 or c1))[:60])); continue
        if weak: setlog(r, '未處理：注記底本「%s」與庫內近似版本 Book（%s）疑同版，不重建' % (base, '；'.join('%s:%s' % (b['id'], (b['ed'] or cititle(b))[:14]) for b in weak[:2]))); continue
        ops.append((r, wid, base, {}))
    if dec[0] == 'NB':   # ('NB', newwork_key, base)：新 Work 的 Book
        ops.append((r, dec[1], dec[2], {}))

# 3. 建 Book（同一 key 同一底本的多行合併為一個 Book 多 contained_in）
groups = collections.OrderedDict()
for r, wk, base, ex in ops:
    wid = wid_by_key.get(wk, wk)
    groups.setdefault((wid, base), []).append((r, ex))
bids = mintid.mint('Book', LANE, len(groups)) if (A.apply and groups) else ['dryb%06d' % i for i in range(len(groups))]
bfiles = {}
for ((wid, base), rs), bid in zip(groups.items(), bids):
    r0, ex = rs[0]; row = rows[r0 - 1]
    wtitle = next((w['title'] for w in wfiles.values() if w['id'] == wid), None) or WID[wid]['title']
    ci = []; ncids = []; vtxts = []
    for r, _ in rs:
        rw = rows[r - 1]; cid = IDS[COLL[rw[0]]]; v = vol_of(rw)
        ci.append({'id': cid, **({'volume_index': v} if v else {})}); ncids.append(rw[1]); vtxts.append(v or '')
    # 同一 Book 多行（同丛編）：合併 volume_index
    merged = collections.OrderedDict()
    for c in ci: merged.setdefault(c['id'], []).append(c.get('volume_index'))
    ci = []
    for cid, vs in merged.items():
        vs = [v for v in vs if v]
        ci.append({'id': cid, **({'volume_index': '、'.join(vs)} if vs else {})})
    cname = row[0]; vtxt = '、'.join(v for v in vtxts if v)
    edition = '%s（%s影印%s）' % (base, cname, '，' + vtxt if vtxt else '')
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': wtitle, 'work_id': wid, 'edition': edition}
    et = etype(base)
    if et: d['edition_type'] = et
    d['sources'] = [CINII(n) for n in dict.fromkeys(ncids)]
    d['ai_note'] = ('2026-11-15 十三經縱向補全·第二輪（無求備齋成員補建）：據 CiNii Books 子記錄 %s 著錄，影印底本為「%s」，%s%s影印本。'
                    '底本信息取自 CiNii 注記，未核原書；CiNii 題名作「%s」' % ('、'.join(dict.fromkeys(ncids)), base, cname, ('（%s）' % vtxt) if vtxt else '', clean_title(row[2])))
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    d['contained_in'] = ci
    fn = '%s-%s%s.json' % (bid, wtitle, re.sub(r'[\\/:*?"<>|（）() ,，;；]', '', base)[:24])
    bfiles['Book/%s/%s/%s/%s' % (bid[-3], bid[-2], bid[-1], fn)] = d
    for r, _ in rs:
        newwk = [k for k, v in wid_by_key.items() if v == wid]
        isnew = wid in wid_by_key.values()
        setlog(r, ('新建 Work；' if isnew else '') + '新建 Book 並挂入丛編', ('%s / ' % wid if isnew else '') + bid)

print('Work 新建', len(wfiles), 'Book 新建', len(bfiles), '既有 Book 挂接', sum(len(v['items']) for v in attaches.values()))
for r in sorted(log): print(r, clean_title(rows[r - 1][2]), '|', log[r][0][:90], log[r][1])
if not A.apply: sys.exit(0)

def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
for pth, d in list(wfiles.items()) + list(bfiles.items()):
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
import subprocess
dirs = sorted({os.path.dirname(v['book']['path']) for v in attaches.values()})
if dirs: subprocess.run(['git', '-C', BI, '-c', 'core.quotepath=off', 'sparse-checkout', 'add'] + dirs, check=True)
for bid, v in attaches.items():
    p = os.path.join(BI, v['book']['path'])
    raw = open(p, encoding='utf-8').read(); d = json.loads(raw); fmt = V.detect_format(raw, d)
    assert d['id'] == bid and d['type'] == 'book'
    cil = d.setdefault('contained_in', [])
    for it in v['items']:
        if any(c['id'] == it['collection'] for c in cil): continue
        item = {'id': it['collection']}
        if it['volume_index']: item['volume_index'] = it['volume_index']
        cil.append(item)
    x_, y_, z_ = (int(t) for t in (d.get('revision') or '1.0.0').split('.')); d['revision'] = '%d.%d.0' % (x_, y_ + 1); d['revised_at'] = TODAY
    open(p, 'w', encoding='utf-8').write(V.dump(d, fmt))
if pairs:
    pth = os.path.join(BI, '.claude/qa/dedup-judged/無求備齋成員補建2.tsv')
    mode = 'a' if os.path.exists(pth) else 'w'
    with open(pth, mode, encoding='utf-8') as f:
        if mode == 'w': f.write('# 十三經縱向補全·無求備齋成員補建（第二輪）：同題異撰人另立，非重出（C）\n')
        for a, b, why in pairs: f.write('%s\t%s\tC\t%s\n' % (a, b, why))
# 台賬：members-todo.tsv 加兩列（第二輪處理／id）
p = os.path.join(BI, '.claude/qa/sjj-collections/members-todo.tsv')
rr = list(csv.reader(open(p, encoding='utf-8'), delimiter='\t'))
if len(rr[0]) < 14: rr[0] = rr[0][:12] + ['第二輪處理（2026-11-15 sjj-members2）', '第二輪 id']
for i, r in enumerate(rr[1:], 2):
    r += [''] * (14 - len(r))
    if i in log: r[12], r[13] = log[i][0], log[i][1]
with open(p, 'w', encoding='utf-8', newline='') as f:
    csv.writer(f, delimiter='\t', lineterminator='\n').writerows(rr)
json.dump({'work': {d['id']: p_ for p_, d in wfiles.items()}, 'book': {d['id']: p_ for p_, d in bfiles.items()},
           'attach': {k: dict(path=v['book']['path'], items=v['items']) for k, v in attaches.items()}},
          open(os.path.join(HERE, 'result2_b%d.json' % A.batch), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已寫')
