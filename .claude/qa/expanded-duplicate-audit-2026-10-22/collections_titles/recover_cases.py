import pathlib,json,hashlib,gzip,collections,copy
R=pathlib.Path(__file__).resolve().parents[4]; O=pathlib.Path(__file__).resolve().parent
assert (R/'Work').exists(),R
def load(i):
 p=next((R/'Work').glob('/'.join(i[-3:])+'/'+i+'-*.json')); b=p.read_bytes();return {'id':i,'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'record':json.loads(b)}
# Explicit, individually reviewed decisions. Candidate generation is not adjudication.
specs=[
('confirmed','d59f2nkoedxf',['d59f6efves5h','d59fymbwry0w'],'高啟五卷古文集，鳬/鳧異體；CiNii BA56562643 明列高太史鳬藻集別題鳧藻集。扣舷集為附刊另集，不把五卷加成六卷。'),
('confirmed','d59f2nj0gtmq',['d59f2njnke0w'],'同一四庫總目提要、同一淩義渠，詩四卷文二卷共六卷；裸題條重出。'),
('confirmed','d59f2nfak0ld',['d59f2nkpnc3l'],'同一四庫提要明記詩671首附奏疏二篇，總目原題與四卷相同；中國古籍總目明記郭鯤溟集（鯤溟詩集）。'),
('confirmed','d59f2ndsv7cz',['d59f6emqxyx1'],'黃雲字應龍崑山人；千頃堂與四庫責任者、字、籍貫俱同，丹岩/丹巖為號及書名異體。'),
('confirmed','d59f2ngf4v0g',['d59f6eigfi13'],'張羽字來儀更字附鳳，兩條均同人同集；傅增湘四部叢刊本跋明述原編六卷與文淵閣改編四卷之關係，屬分卷差異。'),
('confirmed','d59fxrrlvhtu',['d59fyiclljwg'],'兩條皆淩義渠文集二卷；keeper ai_note已完整列loser四個上圖來源記錄，並明記曾留於Work級而未建Book。同一來源重出，兩個Entity暫保留但統一Work作者指向keeper。'),
('confirmed','d59f2goyyrcw',['d59f2gotyyo0'],'同一四庫四卷提要；中國古籍總目明記居竹軒詩集（居竹軒集）四卷，成廷珪同一責任者。'),
('confirmed','d59f2gpbrhmo',['d59f2gpb50jl'],'同一呂誠四庫提要，八卷附補遺一卷；另一條總目也著錄來鶴亭集八卷補遺一卷。'),
('confirmed','d59f2hj0va4g',['d59f2hry2h37'],'蘇泂同一八卷四庫輯本提要；另一條總目明記泠然齋詩集八卷。保留直齋十二卷與提要二十卷異說在來源，不當作已校定數字。'),
('confirmed','d59f2miftq80',['d59f2q8otekh'],'完全同一四庫十六卷著錄及儲大文提要；存研為存硯異寫，空作者條有明確author_info可回歸。'),
('confirmed','d59f2hsg68ld',['d59f2hrl9qtc'],'晁公溯/晁公遡同一Entity，四庫五十四卷原條及提要相同；總目明記新刊嵩山居士文全集（嵩山集、嵩山居士文集）。'),
('confirmed','d59f2heuewar',['d59f2hqh04qq'],'同一林希逸三十卷續集，四庫提要明稱此續集謂竹溪十一稿。與已佚六十卷前集保持分立。'),
('confirmed','d59f2hjr37r5',['d59f2hu51iip'],'陳耆卿同一四庫十卷輯本提要；窗/窻字形差異，不涉及補遺條。'),
('confirmed','d59f2hs6t4ao',['d59f2hgpix34'],'徐元傑同一四庫十二卷輯本，楳/梅、埜/野字形差異；原二十五卷資訊保留來源。'),
('open','d59f2ndsv7cz',['d59f2ndp4cn8'],'黃丹巖先生集十卷很可能同丹岩集；目前只有同作者卷數和公開目錄別名，待核南京本卷首、目錄或原始序跋再併。'),
('open','d59f2nj0gtmq',['d59f6efhzkso','d59fy1g7rlkx'],'遺集未明卷數來源、詩四卷文二卷組合接近，待核版本目錄及Entity別名後再與六卷本合併。'),
('separate','d59f2nj0gtmq',['d59fxqlhrvgg'],'四庫六卷為詩四文二且明言不載奏疏；淩忠介詩集二卷奏疏四卷內容結構不同，不能因總卷數同為六而合。'),
('separate','d59f2ngf4v0g',['d59fs7swvlz5'],'張來儀集一卷為明俞憲輯盛明百家詩選本；不可與張羽靜居集四/六卷全本合。'),
('separate','d59f2hpd1r7n',['d59f2hpdo8ap'],'楊澤民與方千里各有和清真詞；前者錯掛後者四庫提要。提要相同在此是污染證據，不是同書證據。'),
('open','d59f2hr2uqrk',['d59f2hu9eu4h'],'大隱居士詩集作者鄧深但所掛提要為李正民大隱集；需分拆來源/版本，不能整條合。'),
('open','d59f28k1dfk4',['d59f2huigpvm'],'兩條同宋李若水三卷集提要，但前者錯繫唐代同名人物Entity；先查其全部Book和Entity污染再決定Work合併。'),
('open','d59f2gny4r9d',['d59f2mi8n9q9'],'陳秋岩詩集錯切作者宜甫並錯定清代，提要實為元陳宜甫；需先審Book及錯繫人物的整體影響。'),
('open','d59f2go1vls1',['d59f2gnw9c01'],'此山集與此山詩集先保留：此前有四卷選本與十卷原集反證，此次尚未獨立重驗外部原件。'),
]
specs += [
('confirmed','d59f2ghjrmdc',['d59f2godqmf5'],'袁易同一四庫提要，兩條四卷且無另書著錄；裸系來源的靜春堂詩與靜春堂集重出。'),
('confirmed','d59f2neyozya',['d59f2nkk12ir'],'薛瑄同一四庫提要，明記張鼎校定詩文1700篇24卷，敬軒文集條別名也明列薛文清集。'),
('confirmed','d59f2ndlzz7k',['d59f2nkuydc3'],'胡居仁同一四庫三卷原題與提要，僅省公字；胡文敬集條明列胡文敬公集別題。'),
('confirmed','d59f2hqivk02',['d59f2hrngem8'],'薛師石同一四庫一卷詩集提要，瓜廬集僅裸系此來源且別名瓜廬詩；不把附錄一卷算成主體兩卷。'),
('confirmed','d59f2goxekn4',['d59f2hr6wttu'],'吳龍翰同一四庫提要，兩題總目各載六卷；古梅為其號，吟稿/遺稿條明列互為別名，附方秋崖和百韻保留版本層。'),
('confirmed','d59f2nk78bup',['d59f2nj70sua'],'溫純同一四庫三十卷提要，溫恭毅集條僅裸系該來源且別題溫恭毅公集。'),
('confirmed','d59f2mojw16o',['d59f2puzxp1c'],'同一康熙四十六年御定一百二十卷題畫詩集提要，陳邦彥奉敕編來源另由清史稿與總目支持。'),
('open','d59f2moj9k3l',['d59f2mif794x'],'敬業堂詩集條總目為吳翌鳳選本四卷，敬業堂集五十卷；提要重複是混掛訊號，不整體合併。'),
('open','d59f2njh0e82',['d59f2nk1xam8'],'幔亭集明史與總目二十卷，四庫幔亭詩集十五卷；尚缺篇目和版本演變證據。'),
('open','d59f2gozl8g1',['d59f2gi7sw76'],'金王若虛誤切成金若虛，所掛Entity hixhd2h9boid與王若虛不同；先核人物及版本引用。'),
('open','d59f2nke3jsz',['d59f2nijm0hs'],'提要作者佘翔，條目卻繫余翔 hixhd2h9bouh；需先核是否污染而非整條人物合併。'),
('open','d59f2hjfuo75',['d59f2hrnrn5s'],'二薇亭集四庫一卷，二薇亭詩集總目四卷；需對四卷諸本是否混整部永嘉四靈詩，不能僅同提要合併。'),
('open','d59f2hi2ueww',['d59f2hql27sw'],'四庫方泉集賦一卷詩三卷，方泉詩集有詩選本風險；需先清查一卷和四卷本內容。'),
('open','d59f2hqy66ma',['d59f2huba9ds'],'文溪存稿二十卷與文溪集異卷本待核；同提要不足排除選本或範圍不同。'),
]
cases=[];snap={}
for n,(status,k,ls,why) in enumerate(specs,1):
 records=[load(i) for i in [k]+ls];snap.update({x['id']:x for x in records}); ds=[x['record'] for x in records]; kd=ds[0]
 c={'case_id':f'COL-R{n:03d}','type':'Work','status':status,'keeper':k,'losers':ls,'reason':why,'records':[{a:x[a] for a in ['id','path','sha256']} for x in records], 'evidence':[{'id':x['id'],'title':x['record']['title'],'authors':x['record'].get('authors',[]),'indexed_by':x['record'].get('indexed_by',[])} for x in records]}
 if status=='confirmed':
  sf={};remove=[];fd={};keys=set().union(*(d.keys() for d in ds))
  special={'id','type','schema_version','revision','revised_at','updated_at','ai_note','todo','review','merged_in','merged_from','merge_history','indexed_by','emendated_by'}
  for key in sorted(keys-special):
   vals=[d[key] for d in ds if key in d]
   if key=='resource_groups':
    u={}
    for v in vals:
     for kk,vv in v.items():
      assert kk not in u or u[kk]==vv,(k,kk);u[kk]=vv
    sf[key]=u;policy='union_by_key'
   elif key in ['resources','sources','contained_in','related_works','additional_titles','additional_works']:
    u=[]
    for v in vals:
     for x in v:
      if x not in u:u.append(x)
    if key=='additional_titles':
     u=list(dict.fromkeys(u+[d['title'] for d in ds[1:]]));u=[x for x in u if x!=kd['title']]
    sf[key]=u;policy='union_preserve'
   elif key in ['period_upper','period_upper_basis'] and kd.get('period'):
    remove.append(key);policy='remove_obsolete_catalog_bound';fd[key]={'policy':policy,'reason':'作品时代已有作者及原始著录直接证据，旧目录成书上限不优先于作品时代。'};continue
   else:
    sf[key]=copy.deepcopy(kd.get(key,vals[0]));policy='retain_keeper' if key in kd else 'preserve_loser_only'
   fd[key]={'policy':policy,'selected':sf[key],'reason':'见逐案原始著录及完整快照；来源与版本差异保留于indexed_by/Book。'}
  sf['additional_titles']=list(dict.fromkeys(sf.get('additional_titles',[])+[d['title'] for d in ds[1:]]))
  sources=list(dict.fromkeys(x.get('source') for d in ds for x in d.get('indexed_by',[]) if x.get('source')))
  sf['description']={'text':kd['title']+'。'+why,'sources':sources}
  if k=='d59f2hjr37r5':sf['loss_status']='partially_extant';sf['loss_status_basis']='四庫提要明言原初集三十卷、續集三十八卷久無傳本，從永樂大典輯十卷，所存僅十之一二。'
  if k=='d59f2hs6t4ao':sf['loss_status']='partially_extant';sf['loss_status_basis']='四庫提要明記原集二十五卷，永樂大典輯本十二卷，僅存十之五六。'
  if k=='d59f2hjr37r5' and 'loss_status_basis' in fd:fd['loss_status_basis']['selected']=sf['loss_status_basis']
  c['machine_decision']={'set_fields':sf,'remove_fields':remove};c['field_decisions']=fd
  c['apply_prerequisites']=['验证所有记录SHA256未变化','Book.work_id、classification与Work关系等typed refs全量重定向','检查book-text版本/辑佚资产及跨书引用；存在旧ID资产者须配套迁移后方可执行','indexed_by/emendated_by依顺序拼接而不按内容去重；原始记录存档，loser保留墓碑']
 cases.append(c)
# Classification and text-asset inventory, no mutation.
ids=set(snap);clas=collections.defaultdict(list)
for p in (R/'classification').rglob('*.json'):
 d=json.loads(p.read_text())
 if not isinstance(d,dict):continue
 for m in d.get('members',[]):
  i=m[0] if isinstance(m,list) else m.get('id')
  if i in ids:clas[i].append({'path':str(p.relative_to(R)),'node':d.get('node'),'membership':m})
texts={}
for p in (R.parent/'book-text-ref/index/texts').glob('*.json'):
 for i,v in json.loads(p.read_text()).items():
  if i in ids:texts[i]=v
for c in cases:
 c['classification_inventory']={i:clas.get(i,[]) for i in [c['keeper']]+c['losers']}
 c['book_text_assets']={i:texts[i] for i in [c['keeper']]+c['losers'] if i in texts}
 c['book_text_coverage']='仅当前本地index/texts，未覆盖fragments与整理本内引用；不得视为无资产证明'
(O/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
with gzip.open(O/'original-records.json.gz','wt',encoding='utf-8') as f:json.dump(snap,f,ensure_ascii=False)
(O/'stats.json').write_text(json.dumps({'active_work_scanned':266045,'same_source_summary_candidates':151,'decisions':dict(collections.Counter(x['status'] for x in cases)),'confirmed_losers':sum(len(x['losers']) for x in cases if x['status']=='confirmed')},indent=2)+'\n')
print((O/'stats.json').read_text())
