# -*- coding: utf-8 -*-
import json,re,collections,sys
from an2_a4 import *
LIB=json.load(open('/tmp/wa4/libbooks.json'))
W={'孟子':'d59f2hgl5lhd','中庸':'d59f2hracfsy','大學':'d59f2htvoe80','論語':'d59f2hfxqsqo','四書集註':'d59f2hry2h34','春秋左氏傳校本':'d59fxvjsgt8g'}
BAD=re.compile(r'講述|講義|三島|永井|大内|大內|中村惕|註解|增注|增註|標註|標注|評註|鼇頭|首書|頭書|譯|訳|諺解|鈔|抄')
def toks(v):
    out=[]
    for p in v['pub'] or []:
        for t in re.split(r'[:：]|ほか\d*書肆?|\[ほか\]|ほか',p):
            t=re.sub(r'[\[\]\(\)（）\s]|發兌|發賣|發行|発売|発兌|賣弘|出板|專賣|専賣|蔵版|藏版|等|書肆',' ',t).strip()
            for u in t.split():
                u=nz(u); u=u.replace('庄','莊'); u=re.sub(r'^山内.*','山内',u)
                u=re.sub(r'^(文昌堂|文光堂|文魁堂|三松堂|玉山堂|萬笈堂|青裳堂|玉山屋|文求堂|龍章堂|淺井龍章堂|岡島寳玉堂)(?=.{3,})','',u)
                if u and u not in ('出版者不明','不明'): out.append(u)
    return out
def ok(v,fam):
    c=v['cre'] or ''
    if BAD.search(c): return False
    if fam=='春秋左氏傳校本': return '杜' in c and '秦' in c
    return '朱' in c or (fam=='孟子' and '後藤' in c)
def groups():
    cl,_=cluster()
    items=[]
    for (t,y),l in cl.items():
        if t not in W: continue
        for k,v,i in l:
            if i['flag'] or not ok(v,t): continue
            items.append((t,y,k,v,toks(v)))
    byf=collections.defaultdict(list)
    for it in items: byf[(it[0],it[1])].append(it)
    out=[]
    for (t,y),l in byf.items():
        par=list(range(len(l)))
        def f(a):
            while par[a]!=a: par[a]=par[par[a]]; a=par[a]
            return a
        link=lambda s: not s.endswith('藩') and len(s)>=2
        for a in range(len(l)):
            for b in range(a):
                sa={s for s in l[a][4] if link(s)}; sb={s for s in l[b][4] if link(s)}
                if sa&sb: par[f(a)]=f(b)
        g=collections.defaultdict(list)
        for a in range(len(l)): g[f(a)].append(l[a])
        for m in g.values(): out.append((t,y,m))
    return out
KN='〇一二三四五六七八九'
def kan(n):
    if n==1: return '元'
    s=''
    if n>=10: s+=('' if n//10==1 else KN[n//10])+'十'
    return s+(KN[n%10] if n%10 else '')
def libhits(w,y,tk):
    r=[]
    for b in LIB:
        if b['w']!=w: continue
        txt=nz((b['ed'] or '')+(b['pub'] or '')+b['note']).replace('衛','衞')
        yy=b['y']==y or re.search('明治'+kan(y-1867)+'年|明治'+str(y-1867)+'年',txt) or str(y) in txt
        if not yy: continue
        match=any(t.replace('衛','衞') in txt for t in tk)
        haspub=bool(re.search(r'[郎衞助堂屋房館社]',nz(b['ed'] or '')))
        r.append((b['id'],b['ed'],match,haspub))
    return r
if __name__=='__main__':
    g=groups(); print(len(g))
    new=0
    for t,y,m in sorted(g,key=lambda x:(x[0],x[1])):
        tk=sorted({s for it in m for s in it[4]})
        h=libhits(W[t],y,tk)
        st='NEW' if not h else ('DUP' if any(x[2] for x in h) else 'AMBIG')
        print(st,t,y,len(m),'|'.join(tk)[:50],[(x[0],x[2]) for x in h][:3])
