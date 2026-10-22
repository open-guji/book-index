"""Bounded research checkpoint; no production writes or merge application."""
import gzip, hashlib, json, subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
LANE = OUT.parent
MAIN = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
ROOT = OUT.parents[4]
TREE = Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z')
paths = [
    'Work/z/p/c/d59f2q4d1zpc-謝萬注.json',
    'Work/b/0/g/d59f27y99b0g-集解孝經謝萬注.json',
    'Work/6/b/l/d59f2mr6s6bl-春秋左氏傳補注.json',
    'Work/y/y/p/d59f2n9s0yyp-春秋左傳補注.json',
    'Work/l/8/i/d59f2j58ml8i-春秋左氏傳補注.json',
]
tree = {}
for row in TREE.read_bytes().split(b'\0'):
    if b'\t' in row:
        info, path = row.split(b'\t', 1)
        tree[path.decode()] = info.decode().split()[2]
old = json.load(gzip.open(LANE/'astra-review-20261022/main-records.json.gz', 'rt'))
records, validation = {}, []
for path in paths:
    oid = tree[path]
    raw = subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)
    actual_oid = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    sha = hashlib.sha256(raw).hexdigest()
    assert oid == actual_oid
    if path in old:
        assert old[path]['blob'] == oid and old[path]['sha256'] == sha
    records[path] = {'blob': oid, 'sha256': sha, 'record': json.loads(raw)}
    validation.append({'path': path, 'main_tree_blob': oid, 'computed_git_blob': actual_oid,
                       'sha256': sha, 'historical_sha256_match': path in old,
                       'read_method': 'git cat-file blob by fixed-main tree OID'})
with gzip.open(OUT/'main-records.json.gz', 'wt', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
def dump(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
dump('validation.json', {'main_sha': MAIN, 'scope': 'Five named Work blobs only; no full reference or book-text scan',
                         'verified_count': len(validation), 'records': validation, 'production_mutations': 0})
refs = [
 {'id':'E1','url':'https://zh.wikisource.org/zh-hant/新唐書/卷057','title':'新唐書卷57・藝文志・孝經類',
  'locator':'孝經王肅注一卷以下，蘇林與虞盤佐之間；web lines 1074–1095',
  'excerpt':'謝萬注一卷','finding':'謝萬是注者，書題承接孝經；原庫把人名與責任詞當題名且留空authors。',
  'evidence_kind':'古代原典網頁轉錄；非影像','web_ref':'turn16view0'},
 {'id':'E2','url':'https://zh.wikisource.org/zh-hant/隋書/卷32','title':'隋書卷32・經籍志・孝經類',
  'locator':'徐整孝經默注之後、荀昶集議孝經之前；web line 1038',
  'excerpt':'《集解孝經》一卷謝萬集。','finding':'明記謝萬一卷集解；可與唐志孝經一卷互證，並與keeper indexed_by及考證所述對照。',
  'evidence_kind':'古代原典網頁轉錄；非影像','web_ref':'turn22view0'},
 {'id':'E3','url':'https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷223','title':'經義考卷223',
  'locator':'孝經二，徐氏整之後；web lines 125–127',
  'excerpt':'謝氏〈萬〉集解孝經','finding':'獨立章節定位支持集解孝經題名與謝萬；下列隋志一卷、佚。此轉錄本身不是獨立於隋志的新古代證詞。',
  'evidence_kind':'古代原典網頁轉錄；非影像','web_ref':'turn18view1'},
 {'id':'E4','url':'https://zh.wikisource.org/w/index.php?title=經義考_(四庫全書本)/卷198&oldid=614359','title':'經義考卷198（固定修訂614359）',
  'locator':'卷首趙氏汸春秋集傳；春秋屬辭之後補注條；春秋師說之後金居敬總序',
  'excerpt':'春秋左氏傳補注／十卷／存／汸自序曰',
  'finding':'補注條仍屬趙汸連續著錄，下一題春秋師說，金居敬總序再將趙氏集傳、屬辭、左氏傳補注十卷、師說聯列。',
  'evidence_kind':'古代原典網頁轉錄；非影像','web_ref':'turn3view2'},
 {'id':'E5','url':'https://www.shidianguji.com/book/NA02439/chapter/1m8m1du4j1kb7','title':'識典古籍《經義考》卷198',
  'locator':'web lines 64–84及97–98',
  'excerpt':'春秋左氏传补注／十卷／存',
  'finding':'另一轉錄亦保存補注十卷及汸自序的節界；OCR有訪、汝及補法等誤字，不用來校字或冒充影像核驗。',
  'evidence_kind':'原典OCR轉錄；非獨立古代證詞、非影像','web_ref':'turn2view3'},
]
for r in refs: r['accessed_at'] = '2026-10-22'
dump('references.json', refs)
byid = {v['record']['id']: (p,v) for p,v in records.items()}
def common(cid, oldid, status, members):
    return {'case_id':cid,'supersedes_case_id':oldid,'status':status,'prior_status':'open',
            'type':'Work','main_sha':MAIN,'members':members,
            'paths':{i:byid[i][0] for i in members},'sha256':{i:byid[i][1]['sha256'] for i in members},
            'applied':False,'execution_ready':False,'machine_merge_mapping':None}
x = common('JC-1900-XIAOJING','JC-OPEN-d59f2q4d1zpc','confirmed',['d59f2q4d1zpc','d59f27y99b0g'])
x.update({'label':'謝萬注一卷為謝萬集解孝經的省題重出',
 'identity_decision':'新確認一案。d59f2q4d1zpc的謝萬注不是無撰人的書名；唐志孝經類連列省去重複書題。與d59f27y99b0g為同一謝萬孝經注解著作。',
 'evidence_refs':['E1','E2','E3'],
 'repository_corroboration':[
  {'id':'d59f27y99b0g','field':'indexed_by[2]','finding':'丁國鈞補晉書藝文志直接說兩唐志作謝萬注。'},
  {'id':'d59f27y99b0g','field':'emendated_by[0]','finding':'隋書經籍志考證明列日本見在書目孝經一卷謝萬集解、兩唐志謝萬注一卷，並保留馬國翰輯四節及附謝安一節的範圍。'}],
 'proposed_keeper':'d59f27y99b0g','proposed_losers':['d59f2q4d1zpc'],
 'excluded_ids':['d59f27yzh8n5','d59f27xwgkqp','d59f27xu9wxu','d59f9s18wrup'],
 'exclusion_reason':'JC-001是同作者周易繫辭二卷；經類與被注原典不同，明確不納入。本案不另加一個分立案數。',
 'field_repair_proposal':[
  'keeper保留既有隋志、清史稿、五項indexed_by、emendated_by、馬國翰輯本及謝安附錄範圍、related_works出邊；不以新唐書省題覆蓋作品主題名。',
  '將loser新唐書indexed_by整項加入keeper，source_bid和原summary不變；其authors=[]及ai_note的已考無撰人判語作原值寫入台賬，標註被外部完整孝經類上下文推翻，禁止當作權威結論並入keeper。',
  'authors角色撰／集／注不強制相互覆蓋；保留來源角色及entity_id，校正主角色另述依據。period_upper及其basis須列原值，已有晉代判定不可無記錄覆蓋。'],
 'execution_holds':['尚未完成正式庫全部型別化引用、promotions、草稿同步及book-text內容引用全掃。',
  'keeper已有輯佚檔線索，雖本案proposed loser未見文本欄位，不能據此宣稱跨庫文本資產檢查完成。',
  '本輪只有身份研究及字段保留策略，未生成正式無損合併台賬、未執行schema／classification／builder。'],
 'counting':{'new_confirmed':1,'new_separate':0,'open_delta':-1,'applied_merges':0}})
h = common('JC-1900-H005','JC-ASTRA-H005','open',['d59f2mr6s6bl','d59f2n9s0yyp','d59f2j58ml8i'])
polluted = byid['d59f2mr6s6bl'][1]['record']
h.update({'label':'沈欽韓左傳補注：趙汸經義考節界外部核定，修復仍待實施',
 'identity_decision':'維持待核整案；趙汸十卷條明確排除沈欽韓十二卷擬並範圍。',
 'evidence_refs':['E4','E5'],
 'advance_this_round':'從庫內自序文義推測前進到外部原典整卷的連續節界及金居敬總序交叉印證；已可精確指定indexed_by[1]整項為錯掛，不再僅依汸字或卷數衝突判定。',
 'pollution_archive':{'source_record_id':'d59f2mr6s6bl','indexed_by_entry':polluted['indexed_by'][1],
                      'description':polluted['description'],'ai_note':polluted['ai_note']},
 'repair_proposal':[
  '錯掛indexed_by[1]完整原值、原錯誤掛接note與衍生description已封存於本案pollution_archive；未從原生資料刪除。',
  '趙汸d59f2j58ml8i目前indexed_by未含此經義考卷198條；候選修復將該節掛回趙汸，但先核原影像KR2n0011_WYG_198-17b及續頁以滿足前輪原頁門檻。',
  '沈氏description去掉別作十卷、經義考為其目所本的污染敘述；保留續修四庫十二卷國圖稿本的獨立證據。',
  '其餘Book、resources未經本輪影像核定；沿用前輪25個已知Book矩陣作線索而非聲稱全本已驗。污染修復與沈氏兩條身份確認、引用改寫應分步台賬化。'],
 'execution_holds':['本輪讀到兩份原典轉錄，沒有看原刻影像；不宣稱原頁門檻解除。',
  '全量引用、草稿promotions及book-text、字段無損台賬尚未完成。'],
 'counting':{'new_confirmed':0,'new_separate':0,'open_delta':0,'applied_merges':0}})
dump('cases.json',[x,h])
print(json.dumps({'cases':2,'new_confirmed':1,'open_delta':-1,'verified_work_blobs':5,'applied_merges':0}))
