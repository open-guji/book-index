from pathlib import Path
import json,hashlib,subprocess,datetime,copy,gzip
root=Path.cwd(); out=Path(__file__).parent
base=out.parent; old=json.loads((base/'cases.json').read_text())
snap={}
def rec(id,typ):
 p=next((root/typ).glob('/'.join(id[-3:])+'/'+id+'*.json'))
 b=p.read_bytes();d=json.loads(b); h=hashlib.sha256(b).hexdigest();snap[id]={'path':str(p.relative_to(root)),'sha256':h,'record':d};return snap[id]
def evidence(id):
 r=rec(id,'Work');return {'work_id':id,**{k:r[k] for k in ('path','sha256')},'indexed_by':r['record'].get('indexed_by',[]),'authors':r['record'].get('authors',[])}
def case(cid,status,label,ids,why,works,sources,prior=None):
 records=[rec(i,'Entity') for i in ids]
 c={'case_id':cid,'status':status,'type':'Entity','label':label,'keeper':ids[0],'losers':ids[1:],'paths':{i:r['path'] for i,r in zip(ids,records)},'sha256':{i:r['sha256'] for i,r in zip(ids,records)},'why':why,'evidence_refs':[evidence(i) for i in works],'external_evidence':sources,'scope':'identity adjudication; no native data modified'}
 if prior: c['supersedes_case_id']=prior
 if status=='confirmed':
  names=copy.deepcopy(records[0]['record'].get('alt_names',[]))
  for i,r in zip(ids[1:],records[1:]):
   for n in r['record'].get('alt_names',[]):
    if n not in names:names.append(n)
   n={'name':r['record']['primary_name'],'type':'別稱','note':'姓連字之著錄稱呼；本次以原始傳記/書目交叉核定，見 '+cid}
   if not any(x['name']==n['name'] for x in names): names.append(n)
  c['machine_decision']={'field_overrides':{'alt_names':names},'field_delete':[]}
  c['field_decisions']=[{'field':k,'decision':('union all notes/history/sources with original owner; retain description text' if k in ['description','ai_note','merged_in','merge_history','sources'] else 'keep keeper value; archive source values; do not infer new date/place/external-ID values')} for k in sorted(set().union(*(r['record'].keys() for r in records))) if k!='alt_names']
  c['apply_prerequisites']=['Recheck SHA256 immediately before mutation','Update every live typed authors[].entity_id reference in Work/Book/Collection, including records added upstream','Preserve loser tombstone, all notes, sources, historical merge ledgers and original snapshots','Rebuild official derived indices and run project schema/reference validations','Inspect cross-repository typed references before apply; local reference scan is not full book-text validation']
  c['reference_policy']='Redirect entity_id only; retain author name and role. Do not merge works or books as a consequence.'
 return c
S=lambda n,u,f,**kw:dict(name=n,url=u,finding=f,accessed='2026-10-22',**kw)
cases=[]
cases.append(case('PNA-H001','confirmed','蔡卞 / 蔡元度',['hixhd2h9bdyg','hixhd2h9bt2e'],'原open案的董逌尾文已定位為下條《廣川詩故》的作者，不是蔡卞作品共同作者。《四庫總目》《經義考》明記卞字元度；通志堂經解本署蔡元度，同為毛詩名物解二十卷。人物可合；原始尾文不刪，以校勘註說明。',['d59f2hrbldz4','d59f2hs0vlz7','d59f2hgi181t','d59f2hemlypx'],[S('古今圖書集成·經籍典引宋史藝文志','https://zh.wikisource.org/wiki/Page:Gujin_Tushu_Jicheng,_Volume_568_(1700-1725).djvu/111','分列蔡卞《毛詩名物解》二十卷、董逌《廣川詩故》四十卷。讀取頁面183–187行。頁面標未校對，與本庫經義考和四庫提要交叉核定。'),S('授經圖義例卷12','https://zh.wikisource.org/zh-hans/授經圖義例_(四庫全書本)/卷12','分列毛詩名物解二十卷蔡卞與廣川詩故四十卷董逌。搜尋取得原文轉錄。')],prior='PNA-R010'))
cases[-1]['caveats']=['保留蔡卞既有文元/文正諡號、1058生年，不借同人合併重裁傳記字段。文元需另核；經義考引東都事略作文正。','三個名物解/詩學名物解Work是否同作另交經部，不在本案機器決策中合書。','d59f2hs0vlz7 measures 作冊20但 measure_info 二十卷，是既有計量問題，另案修復。']
cases.append(case('PNA-H002','confirmed','喻樗 / 喻子材',['hixhd2h9bhcp','hixhd2h9bppr'],'陸游《入蜀記》乾道六年六月十二日直接稱「喻子材郎中樗」，經義考引紹興府志稱喻樗字子才，互證姓名。孤立子材條只繫宋史《豐公逸事》，CBDB人物22849搜尋結果列同著作；全部五部所繫Work未見跨代或別人反證。',['d59f2psls7i9','d59f2hdmefpg','d59f2hdr2zuq','d59f2hdpit4w','d59f2hicirr6'],[S('陸游入蜀記卷1','https://zh.wikisource.org/wiki/入蜀記/卷1','乾道六年六月十二日：早，謁喻子材郎中樗。頁面152行，直接讀取。'),S('CBDB喻樗22849','https://cbdb.fas.harvard.edu/cbdbapi/person?id=0022849','搜尋索引顯示喻樗及豐公逸事；直開不可用。僅作書目輔證，非成功API讀取。',retrieval='search snippet; open unavailable')]))
cases[-1]['caveats']=['子材和子才兩種字形均保留；保留keeper既有湍石、玉泉及卒1180，不以新研究覆蓋外部映射。','若要求豐公逸事責任者的獨立原書書影證明，可先取無錫金匱縣志卷39藝文或宋史卷203對讀；本案提供人物同一性確證，不合併任何書。']
cases.append(case('PNA-H003','separate','李昭遘 / 李逢吉',['hixhd2h9br6i','hixhd2h9bra8'],'北宋李昭遘字逢吉，不能併入唐代李逢吉。長編康定元年載李昭遘進永熙政範；斷金集直齋著錄為唐令狐楚與李逢吉唱酬，開成初裴夷直序。兩者相隔約二世紀。',['d59f2puydiio','d59f28jyvj7m'],[S('續資治通鑑長編卷128','https://ctext.org/wiki.pl?chapter=460118&if=en','康定元年李昭遘上太宗藩邸聖製三卷、永熙政範二卷。搜尋取得原文。')]))
cases[-1]['next_step']='保留兩實體；候選生成器將此pair標已裁separate，不因姓連字再送入待合清單。'
cases.append(case('PNA-H004','open','汪仲洋 / 汪少海',['hixhd2h9brru','hixi8u5rqf3y'],'晚晴簃詩匯足證汪仲洋字少海，但孤立汪少海名下是禱河冰譜正拍，還沒有卷端/序跋把該正拍者與成都汪仲洋連起來。CiNii只列羅瀛填詞與1824原刻；不能以同時代同字自動併。',['d59f2mvbd4w0','d59fssngoirn'],[S('晚晴簃詩匯卷116','https://ctext.org/wiki.pl?chapter=658574&if=en','汪仲洋字少海，成都人，有心知堂詩稿；搜尋命中，正文頁可開但find未命中。'),S('CiNii BB05605462','https://ci.nii.ac.jp/ncid/BB05605462','祷河冰谱12出首1出，羅瀛填詞；原本道光四年吳儀寫刻本。頁面124、188行。未列正拍者本名。')]))
cases[-1]['next_step']='查傅惜華藏古典戲曲珍本叢刊第90冊禱河冰譜卷端與序跋，或國圖道光原刻本；尋汪少海署籍貫、官職或本名。'
cases.append(case('PNA-H005','open','朱敦儒 / 朱希真',['hixhd2h9bhqe','hixi8u5qspby'],'朱敦儒字希真關係可靠，但《朱敦儒陳淵集》不是已證實的本庫切分錯誤：宋史卷208通行轉錄本身也作該連寫，後接詞三卷。不能憑陳淵亦為人名就擅拆書。本輪把原待核假說改為需校勘原書與不同版本。',['d59f2hgz79xe','d59fryddhqfd','d59fssnosow0','d59f2hi77qiq','d59f2hk4tnnn','d59f2hqag5c0'],[S('宋史卷208','https://zh.wikisource.org/zh-hant/宋史/卷208','搜尋結果明列《朱敦儒陳淵集》二十六卷又《詞》三卷；正文find未命中，作轉錄異常線索而非書影校定。')],prior='PNA-R017'))
cases[-1]['next_step']='覆看宋史卷208不同刻本原頁及校勘記，判陳淵是否原書名、衍字或串行；同時核朱敦儒籍貫保昌與本傳洛陽之不一致，不能只繼承CBDB值。'
allids={i for c in cases for i in [c['keeper'],*c['losers']]}
# Whole current native corpus author-reference scan, excluding historical free-text matches.
files=subprocess.check_output(['rg','-l','|'.join(sorted(allids)),'Work','Book','Collection'],text=True).splitlines()
refs={i:[] for i in allids}
for p in files:
 b=Path(p).read_bytes();d=json.loads(b)
 if d.get('merged_into'):continue
 hit={a.get('entity_id') for a in d.get('authors',[]) if a.get('entity_id') in allids}
 if not hit:continue
 snap[d['id']]={'path':p,'sha256':hashlib.sha256(b).hexdigest(),'record':d}
 for i in hit:refs[i].append({'id':d['id'],'type':d['type'],'path':p,'sha256':snap[d['id']]['sha256']})
for c in cases:
 rr={r['id']:r for i in [c['keeper'],*c['losers']] for r in refs[i]}
 c['related_records']=list(rr.values());c['related_record_ids']=sorted(rr)
 c['related_counts']={t:sum(r['type']==t for r in rr.values()) for t in sorted({r['type'] for r in rr.values()})}
# Recheck previous 13 confirmed input hashes; no new endorsement of every scholarly conclusion.
checks=[]
for c in old:
 if c['status']!='confirmed':continue
 for i,p in c['paths'].items():
  h=hashlib.sha256(Path(p).read_bytes()).hexdigest();checks.append({'case_id':c['case_id'],'id':i,'hash_match':h==c['sha256'][i]})
summary={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'case_counts':{s:sum(c['status']==s for c in cases) for s in ['confirmed','open','separate']},'new_pairs':3,'revisited_open_pairs':2,'status_transitions':{'PNA-R010':'open -> confirmed','PNA-R017':'open -> open, better-defined source question'},'new_confirmed_groups':2,'new_confirmed_losers':2,'new_separate_groups':1,'new_open_groups':1,'existing_open_updated':1,'prior_confirmed_entity_hash_checks':checks,'all_prior_hashes_match':all(x['hash_match'] for x in checks),'snapshot_records':len(snap),'native_data_mutations':0,'cross_repo_validation':'not done by this lane; integration prerequisite','commit_or_pr':'none by this lane'}
for name,data in [('cases.json',cases),('stats.json',summary),('references.json',refs)]:
 (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
with gzip.open(out/'original-snapshots.json.gz','wt',encoding='utf-8') as f:json.dump(snap,f,ensure_ascii=False)
print(json.dumps({k:v for k,v in summary.items() if k!='prior_confirmed_entity_hash_checks'},ensure_ascii=False,indent=2))
