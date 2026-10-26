import csv, glob, os, json, re, sys
ROOT=os.environ.get('BOOK_INDEX','.')
rows=[l.rstrip('\n').split('\t') for l in open(sys.argv[1])]
idx={os.path.basename(p)[:12]:p for p in glob.glob(ROOT+'/Work/*/*/*/*.json')}
P=re.compile(r'所屬叢書記錄 ([0-9a-z]+)（(.*)）[ \t]*$', re.M)
SRC=re.compile(r'源記錄：(\S+)')
out=[]
for r in rows:
    g={'bulei':r[0],'cat':r[1],'key':r[3],'works':[]}
    for i in r[4].split(','):
        w=json.load(open(idx[i]))
        note=w.get('ai_note') or ''
        m=P.search(note); s=SRC.search(note)
        g['works'].append({'id':i,'title':w.get('title'),
          'authors':[(a.get('name'),a.get('role'),a.get('dynasty'),a.get('entity_id')) for a in w.get('authors',[])],
          'dyn':w.get('dynasty'),
          'col':(m.group(2) if m else ''),'colrec':(m.group(1) if m else ''),'src':(s.group(1) if s else ''),
          'ib':[(x.get('title_info'),x.get('author_info'),x.get('section'),(x.get('summary') or '')[:160]) for x in w.get('indexed_by',[])],
          'rel':[x.get('id') for x in w.get('related_works',[])] if isinstance(w.get('related_works'),list) else [],
          'books':0})
    out.append(g)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
