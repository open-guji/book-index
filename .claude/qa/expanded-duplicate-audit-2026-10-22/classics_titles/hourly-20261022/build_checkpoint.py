import json,glob,hashlib,pathlib,subprocess,datetime,gzip,collections
ROOT=pathlib.Path('/workspace/scratch/0bc7226fa660/book-index')
OUT=ROOT/'.claude/qa/expanded-duplicate-audit-2026-10-22/classics_titles/hourly-20261022'
specs=[
('JC-H001','confirmed','鄭玄／康成《三禮目錄》',['d59f2092ixog','d59fkwmysttt'],'兩條責任者實際皆指鄭玄 hixhd2f8wajv；《隋書》直載鄭玄撰一卷，《補後漢書藝文志》載鄭康成同題一卷；康成為字，並非另一著者。', '保留 d59f2092ixog，並 d59fkwmysttt；保留全部著錄及錄／録異寫。陶弘景注本不得併入。'),
('JC-H002','confirmed','鄭玄／康成《論語孔子弟子目錄》',['d59f23nxnmyt','d59fkwn0d0jo'],'《隋志》鄭玄撰一卷與《補後漢書藝文志》鄭康成同題一卷，責任者為同一Entity；姚振宗原文直接串聯隋唐題名和弟子籍注。','保留 d59f23nxnmyt，並 d59fkwn0d0jo；保留各輯者及版本，不併《論語注》《論語釋義》或《孔子弟子籍》原作。'),
('JC-H003','open','鄭玄《尚書大傳注》與輯本範圍',['d59f24moqs5g','d59fkwmxv474'],'身份及原注一致，但後一條附袁鈞三卷、孔廣林四卷及未決同題相關Work；前條亦有正文加鄭注的館藏，不能把注文本身與含正文傳本邊界視為已核。','讀所有關聯Book、袁鈞與孔廣林輯本目錄，確認Work邊界；現不提供執行映射。'),
('JC-H004','open','趙考古文集／先生文集／遺集',['d59f2nkgwp37','d59f2nk7jkld','d59fsgi3c26d'],'四庫二卷為後人裒輯殘篇，含詩十餘、文五十餘及子孫書札；故宮條二冊只是冊數；乾隆張廷枚本六卷另詩續附各一卷。未核篇目不可把冊數和卷數等同或把遺集增補當純異名。','比較順治丁酉黃世春序本、故宮平圖013483-013484鈔本、張廷枚乾隆38/40年本的目錄、首尾篇和續附範圍。'),
('JC-H005','open','沈欽韓左傳補注重出但趙汸來源污染',['d59f2mr6s6bl','d59f2n9s0yyp','d59f2j58ml8i'],'沈氏兩條同為十二卷；d59f2mr6s6bl卻混入《經義考》十卷與「汸自序」，並把混入的十卷寫入description。另一 d59f2j58ml8i 為趙汸十卷。新潟大學正式目錄亦明列元趙汸十卷。','先拆錯掛經義考節，核對全部版本影像屬沈或趙，修正文描述，再合沈氏兩條；趙汸不得合入沈欽韓。'),
('JC-H006','open','沈欽韓地名補注十二卷／二卷',['d59f2mr6s6bk','d59f2n9s0yyq','d59fywb5cvsw'],'前二條清史稿與續修四庫均十二卷，可形成同書線索；心矩齋子目卻錄二卷。書目答問補正檢索結果列心矩齋本為十二卷，提示可能漏十字，但尚未見原刻目錄不能改成已確認。','先查心矩齋原目與卷尾，區分漏十、存二卷或節本；前二條亦先完成Book與文本核驗再執行。'),
('JC-H007','separate','沈欽韓《左傳補注》與《左傳地名補注》',['d59f2n9s0yyp','d59f2n9s0yyq'],'清史稿同一引文明列補注十二卷、考異十卷、地名補注十二卷，是一條目包含多書；續修四庫分列不同來源版本。相同作者、同十二卷與同引文不構成同書。','保持兩書分立；只允許各書內部已另案確認的異名重出歸併。')]
records={}; cases=[]
for cid,status,label,ids,why,nxt in specs:
 paths={}; hashes={}; evidence=[]
 for id in ids:
  p=next((ROOT/'Work'/pathlib.Path(*id[-3:])).glob(id+'-*.json'))
  b=p.read_bytes();r=json.loads(b);records[id]={'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'record':r}
  paths[id]=records[id]['path'];hashes[id]=records[id]['sha256']
  evidence.append({'record_id':id,'title':r.get('title'),'authors':r.get('authors'),'measure_info':r.get('measure_info'),'indexed_by':r.get('indexed_by',[]),'emendated_by':r.get('emendated_by',[])})
 c={'case_id':cid,'type':'Work','status':status,'label':label,'members':ids,'paths':paths,'sha256':hashes,'why':why,'next_step':nxt,'evidence':evidence,'applied':False}
 if status=='confirmed':
  c.update(keeper=ids[0],losers=ids[1:],apply_prerequisites=['重新驗證來源SHA256','全庫型別化引用重指與分類判定','完整book-text元資料與整理本/輯佚引用檢查','重建官方索引並保留墓碑來源歷史'],field_decisions={'indexed_by':'依原順序追加保留全部來源，不因文本相同刪源','authors':'保留keeper鄭玄；來源鄭康成署名留在indexed_by','title':'保留keeper；loser錄/録題作additional_titles','description':'保留keeper，不新增未證斷言','history':'無損聯集，新增本案映射與墓碑'})
 cases.append(c)
# Search all raw source records for typed direct work_id; also retain reference matches for other fields.
ids=set(records); pattern='|'.join(sorted(ids))
proc=subprocess.run(['rg','-l',pattern,'Book','Work','Collection'],cwd=ROOT,text=True,capture_output=True,check=False)
references=[];books={}
for rel in proc.stdout.splitlines():
 p=ROOT/rel
 try:r=json.loads(p.read_bytes())
 except Exception:continue
 if r.get('merged_into'):continue
 hits=sorted(id for id in ids if id in p.read_text())
 references.append({'path':rel,'id':r.get('id'),'type':r.get('type'),'matched_ids':hits,'direct_work_id':r.get('work_id')})
 if rel.startswith('Book/') and r.get('work_id') in ids:books[r['id']]={'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'record':r}
for c in cases:c['related_books']=[{'id':id,'path':x['path'],'work_id':x['record'].get('work_id')}for id,x in books.items() if x['record'].get('work_id') in c['members']]
# Existing-case risk, deliberately separate from new-case totals.
p=next((ROOT/'Work/w/x/u').glob('d59f27xu9wxu-*.json'));b=p.read_bytes();r=json.loads(b)
issue={'issue_id':'JC-H-QA001','existing_case_id':'JC-001','status':'needs_source_repair','record_id':r['id'],'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'evidence':[x for x in r['indexed_by'] if '文廷式' in x['source']], 'finding':'題作周易繫辭注的文廷式著錄節summary卻論歸藏十三篇及三殘篇；不能以無損追加為由認定全部來源已校正。','impact':'人物/書名同一性不因此直接推翻，但自動執行須先標注或修復錯掛段落並保存原文。','next_step':'覆核文廷式補晉書藝文志原文上下文與對應歸藏條，確認是本庫抽段移位還是來源排版問題。'}
records[r['id']]={'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'record':r}
for name,obj in [('cases.json',cases),('references.json',references),('existing-case-risks.json',[issue])]:
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
for name,obj in [('original-records.json.gz',records),('related-books.json.gz',books)]:
 with gzip.open(OUT/name,'wt',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
stats={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_head':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','new_cases':len(cases),'status_counts':dict(collections.Counter(c['status']for c in cases)),'confirmed_losers':sum(len(c.get('losers',[]))for c in cases),'unique_original_records':len(records),'active_related_books':len(books),'existing_case_risk_count':1,'source_hash_validation':'passed','raw_data_modified':False,'cross_repository_validation':'not_completed','applied_merge_groups':0}
(OUT/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False))
