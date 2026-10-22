#!/usr/bin/env python3
"""Read-only broad Work candidate scan. Candidate edges NEVER authorize merges."""
import argparse, collections, difflib, itertools, json, re, sqlite3, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TRANS = str.maketrans('经书礼传说义录论学诗尔风体释编图纂续笺钞类读汇辑圣贤周后讚繋係畧羣衆峯', '經書禮傳說義錄論學詩爾風體釋編圖纂續箋鈔類讀匯輯聖賢周後贊繫系略群眾峰')
def norm(s):
    return re.sub(r'[^\u3400-\u9fffA-Za-z0-9]', '', unicodedata.normalize('NFKC', s or '')).translate(TRANS).replace('繫辭','系辭')
def imprint(s):
    return re.sub(r'^(?:新刻|新刊|重刻|重刊|新鐫|新雕|增訂|校刊|欽定)', '', norm(s))
def dump(name, data):
    (HERE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
def members(c):
    out=set()
    for key in ['keeper','proposed_keeper']:
        if isinstance(c.get(key),str): out.add(c[key])
    for key in ['losers','proposed_losers','ids','members','records']:
        vals=c.get(key,[])
        if isinstance(vals,list):
            out.update(x if isinstance(x,str) else x.get('id','') for x in vals if isinstance(x,(str,dict)))
    if isinstance(c.get('paths'),dict): out.update(c['paths'])
    return {x for x in out if x}
def prior_cases():
    out=[]
    for lane in ['classics_titles','history_titles','masters_titles','collections_titles','people_names_aliases','people_religious_variants']:
        effective={}
        for rel in ['cases-all.json' if lane=='people_religious_variants' else 'cases.json','hourly-20261022/cases.json','astra-review-20261022/cases.json','hourly-20261022T1900/cases.json']:
            for c in json.loads((ROOT/lane/rel).read_text()):
                old=c.get('supersedes_case_id') or c.get('supersedes')
                if old: effective.pop(old,None)
                effective[c['case_id']]=c
        out.extend(effective.values())
    return out
def run(db):
    con=sqlite3.connect('file:'+str(Path(db).resolve())+'?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    metadata=[dict(x) for x in con.execute('select * from metadata')]
    alias_entities=collections.defaultdict(set); entity_count=0
    for row in con.execute("select id,data from records where lower(type)='entity'"):
        d=json.loads(row['data'])
        if d.get('merged_into') or d.get('subtype')!='people':continue
        entity_count+=1; primary=norm(d.get('primary_name',''))
        names={primary}
        for a in d.get('alt_names',[]):
            alt=norm(a.get('name','') if isinstance(a,dict) else str(a))
            if len(alt)>1:
                names.add(alt)
                if primary and len(alt) in (2,3) and not alt.startswith(primary[0]):names.add(primary[0]+alt)
        for n in names:
            if len(n)>1:alias_entities[n].add(row['id'])
    works={}
    for row in con.execute("select * from records where lower(type)='work'"):
        d=json.loads(row['data'])
        if d.get('merged_into'): continue
        compact={'period':d.get('period'),'authors':[{k:a[k] for k in ['name','entity_id'] if k in a} for a in d.get('authors',[]) if isinstance(a,dict)], 'indexed_by':[{k:x[k] for k in ['source','section'] if k in x} for x in d.get('indexed_by',[]) if isinstance(x,dict)]}
        works[row['id']]={'id':row['id'],'title':d.get('title',row['name']),'path':row['path'],'blob_sha':row['blob_sha'],'sha256':row['sha256'],'data':compact}
    membership=collections.defaultdict(list)
    for row in con.execute('select * from membership'):
        membership[row['work_id']].append(dict(row))
    scope={}; author=collections.defaultdict(set); title=collections.defaultdict(set); clean=collections.defaultdict(set)
    for wid,r in works.items():
        d=r['data']; reasons=[]
        if any('經' in str(x.get('division')) or '经' in str(x.get('division')) or str(x.get('division')).lower() in ('classics','jing') for x in membership[wid]): reasons.append('classification')
        if any(re.search(r'經部|经部|甲部經錄|甲部经录', str(x.get('section',''))) for x in d.get('indexed_by',[]) if isinstance(x,dict)): reasons.append('source_section')
        if any('經義考' in str(x.get('source','')) for x in d.get('indexed_by',[]) if isinstance(x,dict)): reasons.append('jingyikao_source')
        if reasons: scope[wid]=reasons
        r['norm_title']=norm(r['title']);r['clean_title']=imprint(r['title'])
        r['author_keys']=set()
        for a in d.get('authors',[]):
            if not isinstance(a,dict): continue
            for val in (["id:"+a['entity_id']] if a.get('entity_id') else [])+(["name:"+norm(a['name'])] if a.get('name') else []):
                r['author_keys'].add(val); author[val].add(wid)
            for eid in alias_entities.get(norm(a.get('name','')),[]):
                val='candidate_alias:'+eid;r['author_keys'].add(val);author[val].add(wid)
        title[r['norm_title']].add(wid);clean[r['clean_title']].add(wid)
    prior=prior_cases();old_pairs=collections.defaultdict(list);old_ids=set()
    for c in prior:
        ids=members(c)&set(works);old_ids.update(ids)
        for a,b in itertools.combinations(sorted(ids),2):old_pairs[(a,b)].append(c['case_id'])
    edges={}; comparisons=collections.Counter()
    def add(a,b,reason,score=0):
        if a not in scope and b not in scope:return
        a,b=sorted((a,b));key=(a,b)
        if key not in edges:edges[key]={'ids':[a,b],'signals':[],'score':0}
        if reason not in edges[key]['signals']:edges[key]['signals'].append(reason)
        edges[key]['score']=max(edges[key]['score'],score)
    for key, ids in title.items():
        if key and len(ids)>1 and ids&scope.keys():
            for a,b in itertools.combinations(sorted(ids),2):add(a,b,'normalized_exact_title',1)
    for key,ids in clean.items():
        if key and len(ids)>1 and ids&scope.keys():
            for a,b in itertools.combinations(sorted(ids),2):
                if works[a]['norm_title']!=works[b]['norm_title']:add(a,b,'imprint_prefix_variant',.98)
    seen=set()
    for key,ids in author.items():
        if len(ids)<2 or not ids&scope.keys():continue
        for a,b in itertools.combinations(sorted(ids),2):
            if (a,b) in seen or (a not in scope and b not in scope):continue
            seen.add((a,b));comparisons['same_author_pairs']+=1
            ta,tb=works[a]['norm_title'],works[b]['norm_title']
            if min(len(ta),len(tb))<2:continue
            if ta==tb:add(a,b,'shared_author_exact_title',1);continue
            if min(len(ta),len(tb))>=3 and (ta in tb or tb in ta):add(a,b,'shared_author_title_containment',.95)
            if len(set(ta)&set(tb))>=2:
                score=difflib.SequenceMatcher(None,ta,tb,autojunk=False).ratio()
                if score>=.67:add(a,b,'shared_author_fuzzy_title',round(score,4))
    # Same exact title with different author IDs/names is retained for alias and homonym review.
    results=[]
    for pair,e in edges.items():
        e['old_case_ids']=old_pairs.get(pair,[])
        e['is_new_pair']=not bool(e['old_case_ids'])
        e['has_old_member']=bool(set(pair)&old_ids)
        e['titles']=[works[x]['title'] for x in pair]
        e['authors']=[[a.get('name') for a in works[x]['data'].get('authors',[]) if isinstance(a,dict)] for x in pair]
        e['periods']=[works[x]['data'].get('period') for x in pair]
        e['scope_reasons']={x:scope.get(x,[]) for x in pair}
        e['shared_author_keys']=sorted(works[pair[0]]['author_keys']&works[pair[1]]['author_keys'])
        results.append(e)
    results.sort(key=lambda x:(not x['is_new_pair'],not bool(x['shared_author_keys']),-x['score'],x['ids']))
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    for e in results:
        a,b=map(find,e['ids']);parent[a]=b
    groups=collections.defaultdict(list)
    for x in parent:groups[find(x)].append(x)
    dump('candidate-pairs.json',results)
    dump('candidate-groups.json',[sorted(x) for x in groups.values()])
    dump('scope.json',[{'id':x,'title':works[x]['title'],'reasons':y,'membership':membership[x]} for x,y in scope.items()])
    stats={'metadata':metadata,'prior_effective_case_count':len(prior),'all_live_works':len(works),'classics_scope_works':len(scope),'scope_by_reason':dict(collections.Counter(x for y in scope.values() for x in y)), 'unclassified_scope_works':sum(not membership[x] for x in scope),'unique_candidate_pairs':len(results),'unique_candidate_components':len(groups),'candidate_work_ids':len(parent),'old_case_duplicate_pairs':sum(not x['is_new_pair'] for x in results),'new_candidate_pairs':sum(x['is_new_pair'] for x in results),'new_pairs_with_old_member':sum(x['is_new_pair'] and x['has_old_member'] for x in results),'new_pairs_both_members_outside_old_cases':sum(x['is_new_pair'] and not x['has_old_member'] for x in results),'signal_counts':dict(collections.Counter(s for x in results for s in x['signals'])),'comparisons':dict(comparisons),'reviewed_new_cases':0,'confirmed_new_cases':0,'native_mutations':0,'candidate_is_confirmation':False}
    dump('scan-stats.json',stats)
    print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',default='audit/broad-current.sqlite');a=p.parse_args();run(a.db)
