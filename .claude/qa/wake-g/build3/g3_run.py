#!/usr/bin/env python3
import sys,json,re,os
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3')
from g3_build import *
APPLY='--apply' in sys.argv
spec=json.load(open(sys.argv[1]))
OUT=[];REJ=[]
for sp in spec:
    cand=json.load(open(S+sp['cand']))
    idx=[]
    if 'rx' in sp:
        rx=re.compile(sp['rx']); ex=re.compile(sp['exrx']) if sp.get('exrx') else None
        idx+=[k for k,o in enumerate(cand) if rx.search(o['tc']) and not (ex and ex.search(o['tc'])) and (not sp.get('aurx') or re.search(sp['aurx'],o['au']))]
    for x in sp.get('idx',[]):
        if isinstance(x,str) and '-' in x: a,b=x.split('-'); idx+=list(range(int(a),int(b)+1))
        else: idx.append(int(x))
    for k in idx:
        if k in sp.get('skip',[]): continue
        o=dict(cand[k])
        for g in sp.get('merge',[]):
            if g[0]==k:
                for m in g[1:]: o['ncids']=o['ncids']+cand[m]['ncids']; o['ps']=sorted(set(o['ps'])|set(cand[m]['ps']))
        if any(k in g[1:] for g in sp.get('merge',[])): continue
        wk=sp['work']
        if wk=='auto':
            if len(o['works'])!=1: REJ.append((sp['cand'],k,o['tc'],o['y'],['Work不唯一 %d'%len(o['works'])])); continue
            wk=o['works'][0][0]
        b,pr=build_one(wk,o,sp.get('title',{}).get(str(k)))
        if not b: REJ.append((sp['cand'],k,o['tc'],o['y'],pr)); continue
        b['idx']=(sp['cand'],k); b['dup']=dupcheck(b)
        OUT.append(b)
# 跨簇同年重疊檢查
seen={}
for b in OUT:
    for p in b['allpubs']:
        key=(b['work'],b['year'],p)
        seen.setdefault(key,[]).append(b['idx'])
pairs={}
for key,v in seen.items():
    if len(v)>1: pairs[tuple(sorted(set(map(tuple,v))))]=key
for n,b in enumerate(OUT):
    print('%3d %s %s %s|%s|n=%d own=%d%s%s%s'%(n,b['idx'][1],b['title'][:14],b['year'],'/'.join(b['pubs_show'])[:28],len(b['recs']),len({o for r in b['recs'] for o in r['owners']}),' DUP:'+','.join(b['dup']) if b['dup'] else '',' P:'+','.join(b['probs']) if b['probs'] else '',' C' if b['colo'] else ''))
print('REJ:'); [print('  ',r) for r in REJ]
print('PAIRS:',[ (a,k) for a,k in pairs.items()])
json.dump([dict(b,recs=[r['ncid'] for r in b['recs']],ext=dict(b['ext'])) for b in OUT],open(sys.argv[1]+'.out.json','w'),ensure_ascii=False)

if APPLY:
    WK='/tmp/wk-wake-g3'
    sys.path.insert(0,WK+'/.claude/qa'); import mintid
    os.chdir(WK)
    skipset=set(tuple(x) for x in json.load(open(S+'skip_all.json'))) if os.path.exists(S+'skip_all.json') else set()
    sel=[b for b in OUT if not b['dup'] and tuple(b['idx']) not in skipset]
    ids=mintid.mint('Book','wake-g',len(sel))
    led=[];paths=[]
    for b,bid in zip(sel,ids):
        d=book_json(b,bid,'g','')
        safe=re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]','',b['ed'])[:24]
        p='Book/%s/%s/%s/%s-%s%s.json'%(bid[-3],bid[-2],bid[-1],bid,b['title'],safe)
        os.makedirs(os.path.dirname(p),exist_ok=True)
        open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
        paths.append(p)
        led.append('\t'.join([bid,b['title'],'新建',b['ed'],'、'.join(x['institution'] for x in d['provenance']),' '.join(x['details'] for x in d['sources'][:3]),b['work']]))
    qa=WK+'/.claude/qa/wake-g'
    open(qa+'/ledger3.tsv','a',encoding='utf-8').write('\n'.join(led)+'\n')
    open(qa+'/changed_paths3.txt','a').write('\n'.join(paths)+'\n')
    print('APPLIED',len(sel))
