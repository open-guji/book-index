#!/usr/bin/env python3
"""每批之後必跑之驗（qa-sweep 硬門禁）。

  python3 .claude/qa/verify.py            # 全庫：索引漂移必須為 0；懸空計數與基線比
  python3 .claude/qa/verify.py --strict   # 懸空亦須為 0（收工前）

輸出五個數：works 索引漂移（period/loss_status/title/subtype/author/dynasty/role；dynasty 取第一個有朝代的作者，無則頂層——同 build）、
entities 索引漂移、work 側懸空引用、entity.works 懸空、單向邊（人指書而書不指人）。
漂移不為 0 即失敗（exit 1）——改了記錄而未回寫索引，或改了索引而未改記錄。

S5（overview#189）另加：通用 `todo`／`review`（審核狀態）形狀校驗、`_edition_count`／
`_member_count` 派生計數校驗（以上四項 0 基線，計入 FAIL）；以及 `related_works[].title`／
`Collection.contained_works[].title` 漂移、`provenance[].institution` 簡體字三項 stale_ref
推廣校驗——這三項是既有欄位之內容問題，非本卡新增，只報數、落 known-issues，不計入 FAIL。

**schema-v2（2026-10-07，overview#459 F6-3；2026-10-11 overview#506 B 收尾）**：源檔不再有 `Work.books`、
`Entity.works`、`Collection.books／contained_works`、`Work.classification`、`_` 派生欄，故 main() 不再驗
`entity.works`（懸空／重複／單向邊）、`_edition_count`／`_member_*`、舊 `classification`、`Collection.contained_works`。
留下：分類改驗 `classification/<法>/members/` 類檔（`classify check`），計入 FAIL；另報 `check_v2.py` 舊格式殘留數
（`--strict` 時計入 FAIL）。entities 索引漂移比的是 index 的 `birth_year`／`death_year` 與源檔 `dates.birth`／`dates.death`。
（對應的 `derive_*`／`*_ok` 輔助函式與 `s3*`／`s5` 一次性腳本、測試另批刪。）
"""
import argparse, collections, glob, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')): out.update(json.load(open(f)))
    return out

def classification_members_problems(root, work_ids, ref_work_ids=frozenset()):
    """schema-v2 分類類檔校驗（SCHEMA〈八〉之 `classify check`）。回 [(檔, 問題)]，空即過。
    work_ids：本倉 Work id；ref_work_ids：草稿庫可指正式庫之 Work。"""
    out = []
    base = os.path.join(root, 'classification')
    sp = os.path.join(base, 'schemes.json')
    if not os.path.exists(sp):
        return out
    for sc in json.load(open(sp, encoding='utf-8')):
        tree_p = os.path.join(base, sc.get('tree') or (sc['id'] + '/tree.json'))
        if not os.path.exists(tree_p):
            out.append((sc['id'], 'tree.json 不存在')); continue
        nodes = {n['id']: n for n in json.load(open(tree_p, encoding='utf-8')).get('nodes') or []}
        seen = collections.defaultdict(list)
        for f in sorted(glob.glob(os.path.join(base, sc['id'], 'members', '*.json'))):
            rel = os.path.relpath(f, root)
            d = json.load(open(f, encoding='utf-8'))
            node = d.get('node')
            if os.path.basename(f) != '%s.json' % node: out.append((rel, '檔名與 node 不符'))
            if node not in nodes: out.append((rel, '節點不在樹上：%s' % node))
            elif nodes[node].get('retired'): out.append((rel, '節點已退役：%s' % node))
            rows = d.get('members') or []
            if [r[0] for r in rows] != sorted(r[0] for r in rows): out.append((rel, '成員行未按 work_id 排序'))
            for r in rows:
                if not (isinstance(r, list) and r and isinstance(r[0], str)):
                    out.append((rel, '成員行形狀不對：%r' % (r,))); continue
                if r[0] not in work_ids and r[0] not in ref_work_ids:
                    out.append((rel, '成員不是 Work：%s' % r[0]))
                seen[r[0]].append(node)
        if sc.get('exclusive', True):
            for wid, ns in seen.items():
                if len(ns) > 1: out.append((sc['id'], '互斥法一部多類：%s %s' % (wid, ns)))
    return out

def dates_ok(d):
    """Entity.dates 校验（S4 新 schema 吸收④）：無此欄即過。
    回傳 None 表示過；否則回傳一句話講哪裡錯。"""
    dt = d.get('dates')
    if dt is None: return None
    birth, death, floruit = dt.get('birth'), dt.get('death'), dt.get('floruit')
    for name, v in (('birth', birth), ('death', death)):
        if v is not None and not isinstance(v, int): return f'{name} 非整数：{v!r}'
    if floruit is not None:
        if not (isinstance(floruit, list) and len(floruit) == 2): return f'floruit 非二元数组：{floruit!r}'
        for v in floruit:
            if not isinstance(v, int): return f'floruit 含非整数：{floruit!r}'
        if floruit[0] > floruit[1]: return f'floruit 起 > 止：{floruit!r}'
    if birth is not None and death is not None and birth > death:
        return f'birth > death：{birth} > {death}'
    # B2 後記錄不再帶 birth_year／death_year：有則須與 dates 一致，無則不查
    by, dy = d.get('birth_year'), d.get('death_year')
    if birth is not None and by is not None and birth != by:
        return f'dates.birth={birth} 与 birth_year={by} 不一致'
    if death is not None and dy is not None and death != dy:
        return f'dates.death={death} 与 death_year={dy} 不一致'
    return None

# overview#217（据 #214 Q4 体检 check5）：朝代大致纪年區間（公歷），僅用於「dynasty 與生卒
# 世纪明顯不合」的粗篩監控，留足餘量（±40年）不作精判——史學慣例常以人物主要活動／卒年所屬
# 朝代標注而非生年所屬朝代（如金末元初文人多繫元），此表對此類情況亦會命中，故只報數不入 FAIL。
DYNASTY_RANGE = {
    '夏': (-2070, -1600), '商': (-1600, -1046), '西周': (-1046, -771), '周': (-1046, -256),
    '春秋': (-770, -476), '戰國': (-475, -221), '秦': (-221, -206),
    '西漢': (-206, 8), '漢': (-206, 220), '新': (8, 23), '東漢': (25, 220),
    '三國': (220, 280), '魏': (220, 265), '蜀': (221, 263), '吳': (222, 280),
    '西晉': (265, 316), '東晉': (317, 420), '晉': (265, 420),
    '南北朝': (420, 589), '宋(南朝)': (420, 479), '齊': (479, 502), '梁': (502, 557), '陳': (557, 589),
    '北魏': (386, 534), '北齊': (550, 577), '北周': (557, 581),
    '隋': (581, 618), '唐': (618, 907), '五代': (907, 960), '十國': (907, 979),
    '宋': (960, 1279), '北宋': (960, 1127), '南宋': (1127, 1279),
    '遼': (916, 1125), '金': (1115, 1234), '西夏': (1038, 1227), '元': (1271, 1368),
    '明': (1368, 1644), '清': (1616, 1912), '民國': (1912, 1949),
}
_DYNASTY_MARGIN = 40

def dynasty_century_mismatch(d):
    """d 之 dynasty 與 birth_year／death_year／dates.birth／dates.death 是否明顯對不上
    （詞表外朝代、無年份、或在寬容範圍內皆不算）。回傳 True／False，只報不改。"""
    dynasty = d.get('dynasty')
    rng = DYNASTY_RANGE.get(dynasty)
    if not rng:
        return False
    lo, hi = rng[0] - _DYNASTY_MARGIN, rng[1] + _DYNASTY_MARGIN
    dates = d.get('dates') or {}
    for y in (d.get('birth_year'), d.get('death_year'), dates.get('birth'), dates.get('death')):
        if isinstance(y, int) and not (lo <= y <= hi):
            return True
    return False

_QID_RE = re.compile(r'^Q\d+$')

def external_ids_ok(d):
    """Entity.external_ids.wikidata_id／viaf_id 校验（S4b，overview#159）：無此二欄即過。
    wikidata_id 須形如 Q\\d+；viaf_id 須為純數字字串。回傳 None 表示過，否則回傳錯誤說明。"""
    ext = d.get('external_ids')
    if not ext: return None
    wd = ext.get('wikidata_id')
    if wd is not None and not (isinstance(wd, str) and _QID_RE.match(wd)):
        return f'wikidata_id 形狀不合：{wd!r}'
    viaf = ext.get('viaf_id')
    if viaf is not None and not (isinstance(viaf, str) and viaf.isdigit()):
        return f'viaf_id 非純數字字串：{viaf!r}'
    return None

def count_ok(c):
    """Collection.count：四項（juan/ce/zhong/han）須為 int 或 None，source 非空字串，
    且至少一項非空（全空即不該寫這個物件，該整欄位留 None）。"""
    if not isinstance(c, dict): return False
    for f in ('juan', 'ce', 'zhong', 'han'):
        v = c.get(f)
        if v is not None and not (isinstance(v, int) and not isinstance(v, bool)): return False
    if not isinstance(c.get('source'), str) or not c.get('source').strip(): return False
    return any(c.get(f) is not None for f in ('juan', 'ce', 'zhong', 'han'))

def provenance_ok(prov):
    """Book.provenance：數組，每項 institution 非空字符串、call_number 為字符串。"""
    if not isinstance(prov, list): return False
    for item in prov:
        if not isinstance(item, dict): return False
        inst = item.get('institution')
        if not isinstance(inst, str) or not inst.strip(): return False
        if not isinstance(item.get('call_number', ''), str): return False
    return True

EDITION_TYPES = {'刻本', '抄本', '稿本', '活字本', '石印本', '油印本', '曬印本', '鉛印本', '影印本', '套印本', '拓本', '印刷本', '其他'}

def edition_type_ok(v):
    """Book.edition_type：須落在受控十詞表內（S2b，overview#157）。"""
    return v in EDITION_TYPES

def physical_description_ok(pd):
    """Book.physical_description：物件，leaf_style/binding/dimensions/condition/source 皆字符串，
    四內容子欄（不含 source）至少一項非空（S2b，overview#157）。"""
    if not isinstance(pd, dict): return False
    content_fields = ('leaf_style', 'binding', 'dimensions', 'condition')
    for f in content_fields + ('source',):
        v = pd.get(f)
        if v is not None and not isinstance(v, str): return False
    if not isinstance(pd.get('source'), str) or not pd.get('source').strip(): return False
    return any((pd.get(f) or '').strip() for f in content_fields)

# ---- S5（overview#189）：通用 todo／審核狀態／派生計數／stale_ref 推廣 ----

def todo_ok(v):
    """通用 `todo`（Work／Book／Collection／Entity 皆可用）：無此欄即過。
    數組，每項至少 `{what}`，`by`／`date` 選填皆為字符串。只定義形狀，本卡不批量回填。"""
    if v is None: return True
    if not isinstance(v, list): return False
    for item in v:
        if not isinstance(item, dict): return False
        what = item.get('what')
        if not isinstance(what, str) or not what.strip(): return False
        for f in ('by', 'date'):
            fv = item.get(f)
            if fv is not None and not isinstance(fv, str): return False
    return True

REVIEW_STATUS = {'unreviewed', 'reviewed', 'disputed'}

def review_ok(v):
    """通用審核狀態 `review`（由 v2 `confirm` 改造）：無此欄即過。
    物件 `{status, by, date}`，`status` 落於三值域，`by`／`date` 選填皆為字符串。
    只定義形狀，本卡不批量回填（現行無條目有此欄，基線 0）。"""
    if v is None: return True
    if not isinstance(v, dict): return False
    if v.get('status') not in REVIEW_STATUS: return False
    for f in ('by', 'date'):
        fv = v.get(f)
        if fv is not None and not isinstance(fv, str): return False
    return True

SIMP_HINT_CHARS = set('国学图书馆')  # 本庫以繁體為主，這批字一見即是簡體（機構名 stale_ref 推廣用）

def institution_simplified(inst):
    """Book.provenance[].institution 是否含簡體字（與全庫繁體慣例不一，如
    「中国国家图书馆」對「中國國家圖書館」）。只報不改——本卡不動既有欄位之值。"""
    return any(ch in SIMP_HINT_CHARS for ch in (inst or ''))

def title_of(rid, IW, IC):
    if rid in IW: return IW[rid]['title']
    if rid in IC: return IC[rid]['title']
    return None

BASE_EDITION_ROLES = {'底本', '配補', '參校'}

def base_edition_ok(be, self_id, book_ids, work_ids):
    """Book.base_edition：陣列，每項 role 落三詞表、name／source 非空字符串，
    book_id／work_id 若填須存在且 book_id 不得指向本書自身（S2c，overview#190）。"""
    if not isinstance(be, list): return False
    for item in be:
        if not isinstance(item, dict): return False
        if item.get('role') not in BASE_EDITION_ROLES: return False
        if not isinstance(item.get('name'), str) or not item.get('name').strip(): return False
        if not isinstance(item.get('source'), str) or not item.get('source').strip(): return False
        bid = item.get('book_id')
        if bid is not None:
            if not isinstance(bid, str) or bid == self_id or bid not in book_ids: return False
        wid = item.get('work_id')
        if wid is not None:
            if not isinstance(wid, str) or wid not in work_ids: return False
    return True

def _CODES_SUBTYPE(cv2):
    """check_v2.CODES 裡屬專名子類型之碼（第二欄為「專名」者）。"""
    return {c for c, (_, grp) in cv2.CODES.items() if grp == '專名'}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--why', action='store_true', help='「索引缺記錄檔」時印出各 id 之最後刪除提交（坑 41）')
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--base', default='origin/main', help='基線 ref（默認 origin/main）；解析不到則略過「消失 id」檢查')
    a = ap.parse_args()
    IW, IB, IE = idx('works'), idx('books'), idx('entities')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    ALL = set(IW) | set(IB) | set(IE) | set(IC)
    drift_w, dangle_w, missing = [], [], []
    bad_prov = []
    bad_et, bad_pd = [], []
    bad_todo, bad_review = [], []
    bad_inst = []
    bad_be = []
    for bid, ie in IB.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(bid); continue
        d = json.load(open(p))
        prov = d.get('provenance')
        if prov is not None and not provenance_ok(prov):
            bad_prov.append(bid)
        if prov:
            for item in prov:
                inst = item.get('institution') if isinstance(item, dict) else None
                if inst and institution_simplified(inst):
                    bad_inst.append((bid, inst))
        et = d.get('edition_type')
        if et is not None and not edition_type_ok(et):
            bad_et.append((bid, et))
        pd_ = d.get('physical_description')
        if pd_ is not None and not physical_description_ok(pd_):
            bad_pd.append(bid)
        if not todo_ok(d.get('todo')): bad_todo.append((bid, 'Book'))
        if not review_ok(d.get('review')): bad_review.append((bid, 'Book'))
        be = d.get('base_edition')
        if be is not None and not base_edition_ok(be, bid, IB, IW):
            bad_be.append(bid)
    stale_related = []
    bad_tomb_target, bad_tomb_unindexed = [], []   # 墓碑：目標須存在且自身非墓碑（防懸空／鏈式）；墓碑檔須在 index/works 有條目
    bad_merged_in = []   # 被併旧 id 必有墓碑（GUJI-126 #326 缺陷：23 个被併 Work 被直接删除，线上 404）
    for wid, ie in IW.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(wid); continue
        d = json.load(open(p))
        for f in ('period', 'loss_status', 'title', 'subtype'):
            x, y = ie.get(f), d.get(f)
            if x is None and y is None: continue
            if x != y: drift_w.append((wid, f, x, y))
        au = d.get('authors') or []; a0 = au[0] if au else {}
        nz = lambda v: None if v in ('', None) else v
        want = {'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
                # schema-v2：index/ 由 build 生成，口徑照 bim entry_extractor 與 SCHEMA〈十四〉——
                # 索引之 dynasty＝撰人朝代：第一個有朝代的作者，無則頂層（book-index#75、overview#496 §六-1；舊 reindex 反之）
                'dynasty': next((a['dynasty'] for a in au if isinstance(a, dict) and isinstance(a.get('dynasty'), str) and a['dynasty']), None)
                           or nz(d.get('dynasty'))}
        for f, y in want.items():
            if nz(ie.get(f)) != y: drift_w.append((wid, f, ie.get(f), y))
        if d.get('merged_into'):
            tp = IW.get(d['merged_into'], {}).get('path')
            try: td = json.load(open(os.path.join(ROOT, tp))) if tp else None
            except Exception: td = None
            if not td or td.get('merged_into'): bad_tomb_target.append((wid, d['merged_into']))
        for m in (d.get('merged_in') or []):
            mid = m.get('id') if isinstance(m, dict) else None
            # 只查 2026-10-14 起 mergework 写入的条目（at 字段）；更早的 merged_in 多为 draft 旧 id／Book id，正式库本无其档
            if not mid or str(m.get('at') or '') < '2026-10-14': continue
            mp = IW.get(mid, {}).get('path')
            try: md = json.load(open(os.path.join(ROOT, mp))) if mp else None
            except Exception: md = None
            if not md or md.get('merged_into') != wid: bad_merged_in.append((wid, mid))
        for r in (d.get('related_works') or []):
            if r.get('id') and r['id'] not in ALL: dangle_w.append((wid, 'related_works', r['id']))
            if r.get('id') and r.get('title') is not None:
                actual = title_of(r['id'], IW, IC)
                if actual is not None and actual != r['title']:
                    stale_related.append((wid, r['id'], r['title'], actual))
        for x in au:
            if x.get('entity_id') and x['entity_id'] not in IE: dangle_w.append((wid, 'authors.entity_id', x['entity_id']))
        if not todo_ok(d.get('todo')): bad_todo.append((wid, 'Work'))
        if not review_ok(d.get('review')): bad_review.append((wid, 'Work'))
    import glob as _glob
    for _f in _glob.glob(os.path.join(ROOT, 'Work', '*', '*', '*', '*.json')):
        _wid = os.path.basename(_f).split('-')[0]
        if _wid in IW: continue
        try: _d = json.load(open(_f))
        except Exception: continue
        if _d.get('merged_into'): bad_tomb_unindexed.append(_wid)
    drift_e, bad_dates, bad_extids = [], [], []
    bad_dynasty_century = []
    for eid, ie in IE.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(eid); continue
        d = json.load(open(p))
        dts = d.get('dates') if isinstance(d.get('dates'), dict) else {}
        for f in ('primary_name', 'dynasty', 'birth_year', 'death_year', 'period'):
            # B2 後源檔無 birth_year／death_year：index 的同名鍵由 dates.birth／dates.death 推出（整數才有）
            y = d.get(f) if f not in ('birth_year', 'death_year') else dts.get('birth' if f == 'birth_year' else 'death')
            if f in ('birth_year', 'death_year') and not (isinstance(y, int) and not isinstance(y, bool)): y = None
            x = ie.get(f)
            if x is None and y is None: continue
            if x != y: drift_e.append((eid, f, x, y))
        err = dates_ok(d)
        if err: bad_dates.append((eid, err))
        err = external_ids_ok(d)
        if err: bad_extids.append((eid, err))
        if dynasty_century_mismatch(d):
            bad_dynasty_century.append((eid, d.get('dynasty'), dts.get('birth'), dts.get('death')))
        if not todo_ok(d.get('todo')): bad_todo.append((eid, 'Entity'))
        if not review_ok(d.get('review')): bad_review.append((eid, 'Entity'))
    # S3（Collection.count 吸收，overview#140）：count 若寫了就必須形狀對、有依據、非全空。
    bad_count = []
    for cid, ie in IC.items():
        p2 = ie.get('path')
        if not p2 or not os.path.exists(p2): continue
        try: dc = json.load(open(p2))
        except Exception: continue
        cnt = dc.get('count')
        if cnt is not None and not count_ok(cnt): bad_count.append(cid)
        if not todo_ok(dc.get('todo')): bad_todo.append((cid, 'Collection'))
        if not review_ok(dc.get('review')): bad_review.append((cid, 'Collection'))
    # schema-v2：分類類檔、舊格式殘留
    bad_cls_members = classification_members_problems(ROOT, set(IW))
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import check_v2 as _cv2
        import entity_subtypes as _es
        # 專名子類型（dynasty／reign／office／place，#464）：與 check_v2 共用 entity_subtypes 同一份實現。
        # ERROR 一律計入 FAIL（四子類型在正式庫為 0 條、草稿庫已清零）；WARN／INFO 只報數。
        _reg = _es.Registry.from_root(ROOT)
        _all = [r for rp in _cv2.walk(ROOT) for r in _cv2.check_file(ROOT, rp, _reg)]
        _all += [(_reg.path.get(i, ''), i, 'Entity', c, f, d, lv) for i, c, lv, f, d in _es.check_global(_reg)]
        _cv2_rows = [r for r in _all if r[6] == _es.ERROR and r[3] not in _CODES_SUBTYPE(_cv2)]
        bad_subtype = [r for r in _all if r[6] == _es.ERROR and r[3] in _CODES_SUBTYPE(_cv2)]
        subtype_warn = [r for r in _all if r[6] == _es.WARN]
        subtype_n = collections.Counter(_reg.sub.get(i) for i in _reg.sub if _reg.sub[i] in _es.NEW_SUBTYPES)
    except Exception as _e:   # noqa: BLE001
        _cv2_rows = [('', '', '', 'ERR', '', str(_e), 'ERROR')]
        bad_subtype, subtype_warn, subtype_n = [], [], collections.Counter()
    print(f'索引檔缺記錄檔        {len(missing)}')
    print(f'works 索引漂移        {len(drift_w)}')
    print(f'entities 索引漂移     {len(drift_e)}')
    print(f'work 側懸空引用       {len(dangle_w)}')
    print(f'被併旧 id 無墓碑（merged_in[] 之 id 須有 merged_into 指回本 Work 之墓碑檔） {len(bad_merged_in)}')
    for r in bad_merged_in[:10]: print('  無墓碑', r)
    # 基線對比（GUJI-126 #326 缺陷：23 個被併 Work 被直接刪檔，線上 404）：相對基線（--base，默認 origin/main）
    # 之全部 Work／Entity id，凡不再有任何檔（墓碑亦是檔，留在原路徑）者即「消失」，一律 FAIL。
    # 同時印出 Work 活條目數之增減分解（新增、轉墓碑、消失），數目對不上必有消失 id。
    vanished, base_note = [], ''
    import subprocess
    _r = subprocess.run(['git', '-C', ROOT, 'rev-parse', '--verify', '-q', a.base + '^{commit}'], capture_output=True, text=True)
    if _r.returncode == 0:
        _bl = subprocess.run(['git', '-C', ROOT, '-c', 'core.quotepath=off', 'ls-tree', '-r', '--name-only', a.base, '--', 'Work', 'Entity'],
                             capture_output=True, text=True).stdout.split('\n')
        _ids = lambda files: {os.path.basename(f).split('-')[0] for f in files if f.endswith('.json')}
        _base_ids = _ids(_bl)
        _cur_ids = _ids(glob.glob(os.path.join(ROOT, 'Work', '*', '*', '*', '*.json')) + glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')))
        vanished = sorted(_base_ids - _cur_ids)
        base_note = f'（基線 {a.base}：{len(_base_ids)} 個 Work／Entity id，現有 {len(_cur_ids)}，新增 {len(_cur_ids - _base_ids)}）'
    else:
        base_note = f'（基線 {a.base} 解析不到，略過）'
    print(f'相對基線消失之 id（被併須留墓碑檔，不得直接刪） {len(vanished)} {base_note}')
    for r in vanished[:10]: print('  消失', r)
    print(f'墓碑目標不存在或亦為墓碑 {len(bad_tomb_target)}')
    for r in bad_tomb_target[:10]: print('  墓碑目標', r)
    print(f'墓碑檔不在 index/works {len(bad_tomb_unindexed)}')
    for r in bad_tomb_unindexed[:10]: print('  墓碑未入索引', r)
    print(f'分類類檔不合（classify check） {len(bad_cls_members)}')
    for r in bad_cls_members[:10]: print('  分類類檔', r)
    _cv2_cnt = collections.Counter(r[3] for r in _cv2_rows)
    print(f'舊格式殘留（check_v2；--strict 計入 FAIL） {len(_cv2_rows)}'
          + ('  ' + ' '.join(f'{k}:{v}' for k, v in sorted(_cv2_cnt.items())) if _cv2_rows else ''))
    print(f'專名子類型不合（dynasty／reign／office／place；ERROR 計入 FAIL） {len(bad_subtype)}'
          + (f'  條目數 {dict(subtype_n)}' if subtype_n else ''))
    for r in bad_subtype[:10]: print('  專名', r[1], r[3], r[4], r[5])
    print(f'專名子類型 WARN（僅報，不入 FAIL） {len(subtype_warn)}')
    print(f'provenance 形狀不合    {len(bad_prov)}')
    for r in bad_prov[:10]: print('  provenance', r)
    print(f'edition_type 不在詞表  {len(bad_et)}')
    for r in bad_et[:10]: print('  edition_type', r)
    print(f'physical_description 形狀不合 {len(bad_pd)}')
    for r in bad_pd[:10]: print('  physical_description', r)
    print(f'base_edition 形狀不合  {len(bad_be)}')
    for r in bad_be[:10]: print('  base_edition', r)
    print(f'entity.dates 不合法 {len(bad_dates)}')
    for r in bad_dates[:10]: print('  dates', r)
    print(f'entity.external_ids 不合法 {len(bad_extids)}')
    for r in bad_extids[:10]: print('  external_ids', r)
    print(f'count 形狀不對          {len(bad_count)}')
    for r in bad_count[:10]: print('  count 壞', r)
    print(f'todo 形狀不合           {len(bad_todo)}')
    for r in bad_todo[:10]: print('  todo 壞', r)
    print(f'review 形狀不合         {len(bad_review)}')
    for r in bad_review[:10]: print('  review 壞', r)
    # S5（overview#189）stale_ref 推廣：下三項是既有欄位之內容漂移／機構名簡繁不一，
    # 屬歷史遺留（本卡「不改任何已有字段的值」），故只報數、落 known-issues，不入 FAIL 之列，
    # 亦不隨 --strict 升級——否則本閘會為與本卡無關的既有數據把全庫判死。
    print(f'related_works[].title 漂移（僅報，不入 FAIL） {len(stale_related)}')
    print(f'provenance[].institution 簡體字（僅報，不入 FAIL） {len(bad_inst)}')
    # overview#217（据 #214 check5）：dynasty 與生卒世纪粗篩，史學慣例假陽性率高（實測約 355/360），
    # 只作監控用之報告項，不入 FAIL，亦不隨 --strict 升級。
    print(f'dynasty 與生卒世纪不合（僅報，不入 FAIL） {len(bad_dynasty_century)}')
    # 2026-09-07 lane-E 所報：賬曾三度被 pushmain 之 --ours 吞掉，共遺落 492 筆而無人察覺
    # ——被吞者無聲、吞人者亦無聲，**只有第三方比對才看得見**。故以水位線守之。
    _ledger_bad = False
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import verdicts as _vd
        _n, _prev, _bad = _vd.highwater()
        print(f'裁決賬（只增不減）  {_n}' + (f'  **退步！曾見 {_prev}**' if _bad else ''))
        _ledger_bad = _bad
    except Exception as _e:
        # 2026-09-07 lane-E 覆驗本閘所報之漏一：原作 _ledger_bad = False，**查不成就算過**。
        # 而這個閘所守的正是「無人會自己發現」的那一類——匯入失敗、賬檔權限出錯，
        # 任一情形都會讓它印一行字然後放行，且那行字混在七行正常輸出裡，
        # pushmain.sh 只 grep -q OK，看不見。**守門者查不成即應算敗。**
        _ledger_bad = True
        print(f'裁決賬（只增不減）  **查不成，算敗**：{_e}')
    for r in (drift_w[:10] + drift_e[:10]): print('  漂移', r)
    if missing and a.why:
        # 「索引缺記錄檔」多半是併條刪檔而未清索引（坑 41）。逕查該 id 之最後刪除提交，
        # 各道遂能自判「是我的批次沒清乾淨」抑或「別人的病，該報協調者」。
        import subprocess
        print('  ── 缺檔之由（--why）──')
        for wid in missing[:20]:
            c = subprocess.run(['git', '-c', 'core.quotePath=false', 'log', '--all',
                                '--diff-filter=D', '--format=%h %an %s', '-1',
                                '--', f'Work/*/*/*/{wid}-*.json'],
                               capture_output=True, text=True).stdout.strip()
            print(f'  {wid}  {c or "（未見刪除提交——檔名或曾改，先查索引 path 是否過時）"}')
        if len(missing) > 20: print(f'  …另有 {len(missing)-20} 條')
    if a.strict:
        for r in dangle_w[:10]: print('  懸空', r)
    # 賬之退步一律算敗（不分 strict）——這正是無人會自己發現的那一類（坑 68、坑 70）
    # 2026-09-07：`entity.works 重複項` 自即日納入 --strict 之成敗（清零後方納，免得未清前卡住各道）。
    # 此病 lane-B 所發（坑 69）：本檔 entity 側原以 set 收 works，同一 work_id 列兩次一入集合即消失
    # ——**檢查所用的容器把要檢查的病吃掉了**，而閘天天綠。清得 24 處（22 整項全同、2 有無 role 之別）。
    bad = (_ledger_bad or missing or bad_merged_in or vanished or bad_tomb_target or bad_tomb_unindexed or drift_w or drift_e or bad_cls_members or bad_prov or bad_dates or bad_extids or bad_count
           or bad_subtype or bad_et or bad_pd or bad_be or bad_todo or bad_review
           or (a.strict and (dangle_w or _cv2_rows)))
    print('FAIL' if bad else 'OK')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
