"""Build bounded research-only review from separately verified fixed-main snapshots."""
import json, gzip, collections
from pathlib import Path

OUT = Path(__file__).resolve().parent
LANE = OUT.parent
SHA = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
validation = json.loads((OUT / 'current-main-validation.json').read_text())
records = json.load(gzip.open(OUT / 'main-records.json.gz', 'rt'))
old = json.loads((LANE / 'cases.json').read_text()) + json.loads((LANE / 'hourly-20261022/cases.json').read_text())
old_by = {c['case_id']: c for c in old}
old_books = json.load(gzip.open(LANE / 'hourly-20261022/related-books.json.gz', 'rt'))
cases = []
for cid in ['JC-H005', 'JC-H006']:
    src = old_by[cid]
    books = []
    for b in src['related_books']:
        snap = records[b['path']]
        r = snap['record']
        books.append({'id': b['id'], 'path': b['path'], 'sha256': snap['sha256'],
                      'unchanged_from_checkpoint': snap['sha256'] == old_books[b['id']]['sha256'],
                      'work_id': r.get('work_id'), 'merged_into': r.get('merged_into'),
                      'measure_info': r.get('measure_info'), 'edition': r.get('edition'),
                      'indexed_by': r.get('indexed_by', []), 'sources': r.get('sources', []),
                      'contained_in': r.get('contained_in', [])})
    case = {'case_id': 'JC-ASTRA-' + cid.removeprefix('JC-'), 'supersedes_case_id': cid,
            'status': 'open', 'prior_status': src['status'], 'label': src['label'],
            'main_sha': SHA, 'members': src['members'], 'paths': src['paths'],
            'sha256': {i: records[p]['sha256'] for i, p in src['paths'].items()},
            'known_books_reviewed': books,
            'known_book_work_distribution': dict(collections.Counter(b['work_id'] for b in books)),
            'book_inventory_scope': 'All Books listed in the historical case were reread at the fixed main SHA. This is not a fresh whole-repository reference enumeration.',
            'applied': False, 'execution_ready': False, 'machine_merge_mapping': None}
    if cid == 'JC-H005':
        case.update({
          'evidence': [
            {'record_id':'d59f2mr6s6bl','field':'indexed_by[1]', 'finding':'經義考卷198、KR2n0011_WYG_198-17b載十卷及「汸自序」，與沈氏十二卷書矛盾。'},
            {'record_id':'d59f2j58ml8i','field':'indexed_by[0]', 'finding':'四庫總目明題元趙汸十卷；提要所述黃澤、杜預、陳傅良與錯掛自序論旨吻合。'},
            {'record_id':'d59f2n9s0yyp','field':'indexed_by[0]', 'finding':'清史稿明列沈欽韓補註十二卷，與續修四庫所影國圖稿本相合。'},
          ],
          'advance_this_round':'把泛稱「查所有版本」縮為25條已知Book的逐條書目矩陣；沈氏10條均著錄十二卷，趙氏15條中9條有十卷著錄，6條缺結構化卷數而保留版本／資源線索。提出錯掛來源與衍生description的定點修復順序。',
          'repair_proposal':[
            '以原書頁面核定經義考條的責任者後，將沈氏條indexed_by中該整節及原note存入修復台賬；避免無損拼接把污染傳給keeper。',
            '核實趙汸條尚未收錄同一來源節，再將原引文附入趙汸條，僅修正錯誤的掛接note並保留原note於台賬。此為建議，未改原生資料。',
            '重寫沈氏條description中混入的十卷說；主計量保留十二卷，逐字段核定其餘來源、版本和館藏。',
            '污染處理完後才另案確認沈氏兩條合併映射；趙汸十卷作品明確排除，所有Book保留個別版本。'
          ],
          'defer_reasons':['尚未讀經義考原影像確認節界；已知Book的目錄記錄不等於逐版本正文影像核驗。','未完成新main全量型別化引用、草稿promotions與book-text內容引用檢查。'],
          'next_step':'先對KR2n0011_WYG_198-17b做獨立來源歸屬校正，再重建沈氏兩條的字段無損台賬。'
        })
    else:
        case.update({
          'evidence':[
            {'record_id':'9950hg69s0','field':'indexed_by[0], sources[0]', 'finding':'十二卷心矩齋叢書本；上圖instance為gn44xfibn7epp487。'},
            {'record_id':'994fbpe9kx','field':'indexed_by[0], sources[0], contained_in[0]', 'finding':'二卷；上圖instance為00btd8k8bz32clqx；掛Collection 8rldoqmomjnl；Book edition空白。'},
            {'record_id':'d59fywb5cvsw','field':'ai_note', 'finding':'導入註明母叢書ej2m7e0071zea5nt（心矩齋叢書十一種）；故心矩齋判定來自子目導入線索，不是本輪已看原刻。'},
            {'record_id':'d59f2mr6s6bk / d59f2n9s0yyq','field':'indexed_by','finding':'續修四庫與清史稿均列沈欽韓十二卷地名補注；與單行補注書保持分立。'}
          ],
          'advance_this_round':'已知9條Book逐條對照：8條掛十二卷Work且均著錄十二卷，1條掛二卷Work。把爭點精確定位到兩個不同上圖instance及子目母叢書線索；不把「同為心矩齋」誤報成同源全字段相同。',
          'repair_proposal':[
            '取00btd8k8bz32clqx子目原始館藏記錄及心矩齋原目、卷首卷末，辨別漏十字、存二卷或節本。',
            '與gn44xfibn7epp487對照館藏及版本範圍；兩instance不同，不符合同source_key且除管理字段全等的Book機械合併條件。',
            '可先另案研究十二卷兩Work的同一性，但不能藉此把第三條二卷Work一併標confirmed；本輪維持整案open。'
          ],
          'defer_reasons':['二卷與十二卷是否為錄入漏字、存殘或節本仍未獲原刻／原館目證據。','未核母Collection原檔及全量跨庫引用；本輪僅檢查已知9條Book。'],
          'next_step':'從兩個上圖instance和母叢書ej2m7e0071zea5nt定點取證，而非再次泛搜同名。'
        })
    cases.append(case)

(OUT / 'cases.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n')
drift = [(c['case_id'], r['id']) for c in validation['cases'] for r in c['records'] if not r['unchanged']]
tombs = [(c['case_id'], r['id'], r['merged_into']) for c in validation['cases'] for r in c['records'] if r['merged_into']]
book_drift = [b['id'] for c in cases for b in c['known_books_reviewed'] if not b['unchanged_from_checkpoint']]
work_path = 'Work/k/7/6/d59fxvkzjk76-王肅周易注.json'
risk = {'case_id':'JC-007','type':'execution_risk_override','status':'confirmed',
        'execution_hold':True,'not_a_new_identity_case':True,'main_sha':SHA,
        'record_id':'d59fxvkzjk76','path':work_path,'sha256':records[work_path]['sha256'],
        'changed_field':'related_works','old_value':None,
        'current_value':records[work_path]['record'].get('related_works'),
        'finding':'新增指向d59fxx72mb5u的related關係，註為同作者、題名包含、卷數相容，未並待核；兩端均為JC-007擬併至d59f27yxltdu的loser。',
        'identity_effect':'新增候選關係不單獨推翻舊同一性裁決；原著錄、責任者及卷數字段未變。',
        'execution_effect':'舊SHA前置條件失效。直接把兩端重指keeper會生成自關係，原note亦會保留過期未並待核判語；必須先更新台賬並明定邊與note的處理，不能照搬舊machine_decision。',
        'next_step':'把當前完整related_works及原note存入修復台賬，明確擬並後自邊的語義處理；重新完成無損與引用檢查後方可解除本項hold。',
        'applied':False}
(OUT / 'existing-case-risks.json').write_text(json.dumps([risk], ensure_ascii=False, indent=2) + '\n')
counts = collections.Counter(c['status'] for c in old)
report = f'''# 经部 Astra 定点复核（2026-10-22）

固定 main：`{SHA}`。仅新增本目录研究材料；原生数据、墓碑、分类与派生索引均未改。

旧有效20案为 **13确认／1分立／6待核**。本轮重新核验20案所列 **{validation['unique_work_count']}个不同Work**，并精查JC-H005、JC-H006的 **34个已知关联Book**。核验覆盖不是新增结案量；新增确认0、分立0，两待核维持open，累计仍13／1／6。实际新增合并0。

## 最新main真实状态

- Work原档相对历史案件SHA256不符：{len(drift)}；墓碑记录：{len(tombs)}。详`current-main-validation.json`。
- 两案已知Book相对历史快照变化：{len(book_drift)}；列表：{json.dumps(book_drift,ensure_ascii=False)}。
- 本轮证明的是已列记录在固定SHA的状态，不声称重新完成全库Book或跨仓引用扫描。历史13组确认及39个拟并ID不等于已执行。
- JC-001来源混入《归藏》的执行暂停仍保留；JC-002、003、006、007的四项文本资产门槛沿用历史核查结果，本轮没有重扫book-text，不宣称资产迁移完成。

## JC-007：本轮新发现的执行风险

唯一变化档是王肃`d59fxvkzjk76`。已逐字段比较：仅新增`related_works`，指向`d59fxx72mb5u`，关系为`related`，note为「經部深度查重：同作者+题名包含+卷数相容，未並，待核」；其余著录、责任者与卷数等字段未变。当前SHA256为`{records[work_path]['sha256']}`。当前blob已按固定main树OID直接读取，未以旧文件代替。

这两个ID均在旧JC-007拟并组内，keeper是`d59f27yxltdu`。旧SHA前提已失效；机械重指两端会产生keeper指向自身的关系，并携带过期的「未並，待核」判语。**保留旧confirmed身份判断，但本轮新增执行hold**：先把原边及note完整记入台账，明确合并后自边的语义处理，并更新字段无损策略和引用审计，再解除此项hold。不能将新的候选关系直接解释成已实施，也不能静默丢失该note。详`existing-case-risks.json`；此为旧案执行覆盖，不增加确认案数。

## JC-H005：沈钦韩《左传补注》污染案

结论维持待核。最新原档中，沈氏`d59f2mr6s6bl`的《经义考》卷198节仍载「十卷」「汸自序」；赵汸`d59f2j58ml8i`的四库提要明确元赵汸十卷，且同论黄泽、杜预、陈傅良。沈氏另一条`d59f2n9s0yyp`及续修四库则为十二卷。不是同题即可整组并。

本轮把25个已知Book逐条展开：沈氏10条均著录十二卷；赵氏15条中9条有十卷著录，6条无结构化卷数、保留版本／资源线索。Book矩阵、当前哈希及来源URI见`cases.json`；这完成书目层面的逐条分流，不冒充看过全部版本影像。

可审阅修复顺序：核《经义考》原页节界→保存原错误挂接及note于台账→将正确来源附回赵汸条→修复沈氏description的十卷污染→再为沈氏两条建立无损并条台账。赵汸作品排除，Book保留各本。未看原页、未扫全量引用和文本库，因此没有提供可执行merge mapping。

## JC-H006：地名补注二卷／十二卷案

结论维持待核。9个已知Book中8条挂十二卷Work且均列十二卷；`994fbpe9kx`独列二卷。十二卷心矩斋本`9950hg69s0`的上图instance为`gn44xfibn7epp487`，二卷子目为`00btd8k8bz32clqx`，二者并非同source_key。二卷Book的edition为空；心矩斋归属依据其Work的导入note（母叢書`ej2m7e0071zea5nt`），不能写成已看原刻的结论。

下一步已收敛到两个instance及母丛书：索取原馆目、心矩斋卷首卷末，区分漏「十」、存残或节本。十二卷两Work可另立窄案，但不得顺带确认第三条。当前证据不满足Book同源全字段全等条件，本轮不并Book。

## 边界与交付

`cases.json`用`supersedes_case_id`替换旧H005/H006的研究说明，两案状态不变，不新增到累计案数。`main-records.json.gz`保留固定main原档解析快照与字节SHA256／Git blob ID；`current-main-validation.json`列全部20案的对照。

已读main《正式库并条审查规则》：执行前仍需字段无损台账、所有型别化引用及promotions、草稿同步、book-text资产和内容引用核查、审计／schema／分类／builder门槛。此研究轮未动数据，未运行或冒称写后检查通过。没有新增外部网页证据，所有事实限定于仓库记录及其已存目录原文。当前一轮到此结束。
'''
(OUT / 'report.md').write_text(report)
print(json.dumps({'work_count':validation['unique_work_count'],'work_drift':drift,'tombstones':tombs,'book_drift':book_drift,'old_counts':dict(counts),'focused_case_count':len(cases)}, ensure_ascii=False))
