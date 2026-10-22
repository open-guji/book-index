import hashlib
import json
import pathlib
import re
import sqlite3

OUT = pathlib.Path(__file__).resolve().parent
AUDIT = OUT.parents[1]
MAIN = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DB = pathlib.Path('/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite')
con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
con.row_factory = sqlite3.Row
manifest = json.loads(con.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base'] == MAIN and not manifest['errors']

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

selected = json.loads((OUT.parent/'broad-20261022/selected-pairs.json').read_text())
pair_lookup = {tuple(x['ids']): x for x in json.loads((OUT.parent/'broad-20261022/candidate-pairs.json').read_text())}
raws = {}
def record(id):
    r = dict(con.execute('select * from records where id=?', (id,)).fetchone())
    raw = r.pop('data').encode()
    assert hashlib.sha256(raw).hexdigest() == r['sha256']
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == r['blob_sha']
    r.update(data=json.loads(raw), raw_utf8=raw.decode())
    raws[id] = r
    return r

common = [
    '执行前在最新main逐一重验原档SHA256与活动状态；本批是固定main研究快照，不是当前可直接执行台账。',
    '扫描正式Work/Book/Collection/Entity/分类/promotions、草稿及book-text全引用；当前SQLite不含Book/Collection及promotions全量，闭包尚未完成。',
    '逐字段制定无损保留表：indexed_by全文、原署名/责任角色、所有来源instance、ai_note/description及独有关系均保留；source_bid不得当作来源行唯一键。',
    'keeper为提案；正式执行前另出带原值、前置SHA256和可复现写入脚本的台账，保留墓碑/merged_in并同步草稿引用和promotions。',
    '写后运行T/L/P/R、D草稿检查、schema、check_v2、分类、官方索引及builder基线比较；本轮未运行数据合并检查。'
]
specs = [
    (23, 'confirmed', '䖷籛𤭏筆／䖷籛□筆', 'd59fxryzim80',
     '同明楊慎、同上图person URI；短缺字记录原title_info明确为䖷籛（⿰谷瓦）筆且ai_note说明□=⿰谷瓦，另一侧为𤭏，即该字的Unicode表达。子部一卷說郛本与叢書子目所屬說郛/說郛續相接。焦竑跋实开列楊慎著述䖷籛瓻筆；馆方题录搜索摘录列䖷籛𤭏筆一卷。判同基于缺字解码、责任与载体，不是把所有含□书名模糊合并。',
     ['保留原title=䖷籛□筆、原IDS题名和缺字注记；规范题名可用䖷籛𤭏筆，瓻筆只作原典异体线索，不未经审核自动扩散到全库。',
      '子目父源ap7cw3wh7xgzw0ph含說郛一百二十卷及說郛續四十六卷，执行前查其Book/Collection具体子卷位置；不得把叢書整部与一卷子书并条。',
      '子目未载卷数不得机械补Book卷数；一卷是Work身份依据及另一来源著录，仍保留子目卷数缺载事实。'],
     ['E-YANG-PREFACE','E-YANG-CATALOGUE','E-CHAR']),
    (10, 'confirmed', '陰陽管見', 'd59fxzsh2ozl',
     '两条同题、明何瑭撰、一卷、同person URI。子部载學海類編及百陵學山，叢書侧为曝書亭輯叢書子目。CiNii馆目实开分别证实何瑭《陰陽管見》的百陵學山影印本与學海類編第34冊载体。不存在新增注释者或增补范围的正面证据；依同题同责任同朝代规则确认Work重复，不由此推断三种载体同版。',
     ['保留學海類編、百陵學山、曝書亭輯叢書三种载体和各自馆藏，不能并其Book为同一刻本。',
      '曝書亭輯叢書父源jq88ndyxp1eolhfs及instance r12puwjcejqr7ask尚未实开；执行前核子目范围、保存容器关系，不与整部叢書合并。',
      'CiNii BB02338745书志责任原写何塘，规范作者入口为何瑭；此为外部目录局部异字，不引入新人物也不覆盖原始署名。'],
     ['E-YINYANG-BAILING','E-YINYANG-XUEHAI']),
    (22, 'separate', '三遂平妖傳二十回／墨憨齋批點北宋三遂平妖傳四十回', None,
     '前条孙楷第书目明确四卷二十回、王慎修本、题東原羅貫中編次，且封面馮猶龍先生增定系后来所加；后条總目明确四十回和馮夢龍增補。是二十回旧本与扩写改编四十回本的范围/责任区别，不是墨憨齋批點等题名修饰所能消除。识典实开新平妖傳序有旧刻/倍前的残损OCR语句，并题天許齋引首，不能冒称实读了嘉會堂原刻序。分立主证为两份固定main原始书目。',
     ['禁止本对合并；若建立原著—增补改编关系，先核schema及各自Book范围。',
      '四十回条structured authors漏馮夢龍增補，需另案逐源补责任，不将其降为单纯批点者。',
      '二十回条现挂维基文库三遂平妖傳资源必须核回数，资源无条件保留或转移均未获核实；本轮不判其正文范围。',
      '另有二十回同题d59fxs7l61oh（Broad第16对），不在本对计数或裁决；后续可单独核与罗贯中原本身份。'],
     ['E-PINGYAO-PREFACE']),
    (14, 'open', '不空罥索神變真言經／不空羂索神變真言經', None,
     '同题异体、两份原始title_info均三十卷且author_info同唐菩提流志，支持核心经本相同。但羂字长记录authors另外混入唐地婆訶羅、南北朝菩提留支/流支，ai_note又留功德施菩薩造、天親菩薩造两项异常责任。其15实例汇聚可能含错题、合册或责任聚合污染，不能以首位译者相同直接整包并入。CBETA《續古今譯經圖紀》官方摘录列唐菩提流志所译本三十卷，尚不能解释长记录的所有实例。故保持open而非认定异体题字导致异书。',
     ['逐个实开短记录2实例和长记录15实例，取得题页/卷首/卷末与合册目录，建立instance→具体作品→责任映射。',
      '核唐菩提流志与南北朝菩提流支的现行Entity及墓碑，保留URI与原值，不能为并Work顺手合并跨时代译者。',
      '查地婆訶羅、功德施、天親责任对应何书及所在合册；责任去向未明前不删除、不整包搬运。',
      '核心三十卷同一判断与全部来源可并分开记录；来源净化后再决定拆分或Work合并，保持不同译本/注释/合册边界。'],
     ['E-CBETA-BODHIRUCI'])
]

external = [
 {'id':'E-YANG-PREFACE','url':'https://www.shidianguji.com/zh/book/7556499731703136306/chapter/1lgle66bjzndm','ref':'turn5view1','access':'opened_transcribed_primary_text','locator':'焦竑跋，lines 7,11','observation':'萬曆丁巳焦竑跋列楊慎著述，末列䖷籛瓻筆。','limits':'实开转录文本，未看影像；瓻与𤭏字形关系不能只靠此一条证明。'},
 {'id':'E-YANG-CATALOGUE','url':'https://omnia.college-de-france.fr/discovery/fulldisplay/alma990003459400107166/33CDF_INST%3A33CDF_INST','ref':'turn5search2 / turn9view0','access':'official_catalogue_search_excerpt; direct_open_failed','observation':'法兰西学院馆目题䖷籛𤭏筆一卷，署明楊慎撰。','limits':'仅官方搜索摘录，不声称实读目录全文或原书。'},
 {'id':'E-CHAR','url':'https://www.chise.org/est/view/character/%F0%A4%AD%8F','ref':'turn15search8 / turn20view0','access':'character_database_search_excerpt; direct_open_failed','observation':'CHISE字结构字段：𤭏为⿰谷瓦；与固定main的缺字注记完全对应。','limits':'只用于缺字编码解读，非作品身份独立主证。'},
 {'id':'E-YINYANG-BAILING','url':'https://ci.nii.ac.jp/ncid/BA55200501','ref':'turn5view0','access':'opened_official_union_catalogue','locator':'lines 108–126','observation':'陰陽管見、何瑭撰；百部叢書集成中的百陵學山，藝文印書館1967。','limits':'具体1967影印版本目录；不等同于本批所有Book。'},
 {'id':'E-YINYANG-XUEHAI','url':'https://ci.nii.ac.jp/ncid/BB02338745','ref':'turn15view2','access':'opened_official_union_catalogue','locator':'lines 158–164,174–190','observation':'學海類編第34冊列陰陽管見，何塘著；作者入口何瑭，六安晁氏，道光11跋；东大东洋文化所藏。','limits':'合册目录，不把同册其他书或其作者都归入陰陽管見。'},
 {'id':'E-PINGYAO-PREFACE','url':'https://www.shidianguji.com/zh/book/CADAL02000633/chapter/1llwtnd07gjzz','ref':'turn15view0','access':'opened_transcribed_primary_text_with_OCR_damage','locator':'lines 8–14','observation':'新平妖傳序文本提及武林旧刻及倍前；引首题天許齋批點北宋三遂平妖傳，署羅貫中編/張無咎校。','limits':'序OCR明显缺损，非本案嘉會堂本影像，不据其残句恢复确切二十/四十回数；本对范围数取固定main两条原始书目。'},
 {'id':'E-CBETA-BODHIRUCI','url':'https://cbetaonline.dila.edu.tw/T2152','ref':'turn15search7 / turn20view1','access':'official_primary_text_search_excerpt; direct_open_frontend_only','locator':'T55n2152_p0371c16','observation':'續古今譯經圖紀菩提流志传列不空羂索神變真言經一部三十卷。','limits':'直接打开仅前端框架；仅支持标准译本名/责任/卷数，不解决17条上图实例聚合污染。'},
 {'id':'E-CBETA-COLLOPHON','url':'https://cbetaonline.dila.edu.tw/T1092_030','ref':'turn15search2','access':'official_primary_text_search_excerpt','locator':'T20n1092_p0393a19–20','observation':'卷第三十题署唐天竺三藏菩提流志译。','limits':'辅助线索，未声称实读全文或影像。'}
]

cases=[]
duplicate_scan=[]
for k,(n,status,title,keeper,reason,gates,ext) in enumerate(specs,1):
    ids=selected[n-1]
    cand=pair_lookup[tuple(sorted(ids))]
    assert not cand['old_cases']
    prior_hits=[]
    for path in AUDIT.rglob('cases.json'):
        if OUT in path.parents:
            continue
        if all(id in path.read_text() for id in ids):
            prior_hits.append(str(path.relative_to(AUDIT)))
    assert not prior_hits, (ids,prior_hits)
    duplicate_scan.append({'pair':ids,'broad_old_cases':cand['old_cases'],'prior_cases_files_with_both_ids':prior_hits})
    rs=[record(id) for id in ids]
    evidence=[]
    for r in rs:
        d=r['data']
        instances=[]
        for line in re.findall(r'源記錄：([^\n]+)',d.get('ai_note','')):
            instances.extend(re.findall(r'\b[a-z0-9]{16}\b',line))
        evidence.append({'id':r['id'],'original_pointer':f'original-records.json#/{r["id"]}/data','title_pointer':f'original-records.json#/{r["id"]}/data/title','catalogue_pointer':f'original-records.json#/{r["id"]}/data/indexed_by','catalogue_entries':d.get('indexed_by',[]),'authors':d.get('authors',[]),'source_instance_urls':['https://data.library.sh.cn/gj/resource/instance/'+x for x in instances],'source_instance_access':'not_fetched; fixed-main ai_note provenance'})
    cases.append({'case_id':f'MR-2022-{k:03}','type':'Work','status':status,'title':title,'members':ids,'keeper':keeper,'losers':[x for x in ids if x!=keeper] if keeper else [],'direction_status':'proposal_only' if keeper else 'no_merge_direction','reason':reason,'base':MAIN,'broad_selected_pair_number':n,'candidate_signals':cand['signals'],'prior_cases':[],'supersedes':[],'records':[{key:r[key] for key in ('id','path','blob_sha','sha256')} for r in rs],'evidence':evidence,'external_evidence_ids':ext,'unresolved_execution_gates':gates+common,'execution_ready':False,'actual_merges':0})

save('cases.json',cases)
save('original-records.json',raws)
save('source-evidence.json',external)
save('new-pair-validation.json',duplicate_scan)
rule=OUT.parent/'hourly-20261022T2000/merge-rules-read.md'
save('validation.json',{'base':MAIN,'database':str(DB),'database_manifest':manifest,'provenance_limit':'SQLite fixed-main manifest inherited; this batch verifies saved raw UTF-8 against both stored hashes, not an independent whole-tree git fetch.','original_records':len(raws),'sha256_verified':len(raws),'git_blob_verified':len(raws),'new_pairs_reviewed':len(cases),'cases_confirmed':2,'cases_separate':1,'cases_open':1,'superseded_cases':0,'actual_merges':0,'native_data_mutated':False,'git_mutations':False,'writes_confined_to':str(OUT),'rules_read':str(rule),'rules_sha256':hashlib.sha256(rule.read_bytes()).hexdigest(),'all_reference_scan_done':False,'book_collection_scan_done':False,'merge_checks_run':False,'protected_cases':'BOOK-0010 defer; JC-001/JC-007 hold; old1876 map prohibited; PR1216/Feng audit untouched'})
manifest_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-manifest.json'}
save('artifact-manifest.json',manifest_files)
print(json.dumps({'cases':len(cases),'confirmed':2,'separate':1,'open':1,'original_records':len(raws),'path':str(OUT)},ensure_ascii=False))
