#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""車道 wake-c 第三輪：通名大 Work（論語孟子大學中庸四書孝經爾雅）日本刊本窮盡。
流程：c3_harvest.py → c3_cand.py → c3_detail.py → c3_select.py → c3_group.py → 本檔。
用法：build3.py [--apply] [--part 1|2]    part1=前150條、part2=其餘
"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa')); sys.path.insert(0, HERE)
import mintid
from c3_map import core_title
APPLY = '--apply' in sys.argv
PART = int(sys.argv[sys.argv.index('--part') + 1]) if '--part' in sys.argv else 0
TODAY = '2026-11-16'; TAG = '和刻本日本館藏專項第三輪（車道 wake-c，2026-11-16）'
KAN = '〇一二三四五六七八九'
def kn(n):
    n = int(n)
    if n == 1: return '元'
    if n < 10: return KAN[n]
    if n == 10: return '十'
    if n < 20: return '十' + KAN[n - 10]
    return KAN[n // 10] + '十' + (KAN[n % 10] if n % 10 else '')
G = json.load(open(os.path.join(HERE, 'c3_groups.json'))); R = {r['ncid']: r for r in json.load(open(os.path.join(HERE, 'c3_rows.json')))}
DET = json.load(open(os.path.join(HERE, 'c3_det.json'))); MINE = json.load(open(os.path.join(HERE, 'c3_mine_full.json')))
AUTH = {'大學或問': '朱', '中庸或問': '朱', '四書或問': '朱', '孟子或問': '朱', '孝經大義': '董鼎|朱', '古文孝經': '孔', '孝經刊誤': '朱', '四書纂疏': '趙順孫', '孟子趙岐注': '趙', '論語義疏': '皇侃', '御注孝經': '玄宗|李隆基', '孝經注疏': '邢|玄宗'}
SI = {'四書章句集注': {'四書', '四書集注', '[四書集注]', '四書章句集注'}}
sel = []; todo = []
for g in G:
    ct = core_title(g['title'])
    sh = [h for h in g['hits'] if h[2]]
    if sh or g['mine_same']:
        todo.append((g, '疑似庫內已有：' + '、'.join(h[0] for h in (sh or [h for h in g['hits'] if h[0] in g['mine_same']])[:3]) + '（同年同書肆或同Work同年；未再補挂）')); continue
    if re.search(r'補解|補注|增注|增補|新注|補遺', g['cr'] or ''): todo.append((g, '責任者含補解／增注（日人增補衍生本），歸屬Work待定，未建')); continue
    if g['wname'] in AUTH and not re.search(AUTH[g['wname']], (g['cr'] or '') + g['title']): todo.append((g, '責任者與本Work不符（疑為日人同題他書），未建')); continue
    if g['amb']: todo.append((g, '同年同題書肆組合部分重疊（相合版／書肆異寫），並條未能核定，未建')); continue
    if g['wname'] in SI and ct not in SI[g['wname']]: todo.append((g, '四書零種（%s）歸屬哪個Work待定，未建' % ct)); continue
    sel.append(g)
sel.sort(key=lambda g: (g['work'], g['y'], g['shops']))
if PART == 1: sel = sel[:150]
elif PART == 2: sel = sel[150:]
print('可建', len(sel), '待核', len(todo))
def clean_shops(g):
    out = []
    for p in R[g['ncids'][0]]['pubs']:
        for s in re.split(r'\s*[;:；：]\s*', re.sub(r'[\[\]]', '', p)):
            s = re.sub(r'\s*ほか.*$', '', s); s = re.sub(r'\s+', '', s)
            if s and s not in out: out.append(s)
    return out
def edname(g):
    sh = clean_shops(g)
    s = '・'.join(sh[:4]) + ('等' if len(sh) > 4 else '')
    return '日本%s%s年（%d）%s刊本' % (g['reign'], kn(g['n']), g['y'], s)
def title_of(g):
    ct = core_title(g['title'])
    return {'四書章句集注': '四書集註', '論語何晏集解': ('論語集解' if ct == '論語集解' else '論語'), '孟子集注': ('孟子集註' if ct == '孟子集注' else '孟子')}.get(g['wname'], ct)
PAT = re.compile(r'(題簽|見返|版心|序|跋|刊記|奥付|藏版|藏板|訓点|句点|頭注|返り点|送り仮名|書名)')
def notes_of(g):
    ns = []
    for nc in g['ncids']:
        for n in R[nc]['notes']:
            if PAT.search(n) and '印記' not in n and n not in ns and len(n) < 90: ns.append(n)
    return ns[:3]
ids = mintid.mint('Book', 'wake-c', len(sel)) if APPLY else ['dryb%06d' % i for i in range(len(sel))]
sibs = collections.defaultdict(list)
for g, bid in zip(sel, ids): sibs[(g['work'], g['y'])].append(bid)
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
changed = {}; rows = []
for g, bid in zip(sel, ids):
    t = title_of(g); ed = edname(g); sh = clean_shops(g); ext = [e for e in g['ext'] if e]
    prov = []
    for nc in g['ncids']:
        for o in R[nc]['own']:
            prov.append({'institution': o, 'notes': 'CiNii Books所藏館「%s」；%s；%s%s' % (o, R[nc]['title'].split(' ; ')[0].strip(), '・'.join(sh[:4]), ('；' + R[nc]['ext']) if R[nc]['ext'] else ''), 'source': 'CiNii Books https://ci.nii.ac.jp/ncid/%s' % nc})
    seen = set(); prov = [p for p in prov if not ((p['institution'], p['source']) in seen or seen.add((p['institution'], p['source'])))]
    pds = [([x for x in (DET[nc]['pd'] or []) if x] or [''])[0] if isinstance(DET[nc]['pd'], list) else DET[nc]['pd'] for nc in g['ncids']]
    dt = {'era': '日本', 'reign': g['reign'], 'year': g['y'], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books著錄出版項刊年「%s」（NCID %s；非括號推定）' % (pds[0].strip(), g['ncids'][0])}
    cr = re.sub(r'[\[\]]', '', g['cr'] or '').replace('(日本)', '日本').strip()
    nts = notes_of(g)
    txt = '%s%s，日本%s%s年（%d）%s刊。%s%s' % (('%s：' % cr) if cr else '', ('《%s》' % t), g['reign'], kn(g['n']), g['y'], '・'.join(sh[:4]) + ('等' if len(sh) > 4 else ''), ('據CiNii著錄：' + '；'.join(nts) + '。') if nts else '', ('冊數：%s。' % ext[0]) if ext else '')
    others = [b for b in sibs[(g['work'], g['y'])] if b != bid]
    ex = [h[0] for h in g['hits'] if h[0] in MINE and MINE[h[0]].get('work_id') == g['work']]
    note = '%s：據CiNii Books書目新建（NCID %s）；刊年與書肆錄自該書目出版項（非括號推定、非借自他書），未核原書。' % (TAG, '、'.join(g['ncids']))
    if len(g['ncids']) > 1: note += '以上各NCID出版項（刊年、書肆、冊數、訓點者）一致，並為同版；各館藏見見返／藏版有無差異未逐一核對。'
    if others: note += '同Work同年另有他書肆組合之刊本（互注，未核是否同板）：%s。' % '、'.join(others)
    if ex: note += '庫內同Work同年另有：%s（書肆不同或未著錄，未並）。' % '、'.join(ex[:3])
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': t, 'work_id': g['work'], 'edition': ed, 'edition_type': '刻本', 'dating': dt, 'provenance': prov,
         'description': {'text': txt, 'sources': ['CiNii Books https://ci.nii.ac.jp/ncid/%s' % nc for nc in g['ncids']]},
         'sources': [{'id': 'cinii-%s' % nc, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/%s' % nc} for nc in g['ncids']],
         'ai_note': note, 'revision': '1.0.0', 'revised_at': TODAY}
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·・\[\]]', '', ed)[:24]
    changed['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, t, safe)] = d
    rows.append((bid, t, '新建', '; '.join(sorted({p['institution'] for p in prov})), 'https://ci.nii.ac.jp/ncid/%s' % g['ncids'][0], g['work'], ed, '|'.join(g['ncids'])))
print('changed files:', len(changed))
if not APPLY: sys.exit(0)
for p, d in changed.items():
    os.makedirs(os.path.join(ROOT, os.path.dirname(p)), exist_ok=True)
    open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(jd(d))
json.dump(list(changed), open(os.path.join(HERE, 'changed3_%d.json' % PART), 'w'), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, 'ledger3.tsv' if PART < 2 else 'ledger3b.tsv'), 'w', encoding='utf-8') as f:
    f.write('Book id\t題名\t判定\t日本館藏\t依據URL\tWork id\tedition\tNCIDs\n')
    for r in rows: f.write('\t'.join(r) + '\n')
with open(os.path.join(HERE, 'TODO3.tsv'), 'w', encoding='utf-8') as f:
    f.write('Work／題\t年\t書肆\tNCIDs\t原因\n')
    for g, why in todo: f.write('%s %s\t%s\t%s\t%s\t%s\n' % (g['wname'], g['title'].split(' ; ')[0][:20], g['y'], '・'.join(g['shops'])[:50], '|'.join(g['ncids'][:4]), why) + '')
print('已寫')
