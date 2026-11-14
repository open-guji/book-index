import json,glob,hashlib,subprocess,sys,collections
sys.path.insert(0,'/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r11')
from meas import norm
S=sys.argv[1]; APPLY='--apply' in sys.argv
RULE='L0 第十一輪 Book 叢書子目重複：同一 Work、同一叢書 Collection；一條為叢書本著錄、另一條為叢書子目著錄（館藏為叢書共有，或至多一條有獨立館藏；故宮等來源按索書號分條）；卷數相同或只差附卷（主卷數不同者先按卷數拆組，只並卷數相同的一對）；版本項至多一種非本叢書名的底本描述（如影印某本），撰人不相抵'
TODAY='2026-11-14'
ok=json.load(open(S+'/okfinal.json'))
def P(i): return glob.glob(f'Book/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def blob(p): return subprocess.run(['git','show','origin/main:'+p],capture_output=True).stdout
LISTS=['contained_in','indexed_by','sources','provenance','resources','external_ids']
SCAL=['edition','edition_type','measures','measure_info','dating','description','publication_info','physical_description','metadata','authors']
ledger=[];mp={}
for n,g in enumerate(ok,1):
    ds={i:json.load(open(P(i))) for i in g['books']}
    score=lambda i:(bool(ds[i].get('provenance')),bool(ds[i].get('edition')),len(ds[i]),i)
    k=max(g['books'],key=score); losers=[i for i in g['books'] if i!=k]
    K=ds[k]; pre=[{'id':i,'path':P(i),'sha256':hashlib.sha256(blob(P(i))).hexdigest()} for i in g['books']]
    for l in losers:
        D=ds[l]
        for f in LISTS:
            for x in D.get(f) or []:
                if x not in (K.get(f) or []): K.setdefault(f,[]).append(x)
        for f in SCAL:
            if not K.get(f) and D.get(f): K[f]=D[f]
        if D.get('ai_note') and D['ai_note'] not in (K.get('ai_note') or ''):
            K['ai_note']=(K.get('ai_note','')+'\n' if K.get('ai_note') else '')+'〔被併條 %s 原註〕%s'%(l,D['ai_note'])
        mp[l]=k
        t={'schema_version':D.get('schema_version',1),'id':l,'type':'book','title':D.get('title'),'work_id':D.get('work_id'),
           'merged_into':k,'merged_basis':{'rule':RULE,'at':TODAY,'by':'L0'},'revision':D.get('revision') or '1.0.0','revised_at':TODAY}
        if APPLY: open(P(l),'w').write(json.dumps(t,ensure_ascii=False,indent=2)+'\n')
    mnote=''
    if g.get('mlong') and len(norm(g['mlong']))>len(norm(K.get('measure_info'))):
        mnote='；本條原卷數「%s」，從詳改為「%s」'%(K.get('measure_info'),g['mlong']) if K.get('measure_info') else ''
        K['measure_info']=g['mlong']
    K['ai_note']=(K.get('ai_note','')+'\n\n' if K.get('ai_note') else '')+'%s L0 併條：併 %s 入本條（同叢書同子目重複著錄%s）。'%(TODAY,'、'.join(losers),''.join('；%s 原版本項「%s」'%(l,ds[l].get('edition')) for l in losers if ds[l].get('edition') and ds[l].get('edition')!=K.get('edition'))+mnote)
    K['revision']='%d.0.0'%(int(str(K.get('revision') or '1.0.0').split('.')[0])+1); K['revised_at']=TODAY
    if APPLY: open(P(k),'w').write(json.dumps(K,ensure_ascii=False,indent=2)+'\n')
    ledger.append({'cluster_id':'L0R11B%04d'%n,'type':'book','keeper':k,'losers':losers,'evidence':'Work %s；Collection %s'%(g['key'][0],g['key'][1]),'rule':RULE,'preconditions':pre,'retained_alternatives':[],'classification_decisions':[],'dropped_author_entities':[]})
if APPLY:
    n=0
    for f in glob.glob('promotions/*.json'):
        t=open(f).read(); o=t
        for l,k in mp.items():
            if l in t: t=t.replace('"production_id": "%s"'%l,'"production_id": "%s"'%k)
        if t!=o: open(f,'w').write(t); n+=1
    print('promo files',n)
    base=subprocess.run(['git','rev-parse','--short=11','origin/main'],capture_output=True,text=True).stdout.strip()
    import os; os.makedirs('.claude/qa/dedup-L0/r11-book',exist_ok=True)
    json.dump({'base':base,'merges':ledger},open('.claude/qa/dedup-L0/r11-book/merges.json','w'),ensure_ascii=False,indent=1)
print(len(ledger),len(mp))
