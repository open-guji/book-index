#!/usr/bin/env python3
"""獨撰子目补撰人：规划（只读）。
    python3 .claude/qa/dedup-duzhuan/plan.py OUT_DIR [--skip-ids FILE ...]
总目「叢書部/獨撰類」子目 Work 不署撰人；按所属 Collection 的撰者补 authors。
输出 OUT_DIR/plan.json（可补条目）、held.tsv（不补，附理由）、stats.json。"""
import argparse, collections, glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import jio  # noqa: E402
from scan import VARIANTS  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'entity-governance-1025'))
from dyn import rel, coarse, idx  # noqa: E402
import opencc  # noqa: E402
T2S = opencc.OpenCC('t2s')
EXTRA = str.maketrans('髙寜啓啟爲衆敎峯煕熈彜彞', '高寧启启为众教峰熙熙彝彝')
_wc = {}
def wide(s):
    if s not in _wc: _wc[s] = T2S.convert(s).translate(EXTRA)
    return _wc[s]

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--skip-ids', nargs='*', default=[])
ap.add_argument('--reviewed', nargs='*', default=[], help='逐条复核表（work_id、判定、名、责任方式、朝代、理由）；判「补」者绕过剔除规则，照表写')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
R = jio.ROOT
def rp(p): return os.path.relpath(p, R)
def nm(s): return re.sub(r'\s', '', (s or '')).translate(VARIANTS)
TCORE = re.compile(r'[（(][^）)]*[）)]')
def tkey(t): return nm(TCORE.sub('', t or ''))

# 1. Collection（按源记录号）
col = {}
for p in glob.glob(R + '/Collection/*/*/*/*.json'):
    c = json.load(open(p))
    if c.get('merged_into'): continue
    for s in c.get('sources') or []:
        if s.get('id'): col[s['id']] = (rp(p), c)
print('载入 Collection', len(col), file=sys.stderr)
assert col

# 2. 人物 Entity（活的）及其名字
ent = {}; ename = collections.defaultdict(set)
for p in glob.glob(R + '/Entity/*/*/*/*.json'):
    d = json.load(open(p))
    if d.get('subtype') != 'people' or d.get('merged_into'): continue
    ent[d['id']] = d
    ename[nm(d.get('primary_name'))].add(d['id'])
    for x in d.get('alt_names') or []:
        n = x.get('name') if isinstance(x, dict) else x
        if n: ename[nm(n)].add(d['id'])
print('载入人物 Entity', len(ent), file=sys.stderr)
assert ent

# 3. Work：候选与同题索引、名→entity
P = re.compile(r'所屬叢書記錄 ([0-9a-z]+)（(.*?)）')
cands = []; bytitle = collections.defaultdict(list); name_ent = collections.defaultdict(lambda: collections.defaultdict(set))
for p in glob.glob(R + '/Work/*/*/*/*.json'):
    w = json.load(open(p))
    if w.get('merged_into'): continue
    aus = [x for x in w.get('authors') or [] if (x.get('name') or '').strip()]
    if aus:
        bytitle[tkey(w.get('title'))].append((w['id'], [(nm(x['name']), x.get('dynasty'), x.get('entity_id')) for x in aus]))
        for x in aus:
            if x.get('entity_id') in ent: name_ent[nm(x['name'])][x['entity_id']].add(x.get('dynasty') or '')
        continue
    ib = w.get('indexed_by') or []
    if not any('獨撰類' in (x.get('section') or '') for x in ib): continue
    m = P.search(w.get('ai_note') or '')
    per = [x.get('section').split('/')[-1] for x in ib if '獨撰類' in (x.get('section') or '')][0]
    cands.append(dict(per=per, id=w['id'], path=rp(p), title=w.get('title'), rec=m.group(1) if m else None,
                      colname=m.group(2) if m else None, ai=[x.get('author_info') for x in ib if x.get('author_info')],
                      revision=w.get('revision')))
print('载入候选', len(cands), file=sys.stderr)
assert cands

skip = set()
for f in a.skip_ids:
    for l in open(f):
        l = l.strip()
        if l: skip.add(l.split()[0])
a4 = json.load(open(R + '/.claude/qa/dedup-part4/候选/4a-alpha-3c74b458.json'))
skip4a = set()
for g in a4: skip4a.add(g['keeper']); skip4a.update(g['losers'])

ZHUAN = {'撰', '著', '撰著', '著述', '述', '作'}
COPY_T = re.compile(r'[鈔抄]|祕笈|秘笈|選本|彙[編刻]|輯[佚本]|佚書')
JUNK_T = re.compile(r'^(卷?首|目錄|總目|序|附|附刻|補遺|續編|外編|別錄|雜著|首卷)$|^(宋|元|明|清|民國)\S*年|年\S*[刻印]$|^陽刻$')
SUBCOPY_T = re.compile(r'酬贈|投贈|贈答|評論|逸事|^附後$|條款|條約|倡和|唱和|摘|雜鈔|抄錄|彙鈔|叢鈔|輯要|先生\S*(言行|雜錄|外錄|見聞)')
# 子目所在时段（section 末段）可容的撰者朝代（粗朝代）
PERIOD_OK = {'民國以來': {'清', '民國'}, '清代後期': {'清', '民國'}, '清代前期': {'明', '清'}, '明代': {'元', '明'}}
LATE = {'明', '清', '民國'}
BIO_T = re.compile(r'年譜|行狀|行述|行實|行略|墓誌|墓表|神道碑|事略|事狀|家傳|別傳|傳略|附錄|祭文|輓|挽[詩詞聯]|誄|哀[辭詞]|題詞|贈言|壽[言序詩]|紀念|遺事|祠記|褒榮|恩榮|誥[命敕]')

BRK = re.compile(r'［([^］]*[校補注][^］]*)］')
def brole(t):
    # 題名帶「［校正］」「［校補］」等（羣書拾補之類）：是撰者對他書的校補，責任方式照括注
    m = BRK.search(t or '')
    return m.group(1) if m else '撰'

plan = []; held = []
reviewed = {}
for f in a.reviewed:
    for l in open(f):
        r = l.rstrip('\n').split('\t')
        if len(r) >= 5 and r[1] == '补' and r[2].strip(): reviewed[r[0]] = dict(name=r[2].strip(), role=r[3].strip() or '撰', dynasty=r[4].strip(), why=r[5].strip() if len(r) > 5 else '')

def entity_for(n, dy, ev_ent):
    if len(ev_ent) == 1:
        e = next(iter(ev_ent))
        if rel(dy, ent[e].get('dynasty')) in ('same', 'unk'): return e, '同题同名他书已挂'
    es = name_ent.get(n, {})
    if len(es) == 1 and len(ename.get(n, ())) <= 1:
        e = next(iter(es))
        ok = all(rel(dy, d) in ('same', 'unk') for d in es[e] | {ent[e].get('dynasty') or ''})
        if ok and (not ename.get(n) or e in ename[n]): return e, '全库该名唯一人物'
    return None, None

def same_title(c, n):
    same = diff = 0; ev_ent = set(); others = []
    for wid, al in bytitle.get(tkey(c['title']), []):
        if wide(n) in {wide(x[0]) for x in al}:
            same += 1; ev_ent |= {x[2] for x in al if wide(x[0]) == wide(n) and x[2] in ent}
        else:
            diff += 1; others.append((wid, al))
    return same, diff, ev_ent, others

def hold(c, why, extra=''):
    held.append((c['id'], c['title'], c['colname'] or '', why, extra))
for c in cands:
    if c['id'] in skip: hold(c, '跳过-开着的PR'); continue
    if c['id'] in skip4a: hold(c, '跳过-4a-α清单'); continue
    if c['ai']: hold(c, 'H-子目自带著者', ' | '.join(c['ai'])); continue
    cc = col.get(c['rec'])
    if not cc: hold(c, 'H-找不到Collection'); continue
    cpath, cd = cc
    rv = reviewed.get(c['id'])
    if rv:
        n = nm(rv['name']); same, diff, ev_ent, _ = same_title(c, n); eid, basis = entity_for(n, rv['dynasty'], ev_ent)
        au = dict(name=rv['name'], role=rv['role'], dynasty=rv['dynasty'])
        plan.append(dict(id=c['id'], path=c['path'], title=c['title'], revision=c['revision'],
                         col_id=cd['id'], col_title=cd.get('title'), col_path=cpath, author=au, col_role=None,
                         entity_id=eid, entity_basis=basis, same_title_same_author=same, mixed_title=bool(diff), reviewed=rv['why']))
        continue
    caus = [x for x in cd.get('authors') or [] if (x.get('name') or '').strip()]
    if not caus: hold(c, 'H-丛书无撰人'); continue
    if caus[0].get('role') not in ZHUAN:
        hold(c, 'X-丛书首位非撰(%s)' % caus[0].get('role'), caus[0]['name']); continue
    zh = [x for x in caus if x.get('role') in ZHUAN]
    if len({nm(x['name']) for x in zh}) > 1:
        hold(c, 'H-丛书多撰者', '、'.join(x['name'] for x in zh)); continue
    au = zh[0]; n0 = nm(au['name']); dy = au.get('dynasty') or ''
    n = n0   # 照丛书著录写名，不改写（於／于等繁简同形者可能是两姓）
    if not re.fullmatch(r'[㐀-鿿\U00020000-\U0002ffff]{2,8}', au['name']) or re.search(r'[□氏等]$', au['name']):
        hold(c, 'H-撰者名异常', au['name']); continue
    if COPY_T.search(cd.get('title') or ''): hold(c, 'H-丛书题名似钞辑', cd.get('title')); continue
    if JUNK_T.match(nm(c['title'])): hold(c, 'H-题名为卷次泛称'); continue
    if BIO_T.search(c['title'] or ''): hold(c, 'H-题名似传记附录'); continue
    if SUBCOPY_T.search(c['title'] or ''): hold(c, 'H-题名似钞辑摘录'); continue
    cd_ = coarse(dy)
    if cd_ and ((c['per'] in PERIOD_OK and cd_ not in PERIOD_OK[c['per']]) or (c['per'] == '明代以前' and cd_ in LATE)):
        hold(c, 'H-撰者朝代与子目时段不合', '%s/%s' % (c['per'], dy)); continue
    # 同题他书
    same, diff, ev_ent, others = same_title(c, n)
    if diff and not same:
        ci = idx(coarse(dy))
        early = any(idx(coarse(x[1])) is not None and ci is not None and idx(coarse(x[1])) < ci for _, al in others for x in al)
        txt = '; '.join(wid + ':' + '、'.join(sorted({x[0] + '/' + (x[1] or '') for x in al})) for wid, al in others[:6])
        hold(c, 'H-同题他书撰人更早(疑辑注钞)' if early else 'H-同题他书撰人不同(同代或后)', txt); continue
    eid, basis = entity_for(n, dy, ev_ent)
    plan.append(dict(id=c['id'], path=c['path'], title=c['title'], revision=c['revision'],
                     col_id=cd['id'], col_title=cd.get('title'), col_path=cpath,
                     author=dict(name=au['name'], role=brole(c['title']), dynasty=dy), col_role=au.get('role'),
                     entity_id=eid, entity_basis=basis, same_title_same_author=same, mixed_title=bool(diff)))

json.dump(plan, open(a.out + '/plan.json', 'w'), ensure_ascii=False, indent=1)
with open(a.out + '/held.tsv', 'w') as f:
    f.write('work_id\t题名\t丛书\t理由\t附注\n')
    for h in held: f.write('\t'.join(h) + '\n')
st = dict(候选=len(cands), 可补=len(plan), 挂entity=sum(1 for x in plan if x['entity_id']),
          entity依据=collections.Counter(x['entity_basis'] for x in plan if x['entity_id']),
          同题同人佐证=sum(1 for x in plan if x['same_title_same_author']),
          不补=collections.Counter(re.sub(r'\(.*', '', h[3]) for h in held))
json.dump(st, open(a.out + '/stats.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(st, ensure_ascii=False, indent=1))
