"""Global candidate census. A matching key is NOT a duplicate verdict."""
import pathlib,json,sqlite3,collections,itertools,unicodedata,re,argparse
ROOT=pathlib.Path('/workspace/scratch/0bc7226fa660')
parser=argparse.ArgumentParser()
parser.add_argument('--db',type=pathlib.Path,default=ROOT/'audit/broad-current.sqlite')
parser.add_argument('--out',type=pathlib.Path,default=ROOT/'book-index-expanded-pr/.claude/qa/expanded-duplicate-audit-2026-10-22/broad-census-20261022')
args=parser.parse_args();OUT=args.out
OUT.mkdir(exist_ok=True,parents=True)
db=sqlite3.connect(f'file:{args.db}?mode=ro',uri=True)
def norm(s):return re.sub(r'[\W_]+','',unicodedata.normalize('NFKC',str(s)))
titles=collections.defaultdict(list);author_titles=collections.defaultdict(list);source_rows=collections.defaultdict(list);source_titles=collections.defaultdict(list)
records={}; divisions=collections.defaultdict(set)
for wid,d in db.execute('SELECT work_id,division FROM membership'):divisions[wid].add(d)
for wid,name,raw in db.execute("SELECT id,name,data FROM records WHERE type='Work'"):
    o=json.loads(raw);a=o.get('authors') or []; first=a[0] if a and isinstance(a[0],dict) else {}
    auth=first.get('entity_id') or norm(first.get('name',''))
    if norm(first.get('name','')) in ('不詳','佚名','無名氏','闕名','失名','未詳','不著撰人',''):auth=''
    key=norm(name);titles[key].append(wid)
    if key and auth:author_titles[(key,auth)].append(wid)
    records[wid]={'id':wid,'title':name,'first_author':first,'divisions':sorted(divisions.get(wid,set()))}
    for s in o.get('indexed_by') or []:
        if not isinstance(s,dict):continue
        summary=s.get('summary','')
        if isinstance(summary,str) and len(norm(summary))>=25:
            source_rows[(str(s.get('source_bid') or s.get('source')),norm(summary))].append(wid)
            source_titles[(str(s.get('source_bid') or s.get('source')),norm(summary),key)].append(wid)
def summary(groups):
    g=[sorted(set(ids)) for ids in groups.values() if len(set(ids))>1]
    return {'groups':len(g),'unique_records':len({x for xs in g for x in xs}),'pair_count_before_cross_rule_dedup':sum(len(xs)*(len(xs)-1)//2 for xs in g),'max_group_size':max(map(len,g),default=0)},g
ts,tg=summary(titles);ats,atg=summary(author_titles);ss,sg=summary(source_rows);sts,stg=summary(source_titles)
pairs={}
for rule,groups in [('same_normalized_title_and_named_first_author',atg),('same_normalized_title_and_long_catalogue_summary_and_source',stg)]:
    for ids in groups:
        for pair in itertools.combinations(ids,2):pairs.setdefault(pair,[]).append(rule)
parent={}
def find(x):
    parent.setdefault(x,x)
    if parent[x]!=x:parent[x]=find(parent[x])
    return parent[x]
for x,y in pairs:parent[find(x)]=find(y)
components=collections.defaultdict(list)
for x in parent:components[find(x)].append(x)
division_counts=collections.Counter();unclassified=[]
for pair,rules in pairs.items():
    ds=set().union(*(divisions.get(x,set()) for x in pair))
    for d in ds:division_counts[d]+=1
    if not ds:unclassified.append(pair)
result={'base':json.loads(db.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0])['base'],'meaning':'Candidate retrieval only; none of these counts asserts duplicate identity or safe merge. Overlapping division/rule counts cannot be added. Same source/summary without same title is diagnostic only: many records contain a whole catalogue paragraph.','active_work_count':len(records),'officially_classified_active_works':sum(bool(divisions.get(x)) for x in records),'unclassified_active_works':sum(not divisions.get(x) for x in records),'same_title_only':ts,'same_title_named_first_author':ats,'same_source_long_catalogue_summary_DIAGNOSTIC_ONLY':ss,'same_title_source_long_summary':sts,'stronger_rule_union_unique_pairs':len(pairs),'stronger_rule_union_components':len(components),'stronger_rule_union_records':len(parent),'pairs_by_division_overlapping':dict(division_counts),'pairs_with_neither_member_classified':len(unclassified)}
(OUT/'stats.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (OUT/'candidate-pairs.jsonl').open('w') as f:
    for (x,y),rules in sorted(pairs.items()):f.write(json.dumps({'ids':[x,y],'rules':rules,'records':[records[x],records[y]],'status':'unreviewed_candidate'},ensure_ascii=False)+'\n')
(OUT/'unclassified-candidate-pairs.json').write_text(json.dumps([{'ids':list(p),'records':[records[x] for x in p],'rules':pairs[p]} for p in unclassified],ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
