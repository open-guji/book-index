"""Bounded read-only history research; only writes this script's directory."""
import hashlib,json,sqlite3,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
AUDIT=OUT.parents[1]
REPO=OUT.parents[4]
ROOT=Path('/workspace/scratch/0bc7226fa660')
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
def dump(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def blob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
db=sqlite3.connect(f'file:{ROOT}/audit/broad-current.sqlite?mode=ro',uri=True)
db.row_factory=sqlite3.Row
manifest=json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base']==BASE
treebytes=(ROOT/'audit/current-main-tree.z').read_bytes()
assert hashlib.sha256(treebytes).hexdigest()==manifest['tree_sha256']
tree={}
for item in treebytes.split(b'\0'):
 if item:
  h,p=item.decode().split('\t');tree[p]=h.split()[2]
specs=[
 {'case_id':'H-2022-001','candidate_id':'H-BROAD-00123','ids':['d59f27scdgjm','d59f27suh81u'],'status':'confirmed','reason':'㑹/會只是题名异体；两条均为谢承七卷原作的目录身份','source_ids':['S1'],'evidence':['固定main两条同署三国吴谢承、同一Entity，均以七卷为原书卷数。异体题只载国史经籍志；常体题兼载隋唐目录。','已打开隋书卷33杂传原文转录，明确七卷谢承，并与钟离岫会稽后贤传记二卷、会稽先贤像赞五卷分列，排除邻题误并。'],'preserve':['两种原题、国史经籍志独有著录与来源、旧唐书五卷异数必须并存；七卷为原书，后世一卷辑本不得覆盖原卷数。','d59f27suh81u已有merged_in 1evcs0f6qxj40和related_works→d59fycrzr7y8；全部历史和出边保留。'],'gates':['d59fycrzr7y8明确清黄奭辑的一卷汉学堂知足斋本，本案不纳入；不得因原作身份确认自动吞并辑本。','d59f27suh81u indexed_by[2].summary尾部夹入徐整豫章列士传；单独台账清理串条，不传播为谢承著述。'],'context_ids':['d59fycrzr7y8'],'keeper_proposal':'d59f27suh81u'},
 {'case_id':'H-2022-002','candidate_id':'H-BROAD-00136','ids':['d59f2hj7qi2r','d59f2hrhiwap'],'status':'confirmed','reason':'三朝北盟集編是徐梦莘自序题，與會編指同一二百五十卷书','source_ids':['S2','S3'],'evidence':['固定main两条同署徐梦莘、同Entity、250卷，集编条来自国史经籍志。','国图明抄本卷首转录题三朝北盟集编序，并题三朝北盟集编书目；序述上中下三帙、250卷。国史经籍志卷三另列集补50卷，不能把集编误当续编。'],'preserve':['保留集編题名及国史经籍志著录；會編条全部资源组、馆藏链接及已合并历史保留。','序文转录的绍兴三十二年/四十六年，与库内四库提要的三十一年/四十五年有差别；不替换为统一断年，保留各源原话待书影核字。'],'gates':['不纳入北盟集补50卷；本轮未逐册检验會編条资源或Book。','识典卷首转录有明显OCR断句、误字；确认依序题与250卷结构，不采用自动转录每一字作精校。'],'context_ids':[],'keeper_proposal':'d59f2hrhiwap'},
 {'case_id':'H-2022-003','candidate_id':'H-BROAD-00144','ids':['d59f2moxmh34','d59f2nc7qnls'],'status':'confirmed','reason':'三藩/三籓紀事本末为杨陆荣四卷原作异体题','source_ids':['S4','S5'],'evidence':['两条同署清杨陆荣、同Entity，均四卷；籓字条独载清史稿艺文志。','中研院提要明确杨陆荣、康熙五十六年成书，记南明福唐桂三王，四卷共22篇；其分卷篇目与本库四库提要相接，不能误解为吴三桂三藩之乱另一书。'],'preserve':['保留三籓源题及清史稿著录；四库存目、书目答问、存目丛书的四卷来源分别保留。','中国古籍总目著录title_info作二十二卷且摘要共22版本，与四卷原作冲突；不能把22篇/22版本自动转成22卷。'],'gates':['逐查d59f2moxmh34 indexed_by[3]对应总目原文和全部Book范围，排除丛编父子串接；本轮仅证明四卷原作身份，未证明22卷聚合来源可直接合入。','当前四库summary写康王，而中研院和卷目为唐王；此为独立字误风险，保留原值后核原书，不顺手覆盖。'],'context_ids':[],'keeper_proposal':'d59f2moxmh34'},
 {'case_id':'H-2022-004','candidate_id':'H-BROAD-00212','ids':['d59f2hs822gx','d59f2huxrchs'],'status':'open','reason':'题名省记可解释，但宋原书与四库重辑本的作品范围须先定','source_ids':['S6'],'evidence':['固定main纂误条引宋史三卷、直斋五卷；史记纂误条主要依据永乐大典辑本，作者同署吴缜。','四库提要明确原书久佚，辑得112事，相对晁公武所记200余事仅存五六成，又加薛史异同附识；卷数相近不证明原貌、重辑和附识层完全相同。','提要同时讨论刘羲仲作者异说并判不足据；这一异说应保留来源层，不另造吴缜/刘羲仲人物合并。'],'preserve':['保留宋史3卷、直斋5卷、重辑3卷及112事各自作用域；保留原作者异说、四库辑佚与附识责任。','related_works→d59f20aowb9c目前是司马迁史记，不能仅因标题含史记而当作五代史底本。'],'gates':['核宋原本/四库辑本身份模型、目录及首末，明确是否原作的一种版本或需独立辑佚Work，再定keeper。','d59f2huxrchs /related_works/0 的 contains_text_of→司马迁史记须单独核实，不能机械迁移为可信关系。','纂误条related→d59fyptzppfl是无名氏五代史纂不分卷明抄本，缺誤字也不能纳入本案；须独立看原件。'],'context_ids':['d59f20aowb9c','d59fyptzppfl'],'keeper_proposal':None}
]
sources=[
 {'id':'S1','url':'https://zh.wikisource.org/wiki/隋書/卷33','ref':'turn33view0','access':'opened primary historical catalogue transcription; no image inspection','pointer':'卷33 雜傳, lines1009–1017','finding':'謝承會稽先賢傳七卷，與後賢傳記二卷及先賢像贊五卷分列。'},
 {'id':'S2','url':'https://www.shidianguji.com/zh/book/NGJ892412000000049154883/chapter/1lvroqroh4wtv','ref':'turn17view0','access':'opened manuscript-derived transcription, visible OCR errors; no image inspection','pointer':'國圖412000000049/湖東精舍明抄本 卷首; lines6–17','finding':'自序及書目題集編；三帙250卷，題署徐夢莘。'},
 {'id':'S3','url':'https://www.shidianguji.com/zh/book/CADAL02091118/chapter/1lcq2me5aorop','ref':'turn21view0','access':'opened primary catalogue transcription; no image inspection','pointer':'國史經籍志卷三 lines314–316','finding':'三朝北盟集編250卷，緊接集補50卷為獨立子目。北字OCR異常，不據此改字。'},
 {'id':'S4','url':'https://taicool.ith.sinica.edu.tw/browse-ebook.html?id=EB0000000149','ref':'turn11view1','access':'opened holding institution catalogue full summary','pointer':'提要 line37','finding':'楊陸榮四卷22篇，康熙56年成書，逐卷篇目及南明三王範圍。'},
 {'id':'S5','url':'https://www.guoxue.com/shibu/24shi/qingshigao/qsg_146.htm','ref':'turn11search4','access':'search-index excerpt of primary historical catalogue only; direct open timed out','pointer':'清史稿卷146 藝文二紀事本末類','finding':'三籓紀事本末四卷，楊陸榮撰；與當前清史稿著錄相符。不能聲稱已閱完整網頁或原書影像。'},
 {'id':'S6','url':'https://zh.wikisource.org/zh-hant/四庫全書總目提要/卷046','ref':'turn25view3','access':'opened primary catalogue transcription; no image inspection','pointer':'lines182–185, 五代史記纂誤三卷永樂大典本條','finding':'吳縝/劉羲仲異說；三五卷異數；原書已佚，重輯112事對200餘事，另加薛史附識。'}
]
dump('sources.json',sources)
selected_ids={i for s in specs for i in s['ids']}
all_ids=selected_ids|{i for s in specs for i in s['context_ids']}
for i in selected_ids:
 d=json.loads(db.execute('select data from records where id=?',(i,)).fetchone()[0])
 all_ids.update(a['entity_id'] for a in d.get('authors',[]) if a.get('entity_id'))
records=[];(OUT/'snapshots').mkdir(exist_ok=True)
for i in sorted(all_ids):
 r=dict(db.execute('select * from records where id=?',(i,)).fetchone());b=r['data'].encode()
 assert r['blob_sha']==tree[r['path']]==blob(b),i
 assert r['sha256']==hashlib.sha256(b).hexdigest(),i
 d=json.loads(b);assert not d.get('merged_into'),i
 (OUT/'snapshots'/f'{i}.json').write_bytes(b)
 records.append({'id':i,'type':d['type'],'path':r['path'],'blob_sha':r['blob_sha'],'sha256':r['sha256'],'snapshot':f'snapshots/{i}.json','role':'case_member' if i in selected_ids else 'context_only','data':d})
dump('current-records.json',records)
byid={r['id']:r for r in records}
overlaps=[]
for p in AUDIT.rglob('cases.json'):
 if OUT in p.parents or 'broad' in str(p.relative_to(AUDIT)):continue
 text=p.read_text();hits=sorted(i for i in selected_ids if i in text)
 if hits:overlaps.append({'path':str(p.relative_to(AUDIT)),'ids':hits})
assert not overlaps,overlaps
candidates=json.loads((OUT.parent/'broad-20261022/candidate-pairs.json').read_text())
chosen=[c for c in candidates if c['candidate_id'] in {s['candidate_id'] for s in specs}]
assert len(chosen)==4
dump('discovery-candidates.json',chosen)
common=['执行前重新fetch main并校验原字节；制作keeper/losers逐字段无损台账及全部源值历史。','未扫描全库引用、分类成员、promotions、草稿及book-text；须另做全引用审计后跑T/L/P/R、schema、check_v2、classification和derived基线比较。','确认只涉及Work身份，不授权机械并Book或人物；本轮无原生修改。']
cases=[]
for s in specs:
 c=dict(s);c['titles']=[byid[i]['data']['title'] for i in c['ids']]
 c.update({'decision_scope':'original Work identity only' if c['status']=='confirmed' else 'original vs reconstructed work scope unresolved','merge_eligible':False,'supersedes':None,'old_case_overlap':[],'discovery_candidate_ids':[c['candidate_id']],'unresolved_gates':c.pop('gates')+common,'preservation_requirements':c.pop('preserve'),'member_snapshots':[{k:byid[i][k] for k in ['id','path','blob_sha','sha256','snapshot']} for i in c['ids']]})
 c['source_urls']=[x['url'] for x in sources if x['id'] in c['source_ids']]
 c['field_pointers']={i:['/'+k for k in ['title','authors','indexed_by','juan_count','description','ai_note','related_works','merged_in','resources','resource_groups'] if k in byid[i]['data']] for i in c['ids']}
 cases.append(c)
dump('cases.json',cases)
rule_path='.claude/qa/正式库并条审查规则.md'
rule=(AUDIT/'people_names_aliases/hourly-20261022T2000/merge-rules.snapshot.md').read_bytes()
assert blob(rule)==tree[rule_path]
(OUT/'evidence/merge-rules.snapshot.md').write_bytes(rule)
validation={'base':BASE,'census_sqlite':'/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite','tree_sha256':manifest['tree_sha256'],'work_records_reviewed':8,'context_work_records':3,'author_entity_records':4,'snapshots':len(records),'all_snapshot_blobs_equal_fixed_main_tree':True,'all_snapshot_sha256_equal_readonly_census':True,'prior_case_ledgers_checked':'all audit subtree cases.json, excluding this directory and broad discovery pools; raw member-ID overlap test','prior_case_member_overlaps':overlaps,'review':{'groups':4,'new_pairs':4,'distinct_work_members':8,'confirmed':3,'separate':0,'open':1},'broad_pool_rescanned':False,'actual_scope':'four selected broad pairs, three explicit related Work targets and four author Entities; no Book, Collection or all-reference audit','book_records_reviewed':0,'image_pages_inspected':0,'formal_rule_path':rule_path,'formal_rule_blob_sha':blob(rule),'native_records_changed':0,'native_merges':0,'all_references_audited':False,'execution_checks_run':False}
assert len(records)==15
dump('validation.json',validation)
lines=['# 史部20:22新案：4组，3确认、1待核','',f'固定main `{BASE}`。本轮仅写本目录；原生合并0。全部为新案，supersedes=null；跨六路既有cases.json成员ID检索无交叠。宽扫候选不是既有人工案件，也不计作确认。','', '实际复核8个Work成员，另读3个related目标Work、4个作者Entity；15份原字节快照全部与固定main树Git blob及只读census SHA256一致。没有Book/Collection全扫，没有书影目验，没有全引用或执行检查。','', '| 案 | 状态 | 结论 |','|---|---|---|']
for c in cases:lines.append(f'| {c["case_id"]} | {c["status"]} | {c["reason"]} |')
for c in cases:
 lines+=['',f'## {c["case_id"]} — '+ ' / '.join(c['titles']),'','成员：'+', '.join('`'+i+'`' for i in c['ids'])+'。','',*c['evidence'],'','保留要求：'+ '；'.join(c['preservation_requirements']),'','执行门槛：'+'；'.join(c['unresolved_gates']),'','来源：'+', '.join('['+s['id']+']('+s['url']+')' for s in sources if s['id'] in c['source_ids'])+'。']
lines+=['','## 边界与后续','', '五代史案保持open，并非因同作者自动合并。前三案也不是可执行merge-map；keeper_proposal仅供后续台账设计。会稽黄奭一卷辑本、北盟集补50卷均明确排除。三藩22卷字段和五代史错误关系均须先核，未原生修复。','', 'S1/S2/S3/S6为原书或古目录转录，非书影校读；S4为中研院馆目完整提要；S5仅检索片段且直开超时。全部工具返回存evidence/web-retrievals.json，不能将搜索片段说成实物目验。未使用旧1876映射，未触动BOOK-0010、#1216四人或冯氏专案。','', '可复核：cases.json、sources.json、current-records.json、discovery-candidates.json、validation.json、snapshots/、evidence/、build_report.py。']
(OUT/'report.md').write_text('\n'.join(lines)+'\n')
files=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name!='artifact-manifest.json':files.append({'path':str(p.relative_to(OUT)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
dump('artifact-manifest.json',{'base':BASE,'files':files})
print(json.dumps(validation,ensure_ascii=False,indent=2))
