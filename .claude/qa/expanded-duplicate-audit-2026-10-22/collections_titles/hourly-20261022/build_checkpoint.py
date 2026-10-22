import json, pathlib, hashlib, datetime
root=pathlib.Path(__file__).resolve().parents[5]
out=pathlib.Path(__file__).resolve().parent
base=out.parent
old={x['case_id']:x for x in json.loads((base/'cases.json').read_text())}
records=json.loads((out/'original-records.json').read_text())
refs=json.loads((out/'entity-reference-records.json').read_text())
for p,d in refs.items():
 f=root/p
 records[d['id']]={'path':p,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'record':d}
(out/'original-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
def rec(ids):return [{k:records[i][k] for k in ['path','sha256']}|{'id':i} for i in ids]
def excerpt(i):
 d=records[i]['record'];return {'id':i,'authors':d.get('authors'),'indexed_by':d.get('indexed_by',[])}
def new(n,oldid,status,ids,reason):
 c=old[oldid]
 return {'case_id':n,'supersedes':oldid,'type':'Work','status':status,'applied':False,'reason':reason,'records':rec(ids),'evidence':[excerpt(i) for i in ids if records[i]['path'].startswith('Work/')], 'related_books':c['related_books'],'book_text_assets':c['book_text_assets'],'book_text_coverage':c['book_text_coverage'],'classification_inventory':c['classification_inventory'],'review_scope':'实体真实authors引用扫描覆盖Work/Book/Collection；30个直接相关Book逐条读原始著录。未对全库历史字符串或book-text完整元数据作执行验证。'}
cases=[]
c=new('COL-H001','COL-R021','open',['d59f28k1dfk4','d59f2huigpvm','hixhd2h9bmi9','hixi8u5ywvgi','d59f28lfbeh1'],'两条三卷四库辑本的著录同一性已核，但现有忠愍集另混挂三个一卷本，须先辨选本范围；唐宋李若水实体不得合并。')
c['external_sources']=[{'url':'https://zh.wikisource.org/wiki/四庫全書總目提要/卷155','checked':'2026-10-22','evidence':'忠湣集条明确宋李若水、本名若冰字清卿；原十/十二卷已佚，永乐大典辑为三卷。'}]
c['new_findings']=[{'ids':['98y722u8le','98y722u8lf','98yblor2f7'],'finding':'分别是畿辅丛书本、乾坤正气集本及无版本说明的一卷忠愍公集/忠愍集，旧录仅依同题同作者归入三卷本，没有正文范围证据。'},{'ids':['d59f28lfbeh1'],'finding':'李若水集十/十二卷也误连唐人；总目解释十卷与十二卷（后二卷附录）关系，但原集与三卷辑本应明确层级后再处理。'}]
c['next_steps']=['核一卷本首尾篇目及所收范围，必要时拆独立选本Work。','仅修指定宋人作品责任者至hixi8u5ywvgi；保留唐人hixhd2h9bmi9。','原集与辑本关系及文本侧迁移方案完成后再作合并机器决策。'];cases.append(c)
c=new('COL-H002','COL-R022','confirmed',['d59f2gny4r9d','d59f2mi8n9q9','hixhd2h9bky2','hixhd2h9bfij'],'同一元人二卷四库辑本；现补齐全部8个Book著录并确认“宜甫”误连清章成义，不是清代另一本陈秋岩诗集。')
c['keeper']='d59f2gny4r9d';c['losers']=['d59f2mi8n9q9']
c['external_sources']=[{'url':'https://zh.wikisource.org/wiki/四庫全書總目提要/卷166','checked':'2026-10-22','evidence':'陈秋岩诗集二卷条以国史经籍志陈宜甫秋岩集辨人，并据至元、元贞诗题判为元人；明载永乐大典所存编成二卷。'}]
c['machine_decision']={'set_fields':{'authors':records[c['keeper']]['record']['authors'],'dynasty':'元','period':'liao-jin-yuan','dynasty_basis':'《四庫全書總目》卷166陳秋岩詩集提要及全部相關Book責任者','period_basis':'據元陳宜甫及提要所述至元、元貞年事','description':{'text':'元陳宜甫撰。《四庫全書總目》據《永樂大典》所存詩編為二卷，題《陳秋岩詩集》，亦題《秋巖詩集》。原作者爵里未詳；清章成義別名宜甫與此書無涉。','sources':['欽定四庫全書總目','補遼金元藝文志','元史藝文志','清史稿藝文志','中國古籍總目']}},'forbidden_entity_merges':[['hixhd2h9bky2','hixhd2h9bfij']]}
c['field_decisions']={'authors':'只用元陈宜甫，不合并旧宜甫/清章成义作者项；旧值保留快照与校误note。','measures':'保留keeper二卷；Book的不分卷不改写。','additional_titles':'保留原别题，补loser题名。','indexed_by':'按原顺序追加，保留清史稿条而不据其书名误定清代。','resources/resource_groups/contained_in/related_works':'保留并集，resource_groups冲突则阻断。','ai_note/merged_in/merge_history':'保留全部原文及历史，追加误连原因，不删旧记录。'}
c['apply_prerequisites']=['重验全部原档hash。','本案替代COL-R022，不可两次计数。','全部引用重指、分类唯一化、官方派生索引重建。','完整book-text/fragments/整理本元数据检查；旧索引未见loser文本不能代替完整验证。','Entity章成义保持独立；不得将宜甫作为陈宜甫的新增字/号。'];cases.append(c)
c=new('COL-H003','COL-R033','confirmed',['d59f2gozl8g1','d59f2gi7sw76','hixhd2h9boid','hixhd2h9bfhn','d59fymrqr5z4'],'两条均指金王若虚四十五卷全集，全部6个Book为四十五卷本含后附续编/诗集；金若虚是误切责任者，需定点修复，不扩大到四卷选本。')
c['keeper']='d59f2gozl8g1';c['losers']=['d59f2gi7sw76']
c['external_sources']=[{'url':'https://zh.wikisource.org/wiki/滹南集_(四庫全書本)','checked':'2026-10-22','evidence':'四库本页题滹南集，提要明确滹南遗老集四十五卷续编一卷、金王若虚；与保存的总目四十五卷条同书。'},{'url':'https://zh.wikisource.org/wiki/四庫全書總目提要/卷166','checked':'2026-10-22','evidence':'列全集各篇组成合计四十五卷，王若虚字从之号慵夫。'}]
c['machine_decision']={'set_fields':{'authors':records['d59f2gi7sw76']['record']['authors'],'dynasty':'金','period':'liao-jin-yuan','dynasty_basis':'《四庫全書總目》卷166滹南遺老集及四庫本卷首','period_basis':'據金王若虛','juan_count':{'number':45},'measures':[{'unit':'卷','number':45}],'measure_info':'四十五卷','description':{'text':'金王若虛撰，四十五卷，亦題《滹南遺老集》。各版本所附續編、詩集在Book層保留原著錄，不將附編算入主書卷數。舊作者金若虛係責任者切分錯誤。','sources':['欽定四庫全書總目','補遼金元藝文志','元史藝文志']}},'excluded_work_ids':['d59fymrqr5z4','d59fsdvsf282','d59f2gl8qps1'],'entity_merge_authorized':False}
c['new_findings']=[{'ids':['d59fymrqr5z4'],'finding':'同名滹南集明确四卷诗话三卷，与45卷全集范围不同；留独立候选，不纳入合并。'},{'ids':['d59f2gl8qps1','d59fsdvsf282'],'finding':'另有45卷题名变体但尚未核完其Book；本案不顺带扩大。'}]
c['field_decisions']={'authors':'替换金若虚为有据王若虚；错误name_basis转入校误note，不合并到新作者。','measures':'主书45卷；6个Book的续一卷/诗一卷等完整保留，不改Book。','indexed_by/resources/additional_titles/contained_in':'按无损策略追加各来源与别题，非加和键冲突需阻断。','ai_note/merged_in/merge_history':'无损保留；金若虚Entity不在此Work决策内删除或并条。'}
c['apply_prerequisites']=['重验原档hash。','仅COL-R033的两条Work；不能把同人短题命中全部并入。','完整book-text与所有typed引用校验，重建官方索引。','误连责任者须和Work合并同一提交完成；金若虚Entity后续另案。'];cases.append(c)
c=new('COL-H004','COL-R034','confirmed',['d59f2nke3jsz','d59f2nijm0hs','hixhd2h9bouh','hixhd2h9bfn2'],'四库提要及7个相关Book均为佘翔四卷诗集；余翔实体的唯一真实作品引用即该误字书，定点修Work责任者后两条同书。')
c['keeper']='d59f2nke3jsz';c['losers']=['d59f2nijm0hs']
c['external_sources']=[{'url':'https://zh.wikisource.org/wiki/欽定四庫全書總目_(四庫全書本)/集部/卷172','checked':'2026-10-22','evidence':'薜荔园集四卷明佘翔撰；字宗汉号凤台；提要说明各游历作品合编仍称薜荔园诗。'}]
c['machine_decision']={'set_fields':{'authors':records['d59f2nijm0hs']['record']['authors'],'dynasty':'明','period':'ming','dynasty_basis':'《欽定四庫全書總目》卷172及Book原著錄','period_basis':'據明佘翔','juan_count':{'number':4},'measures':[{'unit':'卷','number':4}],'measure_info':'四卷','description':{'text':'明佘翔撰，四卷，亦題《薜荔園集》《薜荔園稿》。總目明載作者字宗漢、號鳳臺，並記合編遊梁及金陵紀遊之作。舊責任者余翔係形近字誤錄，並非本書另一作者。','sources':['欽定四庫全書總目','中國古籍總目']}},'entity_merge_authorized':False}
c['field_decisions']={'authors':'替换余翔为佘翔；误字name_basis和旧说明留校误note/快照，不作为合法人名别称。','measures':'取有明确原文的四卷。','indexed_by':'两个相同提要均保留来源沿革。','resources/resource_groups/additional_titles/contained_in':'无损并集；保留现有文本资产所在keeper。','ai_note/merged_in/merge_history':'保留旧著录与并条历史；余翔Entity暂不动，另案处理来源误字。'}
c['apply_prerequisites']=['重验源档hash。','责任者替换和description修正必须与Work并条一起执行。','完整book-text/整理本/fragments与typed引用检查。','全量引用、分类及官方派生索引更新；Book不合并。'];cases.append(c)
cases.append({'case_id':'COL-H005','type':'Entity','status':'separate','applied':False,'records':rec(['hixhd2h9bky2','hixhd2h9bfij']),'reason':'元陈宜甫与清章成义分立。章成义条的宜甫是其别名；将陈宜甫拆成宜甫后自动命中该别名造成跨时代错连，不是同人异称。','evidence':[{'id':'hixhd2h9bky2','primary_name':'陳宜甫','dynasty':'元'},{'id':'hixhd2h9bfij','primary_name':'章成義','dynasty':'清','alt_name':'宜甫','dates':{'birth':1845,'death':1894}}, {'work_id':'d59f2mi8n9q9','source':'欽定四庫全書總目卷166','finding':'提要以至元十七年及元贞诗题定作者时代，明确名陈宜甫。'}],'next_steps':['执行COL-H002时仅撤销错误Work作者链接，不对两Entity作任何合并。'],'external_sources':[{'url':'https://zh.wikisource.org/wiki/四庫全書總目提要/卷166','checked':'2026-10-22'}]})
(out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
stats={'case_counts':{'confirmed':3,'open':1,'separate':1},'promoted_existing_open_cases':['COL-R022','COL-R033','COL-R034'],'reviewed_existing_open_kept_open':['COL-R021'],'new_separate_entity_cases':1,'confirmed_work_losers':3,'entity_merges':0,'book_merges':0,'native_records_modified':0,'snapshot_records':len(records),'direct_book_records_reviewed':30,'actual_author_reference_records':len(refs),'base_head':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','apply_gate':'not_applied_pending_cross_repository_and_integration_validation'}
(out/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
errors=[]
for i,r in records.items():
 if hashlib.sha256((root/r['path']).read_bytes()).hexdigest()!=r['sha256']: errors.append(i)
(out/'verification.json').write_text(json.dumps({'snapshot_hashes_checked':len(records),'hash_mismatches':errors,'cases_json_valid':True,'native_data_modified':False},ensure_ascii=False,indent=2)+'\n')
print(stats);print('hash errors',errors)
