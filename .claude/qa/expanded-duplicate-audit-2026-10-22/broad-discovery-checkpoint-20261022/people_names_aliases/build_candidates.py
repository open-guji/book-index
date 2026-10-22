"""Read-only broad person candidate discovery from root's verified main SQLite."""
import json,sqlite3,pathlib,collections,re,itertools,unicodedata
ROOT=pathlib.Path('/workspace/scratch/0bc7226fa660')
OUT=pathlib.Path(__file__).resolve().parent
AUDIT=OUT.parent.parent
DB=ROOT/'audit/broad-current.sqlite'
db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
manifest=json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base']=='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
entities={}; names=collections.defaultdict(list)
for i,n,p,b,s,d in db.execute("select id,name,path,blob_sha,sha256,data from records where type='Entity'"):
 o=json.loads(d)
 if o.get('subtype')=='people':entities[i]={'id':i,'name':n,'path':p,'blob_sha':b,'sha256':s,'record':o};names[n].append(i)
oldpairs=collections.defaultdict(list)
for f in AUDIT.rglob('cases.json'):
 if 'broad-' in str(f):continue
 try: cases=json.loads(f.read_text())
 except:continue
 if isinstance(cases,dict):cases=cases.get('cases',[])
 for c in cases:
  if not isinstance(c,dict):continue
  ids=[c.get('keeper')]+c.get('losers',[]) if isinstance(c.get('losers',[]),list) else []
  ids=[i for i in ids if isinstance(i,str)]
  ids+=c.get('ids',[]) if isinstance(c.get('ids'),list) else []
  for a,b in itertools.combinations(set(i for i in ids if isinstance(i,str)),2):oldpairs[tuple(sorted([a,b]))].append(c.get('case_id'))
candidates={}
def add(a,b,rule,details):
 if a==b:return
 pair=tuple(sorted([a,b]));x=candidates.setdefault(pair,{'ids':list(pair),'names':[entities[i]['name'] for i in pair],'rules':[],'old_case_ids':sorted(set(oldpairs.get(pair,[])))})
 r={'rule':rule,**details}
 if r not in x['rules']:x['rules'].append(r)
for n,ids in names.items():
 for a,b in itertools.combinations(ids,2):add(a,b,'exact_primary_name',{'name':n})
compound=('歐陽','司馬','夏侯','諸葛','皇甫','上官','司徒','司空','令狐','尉遲','公孫','慕容','宇文','長孫','鮮于','万俟','萬俟')
alt_count=0
for i,e in entities.items():
 n=e['name']; surname=next((s for s in compound if n.startswith(s)),n[:1])
 for a in e['record'].get('alt_names',[]):
  if not isinstance(a,dict):continue
  alias=a.get('name','');alt_count+=1
  if not alias:continue
  for j in names.get(alias,[]):add(i,j,'exact_alt_name',{'owner':i,'alias':a})
  if a.get('type') not in ('諡號','廟號','年號','封號'):
   for j in names.get(surname+alias,[]):add(i,j,'surname_plus_alias',{'owner':i,'alias':a,'surname':surname})
# These equivalences are discovery-only, never decisions.
variants=str.maketrans({'峯':'峰','羣':'群','竝':'並','恆':'恒','槩':'概','鼇':'鰲','巖':'岩','嶽':'岳','鍊':'煉','卽':'即','眞':'真','爲':'為','衞':'衛','冩':'寫','啓':'啟','祐':'佑','徴':'徵','徳':'德','﨑':'崎','梁':'樑','朴':'樸','祕':'秘','汎':'泛','緖':'緒','寛':'寬','羨':'羡','邱':'丘','舘':'館'})
normal=collections.defaultdict(list)
for i,e in entities.items():normal[unicodedata.normalize('NFKC',e['name']).translate(variants)].append(i)
for norm,ids in normal.items():
 for a,b in itertools.combinations(ids,2):
  if entities[a]['name']!=entities[b]['name']:add(a,b,'graphic_variant_candidate',{'normalized':norm})
# Shared IDs are discovery clues only: false enrichment must be separately assessed.
ext=collections.defaultdict(list)
for i,e in entities.items():
 for k,v in e['record'].get('external_ids',{}).items():
  if k.endswith('_id') and isinstance(v,(str,int)):ext[(k,str(v))].append(i)
for (k,v),ids in ext.items():
 for a,b in itertools.combinations(ids,2):add(a,b,'shared_external_identifier',{'key':k,'value':v})
works=collections.defaultdict(list); author_rows=0; work_rows=0; signature_pairs=0; source_summary_rows=0; explicit_bridge_checks=0
for wid,n,p,b,s,d in db.execute("select id,name,path,blob_sha,sha256,data from records where type='Work'"):
 o=json.loads(d);work_rows+=1
 source_summary_rows+=len(o.get('indexed_by',[]))
 for a in o.get('authors',[]):
  if not isinstance(a,dict):continue
  author_rows+=1;i=a.get('entity_id');an=a.get('name')
  if i not in entities:continue
  works[i].append({'id':wid,'name':n,'path':p,'sha256':s,'blob_sha':b,'author':a,'indexed_by':o.get('indexed_by',[]),'description':o.get('description'),'ai_note':o.get('ai_note')})
  owner_name=entities[i]['name'];surname=next((s for s in compound if owner_name.startswith(s)),owner_name[:1])
  given=owner_name[len(surname):]
  if len(given)>=1:
   for source in o.get('indexed_by',[]):
    summary=source.get('summary','')
    if not isinstance(summary,str):continue
    explicit_bridge_checks+=1
    pat='(?:'+re.escape(owner_name)+'|'+re.escape(given)+r')[，,、 ]?(?:字|號|本名|初名|一名)([\u3400-\u9fff]{1,6})'
    for m in re.finditer(pat,summary):
     tail=m.group(1)
     for length in range(1,len(tail)+1):
      alias=tail[:length]
      for target in (alias,surname+alias):
       for j in names.get(target,[]):
        add(i,j,'source_explicit_name_bridge_candidate',{'work_id':wid,'owner':i,'source':source.get('source'),'page':source.get('page'),'matched_alias':alias,'excerpt':summary[max(0,m.start()-20):m.end()+40]})
  if an and an!=entities[i]['name']:
   for j in names.get(an,[]):add(i,j,'author_signature_alias',{'work_id':wid,'entity_id':i,'signature':an});signature_pairs+=1
for x in candidates.values():
 x['work_counts']={i:len(works[i]) for i in x['ids']}
 x['religious_or_sovereign_name_flag']=any(re.search(r'^(釋|僧|唐王|明太祖|唐太宗|唐玄宗)|皇帝|親王|真人|天師|道士|成宗',n) for n in x['names'])
 x['discovery_only']=True
queue=sorted(candidates.values(),key=lambda x:(bool(x['old_case_ids']),x['religious_or_sovereign_name_flag'],x['names']))
for filename,obj in [('candidate-queue.json',queue),('entity-snapshots.json',{i:entities[i] for x in queue for i in x['ids']}),('work-snapshots.json',{i:works[i] for x in queue for i in x['ids']})]:
 (OUT/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
prior_queue=json.loads((OUT.parent/'candidate-queue.json').read_text());priorpairs={tuple(sorted(x['ids'])) for x in prior_queue}
stats={'main_sha':manifest['base'],'db_manifest':manifest,'coverage':{'active_people':len(entities),'active_entity_names':len(names),'alt_name_rows':alt_count,'active_work_records':work_rows,'author_rows':author_rows,'indexed_by_rows':source_summary_rows,'source_owner_checks':explicit_bridge_checks},'candidates':{'scope':'ALL active subtype=people; includes religious/sovereign people. General-person reviewed cases manually scoped.', 'unique_pairs':len(queue),'old_reviewed_pairs':sum(bool(x['old_case_ids']) for x in queue),'not_previously_reviewed_pairs':sum(not x['old_case_ids'] for x in queue),'not_in_old_696_queue':sum(tuple(x['ids']) not in priorpairs for x in queue),'religious_or_sovereign_name_flag':sum(x['religious_or_sovereign_name_flag'] for x in queue),'by_rule':dict(collections.Counter(r['rule'] for x in queue for r in x['rules']))},'limitations':['Automatic candidate generation is not identity confirmation.','No full simplified/traditional mapping; conservative explicit graphic equivalence only.','The religious/sovereign flag is heuristic; final cases manually scoped.','No native file writes, merge implementation or full-reference rewrite audit.']}
(OUT/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False))
