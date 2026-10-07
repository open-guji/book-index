#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""併條（Work 併 Work），並把善後一次辦完。schema-v2 版（2026-10-07，overview#459 F6-3）。

**所以立此**：坑 41 說善後三件、坑 61 補第四、坑 64 第五，「每次以為數全了就又冒出一處」。
逐次手辦必有遺漏，故把善後寫成一支，由 `backrefs.py` 那張「誰指著我」之表驅動。

    python3 .claude/qa/mergework.py --keeper <id> --drop <id>[,<id>...] \
        --rule <判準> --why <所以然> [--root <倉>] [--apply]

**不加 `--apply` 即為乾跑**：只印逐欄之 diff 與將要動的每一處，不寫任何檔。
坑 67 之戒——「做去重之前，先把兩個重複項並排逐欄 diff 一遍」——故乾跑是預設，
且 diff 印的是**整節所有欄位**，不是我挑的那幾欄。

**schema-v2 之變**（SCHEMA〈〇〉）：源檔裡一條關係只存一側，反向由 build 生成。故：
- 不再寫 `Work.books`、`Entity.works`、`Collection.contained_works`、`_edition_count`、`index/`
  （這些或已不在源檔，或由 `build/build_derived.py` 生成；併後跑 build 即得）；
- 被併者**自己存著的出邊**（`related_works`：它 studies／part_of／related 誰）是該關係唯一的
  存儲，併時必搬到 keeper，否則隨刪檔丟失；搬時照規範方向落筆，`related` 落小 id 側；
- 他條指被併者之處，只改存儲一側的欄（見 `backrefs.PLACES`）；
- 被併者的分類成員行改指 keeper（keeper 已有歸屬則刪被併者之行，類不同者報出）。

善後各件：
  1 著錄併入 keeper（indexed_by，**整節為鍵**去重，不取子集——坑 67）
  2 被併者之出邊（related_works）搬到 keeper，按規範方向／小 id 規則落筆、去自指、去重、note 拼接
  3 他條之 related_works 指被併者者改指 keeper；`related` 改指後若存儲側不再是小 id，搬到 keeper 側
  4 Book／Collection 之 work_id 改指 keeper
  5 他條著錄之 source_bid／in_note_of（被併者是志書時）、Book.base_edition.work_id、
    Collection.contains[].work_id 改指 keeper
  6 分類成員行（classification/<法>/members）改指 keeper
  7 keeper 之 `merged_in` **填欄位**，不只寫散文（坑 64）
  8 被併者獨有之其餘欄位（contained_in／period／resources …）搬入 keeper；
    兩邊皆有且值不同者**不搬**，只印出報告，須人斷孰是
  9 keeper 之 related_works 刪自指項
 10 被併者撰人帶 entity_id 而 keeper 沒有者：**報**（人物頁的作品列表由 authors 反查，
    併後該人少此條；若是同一撰人之異寫，應先把 entity_id 補進 keeper），不擋
 11 刪被併者之檔。之後跑 `build/build_derived.py --write-index`（索引、派生欄由它生成）
"""
import json, os, sys, glob, argparse, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'build'))
import backrefs                      # noqa: E402
import v2common as V                 # noqa: E402

# 兩側皆真即真的准留源欄（SCHEMA〈十〉例外）
BOOL_OR_FIELDS = {'_has_text', '_has_collated'}
# 已各有專屬善後步驟或明訂不由本工具自動搬的欄：
#   id/type/title/path/revision/revised_at 結構性；indexed_by/merged_in/additional_titles 各有步驟；
#   authors 屬 B 字段族，併條不動撰人著錄本身；description/ai_note 併後語意須人改；
#   related_works 由步驟 2 按規範方向搬；merged_into 是墓碑欄
MERGE_SKIP_FIELDS = {
    'id', 'type', 'title', 'path', 'revision', 'revised_at', 'schema_version', 'updated_at',
    'indexed_by', 'merged_in', 'merged_into', 'additional_titles',
    'authors', 'description', 'ai_note', 'related_works',
}
# 舊格式欄：源檔不該有，有也不搬（check_v2 該擋）
LEGACY_FIELDS = {'books', 'classification', 'has_text', 'has_image', 'has_collated',
                 'promoted_to', 'promoted_at'}


# ---------- 讀寫 ----------
def find(typ, rid, root=None):
    root = root or ROOT
    for pat in ('%s-*.json' % rid, '%s.json' % rid):
        for p in glob.glob(os.path.join(root, typ, '*', '*', '*', pat)):
            return p
    return None


def load(p):
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    return d, V.detect_format(raw, d)


def save(p, d, fmt):
    with open(p, 'w', encoding='utf-8') as f:
        f.write(V.dump(d, fmt))


def addnote(d, note):
    old = d.get('ai_note') or ''
    d['ai_note'] = (old.rstrip() + '\n\n' + note) if old.strip() else note


def rel(p, root=None):
    return os.path.relpath(p, root or ROOT)


# ---------- 純函式（可單測） ----------
def diff_fields(keeper, drops):
    """逐欄並排。坑 67：印所有欄位之並集，不挑。"""
    keys = set(keeper)
    for d in drops:
        keys |= set(d)
    out = []
    for k in sorted(keys):
        vals = [keeper.get(k)] + [d.get(k) for d in drops]
        same = all(json.dumps(v, ensure_ascii=False, sort_keys=True) ==
                   json.dumps(vals[0], ensure_ascii=False, sort_keys=True) for v in vals)
        mark = '  ' if same else '**'
        out.append('%s %-18s %s' % (mark, k, ' | '.join(
            json.dumps(v, ensure_ascii=False)[:150] for v in vals)))
    return '\n'.join(out)


def node_key(n):
    """整節為鍵——所有欄位，不取子集（坑 67）。"""
    return json.dumps(n, ensure_ascii=False, sort_keys=True)


def _empty(v):
    return v is None or v == '' or v == [] or v == {}


def plan_scalar_merge(keeper, dps):
    """被併者有而 keeper 無之欄位搬過去；兩邊皆有且不同者不搬，只報告。
    list 取兩邊並集去重（整項 json 為鍵）；`_has_text`／`_has_collated` 取或；
    純量 keeper 為空即搬，否則不同即報衝突。回 (moved, conflicts, new_values)。冪等。"""
    moved, conflicts, new_values = [], [], {}
    for d, _p, dd, _fmt in dps:
        for k, v in dd.items():
            if k in MERGE_SKIP_FIELDS or k in LEGACY_FIELDS or _empty(v):
                continue
            if k.startswith('_') and k not in BOOL_OR_FIELDS:
                continue                      # 派生欄不搬（源檔本不該有）
            kv = new_values.get(k, keeper.get(k))
            if k in BOOL_OR_FIELDS:
                if v and not kv:
                    new_values[k] = True
                    moved.append((d, k, v))
                continue
            if _empty(kv):
                new_values[k] = v
                moved.append((d, k, v))
            elif isinstance(kv, list) and isinstance(v, list):
                have = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in kv}
                added = [x for x in v if json.dumps(x, ensure_ascii=False, sort_keys=True) not in have]
                if added:
                    new_values[k] = kv + added
                    moved.append((d, k, added))
            elif kv != v:
                conflicts.append((d, k, kv, v))
    return moved, conflicts, new_values


def clean_self_related(related, keeper_id, drop_ids):
    """去掉 keeper.related_works 中指向自己或指向被併者之項。回 (新清單, 被去之項)。"""
    gone = set(drop_ids) | {keeper_id}
    out, removed = [], []
    for r in (related or []):
        (removed if V.rel_target(r) in gone else out).append(r)
    return out, removed


def add_edge(items, tgt, relation, note=None):
    """把一條規範邊加進某記錄的 related_works（就地）；同 (id, relation) 已有則拼 note。
    回 True 表有改動。"""
    for r in items:
        if V.rel_target(r) == tgt and V.RENAME.get(r.get('relation'), r.get('relation')) == relation:
            merged = V.merge_notes([r.get('note'), note])
            if merged and merged != r.get('note'):
                r['note'] = merged
                return True
            return False
    item = {'id': tgt, 'relation': relation}
    if note:
        item['note'] = note
    items.append(item)
    return True


def plan_edges(keeper_id, drop_ids, drop_recs, back, works):
    """步驟 2／3：回 {記錄 id: [(動作, 項)]}，動作 ∈ add（加規範邊）／retarget（改指）／remove（刪項）。
    works: {id: dict} 供讀他條現況。只算不寫。"""
    gone = set(drop_ids) | {keeper_id}
    ops = collections.defaultdict(list)
    # 2 被併者的出邊 → 規範落筆
    for d in drop_ids:
        for r in (drop_recs[d].get('related_works') or []):
            tgt, relw = V.rel_target(r), r.get('relation')
            if not tgt or tgt in gone:
                continue
            s, t, rr = V.canon_edge(keeper_id, tgt, relw)
            ops[s].append(('add', {'id': t, 'relation': rr, 'note': r.get('note'), 'from': d}))
    # 3 他條指被併者
    for d in drop_ids:
        for where, src, _det in back.get(d, []):
            if where != 'Work.related_works' or src in gone:
                continue
            for r in (works.get(src, {}).get('related_works') or []):
                if V.rel_target(r) != d:
                    continue
                s, t, rr = V.canon_edge(src, keeper_id, r.get('relation'))
                if s == src:
                    ops[src].append(('retarget', {'old': d, 'id': keeper_id, 'relation': r.get('relation')}))
                else:   # related：改指後小 id 在 keeper 側 → 搬到 keeper
                    ops[src].append(('remove', {'id': d, 'relation': r.get('relation')}))
                    ops[s].append(('add', {'id': t, 'relation': rr, 'note': r.get('note'), 'from': src}))
    return ops


def apply_edge_ops(rec, ops):
    """把 plan_edges 給某記錄的動作套到該記錄（就地）。回改動數。"""
    items = list(rec.get('related_works') or [])
    n = 0
    for act, it in ops:
        if act == 'retarget':
            keep = []
            for r in items:
                if V.rel_target(r) == it['old'] and r.get('relation') == it['relation']:
                    k = 'id' if 'id' in r else 'work_id'
                    nr = {kk: vv for kk, vv in r.items() if kk not in ('id', 'work_id', 'title')}
                    nr = dict({'id': it['id']}, **nr) if k == 'id' else dict(nr, work_id=it['id'])
                    # 改指後與既有項同 (id, relation) 則併 note
                    dup = [x for x in keep if V.rel_target(x) == it['id'] and x.get('relation') == nr.get('relation')]
                    if dup:
                        m = V.merge_notes([dup[0].get('note'), nr.get('note')])
                        if m:
                            dup[0]['note'] = m
                    else:
                        keep.append(nr)
                    n += 1
                else:
                    keep.append(r)
            items = keep
        elif act == 'remove':
            before = len(items)
            items = [r for r in items if not (V.rel_target(r) == it['id'] and r.get('relation') == it['relation'])]
            n += before - len(items)
        elif act == 'add':
            if add_edge(items, it['id'], it['relation'], it.get('note')):
                n += 1
    if items:
        rec['related_works'] = items
    else:
        rec.pop('related_works', None)
    return n


def retarget_ids(rec, old, new):
    """步驟 5：著錄 source_bid／in_note_of、base_edition.work_id、contains[].work_id、
    related_collections 等存儲側欄裡的 old → new。回改動數。不碰舊格式欄。"""
    n = 0
    for fld in ('indexed_by', 'emendated_by'):
        for x in (rec.get(fld) or []):
            for k in ('source_bid', 'in_note_of'):
                if isinstance(x, dict) and x.get(k) == old:
                    x[k] = new; n += 1
    for x in (rec.get('base_edition') or []):
        if isinstance(x, dict) and x.get('work_id') == old:
            x['work_id'] = new; n += 1
    for x in (rec.get('contains') or []):
        if isinstance(x, dict) and x.get('work_id') == old:
            x['work_id'] = new; n += 1
    for fld in ('related_books', 'related_collections'):
        v = rec.get(fld)
        if isinstance(v, list) and old in v:
            rec[fld] = [new if x == old else x for x in v]; n += 1
    if rec.get('work_id') == old:
        rec['work_id'] = new; n += 1
    return n


def members_dump(node, rows):
    """與 build/migrate_v2.members_dump 同式：一行一條、按 work_id 排序。"""
    body = ',\n'.join('    ' + json.dumps(r, ensure_ascii=False) for r in rows)
    return '{\n  "node": %s,\n  "members": [\n%s\n  ]\n}\n' % (json.dumps(node), body)


def plan_classification(root, keeper_id, drop_ids):
    """步驟 6：回 (寫檔 {rel: (node, rows)}, 報告[])。互斥分類法下 keeper 已有歸屬者刪被併者之行，
    類不同者報出；keeper 無歸屬者被併者之行改指 keeper（同類多被併者只留一行）。"""
    writes, notes = {}, []
    schemes = {}
    sp = os.path.join(root, 'classification', 'schemes.json')
    if os.path.exists(sp):
        schemes = {s['id']: s for s in json.load(open(sp, encoding='utf-8'))}
    for sdir in sorted(glob.glob(os.path.join(root, 'classification', '*', 'members'))):
        scheme = os.path.basename(os.path.dirname(sdir))
        exclusive = schemes.get(scheme, {}).get('exclusive', True)
        files = {}
        for p in sorted(glob.glob(os.path.join(sdir, '*.json'))):
            d = json.load(open(p, encoding='utf-8'))
            files[rel(p, root)] = (d.get('node'), [list(r) for r in d.get('members') or []])
        keeper_nodes = {n for f, (n, rows) in files.items() if any(r[0] == keeper_id for r in rows)}
        for f, (node, rows) in files.items():
            if not any(r[0] in drop_ids for r in rows):
                continue
            new = []
            for r in rows:
                if r[0] not in drop_ids:
                    new.append(r); continue
                if exclusive and keeper_nodes and node not in keeper_nodes:
                    notes.append('分類（%s）：被併者 %s 在 %s，keeper 在 %s——刪被併者之行，留 keeper 的；類不同須人看'
                                 % (scheme, r[0], node, '、'.join(sorted(keeper_nodes))))
                    continue
                if any(x[0] == keeper_id for x in new) or (exclusive and node in keeper_nodes):
                    continue           # keeper 已在此類
                new.append([keeper_id] + r[1:])
                keeper_nodes.add(node)
            new.sort(key=lambda x: x[0])
            writes[f] = (node, new)
    return writes, notes


# ---------- 主程 ----------
def main(argv=None):
    global ROOT
    ap = argparse.ArgumentParser(description='併條並辦善後（schema-v2）')
    ap.add_argument('--keeper', required=True)
    ap.add_argument('--drop', required=True, help='逗號分隔')
    ap.add_argument('--rule', required=True, help='判準——第一等公民，無 rule 則日後無從整批翻案')
    ap.add_argument('--why', required=True)
    ap.add_argument('--by', default='lane-B')
    ap.add_argument('--root', default=ROOT, help='數據倉根（預設本倉）')
    ap.add_argument('--at', help='merged_in.at 之時間（預設現在；測試用）')
    ap.add_argument('--apply', action='store_true', help='真寫；不加即乾跑')
    a = ap.parse_args(argv)
    ROOT = root = os.path.abspath(a.root)

    drops = [x for x in a.drop.split(',') if x]
    if a.keeper in drops:
        raise SystemExit('keeper 不得在被併者之列')
    kp = find('Work', a.keeper, root)
    if not kp:
        raise SystemExit('keeper 檔不存在：%s' % a.keeper)
    keeper, kfmt = load(kp)
    dps = []
    for d in drops:
        p = find('Work', d, root)
        if not p:
            raise SystemExit('被併者檔不存在：%s（先查坑 64：曾建而後刪 vs 從未建出）' % d)
        dd, dfmt = load(p)
        dps.append((d, p, dd, dfmt))
    drop_recs = {d: dd for d, _, dd, _ in dps}

    print('== 逐欄 diff（keeper | %s）==' % ' | '.join(drops))
    print(diff_fields(keeper, [x[2] for x in dps]))

    back = backrefs.scan(root)
    plan = collections.defaultdict(list)
    gone = set(drops) | {a.keeper}

    # 1 著錄
    have = {node_key(n) for n in (keeper.get('indexed_by') or [])}
    add_nodes = []
    for d, p, dd, _ in dps:
        for n in (dd.get('indexed_by') or []):
            if node_key(n) not in have:
                have.add(node_key(n)); add_nodes.append((d, n))
                plan['著錄移入 keeper'].append((d, n.get('source'), n.get('title_info')))
            else:
                plan['著錄·整節全同故不重複移'].append((d, n.get('source')))

    # 2/3 關係
    srcs = {src for d in drops for w, src, _ in back.get(d, []) if w == 'Work.related_works'}
    works = {}
    for i in srcs | {a.keeper}:
        p = kp if i == a.keeper else find('Work', i, root)
        if p:
            works[i] = keeper if i == a.keeper else load(p)[0]
    edge_ops = plan_edges(a.keeper, drops, drop_recs, back, works)
    for i, ops in sorted(edge_ops.items()):
        for act, it in ops:
            plan['related_works %s（%s）' % (act, '本 keeper' if i == a.keeper else '他條')].append((i, it))
    missing_edge_targets = [i for i in edge_ops if i != a.keeper and i not in works
                            and not find('Work', i, root)]
    for i in missing_edge_targets:
        plan['**關係落筆之條不在本倉（跨倉？）——須人看**'].append((i,))

    # 4/5 存儲側引用改指
    ref_fix = collections.defaultdict(set)      # (type, id) -> {drop}
    handled = {'Work.related_works', 'Work.authors.entity_id'}
    unhandled = []
    for d in drops:
        for where, src, det in back.get(d, []):
            if where in handled or src in gone:
                continue
            if where.endswith('merged_in'):
                plan['他條之併條賬指著被併者（墓誌，不改）'].append((src, where, det))
                continue
            if where.split('.')[0] in backrefs.TYPES and where in backrefs.LEGACY:
                plan['**舊格式欄指著被併者（不改寫；先遷移）**'].append((src, where))
                continue
            if where == 'classification.members':
                continue
            typ = where.split('.')[0]
            if typ in backrefs.TYPES and any(where.startswith(x) for x in (
                    'Book.work_id', 'Collection.work_id', '%s.indexed_by' % typ, '%s.emendated_by' % typ,
                    'Book.base_edition', 'Collection.contains', 'Book.related_', 'Collection.related_')):
                ref_fix[(typ, src)].add(d)
                plan['%s 改指 keeper' % where].append((src, d))
            else:
                unhandled.append((where, src, det))
    for w, s, det in unhandled:
        plan['**他處指著被併者而本工具不辦——須人看**'].append((w, s, det))

    # 6 分類
    cls_writes, cls_notes = plan_classification(root, a.keeper, drops)
    for f, (node, rows) in sorted(cls_writes.items()):
        plan['分類成員行改指／刪（%s）' % f].append((node, len(rows)))
    for n in cls_notes:
        plan['**%s**' % n].append(())

    # 8 欄位
    moved, conflicts, new_values = plan_scalar_merge(keeper, dps)
    for d, k, v in moved:
        plan['欄位搬遷（keeper 原無）'].append((d, k, v))
    for d, k, kv, v in conflicts:
        plan['**欄位衝突（兩邊皆有且不同，不搬，須人看）**'].append((d, k, kv, v))
    cids = collections.Counter(V.ref_id(c) for c in (new_values.get('contained_in') or keeper.get('contained_in') or []))
    for c, n in cids.items():
        if n > 1:
            plan['**contained_in 同一叢編出現 %d 項（冊次不同？）——須人看**' % n].append((c,))
    for d, _, dd, _ in dps:
        for k in sorted(LEGACY_FIELDS & set(dd)):
            plan['被併者帶舊格式欄（不搬）'].append((d, k))

    # 9 自指
    _, self_rel = clean_self_related(keeper.get('related_works'), a.keeper, drops)
    for r in self_rel:
        plan['keeper related_works 刪自指項'].append((r,))

    # 10 撰人 entity
    kent = {x.get('entity_id') for x in (keeper.get('authors') or []) if isinstance(x, dict) and x.get('entity_id')}
    for d, _, dd, _ in dps:
        for au in (dd.get('authors') or []):
            if isinstance(au, dict) and au.get('entity_id') and au['entity_id'] not in kent:
                plan['**被併者撰人帶 entity_id 而 keeper 無（併後人物頁少此條）——須人看**'].append(
                    (d, au.get('name'), au.get('role'), au['entity_id']))

    dtxt = (keeper.get('description') or {}).get('text') or '' if isinstance(keeper.get('description'), dict) else ''
    if any(w in dtxt for w in ('別無他證', '一志著錄', '惟《')):
        plan['**keeper description 有「別無他證／惟某志著錄」之語，併入新源後即失實——須人改**'].append((a.keeper,))

    print('\n== 將動之處 ==')
    if not plan:
        print('   （無）')
    for k in sorted(plan):
        print('  %s  ×%d' % (k, len(plan[k])))
        for it in plan[k][:12]:
            print('      %s' % (it,))

    if not a.apply:
        print('\n[乾跑] 未寫任何檔。覆核無誤後加 --apply。')
        return 0
    if missing_edge_targets:
        raise SystemExit('拒絕：關係須落筆於本倉不存在之條 %s' % missing_edge_targets)

    now = a.at or (datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z')
    # keeper
    for k, v in new_values.items():
        keeper[k] = v
    if add_nodes:
        keeper.setdefault('indexed_by', []).extend([n for _, n in add_nodes])
    at = list(keeper.get('additional_titles') or [])
    for d, p, dd, _ in dps:
        for t in [dd.get('title')] + list(dd.get('additional_titles') or []):
            if t and t != keeper.get('title') and t not in at:
                at.append(t)
    if at:
        keeper['additional_titles'] = at
    if keeper.get('related_works'):
        keeper['related_works'], _ = clean_self_related(keeper['related_works'], a.keeper, drops)
    apply_edge_ops(keeper, edge_ops.get(a.keeper, []))
    if not keeper.get('related_works'):
        keeper.pop('related_works', None)
    for k in ('books', '_edition_count'):        # 舊格式殘留，順手不留
        keeper.pop(k, None)
    mi = list(keeper.get('merged_in') or [])
    for d, p, dd, _ in dps:
        mi.append({'id': d, 'title': dd.get('title'), 'at': now,
                   'by': a.by, 'rule': a.rule, 'why': a.why})
    keeper['merged_in'] = mi
    addnote(keeper, '%s %s 併條（rule=%s）：併 %s 入本條。%s' % (
        now[:10], a.by, a.rule, '、'.join('%s《%s》' % (d, dd.get('title')) for d, _, dd, _ in dps), a.why))
    save(kp, keeper, kfmt)

    # 他條關係
    n_rel = 0
    for i, ops in edge_ops.items():
        if i == a.keeper:
            continue
        p = find('Work', i, root)
        rd, rfmt = load(p)
        if apply_edge_ops(rd, ops):
            addnote(rd, '%s %s 併條善後：所關聯之 %s 已併入 %s，關係改指（按規範方向落筆）。'
                    % (now[:10], a.by, '、'.join(drops), a.keeper))
            save(p, rd, rfmt); n_rel += 1
    # 存儲側引用
    n_ref = 0
    for (typ, src), ds in sorted(ref_fix.items()):
        p = find(typ, src, root)
        if not p:
            continue
        rd, rfmt = load(p)
        c = sum(retarget_ids(rd, d, a.keeper) for d in ds)
        if c:
            save(p, rd, rfmt); n_ref += 1
    # 分類
    for f, (node, rows) in cls_writes.items():
        p = os.path.join(root, f)
        if rows:
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(members_dump(node, rows))
        else:
            os.remove(p)
    # 刪檔
    for d, p, dd, _ in dps:
        os.remove(p)
    print('\n已併：%s <- %s' % (a.keeper, ','.join(drops)))
    print('善後：著錄 %d 節、他條關係 %d 條記錄、存儲側引用改指 %d 條記錄、分類檔 %d、刪檔 %d'
          % (len(add_nodes), n_rel, n_ref, len(cls_writes), len(dps)))
    print('下一步：python3 build/build_derived.py --write-index（重生 index/ 與派生欄），'
          'python3 .claude/qa/check_v2.py --paths <改動之檔>')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
