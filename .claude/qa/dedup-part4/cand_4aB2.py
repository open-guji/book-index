"""4a-B 扩展候选：由早先 4aB.json（同题单边对全集）筛出未核过的对——子集未分类的同卷对，以及各部类卷缺对；
剔除族谱方志、卷数不同、已并、责任者已变、已登 dedup-judged、国書线索候选、敦煌。用法：P4WORK=... python3 cand_4aB2.py → $P4WORK/4aB2.json"""
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'feat.py')).read().split("groups=[]")[0])
import json,glob
P=__import__('os').environ.get('P4WORK','/tmp/p4')
d=json.load(open(P+'/4aB.json'))
judged=set()
for f in glob.glob('.claude/qa/dedup-judged/*.tsv'):
    for l in open(f):
        c=l.split('\t')
        if len(c)>2: judged.add(frozenset(c[:2]))
koku=set()
for f in glob.glob('.claude/qa/dedup-kokusho/**/*',recursive=True):
    try: koku|=set(re.findall(r'd59f[0-9a-z]{8}',open(f).read()))
    except Exception: pass
out=[];c=collections.Counter()
for x in d:
    if x['puzhi'] or x['juan']=='异': continue
    if x['juan']=='同' and x['bulei'] in ('經部','史部'): continue
    a,n=x['anon'],x['named']
    if a not in W or n not in W or W[a].get('merged_into') or W[n].get('merged_into'): c['已并']+=1; continue
    if first_author(W[a]) or not first_author(W[n]): c['责任者已变']+=1; continue
    if frozenset((a,n)) in judged: c['已判']+=1; continue
    if a in koku or n in koku: c['国書线索']+=1; continue
    if '敦煌' in (W[n].get('ai_note') or '')+(W[a].get('ai_note') or ''): c['敦煌']+=1; continue
    out.append(x)
print(len(out),c, collections.Counter((x['juan'],x['bulei']) for x in out))
json.dump(out,open(P+'/4aB2.json','w'),ensure_ascii=False,indent=1)
