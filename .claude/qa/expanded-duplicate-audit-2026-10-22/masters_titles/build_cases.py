from pathlib import Path
import json,hashlib,gzip,os,collections,copy
O=Path(__file__).resolve().parent;R=O.parents[3]
rows=json.load(gzip.open(O/'candidate-snapshots.json.gz','rt',encoding='utf-8')) if (O/'candidate-snapshots.json.gz').exists() else json.loads((O/'candidate-snapshots.json').read_text());cand=json.loads((O/'candidate-alias.json').read_text());classes=json.loads((O/'classifications-before.json').read_text())
C=[];snap={};classdec={}
def get(i,t='Work'):
 if i in rows:return rows[i]
 p=next((R/t/i[-3]/i[-2]/i[-1]).glob(i+'-*.json'));b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'record':json.loads(b)}
def add(keeper,loser,why,typ='Work',setf=None,node=None,rule='same-source-record',status='confirmed'):
 ids=[keeper,loser];xs=[get(i,typ) for i in ids];ds=[x['record'] for x in xs]
 case={'case_id':f'MR-{len(C)+1:03d}','type':typ,'status':status,'keeper':keeper,'losers':[loser],'title':ds[0]['title'],'reason':why,'rule':rule,'records':[{k:x[k] for k in ['path','sha256']}|{'id':i} for i,x in zip(ids,xs)],'evidence':[{'id':i,'indexed_by':d.get('indexed_by',[]),'sources':d.get('sources',[]),'source_record_note':d.get('ai_note','')} for i,d in zip(ids,ds)],'machine_decision':{'set_fields':setf or {},'remove_fields':[]},'field_decisions':{},'apply_prerequisites':['全庫有效引用改指keeper；建立loser墓碑並保留歷史合併帳。','檢查book-text整理本/輯佚檔之跨庫引用；本分道沒有完整book-text快照，不能宣稱聯動檢查完成。']}
 for k in set().union(*(d.keys() for d in ds)):
  vals=[d.get(k) for d in ds]
  if k in (setf or {}): act='explicit_set';val=setf[k]
  elif k in ['id','title']:act='retain_keeper';val=vals[0]
  elif k in ['revision','revised_at','updated_at']:act='bump_by_schema';val=None
  elif k in ['indexed_by','emendated_by']:act='append_preserve_order';val=None
  elif k in ['sources','resources','additional_titles','related_works','contained_in','merged_in','merged_from','merge_history']:act='union_preserve_payload';val=None
  elif k=='ai_note':act='preserve_with_original_id';val=None
  elif vals[0]==vals[1]:act='equal_keep';val=vals[0]
  elif vals[0] is None:act='copy_loser';val=vals[1];case['machine_decision']['set_fields'][k]=val
  else:raise RuntimeError((keeper,k,vals))
  case['field_decisions'][k]={'action':act,'selected':val}
 if node:
  case['classification_decision']={'node':node,'reason':'同一作品的專門內容分類優先；合編/叢編是來源載體，原著錄section保留於indexed_by。','before':{i:classes.get(i,[]) for i in ids}}
  classdec[keeper]=case['classification_decision']|{'member_source':'中國古籍總目'}
 C.append(case)
 for i,x in zip(ids,xs):snap[i]=x
 return case
add('d59fydyduha8','d59fyfkh8f7k','完整 indexed_by 相同，均同一上圖源記錄 t5fdt5mvl7kspg0x；差異是一次晉升前補作者，何粲注在兩條原文均明示。',setf={'authors':get('d59fydyduha8')['record']['authors'],'dynasty':'宋','period':'song','period_basis':'據 authors[0].dynasty「宋」'},node='zm0513')
add('d59fy2maxnnk','d59fy6kgwm4g','完整 indexed_by 相同、源記錄 drwyyz2b2gg0i5fi 相同；一側佚名為漏錄，原文清雲龕道人等撰已於keeper補入。',setf={'authors':get('d59fy2maxnnk')['record']['authors']},node='zm0523')
add('d59fydh8f1fm','d59fydxeknwg','同一總目著錄、同一組8源版本；完整 indexed_by 相同，差異僅漏錄輯者黃秩模。',setf={'authors':get('d59fydxeknwg')['record']['authors']},node='zm0549')
add('d59fydxphyww','d59fyfkj3ugx','完整兩條 indexed_by 相同，來源 mn24bl1ybmaouwyn 及歷史合併帳相同；差異僅漏錄撰者葉樞。',setf={'authors':get('d59fydxphyww')['record']['authors']},node='zm0270')
add('d59fy9ep4ikg','d59fydymwd1c','完整三條 indexed_by 及歷史合併帳相同；同一譯本同一導入源 wjj7a2f4dl1egcfr，另一側authors被清空。保留闍那崛多譯；不是把不同譯者同名經合併。',setf={'authors':get('d59fy9ep4ikg')['record']['authors']},node='zm0524')
# Each pair manually examined in full, beyond alias-string matches.
settings=[(1,0,'zm0337','原題明列楊椒山先生遺訓為異名；同一楊繼盛、同一一卷家訓，只有尊稱題差異。'),(4,1,'zm0418','原題明列青囊敍為異名；曾文辿、一卷完全相同，序/敍為題名異寫，非增訂注本。'),(12,1,'zm0389','原題明列新刊/新刻題為版本冠詞；同一朱棟隆、一卷方論，責任者無增注差異。'),(14,0,'zm0357','總目明列圖像水黃牛經大全異名；喻仁與喻傑二人、二卷相同，刻本/石印本分留Book。'),(15,0,'zm0389','原題明列刺種牛痘要法異名；同一余楙一卷、無增注責任者，叢編子目是同書收入不同載體。'),(22,0,'zm0399','紀畧/紀要在原題明列異名；兩側 author_info 均曹存心撰、吳元善輯，相同二重責任，非另一作者醫案。'),(23,1,'zm0384','原題明列沈注金匱要畧為異名，沈明宗、二十四卷同；合併的是同一注本，並非張仲景原典。'),(31,1,'zm0336','原題明列宰嘉訓俗為異名；同一陸隴其、一卷，差異為作者諡號冠詞。')]
settings += [
(36,0,'zm0399','原題明列千里醫案異名；張千里、五卷同，沒有另編者或增注層。'),
(39,1,'zm0388','新刻祕授為題名冠詞，原題列為異名；龔居中、四卷及外科內容一致。'),
(47,1,'zm0389','原題明列東園痘症要訣異名；吳子揚輯、二卷同，保產痘症合編本僅為收入載體。'),
(49,0,'zm0525','同一釋處觀三卷音義書，原題明列紹興重雕大藏音異名，無異譯者之別。'),
(54,1,'zm0390','原題明列外治壽世方異名，鄒存淦輯、四卷同，初編未與續編相混。'),
(55,1,'zm0399','明列薛生白醫案異名，兩條都明指薛雪且一卷；不涉及其他薛氏醫家。'),
(57,0,'zm0360','同一周子幹三卷合輯，先生敬稱有無不改範圍；不是將某一子書併進三書。'),
(63,1,'zm0360','原題明列知醫必辨異名；含飴堂冠詞有無，責任者均李文榮，無續補或注本層。')]
for n,pos,node,why in settings:
 ids=cand[n]['ids'];k=ids[pos];l=ids[1-pos];sf={}
 if n==14:
  au=copy.deepcopy(get(k)['record']['authors']);au[1]['source']=copy.deepcopy(get(l)['record']['authors'][0]['source']);sf['authors']=au
 if n==22:sf['authors']=get(k)['record']['authors']+[{'name':'吳元善','role':'輯','dynasty':'清'}]
 if n==23:sf['authors']=get(k)['record']['authors']
 add(k,l,why,setf=sf,node=node,rule='explicit-alias-same-responsibility-and-scope')
# Book duplicate keys require same instance, all payloads, and normalized explicit promotion.
for k,l,w in [('993wfb6juo','993wunomps','d59fydh8f1fm'),('993wi5ke0w','993wult7gh','d59fydh8f1fm'),('993wvk5b7l','993yiwhfcx','d59fydyduha8')]:
 a,b=[get(i,'Book')['record'] for i in [k,l]];ignore={'id','work_id','contained_in'}
 assert {x:y for x,y in a.items() if x not in ignore}=={x:y for x,y in b.items() if x not in ignore}
 promos={};norm=[]
 for ci in a.get('contained_in',[])+b.get('contained_in',[]):
  ci=copy.deepcopy(ci);i=ci['id'];p=R/'promotions'/(i[-2:]+'.json');pr=json.loads(p.read_text()).get('promotions',{}).get(i) if p.exists() else None
  if pr:promos[i]=pr;ci['id']=pr['production_id']
  if ci not in norm:norm.append(ci)
 assert len(norm)==1
 cc=add(k,l,'同一上圖 instance ID、同一逐項館藏 item、卷數/附錄/版本及全部業務欄位完全相同；僅id、已確認重複work_id、草稿Collection晉升ID不同。',typ='Book',setf={'work_id':w,'contained_in':norm},rule='same-instance-full-payload-explicit-promotion')
 cc['promotions_evidence']=promos;cc['machine_decision']['work_resolution']={'work_id':w};cc['depends_on_work_merge']=w
 if k=='993wvk5b7l':cc['followup_issue']='原Book何粲標唐、Work原著錄標宋，屬兩重來源時代衝突；此次同實例去重保留原值，不據此推定朝代。影印本與宋刻原本絕不可併。'
# Explicit negative controls and difficult cases, no machine action.
negative={2:('open','焦氏條另附十藥神書一卷，另一側叢編範圍不明；須核對書影/子目而非僅括注。'),5:('open','一側地理點穴撼龍經十卷、清高其倬批；另一側原典一卷，存在增批與內容範圍差。'),7:('open','同作者王植但8卷/14卷，需確認改編或分卷差異。'),9:('open','同源總目一卷/二卷同注者，尚須版本目錄對照。'),13:('separate','張鶩翼重訂與徐大椿評為不同加工層，不將相同陳實功基礎作者誤作同一Work。'),19:('open','一側含續補一卷，叢編子目範圍未明，保持先前待核。'),20:('open','楊慎原作與胡世安補三卷閏集一卷責任範圍待分層。'),24:('open','憨山夢遊全集55卷與20卷+年譜2卷、編者組合不同，需檢原目。'),29:('separate','同名同天親原作，但菩提流支與真諦各自漢譯，依庫例分立。'),32:('open','雪嶠禪師語錄十卷/六卷，編纂範圍及年代不同，不能僅弘歇名同即合。'),33:('open','脈因證治四卷/二卷，總目分列且未核分卷關係。'),34:('separate','經正文與讀誦前啓請法為不同文本範圍，括注經名不能判同書。')}
negative.update({
40:('open','華嚴疏鈔會本80卷/220卷，需校核會編結構，不能僅作者澄觀相同即併。'),
42:('separate','黃氏畫譜括號逐列八種畫譜，六言唐詩畫譜只是其中一種，為整體與組成部分。'),
43:('open','素問玄機原病式同薛時平注但一卷/二卷，先核版本分卷。'),
44:('separate','因明正理門論同原作但義淨/玄奘不同漢譯，分立。'),
46:('open','參同契注/考異涉及一卷與三卷、黃瑞節附錄及名字切分錯誤，須分層核定。'),
50:('open','鄉守輯要合抄十卷與十二卷，合抄可能節取，不把括號別名當全本同一證據。'),
52:('open','痘疹玉髓金鏡錄三卷首一卷與四卷圖像一卷、陸道元補遺等責任層不同，須核增補。'),
53:('separate','十竹齋書畫譜含書畫册等八種，書畫册一卷是組成部分，非全書別名。'),
56:('open','西銘一條混朱熹注與無注原典著錄，先拆責任層，不將事天謨原典整條併入。'),
58:('open','夢溪筆談二十六卷與一卷叢編節本可能不同範圍，須核原目及起訖。'),
59:('open','關中四先生要語錄另一側有李元春註，是注本層差，暫不併。'),
60:('open','上蔡先生語錄一側含張伯行重訂、另一側朱熹role混撰/輯，須核編纂層。'),
64:('open','二程全書68卷與51卷屬編次範圍差，未核目錄不可合。'),
94:('open','吳又可瘟疫論含補遺一卷而溫疫論僅二卷；須核補遺是否另作及各版本範圍，保持待核。')})
for n,(status,why) in negative.items():
 ids=cand[n]['ids']; xs=[get(i) for i in ids]; C.append({'case_id':f'MR-{len(C)+1:03d}','type':'Work','status':status,'ids':ids,'titles':[x['record']['title'] for x in xs],'reason':why,'records':[{'id':i,'path':x['path'],'sha256':x['sha256']} for i,x in zip(ids,xs)],'next_step':'核對各版本目錄及正文起訖，尋書目明文，不按相似度自動合併。'})
 for i,x in zip(ids,xs):snap[i]=x
ids=['d59fy113p4w1','d59fy113p4w0'];xs=[get(i) for i in ids]
C.append({'case_id':f'MR-{len(C)+1:03d}','type':'Work','status':'open','ids':ids,'titles':[x['record']['title'] for x in xs],'reason':'性理會通續編42卷與性理大全會通70卷，同鍾人傑而分題明載續編；不可只按近題同作者合。若另有42卷同書條目，須先定位原本目次再擴組。','records':[{'id':i,'path':x['path'],'sha256':x['sha256']} for i,x in zip(ids,xs)],'next_step':'核續編與正編目次起訖，獨立查找同42卷異題本。'})
for i,x in zip(ids,xs):snap[i]=x
(O/'cases.json').write_text(json.dumps(C,ensure_ascii=False,indent=2)+'\n');(O/'classification-decisions.json').write_text(json.dumps(classdec,ensure_ascii=False,indent=2)+'\n')
with gzip.open(O/'reviewed-original-records.json.gz','wt',encoding='utf-8') as f:json.dump(snap,f,ensure_ascii=False,indent=2)
(O/'stats.json').write_text(json.dumps(dict(collections.Counter((c['type']+'_'+c['status']) for c in C)),ensure_ascii=False,indent=2))
print('cases',len(C),dict(collections.Counter(c['status'] for c in C)))
