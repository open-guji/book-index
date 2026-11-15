#!/usr/bin/env python3
"""十三經縱向補全·丛編成員待辦（無求備齋諸集成）：補建 Work／Book 並挂接 contained_in（車道 a11-sjj-members）。

輸入：../sjj-collections/members-todo.tsv（CiNii 子記錄，含題名、責任者、函冊、底本注記）。
庫內索引：流式讀 git 對象（idx.py 產 pickle，免整庫檢出）；用法：
    build_members.py --idx /path/idx.pkl [--apply]
默認乾跑。判斷口徑見 README.md。
"""
import argparse, collections, csv, datetime, glob, json, os, pickle, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
import mintid
sys.path.insert(0, os.path.join(BI, 'build'))
import v2common as V  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--idx', required=True); ap.add_argument('--apply', action='store_true')
ap.add_argument('--limit', type=int, default=0, help='只取前 N 個 Work 新建／N 個 Book 操作（小樣本）')
ap.add_argument('--only', default='', help='逗號分隔行號，只處理這些行')
A = ap.parse_args()
TODAY = '2026-11-15'
LANE = 'a11-sjj-members'
IDS = json.load(open(os.path.join(BI, '.claude/qa/sjj-collections/ids.json'), encoding='utf-8'))
COLL = {'無求備齋論語集成': 'lunyu', '無求備齋老子集成初編': 'laozi1', '無求備齋老子集成續編': 'laozi2', '無求備齋孟子十書': 'mengzi10', '無求備齋老列莊三子集成補編': 'laolie'}
ROOT = {'lunyu': 'd59f1iopaku8', 'laozi': 'd59ezkx8dt6o', 'mengzi': 'd59ezajwvda8', 'zhuang': 'd59fy1y0aqde', 'lie': 'd59ezahwgb9c'}
EDO = '江戶時代'; JP = '日本'
EDO_ERA = '寬永 正保 慶安 承應 明曆 萬治 寬文 延寶 天和 貞享 元祿 寶永 正德 享保 元文 寬保 延享 寬延 寶曆 明和 安永 天明 寬政 享和 文化 文政 天保 弘化 嘉永 安政 萬延 文久 元治 慶應 '.split()
# 人名 → 朝代（人工；其餘取庫內 Entity 唯一匹配）
NAME_DYN = {'楊德崇': '民國', '宋翔鳳': '清', '黃奭': '清', '嚴靈峯': '民國', '袁鈞': '清', '馬國翰': '清', '王謨': '清', '江帆': '清', '朴世堂': '朝鮮', '陳繼儒': '明',
            '楊起元': '明', '魏徵': '唐', '葉玉麟': '民國', '勞健': '民國', '劉咸炘': '民國', '胡遠濬': '清', '陳柱': '民國', '黃元炳': '民國', '徐紹楨': '清', '劉師培': '清',
            '劉國鈞': '民國', '顧錫疇': '明', '潘基慶': '明', '張洪陽': '明', '陳觀吾': '清', '奚侗': '民國', '區大典': '民國', '徐永祐': '清', '郭乾泗': '清', '馬敍倫': '民國',
            '阮毓崧': '民國', '沈汝紳': '明', '鄒之嶧': '明', '楊伯峻': ''}
# row → (根鍵, 關係)；C=contains_text_of  S=studies
NEW = {12: ('lunyu', 'S'), 17: ('lunyu', 'S'), 21: ('lunyu', 'C'), 37: ('lunyu', 'S'), 6: ('lunyu', 'S'), 20: ('lunyu', 'C'), 23: ('lunyu', 'C'), 48: ('lunyu', 'S'),
       19: ('lunyu', 'C'), 30: ('lunyu', 'C'), 107: ('lunyu', 'C'),
       153: ('laozi', 'C'), 154: ('laozi', 'C'), 163: ('laozi', 'C'), 164: ('laozi', 'C'), 181: ('laozi', 'C'), 248: ('laozi', 'C'), 249: ('laozi', 'C'), 270: ('laozi', 'C'), 273: ('laozi', 'C'),
       344: ('laozi', 'C'), 346: ('laozi', 'S'), 356: ('laozi', 'S'), 360: ('laozi', 'C'), 363: ('laozi', 'S'), 365: ('laozi', 'C'), 366: ('laozi', 'C'), 370: ('laozi', 'C'),
       382: ('laozi', 'C'), 423: ('laozi', 'S'), 438: ('laozi', 'S'), 160: ('laozi', 'C'), 168: ('laozi', 'C'), 205: ('laozi', 'C'), 214: ('laozi', 'C'), 287: ('laozi', 'C'),
       288: ('laozi', 'C'), 290: ('laozi', 'C'), 294: ('laozi', 'C'), 295: ('laozi', 'C'), 297: ('laozi', 'C'), 299: ('laozi', 'C'), 303: ('laozi', 'C'), 312: ('laozi', 'C'),
       313: ('laozi', 'C'), 319: ('laozi', 'C'), 320: ('laozi', 'C'), 327: ('laozi', 'C'), 328: ('laozi', 'C'), 332: ('laozi', 'C'), 375: ('laozi', 'C'), 435: ('laozi', 'C'),
       440: ('laozi', 'C'), 443: ('laozi', 'C'),
       469: ('zhuang', 'C'), 476: ('zhuang', 'C'), 477: ('zhuang', 'S'), 479: ('zhuang', 'C'), 486: ('zhuang', 'C'), 492: ('zhuang', 'C'), 493: ('zhuang', 'C'), 502: ('lie', 'C')}
# 判為同書、改指庫內既有 Work 的行（題名異體／署名異寫，人工核過）
EXIST_MAP = {5: 'd59f2q3r7e2p', 118: 'd59gdtwu05q9', 9: 'd59fxrc34t8g', 10: 'd59fxrc34t8h', 31: 'd59gdtwu05qo', 42: 'd59f2mrceg3l', 93: 'd59fy84q48w2', 95: 'd59fy9x2kc1u',
             123: 'd59fy3teb1mp', 167: 'd59fxycjb6dd', 222: 'd59fxyy14gzl', 237: 'd59fxwdw8su9', 239: 'd59fydxce03k', 321: 'd59fxycjmeww', 466: 'd59fxrcdqvpc',
             481: 'd59f2q8d9n28', 501: 'd59f2hqot2bn', 265: 'd59gduogi8lu', 300: 'd59gduogi8mh', 307: 'd59gduogi8mn', 442: 'd59gduogi8ok', 450: 'd59gduogi8oo'}
HOLD_ROWS = {9: '庫內已有春暉樓叢書上集本，疑與「春暉堂叢書」同版，不重建', 10: '庫內已有春暉樓叢書上集本，疑與「春暉堂叢書」同版，不重建'}
CINII = lambda n: {'id': n, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + n}
REL = {'C': 'contains_text_of', 'S': 'studies'}
PERIOD = {'明': 'ming', '清': 'qing', '民國': 'modern', '唐': 'sui-tang', '宋': 'song', '南宋': 'song'}

I = pickle.load(open(A.idx, 'rb'))
res = pickle.load(open(os.path.join(os.path.dirname(A.idx), 'res.pkl'), 'rb'))
rows = list(csv.reader(open(os.path.join(BI, '.claude/qa/sjj-collections/members-todo.tsv'), encoding='utf-8'), delimiter='\t'))
HEAD, rows = rows[0], rows[1:]
BW = collections.defaultdict(list)
for b in I['Book']:
    if not b['mg']: BW[b['wid']].append(b)
WID = {w['id']: w for w in I['Work']}
WNORM = collections.defaultdict(list)
for w in I['Work']:
    if not w['mg']: WNORM[norm(w['title'])].append(w)
ENT = collections.defaultdict(list)
for e in I['Entity']:
    if not e['mg']: ENT[nname(e['name'])].append((e['id'], e['dyn']))
ONLY = {int(x) for x in A.only.split(',') if x}
D = {x['row']: x for x in res}
log = []   # (row, action, detail)
def L(row, act, det=''): log.append((row, act, det))

def vol_of(x):
    v = x['vol'] or ''
    m = re.search(r'第\s*(\d+(?:\s*[-—ー]\s*\d+)?)\s*函', v + ' ' + x['note'])
    if m and COLL[x['coll']] != 'laolie': return '第%s函' % re.sub(r'\s', '', m.group(1))
    if COLL[x['coll']] == 'laolie' and re.match(r'^[\d\-, ]+$', v): return '第%s冊' % re.sub(r'\s', '', v)
    return None
def edo(bases):
    return any(e in b for b in bases for e in EDO_ERA)
def etype(b):
    if re.search(r'活字', b): return '活字本'
    if re.search(r'石印', b): return '石印本'
    if re.search(r'套印', b): return '套印本'
    if re.search(r'鈔|抄|寫本', b): return '抄本'
    if re.search(r'排印|鉛印', b): return '鉛印本'
    if re.search(r'刊|刻|版', b): return '刻本'
    return None

# ---------------------------------------------------------------- Work 新建
groups = collections.OrderedDict()
for r in sorted(NEW):
    if ONLY and r not in ONLY: continue
    x = D[r]; t = disp(x['title']); key = (norm(t), tuple(disp(a[0]) for a in x['aus']))
    groups.setdefault(key, []).append(r)
if A.limit: groups = collections.OrderedDict(list(groups.items())[:A.limit])
ids = mintid.mint('Work', LANE, len(groups)) if A.apply else ['dry%08d' % i for i in range(len(groups))]
newwork = {}   # row → work id
pairs = []
wfiles = {}
for (key, rs), wid in zip(groups.items(), ids):
    r0 = rs[0]; x = D[r0]; rk, rel = NEW[r0]; t = disp(x['title'])
    bases = [disp(b) for r in rs for b in bases_of(D[r]['note'])]
    al = []
    for n, role, hint in x['aus']:
        n = disp(n)
        dyn = NAME_DYN.get(n)
        if n not in NAME_DYN:
            dyn = EDO if edo(bases) else JP
        a = {'name': n, 'role': role}
        if dyn: a['dynasty'] = dyn
        ok = {dyn} | ({'中華民國'} if dyn == '民國' else set()) | ({'日本'} if dyn in (EDO, JP) else set())
        c = [e for e in ENT.get(nname(n), []) if e[1] in ok]
        if len(c) == 1 and len(ENT.get(nname(n), [])) == 1 and dyn not in (EDO, JP): a['entity_id'] = c[0][0]
        al.append(a)
    dyn0 = al[0].get('dynasty')
    near = [w for w in WNORM.get(norm(t), [])]
    ncid = ';'.join(D[r]['ncid'] for r in rs)
    note = ('2026-11-15 十三經縱向補全（無求備齋成員補建）：據 CiNii Books 子記錄 %s（%s・%s）著錄，庫內無同題同撰人 Work 而新建。'
            '題名、責任者、朝代取自該目，未覆核原書；責任者未逐一考證' % (ncid, D[r0]['coll'], vol_of(D[r0]) or '')) + \
           ('；庫內另有同題異撰人 Work %s，非同書另立' % '、'.join(w['id'] for w in near[:6]) if near else '') + \
           ('；朝代為推定：日本人，生年不詳' if dyn0 in (JP,) else '') + '。'
    d = {'schema_version': 1, 'id': wid, 'type': 'work', 'title': t, 'authors': al}
    if dyn0: d['dynasty'] = dyn0
    d['related_works'] = [{'id': ROOT[rk], 'relation': REL[rel]}]
    d['sources'] = [CINII(D[r]['ncid']) for r in rs]
    d['ai_note'] = note; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    if r0 == 502:
        d['period'] = 'modern'; d['period_basis'] = '撰人楊伯峻（1909—1992），《列子集釋》初版於 1958 年，著錄本為 1979 年增訂排印本'
    elif dyn0 == EDO:
        d['period_upper'] = 'qing'; d['period_upper_basis'] = '撰人為日本江戶時代人，與清並行；歧而未決，無論何解皆不晚於 qing'
    elif dyn0 == '朝鮮':
        d['period_upper'] = 'qing'; d['period_upper_basis'] = '撰人朴世堂（1629—1703）為朝鮮人，無論何解皆不晚於 qing'
    elif dyn0 in PERIOD:
        d['period'] = PERIOD[dyn0]; d['period_basis'] = '據 authors[0].dynasty「%s」' % dyn0
    for r in rs: newwork[r] = wid
    pth = 'Work/%s/%s/%s/%s-%s.json' % (wid[-3], wid[-2], wid[-1], wid, t)
    wfiles[pth] = d
    for w in near: pairs.append((wid, w['id'], '無求備齋成員補建：同題異撰人另立（%s／%s），非同書' % ('、'.join(a['name'] for a in al), '、'.join(a[0] for a in w['au']) or '未署')))
    L(r0, 'NEW-Work', '%s %s %s' % (wid, t, [a['name'] for a in al]))
# 同批同題
bt = collections.defaultdict(list)
for pth, d in wfiles.items(): bt[norm(d['title'])].append(d)
for k, v in bt.items():
    for i in range(len(v)):
        for j in range(i + 1, len(v)): pairs.append((v[i]['id'], v[j]['id'], '無求備齋成員補建：同批同題異撰人'))

# ---------------------------------------------------------------- Book 操作
bfiles = {}; attaches = {}; held = {}
bids_needed = []
ops = []
for x in res:
    r = x['row']
    if ONLY and r not in ONLY: continue
    st = x['st']
    if st == '已挂': continue
    if r in HOLD_ROWS: held[r] = HOLD_ROWS[r]; continue
    if x['comp']: held[r] = '合冊著錄（一條 CiNii 記錄含多書），暫不拆'; continue
    ck = COLL[x['coll']]; cid = IDS[ck]
    vol = vol_of(x)
    if r in newwork: wids = [newwork[r]]; mode = 'create'
    elif r in EXIST_MAP: wids = [EXIST_MAP[r]]; mode = 'create' if st == '庫內無Work' else 'attach'
    elif st == '庫內無Work' and x['same']: wids = [h[0] for h in x['same']]; mode = 'create'
    elif st.startswith('Work已有') or (st == '僅同題異作者' and x['same']):
        wids = [w for w in rows[r - 2][6].split(';') if w] or [h[0] for h in x['same']]; mode = 'attach'
    else:
        held[r] = {'庫內無Work': '近似題名／署名不明／屬他書分卷或版本層，不另立', '僅同題異作者': '同題異作者，異書另立證據不足或屬版本層'}.get(st, '待判'); continue
    if r in newwork and r not in D: continue
    bases = list(dict.fromkeys(disp(b) for b in bases_of(x['note'])))
    if len(bases) != 1:
        held[r] = '底本%s' % ('未載' if not bases else '多於一種，無法對應'); continue
    base = bases[0]
    if not usable(base):
        held[r] = '底本注記不足以認定版本（%s）' % base; continue
    if len(wids) > 1:
        held[r] = '庫內有多個同題同撰人 Work（%s），不定對應' % ','.join(wids); continue
    wid = wids[0]
    bs = BW.get(wid, [])
    sc = sorted(((ed_match(base, b['ed']), b) for b in bs), key=lambda t: -t[0])
    strong = [b for s, b in sc if s >= 0.9]
    if mode == 'attach' or strong or (sc and sc[0][0] >= 0.3):
        if len(strong) == 1:
            b = strong[0]
            if any(c['id'] == cid for c in (b['ci'] or [])): held[r] = '已挂'; continue
            attaches.setdefault(b['id'], dict(book=b, items=[]))['items'].append(dict(collection=cid, volume_index=vol, ncid=x['ncid'], row=r))
            L(r, 'ATTACH', '%s %s' % (b['id'], b['ed']))
        elif mode == 'attach': held[r] = '注記底本「%s」與庫內 Book.edition %s' % (base, '無吻合' if not strong else '吻合不止一個')
        else: held[r] = '庫內已有近似版本 Book（%s），不重建' % '；'.join('%s:%s' % (b['id'], b['ed']) for s, b in sc[:2])
        continue
    ops.append((r, wid, base, ck, cid, vol, x))
if A.limit: ops = ops[:A.limit]
bids = mintid.mint('Book', LANE, len(ops)) if A.apply else ['dryb%06d' % i for i in range(len(ops))]
for (r, wid, base, ck, cid, vol, x), bid in zip(ops, bids):
    wtitle = (wfiles and next((d['title'] for d in wfiles.values() if d['id'] == wid), None)) or WID[wid]['title']
    cname = x['coll']; vtxt = vol or ''
    edition = '%s（%s影印%s）' % (base, cname, '，' + vtxt if vtxt else '')
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': wtitle, 'work_id': wid, 'edition': edition}
    et = etype(base)
    if et: d['edition_type'] = et
    d['sources'] = [CINII(x['ncid'])]
    d['ai_note'] = ('2026-11-15 十三經縱向補全（無求備齋成員補建）：據 CiNii Books 子記錄 %s 著錄，影印底本為「%s」，%s%s影印本。'
                    '底本信息取自 CiNii 注記，未核原書；CiNii 題名作「%s」' % (x['ncid'], base, cname, ('（%s）' % vtxt) if vtxt else '', clean_title(x['raw'])))
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    ci = {'id': cid}
    if vtxt: ci['volume_index'] = vtxt
    d['contained_in'] = [ci]
    fn = '%s-%s%s.json' % (bid, wtitle, re.sub(r'[\\/:*?"<>|（）() ,，;；]', '', base)[:24])
    bfiles['Book/%s/%s/%s/%s' % (bid[-3], bid[-2], bid[-1], fn)] = d
    L(r, 'NEW-Book', '%s %s' % (bid, edition))

# ---------------------------------------------------------------- 輸出
cnt = collections.Counter(a for _, a, _ in log)
print('Work 新建', len(wfiles), 'Book 新建', len(bfiles), '既有 Book 挂接', sum(len(v['items']) for v in attaches.values()), '擱置', len(held))
for r, a, dd in log[:400]: print(r, a, dd)
for r, why in sorted(held.items()): print('HELD', r, D[r]['title'], '|', why)
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
    ci = d.setdefault('contained_in', [])
    for it in v['items']:
        if any(c['id'] == it['collection'] for c in ci): continue
        item = {'id': it['collection']}
        if it['volume_index']: item['volume_index'] = it['volume_index']
        ci.append(item)
    x_, y_, z_ = (int(t) for t in (d.get('revision') or '1.0.0').split('.')); d['revision'] = '%d.%d.0' % (x_, y_ + 1); d['revised_at'] = TODAY
    open(p, 'w', encoding='utf-8').write(V.dump(d, fmt))
with open(os.path.join(BI, '.claude/qa/dedup-judged/無求備齋成員補建.tsv'), 'w', encoding='utf-8') as f:
    f.write('# 十三經縱向補全·無求備齋成員補建：同題異撰人另立，非重出（C）\n')
    for a, b, why in pairs: f.write('%s\t%s\tC\t%s\n' % (a, b, why))
json.dump({'work': {d['id']: p for p, d in wfiles.items()}, 'book': {d['id']: p for p, d in bfiles.items()}, 'attach': {k: dict(path=v['book']['path'], items=v['items']) for k, v in attaches.items()},
           'held': {str(k): v for k, v in held.items()}},
          open(os.path.join(HERE, 'result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
rowlog = {}
NAMES = {'NEW-Work': '新建 Work', 'NEW-Book': '新建 Book 並挂入丛編', 'ATTACH': '挂入既有 Book'}
def rl(r): return rowlog.setdefault(str(r), {'acts': [], 'idl': []})
for r, a_, dd in log:
    rl(r)['acts'].append(NAMES[a_]); rl(r)['idl'].append(dd.split(' ')[0])
for r, wid in newwork.items():
    e = rl(r)
    if '新建 Work' not in e['acts']: e['acts'].insert(0, '新建 Work'); e['idl'].insert(0, wid)
for r, why in held.items(): rl(r)['acts'].append('未處理：' + why)
for e in rowlog.values(): e['act'] = '；'.join(e.pop('acts')); e['ids'] = ' / '.join(e.pop('idl'))
json.dump(rowlog, open(os.path.join(HERE, 'rowlog.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已寫')
