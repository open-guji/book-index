import pickle,collections,json,glob,re
W,B=pickle.load(open('bi.pkl','rb')); inst=pickle.load(open('zongmu_inst.pkl','rb'))
def live(w,depth=0):
    while w in W and W[w]['merged'] and depth<10: w=W[w]['merged']; depth+=1
    return w if w in W else None
inst2W=collections.defaultdict(set)
for bid,b in B.items():
    for s in b['ids']:
        lw=live(b['w'])
        if lw: inst2W[s].add(lw)
for wid,w in W.items():
    for s in w['src']:
        lw=live(wid)
        if lw: inst2W[s].add(lw)
zw2W=collections.defaultdict(collections.Counter)
for k,v in inst.items():
    for w in inst2W.get(k,()): zw2W[v['work']][w]+=1
print('zm instances mapped',sum(1 for k in inst if k in inst2W),'/',len(inst))
print('zm works mapped',len(zw2W), 'multi-Work',sum(1 for v in zw2W.values() if len(v)>1))
pickle.dump((dict(inst2W),dict(zw2W)),open('bridge.pkl','wb'))
