import sys,json,glob,collections
ROOT='/home/user/book-index'
ids=[l.strip() for l in open('ids.txt')]
files=[l.strip() for l in open('files.txt')]
by=collections.defaultdict(list)
for f in files:
    d=json.load(open(f))
    for i,a in enumerate(d.get('authors',[])):
        if a.get('entity_id') in ids: by[a['entity_id']].append((f,d,a))
for eid in ids:
    ef=glob.glob(f'{ROOT}/Entity/*/*/*/{eid}-*.json')[0]
    e=json.load(open(ef))
    print('='*10,eid,e['primary_name'],e.get('dynasty'),e.get('dates'),e.get('native_place'),(e.get('external_ids') or {}).get('cbdb_id'),[a['name'] for a in e.get('alt_names',[])][:15])
    for f,d,a in by[eid]:
        ib=d.get('indexed_by',[])
        inf='; '.join((x.get('source','')[:5]+':'+(x.get('author_info') or '')[:25]+'|'+(x.get('summary') or '')[:90]) for x in ib[:2])
        print(' ',d['type'][0],d['id'],d['title'][:20],'|',a.get('role'),a.get('dynasty'),'|',d.get('dynasty'),'|',inf[:230])
