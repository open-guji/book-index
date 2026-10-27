import json,glob,re,os,sys,collections
D=json.load(open('/tmp/claude-0/w/tiered.json'))
man=[g for g in D if not g['safe']]; safe=[g for g in D if g['safe']]
J={}
for f in sorted(glob.glob('/tmp/claude-0/j/b0*.txt')):
    for l in open(f):
        l=l.rstrip('\n')
        if not l.strip(): continue
        c=l.split('\t'); J[int(c[0])]=(c[1],c[2] if len(c)>2 else '')
assert len(J)==len(man), (len(J),len(man))
JA={}
for l in open('/tmp/claude-0/j/auto_all.tsv'):
    c=l.rstrip('\n').split('\t'); JA[int(c[0][5:])]=(c[1].strip(),c[2] if len(c)>2 else '')
assert len(JA)==len(safe)
NOADD_ROLE={'撰','','舊題撰','著','作','述'}
ADD={387,334,577,9,15,28,29,32,69,119,127,138,149,150,151,160,188,194,212,220,284,285,293,294,297,320,331,341,360,402,429,436,438,448,452,454,465,471,474,483,490,504,527,545,557,558,559,586,605,607,617,468}
def fa(w): return (w.get('authors') or [{}])[0]
def desc(w):
    a=fa(w); dy=a.get('dyn') or w.get('period') or '朝代缺'
    return '%s(%s,%s卷)'%(a.get('name') or '不著撰人',dy,w.get('juan') or '?')
groups=[];pairs=[];stats=collections.Counter()
ALL=[(k,g,J[k],'YRZ-%04d'%(k+1),k in ADD) for k,g in enumerate(man)]+[(k,g,JA[k],'YRZ-A%03d'%k,None) for k,g in enumerate(safe)]
for k,g,(act,note),cid,addf in ALL:
    ws=g['works']; ids=[w['id'] for w in ws]
    par=list(range(len(ws)))
    def f(x):
        while par[x]!=x: x=par[x]
        return x
    merges=[];Dp=[]
    for part in [p.strip() for p in act.split(';')]:
        if part.startswith('M '):
            for m in part[2:].split(','):
                a,b=map(int,m.split('>')); merges.append((a,b))
        elif part.startswith('D '):
            for m in part[2:].split(','):
                a,b=map(int,m.split('-')); Dp.append((a,b))
        elif part=='C': pass
        else: raise SystemExit((k,act))
    keepers=collections.defaultdict(list)
    for a,b in merges:
        while b in [x for x,_ in merges]: b=[y for x,y in merges if x==b][0]
        keepers[b].append(a); par[a]=b
    for kp,ls in keepers.items():
        ev='首位异人同题组逐组判：'+'／'.join('《%s》%s'%(ws[i]['title'],desc(ws[i])) for i in [kp]+ls)+'；'+note
        groups.append({'case_id':cid,'cluster_id':cid,'type':'work','keeper':ids[kp],'losers':[ids[i] for i in ls],
            'keeper_source':'去重第二轮细拆「新-异人登记-子」普查（book-index da71022733）','evidence':ev,'why':ev,
            'rule':'去重方案第二轮细拆「新-异人登记-子」：首位异人同题组逐组判，误字／占位名／同书异署者并（3c 口径）',
            'add_author':addf if addf is not None else any(fa(ws[i]).get('role','') not in NOADD_ROLE and fa(ws[i]).get('name') for i in ls)})
        stats['merge_groups']+=1; stats['losers']+=len(ls)
    reps=sorted({f(i) for i in range(len(ws))})
    # union-find on reps for connectivity
    p2={r:r for r in reps}
    def g2(x):
        while p2[x]!=x: x=p2[x]
        return x
    inD=set()
    for a,b in Dp:
        a,b=f(a),f(b)
        if a==b: continue
        pairs.append((ids[a],ids[b],'D','新-异人登记-子 %s：%s／%s；%s'%(cid,desc(ws[a]),desc(ws[b]),note or '待核'))); p2[g2(a)]=g2(b); inD|={a,b}
        stats['D']+=1
    r0=reps[0]
    for r in reps[1:]:
        if g2(r)==g2(r0): continue
        # C edge from r0 (or from a rep in r0's comp if r in D set)
        pairs.append((ids[r0],ids[r],'C','新-异人登记-子 %s：首位责任者异人，%s／%s，逐组判同题异书%s'%(cid,desc(ws[r0]),desc(ws[r]),('；'+note) if note and not merges and not Dp else '')))
        p2[g2(r)]=g2(r0); stats['C']+=1
    assert len({g2(r) for r in reps})==1, k
print(stats)
json.dump({'groups':groups},open('/tmp/claude-0/w/batch.json','w'),ensure_ascii=False,indent=1)
with open('/tmp/claude-0/w/judged.tsv','w') as f:
    f.write('# 去重第二轮细拆「新-异人登记-子」（子部，首位责任者异姓／朝代不同的同题组）判为分立（C）或存疑（D）的对；基线 main da71022733；编号 YRZ-A 者为初筛「异人卷数悬殊／朝代悬隔」组，复核后亦逐组判。并条见 .claude/qa/dedup-yiren-zi/。\n')
    for p in pairs: f.write('\t'.join(p)+'\n')
