"""Read-only fixed-main research; writes only its own directory. No merge execution."""
import hashlib,json,sqlite3,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=OUT.parents[3]
ROOT=Path('/workspace/scratch/0bc7226fa660')
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
db=sqlite3.connect(f'file:{ROOT}/audit/broad-current.sqlite?mode=ro',uri=True)
db.row_factory=sqlite3.Row
manifest=json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base']==BASE
tree={}
for entry in (ROOT/'audit/current-main-tree.z').read_bytes().split(b'\0'):
 if entry:
  h,p=entry.decode().split('\t');tree[p]=h.split()[2]
assert hashlib.sha256((ROOT/'audit/current-main-tree.z').read_bytes()).hexdigest()==manifest['tree_sha256']
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def blob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
selected=['H-BROAD-00002','H-BROAD-00004','H-BROAD-00014','H-BROAD-00019','H-BROAD-00126','H-BROAD-00161','H-BROAD-00203','H-BROAD-00207']
inputs=json.loads((OUT.parent/'broad-20261022/review-input.json').read_text())
inputs=[d for d in inputs if d['candidate']['candidate_id'] in selected]
bycand={x['candidate']['candidate_id']:x for x in inputs}
ids={i for x in inputs for i in x['candidate']['ids']}|{'d59fyqxfoagx'}
records=[];rawdir=OUT/'snapshots';rawdir.mkdir(exist_ok=True)
def add_record(p,b,expected_sha256=None,read_from='current-main-matching archived bytes'):
 assert blob(b)==tree[p],p
 if expected_sha256: assert hashlib.sha256(b).hexdigest()==expected_sha256,p
 d=json.loads(b);(rawdir/(d['id']+'.json')).write_bytes(b)
 rec={'id':d['id'],'type':d['type'],'path':p,'blob_sha':blob(b),'sha256':hashlib.sha256(b).hexdigest(),'read_from':read_from,'snapshot':'snapshots/'+d['id']+'.json','data':d};records.append(rec);return rec
for i in sorted(ids):
 r=dict(db.execute('select * from records where id=?',(i,)).fetchone());assert r['blob_sha']==tree[r['path']]
 add_record(r['path'],r['data'].encode(),r['sha256'],'read-only fixed-main SQLite raw data')
# Filename neighborhood is explicit and bounded, not an all-reference census.
need=['丙湖遊幸','西湖遊幸','天啓本東安','天啓東安','嘉定鎮江志','丁酉北闈','二十四史月日','乾隆臺灣府志','乾隆重修臺灣府志','乾隆重修福建臺灣府志','乾隆新疆外藩紀畧','乾隆新疆紀畧']
for p in tree:
 if p.startswith('Book/') and any(x in p for x in need): add_record(p,(ROOT/'book-index'/p).read_bytes())
parent_ids={x['id'] for r in records for x in r['data'].get('contained_in',[])}
for p in tree:
 if p.startswith('Collection/') and p.split('/')[-1].split('-')[0] in parent_ids: add_record(p,(ROOT/'book-index'/p).read_bytes())
dump('current-records.json',records)
sources=[
 {'id':'S1','url':'https://www.loc.gov/item/2014514489/','access':'search-index metadata read; direct open 403; no image inspection','pointer':'Notes: title leaf and four bound volumes','finding':'LOC describes title leaf Xinjiang waifan jilue, while volumes 1–2 are Xinjiang jilue and volumes 3–4 Waifan jilue; this exposes a whole/part risk.'},
 {'id':'S2','url':'https://taicool.ith.sinica.edu.tw/browse-ebook.html?id=EB0000000105','access':'opened full catalogue entry','pointer':'提要, web lines 37–38','finding':'Academia Sinica identifies Fan Xian compilation as 25 juan and states it combines and revises Gao/Liu gazetteers. It is not merely another title for Liu’s earlier gazetteer.'},
 {'id':'S3','url':'https://ci.nii.ac.jp/ncid/BN03253416','access':'opened full catalogue entry','pointer':'bibliography and notes; lines 120–126,311','finding':'Lu Xian, Jiading Zhenjiang zhi, Wanwei biecang 44; residual 22 juan plus first juan.'},
 {'id':'S4','url':'https://ci.nii.ac.jp/ncid/BA64163665','access':'opened full catalogue entry','pointer':'bibliography and notes; lines 120,131,211','finding':'Lu Xian; alternate short title Jiading Zhenjiang zhi; reprint based on Daoguang 22 printing.'},
 {'id':'S5','url':'https://www.toyo-bunko.org/open/KansekiQueryResult10.php?ORDERBY1=&UNIT=200&andor=&iPage=56&iTotal=80868&navizonestart=6&searchtype=&sw1=','access':'opened catalogue with neighboring entries','pointer':'No.11066–11069, callmark II-11-B-a-285; lines149–155','finding':'Anci context separates Tianqi Dong’an residual five juan (2–6), Qianlong 22 juan and Kangxi 10 juan. Tianqi entry says reprint from Tianqi 5, Ming Feng Taiyun; Zheng name is 鄭之成, variant to local 鄭之城. External reprint year 1936 differs from local Collection 1935.'},
 {'id':'S6','url':'https://www.ahm.cn/Wap/News/Details/cpzm?nid=11165','access':'search-index catalogue excerpt only; direct open405','pointer':'Anhui Museum inventory GJ01391','finding':'Dingyou beiwei DAYU jilue, Xin Tianweng, 1911 Commercial Press lead type. Supports typo hypothesis but does not inspect Nanjing QIYU original.'},
 {'id':'S7','url':'https://commons.wikimedia.org/wiki/File:NTUL-9900006341_丁酉北闈大獄記略_一卷.pdf','access':'opened metadata; no PDF image inspection','pointer':'NTUL-9900006341, accession2504830; 34pages','finding':'NTU copy is 1917 Shanghai Commercial Press, one juan by Xin Tianweng; later edition only.'},
 {'id':'S8','url':'https://www.city.machida.tokyo.jp/bunka/bunka_geijutsu/cul/cul08Literature/kensaku_mokuroku/aosiba.files/kanseki.pdf','access':'PDF text read and page26 (zero-based25) screenshot visually inspected','pointer':'entry105 香豔叢書; 第十一集, PDFpage26 lines839–842','finding':'In Xiangyan congshu XI, Xihu youxing ji one juan by Zhou Mi follows Xuanmiao dongtian ji and precedes Xihu liuqiao taoping. Parent edition is 1910–1911 Guoxue fulunshe.'},
 {'id':'S9','url':'https://commons.wikimedia.org/wiki/File:NLC892-412000002897-66220_二十四史月日考_第19冊.pdf','access':'opened derivative metadata; no manuscript image inspection','pointer':'NLC善本書號A02187; lines125–153','finding':'Wang Yuezheng manuscript; residual116 juan; Zhou shu only upper juan. Not an identity assertion with the 236-juan 日月考 catalogue record.'},
 {'id':'S10','url':'https://zh.wikisource.org/zh/崇文總目輯釋/卷二','access':'read original catalogue commentary in transcription, not book image','pointer':'地理類; lines1422–1434, especially1426–1428','finding':'Qian Yi explicitly annotates the Ping Juhui one-juan Yutian guo xingcheng ji entry: Song catalogue uses 錄 for 記. Direct title equivalence commentary rather than merely copied adjacent paragraphs.'},
 {'id':'S11','url':'https://data.library.sh.cn/gj/resource/instance/1wma8m8f8za6n50k','access':'direct open unavailable','pointer':'丙湖 original instance; same access failure for izc7xadnzhfqss4x and bbrnaoodlhqruqmn','finding':'No claim that live Shanghai original entries were read; use fixed-main source identifiers and independent contextual catalogues, retaining source-inspection gates.'}
]
dump('sources.json',sources)
case_specs=[
('H-BROAD-00002','open','新疆全书与分篇范围不能因短题合并', ['S1'], ['固定记录两题均署七十一；外藩题二卷有乾隆四十二年思位堂刻本，短题同时含西域闻见录本、丛钞本及一卷著录。','LOC实物目录把同一总题之下的新疆纪略与外藩纪略分装，说明总题、分题共存。当前外藩二卷到底只含外藩分篇还是全书，尚无卷首及目录证据。'], ['读9949tyvk74等思位堂本目录、卷首和末叶，核是否新疆篇或外藩篇；再核994pgaw5j4的西域闻见录位置及一卷条的节录界限。'], []),
('H-BROAD-00004','open','台湾一卷杂钞不能直接等同范志二十五卷', ['S2'], ['993yll8zk0 contained_in→8rldo9qhnwua明确为管庭芬待清书屋杂钞，所载一卷；范志主体二十五卷首一卷。','独立提要确认范志的篇章纲目和增损前志性质，无法证明杂钞一卷是残卷、节抄还是摘要改编。'], ['查天津图书馆待清书屋杂钞该子目起讫、卷首题及选抄说明；在摘编/残本范围消歧前不定keeper。'], []),
('H-BROAD-00014','confirmed','嘉定镇江志方括号与丛书子目同一原作', ['S3','S4'], ['同属宋卢宪嘉定镇江志，22卷主体；宛委别藏残22卷首1卷独立馆目与两侧所载版本相接，括号是年号标示。附录、清人校勘记属于版本附属，不构成另一卢宪原作。','Book 994bqhru9t把宣统二年刻与宋嘉熙二年碛砂延圣院刻串接并解析year1238；9945fxcw74把抄本与奚冈篆刻串接；9950nh4740把嘉定六年修误当抄写年1213。三处是出版字段污染，不能随合并当真保存为统一出版断代。'], ['合并前逐字段保留22/30卷历史著录分歧、两版校勘责任；污染字段单独原目录核查/台账，不给Book机械并条。'], ['994bqhru9t','9945fxcw74','9950nh4740']),
('H-BROAD-00019','confirmed','天启东安六卷原志与残五卷为同一原作', ['S5'], ['9946simxa8著原六卷而馆藏注明存卷二至六；994pgde1vk残五卷挂安次县旧志合刊Collection，责任人为郑之城修、冯泰运纂。','独立东洋文库同一安次上下文明确天启五年原本、存卷2–6，并把康熙10卷和乾隆22卷列为另种，排除同名异地及不同修次误并。'], ['保留6卷原数和残存5卷分别作用域；1935/1936合刊年份与鄭之城/成字异需版本层核查，不能机械合Book。'], []),
('H-BROAD-00126','open','丁酉北闱七狱疑大狱讹字但南京原本未核', ['S6','S7'], ['同一信天翁权威URI、一卷及1911商务印书馆的独立藏品目录强烈支持七→大误录。','但独立1917台大本不是南京1911本；现有目录摘要未给七狱侧卷首、正文起讫或痛史分册位置。'], ['读南京图书馆38oqlna27qelkyz6对应卷首及1911出版牌记，与痛史第三种及正文首末核同；确认是源目录误录后方可改题并条。'], []),
('H-BROAD-00161','confirmed','丙湖是香艳丛书西湖游幸记子目误字', ['S8'], ['丙湖Book993xj9k2yo父8rldo8x3677k确指宣统国学扶轮社香艳丛书，西湖Book994b8q6q68亦明记香艳丛书本，作者周密、一卷一致。','独立实体馆藏编目PDF目验第26页，香艳十一集确著西湖游幸记，前后子目连续；这条母子位置证据比同题同作者摘要更强，丙/西形近误字可认定同一Work。'], ['未来合并保留丙湖源题及来源1wma8m8f8za6n50k作为误题台账；两Book源ID不同且edition/contained_in不同，不作机械并Book。'], []),
('H-BROAD-00203','open','二十四史日月考236卷与残存月日考须核总范围', ['S9'], ['当前日月考236卷来自清史稿艺文志；月日考两稿本有明确残存各史清单，并非完全没有卷数资料。','国图衍生目录A02187称存116卷，周书上卷；本库994cp88nb4馆藏notes作周书二卷。上图994cp7xerl覆盖宋辽金元，与国图残存范围不同，不能把残存卷数简单相加当作236。'], ['对读清史稿原著录及汪氏稿本总目、序跋，证明日月/月日题倒置与236卷原编范围；优先校周书上卷/二卷差异。若并条，处理已有related_works改指后的自边。'], ['994cp88nb4']),
('H-BROAD-00207','confirmed','于阗行程记/录有原目录明确异名校语', ['S10'], ['钱绎崇文总目辑释卷二地理类，在平居诲于阗国行程记一卷条下明确说明宋志记作录；前项敦煌新录、后项晋安海物异名记范围清楚。','这直接解释两Work分别来自崇文总目/国史经籍志与宋史艺文志的题名差异；不是因复制书目段落自动判同。'], ['未来保留记/录两题、各目录来源、资源和period依据；高居诲/平居诲人名版本问题另开人物审查，不在此案擅自更改作者实体。'], [])
]
cases=[]
common_gates=['未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。','执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。']
for n,(candidate,status,reason,src,evidence,gates,pollution) in enumerate(case_specs,1):
 c=bycand[candidate]['candidate'];members=[r for r in records if r['id'] in c['ids']]
 cases.append({'case_id':f'H-2000-{n:03}','candidate_id':candidate,'ids':c['ids'],'titles':c['titles'],'status':status,'decision_scope':'Work identity only','merge_eligible':False,'reason':reason,'evidence':evidence,'source_ids':src,'unresolved_gates':gates+common_gates,'pollution_book_ids':pollution,'discovery_candidate_ids':[candidate],'supersedes':None,'old_case_overlap':c['old_case_ids'],'member_snapshots':[{k:r[k] for k in ['id','path','blob_sha','sha256','snapshot']} for r in members]})
cases.append({'case_id':'H-2000-009','candidate_id':'new-context-expansion','ids':['d59fyqxfoagx','d59fynrbt7uq'],'titles':['[乾隆]重修福建臺灣府志','[乾隆]重修臺灣府志'],'status':'separate','decision_scope':'distinct gazetteer recensions','merge_eligible':False,'reason':'刘良璧二十卷与六十七/范咸二十五卷为前后修次，不能删福建/重修归一','evidence':['当前记录分别署刘良璧与六十七/范咸、20卷首1卷与25卷首1卷。','中研院提要明确范志参酌、增损高/刘前志；同一地区和乾隆年号不取消后修新编身份。'],'source_ids':['S2'],'unresolved_gates':['不建立merge-map；可另核前后修订关系，但不以related关系替代两条身份。'],'discovery_candidate_ids':[],'supersedes':None,'old_case_overlap':[],'member_snapshots':[{k:r[k] for k in ['id','path','blob_sha','sha256','snapshot']} for r in records if r['id'] in ['d59fyqxfoagx','d59fynrbt7uq']]})
# Cross-check only prior reviewed case ledgers, not broad retrieval pool.
overlaps=[]
for f in OUT.parent.rglob('cases.json'):
 if OUT in f.parents:continue
 try: text=f.read_text()
 except:continue
 hit=sorted(i for i in ids if i in text)
 if hit:overlaps.append({'path':str(f.relative_to(OUT.parent)),'member_ids':hit})
dump('cases.json',cases)
stats=json.loads((OUT.parent/'broad-20261022/stats.json').read_text())
validation={'base':BASE,'tree_sha256':manifest['tree_sha256'],'records_snapshotted':len(records),'work_records':sum(r['type']=='work' for r in records),'book_records':sum(r['type']=='book' for r in records),'collection_records':sum(r['type']=='collection' for r in records),'all_blob_sha_verified':True,'all_work_sha256_verified_against_db':True,'prior_reviewed_case_member_overlaps':overlaps,'discovery':{k:stats[k] for k in ['all_live_work_rows','history_union_work_rows','candidate_pairs','new_pairs','candidate_distinct_work_ids']},'review':{'groups':9,'distinct_work_members':len(ids),'confirmed':sum(c['status']=='confirmed' for c in cases),'separate':1,'open':sum(c['status']=='open' for c in cases)},'native_records_changed':0,'native_merges':0,'all_references_audited':False,'execution_checks_run':False,'formal_rule_blob_sha':'f899c5884844d7ddca9f68186d9e4a165ea7ff43'}
dump('validation.json',validation)
lines=['# 史部20:00新候选审查：9案，4确认、1分立、4待核','',f'固定main `{BASE}`。本轮只写本目录；原生合并0。读取当前正式库并条规则，Work身份确认与执行放行严格分开。未重跑H-C010/H-C082，未使用旧1876映射。','',f'继承宽扫发现覆盖{stats["history_union_work_rows"]:,}个史部联合范围Work、{stats["candidate_pairs"]:,}候选对（非判同数）；本轮人工审查9组、{len(ids)}个不同Work，新增宽扫候选8组，另从台湾同地同年号邻域补1组分立。前8组以discovery_candidate_ids记录H-BROAD发现来源；这些宽扫候选不是旧有效案件。本轮9案均为新审查案件，supersedes为null，不替代任何旧案。','',f'快照{len(records)}档（{validation["work_records"]} Work、{validation["book_records"]} Book、{validation["collection_records"]} Collection），原字节存snapshots/，Git blob与固定主树逐档相等；Work另与SQLite SHA256相等。旧归档Book/Collection只有字节匹配当前树才使用。当前记录及源instance指针见current-records.json。此为题名邻域，未声称全引用扫描。','', '## 本轮结论','', '| 案 | 状态 | 判断 |','|---|---|---|']
for c in cases:lines.append(f'| {c["case_id"]} | {c["status"]} | {c["reason"]} |')
for c in cases:
 lines+=['',f'## {c["case_id"]} — '+ ' / '.join(c['titles']),'', '成员：'+', '.join('`'+i+'`' for i in c['ids'])+'。', '',*c['evidence'],'','证据：'+', '.join('['+s['id']+']('+s['url']+')' for s in sources if s['id'] in c['source_ids'])+'。','', '仍需：'+'；'.join(c['unresolved_gates'])]
lines+=['','## 证据边界与交接','', '实际目验仅为町田市民文学馆目录PDF第26页，非古书正文书影；于阗案阅读的是古目录原文转录。上图原始在线instance打开不可用，LOC 403、安徽馆405与陕西馆超时均未伪称已阅原页。sources.json逐项区分完整页面、检索片段、转录及图像。目录摘抄本身只证明来源，不独自证明作品身份。','', '嘉定案三个出版字段污染和二十四史稿本周书卷数冲突均已落入cases.json；未做原生修复。执行门槛必须另行完成，尤其无损台账、related自边、Book差异、全部引用与草稿同步。', '', '旧人工cases的成员交叠检索结果：'+json.dumps(overlaps,ensure_ascii=False)+'。','', '可复核产物：cases.json、sources.json、current-records.json、validation.json、snapshots/与build_report.py。']
(OUT/'report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(validation,ensure_ascii=False,indent=2))
