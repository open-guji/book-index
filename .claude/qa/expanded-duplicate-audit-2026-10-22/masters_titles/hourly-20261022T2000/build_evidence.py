import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[4]
DB = pathlib.Path('/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite')
MAIN = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
con.row_factory = sqlite3.Row
manifest = json.loads(con.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base'] == MAIN

def save(name, obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

selected = json.loads((OUT.parent/'broad-20261022/selected-pairs.json').read_text())
pairs = json.loads((OUT.parent/'broad-20261022/candidate-pairs.json').read_text())
pair_lookup = {tuple(x['ids']):x for x in pairs}
raws = {}
def record(id):
    r = dict(con.execute('select * from records where id=?',(id,)).fetchone())
    raw = r.pop('data').encode()
    assert hashlib.sha256(raw).hexdigest() == r['sha256'], id
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == r['blob_sha'], id
    r['data'] = json.loads(raw)
    r['raw_utf8'] = raw.decode()
    raws[id] = r
    return r

common_gates = [
 '执行前在最新main重验全部原档SHA256，处理main漂移；本批固定main只作研究基线。',
 '全量扫描Work/Book/Collection/Entity/分类/promotions及book-text的入边与出边；当前SQLite只有活动Work、Entity及分类成员，不支持声称全引用闭包完成。',
 '逐字段出无损保留表，保留不同indexed_by全文、authors责任角色、资源组、contained_in、关系及独有ai_note/description；source_bid不是唯一来源记录键。',
 '确定keeper/losers后先出带前置SHA256的正式台账，再用可复现脚本改数据；同步草稿引用与promotions，仅改被并ID到keeper。',
 '完成T/L/P/R审计、D草稿后续PR、schema、分类、builder检查；本批均未运行正式合并后检查。'
]

specs = [
 (1,'confirmed','内外傷辨','d59fxzex6s5c',
  '两侧题名及三卷范围相同；第一责任者为同一李杲，上图person URI完全相同；两份原始author_info都明确金李杲撰。叢書子目自称来自叢書集成初編，独立一侧保存七种版本。子目authors写宋与其自己原著录相冲突，是归代字段问题，不是另一宋人同名著作。判同依据是题名、责任实体、朝代原文、卷数及子目层级的组合，并非source_bid或摘要相等。',
  ['将子目authors[0].dynasty=宋的冲突在台账显式记为原著录金，保留原值及更正依据；不按宋另立李杲。','逐个保留两侧版本/分类来源；若Book层发现摘录范围则单独处置，不由Work判同推导Book可并。'],['E-LI']),
 (2,'confirmed','儼山外纂','d59fxzsgg7wh',
  '同题、明陸深撰、一卷；两侧共享陸深person URI。子部版本明确为學海類編本，叢書侧父源明确學海類編四百三十種，构成具体载体回接；这是同一作品在子部与叢書子目重复建Work，不把學海類編整部与该一卷书合并。',
  ['保留两条indexed_by及子部/叢書分类来源；叢書父源6vdgzv8ybc7u7qgg与两条instance来源均须落到Book/Collection再改引用。'],[]),
 (6,'confirmed','武備輯要','d59fy5b4dhxc',
  '同题、清許學范撰、六卷及相同person URI；子部两版本之一明确敏果齋七種本，叢書侧父目明确敏果齋七種并记道光十二年广州刻。该版本与全书卷数相合，另抄本是作品的版本差异，不是另一著述。',
  ['保留子部抄本、敏果齋版本及叢書道光十二年来源三种著录信息；不能把抄本Book和刻本Book并为同版。'],[]),
 (11,'open','三元延壽參賛書／三元延壽參贊書',None,
  '内部两条均李鵬飛、元、五卷，賛/贊题字及輯/集角色差异本来支持同一作品。但d59f2gljz9c1所挂kokusho-100314944资源的IIIF指向京大RB00000599；实开京大馆方目录署曲直瀬道三(正慶)著、一册写本。不能将该异责任资源当作李鵬飛作品的佐证，也不能不解决而整包搬运。依外部标识冲突门槛，本轮保持open。',
  ['实开国书100314944并比较京大RB00000599题签、序跋、首末；确认是错挂、同题异书、改编或传抄责任差异。','逐项提出resources、resource_groups及IIIF挂接纠偏；原资源信息必须有可追溯去向，未审不得静默删除。','资源归属解决后再审两条李鵬飛五卷Work身份；不要将日本一册写本册数误当五卷的卷数矛盾。'],['E-KYOTO']),
 (12,'confirmed','三教平心論／靜齋學士三教平心論','d59f2ghlbt34',
  '两条内部独立目录著录均二卷，责任归元劉謐；长题目录保留劉謐靜齋學士三教平心論字串，短题有中國古籍總目二卷劉謐撰。CBETA官方检索命中卷下题三教平心論并署靜齋學士劉謐撰，说明靜齋學士属于责任称谓。旧分立理由静同劉字十是已记录的导入乱序，不可继续作为异作者证据。',
  ['短题description仍把静同劉字十当人名且说仅一志著录；保留原文于台账并另给可追溯更正，不能无损拼接污染为事实。','完整保留长题ai_note中的旧并入历史1evkaiy7xtp1c，核实其墓碑与promotions，不使用旧1876映射。','另有第三条d59f6ekv7h1c静齋學士三教平心論，已读全文作上下文，未计新增身份确认；执行前纳入闭包并单独裁决，避免只并两条又漏第三条。','CBETA实开仅返回前端框架；官方索引题署是辅助佐证，执行前最好留原页影像或可取的正文版本。'],['E-CBETA-SANJIAO']),
 (13,'confirmed','下陴紀談／下陴記談','d59f2ngxjv9f',
  '两侧均明皇甫錄、同一实体hixhd2h9bf7o、二卷。四庫總目提要明确该书为守顺庆时作并解释下陴题名；另一侧存目叢書及總目载嘉靖刻本。紀/記不改变这个特定作品识别；没有另一个作者或注疏层。四庫侧末附皇甫沖三峽山水記一卷必须保留为附书信息，不将父子责任混同。',
  ['核Book是否含三峽山水記附卷；不能把附书一卷并入主书二卷或把皇甫沖写成主书作者。','保留天一閣藏本与国图嘉靖本来源的差别，description中仅一志著录的旧断语须随合并重述并留原文。'],['E-XIAPI']),
 (15,'confirmed','駉思室答問','d59fxyeqa8lc',
  '同题一卷，子部成蓉鏡侧版本含南菁書院叢書；叢書侧父目正是南菁書院叢書，author_info明确清成孺（蓉鏡）撰。当前成孺实体hixhd2f8wain已列成蓉鏡别名且保留两侧上图URI；清史稿成孺传实开明确原名蓉镜，构成独立人物消歧证据。此案是两个Work重复，不需要重新合并已合人物。',
  ['保留成孺、成蓉鏡两个原始署名及各自person URI，统一指向当前hixhd2f8wain前核墓碑链。','父南菁書院叢書51ge66l3yznzczdc、成氏遺書本来源与Book容器关系另行保存。'],['E-CHENG']),
 (18,'open','天方字母解義一卷／三卷',None,
  '两侧同题同清劉智且person URI相同，但一侧一卷且无补者，另一侧三卷并明确馬德新（復初）補；后者structured authors漏补者。具体版本也分别为镇江/光绪十九年与同治二年/成都光绪十二年。不能从同首位责任者推导一卷原著与三卷补本完全同一；现证据尚不足判独立改编或同Work附补版本。',
  ['取得四条实例140yk1oxtwika6ch、ul7cldphm6sh1kxv、oue7783k55z5fw2k、cyr1ngpbl4tv05wg的题页、目录、序跋和补文起讫。','判明三卷为原著分卷、合刊补编还是再创作；保留馬德新补的责任，未定范围不批量改Book.work_id。'],[]),
 (19,'separate','七俱胝佛母所說准提陀羅尼經／會釋',None,
  '一卷原经为唐不空译；三卷會釋明确清弘贊会释且类别为章疏，书名含會釋。CBETA官方发布目录独立列X0446三卷、清弘贊会释，支持这是后出解释文本。原经与会释有著述层级差异，应分立关联，不是仅同一作品两个版本。',
  ['禁止本对合并；可另拟原经—会释关系，选择schema支持关系后再写。','会释Work当前dynasty=唐由第一译者传播而来，与会释成书时代不同；应另审责任层与断代，不因本次分立擅改。','其related_works目标d59fyjst1jwg不在本对判定中，不能外推其身份。'],['E-CBETA-HUISHI']),
 (20,'separate','三子通義／列子通義',None,
  '千頃堂書目原文把三子通義展开为老子二卷、莊子十卷、列子八卷，合二十卷；另一条列子通義八卷版本明确三子通義本。是整体与所含八卷子书，作者相同及题名包含不能构成重复。',
  ['禁止将二十卷整体与八卷子书合并；另审整体/子书关系及Book层contained_in表达。','三子通義资源自带存一种标题的扫描，应查实际所存子书，不将局部影像说明为二十卷齐备。'],[])
]

external = [
 {'id':'E-LI','url':'https://www.nmtcm.cn/stars_detail/271.html','access':'search_result_full_text','ref':'turn21search7','claim':'国家中医药博物馆：李杲为金元四大家，列内外伤辨惑论为其著作；仅用作人物时代与作品名的辅助背景。'},
 {'id':'E-KYOTO','url':'https://rmda.kulib.kyoto-u.ac.jp/item/rb00000599','access':'opened','ref':'turn16view0','locator':'lines 4, 18–28, 34–40','claim':'标题三元延寿参賛書；曲直瀬道三(正慶)著；一册，写 和大；サ/121，184968。是现挂IIIF目标的馆方目录责任冲突，不证明两个李鵬飛Work本身异书。'},
 {'id':'E-CBETA-SANJIAO','url':'https://cbetaonline.dila.edu.tw/T52n2117_002','access':'official_search_excerpt; open_shell_only','ref':'turn9search6 / turn16view1','locator':'T52n2117_p0787b03–04','claim':'官方搜索摘录题三教平心論卷下，署靜齋學士劉謐撰。直接打开仅前端框架，未声称实读全文。PDF导出打开为unsupported application/octet-stream。'},
 {'id':'E-XIAPI','url':'https://www.shidianguji.com/zh/book/NGJ892412000000450164048/chapter/1lqi6xainmayx','access':'search_excerpt_only; direct_open_failed','ref':'turn5search2 / turn9view0 / turn21view2','claim':'搜索摘录显示下陴記談卷首内题下陴紀談序、皇甫沖。实开失败，仅作待取影像线索，判同主证为固定main中四庫總目详细提要及存目叢書著录。'},
 {'id':'E-CHENG','url':'https://www.shidianguji.com/book/LS0025/chapter/1kt95ynvcw6cp','access':'opened','ref':'turn9view2','locator':'清史稿·成孺，line 7','claim':'成孺传明确原名蓉镜、字芙卿、宝应人，与当前实体姓名、籍贯相合。'},
 {'id':'E-CBETA-HUISHI','url':'https://cbetaonline.dila.edu.tw/doc/zh/07-29_2025-r1.php','access':'opened','ref':'turn21view1','locator':'line 136, X23n0446','claim':'官方目录独立列七俱胝佛母所說準提陀羅尼經會釋，三卷，清弘贊会释；用来复核著述层级。'},
 {'id':'E-SEARCH-BOUNDARY','url':None,'access':'not_adopted','claim':'天方补本相关查询未取得足以解决一卷/三卷关系的权威原典；Oxford成孺题录实开失败；不将搜索失败视为不存在，也不据站内镜像自证。'}
]

cases=[]
for k,(n,status,title,keeper,reason,gates,ext) in enumerate(specs,1):
    members=selected[n-1]
    candidate=pair_lookup[tuple(sorted(members))]
    assert not candidate['old_cases']
    rs=[record(id) for id in members]
    evidence=[]
    for r in rs:
        d=r['data']
        source_instances=[]
        for hit in re.findall(r'源記錄：([^\n]+)',d.get('ai_note','')):
            source_instances.extend(re.findall(r'\b[a-z0-9]{16}\b',hit))
        evidence.append({'id':r['id'],'pointer':f'original-records.json#/{r["id"]}/data','catalogue_entries':d.get('indexed_by',[]),'source_instance_urls':['https://data.library.sh.cn/gj/resource/instance/'+s for s in source_instances],'source_instance_access':'not_fetched; provenance from fixed-main ai_note','authors':d.get('authors',[])})
    cases.append({'case_id':f'MR-H2000-{k:03}','type':'Work','status':status,'title':title,'members':members,'keeper':keeper,'losers':[id for id in members if id!=keeper] if keeper else [],'direction_status':'proposal_only' if keeper else 'no_merge_direction','reason':reason,'base':MAIN,'broad_selected_pair_number':n,'candidate_signals':candidate['signals'],'prior_cases':candidate['old_cases'],'records':[{key:r[key] for key in ('id','path','blob_sha','sha256')} for r in rs],'evidence':evidence,'external_evidence_ids':ext,'unresolved_execution_gates':gates+(common_gates if keeper else []),'execution_ready':False,'actual_merges':0})

for id in ['d59f6ekv7h1c','hixhd2f8wain']:
    record(id)

rulepath='.claude/qa/正式库并条审查规则.md'
rule=subprocess.check_output(['git','show',MAIN+':'+rulepath],cwd=ROOT)
(OUT/'merge-rules-read.md').write_bytes(rule)
save('cases.json',cases)
save('original-records.json',raws)
save('external-evidence.json',external)
save('validation.json',{'base':MAIN,'database_manifest':manifest,'source':'read-only SQLite; original UTF-8 and hashes preserved; no old checkout input','original_records':len(raws),'primary_work_records':20,'context_work_records':1,'context_entity_records':1,'sha256_verified':len(raws),'git_blob_verified':len(raws),'rules':{'path':rulepath,'sha256':hashlib.sha256(rule).hexdigest()},'candidate_pairs_generated':25930,'new_candidate_pairs_generated':25878,'screened_selected_pairs':24,'new_pairs_reviewed':10,'cases_confirmed':6,'cases_separate':2,'cases_open':2,'actual_merges':0,'native_data_mutated':False,'book_collection_scan_done':False,'all_reference_scan_done':False,'merge_checks_run':False,'third_sanjiao_record':'context only; no added pair/count'})
print(json.dumps({'cases':len(cases),'confirmed':sum(x['status']=='confirmed' for x in cases),'records':len(raws),'output':str(OUT)},ensure_ascii=False))
