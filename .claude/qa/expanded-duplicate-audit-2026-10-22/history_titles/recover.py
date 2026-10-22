import pathlib,json,hashlib,gzip,collections,re,datetime,copy
R=pathlib.Path(__file__).resolve().parents[4];O=pathlib.Path(__file__).resolve().parent
# This script writes research artifacts only. It never changes native records.
def load(i):
 p=next((R/'Work'/i[-3]/i[-2]/i[-1]).glob(i+'-*.json')); b=p.read_bytes(); return str(p.relative_to(R)),json.loads(b),hashlib.sha256(b).hexdigest()
def union(a,b):
 return a+[x for x in b if x not in a]
sets=[
('d59f27sdmepu','d59f27xc65fl','韋昭注國語：兩條同收《經義考》同題同文；三國藝文志逐項引隋唐著錄與前條吻合。二十、二十一、二十二卷為跨志分卷異文，原文全部保存。'),
('d59f27t7l6v5','d59f27xgjh1d','虞翻注國語：兩條同收《經義考》同題同文；三國藝文志明引隋志二十一卷及唐志，且指出撰當作注。'),
('d59f27sbfqwx','d59f27xchdz4','唐固注國語：兩條同收《經義考》同題同文；三國藝文志明引隋志二十一卷及唐志，唐固與虞翻、韋昭各是獨立注本，三者不互合。'),
('d59f2nehu6tc','d59f2nk1xb0i','雷禮、唐臣嘉靖真定府志：同有國史經籍志三十三卷著錄，四庫提要與千頃堂明述雷禮嘉靖時修；四庫存目保留唐臣合纂。保留兩名責任者及三十二/三十三卷原始異文。'),
('d59f2neqw2dc','d59f6emqmqdi','戴日強萬曆餘杭縣志：同一作者 Entity，古籍總目明題萬曆十卷，四庫提要同題十卷，四庫存目亦明載萬曆刻本。略去年號產生另一題名。'),
('d59f2nepycqr','d59f6eocdmva','葛洞嘉靖江都縣志：千頃堂書目明載葛洞嘉靖間修，四庫提要同人嘉靖壬戌受趙訥之命編八門，前條是無年號簡稱。'),
('d59f2ng39urk','d59f6egvxjpf','謝少南嘉靖全州志：千頃堂書目同人全州志，明史及國史同人七卷，四庫提要同人嘉靖己酉修六卷；跨志卷數不同不構成二書證據。')]
cases=[];snap={}; ids=set()
for n,(keep,lose,why) in enumerate(sets,1):
 p,k,h=load(keep);q,l,j=load(lose);ids.update([keep,lose]);snap[keep]={'path':p,'record':k};snap[lose]={'path':q,'record':l}
 fields={};remove=[];decisions={}
 if n<=3:
  fields['authors']=copy.deepcopy(k['authors']);fields['authors'][0]['role']='注';fields['authors'][0]['role_basis']='據本組 indexed_by 所引隋書經籍志與三國藝文志，責任方式明為注。'
  fields['title']= {'d59f27sdmepu':'春秋外傳國語韋昭注','d59f27t7l6v5':'春秋外傳國語虞翻注','d59f27sbfqwx':'春秋外傳國語唐固注'}[keep]
  fields['dynasty']='三國吳';fields['dynasty_basis']=l['dynasty_basis']
  if 'loss_status' in l:
   fields['loss_status']=l['loss_status'];fields['loss_status_basis']=l['loss_status_basis']
 if n==5:
  fields['resource_groups']=l['resource_groups']
 if n in (5,7):remove=['period_upper','period_upper_basis']
 # Exhaustive scalar decisions; list payloads retain original order and all source entries.
 listfields=['indexed_by','emendated_by','resources','contained_in','related_works','sources','additional_titles','merged_in','merged_from','merge_history']
 keys=set(k)|set(l)
 for key in sorted(keys):
  if key in ['id','revision','revised_at','updated_at','schema_version','type']:continue
  if key in listfields:decisions[key]={'action':'ordered_union_without_dropping_source_entries','reason':'保留全部來源和關係；indexed_by/emendated_by須串接，不按內容去重。'}
  elif key=='ai_note':decisions[key]={'action':'append_attributed','reason':'舊判語按原記錄 id 留存，不能充當新證據。'}
  elif key in fields:decisions[key]={'action':'set','value':fields[key],'reason':why}
  elif key in remove:decisions[key]={'action':'remove','reason':'已由直接著錄定為明，舊上限只是裸系千頃堂的過時保守推定。'}
  elif key not in k:fields[key]=l[key];decisions[key]={'action':'set','value':l[key],'reason':'另一條獨有而無衝突的原生信息保留。'}
  else:decisions[key]={'action':'retain_keeper','value':k[key],'other_value':l.get(key),'reason':'主條直接著錄與計量較完備；各志異文及舊說完整留在來源與快照。'}
 # Remove misleading prose description of the注者 as撰者; generate narrow source-grounded text.
 if n<=3:
  name=k['authors'][0]['name'];fields['description']={'text':name+'（三國吳）注《國語》。本條合併同一注本於《經義考》《三國藝文志》等目錄的重複著錄；各志卷數及輯本信息保留於著錄原文。','sources':list(dict.fromkeys(x['source'] for x in k.get('indexed_by',[])+l.get('indexed_by',[])))}
 for key,value in fields.items():decisions[key]={'action':'set','value':value,'reason':why}
 cases.append({'case_id':f'H-R{n:03}','cluster_id':f'H-R{n:03}','type':'Work','status':'confirmed','verdict':'confirmed','keeper':keep,'losers':[lose],'paths':{keep:p,lose:q},'sha256':{keep:h,lose:j},'reason':why,'evidence':{keep:k.get('indexed_by',[]),lose:l.get('indexed_by',[])},'field_decisions':decisions,'machine_decision':{'set_fields':fields,'remove_fields':remove},'apply_prerequisites':['更新所有 Book.work_id 和其他原生引用、分類，保留墓碑及合併歷史。','檢查 book-text 正文/輯佚資產與引用並完成相應遷移後方可落地。'],'related_books':[]})
# Scanned candidates are explicitly unresolved, not claimed individually adjudicated.
groups=json.loads((O/'candidate-groups.json').read_text())
separate={8:'原書與袁祖志重修本：原著錄明載不同修訂者，四卷相同不足以合併。',69:'齊召南十卷原書與阮元十二卷重訂本內容範圍不同，分立。',104:'弘治十五年與順治十五年會試錄屬不同朝代、不同科次，年號不可作可刪前綴。'}
for i,g in enumerate(groups):
 if any(x['id'] in ids for x in g):continue
 status='separate' if i in separate else 'open'
 why=separate.get(i,'只完成候選篩查；須查明來源記錄、版次、修纂範圍。匿名作者不可作同人證據，相同摘要與館藏列表亦不能排除同名異書。')
 members=[]
 for x in g:
  p,d,h=load(x['id']);members.append({'id':d['id'],'path':p,'sha256':h,'title':d['title'],'authors':d.get('authors',[]),'indexed_by':d.get('indexed_by',[]),'source_record_ids':re.findall('源記錄[：:]([^\\n ]+)',d.get('ai_note',''))})
 cases.append({'case_id':f'H-C{i:03}','type':'Work','status':status,'verdict':status,'reason':why,'members':members,'review_depth':'source_fields_compared' if i in separate else 'candidate_screen_only'})
for extra in [('d59fybddr11c','d59fybbovr40','後渠雜識與後渠漫記：古籍總目括注提出異名可能，但須查說郛續不同卷次所收原文。僅有括注不能證明文本相同。'),('d59ezahlu8sg','d59f27sdmepu','國語原典條混左丘明、韋昭以及汲冢材料，不能整條合入韋昭注本。須按著錄段落及版本拆辨。'),('d59f2hswekua','d59fyfefz9c0','國語補音主條有宋史林概著錄與宋庠主作者衝突，先查錯掛來源，不以同題整體合併。')]:
 members=[]
 for i in extra[:2]:
  p,d,h=load(i);members.append({'id':i,'path':p,'sha256':h,'record':d})
 cases.append({'case_id':f'H-X{len(cases):03}','type':'Work','status':'open','verdict':'open','reason':extra[2],'members':members,'review_depth':'source_fields_compared'})
# Scan all active Book records once, recording every affected reference.
book_count=0
for p in (R/'Book').glob('*/*/*/*.json'):
 b=json.loads(p.read_text());book_count+=1
 if not b.get('merged_into') and b.get('work_id') in ids:
  for c in cases[:len(sets)]:
   if b['work_id'] in [c['keeper']]+c['losers']:
    c['related_books'].append({'id':b['id'],'path':str(p.relative_to(R)),'work_id':b['work_id'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'record':b})
# Preserve classifications as they currently stand; a coordinator must adjudicate any cross-node conflict.
for p in (R/'classification').rglob('*.json'):
 txt=p.read_text()
 for c in cases[:len(sets)]:
  hits=[i for i in [c['keeper']]+c['losers'] if i in txt]
  if hits:c.setdefault('classification_files',[]).append({'path':str(p.relative_to(R)),'ids':hits,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
with gzip.open(O/'confirmed-original-records.json.gz','wt',encoding='utf8') as f:json.dump(snap,f,ensure_ascii=False)
stats={'base':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','target_work_rows':39457,'candidate_groups':len(groups),'cases':len(cases),'decisions':dict(collections.Counter(c['status'] for c in cases)),'confirmed_losers':len(sets),'books_scanned':book_count,'related_books':sum(len(c['related_books']) for c in cases[:len(sets)]),'native_records_changed':0}
(O/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(stats)
