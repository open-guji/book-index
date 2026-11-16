# -*- coding: utf-8 -*-
"""wake-d 第三輪：由 CiNii 檢索結果生成候選簇（年+首書肆），對照庫內既有日本刊本標 DUP。輸出 cand3.json。"""
import sys, re, json, collections
sys.path.insert(0, '/tmp'); sys.path.insert(0, '.')
import wk_d3_q as q
import wk3lib as L
ERA = r'慶長|元和|寛永|寬永|寛文|寬文|正保|慶安|承応|承應|明暦|明曆|万治|萬治|延宝|延寶|天和|貞享|元禄|元祿|宝永|寶永|正徳|正德|享保|元文|寛保|寬保|延享|寛延|寬延|宝暦|寶曆|明和|安永|天明|寛政|寬政|享和|文化|文政|天保|弘化|嘉永|安政|万延|萬延|文久|元治|慶応|慶應|明治'
EXCL = r'表目|研究|雕題|目録|目錄|論文|觿|短長|索引|講義|字引|字解|字類|讀本|抄$|鈔$'
JP = json.load(open('/tmp/wk_d3_jpbooks.json'))
def nt(s): return L.trad(re.sub(r'[\s　]', '', s))
TARGETS = [
 dict(name='史記評林', work='d59f2njbpd6r', queries=['史記評林'], tre=r'史記評林', excl=r'表目|研究|雕題|目録|鈔|論|短長|纂'),
 dict(name='漢書評林', work='d59f2njhbn5t', queries=['漢書評林'], tre=r'漢書評林', excl=r'表目|研究'),
 dict(name='三國志', work='d59f282rkphc', queries=['三國志 陳壽'], tre=r'^三國志', au=r'陳壽', excl=r'演義|通俗|傳'),
 dict(name='資治通鑑', work='d59f2pynclxd', queries=['資治通鑑 司馬光'], tre=r'^資治通鑑 ?,?\d|^資治通鑑$', au=r'司馬光', excl=r'綱目|評'),
 dict(name='資治通鑑綱目', work='d59fxz40i60w', queries=['通鑑綱目'], tre=r'^資治通鑑綱目 ?,?(正編)?\d', excl=r'抄略|條記|辨解'),
 dict(name='十八史略', work='d59f2j4w53i8', queries=['十八史略'], tre=r'^立齋先生標[題註]觧?解?註?音釋十八史[略畧]|^立齋先生標題[解觧]註音釋十八史|十八史[略畧] ?,?7', excl=r'便蒙|字引|字解|字類|讀本|校本|講義|紀事|年表|譯|補遺|副詮|大全|定本|備考|標註|標注'),
 dict(name='貞觀政要', work='d59f28jel3wk', queries=['貞觀政要'], tre=r'^貞觀政要 ?,?10', au=r'呉兢|呉競', excl=r'諺解|格式|讀'),
 dict(name='國語', work='d59ezahlu8sg', queries=['國語 韋昭'], tre=r'^(重刻|増註|增註)?國語( |,|定本)', au=r'韋', excl=r'札記$'),
 dict(name='唐鑑', work='d59f2hpi1jwg', queries=['唐鑑'], tre=r'唐鑑 ?,?24', au=r'范祖禹', excl=r''),
]
def pubkey(p):
    p = nt(p); p = re.sub(r'^[\[［]', '', p)
    return re.split(r'[,:;、 ·\[\(（]', p)[0][:8]
def main(names=None):
    out = []
    for T in TARGETS:
        if names and T['name'] not in names: continue
        recs = {}
        for qq in T['queries']:
            for x in q.old(qq, 6): recs[x['ncid']] = x
        cl = collections.OrderedDict()
        for x in recs.values():
            t = nt(x['title']); yr = x['yr']
            if not (x['y'] and 1500 < x['y'] <= 1912): continue
            if yr.strip().startswith('['): continue
            if not re.match(ERA, nt(yr)): continue
            if not re.search(T['tre'], t): continue
            if T.get('excl') and re.search(T['excl'], t): continue
            if T.get('au') and not re.search(T['au'], nt(x['au'])): continue
            if re.search('序|跋|頃|推|以前|以後', yr): continue
            if not x['pub'] or '不明' in x['pub']: continue
            cl.setdefault((x['y'], pubkey(x['pub'])), []).append(x)
        for (y, p), l in sorted(cl.items()):
            dup = [b['id'] + ' ' + (b.get('edition') or '') for b in JP if (b.get('dating') or {}).get('year') == y and (T['name'][:3] in nt(b.get('title', '')) or T['name'][:2] in nt(b.get('title', '')))]
            out.append(dict(target=T['name'], work=T['work'], year=y, pub=p, n=len(l), ncids=[z['ncid'] for z in l], title=l[0]['title'], pubfull=l[0]['pub'], yr=l[0]['yr'], dup=dup))
    return out
if __name__ == '__main__':
    out = main(sys.argv[1:] or None)
    json.dump(out, open('/tmp/wk_d3_cand.json', 'w'), ensure_ascii=False, indent=0)
    for o in out: print(o['target'], o['year'], o['pub'], o['n'], '|', o['title'][:20], '|', o['yr'], '|', ' '.join(o['ncids'][:3]), '| DUP:' + ';'.join(o['dup']) if o['dup'] else '')
