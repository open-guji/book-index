"""Research-only snapshot and bounded review. Writes only this directory."""
import json,sqlite3,pathlib,hashlib,itertools,subprocess,collections
OUT=pathlib.Path(__file__).resolve().parent
AUDIT=OUT.parent.parent
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
db=sqlite3.connect('file:/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite?mode=ro',uri=True)
manifest=json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0]);assert manifest['base']==BASE and not manifest['errors']
def save(n,o): (OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
case_specs=[
('PNA-2022-001','仇兆鰲／仇滄柱','confirmed',['hixhd2h9bf9t','hixhd2h9bjaz'],['仇兆鰲','仇兆鼇','仇滄柱'],['d59f2mi7ebk1','d59f2nmpfsw0','d59fxxr66fwh'],
 '四庫總目杜詩詳注明言兆鼇字滄柱、鄞縣、康熙乙丑進士；清史稿署仇滄柱參同契集注二卷，中國古籍總目署仇兆鰲古本周易參同契集注二卷及補遺附錄圖說，時代與著述領域吻合。CiNii古籍著錄又將封面甬上仇滄柱輯繫至仇兆鰲權威記錄。',
 ['不把清史稿簡題二卷與古籍總目含補遺等全套Work機械相併。','keeper.cbdb_source含ambiguous_2，現行1638–1717與外部ID、上圖來源均未獨立重驗，原值全留。','仇知幾是另一個待研究Entity，本案未裁定或改指；不得藉本案擴大為三人實施。'],
 [{'url':'https://ci.nii.ac.jp/ncid/BB21230531','kind':'institutional_original_catalogue','ref':'turn39view1','locator':'lines 110–131, 175','supports':'古籍封面甬上仇滄柱輯，著者權威繫仇兆鰲；非出生年份證據。'}]),
('PNA-2022-002','龔昱／龔立道','confirmed',['hixhd2h9buzq','hixhd2h9bm5v'],['龔昱','龔立道'],['d59f2hsc45j4','d59f2huga22p','d59f2hfodog0','d59f2ninzbwh','d59fxyf17jlt'],
 '四庫樂菴語錄提要及總目樂菴遺書條均直接稱龔昱字立道、崑山人、李衡門人；國史經籍志署龔立道崑山雜詠四卷。俞允文二十八卷本總目追述龔昱原編三卷續集一卷，提供同一地志詩集與卷數差別的上下文。',
 ['人物確認不自動合併三卷、四卷、二十八卷Work。三卷加續集一卷只是解釋四卷的候選，原篇章範圍未逐葉核對。','樂菴遺書提要對傳本真偽有疑，完整疑文保留；不以身份確認裁定語錄文本真偽。','keeper現有丘道、立道、邱道三種字；本輪只核立道，不刪其餘異說。','keeper上圖來源與CBDB既有值保持；loser period_basis歷史原文須入完整字段台賬。'],
 [{'url':'https://zh.wikisource.org/zh-hant/芻言_(四庫全書本)','kind':'classical_primary_text_transcription','ref':'turn36view2','locator':'line 114, 樂菴語錄提要','supports':'宋龔昱字立道，崑山人；吳仁傑後序稱龔君立道從先生游六年。網頁標題芻言，實際合載樂菴語錄提要。'}]),
('PNA-2022-003','何澹／何自然','separate',['hixhd2h9bosw','hixhd2h9bdqk'],['何澹','何自然'],['d59f2q96ap6p','d59f28lmt3if','d59f2pvscav4'],
 '宋史卷394直接稱何澹字自然、處州龍泉人、乾道二年進士，並以何自然稱之；但現有何自然Entity繫笑林三卷，其書已見新唐書藝文志且國史經籍志明署唐何自然，早於南宋何澹。真實字橋不能跨越作者鏈時代衝突。',
 ['何自然既有CBDB 93259的dy_mismatch_6及ambiguous_2是未核權威匹配，不能因字自然相合而移交何澹。','何澹本條缺period且1146–1220出於既有補值，本輪不補寫或重新認證生卒。','何澹小山雜著只有題名含人名，無結構作者引用；列為關聯線索，未補entity_id。','何澹安醫案題名子串是異人何遊線索，保留原文而排除身份推定。'],
 [{'url':'https://zh.wikisource.org/wiki/宋史/卷394','kind':'classical_primary_text_transcription','ref':'turn19view1','locator':'lines 144,148','supports':'何澹字自然，乾道二年進士及何自然稱名。'},{'url':'https://zh.wikisource.org/wiki/新唐書/卷059','kind':'classical_primary_text_transcription','ref':'turn50view1','locator':'line 1885, 藝文三小說類','supports':'原文何自然笑林三卷；初次find失敗，後按行號open取得實文。'}]),
('PNA-2022-004','何涉／何濟川','separate',['hixhd2h9bnw5','hixi5fstaolq'],['何涉','何渉','何濟川'],['d59f2he7xt6o','d59f2hl1wt8g','d59f2hlvkcu8','d59fxqu91q82','d59fxrvg5slc','d59fxrbvycqq'],
 '經義考卷188引程端學明言渉字濟川；宋史卷432原傳再證字濟川及范仲淹、元昊時官歷，並載治道中術、春秋本旨；治道中術、治道中說另著錄於宋史藝文志。另一何濟川Entity所繫管窺圖說、溝洫圖說，中國古籍總目責任者明署清何濟川；宮室圖說另有無entity_id作者同署清。現有作者鏈是宋人與清人，應分立。',
 ['嘉慶二十五年刻本是版本年代，不能獨自證明作者為清人；分立使用責任者明署清與宋代著錄，非以刊年當生年。','清何濟川的CBDB 582058人工匹配原注已承認唯一性未驗；此案不將其提升為已驗身份。','何涉既有南充、Work舊按西充、縣志所述宋史版本南兗等籍貫異文須保留，不藉分立統一地名。','何涉既有何渉merged_in保留；宮室圖說無entity_id，不能把它算作已知結構改指數。','未讀清人各書原序，此限制保留；不因不足而把明確異代作者鏈併在一起。'],
 [{'url':'https://zh.wikisource.org/wiki/宋史/卷432','kind':'classical_primary_text_transcription','ref':'turn50view0','locator':'lines 270–274','supports':'何涉字濟川、南充人，范仲淹與元昊時官歷，治道中術及春秋本旨著作。'},{'url':'https://wk.100ke.info/wiki/民國新脩合川縣志/卷37','kind':'classical_primary_text_transcription_search_result','ref':'turn41search1','locator':'何涉條','supports':'何涉字濟川與南充/南兗異文線索；尚未open，僅輔助。'}])]
ids={i for s in case_specs for i in s[3]};names={n for s in case_specs for n in s[4]}
snaps={};works={};refs=[];counts=collections.Counter()
def walk(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():yield from walk(x,p+'/'+k.replace('~','~0').replace('/','~1'))
 elif isinstance(v,list):
  for j,x in enumerate(v):yield from walk(x,p+'/'+str(j))
 elif isinstance(v,str):yield p,v
for i,t,n,p,b,h,raw in db.execute('select id,type,name,path,blob_sha,sha256,data from records'):
 counts[t]+=1
 hasid=any(x in raw for x in ids);hasname=t=='Work' and any(x in raw for x in names)
 if not(hasid or hasname or i in ids):continue
 o=json.loads(raw)
 if i in ids or hasname or hasid:
  by=raw.encode();assert hashlib.sha256(by).hexdigest()==h
  assert hashlib.sha1(b'blob '+str(len(by)).encode()+b'\0'+by).hexdigest()==b
  gitraw=subprocess.check_output(['git','cat-file','blob',b]);assert gitraw==by
  snaps[i]={'id':i,'type':t,'name':n,'path':p,'blob_sha':b,'sha256':h,'raw':raw,'record':o}
 if t=='Work' and (hasname or hasid):works[i]=snaps[i]
 if hasid:
  for ptr,v in walk(o):
   for target in ids:
    if target in v:refs.append({'record_id':i,'type':t,'path':p,'pointer':ptr,'target':target,'match':'exact' if v==target else 'substring','value':v,'self_id':ptr=='/id' and i==target})
oldpairs={};scanned=[]
for f in AUDIT.rglob('cases.json'):
 if f.parent==OUT:continue
 try:cs=json.loads(f.read_text())
 except:continue
 if isinstance(cs,dict):cs=cs.get('cases',[])
 scanned.append(str(f.relative_to(AUDIT)))
 for c in cs:
  if not isinstance(c,dict):continue
  members=set(x for x in c.get('ids',[])+[c.get('keeper')]+c.get('losers',[])+[c.get('suggested_keeper')]+c.get('suggested_losers',[]) if isinstance(x,str))
  for a,b in itertools.combinations(sorted(members),2):oldpairs.setdefault((a,b),[]).append(c.get('case_id'))
q=json.loads((OUT.parent/'broad-20261022/candidate-queue.json').read_text());cases=[]
for cid,label,status,members,cnames,evidence,decision,cautions,external in case_specs:
 pair=tuple(sorted(members));assert pair not in oldpairs,(cid,oldpairs.get(pair))
 disc=next(x for x in q if tuple(sorted(x['ids']))==pair)
 ws=[w for w in works.values() if any(a.get('entity_id') in members for a in w['record'].get('authors',[]))]
 candidate_ws=[w for w in works.values() if any(n in w['raw'] for n in cnames)]
 c={'case_id':cid,'label':label,'status':status,'ids':members,'supersedes_case_id':None,'native_merge_groups':0,'research_only':True,'suggested_keeper':members[0] if status=='confirmed' else None,'suggested_losers':[members[1]] if status=='confirmed' else [],'decision':decision,'cautions':cautions,'work_evidence_ids':evidence,'discovery_rules':disc['rules'],'previous_case_ids':[], 'entity_snapshots':[{k:snaps[i][k] for k in ['id','path','blob_sha','sha256']} for i in members], 'catalogue_pointers':[{'work_id':i,'path':snaps[i]['path'],'pointer':'/indexed_by','values':snaps[i]['record'].get('indexed_by',[])} for i in evidence], 'external_sources':external,'structured_author_work_ids':[w['id'] for w in ws],'name_mention_work_ids':[w['id'] for w in candidate_ws], 'known_references':[r for r in refs if r['target'] in members], 'execution_gates':['Refresh origin/main and both SHA256/Git blob preconditions before any apply.','Complete lossless field ledger for both people and every changed record; preserve all original values and history.','Person merge does not authorize Work merge or metadata correction.','Scan formal Book/Collection/classification/promotions, draft repository and book-text; current census is Entity+Work only.','Before implementation: no conflicting external ID; keep original author name/name_basis and sources.','After implementation: T/L/P/R/D audit, schema, changed-path check_v2, classification and official builder with valid text-index baseline; do not handcraft indexes.']}
 cases.append(c)
save('cases.json',cases);save('source-snapshots.json',snaps)
save('related-works.json',{'scope':'Every current-main Work with any selected entity ID substring or one of the selected name variants; all full records retained. Name-only matches are not silently attributed.','name_variants':sorted(names),'works':works})
save('reference-review.json',{'scope':'All active records in readonly census, Entity+Work only','counts':dict(counts),'matches':refs,'not_scanned':['Book','Collection','classification','promotions','draft repository','book-text'],'full_reference_scan_passed':False})
save('validation.json',{'base':BASE,'manifest':manifest,'cases':len(cases),'counts':dict(collections.Counter(c['status'] for c in cases)),'unique_people':len(ids),'snapshot_records':len(snaps),'work_snapshots':len(works),'sha256_and_git_blob_checked':len(snaps),'actual_git_blob_bytes_compared':len(snaps),'new_pairs_checked_against':scanned,'no_existing_pairs_reused':True,'native_mutations':0,'old_1876_map_used':False,'BOOK_0010':'hold, untouched','full_reference_scan_passed':False,'schema_audit_run':False,'native_apply_run':False,'builder_run':False,'limitations':['Snapshot contents verified against immutable Git blob IDs and fixed-main manifest, not against changing working-tree bytes.','Name-only Work mentions include other authors and are retained as context, not identity proof.','External tool failures retained; search-only evidence labeled.']})
print(json.dumps({'cases':len(cases),'statuses':dict(collections.Counter(c['status'] for c in cases)),'snapshots':len(snaps),'works':len(works),'references':len(refs),'structured_work_counts':{c['label']:len(c['structured_author_work_ids']) for c in cases}},ensure_ascii=False))
