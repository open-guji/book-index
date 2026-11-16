"""用 indexed_by[source=中國地方志總目提要].section 回填 Work.region（迁移，不改 revision）。仓根执行：backfill_region.py [--apply]"""
import sys,os,json,glob
SRC='中國地方志總目提要'; apply='--apply' in sys.argv; n=skip=conflict=0
for p in glob.glob('Work/*/*/*/*.json'):
    s=open(p).read()
    if SRC not in s: continue
    d=json.loads(s)
    if d.get('merged_into'): continue
    secs=[i.get('section') for i in d.get('indexed_by',[]) if isinstance(i,dict) and i.get('source')==SRC and i.get('section')]
    if not secs: continue
    if len(set(secs))>1: conflict+=1; print('多地区',d['id'],secs); continue
    if d.get('region'): skip+=1; continue
    d['region']=secs[0]; n+=1
    if apply: open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('回填',n,'已有',skip,'多地区跳过',conflict)
