import json,os,re,pickle,collections
R='/home/user/book-index/'
W={};B={}
c=collections.Counter()
for kind in ('Work','Book'):
    for dp,_,fs in os.walk(R+kind):
        for f in fs:
            if not f.endswith('.json'): continue
            p=os.path.join(dp,f)
            try: d=json.load(open(p))
            except Exception: c['bad']+=1; continue
            note=d.get('ai_note') or ''
            src=re.findall(r'源記錄：([0-9a-z]+)',note)
            res=[(x.get('id'),x.get('url')) for x in d.get('resources') or []]
            if kind=='Work':
                W[d['id']]=dict(t=d.get('title'),at=[ (a if isinstance(a,str) else a.get('title') or a.get('name')) for a in d.get('additional_titles') or []],
                  au=[(a.get('name'),a.get('dynasty'),a.get('role')) for a in d.get('authors') or []],dyn=d.get('dynasty'),
                  merged=d.get('merged_into'),src=src,ib=[(x.get('source'),x.get('title_info'),x.get('author_info')) for x in d.get('indexed_by') or []],res=res,path=p[len(R):],
                  wtype=d.get('work_type'), parent=d.get('parent_work') or d.get('parent_works'))
            else:
                ids=[]
                for s in d.get('sources') or []:
                    m=re.search(r'/instance/([0-9a-z]+)',s.get('details') or '')
                    if m: ids.append(m.group(1))
                B[d['id']]=dict(t=d.get('title'),w=d.get('work_id'),ed=d.get('edition'),et=d.get('edition_type'),
                  prov=[p2.get('institution') for p2 in d.get('provenance') or []],ids=ids,src=src,res=res,merged=d.get('merged_into'),
                  year=(d.get('publication_info') or {}).get('year'))
            c[kind]+=1
print(c)
pickle.dump((W,B),open('bi.pkl','wb'))
