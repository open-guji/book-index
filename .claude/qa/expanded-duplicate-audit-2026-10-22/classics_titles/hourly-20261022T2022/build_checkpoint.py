import gzip, hashlib, json, pathlib, re, sqlite3, subprocess

ROOT = pathlib.Path(__file__).resolve().parent
AUDIT = ROOT.parent.parent
BASE = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DB = '/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite'
TREE = pathlib.Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z')
SELECTION = [47, 48, 63, 69, 74]
def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

con = sqlite3.connect('file:' + DB + '?mode=ro', uri=True)
manifest = json.loads(con.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base'] == BASE
assert hashlib.sha256(TREE.read_bytes()).hexdigest() == manifest['tree_sha256']
tree = {}
for entry in TREE.read_bytes().split(b'\0'):
    if entry:
        head, path = entry.split(b'\t', 1)
        tree[path.decode()] = head.decode().split()[2]
pairs = json.loads((ROOT.parent / 'broad-20261022/candidate-pairs.json').read_text())
ids = sorted({i for n in SELECTION for i in pairs[n]['ids']})
snapshots = {}
for i in ids:
    path, oid, sha, data = con.execute('select path,blob_sha,sha256,data from records where id=?', (i,)).fetchone()
    assert tree[path] == oid
    raw = subprocess.check_output(['git', 'cat-file', 'blob', oid])
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == oid
    assert hashlib.sha256(raw).hexdigest() == sha
    parsed = json.loads(raw)
    assert parsed == json.loads(data) and not parsed.get('merged_into')
    snapshots[i] = dict(id=i, path=path, blob_sha=oid, sha256=sha, raw_utf8=raw.decode(), data=parsed)

prior_files, member_overlaps, pair_overlaps = [], [], []
for file in ROOT.parent.rglob('cases.json'):
    if ROOT in file.parents:
        continue
    prior_files.append(str(file.relative_to(ROOT.parent)))
    hit = set(re.findall(r'd59[a-z0-9]+', file.read_text())) & set(ids)
    if hit:
        member_overlaps.append(dict(path=str(file.relative_to(ROOT.parent)), ids=sorted(hit)))
    obj = json.loads(file.read_text())
    rows = obj if isinstance(obj, list) else obj.get('cases', [])
    for row in rows:
        present = set(re.findall(r'd59[a-z0-9]+', json.dumps(row)))
        for n in SELECTION:
            if set(pairs[n]['ids']) <= present:
                pair_overlaps.append(dict(path=str(file), case_id=row.get('case_id'), candidate_index=n))
assert not member_overlaps and not pair_overlaps

refs = [
 dict(id='E1', url='https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷086', pointer='卷86，web lines196–197；庫內KR2n0011_WYG_086-21a', excerpt='吾丘氏〈衍〉尚書要略；未見', claim='精確標目與作者；未見為朱氏判語。'),
 dict(id='E2', url='https://zh.wikisource.org/wiki/竹素山房詩集_(四庫全書本)/全覽', pointer='提要，web line117', excerpt='其名或稱吾衍或稱郚衍或稱吾世衍', claim='同段以吾丘衍為主名並列吾衍，且列所著尚書要畧；明確別名互證與書目交叉。'),
 dict(id='E3', url='https://zh.wikisource.org/zh-hant/竹素山房詩集_(四庫全書本)/附録', pointer='王禕吾丘子行傳，著述列舉', excerpt='吾丘子行者名衍太末人也', claim='傳記列尚書要略及其他著述；不以共用entity充當獨立證據。'),
 dict(id='E4', url='https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷040', pointer='俞氏琰周易集説條，引吳中人物誌及納蘭成德序', excerpt='俞琰字玉吾', claim='同段列卦爻象占分類；納蘭序將讀易須知、卦爻象占分類等分列，不是合題一書。'),
 dict(id='E5', url='https://zh.wikisource.org/zh-hant/周易集説_(四庫全書本)', pointer='四庫提要，web line114附近', excerpt='琰字玉吾', claim='提要列卦爻象占分類為另著，原附集說；不能將附刊關係誤作與周易集說同一。'),
 dict(id='E6', url='https://zh.wikisource.org/zh-hant/宋史/卷428', pointer='謝良佐傳，web line148', excerpt='謝良佐字顯道，壽春上蔡人', claim='謝顯道與謝良佐直接人物同一證；傳中書題作論語說，並非本案兩側原題逐字相同證。'),
 dict(id='E7', url='https://zh.wikisource.org/zh-hant/郡齋讀書志/卷四', pointer='論語類，web lines172–174', excerpt='謝顯道論語解十卷', claim='宋人目錄直接將字號、精確書題、十卷連接；與經義考良佐十卷可相接。'),
 dict(id='E8', url='https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷214', pointer='謝氏良佐論語解，web lines129–132；庫內KR2n0011_WYG_214-2b', excerpt='謝氏〈良佐〉論語解；宋志十卷', claim='本名下同題十卷，並載良佐自序。'),
 dict(id='E9', url='https://zh.wikisource.org/zh-hant/欽定古今圖書集成/理學彙編/經籍典/第267卷', pointer='明焦竑經籍志之論語類，謝顯道條', excerpt='論語解二卷；謝顯道', claim='古今圖書集成轉引焦志確有二卷讀法，不把庫內二卷逕稱OCR；此為焦志衍生證人，非獨立第二目錄。'),
 dict(id='E10', url='https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷105', pointer='蔡氏卞毛詩名物解，web lines127–131；庫內KR2n0011_WYG_105-5a', excerpt='蔡卞元度撰', claim='同條本名、字及書目直接相接，二十卷；陸元輔段亦以蔡元度稱其書。'),
 dict(id='E11', url='https://www.wul.waseda.ac.jp/kotenseki/html/ro12/ro12_03609/index.html', pointer='title lines0,14；authority22；imprint33；extent40', excerpt='毛詩名物解. 巻第1-20 / 蔡元度 集解', claim='館藏本題蔡元度，權威作者欄蔡卞；通志堂康熙15序，20卷而此藏本1冊。不能拿此冊數覆寫故宮另藏本。', evidence_level='holding_institution_catalog'),
 dict(id='E12', url='https://zh.wikisource.org/zh-hant/清史稿/卷145', pointer='小學類韻學，web line226', excerpt='古韻通說四卷。龍翰臣撰', claim='四卷確為志文轉錄，不能直接改成二十卷或臆測四冊。'),
 dict(id='E13', url='https://www.shidianguji.com/book/LS0025/chapter/1kt95z2ebilhb', pointer='清史稿卷482龍啟瑞傳，web lines5–9', excerpt='字翰臣，臨桂人', claim='龍啟瑞傳直接連接翰臣與古韻通說二十卷，並說明全書論本音、通韻、轉音的內容。'),
 dict(id='E14', url='https://zh.wikisource.org/wiki/清史稿/卷482', pointer='龍啓瑞傳', excerpt='而著古韻通説二十巻', claim='同一原典之另一轉錄核對，與E13非兩個獨立古代證人。')
]
for ref in refs:
    ref.setdefault('evidence_level', 'primary_text_transcription_not_image')
    ref.update(accessed='2026-10-22', image_checked=False)
common_gates = [
 '同步最新main並重核兩側原值、blob與墓碑狀態',
 '建立逐字段無損台帳；保存全部來源、作者角色、獨有note/description及衝突原值',
 '全庫Book/Work/Entity/Collection/分類/promotions型別引用掃描，不能只按文字替換',
 '草稿庫與book-text整理本/輯佚檔/內容引用核查並同步另PR',
 '實際寫後audit-merge-ledger T/L/P/R、schema、check_v2、分類、官方索引與builder基線比較均通過'
]
configs = [
 (47, '尚書要略：吾丘衍／吾衍', 'd59f2gidf5z4', ['E1','E2','E3'],
  '四庫提要在同段明列吾丘衍之名或稱吾衍，並列尚書要畧；王禕本傳列尚書要略；經義考標目亦精確相接。兩側並非原典與注本，均指吾氏所撰要略。未見沒有被提升為全佚。',
  ['d59f2gcv7h1e#/indexed_by/0','d59f2gcv7h1e#/authors/0','d59f2gidf5z4#/indexed_by','d59f2gidf5z4#/merged_in','d59f2gidf5z4#/related_works/0'],
  ['保留經義考未見判語、卷86原頁、尚書要畧異體及原有d59f6eoatg5i歷史合併台帳，不把歷史項重算新案','description僅一志／別無他證是過時派生語，更新須保留原值；不得把本書併入尚書原典','contains_text_of目標d59f20arpg5c為既有邊；本案未核其古今文範圍，不擅自新增、刪除或改指']),
 (48, '卦爻象占分類：俞玉吾／俞琰', 'd59f2gcybugx', ['E4','E5'],
  '經義考引吳中人物誌直稱俞琰字玉吾，且列卦爻象占分類；四庫周易集說提要亦以此名/字和另著相接。此是同一別著的二次目錄建條，非周易原典或周易集說；曾附刊並不消除別著身份。',
  ['d59f2gcybugx#/indexed_by/0','d59f2gcybugx#/ai_note','d59f6eryjldy#/indexed_by/0','d59f6eryjldy#/authors/0','d59f6eryjldy#/ai_note'],
  ['核兩個不同entity責任連結，名/字可保留但不在本Work案順便合Person','保留千頃堂author_info之缺與元史藝文志一卷，各為來源語，不把缺當人名或全佚證','嚴格保留讀易須知與卦爻象占分類既有分拆；候選53讀易須知不在本次裁定範圍','宋遺民入元著述的斷代須有本書證，不由提要署宋或補元志單獨覆蓋period']),
 (63, '論語解：謝良佐／謝顯道', 'd59f2he2mry8', ['E6','E7','E8','E9'],
  '宋史本傳確證謝良佐字顯道；郡齋讀書志直接列謝顯道論語解十卷，與經義考謝良佐同題十卷相接，並非只認同一人。焦志二卷是異志卷數歧異，依固定main錄入判準III.1不作二書證。卷差原因未證，不能杜撰殘本、節本或OCR。',
  ['d59f2he2mry8#/indexed_by/0','d59f2he2mry8#/indexed_by/1','d59f2he2mry8#/merged_in','d59f2hlnrf9e#/indexed_by/0','d59f2hlnrf9e#/juan_count','d59f2hlnrf9e#/period_basis'],
  ['兩卷/十卷逐源全留；若實際Book呈另編或節抄，須先分流該Book而不能機械吞併','本傳作論語說僅供人與著述脈絡，不在未查其全庫條目前把所有論語說一併改題合入','既有范祖禹論語解之誤掛及歷史merged_in全留；本案不再計該墓碑一次','兩個Person entity須另案清點，不以Work身份確認替代Person全引用審計']),
 (69, '毛詩名物解：蔡卞／蔡元度', 'd59f2hrbldz4', ['E10','E11'],
  '經義考同條稱蔡卞元度撰並列毛詩名物解；早稻田同一通志堂二十卷藏本題蔡元度集解，作者權威欄蔡卞。故宮來源一側的同題二十卷並非另一位作者的新解。版本來源仍是Work，合Work不合故宮、早稻田或四庫各實物。',
  ['d59f2hrbldz4#/indexed_by/1','d59f2hrbldz4#/indexed_by/3','d59f2hrbldz4#/resources','d59f2hs0vlz7#/authors/0','d59f2hs0vlz7#/description','d59f2hs0vlz7#/measures/0','d59f2hs0vlz7#/measure_info'],
  ['故宮贈善023662所屬Book與原始著錄仍須定位；本輪未讀故宮原記錄，不可稱已核實物或Book重複','蔡元度集解與蔡卞撰兩種角色／源名保留，兩Person entity另案核','20卷與measures冊20衝突須原值封存後核故宮實物；早稻田1冊不可套用於故宮本','保留通志堂校訂者成德及所有資源；與詩經原典、陸佃埤雅分立']),
 (74, '古韻通說：龍啓瑞／龍翰臣', 'd59f2mrsy0w2', ['E12','E13','E14'],
  '清史稿本傳直接稱龍啟瑞字翰臣並述古韻通說二十卷，且說明本書內容；藝文志以字著錄同題四卷。這不是同一志內兩條同題書，更無初續、改編標記。人書同一可確認，四/二十卷為未解釋的來源衝突，不能據此臆造四冊或另一版。',
  ['d59f2mrsy0w2#/indexed_by/0','d59f2mrsy0w2#/authors/0','d59f2mrsy0w2#/resources','d59f2nbi5728#/indexed_by/0','d59f2nbi5728#/juan_count','d59f2nbi5728#/authors/0'],
  ['完整保留藝文志四卷原文與續修四庫二十卷、同治六年版；不得把原引文直接改成二十','核同治六年藏本序目與實際Book；四卷成因尚未證實，若見另一編次須先分流','字/號翰臣稱謂不同來源各存，本輪只用清史稿字說不強行統一所有來源','兩Person entity須另立全引用台帳；不由Work合併擅改人物外部標識'])
]
cases = []
for order, (n, title, keeper, evidence, decision, pointers, gates) in enumerate(configs, 1):
    pair = pairs[n]
    for pointer in pointers:
        i, ptr = pointer.split('#', 1)
        value = snapshots[i]['data']
        for piece in ptr.lstrip('/').split('/'):
            value = value[int(piece)] if isinstance(value, list) else value[piece]
    cases.append(dict(case_id=f'JC-2022-{order:03d}', status='confirmed', title=title,
      ids=pair['ids'], supersedes=[], new_case=True, relationship_kind='same_work',
      candidate_pair_index_zero_based=n, candidate_provenance=pair, decision=decision,
      research_keeper_candidate=keeper, research_loser_candidates=[i for i in pair['ids'] if i != keeper],
      machine_merge_mapping=None, execution_ready=False, native_merges=0, already_main_covered=False,
      evidence_ids=evidence, evidence_urls=[r['url'] for r in refs if r['id'] in evidence],
      exact_source_pointers=pointers,
      records=[{k:snapshots[i][k] for k in ['id','path','blob_sha','sha256']} for i in pair['ids']],
      specific_execution_gates=gates, common_execution_gates=common_gates,
      raw_conflict_archive='main-records.json.gz: complete parsed data plus byte-exact raw_utf8 for each record'))
write('cases.json', cases)
write('references.json', refs)
with gzip.open(ROOT / 'main-records.json.gz', 'wt', encoding='utf8') as f:
    json.dump(dict(base=BASE, records=snapshots), f, ensure_ascii=False, indent=2)
write('validation.json', dict(base=BASE, database_manifest=manifest, database_readonly=True,
  tree_sha256_verified=True, record_count=len(snapshots), selected_candidate_pairs=SELECTION,
  records=[dict(id=i, path=s['path'], blob_sha=s['blob_sha'], sha256=s['sha256'], tree_match=True,
                raw_hash_verified=True, sqlite_equal=True, active=True) for i,s in snapshots.items()],
  exact_json_pointers_resolved=True, old_cases_checked=prior_files,
  prior_member_overlaps=member_overlaps, prior_pair_overlaps=pair_overlaps,
  selected_count=5, new_confirmed=5, new_separate=0, new_open=0,
  native_merges=0, native_files_modified=0, machine_merge_mappings=0,
  confirmation_scope='Work identity only; no execution release or Person/Book merge decision',
  rules_read=[BASE+':.claude/qa/正式库并条审查规则.md',BASE+':schema/cataloging-rules.md sections I–III'],
  gates_not_run=['full inbound typed references','Book inventory and physical copies','promotions',
    'draft repository','book-text/collated editions/fragments','field-complete executable merge ledger',
    'write-after T/L/P/R','schema/check_v2','classification','official indexes','builder baseline comparison'],
  web_image_check=False, scope_locks=['JC-001/JC-007 hold','BOOK-0010 defer','no obsolete 1876 mapping','no Feng edits','no PR1216 persons action']))
print(json.dumps(dict(cases=len(cases),records=len(snapshots),confirmed=5,prior_overlap=0),ensure_ascii=False))
