import sys, pickle, collections, csv, re
sys.path.insert(0,'/home/claude/w3c')
from load_dc import dc
W,E,P=pickle.load(open('db.pkl','rb'))
S='/tmp/claude-0/-home-claude/ad943395-2758-57ca-8123-45e21779f58e/scratchpad'
nn=dc.norm_name
cnt=collections.Counter(); ent_of=collections.defaultdict(set)
for w in W.values():
    for a in w.get('authors') or []:
        if isinstance(a,dict) and a.get('name'):
            n=nn(a['name']); cnt[n]+=1
            if a.get('entity_id'): ent_of[n].add(a['entity_id'])
ename=collections.defaultdict(set)
for e in E.values():
    if e.get('subtype')!='people': continue
    for x in [e.get('primary_name')]+list(e.get('alt_names') or []):
        x = x if isinstance(x,str) else (x.get('name') if isinstance(x,dict) else None)
        if x: ename[nn(x)].add(e['id'])
def fa(w):
    a=[x for x in W[w].get('authors') or [] if isinstance(x,dict)][:1]
    return a[0] if a else None
def ainfo(w):
    return ' / '.join(sorted({i.get('author_info','') for i in W[w].get('indexed_by') or [] if i.get('author_info')}))[:80]
rows=[r.rstrip('\n').split('\t') for r in open(S+'/diff.tsv')]
typo=[]; members={}
for bl,k,key,n,ids,names,dyn in rows:
    if k=='异姓' and re.search('[譜志]$',key): continue
    if k not in ('异姓','朝代不同'): continue
    ids=ids.split(',')
    named=[(w,fa(w)) for w in ids if w in W and fa(w) and nn(fa(w).get('name')) not in dc.ANONYMOUS]
    for w,a in named: members[w]=(bl,k,key)
    seen=set()
    for i,(w1,a1) in enumerate(named):
        for w2,a2 in named[i+1:]:
            n1,n2=nn(a1['name']),nn(a2['name'])
            if n1==n2 or len(n1)!=len(n2) or len(n1)<2: continue
            d=[j for j in range(len(n1)) if n1[j]!=n2[j]]
            if len(d)!=1: continue
            if (n1,n2) in seen: continue
            seen.add((n1,n2))
            typo.append((bl,k,key,w1,n1,a1.get('dynasty') or W[w1].get('dynasty') or '',cnt[n1],len(ename[n1]),w2,n2,a2.get('dynasty') or W[w2].get('dynasty') or '',cnt[n2],len(ename[n2]),n1[d[0]]+'/'+n2[d[0]],ainfo(w1),ainfo(w2)))
with open(S+'/typo_cand.tsv','w') as f:
    f.write('部类\t类\t题名\tw1\t名1\t朝1\t频1\t人1\tw2\t名2\t朝2\t频2\t人2\t异字\t著录1\t著录2\n')
    for r in typo: f.write('\t'.join(map(str,r))+'\n')
print('typo pairs',len(typo))
pickle.dump((cnt,ent_of,ename,members),open('/home/claude/w3c/stats.pkl','wb'))
