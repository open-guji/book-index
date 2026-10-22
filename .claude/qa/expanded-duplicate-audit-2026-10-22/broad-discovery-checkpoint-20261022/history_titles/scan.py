#!/usr/bin/env python3
"""Read-only reproducible broad History Work candidate census. No identity inference from similarity."""
import argparse,collections,difflib,itertools,json,pathlib,re,sqlite3,unicodedata
P=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--db',default='/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite');args=ap.parse_args()
c=sqlite3.connect('file:'+args.db+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
trans=str.maketrans('録畧羣峯恆敘遊臺綂彚荆','錄略群峰恒序游台統彙荊')
def norm(t):return re.sub(r'[^\w\u3400-\u9fff]','',unicodedata.normalize('NFKC',t).translate(trans))
def bare(t):return norm(re.sub(r'[\[［【][^\]］】]*[\]］】]','',t))
def names(w):
 a=w['data'].get('authors',[]);return {norm(x.get('name','')) for x in a if x.get('name') and x.get('name') not in ('佚名','不詳','無名氏','□□')}
def primary(w):
 a=w['data'].get('authors',[]);return norm(a[0].get('name','')) if a and a[0].get('name') not in ('佚名','不詳','無名氏','□□') else ''
rows=[]
for r in c.execute("SELECT * FROM records WHERE lower(type)='work'"):
 d=dict(r);d['data']=json.loads(d['data']);
 if not d['data'].get('merged_into'):rows.append(d)
byid={x['id']:x for x in rows}
hist={r[0] for r in c.execute("SELECT work_id FROM membership WHERE division LIKE '%史%' OR lower(division) IN ('history','shi')")}
source_hist={x['id'] for x in rows if any('史部' in str(i.get('section','')) for i in x['data'].get('indexed_by',[]))}
hist |=source_hist
old_pairs=set();old_ids=set();old_cases={}
for p in P.parent.rglob('cases.json'):
 if P in p.parents:continue
 for case in json.loads(p.read_text()):
  ids=set(case.get('paths',{}))|set(case.get('sha256',{}))
  ids|={m.get('id') if isinstance(m,dict) else m for m in case.get('members',[])}
  ids|=set(case.get('losers',[]));ids.add(case.get('keeper'));ids.discard(None)
  old_ids|=ids
  for pair in itertools.combinations(sorted(ids),2):old_pairs.add(pair);old_cases.setdefault(pair,set()).add(case['case_id'])
pairs={}
def add(a,b,channel,key):
 if a==b or not ({a,b}&hist):return
 pair=tuple(sorted((a,b)));e=pairs.setdefault(pair,{'ids':list(pair),'channels':[],'keys':[]})
 if channel not in e['channels']:e['channels'].append(channel)
 if key not in e['keys']:e['keys'].append(key)
def group(channel,fn,cap=150):
 idx=collections.defaultdict(list)
 for w in rows:
  for key in fn(w):
   if key and len(key)>=2:idx[key].append(w['id'])
 skip=[];groups=0
 for k,ids in idx.items():
  ids=sorted(set(ids))
  if len(ids)<2 or not set(ids)&hist:continue
  if len(ids)>cap:skip.append({'key':k,'count':len(ids)});continue
  groups+=1
  for a,b in itertools.combinations(ids,2):add(a,b,channel,k)
 return {'groups':groups,'oversize_groups':skip}
ch={}
ch['normalized_title']=group('normalized_title',lambda w:[norm(w['name'] or w['data'].get('title',''))])
ch['bracketless_title']=group('bracketless_title',lambda w:[bare(w['name'] or '')])
ch['revision_stem']=group('revision_stem',lambda w:[re.sub(r'^(?:重修|續修|新修|重纂|續纂|增修|重訂|新訂|增訂)','',bare(w['name'] or ''))])
ch['explicit_alternate_title']=group('explicit_alternate_title',lambda w:[norm(w['name'] or '')]+[norm(t.get('title',t.get('name','')) if isinstance(t,dict) else t) for t in w['data'].get('additional_titles',[]) if isinstance(t,(str,dict))])
# Keep author groups bounded and qualify short strings conservatively.
aidx=collections.defaultdict(list)
for w in rows:
 for n in names(w):aidx[n].append(w)
examined=0;oversize=[]
for n,ws in aidx.items():
 if not any(w['id'] in hist for w in ws):continue
 if len(ws)>400:oversize.append({'name':n,'count':len(ws)});continue
 for a,b in itertools.combinations(ws,2):
  if not ({a['id'],b['id']}&hist):continue
  x,y=bare(a['name'] or ''),bare(b['name'] or '');examined+=1
  if x==y or min(len(x),len(y))<3:continue
  if (min(len(x),len(y))/max(len(x),len(y))>=.5 and (x in y or y in x)) or difflib.SequenceMatcher(None,x,y,autojunk=False).ratio()>=.76:add(a['id'],b['id'],'shared_author_near_title',n)
ch['shared_author_near_title']={'compared_pairs':examined,'oversize_author_groups':oversize}
# Person-label normalization uses only attested Entity alternate names, no invented name equivalence.
ali=collections.defaultdict(set);derived_aliases=collections.defaultdict(set)
for r in c.execute("SELECT id,name,data FROM records WHERE lower(type)='entity'"):
 d=json.loads(r['data'])
 if d.get('subtype')!='people' or d.get('merged_into'):continue
 ns={norm(d.get('primary_name',''))}
 ns|={norm(v.get('name','') if isinstance(v,dict) else v) for v in d.get('alt_names',[]) if isinstance(v,(str,dict))}
 for n in ns:
  if 2<=len(n)<=7:ali[n].add(r['id'])
  main=norm(d.get('primary_name',''))
  if len(main) in (2,3) and len(n)==2 and n!=main and not n.startswith(main[:1]):derived_aliases[main[:1]+n].add(r['id'])
# Also compare title variants when named authors resolve to the same existing authority.
eidx=collections.defaultdict(list)
for w in rows:
 keys=set()
 for a in w['data'].get('authors',[]):
  n=norm(a.get('name',''));k=a.get('entity_id')
  if k:keys.add(k)
  elif len(ali.get(n,[]))==1:keys.add(next(iter(ali[n])))
 for k in keys:eidx[k].append(w)
ecomp=0
for k,ws in eidx.items():
 if len(ws)>400 or not any(w['id'] in hist for w in ws):continue
 for a,b in itertools.combinations(ws,2):
  if not ({a['id'],b['id']}&hist):continue
  x,y=bare(a['name'] or ''),bare(b['name'] or '');ecomp+=1
  if min(len(x),len(y))<3:continue
  if x==y or (min(len(x),len(y))/max(len(x),len(y))>=.5 and (x in y or y in x)) or difflib.SequenceMatcher(None,x,y,autojunk=False).ratio()>=.76:add(a['id'],b['id'],'shared_author_authority_near_title',k)
ch['shared_author_authority_near_title']={'compared_pairs':ecomp}
pidx=collections.defaultdict(list);alias_hits=0
for w in rows:
 t=bare(w['name'] or '')
 if not any(s in t for s in ['年譜','事略','傳','行實','遺事','碑','墓誌']):continue
 for z in range(2,min(len(t),7)+1):
  prefix=t[:z]
  if prefix in ali and len(ali[prefix])==1:
   pid=next(iter(ali[prefix]));pidx[(pid,t[z:])].append(w['id']);alias_hits+=1
for key,ids in pidx.items():
 if len(ids)<2 or len(ids)>150:continue
 for a,b in itertools.combinations(ids,2):add(a,b,'attested_person_name_title',':'.join(key))
ch['attested_person_name_title']={'title_prefix_hits':alias_hits,'unique_unambiguous_aliases':sum(len(s)==1 for s in ali.values())}
# Surname + courtesy-name forms are retrieval hints only, never independent identity evidence.
didx=collections.defaultdict(list)
for w in rows:
 t=bare(w['name'] or '')
 if not any(v in t for v in ['年譜','事略','傳','行實','遺事']):continue
 for z in range(2,min(len(t),7)+1):
  p=t[:z];ids=ali.get(p,set())|derived_aliases.get(p,set())
  if len(ids)==1:didx[(next(iter(ids)),t[z:])].append(w['id'])
for key,ids in didx.items():
 if 2<=len(ids)<=150:
  for a,b in itertools.combinations(ids,2):add(a,b,'surname_courtesy_title_hint',':'.join(key))
ch['surname_courtesy_title_hint']={'derived_forms':len(derived_aliases),'interpretation':'constructed retrieval hints; require original catalogue evidence'}
output=[]
for pair,e in pairs.items():
 a,b=map(byid.get,pair);e['old_pair']=pair in old_pairs;e['old_case_ids']=sorted(old_cases.get(pair,[]));e['old_member_overlap']=bool(set(pair)&old_ids)
 e['titles']=[a['name'],b['name']];e['primary_authors']=[primary(a),primary(b)];e['shared_authors']=sorted(names(a)&names(b))
 e['same_primary_author']=bool(primary(a) and primary(a)==primary(b));e['same_raw_title']=a['name']==b['name'];e['dynasties']=[a['data'].get('dynasty'),b['data'].get('dynasty')]
 e['risk_flags']=[]
 if not names(a) or not names(b):e['risk_flags'].append('unknown_author')
 if not e['shared_authors']:e['risk_flags'].append('no_shared_named_author')
 if any('譜' in t for t in e['titles']):e['risk_flags'].append('genealogy_or_chronology_revision_requires_scope_check')
 if any('志' in t or '誌' in t for t in e['titles']):e['risk_flags'].append('gazetteer_or_record_revision_requires_scope_check')
 if any(re.search('續|重修|新修|增修|補|重訂',t) for t in e['titles']):e['risk_flags'].append('revision_marker')
 e['status']='candidate';e['merge_eligible']=False
 output.append(e)
output.sort(key=lambda e:(e['old_pair'],-e['same_primary_author'],-('shared_author_near_title'in e['channels']),e['titles'],e['ids']))
for i,e in enumerate(output,1):e['candidate_id']=f'H-BROAD-{i:05}'
(P/'candidate-pairs.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
covered=set().union(*(set(e['ids']) for e in output)) if output else set()
stats={'upstream_sha':'c6dd8356d613fc5614beb88f0a61a3d04cfb069e','all_live_work_rows':len(rows),'history_union_work_rows':len(hist),'history_source_work_rows':len(source_hist),'candidate_pairs':len(output),'candidate_distinct_work_ids':len(covered),'history_candidate_work_ids':len(hist&covered),'old_pair_hits':sum(e['old_pair'] for e in output),'new_pairs':sum(not e['old_pair'] for e in output),'new_pairs_no_old_member':sum(not e['old_member_overlap'] for e in output),'channels':ch,'channel_pair_counts':dict(collections.Counter(v for e in output for v in e['channels'])),'same_named_primary_author_pairs':sum(e['same_primary_author'] for e in output),'status':'retrieval_candidates_not_identity_decisions','native_records_changed':0}
(P/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps(stats,ensure_ascii=False,indent=2))
