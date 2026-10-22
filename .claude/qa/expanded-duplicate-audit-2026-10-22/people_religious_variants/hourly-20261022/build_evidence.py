import json,hashlib,pathlib,gzip,subprocess,collections
ROOT=pathlib.Path(__file__).resolve().parents[5]
OUT=pathlib.Path(__file__).resolve().parent
IDS=['hixhjhayeltw','hixi5fxknyts','hixi5fxknytr','hixhjhavlgxw','hixi5eks7m81','hixhd2h9bsyc','hixhd2f8wam8','hixhd2h9bdzw','hixi5vzpexvm','hixhd2f8wakd']
def locate(typ,i):
 p=list((ROOT/typ/i[-3]/i[-2]/i[-1]).glob(i+'-*.json'))
 assert len(p)==1,(typ,i,p)
 return p[0]
def obj(typ,i):return json.loads(locate(typ,i).read_text())
def meta(p):
 raw=p.read_bytes();d=json.loads(raw)
 return {'id':d['id'],'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'primary_name':d.get('primary_name'),'title':d.get('title')}
paths={locate('Entity',i) for i in IDS}
r=subprocess.run(['rg','-l','|'.join(IDS),'Work','Book','Collection'],cwd=ROOT,text=True,capture_output=True)
assert r.returncode in (0,1),r.stderr
refs={i:[] for i in IDS}
for s in r.stdout.splitlines():
 p=ROOT/s; d=json.loads(p.read_text())
 if d.get('merged_into'):continue
 for a in d.get('authors',[]):
  if a.get('entity_id') in refs:
   refs[a['entity_id']].append(d['id']);paths.add(p)
extra=['d59f28mx07wl','d59fxw0uglq8','d59f2hsp84cg','d59fxsymfytd','d59fxsymr7cw','d59f2q855gcg','d59f9bl4cs1y','d59f9bl4o0lk','d59f2q3vkpoi','d59f2pz70k5e','d59f28jd0x6w']
for i in extra:paths.add(locate('Work',i))
bookrefs={}
r=subprocess.run(['rg','-l','|'.join(extra),'Book'],cwd=ROOT,text=True,capture_output=True)
assert r.returncode in (0,1),r.stderr
for s in r.stdout.splitlines():
 p=ROOT/s;d=json.loads(p.read_text())
 if d.get('merged_into'):continue
 if d.get('work_id') in extra:bookrefs.setdefault(d['work_id'],[]).append(d['id']);paths.add(p)
records={str(p.relative_to(ROOT)):json.loads(p.read_text()) for p in paths}
with gzip.open(OUT/'original-records.json.gz','wt',encoding='utf-8') as f:json.dump(records,f,ensure_ascii=False,indent=2)
manifest=[meta(p) for p in sorted(paths)]
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'references.json').write_text(json.dumps({'entity_authors':refs,'work_books':bookrefs,'scope':'All current local Work/Book/Collection authors[].entity_id for ten target entities; Book.work_id for eleven explicitly reviewed works. Does not claim book-text coverage.'},ensure_ascii=False,indent=2)+'\n')
sources=[
 {'url':'https://authority.dila.edu.tw/person/search.php?aid=A001357','title':'DILA A001357 菩提流支','retrieved_at':'2026-10-22','support':'北魏译师；别名菩提留支；列十二因缘论、差摩婆帝授记经、十地经论。','quote':'道希,菩提留支,留支,三藏流支'},
 {'url':'https://authority.dila.edu.tw/person/search.php?aid=A001358','title':'DILA A001358 菩提流志','retrieved_at':'2026-10-22','support':'唐代译师；本名达摩流支，与北魏菩提流支分立；列大宝积经和不空羂索咒心经。','quote':'朝代 Dynasty：唐;'},
 {'url':'https://ci.nii.ac.jp/ncid/BB25631851','title':'CiNii 晦菴先生所定古文孝經句解','retrieved_at':'2026-10-22','support':'通志堂本责任者朱申、成德，非唐玄宗。','quote':'(宋) 朱申注 ; (清) 成徳挍訂'},
 {'url':'https://da.adm.thers.ac.jp/item/n004-20230901-04019','title':'名古屋大学 晦菴先生所定古文孝經句解一卷','retrieved_at':'2026-10-22','support':'馆藏著录为元朱申撰；未提供书影，不冒称核过卷首。','quote':'元朱申撰'},
 {'url':'https://pedia.cloud.edu.tw/Entry/Detail?title=%E5%90%B3%E9%A8%AB%281733-1813%29','title':'台湾教育百科 吴骞','retrieved_at':'2026-10-22','support':'生1733、字槎客、号兔床，海宁藏书家。只有搜索结果检得，非本次完整打开页面；作为年龄矛盾辅证。','quote':'吳騫，字槎客（楂客），一字葵里（揆里），號兔床，又號愚谷。'}]
(OUT/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
def entities(ids):return [meta(locate('Entity',i)) for i in ids]
def works(ids):
 out=[]
 for i in ids:
  d=obj('Work',i);out.append({**meta(locate('Work',i)),'authors':d.get('authors'),'indexed_by':d.get('indexed_by'),'ai_note':d.get('ai_note'),'book_ids':bookrefs.get(i,[])})
 return out
cases=[]
keeper=obj('Entity','hixhd2h9bsyc');loser=obj('Entity','hixi5eks7m81')
overrides={'alt_names':keeper.get('alt_names',[])+[{'name':'釋菩提流志','type':'別名','note':'唐代译师之释氏前缀；DILA A001358 及本库大宝积经总目著录。'}], 'ai_note':keeper.get('ai_note','')+'\n\n[來源 hixi5eks7m81] '+loser['ai_note']+'\n\n2026-10-22 PRV-H001：唐菩提流志与释菩提流志同人，北魏菩提流支另人。证据 DILA A001358 与大宝积经总目责任者；不自动补生卒或改译经角色。','review':loser['review'],'external_ids':loser['external_ids']}
cases.append({'case_id':'PRV-H001','type':'Entity','status':'confirmed','keeper':'hixhd2h9bsyc','losers':['hixi5eks7m81'],'why':'同一唐代译师。释为僧人称谓；keeper所系大宝积经120卷总目直接署唐释菩提流志，loser建档依据不空羂索咒心经亦列DILA A001358作译目录。','records':entities(['hixhd2h9bsyc','hixi5eks7m81']),'evidence':[sources[1]],'work_evidence':works(['d59f28jd0x6w']),'related_work_ids':sorted(set(refs['hixhd2h9bsyc']+refs['hixi5eks7m81'])),'reference_note':'本地三类原生authors引用扫描，keeper仅一Work，loser零引用；建档说明中的三部不是当前引用数。','machine_decision':{'field_overrides':overrides},'field_decisions':{'primary_name':'保留菩提流志；释菩提流志入别名。','dynasty':'双方唐，period双方sui-tang，保留。','external_ids':'keeper缺；保留loser原有none匹配说明，不新造权威ID。','ai_note':'逐条保留并标记来源。','review':'保留unreviewed。','history':'并集既有merged_in/merge_history，新增墓碑及合并历史；源档快照已另存。','authors':'只迁移真实entity_id；不合并Work或Book，不改role或姓名文字。'},'apply_prerequisites':['主会话复验源档hash、全引用、schema与官方索引','跨库book-text检查尚未完成；完成后方可套用','仅本案两ID合并，不能扩大到北魏流支/留支']})
north=['hixhjhayeltw','hixhjhavlgxw','hixi5fxknyts','hixi5fxknytr']
cases.append({'case_id':'PRV-H002','type':'Entity','status':'open','records':entities(north),'why':'北魏流支/留支姓名同一性有DILA直接证据，但整体人物引用含异译与误挂。先拆责任者再全组并条；confirmed identity 不等于可执行整条合并。','evidence':[sources[0]],'work_evidence':works(['d59f2q855gcg','d59f9bl4cs1y','d59f9bl4o0lk','d59f2q3vkpoi','d59f2pz70k5e']),'related_work_ids':sorted(set(sum([refs[i] for i in north],[]))),'blockers':['d59f2q855gcg 同收补宋志求那跋陀罗译与补魏志同本异译，当前作者只菩提留支，需拆分来源/版本。','d59f9bl4cs1y 原摘要明言瞿昙留支即般若留支；不能根据现有entity_id回证归属。','d59f9bl4o0lk、d59f2q3vkpoi 留有般若留支/菩提留支异译争议，须按原目及经首分辨。','d59f2pz70k5e 论主净意、译者菩提流支；当前role撰错误。建武三年出与北魏译期关系须核原经录。'],'next_steps':['核CBETA经首及开元录对应经号，区别论主/译者','为冲突Work拟分拆与Book归属方案；全部引用重验后再议Entity合并']})
cases.append({'case_id':'PRV-H003','type':'Entity','status':'separate','records':entities(['hixhjhayeltw','hixhjhavlgxw','hixhd2h9bsyc','hixi5eks7m81']),'why':'北魏菩提流支/留支与唐菩提流志/留志为两人，DILA分别A001357、A001358，时代、来华经历、译书范围均不同。两者梵文可同写Bodhiruci，不能用罗马字同形推为一人。','evidence':sources[:2],'next_steps':['任何候选归并保留时代与译书边界；流/留及支/志不能统一为无差别字符']})
cases.append({'case_id':'PRV-H004','type':'Work','status':'open','records':[meta(locate('Work',i)) for i in ['d59f28mx07wl','d59fxw0uglq8','d59f2hsp84cg']],'why':'d59f28mx07wl 唐玄宗注的署名与其题名及通志堂载体不合，CiNii与名古屋目录均归朱申。题名重复很可能由合册责任者串接造成，但未回验该故宫贈善023860原始记录，不直接改作者或合Work。','evidence':sources[2:4],'work_evidence':works(['d59f28mx07wl','d59fxw0uglq8','d59f2hsp84cg']),'related_entity_ids':['hixhd2f8wam8','hixhd2h9bdzw'],'next_steps':['查故宫贈善023860目录和卷首，确认其责任者分界','若证实，先修authors及错误传播唐代period，再与朱申孝经句解组比较文本范围','通知经部lane避免将该条作为唐玄宗另注自动排除或立即合并']})
cases.append({'case_id':'PRV-H005','type':'Entity','status':'open','records':entities(['hixhd2f8wakd','hixi5vzpexvm']),'why':'吴骞/吴鶱同拜经楼著述与相同上图URI构成强线索，但keeper目前混有清雍正间刊当涂吴熙伯先生遗训笺释作者吴骞；海宁吴骞生1733，若版本年代无误则不可能在雍正末幼年完成注释。不能把同URI当绝对同人。','evidence':[sources[4]],'work_evidence':works(['d59fxsymfytd','d59fxsymr7cw']),'related_work_ids':sorted(set(refs['hixhd2f8wakd']+refs['hixi5vzpexvm'])),'next_steps':['核雍正刻本题签、序跋与当涂吴氏家谱，辨注释者吴骞是否同名异人或版本年代误载','先拆责任者再并拜经楼同人异写','槎客应按字、兔床按号复核；1813/1814卒年差异另列，不擅改原值']})
(OUT/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
old=json.loads((OUT.parent/'cases-all.json').read_text())
assert not {x['case_id'] for x in old}&{x['case_id'] for x in cases}
oldconfirmed={i for c in old if c['status']=='confirmed' for i in [c['keeper']]+c['losers']}
newconfirmed={i for c in cases if c['status']=='confirmed' for i in [c['keeper']]+c['losers']}
assert not oldconfirmed&newconfirmed
stats={'base':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','new_case_counts':dict(collections.Counter(c['status'] for c in cases)),'confirmed_losers':1,'snapshot_count':len(records),'original_sha256_reverified':all(hashlib.sha256((ROOT/m['path']).read_bytes()).hexdigest()==m['sha256'] for m in manifest),'confirmed_no_overlap_with_existing':True,'native_data_modified':False,'cross_repository_validation':'not_performed'}
(OUT/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False))
