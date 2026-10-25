"""4b-α：全無責任者组里，叢書子目按所屬叢書撰者推定作者；推定作者相同（且朝代、卷數相容）的子目 Work 互并。"""
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'feat.py')).read())
import json
OKROLE={'撰','撰輯','著','輯撰','撰并輯','纂','編撰','撰著'}
def ca(c):
    a=[x for x in c.get('authors') or [] if isinstance(x,dict)]
    return a[0] if a else {}
out=[]; skip=collections.Counter()
for g in groups:
    if g['判定']!='未判' or g['类别']!='全无': continue
    ids=g['ids'].split(',')
    by=collections.defaultdict(list)
    for i in ids:
        f=feat(i); w=W[i]
        if w.get('authors') or not f['congshu'] or not f['cols']: skip['非纯叢書子目']+=1; continue
        cols=[C[c[0]] for c in f['cols']]
        ns={norm_name(ca(c).get('name')) for c in cols}
        if len(ns)!=1 or '' in ns: skip['丛书撰者不一或缺']+=1; continue
        if not {ca(c).get('role') for c in cols}<=OKROLE: skip['角色非撰']+=1; continue
        if not f['secs'] or not all(s.startswith('叢書部/獨撰類') for s in f['secs']): skip['非獨撰類']+=1; continue
        ds={ca(c).get('dynasty') for c in cols}-{None,''}
        by[ns.pop()].append((f,ds,cols))
    for name,fl in by.items():
        if len(fl)<2: continue
        ds=set().union(*[x[1] for x in fl])
        if len(ds)>1: skip['朝代冲突']+=1; continue
        cc=collections.Counter(c['id'] for _,_,cols in fl for c in cols)
        if any(v>1 for v in cc.values()): skip['同一叢書内同题多条(疑异篇)']+=1; continue
        js=[{f['juan']}|f['bjuan'] for f,_,_ in fl]; allj=set().union(*js)-{None}
        if allj and max(allj)-min(allj)>1: skip['卷数差>1']+=1; continue
        fl.sort(key=lambda x:(-x[0]['nbooks'],x[0]['id']))
        k=fl[0][0]
        ev=['《%s》（%s）属《%s》'%(f['title'],f['id'],'、'.join(c.get('title') for c in cols)) for f,_,cols in fl]
        out.append(dict(bulei=g['部类'],key=g['题名键'],keeper=k['id'],keeper_title=k['title'],author=ca(fl[0][2][0]).get('name'),dyn=next(iter(ds),''),
            losers=[f['id'] for f,_,_ in fl[1:]],evidence=ev))
print(len(out),'组',sum(len(o['losers']) for o in out),'条'); print(skip.most_common())
print(collections.Counter(o['bulei'] for o in out))
json.dump(out,open(__import__('os').environ.get('P4WORK','/tmp/p4')+'/beta.json','w'),ensure_ascii=False,indent=1)
