import json,os,sys,hashlib
ADMIN={'id','work_id','revision','revised_at','updated_at','ai_note','merged_from','schema_version'}
out=open('/tmp/claude-0/s/books2.jsonl','w');n=0
for d,_,fs in os.walk('Book'):
    for f in fs:
        if not f.endswith('.json'):continue
        p=os.path.join(d,f); j=json.load(open(p,encoding='utf-8')); n+=1
        if j.get('merged_into'): continue
        core={k:v for k,v in j.items() if k not in ADMIN}
        h=hashlib.sha1(json.dumps(core,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
        srcs=[s.get('id') for s in j.get('sources') or [] if s.get('id')]
        out.write(json.dumps({'p':p,'id':j['id'],'w':j.get('work_id'),'t':j.get('title'),'ed':j.get('edition'),'h':h,'src':srcs,
          'ci':[c.get('id') for c in j.get('contained_in') or []],'prov':[x.get('institution') for x in j.get('provenance') or []],
          'yr':(j.get('publication_info') or {}).get('year'),'jc':j.get('juan_count'),'nres':len(j.get('resources') or []),
          'note':(j.get('ai_note') or '')[:120],'mf':j.get('merged_from')},ensure_ascii=False)+'\n')
print(n,file=sys.stderr)
