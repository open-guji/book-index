from pathlib import Path
import json,copy,collections
D=Path(__file__).parent;E=json.loads((D/'batch2-entity-snapshots.json').read_text());W=json.loads((D/'batch2-work-snapshots.json').read_text());R=json.loads((D/'batch2-references.json').read_text());old=json.loads((D/'cases.json').read_text());old=[c for c in old if int(c['case_id'][-3:])<=10]
N={v['record']['primary_name']:k for k,v in E.items() if k!='hixi8us1n2xj'}
configs=[
('錢易',['錢希白'],'confirmed',['d59f2hu6wxs1','d59f2hket91f'],'《南部新書》提要明載錢易字希白，同一條國史經籍志責任者作錢希白；錢希白名下洞微志亦與錢易相應。','https://id.ndl.go.jp/auth/ndlna/a1100013019'),
('莊綽',['莊季裕'],'confirmed',['d59f2hu1ao00','d59fy2dz9uyp'],'雞肋編提要直載季裕名綽以字行；總目作宋莊季裕（綽），明堂針灸經與膏肓灸法亦明載莊綽季裕。','https://ci.nii.ac.jp/ncid/BA7872416X'),
('史堪',['史載之'],'confirmed',['d59f2hfri1vk','d59f2hhdk6wx','d59f2hrdgt8g'],'直齋書錄解題指南方載蜀人史堪載之撰，續修四庫史載之方責任者宋史堪；所繫作品均為此醫家。',None),
('陸德明',['陸元朗'],'confirmed',['d59f28j8nll0'],'經典釋文提要明載元朗字德明以字行；同條新舊目錄題陸德明與陸元朗。兩者是本名與通行字，不應將元朗再寫成字。',None),
('柳宗直',['柳正夫'],'open',['d59f28jsy0w6','d59f2qajay9t'],'宗直已有字正夫，然而正夫孤立條僅西漢蒙求一卷，尚無足夠原始資料將它與宗直西漢文類四十卷繫為同一作者；不能由共字或漢字題名推定。',None),
('沈束',['沈宗約'],'separate',['d59f2ncuubr4','d59frybvhog1'],'沈束為明嘉靖人物；沈宗約名下潭影軒詞總目明載清人，清道光十八年刻。現有資料指向異人，不能用沈束字宗約合併。',None),
('朱敦儒',['朱希真'],'open',['d59f2hgz79xe','d59fryddhqfd'],'朱敦儒字希真與樵歌作品關係強；但 keeper 有可疑朱敦儒陳淵集二十六卷，僅以題名前綴歸人，應先核宋史原段是否串接兩人。',None),
('俞琰',['俞玉吾'],'open',['d59f2gifal8h','d59f2gcybugx','d59fs7txedja'],'元俞琰字玉吾無疑，但 keeper 混入清俞琰輯咏物詩選、詠物詩詞及兩條清刻 Book 責任者；須拆分同名清人，不可整體合併帶入。',None),
('李杲',['李東垣'],'open',['d59f2j514w74','d59f2gijcoaq','d59f2j572eio'],'李杲自號東垣老人；但 keeper《此事難知》現繫李杲，提要明說元王好古撰，並斥東垣十書屬李杲為誤。合輯責任者範圍和誤繫先修，才整併。',None),
]
for num,(kn,lns,status,proof,why,url) in enumerate(configs,11):
 k=N[kn];ls=[N[n] for n in lns];members=[k]+ls;kd=E[k]['record'];ids=sorted({v for m in members for v in R[m]})
 c={'case_id':f'PNA-R{num:03}','status':status,'type':'Entity','label':' / '.join([kn]+lns),'keeper':k,'losers':ls,'paths':{m:E[m]['path'] for m in members},'sha256':{m:E[m]['sha256'] for m in members},'why':why,'evidence_refs':[{'work_id':wid,'path':W[wid]['path'],'sha256':W[wid]['sha256'],'indexed_by':W[wid]['record'].get('indexed_by',[]),'description':W[wid]['record'].get('description')} for wid in proof],'external_evidence':[] if not url else [{'url':url,'finding':why,'accessed':'2026-10-22'}],'related_record_ids':ids,'related_counts':dict(collections.Counter(W[x]['record']['type'] for x in ids))}
 if status=='confirmed':
  fields={key:copy.deepcopy(val) for key,val in kd.items() if key not in {'id','type','schema_version','subtype','revision','revised_at','updated_at','ai_note','merged_in','merge_history'}}
  alt=fields.setdefault('alt_names',[])
  if kn=='陸德明':
   for a in alt:
    if isinstance(a,dict) and a.get('name')=='元朗':a.update(type='別名',note='本名；《經典釋文》四庫提要明載元朗字德明。')
  for n in lns:
   if not any(isinstance(a,dict) and a.get('name')==n for a in alt):alt.append({'name':n,'type':'別名' if kn=='陸德明' else '別稱','note':'本名（通行名以字行）' if kn=='陸德明' else '姓連字的著錄稱呼；姓名關係見本案原始著錄。'})
  desc=fields.setdefault('description',{});sources=desc.setdefault('sources',[])
  for l in ls:
   for s in E[l]['record'].get('description',{}).get('sources',[]):
    if s not in sources:sources.append(copy.deepcopy(s))
  if url:sources.append({'name':'人物名稱權威／館藏書目核查','type':'url','details':url})
  c['machine_decision']={'field_overrides':fields,'field_delete':[]}
  c['field_decisions']=[{'field':key,'decision':('append original notes/history with owner attribution' if key in {'ai_note','merged_in','merge_history'} else 'union description sources; keep keeper text' if key=='description' else 'retain keeper scalar/basis/identifier; archive full loser original; do not use loser to silently overwrite biography')} for key in sorted(set().union(*(E[l]['record'].keys() for l in ls))) if key not in {'id','type','subtype','schema_version','revision','revised_at','updated_at','primary_name'}]
  c['reference_policy']='Redirect live authors[].entity_id for all types; preserve name/role/source. Keep tombstones/history and rebuild indexes.'
  c['caveats']=['Existing keeper biographical fields are retained as historical metadata, not freshly certified by this identity audit.']
  if kn=='陸德明':c['caveats'].append('另一條同名 hixi8us1n2xj 暫不納入：其孝經註疏 d59fxxkxqrr4 列陸德明音義，但所存兩段 indexed_by 未列此責任者，待查具體版本附音。')
 else:c['apply_blocker']=why
 old.append(c)
(D/'cases.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
for name,new in [('entity-snapshots.json',E),('work-snapshots.json',W),('references.json',R)]:
 p=D/name;current=json.loads(p.read_text());current.update(new);p.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
allW=json.loads((D/'work-snapshots.json').read_text());counts=dict(collections.Counter(c['status'] for c in old));counts['confirmed_losers']=sum(len(c['losers']) for c in old if c['status']=='confirmed');counts['referenced_records']=len(allW);counts['scanned_active_people']=52806;counts['candidate_pairs']=696;(D/'stats.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
p=D/'report.md';txt=p.read_text().replace('本批確認 9 組、10 個被併 ID；另 1 組待核。21 條 Entity、148 條真正 authors 引用已保存完整快照及 SHA256（其中同一條可被兩 Entity 同時引用）。','累計確認 13 組、14 個被併 ID；5 組待核、1 組判異人。兩批快照均已保留，數目以 stats.json 為準。新掃 52,806 位活躍人物，產生 696 對候選；候選不等於重複。');txt+='\n## 第二批追加\n\n| 編號 | 人物組 | 判定 | 原因 |\n|---|---|---|---|\n'
for c in old[10:]:txt+='| '+c['case_id']+' | '+c['label']+' | '+c['status']+' | '+c['why']+' |\n'
txt+='\n發現兩項實質混人／誤繫風險：俞琰含清代同名編者；李杲含《此事難知》王好古著作。這些案件先保留，不能用可靠的姓名同一性掩蓋不可靠的作品歸屬。\n';p.write_text(txt)
print(counts)
