#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-d 第三輪 PR #2848 復抽修正：拆簇、併重、補注。一次性腳本。"""
import json, os, re, subprocess, sys, copy
ROOT = '/tmp/wk-wake-d3'; HERE = ROOT + '/.claude/qa/wake-d'
sys.path.insert(0, ROOT + '/.claude/qa'); sys.path.insert(0, HERE)
import mintid, wk3lib as L
CI = 'https://ci.nii.ac.jp/ncid/'; TODAY = '2026-11-16'
def sh(*a): return subprocess.run(a, capture_output=True, cwd=ROOT).stdout
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def gitshow(p): return json.loads(sh('git', '-c', 'core.quotepath=false', 'show', ':' + p))
P = json.load(open('/tmp/wk_d3_paths.json'))
D = {k: gitshow(p) for k, p in P.items()}
PATH = dict(P)
DEL = []
def nc(s): return s.rsplit('/', 1)[1]
def pid(d): return d['id']
def move(src, dst, ncids=None):
    """把 src 的來源／館藏（限 ncids，缺省全部）併入 dst。"""
    S, T = D[src], D[dst]
    have = {nc(x['details']) for x in T['sources']}
    for s in list(S['sources']):
        n = nc(s['details'])
        if ncids and n not in ncids: continue
        if n not in have: T['sources'].append(s); T['description']['sources'].append('CiNii Books ' + CI + n)
        if ncids: S['sources'].remove(s); S['description']['sources'].remove('CiNii Books ' + CI + n)
    for pv in list(S.get('provenance', [])):
        n = nc(pv['source'])
        if ncids and n not in ncids: continue
        T.setdefault('provenance', []).append(pv)
        if ncids: S['provenance'].remove(pv)
    if ncids and not S.get('provenance'): S.pop('provenance', None)
def note(k, t): D[k]['ai_note'] += t
def addpub(k, *ps):
    cur = D[k]['publication_info']['publisher'].split('、')
    for p in ps:
        if p not in cur: cur.append(p)
    D[k]['publication_info']['publisher'] = '、'.join(cur)
def drop(k):
    DEL.append(k)

# 1 b2a 混入 BB1791069X → b2b
move('b2a', 'b2b', {'BB1791069X'})
note('b2a', '復抽修正：原誤併之 BB1791069X（頁面為野田氏寛保3[1743]校本）已移出，歸 99jv424b2b。')
note('b2b', '復抽修正：自 99jv424b2a 移入 BB1791069X（出版者野田太兵衞、野田弥兵衞，萬治2[1659]刊本之寛保3[1743]校印）。')

# 2 唐鑑：b2y、b34 → b33；b32 → b31
move('b2y', 'b33'); addpub('b33', '河内屋勘助')
note('b33', '復抽修正：併入 99jv424b2y（BB23965073，CiNii 出版事項著錄天保14[1843]河内屋勘助等，但見返し為「萬延元年庚申秋補刻、浪華書林文金堂寳巖堂製本」，與本條同為萬延元年補刻印次，年份書肆衝突，以見返し為準；天保14原刻是否另有獨立印次待考）與 99jv424b34（BB12143695，大阪河内屋勘助，見返し與本條完全相同）。')
drop('b2y'); drop('b34')
move('b32', 'b31'); addpub('b31', '出雲寺萬次郎')
note('b31', '復抽修正：併入 99jv424b32（出雲寺萬次郎，BB18304185 等）；天保十年刊、嘉永六年重刊為同一官版（昌平坂學問所版），出雲寺為發賣書肆，不另立。')
drop('b32')
note('b2w', '弱疑：與 99jv424b2x（唐本屋清兵衞）刊記同文，可能為同版異書肆印次，待核，暫並列。')
note('b2x', '弱疑：與 99jv424b2w（風月荘左衞門）刊記同文，可能為同版異書肆印次，待核，暫並列。')

# 3 資治通鑑：b3l→b3j；b3i→b3g；史記評林 b2s→b2r
move('b3l', 'b3j'); note('b3j', '復抽修正：併入 99jv424b3l（BA54200346，著錄明治17[1884]鳳文館），同為鳳文館294巻首1巻一部，不另立。'); drop('b3l')
move('b3i', 'b3g'); note('b3g', '復抽修正：併入 99jv424b3i（BB08679680，著錄嘉永2[1849]山形屋傳右衞門、雲出屋伊十郎等）；有造館藏版，BA9095212X 帶嘉永2跋，為同版後印，不另立。'); drop('b3i')
move('b2s', 'b2r'); addpub('b2r', '豐田宇左衞門')
note('b2r', '復抽修正：併入 99jv424b2s（BA54149056，豐田宇左衞門）；其 NCID 頁「他の出版者：豊田宇左衛門」，封面浪華五書房合梓，同一印次，不另立。'); drop('b2s')

# 4 b3c 明曆3→明曆4（跋「明曆戊戌」=1658）
d = D['b3c']
d['edition'] = '日本明曆四年松栢堂時元林和泉掾刊本'
d['dating'].update(year=1658, basis='跋「書漢志後（明曆戊戌桃林軒玄朴誌）」，戊戌＝1658（明曆4，同年七月改元萬治）；CiNii Books BB0791677X、BB04869072 著錄明曆4[1658]，BA85581186 等著錄出版者松栢堂時元林和泉掾、明曆3[1657]')
d['description']['text'] = d['description']['text'].replace('明曆3[1657]', '明曆3[1657]（CiNii 著錄；跋作明曆戊戌即1658）')
note('b3c', '復抽修正：原據 CiNii BA85581186 等著錄「明曆3[1657]」，但跋署「明曆戊戌」（1658，明曆4），書不能早於其跋，改定為1658；同書另有 CiNii BB0791677X、BB04869072 著錄明曆4[1658]，書肆松栢堂林和泉掾，未併入來源，待核是否同一印次。')

# 5 b37 拆簇：柳原積玉圃組另立
a = D['b37']; b = copy.deepcopy(a)
keepA = {'BB00850946'}; keepB = {'BA81790628', 'BB00838601'}
for X, keep in ((a, keepA), (b, keepB)):
    X['sources'] = [s for s in X['sources'] if nc(s['details']) in keep]
    X['provenance'] = [s for s in X['provenance'] if nc(s['source']) in keep]
    X['description']['sources'] = ['CiNii Books ' + CI + n for n in (nc(s['details']) for s in X['sources'])]
bid = mintid.mint('Book', 'wake-d', 1)[0]
b['id'] = bid; b['revised_at'] = TODAY
b['edition'] = '日本文化七年柳原積玉圃刊本'
b['publication_info'] = {'publisher': '柳原積玉圃、河内屋喜兵衞', 'place': '浪華[大阪]'}
b['dating']['basis'] = 'CiNii Books BB00838601 著錄出版者柳原積玉圃、河内屋喜兵衞、文化7[1810]牋刊；BA81790628 著錄柳原積玉圃、文化7[1810]'
b['description']['text'] = ('(呉)韋昭解;(宋)宋庠補音;(日本)秦鼎校。出版者：柳原積玉圃、河内屋喜兵衞；文化7[1810]牋刊。CiNii 著錄：6冊。'
    'CiNii 注記：見返し題:春秋外傳國語定本；見返しに「文化己巳春日新鐫」とあり；「上國語定本牋」に「文化七年庚午四月 儒官臣 秦鼎上牋」とあり；「國語定本跋」に「文化六年己巳夏六月 尾張 神野世猷識」とあり；'
    '奥付に江戸書肆（須原屋茂兵衞、須原屋伊八、岡田屋嘉七、山城屋佐兵衞、西宮弥兵衞、岡村庄助、永樂屋東四郎）及大阪河内屋喜兵衞計8書肆名あり；末尾に「浪華書林柳原積圃藏書目録」あり。')
tail = '復抽修正：原誤把文榮閣、桂雲堂組與柳原積玉圃組併為一簇（書肆無交集），現拆開；柳原積玉圃組（BA81790628、BB00838601）另立為 %s，本條僅留文榮閣、桂雲堂豐住伊兵衞組（BB00850946）。' % bid
a['ai_note'] += tail
b['ai_note'] = b['ai_note'].replace('同簇共 3 條 NCID', '同簇共 2 條 NCID') + '復抽修正：自 99jv424b37 拆出（文榮閣、桂雲堂組仍為 99jv424b37）。'
a['ai_note'] = a['ai_note'].replace('同簇共 3 條 NCID', '同簇共 1 條 NCID')
D['new37'] = b

# 6 史記評林 b2m → 庫內 99juhwkys1
ex_path = 'Book/y/s/1/99juhwkys1-史記評林日本寬文十三年中村積德堂刊本.json'
ex = gitshow(ex_path)
m = D['b2m']
have = {s['id'] for s in ex['sources']}
for s in m['sources']:
    if s['id'] not in have: ex['sources'].append(s); ex['description']['sources'].append('CiNii Books ' + CI + nc(s['details']))
ex['provenance'].extend(m.get('provenance', []))
ex['ai_note'] += ('第三輪 wake-d 復抽併入：原擬另立之「寬文十二年八尾友春刊本」（99jv424b2m）實為同一版——CiNii BB17951700、BB18052366、BB24950377、BD02060031 刊記作「寛文十三癸丑八尾甚四郎友春開板」，'
    '版心「寛文壬子年刋」（1672）僅為版心年；故併入本條，來源與館藏取並集（東京大學總合圖書館 BB17951700 等）。')
drop('b2m')
note('b2n', '疑為寛永十三年本改印：CiNii BA82770105 注記「出版年は刊記の『干時寬永十三丙子年元文元年辰九月改』による」，即據寛永13本改刻刊記，印次關係待核，暫另立。')

# 7 十八史略 Work 卷數與衍生本注
for k, d in D.items():
    if d['title'].startswith('立齋先生標題') or d['title'].startswith('立齋先生'):
        d['ai_note'] += ('復抽補註：本條掛靠 Work d59f2j4w53i8（現記2卷），而 CiNii 著錄日本刊本為7卷（卷之1-7），卷數與 Work 不一致，以 CiNii 著錄為準；'
                         '日本和刻本多為岩垣龍溪標記增補本，屬衍生本，本條是否即此本以各 NCID 書誌注記為準。')
# 8 b3c 改名；寫盤
def fname(d):
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·\[\]]', '', d['edition'])[:26]
    return 'Book/%s/%s/%s/%s-%s%s.json' % (d['id'][-3], d['id'][-2], d['id'][-1], d['id'], d['title'][:20], safe)
for k in DEL:
    sh('git', 'rm', '-q', '--cached', '--sparse', '-f', P[k]); 
    if os.path.exists(ROOT + '/' + P[k]): os.remove(ROOT + '/' + P[k])
newp = {}
for k, d in D.items():
    if k in DEL: continue
    p = fname(d) if k in ('b3c', 'new37') else P[k]
    if k == 'b3c' and p != P[k]:
        sh('git', 'rm', '-q', '--cached', '--sparse', '-f', P[k])
        if os.path.exists(ROOT + '/' + P[k]): os.remove(ROOT + '/' + P[k])
    d['revised_at'] = TODAY if k in ('b2a','b2b','b33','b31','b3j','b3g','b2r','b3c','new37','b37','b2n','b2w','b2x') or d['title'].startswith('立齋') else d['revised_at']
    os.makedirs(os.path.dirname(ROOT + '/' + p), exist_ok=True); open(ROOT + '/' + p, 'w', encoding='utf-8').write(jd(d)); newp[k] = p
d = ex; d['revised_at'] = TODAY
os.makedirs(os.path.dirname(ROOT + '/' + ex_path), exist_ok=True); open(ROOT + '/' + ex_path, 'w', encoding='utf-8').write(jd(d))
sh('git', 'add', '--sparse', '-A', 'Book')
# changed3 / ledger
ch = [newp[k] for k in newp]
json.dump(ch, open(HERE + '/changed3.json', 'w'), ensure_ascii=False, indent=0)
rows = [r.split('\t') for r in open(HERE + '/ledger3.tsv', encoding='utf-8').read().split('\n') if r]
gone = {D[k]['id'] for k in DEL}
out = []
for r in rows:
    if r[0] in gone: continue
    k = next((kk for kk, dd in D.items() if dd['id'] == r[0]), None)
    if k and k != 'new37':
        dd = D[k]; r[5] = dd['edition']; r[3] = '；'.join(dict.fromkeys(p['institution'] for p in dd.get('provenance', []))) or '（NCID 頁無所藏明細）'
    out.append(r)
dd = D['new37']; out.append([dd['id'], dd['title'], '新建', '；'.join(dict.fromkeys(p['institution'] for p in dd['provenance'])), CI + 'BB00838601', dd['edition']])
out.append(['99juhwkys1', '史記評林', '併入既有（復抽）', '補入東京大學總合圖書館、滋賀大學附屬圖書館', CI + 'BB17951700', '原擬 99jv424b2m 寬文十二年八尾友春，併入寬文十三年中村積德堂刊本'])
open(HERE + '/ledger3.tsv', 'w', encoding='utf-8').write('\n'.join('\t'.join(r) for r in out) + '\n')
print('刪', [D[k]['id'] for k in DEL], '新', bid, '總', len(ch))
