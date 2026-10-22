import json,pathlib,gzip,hashlib,collections,copy
O=pathlib.Path(__file__).resolve().parent;R=O.parents[3]
c=json.load(open(O/'cases.json')); snap=json.load(gzip.open(O/'original-records.json.gz','rt'));books={};bywork=collections.defaultdict(list)
for line in (O/'book-ref-paths.txt').read_text().splitlines():
 p=R/line;b=p.read_bytes();d=json.loads(b)
 if d.get('merged_into') or d.get('work_id') not in snap:continue
 books[d['id']]={'path':line,'sha256':hashlib.sha256(b).hexdigest(),'record':d};bywork[d['work_id']].append(d['id'])
for x in c:
 x['related_books']={i:bywork[i] for i in [x['keeper']]+x['losers']}
 if x['status']!='confirmed':continue
 sf=x['machine_decision']['set_fields'];ds=[snap[i]['record'] for i in [x['keeper']]+x['losers']]
 # Preserve source and explanatory metadata of the same author in the chosen role.
 for a in sf.get('authors',[]):
  for d in ds:
   for b in d.get('authors',[]):
    if a.get('entity_id')==b.get('entity_id') and a.get('role')==b.get('role'):
     for key,val in b.items():
      if key not in a:a[key]=copy.deepcopy(val)
      elif key in ['note','name_basis','dynasty_basis'] and a[key]!=val and val not in a[key]:a[key]+='；'+val
 x['field_decisions']['authors']={'policy':'retain_canonical_identity_merge_metadata','selected':sf.get('authors',[]),'reason':'同一entity_id与role补入note/source/name_basis，异体名保留原始indexed_by与快照；COL-R006两Entity同名同来源但本轮不合Entity。'}
 for k in ['description','loss_status','loss_status_basis']:
  if k in sf:x['field_decisions'][k]={'policy':'explicit_evidence_based_value','selected':sf[k],'reason':x['reason']}
 if any(i in x['book_text_assets'] for i in x['losers']):x['apply_blocker']='loser存在book-text文本版本；须完成保留全部版本的配套迁移后解除，不得只改book-index。'
 if x['keeper']=='d59f2goyyrcw':
  x['apply_blocker']='除book-text资产迁移外，keeper所挂98y6e34lj9为顾嗣立选元诗选本，须先核分选本Work。'
  x['book_anomalies']=['98y6e34lj9 作者顾嗣立role=選、edition=元詩選本，不可默认为四卷全本。']
 if x['keeper']=='d59f2ghjrmdc':
  x['apply_blocker']='keeper所挂98y6e0bgn6为顾嗣立元诗选一卷本，应先分选本Work；四卷书身份可确证。'
  x['book_anomalies']=['98y6e0bgn6 一卷元詩選本，顾嗣立選。']
 if x['keeper']=='d59f2goxekn4':
  x['apply_blocker']='keeper同时挂一卷宋百家诗存选本和五卷/六卷本；先分选本、核吟稿五卷附遗稿一卷，再执行同四库六卷本的Work合并。'
  x['book_anomalies']=['98y5qmro5f 宋百家詩存一卷；98y5qmro5e 五卷遺稿一卷；98y5qmro5d 兩宋名賢小集五卷。']
 if x['keeper']=='d59f2ngf4v0g':x['book_anomalies']=['98y6choxkx 胡思敬/元旷朝代为魏，明显待核；本轮Work身份裁决不沿用该错误朝代。']
 # Reviewer-facing text should avoid embedding an operational merge instruction in product description.
 sources=sf['description']['sources'];name=sf['authors'][0]['name'] if sf.get('authors') else ''
 sf['description']={'text':name+'撰。'+('主著錄為'+str(sf['juan_count']['number'])+'卷。' if sf.get('juan_count') else '')+'另題'+ '、'.join('《'+t+'》' for t in sf['additional_titles'])+'。卷數、版本及原始著錄詳見來源。','sources':sources}
 x['field_decisions']['description']['selected']=sf['description']
classes={}
for x in c:
 if x['status']!='confirmed':continue
 nodes=set(v['node'] for vv in x['classification_inventory'].values() for v in vv)
 if len(nodes)>1:
  target=next((n for n in nodes if n!='zm0666'),None)
  if x['case_id']=='COL-R006':target='zm0671'
  if x['case_id']=='COL-R030':target='zm0680'
  classes[x['keeper']]={'node':target,'reason':'具名作者别集，按原始著录朝代归细类；父类别集仅是较粗粒度。' if x['case_id']!='COL-R006' else '淩義渠一人文集二卷，總目別集類明代之屬明確；另一條通代總集分類來自同來源混掛，保留來源而歸明代別集。','case_id':x['case_id']}
classes['d59f2mojw16o']['reason']='跨朝代题画诗汇编，取通代之属zm0680，优于总集父类zm0676；不是单一作者别集。'
(O/'classification-decisions.json').write_text(json.dumps(classes,ensure_ascii=False,indent=2)+'\n')
(O/'cases.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
with gzip.open(O/'related-books-original.json.gz','wt') as f:json.dump(books,f,ensure_ascii=False)
s={'active_work_scanned':266045,'same_source_summary_candidates':151,'decisions':dict(collections.Counter(x['status'] for x in c)),'confirmed_losers':sum(len(x['losers']) for x in c if x['status']=='confirmed'),'confirmed_with_apply_blocker':sum('apply_blocker' in x for x in c),'related_active_books':len(books)}
(O/'stats.json').write_text(json.dumps(s,indent=2)+'\n')
report=['# 集部扩大去重：恢复批次','', '当前基线 bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca。旧 expanded 目录未保留，本报告从现有原始 JSON 重新核查，不沿用旧确认数。','',f'扫描266,045条active Work，生成151组同四库长提要候选；本批逐案裁定21组确证、13组待核、3组不并。确证涉及22条冗余Work。关联Book '+str(len(books))+' 条，均只审不改；未确认Book重复。','', '确证不等于可立即执行：15组有loser文本版本，须配套book-text迁移。居竹轩另有元诗选本混挂待分。所有候选有完整源档快照、路径和SHA256，所有来源著录按原顺序保留。','', '| 案例 | 裁定 | 题名 | 说明 |','|---|---|---|---|']
for x in c:report.append('|'+x['case_id']+'|'+x['status']+'|'+' / '.join(snap[i]['record']['title'] for i in [x['keeper']]+x['losers'])+'|'+x['reason']+'|')
report+=['','## 外部核查','', '- CiNii BA56562643：https://ci.nii.ac.jp/ncid/BA56562643 。馆藏目录列五卷高太史鳬藻集，别题鳧藻集；扣舷集另列一卷。','- 傅增湘《靜居集》跋原文：https://zh.wikisource.org/wiki/靜居集_(四部叢刊本)/跋 。原编六卷与文渊阁四卷分卷差异有明确说明。','- 黃丹巖先生集与丹岩集的外部书目线索尚未核原本，故仍open，不因相同作者与十卷自动合。','','## 反例与后续','', '同提要不能自动合并：楊澤民《和清真詞》误挂方千里提要；鄧深《大隱居士詩集》误挂李正民提要。四库提要经常合写诗集、文集、续集，151组中大量属于该形态。','', '其余候选保留在same-source-summary-candidates.json。下一批优先抽取同人题名异体与简称；逐条检查全文/选本、全部Book、book-text资产及分类，不做批量相似度合并。']
(O/'report.md').write_text('\n'.join(report)+'\n')
print(s)
