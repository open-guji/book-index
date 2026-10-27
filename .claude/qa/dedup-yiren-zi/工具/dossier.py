import json,glob,sys,csv,os,re
R='/home/user/book-index'
def find(kind,i):
    g=glob.glob(f'{R}/{kind}/{i[-3]}/{i[-2]}/{i[-1]}/{i}*.json')
    g=[p for p in g if os.path.basename(p).split('-')[0].split('.')[0]==i]
    return json.load(open(g[0])) if g else None
ec={}
def ent(e):
    if e not in ec:
        d=find('Entity',e) or {}
        ec[e]={k:d.get(k) for k in ('primary_name','alt_names','period','dynasty','birth_year','death_year','cbdb_id','person_uri','merged_into') if d.get(k)}
        for k in ('names','alternate_names','courtesy_name','art_name'):
            if d.get(k): ec[e][k]=d[k]
    return ec[e]
def short(s,n=160):
    s=(s or '').replace('\n',' ')
    return s if len(s)<=n else s[:n]+'…'
out=[]
for row in csv.reader(open(sys.argv[1]),delimiter='\t'):
    ids=row[6].split(',')
    g={'title':row[5],'diff':row[4],'works':[]}
    for i in ids:
        d=find('Work',i)
        au=[]
        for a in d.get('authors') or []:
            if not isinstance(a,dict): continue
            x={'name':a.get('name'),'role':a.get('role')}
            if a.get('dynasty'): x['dyn']=a['dynasty']
            if a.get('entity_id'): x['eid']=a['entity_id']; x['ent']=ent(a['entity_id'])
            if a.get('original_name'): x['orig']=a['original_name']
            au.append(x)
        src=[]
        for s in (d.get('indexed_by') or [])[:6]:
            src.append({k:short(s.get(k)) for k in ('source','title_info','author_info','summary','section') if s.get(k)})
        w={'id':i,'title':d.get('title'),'authors':au,'period':d.get('period'),'juan':(d.get('juan_count') or {}).get('number'),
           'measure':d.get('measure_info'),'alt':d.get('additional_titles'),'src':src,'nsrc':len(d.get('indexed_by') or []),
           'contained_in':d.get('contained_in'),'related':[r.get('id') for r in d.get('related_works') or [] if isinstance(r,dict)],
           'note':short(d.get('ai_note'),300)}
        g['works'].append({k:v for k,v in w.items() if v})
    out.append(g)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
print(len(out))
