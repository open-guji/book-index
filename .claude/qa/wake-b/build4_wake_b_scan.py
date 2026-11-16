# -*- coding: utf-8 -*-
"""wake-b 第四輪：「存疑」批再核——掃描階段。對每條 Book 取年（edition/dating）→CiNii 題名＋年窗檢索，輸出候選供人工判讀。"""
import json,re,sys,os
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
import b3_cinii as c, eras, ndl
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/w4'
B=json.load(open(S+'/books.json'))
SKIP=re.compile(r'影印|排印|鉛印|石印|昭和|大正|景印|影刻|影寫|影抄|影鈔|鈔本|抄本|手稿|摹|傳鈔|舊鈔|手鈔|稿本|^清|^明|光緒|嘉慶|道光|宣統|萬曆|^見|佚存|^倭|^國朝|景日本|影宋|影元')
def scan(ids,maxn=8):
    out=[]
    for bid in ids:
        b=B[bid]['b'];ed=b.get('edition','')
        y,_=eras.era_year(ed)
        if not y: y=(b.get('dating') or {}).get('year')
        t=b['title']
        o=[f'## {bid} {t} | {ed} | y={y} | prov={[p["institution"] for p in b.get("provenance",[])]}']
        qs=[ndl.jp(t)]
        for q in qs:
            kw={'title':q}
            if y: kw.update(year_from=y-1,year_to=y+1)
            r=c.search_all(maxpages=2,**kw)
            for x in r[:maxn]:
                o.append(f"  {x['ncid']} {x['title'][:40]} | {x['date']} | {x['pub']} | {x['cr'][:20] if isinstance(x['cr'],str) else x['cr']} | own={x['own']}")
        out.append('\n'.join(o))
    return out
def cands():
    r=[]
    for k,v in B.items():
        b=v['b'];ed=b.get('edition','')
        y,_=eras.era_year(ed)
        if not y: y=(b.get('dating') or {}).get('year')
        if SKIP.search(ed) and not re.search(r'翻刊|翻刻|覆',ed): continue
        r.append(k)
    return r
if __name__=='__main__':
    ids=sys.argv[1:] or cands()
    print('\n'.join(scan(ids)))
