import copy, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRE=HERE.parent/'astra-review-20261022'
MAIN='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
records=json.loads((PRE/'verified-original-records.json').read_text())
old=json.loads((PRE/'cases.json').read_text())
tree_path=Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z')
tree={}
for row in tree_path.read_bytes().split(b'\0'):
 if not row: continue
 meta,path=row.split(b'\t',1)
 tree[path.decode()]=meta.split()[2].decode()
checks=[]
for rid,v in records.items():
 raw=(json.dumps(v['record'],ensure_ascii=False,indent=2)+'\n').encode()
 sha=hashlib.sha256(raw).hexdigest(); oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 assert sha==v['sha256'],rid
 assert tree.get(v['path'])==oid,rid
 checks.append(dict(id=rid,path=v['path'],sha256=sha,git_blob_oid=oid,status='exact_baseline_bytes_at_current_main'))
def write(name,value):
 (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
write('verification.json',dict(research_ref=MAIN,method='Reconstruct JSON with ensure_ascii=False, indent=2 and trailing newline; verify saved SHA256 and fixed-main full-tree blob SHA1.',tree_path=str(tree_path),checked=len(checks),byte_identical=len(checks),drift=0,tombstones=sum(bool(v['record'].get('merged_into')) for v in records.values()),checks=checks,scope='Only inherited 4 Work + 25 Book records; no whole-library typed-reference or book-text scan.'))
write('original-records.json',records)
refs=[
 dict(id='COL-1900-S1',url='https://www.nlcpress.com/ProductView.aspx?Id=10391',title='上海图书馆藏张元济古籍题跋真迹',authority='上海图书馆编；国家图书馆出版社官网',accessed='2026-10-22',locator='目录第28项，页59',finding='目录将五十四卷本著录为清张宗橚抄本，卷一至四十八配清康熙五十八年刻本；补遗、余波词、附录各一卷。',limitations='本轮实际打开出版社目录；未看到页59原跋影像和馆藏号，故不能单凭同题同卷数证明与98y5sg09ok为同一实物。'),
 dict(id='COL-1900-S2',url='https://www.nlcpress.com/ProductView.aspx?Id=10880',title='上海图书馆藏涉园稿抄校本丛书（全一百册）',authority='上海图书馆编；国家图书馆出版社官网',accessed='2026-10-22',finding='核明上图涉园旧藏影印丛书、ISBN 978-7-5013-6678-1及2019年出版；官网正文未给分册目录，不能由此独立证明54卷具体分配。'),
 dict(id='COL-1900-S3',url='https://www.toho-shoten.co.jp/toho-web/search/detail?bookType=ch&id=457511',title='涉园稿抄校本丛书目录转载',authority='东方法书店目录转载，辅证',accessed='2026-10-22',finding='第49–54卷配张宗橚抄本的著录与S1的前48卷配刻本互补。',limitations='只作S1的辅助定位；不是独立馆藏核验，不据此回写Book。'),
 dict(id='COL-1900-S4',url='https://zh.wikisource.org/wiki/四庫全書總目提要/卷167',title='四库全书总目提要卷167 此山集',authority='古代目录公开转录',accessed='2026-10-22',finding='四卷条明记陈旅选定，与十卷书前提要同有陈旅选定说。'),
 dict(id='COL-1900-S5',url='https://zh.wikisource.org/wiki/欽定四庫全書簡明目錄_(四庫全書本)/卷十七',title='四库全书简明目录卷十七',authority='古代目录公开转录',accessed='2026-10-22',finding='另记此山集四卷，并说明陈旅所定。'),
 dict(id='COL-1900-S6',url='https://zh.wikisource.org/wiki/此山詩集_(四庫全書本)/全覽',title='此山诗集四库本书前提要、陈旅序',authority='古籍公开转录',accessed='2026-10-22',finding='书前提要作十卷、陈旅所选定；与S4/S5四卷目录形成版本层级卷数异文。',limitations='没有四卷与十卷全目录逐篇比对，不能判断重新分卷或删选。'),
 dict(id='COL-1900-S7',url='https://commons.wikimedia.org/wiki/File:Shanghai_敬業堂詩集五十四卷餘波詞一卷詩集補遺一卷餘波詞補遺一卷附錄一卷_part_1.pdf',title='上图54卷本影像入口',authority='上图来源影像的Commons镜像',accessed='2026-10-22',finding='已打开文件说明页，标上海图书馆来源，617页。',limitations='原PDF及第2–4页缩略图读取失败；不能声称已核原跋或卷49卷首。文件题额另列余波词补遗一卷，须单独核对应。')]
write('references.json',refs)
# Concrete non-native source repair proposals; no merge mapping.
proposals=[]
for rid,idx,bookids in [
 ('d59f2gnw9c01',3,['98y4tn1p8i','98y4tn1p8j','98y4tn1p8k']),
 ('d59f2moj9k3l',1,['98y5sg09oi','98y5sg09oj','98y5sg09ok'])]:
 before=records[rid]['record']['indexed_by'][idx]
 after=[]
 if rid=='d59f2gnw9c01':
  entry=copy.deepcopy(before)
  entry.update(title_info='此山詩集（此山先生詩集、周此山先生詩集）十卷',author_info='元周權撰;元陳旅選',summary='共 3 個版本：清刻本（上海圖書館、山東省圖書館）；抄本（北京大學圖書館）；清抄本（南京圖書館）')
  after=[entry]
 else:
  for bid in bookids:
   b=records[bid]['record']; src=b['indexed_by'][0]
   entry=copy.deepcopy(before)
   author=src['summary'].split('｜')[1]
   entry.update(title_info=src['title_info'],author_info=author,summary=src['summary'])
   after.append(entry)
 proposals.append(dict(work_id=rid,path=records[rid]['path'],pre_sha256=records[rid]['sha256'],json_pointer=f'/indexed_by/{idx}',before=before,proposed_replacement_entries=after,evidence_books=bookids,mode='research_proposal_not_applied',preserve_old_value='before is retained verbatim in this checkpoint; final ledger/note must retain correction history',field_policy='Keep existing source/source_bid/section; split scope only, no author union or Book reparenting.'))
write('source-repair-proposals.json',proposals)
cases=[]
for n,c in enumerate(old,1):
 c=copy.deepcopy(c); previous=c['case_id']; c['case_id']=f'COL-1900-{n:03d}'; c['supersedes_case_id']=previous
 c['status']='open'; c['applied']=False; c['native_mutations']=0; c['execution_hold']=True
 c['research_ref']=MAIN; c['source_repair_proposal']='source-repair-proposals.json'; c['main_verification']=dict(all_records_byte_identical=True,record_count=13 if n==1 else 16,reference='verification.json',main_merged_relations=0,source_drift_count=0)
 if n==1:
  c['reason']='本轮把来源聚合污染推进为带原值、前置散列、逐Book证据的精确字段修复提案；四卷及十卷均有陈旅选定证据，仍不得整组并。'
  c['new_findings']=['新增《四库总目》卷167与《简明目录》卷17外证：四卷条也明确陈旅所定。不能把陈旅责任当十卷专属判据。','d59f2gnw9c01.indexed_by[3]应改为十卷陈旅选的三个版本；四卷补遗一卷已在indexed_by[2]保留，不能简单删除两个重复标题而丢三种十卷本。','文渊阁本与总目四卷异文需保持，不仅凭四库标签回填卷数；此结论不改98y6fc2rr7原著录十卷。']
  c['external_sources']=['COL-1900-S4','COL-1900-S5','COL-1900-S6']
  c['next_steps']=['执行前审核source-repair-proposals.json中的indexed_by[3]替换并将旧值写入正式校误台账；无需等待Work合并才能修复范围串接。','取得四卷目录与十卷目录逐篇对照；顾嗣立一卷选本保持独立范围。','文本资产manifest和全型别引用未核，不生成keeper/loser。']
 else:
  c['reason']='本轮将4/48/54卷聚合污染拆为具体来源条提案，并以国家图书馆出版社的上图编目证实54卷馆藏的刻抄配补结构；相应Book的抄者归属存在新冲突，整组仍open。'
  c['new_findings']=['S1目录第28项页59明确：54卷上图藏本为张宗橚抄本，卷1–48配康熙58年刻本；这排除了把54直接当50加4或56的无证算术。','仓库98y5sg09ok.edition称许昂霄钞配，authors却是许昂霄、傅增湘、张元济跋；新权威目录提出张宗橚抄。在原跋/馆藏号对应前标为来源冲突，不把许昂霄跋自动改作抄，也不直接换实体。','d59f2moj9k3l.indexed_by[1]有三个范围：吴翌凤选四卷、康熙58年48卷、54卷刻抄配补本。给出一拆三字段提案，每条author_info独立；吴翌凤不传播至48/54卷。','Commons上图影像标题另列余波词补遗一卷，仓库54卷题名未列；只是待核附加范围，不能擅自补计总卷。']
  c['external_sources']=['COL-1900-S1','COL-1900-S2','COL-1900-S3','COL-1900-S7']
  c['edition_attribution_conflict']=dict(book_id='98y5sg09ok',field='edition',repository_value=records['98y5sg09ok']['record']['edition'],authoritative_catalog='清张宗橚抄本（卷一至四十八配清康熙五十八年刻本）',identity_of_physical_copy_verified=False,action='hold Book attribution overwrite; obtain page59 colophon/call number and scan volume49 heading')
  c['next_steps']=['先按逐Book原目录完成Work聚合来源一拆三并保留旧原文；54卷来源条保留原著录，不暗中把抄者校改混入来源重分组。','定点读取上图编《题跋真迹》页59与54卷影像第49卷起首，核张宗橚/许昂霄身份及同一馆藏号。','核48、50及54的篇目而非相减卷数；吴翌凤四卷选本、一卷本、稿本继续隔离。','完整typed refs、book-text联动和main规则审计未过，不执行Work并条。']
 cases.append(c)
write('cases.json',cases)
print('verified',len(checks),'records; wrote',len(cases),'replacement cases and',len(proposals),'source repair proposals')
