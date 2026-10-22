import json,pathlib,hashlib,gzip,datetime,collections
R=pathlib.Path(__file__).resolve().parents[4]; A=pathlib.Path(__file__).resolve().parent
rows=json.loads((A/'target-records.json').read_text()); D={x['record']['id']:x for x in rows}
def load(i):
 if i not in D:
  pp=list((R/'Work'/i[-3]/i[-2]/i[-1]).glob(i+'-*.json'));assert len(pp)==1,(i,pp)
  D[i]={'path':str(pp[0].relative_to(R)),'record':json.loads(pp[0].read_text())}
 return D[i]
groups=[
('JC-001','d59f27yzh8n5',['d59f27xwgkqp','d59f27xu9wxu','d59f9s18wrup'],'謝萬《周易繫辭注》','各条均谢万注繫辞二卷，隋、两唐、经义考及补晋志明引同条；不是完整周易原典。','注','zm0012','https://zh.wikisource.org/wiki/新唐書/卷057'),
('JC-002','d59f23nxyvic',['d59f24mmvcw8','d59f24mp20p2','d59f24mckiz3','d59fxvkyam0y','d59fyivkw4xs','d59fxs5arbb5'],'劉表《周易章句》','后汉艺文志及马国翰辑本序明确串联十卷、九卷附目录、隋唐五卷、清辑一卷；张惠言辑本亦为景升章句。各辑本的内容与馆藏在各自Book保留，不合并Book。','章句','zm0012','https://www.eee-learning.com/book/1392'),
('JC-003','d59f27wog45f',['d59f27yathqb','d59f27vqf8xu','d59f27te569y','d59f9uw7nu9x'],'孔倫《集注喪服經傳》','丁国钧、黄逢元、吴士鉴补晋志均明言唐志儀禮注系误作全书，通志重出。秦荣光按另列两种只是循通志，保留其异说原文，不视为二书新证。','集注',None,'https://upload.wikimedia.org/wikipedia/commons/2/2a/NLC416-06jh006444-16298_補晉書藝文志.pdf'),
('JC-004','d59f27xxpiww',['d59f27yd05j6','d59f9s1p543l','d59f27y7dvr6','d59f2q3l9v5t'],'鄒湛《周易統略》','经义考、丁国钧补晋志及隋志考证明言隋五卷与两唐统略论三卷是一书异录；清辑一卷是佚文重辑，不另立原作。','撰','zm0012','https://www.eee-learning.com/book/1404'),
('JC-005','d59f2nfolp1f',['d59f2nd4iolc'],'明仁宗《體尚書》','两条作者Entity已同为朱高炽，二卷与尚书中皋陶谟甘誓盘庚等十六篇的内容描述逐字互证。','撰',None,'https://zh.wikisource.org/wiki/明史_(四庫全書本)/卷096'),
('JC-006','d59f24moqs5f',['d59f24mo4b2b','d59f24mhkbno','d59f2q0pbuv5','d59f2qajaygx','d59fkwmxjvnn','d59fyjrniy9s','d59fyfkcv3lu'],'馬融《尚書注》','后汉艺文志引隋十一卷、唐十卷及马国翰辑本序明确说明书序单篇造成卷数差，并说明马国翰四卷与王谟一卷皆其辑本。','注','zm0022',None),
('JC-007','d59f27yxltdu',['d59f27xdqc5e','d59f27s5th4w','d59fxvkzjk76','d59fxx72mb5u','d59fyivm5341','d59fxs5h0268'],'王肅《周易注》','隋两唐十卷同作者原注；清史稿一卷与玉函山房二卷以及孙堂、黄奭、张惠言各辑本均承王肃易注。排除混入曹瞒传的王肃易传条。','注','zm0012','https://zh.wikisource.org/wiki/新唐書/卷057')]
groups.extend([
('JC-008','d59f2nj8w8ao',['d59f6et3qx38'],'趙撝謙《六書本義》','四库提要明言撝谦原名古则；千顷堂与四库均十二卷，同一字学著作，作者Entity已同。','撰',None,'https://zh.wikisource.org/wiki/欽定四庫全書總目_(四庫全書本)/經部/卷041'),
('JC-009','d59f2ng8w45c',['d59f6ethslj4'],'趙撝謙《童蒙習句》','千顷堂赵古则童䝉习句一卷与四库赵撝谦童蒙习句一卷，作者原名已明确，䝉/蒙异体。','撰',None,'https://zh.wikisource.org/wiki/欽定四庫全書總目_(四庫全書本)/經部/卷041'),
('JC-010','d59f2ndpfl6p',['d59fxvllperm','d59f6ehlj094'],'趙撝謙《聲音文字通》','keeper已收四库存目丛书与续修四库的皇极声音文字通三十二卷，新增中国古籍总目两馆明清抄本与其完全对应；千顷堂古则别称同人，洪武十一年序。','撰',None,'https://www.shidianguji.com/zh/book/SK0000A/chapter/1kgsnk8if8tts'),
('JC-011','d59f2nfjlw5f',['d59f2nighmo0','d59f6epcl5vk'],'趙撝謙《學範》','四库提要明确分六门，存目丛书二卷明刻本，千顷堂赵氏学范为同作者；二卷/六篇与志书六卷保存各来源不互相覆盖。','撰',None,'https://ctext.org/wiki.pl?chapter=656254&if=en')
])
allids={i for _,k,ls,*_ in groups for i in [k]+ls};books=collections.defaultdict(list);n=0
for p in (R/'Book').rglob('*.json'):
 n+=1
 try:d=json.loads(p.read_text())
 except:continue
 if d.get('merged_into'):continue
 if d.get('work_id') in allids:books[d['work_id']].append({'id':d['id'],'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'record':d})
classes=collections.defaultdict(list)
for p in (R/'classification/zongmu/members').glob('*.json'):
 d=json.loads(p.read_text())
 for row in d['members']:
  if row[0] in allids:classes[row[0]].append({'node':d['node'],'member':row})
texts={}
for p in (R.parent/'book-text-ref/index/texts').glob('*.json'):texts.update(json.loads(p.read_text()))
cases=[];snapshots={};classification={}
additive={'indexed_by','emendated_by','resources','sources','contained_in','related_works','additional_titles','merged_in','merged_from','merge_history','ai_note','todo'}
for cid,k,ls,label,why,role,node,url in groups:
 rr=[load(i) for i in [k]+ls];ds=[r['record'] for r in rr];kd=ds[0]; assert all(not d.get('merged_into') for d in ds)
 author=dict(kd['authors'][0]);author['role']=role
 sets={'authors':[author]}; removes=[]
 if cid in ['JC-002','JC-003','JC-004','JC-006','JC-007']:
  sets['loss_status']='partially_extant';sets['loss_status_basis']='本组著录明确载马国翰、王谟、孙堂或黄奭辑本；保留原作与各辑本卷数差异于 indexed_by。'
 if cid=='JC-001':sets['title']='周易繫辭注'
 sources=list(dict.fromkeys(e.get('source','') for d in ds for e in d.get('indexed_by',[])))
 sets['description']={'text':label+'。'+why,'sources':sources}
 rg={}
 for d in ds:
  for key,val in d.get('resource_groups',{}).items():
   if key in rg:assert rg[key]==val,(cid,key)
   rg[key]=val
 if rg:sets['resource_groups']=rg
 if kd.get('period_upper'):removes+=['period_upper','period_upper_basis']
 keys=set().union(*(d.keys() for d in ds));decisions={}
 for key in sorted(keys-additive-{'id','revision','revised_at','updated_at'}):
  values={d['id']:d[key] for d in ds if key in d}
  if key in sets:policy='set_explicit'
  elif key in removes:policy='remove_redundant_catalog_upper_bound'
  else:policy='retain_keeper'
  decisions[key]={'policy':policy,'selected':sets.get(key,kd.get(key)),'original_values':values,'reason':'同书不同著录与辑本数据保留在来源条及完整原档；规范主计量沿用keeper，不以清辑卷数覆盖原书卷数。'}
 paths={r['record']['id']:r['path'] for r in rr};sha={i:hashlib.sha256((R/p).read_bytes()).hexdigest() for i,p in paths.items()}
 ev=[{'record_id':d['id'],'field':'indexed_by','entries':d.get('indexed_by',[])} for d in ds]
 asset=[{'id':d['id'],'text_index':texts.get(d['id']),'fragment_mentioned_in_notes':'fragments/' in d.get('ai_note','')} for d in ds if d['id'] in texts or 'fragments/' in d.get('ai_note','')]
 c={'case_id':cid,'cluster_id':cid,'type':'Work','status':'confirmed','label':label,'keeper':k,'losers':ls,'why':why,'paths':paths,'sha256':sha,'evidence':ev,'external_sources':[url] if url else [],'machine_decision':{'set_fields':sets,'remove_fields':removes},'field_decisions':decisions,'classifications':{i:classes[i] for i in [k]+ls},'related_books':{i:[{'id':b['id'],'path':b['path'],'sha256':b['sha256']} for b in books[i]] for i in [k]+ls},'book_text_assets':asset,'apply_prerequisites':['扫描并联动修正 book-text 整理本的 work_id/work_ids；当前本地仅有 texts 索引，不能宣称跨仓引用检查完成。','若 loser 有 fragments 或文本目录，先完成无损迁移并重建 book-text 索引；不得只改 book-index。','Book 只改 work_id，保留每个辑本的作者、卷数、版本和馆藏，不在此组内合并 Book。']}
 cases.append(c)
 if node:classification[k]={'node':node,'reason':'经注属于传说之属；来源丛编指所收版本，不改原注作品性质。'}
 for r in rr:snapshots[r['record']['id']]=r
for i in ['d59f27srzbpe','d59f2q4d1zpc']:
 x=load(i);d=x['record'];snapshots[i]=x
 cases.append({'case_id':'JC-OPEN-'+i,'type':'Work','status':'open','ids':[i],'label':d['title'],'paths':{i:x['path']},'sha256':{i:hashlib.sha256((R/x['path']).read_bytes()).hexdigest()},'evidence':d.get('indexed_by',[]),'why': '同条含宋志王肃传十一卷及三国艺文志曹瞒传，须先分拆误挂著录，不能整体合并。' if i=='d59f27srzbpe' else '谢万注一卷是孝经著录，不能按作者及注字混入繫辞二卷组；待孝经专组复核。'})
(A/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
classification.update({
'd59f27wog45f':{'node':'zm0042','reason':'经部/礼类父子重挂，保留已有更细礼类；本书为仪礼丧服专注。'},
'd59f2nfolp1f':{'node':'zm0020','reason':'经部与书类父子重挂，保留已有书类。'},
'd59f2ndpfl6p':{'node':'zm0161','reason':'小学类与韵书父子重挂，四库提要明言所定韵谱，保留已有韵书节点。'},
'd59f2nfjlw5f':{'node':'zm0488','reason':'四库总目卷131杂家类存目八直接著录学范；六门内容包括教、读、点、作、书、杂，不以作者精小学而归全书为小学。'}
})
(A/'classification-decisions.json').write_text(json.dumps(classification,ensure_ascii=False,indent=2)+'\n')
with gzip.open(A/'original-snapshots.json.gz','wt') as f:json.dump(snapshots,f,ensure_ascii=False)
with gzip.open(A/'related-books.json.gz','wt') as f:json.dump(books,f,ensure_ascii=False)
stats={'target_author_records':len(rows),'confirmed_groups':len(groups),'losers':sum(len(g[2]) for g in groups),'open':2,'book_files_scanned':n,'related_active_books':sum(map(len,books.values())),'native_mutations':0,'book_text_full_scan_complete':False}
(A/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(stats)
