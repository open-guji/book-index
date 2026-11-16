# -*- coding: utf-8 -*-
"""wake-b 第四輪 掃描2：不限年窗（題名檢索，翻頁），以書肆字串過濾候選。"""
import json,re,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import b3_cinii as c, ndl
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/w4'
B=json.load(open(S+'/books.json'))
STOP=['兵衛','衞門','衛門','兵衞','右衞','左衞','右衛','左衛','之一','書林','書肆','書舖','活字','刻本','刊本','印本','補刻','修補','發行','重刻','翻刻','翻刊','京都','東都','江戶','江都','大阪','浪華','平安','皇都','京師','東京','白文','覆元','覆宋','影印','日本']
def norm(s): return ndl.jp(s).replace('刋','刊').replace('経','經').replace('伝','傳')
def key(ed):
    e=ed
    if '年' in e: e=e.split('年',1)[1]
    e=re.sub(r'[（(][^）)]*[）)]','',e)
    for s in STOP: e=e.replace(s,'|')
    return norm(e)
def grams(k):
    g=set()
    for p in k.split('|'):
        p=re.sub(r'(刊|刻|本|印|版|等|校|之)$','',p)
        if len(p)>=3:
            for i in range(len(p)-2): g.add(p[i:i+3])
        elif len(p)==2: g.add(p)
    return g
if __name__=='__main__':
    for bid in sys.argv[1:]:
        b=B[bid]['b'];ed=b['edition'];g=grams(key(ed))
        print('##',bid,b['title'],'|',ed,'|',sorted(g))
        if not g: continue
        r=c.search_all(maxpages=4,title=norm(b['title']))
        for x in r:
            if any(k in norm(' '.join(x['pub'])) for k in g):
                print('  ',x['ncid'],x['title'][:40],'|',x['date'],'|',x['pub'][:2],'|',x['own'])
