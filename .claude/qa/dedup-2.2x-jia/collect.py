"""汇总 verdict-*.tsv → 挂接清单（SAME/PARTIAL）与判过清单（DIFF/UNSURE/PARTIAL 排除位）。
Book 随所属 Work（followW）的作者位：Work 位判挂谁就跟谁。"""
import pickle,json,collections,glob,sys
SP='/tmp/claude-0/-home-claude/092cb9df-56d3-58b4-85bf-4d6645dab605/scratchpad/j/'
sys.path.insert(0,SP); import dyn2
P,R=pickle.load(open(SP+'db.pkl','rb')); rows=pickle.load(open(SP+'rows0t.pkl','rb'))
D={f:d for t,f,d in R}
V={}
for f in sorted(glob.glob(SP+'verdict-*.tsv')):
    for ln in open(f):
        p=ln.rstrip('\n').split('\t')
        if len(p)<5 or not p[0].strip().isdigit(): continue
        V[int(p[0])]=(p[1].strip().upper(),p[2].strip(),p[3].strip(),p[4].strip())
print('判定组',len(V),collections.Counter(v[0] for v in V.values()))
G=collections.defaultdict(list)
for r in rows:
    if 'gid' in r: G[r['gid']].append(r)
att=[]; judged=[]; wdec={}
for g,rs in G.items():
    if g not in V: continue
    v,eid,exc,why=V[g]
    exc={int(x) for x in exc.replace('，',',').split(',') if x.strip().isdigit()}
    if v in('SAME','PARTIAL') and eid in rs[0]['ids']:
        listed_titles={D[r['path']].get('title') for r in rs[:40] if r['k'] not in exc}
        for r in rs:
            ok = r['k'] not in exc and (r['k']<40 or D[r['path']].get('title') in listed_titles)
            if ok and dyn2.rel(r['dyn'],P[eid][1].get('dynasty'))=='incompat': ok=False
            if ok:
                att.append(dict(path=r['path'],slot=r['slot'],name=r['name'],entity_id=eid,basis='T2 复核 SAME：'+why))
                if r['type']=='Work': wdec[(r['path'],r['name'])]=eid
            else: judged.append((r['path'],r['slot'],r['name'],eid,'排除',why))
    else:
        for r in rs: judged.append((r['path'],r['slot'],r['name'],eid if eid!='-' else ','.join(r['ids']),v,why))
W={d['id']:f for t,f,d in R if t=='Work'}
nf=0
for r in rows:
    if r.get('followW') and (r['followW'],r['name']) in wdec:
        eid=wdec[(r['followW'],r['name'])]
        if eid in r['ids'] and dyn2.rel(r['dyn'],P[eid][1].get('dynasty'))!='incompat':
            att.append(dict(path=r['path'],slot=r['slot'],name=r['name'],entity_id=eid,basis='T2 随所属 Work 判定')); nf+=1
print('挂接',len(att),'其中随Work',nf,'不挂登记',len(judged))
att.sort(key=lambda x:x['path'])
json.dump(att,open(SP+'t2-all.json','w'),ensure_ascii=False,indent=1)
with open(SP+'t2-judged.tsv','w') as f:
    f.write('path\tslot\tname\tentity\t判定\t理由\n')
    for j in judged: f.write('\t'.join(map(str,j))+'\n')
