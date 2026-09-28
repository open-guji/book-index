#!/usr/bin/env python3
"""每批之後必跑之驗（qa-sweep 硬門禁）。

  python3 .claude/qa/verify.py            # 全庫：索引漂移必須為 0；懸空計數與基線比
  python3 .claude/qa/verify.py --strict   # 懸空亦須為 0（收工前）

輸出五個數：works 索引漂移（period/loss_status/title/subtype/author/dynasty/role；dynasty 取頂層，無則 authors[0]）、
entities 索引漂移、work 側懸空引用、entity.works 懸空、單向邊（人指書而書不指人）。
漂移不為 0 即失敗（exit 1）——改了記錄而未回寫索引，或改了索引而未改記錄。
"""
import argparse, collections, glob, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')): out.update(json.load(open(f)))
    return out

def load_classific_vocab():
    """classific.json：l1s、(l1,l2) 集合、(l1,l2,l3) 集合、(l1,l2,l3,l4) 集合。"""
    rows = json.load(open(os.path.join(ROOT, 'classific.json'), encoding='utf-8'))
    l1s, l12, l123, l1234 = set(), set(), set(), set()
    for r in rows:
        l1, l2, l3, l4 = r['cata_l1'], r['cata_l2'], r.get('cata_l3'), r.get('cata_l4')
        l1s.add(l1); l12.add((l1, l2))
        if l3: l123.add((l1, l2, l3))
        if l4: l1234.add((l1, l2, l3, l4))
    return l1s, l12, l123, l1234

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
    by, dy = d.get('birth_year'), d.get('death_year')
    if birth is not None and by is not None and birth != by:
        return f'dates.birth={birth} 与 birth_year={by} 不一致'
    if death is not None and dy is not None and death != dy:
        return f'dates.death={death} 与 death_year={dy} 不一致'
    return None

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

MEMBER_TYPES = {'Work', 'Book', 'Collection', 'mixed'}

def derive_member_type(d):
    """Collection._member_type：由 `books`／`contained_works` 是否非空機械推出（S3b，overview#171）。
    `contains`（結構組成部分，非平列成員，見 SCHEMA collection 一節）不計入。
    只 books 非空→'Book'；只 contained_works 非空→'Work'；兩者皆非空→'mixed'；兩者皆空→None（無可推之依據）。"""
    has_b = bool(d.get('books'))
    has_w = bool(d.get('contained_works'))
    if has_b and has_w: return 'mixed'
    if has_b: return 'Book'
    if has_w: return 'Work'
    return None

def member_type_ok(d):
    """_member_type 若寫了：須落在值域內，且須等於重新推導之值（派生欄位，手寫無用）。"""
    v = d.get('_member_type')
    if v is None: return True
    if v not in MEMBER_TYPES: return False
    return v == derive_member_type(d)

def classification_ok(c, vocab):
    l1s, l12, l123, l1234 = vocab
    l1, l2, l3, l4 = c.get('l1') or '', c.get('l2') or '', c.get('l3') or '', c.get('l4') or ''
    if not l1: return l2 == '' and l3 == '' and l4 == ''
    if l1 not in l1s: return False
    if not l2: return l3 == '' and l4 == ''
    if (l1, l2) not in l12: return False
    if not l3: return l4 == ''
    if (l1, l2, l3) not in l123: return False
    if not l4: return True
    return (l1, l2, l3, l4) in l1234

def provenance_ok(prov):
    """Book.provenance：數組，每項 institution 非空字符串、call_number 為字符串。"""
    if not isinstance(prov, list): return False
    for item in prov:
        if not isinstance(item, dict): return False
        inst = item.get('institution')
        if not isinstance(inst, str) or not inst.strip(): return False
        if not isinstance(item.get('call_number', ''), str): return False
    return True

EDITION_TYPES = {'刻本', '抄本', '稿本', '活字本', '石印本', '鉛印本', '影印本', '套印本', '拓本', '其他'}

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

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--why', action='store_true', help='「索引缺記錄檔」時印出各 id 之最後刪除提交（坑 41）')
    ap.add_argument('--strict', action='store_true'); a = ap.parse_args()
    IW, IB, IE = idx('works'), idx('books'), idx('entities')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    ALL = set(IW) | set(IB) | set(IE) | set(IC)
    CVOCAB = load_classific_vocab()
    bad_cls = []
    drift_w, dangle_w, missing, back = [], [], [], {}
    bad_prov = []
    bad_et, bad_pd = [], []
    for bid, ie in IB.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(bid); continue
        d = json.load(open(p))
        prov = d.get('provenance')
        if prov is not None and not provenance_ok(prov):
            bad_prov.append(bid)
        et = d.get('edition_type')
        if et is not None and not edition_type_ok(et):
            bad_et.append((bid, et))
        pd_ = d.get('physical_description')
        if pd_ is not None and not physical_description_ok(pd_):
            bad_pd.append(bid)
    for wid, ie in IW.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(wid); continue
        d = json.load(open(p))
        c = d.get('classification')
        if c and not classification_ok(c, CVOCAB):
            bad_cls.append((wid, c.get('l1'), c.get('l2'), c.get('l3'), c.get('l4')))
        for f in ('period', 'loss_status', 'title', 'subtype'):
            x, y = ie.get(f), d.get(f)
            if x is None and y is None: continue
            if x != y: drift_w.append((wid, f, x, y))
        au = d.get('authors') or []; a0 = au[0] if au else {}
        nz = lambda v: None if v in ('', None) else v
        want = {'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
                'dynasty': nz(d.get('dynasty')) if nz(d.get('dynasty')) is not None else nz(a0.get('dynasty'))}
        for f, y in want.items():
            if nz(ie.get(f)) != y: drift_w.append((wid, f, ie.get(f), y))
        for r in (d.get('related_works') or []):
            if r.get('id') and r['id'] not in ALL: dangle_w.append((wid, 'related_works', r['id']))
        for b in (d.get('books') or []):
            if b not in ALL: dangle_w.append((wid, 'books', b))
        back[wid] = {x.get('entity_id') for x in au if x.get('entity_id')}
        for x in au:
            if x.get('entity_id') and x['entity_id'] not in IE: dangle_w.append((wid, 'authors.entity_id', x['entity_id']))
    drift_e, dangle_e, fwd, dup_e, bad_dates, bad_extids = [], [], {}, [], [], []
    for eid, ie in IE.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(eid); continue
        d = json.load(open(p))
        for f in ('primary_name', 'dynasty', 'birth_year', 'death_year', 'period'):
            x, y = ie.get(f), d.get(f)
            if x is None and y is None: continue
            if x != y: drift_e.append((eid, f, x, y))
        err = dates_ok(d)
        if err: bad_dates.append((eid, err))
        err = external_ids_ok(d)
        if err: bad_extids.append((eid, err))
        if ie.get('path') != d.get('path', ie.get('path')): pass
        # 2026-09-07 lane-B 所報：本迴圈原以 set 收 works，**同一 work_id 列兩次者一入集合即消失**
        # ——檢查所用之資料結構本身把一類缺陷吃掉了（全庫十一個 entity 有此病，清聖祖十二處）。
        # 今先以 list 收，數過重複再入集合。**凡以 set／dict 收待驗之物者，須先問
        # 「這個容器會不會把我要驗的那種病吃掉」**——坑 61「不在 A 之索引裡不等於不存在」之另一面。
        seen_e = []
        for w in (d.get('works') or []):
            if w.get('work_id') and w['work_id'] not in IW: dangle_e.append((eid, w['work_id']))
            elif w.get('work_id'):
                seen_e.append(w['work_id']); fwd.setdefault(eid, set()).add(w['work_id'])
        for wid, c in collections.Counter(seen_e).items():
            if c > 1: dup_e.append((eid, wid, c))
    # 2026-09-07 lane-B 所報之二：Collection.contained_works[].id 從來無人驗——
    # 併條而漏改此處，斷了無人知。今併入「work 側懸空引用」一項。
    # S3（Collection.count 吸收，overview#140）：count 若寫了就必須形狀對、有依據、非全空。
    bad_count = []
    bad_member_type = []
    for cid, ie in IC.items():
        p2 = ie.get('path')
        if not p2 or not os.path.exists(p2): continue
        try: dc = json.load(open(p2))
        except Exception: continue
        for cw in (dc.get('contained_works') or []):
            x = cw.get('id') or cw.get('work_id') if isinstance(cw, dict) else cw
            if isinstance(x, str) and x not in IW and x not in IC: dangle_w.append((cid, 'contained_works', x))
        cnt = dc.get('count')
        if cnt is not None and not count_ok(cnt): bad_count.append(cid)
        if not member_type_ok(dc): bad_member_type.append((cid, dc.get('_member_type'), derive_member_type(dc)))
    oneway = [(e, w) for e, ws in fwd.items() for w in ws if e not in back.get(w, set())]
    print(f'索引檔缺記錄檔        {len(missing)}')
    print(f'works 索引漂移        {len(drift_w)}')
    print(f'entities 索引漂移     {len(drift_e)}')
    print(f'work 側懸空引用       {len(dangle_w)}')
    print(f'entity.works 懸空     {len(dangle_e)}')
    print(f'entity.works 重複項  {len(dup_e)}')
    print(f'單向邊 人指書書不指人 {len(oneway)}')
    print(f'classification 不在詞表 {len(bad_cls)}')
    for r in bad_cls[:10]: print('  詞表外', r)
    print(f'provenance 形狀不合    {len(bad_prov)}')
    for r in bad_prov[:10]: print('  provenance', r)
    print(f'edition_type 不在詞表  {len(bad_et)}')
    for r in bad_et[:10]: print('  edition_type', r)
    print(f'physical_description 形狀不合 {len(bad_pd)}')
    for r in bad_pd[:10]: print('  physical_description', r)
    print(f'entity.dates 不合法 {len(bad_dates)}')
    for r in bad_dates[:10]: print('  dates', r)
    print(f'entity.external_ids 不合法 {len(bad_extids)}')
    for r in bad_extids[:10]: print('  external_ids', r)
    print(f'count 形狀不對          {len(bad_count)}')
    for r in bad_count[:10]: print('  count 壞', r)
    print(f'_member_type 不合／過期 {len(bad_member_type)}')
    for r in bad_member_type[:10]: print('  _member_type 壞', r)
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
        for r in dangle_w[:10] + dangle_e[:10]: print('  懸空', r)
        for r in oneway[:10]: print('  單向', r)
    # 賬之退步一律算敗（不分 strict）——這正是無人會自己發現的那一類（坑 68、坑 70）
    # 2026-09-07：`entity.works 重複項` 自即日納入 --strict 之成敗（清零後方納，免得未清前卡住各道）。
    # 此病 lane-B 所發（坑 69）：本檔 entity 側原以 set 收 works，同一 work_id 列兩次一入集合即消失
    # ——**檢查所用的容器把要檢查的病吃掉了**，而閘天天綠。清得 24 處（22 整項全同、2 有無 role 之別）。
    bad = (_ledger_bad or missing or drift_w or drift_e or bad_cls or bad_prov or bad_dates or bad_extids or bad_count
           or bad_et or bad_pd or bad_member_type
           or (a.strict and (dangle_w or dangle_e or oneway or dup_e)))
    print('FAIL' if bad else 'OK')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
