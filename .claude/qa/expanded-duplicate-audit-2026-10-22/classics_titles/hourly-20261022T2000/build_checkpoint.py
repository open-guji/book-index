import json,sqlite3,pathlib,hashlib,subprocess,gzip,re
ROOT=pathlib.Path(__file__).resolve().parent
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DB='/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite'
TREE=pathlib.Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z')
c=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
manifest=json.loads(c.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base']==BASE
assert hashlib.sha256(TREE.read_bytes()).hexdigest()==manifest['tree_sha256']
tree={}
for x in TREE.read_bytes().split(b'\0'):
 if x:
  h,p=x.split(b'\t',1);tree[p.decode()]=h.decode().split()[2]
pairs=json.load(open(ROOT.parent/'broad-20261022/candidate-pairs.json'))
selection=[27,28,29,31,36,37,39,41]
ids=sorted({i for n in selection for i in pairs[n]['ids']})
snaps={};check=[]
for i in ids:
 row=c.execute('select path,blob_sha,sha256,data from records where id=?',(i,)).fetchone()
 path,oid,sha,data=row
 assert tree[path]==oid
 b=subprocess.check_output(['git','cat-file','blob',oid])
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
 assert hashlib.sha256(b).hexdigest()==sha
 d=json.loads(b);assert d==json.loads(data);assert not d.get('merged_into')
 snaps[i]={'id':i,'path':path,'blob_sha':oid,'sha256':sha,'raw_utf8':b.decode(),'data':d}
 check.append({'id':i,'path':path,'blob_sha':oid,'sha256':sha,'tree_match':True,'raw_hash_verified':True,'sqlite_equal':True,'active':True})
oldhits=[];oldfiles=[]
for f in ROOT.parent.rglob('cases.json'):
 if ROOT in f.parents:continue
 oldfiles.append(str(f.relative_to(ROOT.parent)))
 found=set(re.findall(r'd59[a-z0-9]+',f.read_text())) & set(ids)
 if found:oldhits.append({'path':str(f),'ids':sorted(found)})
assert not oldhits
refs=[
 {'id':'E1','url':'https://zh.wikisource.org/zh-hant/宋史/卷206','pointer':'蓍龜類；web lines 804–808','excerpt':'京房《易傳算法》一卷《易傳》三卷管輅《遇仙訣五音歌》六卷《周易八仙歌》三卷；《易傳》一卷郭璞《周易洞林》一卷','claim':'前置責任者承接：三卷本屬京房；一卷本屬管輅。'},
 {'id':'E2','url':'https://zh.wikisource.org/zh-hant/隋書/卷32','pointer':'經籍志一：易類284行；春秋863行；小學1275、1353行','excerpt':'《周易繫辭義疏》二卷劉瓛撰。／《春秋條例》十一卷晉太尉劉寔撰。／《發蒙記》一卷晉著作郎束皙撰。／《聲類》十卷魏左校令李登撰。','claim':'四案原始目錄的作者、書名、卷數及部類。'},
 {'id':'E3','url':'https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷174','pointer':'卷首劉氏實條；web lines 116–127；庫存原頁KR2n0011_WYG_174-1a','excerpt':'劉氏〈實〉春秋條例；隋志十一卷；左氏牒例；唐志二十卷','claim':'劉實與劉寔的同書比對；後續左氏牒例另起標目，不納入本案。'},
 {'id':'E4','url':'https://zh.wikisource.org/zh-hant/隋書/卷33','pointer':'經籍志二地理類；web lines 1446–1454','excerpt':'《發蒙記》一卷束皙撰。載物產之異。','claim':'同志史部另列，不能僅用作者異體消除兩部類區別。'},
 {'id':'E5','url':'https://zh.wikisource.org/zh-hant/發蒙記','pointer':'馬國翰輯本序；web line126','excerpt':'兩書同名而分著之與？抑一書而兩載，失於釐定歟？疑不能明。','claim':'輯者明言兩書或重出未決，且所輯含啓蒙記一條及未詳所據九條。'},
 {'id':'E6','url':'https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷069','pointer':'web lines 285–299；庫存原頁KR2n0011_WYG_069-21a/21b','excerpt':'劉氏〈瓛〉周易繫辭義疏／沈氏〈驎士〉周易兩繋訓注','claim':'劉瓛與沈驎士兩作品各有獨立標目；不可互混或與易經原典合併。'},
 {'id':'E7','url':'https://zh.wikisource.org/zh-hant/南齊書_(四庫全書本)/卷54','pointer':'高逸傳沈驎士段，著述列舉，無現代標點原文','excerpt':'著周易兩繫莊子內篇訓注易經禮記春秋尚書論語孝經䘮服老子要畧數十卷','claim':'訓注與要略成組，周易兩繫訓注不能吸收易經要略；數十卷屬合列，不能賦予單書。'},
 {'id':'E8','url':'https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷223','pointer':'web lines 207–220；庫存原頁KR2n0011_WYG_223-8a','excerpt':'孝眀帝〈巋〉孝經義記；佚','claim':'帝號附名直指巋，與相鄰梁武帝、簡文帝諸書分立。'},
 {'id':'E9','url':'https://zh.wikisource.org/zh-hant/隋書/卷79','pointer':'蕭巋傳末；web line153','excerpt':'梁之臣子諡曰孝明皇帝，廟號世宗。','claim':'蕭巋與孝明帝獨立人物同一證；本傳現代標點把孝經、周易義記拆開，書題仍據E8，不冒稱本傳逐字同題。'},
 {'id':'E10','url':'https://zh.wikisource.org/zh-hant/清史稿/卷145','pointer':'藝文志一：易類輯佚line138；小學類韻書line227','excerpt':'梁武帝《周易大義》一卷；以上均馬國翰輯。／魏李登《聲類》一卷；以上均馬國翰輯。','claim':'古書原卷數與清輯本一卷可並存，但不能憑此替未載版本的總目條指定輯家。'},
 {'id':'E11','url':'https://www.shidianguji.com/zh/book/CADAL02091108/chapter/1lcpv6bbdy6us','pointer':'三國藝文志卷一，小學類韻書之屬，李登聲類條；web lines508–510','excerpt':'隋唐志，並十卷，今佚。輯錄二百餘條，隱依今韻排次。','claim':'原典轉錄引馬國翰輯本序，可證原書與輯本範圍差異；與庫內同源姚氏引文不算獨立古代證詞。'},
 {'id':'E12','url':'https://zh.wikisource.org/zh-hant/隋書/卷32','pointer':'易類web lines249–257','excerpt':'《周易大義》二十一卷梁武帝撰。／《周易大義》一卷','claim':'同一目錄另有無撰人一卷本；不可用一卷機械把總目條對到此條或武帝原書。'}
]
for r in refs:r.update(accessed='2026-10-22',evidence_level='primary_text_transcription_not_image',image_checked=False)
common_gates=['同步最新origin/main並重核全字段與墓碑狀態','逐字段無損台帳，保存所有來源、責任角色、獨有ai_note/description及矛盾原值','逐Book/Collection/Entity/分類/promotions型別引用審計；草稿庫同步另PR','book-text整理本、輯佚檔及內容引用遷移核查','正式audit-merge-ledger T/L/P/R、check_v2、check-classification及官方build_derived --check-only全通過']
configs=[
 (27,'separate','易傳：京房三卷錯掛管輅，與管輅一卷分立',None,['E1'],
 '宋志整段採作者前置；京房領易傳算法一卷及易傳三卷，管輅從遇仙訣五音歌起，領周易八仙歌及易傳一卷。三卷條作者名、entity、朝代及description均受截句錯誤污染。另一條題管格而按語全述管輅，是另項字形污染；相同entity不構成同書證。',
 ['d59f27sg4b2a#/indexed_by/0','d59f27sg4b2a#/authors/0','d59f27sg4b2a#/ai_note','d59f27sg4b2a#/description','d59f27xhh6o3#/indexed_by/0/summary','d59f27xhh6o3#/authors/0'],
 ['校正文獻責任人與受污染推生字段；保留舊說原值入污染台帳','另查京房三卷本現有Work，不能將這對分立計作京房去重成功','管格字形與注角色須查三國藝文志原頁；不因本文判斷直接修改contains_text_of']),
 (28,'confirmed','聲類：魏李登原書與輯本目錄重出','d59f27t3uccg',['E2','E10','E11'],
 '總目側13項author_info全部為魏李登，首項明示三國魏李登撰、清黃奭輯；所稱明李登只在衍生authors/dynasty/period。隋志十卷和清史稿馬國翰輯一卷解釋原書/輯本卷差；作品對象同一可確認，但13條版本著錄與附刻韻書不能不分範圍整包吞入。',
 ['d59f27t3uccg#/indexed_by/0','d59f27t3uccg#/indexed_by/2','d59f27t3uccg#/indexed_by/3','d59fyivqiept#/indexed_by','d59fyivqiept#/indexed_by/3/title_info','d59fyivqiept#/authors/0','d59fyivqiept#/ai_note','d59f27t3uccg#/related_works/0'],
 ['將明代人物URI與衍生朝代列污染候選，不以同名誤合兩個Person','逐核21版本及note列13 Book的現行ID，附韻集/韻畧/聲譜/音譜/字音韻譜不歸原作正文','保留黃奭、馬國翰、任大椿等輯本差異；趙之謙role異常原note不可丟','現有兩條之related邊在合併後會成自邊，須有顯式處理台帳']),
 (29,'confirmed','春秋條例：劉實／劉寔異名重出','d59f27wapo8x',['E2','E3'],
 '經義考卷174卷首劉氏實條明引隋志十一卷，隋志原文署晉太尉劉寔；同卷隨後的生平亦指劉寔。同一條隋志著錄在兩側重出。這比同entity或實寔字形更強。十/十一/二十卷諸源異數留各源；本案不吸收左氏牒例二十卷或公羊達義。',
 ['d59f27td7gn6#/indexed_by/0','d59f27wapo8x#/indexed_by/2','d59f27wapo8x#/indexed_by/3'],
 ['經義考條的attested_status及卷174原頁保留','補晉書條summary中的劉庭疑OCR不可提升為作者別名','左氏牒例與公羊達義僅為排除邊界，本案不另判不另計']),
 (31,'open','發蒙記：經部小學／史部地理重出或同名書未決',None,['E2','E4','E5'],
 '隋志兩部確實各列一卷束皙；史部特注載物產之異。馬國翰輯本序明言兩書或重出疑不能明。庫中地理側已吸入秦榮光經部著錄，小學側輯本又混物產佚文，不能把同作者異體與同卷數當成同書。現階段保持兩Work，不以歷代疑說充確認。',
 ['d59f27tuor29#/indexed_by/2','d59f27tuor29#/indexed_by/3','d59f27tuor29#/indexed_by/7','d59f27wtfwua#/indexed_by/0','d59f27wtfwua#/indexed_by/3','d59f27wtfwua#/indexed_by/5','d59f27wtfwua#/indexed_by/6'],
 ['逐段核兩類著錄、馬氏輯本及說郛十五條；特別排除啓蒙記一條','地理側秦榮光經部來源是否錯掛須獨立污染台帳','未能證明一書前不改成一書兩著，不合Work']),
 (36,'confirmed','周易繫辭義疏：劉瓛系／繫異體重出','d59f2841glc0',['E2','E6'],
 '隋志明列劉瓛二卷；經義考同人同題。另一側補南齊兩志直接以隋志、新唐志為據，所指為同一作品而非新編；系/繫為字形差。原作二卷與後人一卷輯本不互覆；乾坤義佚文的混入辨析須保留。',
 ['d59f2841glc0#/indexed_by/0','d59f2841glc0#/indexed_by/1','d59f2841glc0#/indexed_by/3','d59f8ii7ck5d#/indexed_by/0','d59f8ii7ck5d#/indexed_by/1','d59f2841glc0#/related_works'],
 ['完整保存補南齊志所引張惠言、馬國翰輯本邊界','contains_text_of原典邊保留；不能與原典或乾坤義合併','keeper existing indexed_by merged_from自值是歷史來源原值，本輪不擅改']),
 (37,'open','周易大義：梁武帝原書與總目一卷本待版本定位',None,['E10','E12'],
 '隋志武帝二十一卷與清史稿馬國翰輯一卷建立可行原作/輯本鏈；總目側作者南朝梁武帝同一，但僅著一個未載版本的記錄。隋志另有無撰人同題一卷，原書/輯本/同名條界限不能只憑卷數。保留高度疑同判斷，待總目源記錄giv76i0d03xubbl7版本及序錄驗證。',
 ['d59f2843yhoh#/indexed_by/0','d59f2843yhoh#/indexed_by/1','d59f2843yhoh#/indexed_by/2','d59fxygrmxvl#/indexed_by/0','d59fxygrmxvl#/ai_note','d59f2843yhoh#/related_works/1'],
 ['核總目原記錄giv76i0d03xubbl7及所藏本，確認輯家與內容範圍','不得把二十/二十一原書卷數改成輯本一卷','若身份升確認，related互指自邊和輯佚檔須列執行台帳']),
 (39,'confirmed','周易兩繫訓注：沈驎士繋／繫異體重出','d59f28503xmo',['E6','E7'],
 '經義考直接標沈驎士周易兩繋訓注；補南齊志以本傳著述列舉建立同題。南齊書四庫轉錄未標點原文支持訓注/要略兩組，不能把數十卷或另列易經要略揉為本書。只合兩條同一兩繫訓注，不吸收莊子訓注或易經要略。',
 ['d59f28503xmo#/indexed_by/0','d59f8ii6euip#/indexed_by/0'],
 ['保存兩繫/兩繋字形與經義考原頁、佚之來源判斷','補南齊條title_info兼載易經要略，遷移保留原文並標明本Work承載兩繫訓注範圍','南齊書現代有標點版本歧讀，不用其標點當作新作品證']),
 (41,'confirmed','孝經義記：西梁孝明帝／蕭巋重出','d59f990c2b5x',['E8','E9'],
 '經義考孝明帝巋標目直指蕭巋，隋書本傳明載蕭巋諡孝明皇帝；補周、補梁、補南北史三志同述此書。帝號與姓名非兩作者。隋書現代標點將孝經與周易義記拆開，故題名依經義考，人物同一依本傳，不冒稱所有來源逐字相同。',
 ['d59f2850f66e#/indexed_by/0','d59f990c2b5x#/indexed_by/0','d59f990c2b5x#/indexed_by/1','d59f990c2b5x#/indexed_by/2','d59f990c2b5x#/period_basis'],
 ['保存孝明帝稱號、經義考佚判和原頁，不改作確定全佚','補周志收書時代與作者西梁身份分開；period_basis現仍稱北周須記矛盾','不將鄰列梁武帝/簡文帝孝經義疏納入'])
]
cases=[]
for k,(n,status,title,keeper,evidence,reason,pointers,gates) in enumerate(configs,1):
 pair=pairs[n]
 cases.append({'case_id':f'JC-2000-{k:03d}','status':status,'title':title,'ids':pair['ids'],'supersedes':[], 'new_case':True,'candidate_pair_index_zero_based':n,'candidate_provenance':pair,'decision':reason,'relationship_kind':{'confirmed':'same_work','separate':'homonym_with_author_contamination','open':'scope_or_edition_unresolved'}[status], 'research_keeper_candidate':keeper,'research_loser_candidates':[i for i in pair['ids'] if keeper and i!=keeper],'machine_merge_mapping':None,'native_merges':0,'already_main_covered':False,'evidence_ids':evidence,'evidence_urls':[r['url'] for r in refs if r['id'] in evidence],'exact_source_pointers':pointers,'records':[{q:snaps[i][q] for q in ['id','path','blob_sha','sha256']} for i in pair['ids']],'specific_execution_gates':gates,'common_execution_gates':common_gates,'raw_conflict_archive':'main-records.json.gz contains complete data and exact raw_utf8 for both records; pointers identify disputed fields'})
def write(name,obj):
 (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
write('cases.json',cases);write('references.json',refs)
with gzip.open(ROOT/'main-records.json.gz','wt',encoding='utf-8') as f:json.dump({'base':BASE,'records':snaps},f,ensure_ascii=False,indent=2)
write('validation.json',{'base':BASE,'database_manifest':manifest,'tree_verified':True,'records':check,'old_cases_checked':oldfiles,'prior_case_id_overlaps':oldhits,'selected_candidate_pairs':selection,'candidate_pair_total':len(pairs),'selected_count':8,'new_confirmed':5,'new_separate':1,'new_open':2,'native_merges':0,'native_files_modified':0,'database_readonly':True,'not_audited':['global inbound references','Book records','promotions','draft repository','book-text','schema/classification/build after merge'],'rules_read':[BASE+':.claude/qa/正式库并条审查规则.md',BASE+':schema/cataloging-rules.md'],'local_main_is_stale':'4d6e3219417ac0f2217548b7c241e098c4d39815; no native records sourced from that ref'})
print('Saved',len(cases),'cases;',len(snaps),'complete records;',len(refs),'references; prior overlaps',len(oldhits))
