# -*- coding: utf-8 -*-
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_an as a
rows=json.load(open('/tmp/wb3_pre.json'))
names=[l for l in open('/tmp/wb_works.txt').read().split('\n') if l]
idx=collections.defaultdict(list)
for n in names:
    i,_,t=n.partition('-'); idx[a.N(t)].append(i)
ex=collections.defaultdict(collections.Counter)
for b in a.jb: ex[a.nt(b['title'])][b['work_id']]+=1
# 手工映射：規範化題名 -> Work id
MAN={'儀礼白文':'d59ezak3445c','周礼白文':'d59f1ioc6m0w','春秋正文':'d59ezajq05c0','春秋経':'d59ezajq05c0',
'礼記不分卷':'d59fxwojk6bm','礼記不分巻':'d59fxwojk6bm','春秋不分卷':'d59fxx82tu68','春秋不分巻':'d59fxx82tu68','東莱博議':'d59f2hr51ekh',
'左氏雕題略':'d59gdup8ad4y','校定音訓礼記':'d59fxwojk6bm','春秋左伝属事':'d59f2nhk0y68','春秋左氏伝觿':None}
def auto(t):
    if t in MAN: return MAN[t]
    if t in ex: return ex[t].most_common(1)[0][0]
    if t in idx and len(idx[t])==1: return idx[t][0]
    return None
if __name__=='__main__':
    inc=[x for x in rows if not x['flags']]
    un=collections.OrderedDict()
    for x in inc:
        w=auto(x['t'])
        if w is None: un.setdefault(x['t'],[]).append(x['i'])
    print(len(inc),'inc;unresolved titles:')
    for t,l in un.items(): print(t,l,idx.get(t,[])[:6])
