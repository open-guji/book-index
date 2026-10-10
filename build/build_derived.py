#!/usr/bin/env python3
"""schema-v2 build：源記錄 → `_build/`（頁面就緒條目＋分頁大列表＋樞紐表）。

依據 overview `F-數據結構/F2-3-build與派生字段.md` §一～§三（含兩則「補」：樞紐規則、卡片分類寫節點 id），
卡片欄位取 F4-2 §二（短鍵名），分頁大小以 F2-3 為準（每頁 200）。

    python3 build/build_derived.py                       # 正式庫（本倉）
    python3 build/build_derived.py --root ../book-index-draft --ref-root .   # 草稿庫，對方 id 由正式庫解析
    python3 build/build_derived.py --check-only          # 只校驗、不寫 _build/
    python3 build/build_derived.py --hub-check           # 加跑「改樞紐名只牽動幾個產物檔」自校驗

產物（不進 git）：
    _build/entry/<id>.json          源記錄＋全部 `_` 派生欄（舊 `_` 欄一律以重算值為準）
    _build/members/<cid>/<n>.json   叢編成員分頁（n 從 1 起，每頁 PAGE 項）
    _build/catalog/<wid>/<n>.json   志書著錄成員分頁
    _build/related/<wid>/<n>.json   關聯超過 PAGE 者之餘頁
    _build/lineage/<wid>.json       作品下版本圖（有承襲資料者）
    _build/_hubs.json               樞紐名稱表
    _build/report.json              校驗報告（確定性，無時間戳）

性質：純函數、確定性（鍵排序、列表按固定鍵排序、緊湊 JSON），同源 → 逐字節同產物；
只寫有變的檔，刪掉不再產出的舊檔。校驗失敗退出碼 1。
"""
import argparse
import collections
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v2common as V  # noqa: E402
import names as N  # noqa: E402
import textindex as TX  # noqa: E402

HUB = 200          # 被內聯引用超過此數者為樞紐：卡片只寫 id＋h:1，名稱進 _hubs.json（F4-2 §一 4）
PAGE = 200         # 分頁大小（F2-3 §二 Collection）
MEMBER_HEAD = 20   # 叢編記錄本身只帶前 20 項成員摘要（F2-3 §二）
SIBLINGS_MAX = 40  # Book._siblings 上限（F2-3 §二）
HUB_CHECK_MAX = 6  # 改樞紐名，牽動產物檔數上限（F4-4：2～4 檔）

DEFAULT_ROLE = '撰'
CONTRACT = 3       # _build/ 契約版本：2＝F6-5b 加專名派生欄與 dynasty_reign_keys／office_keys（overview#458，純增量）；
                   # 3＝Book／Collection 加 `_related`（related_books／related_collections 兩側並集，純增量）


# ---------- 小工具 ----------
def jb(o):
    return (json.dumps(o, ensure_ascii=False, separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8')


def clean(d, keep=('id',)):
    return {k: v for k, v in d.items() if k in keep or v not in (None, '', [], {}, False)}


def text(x):
    if isinstance(x, dict):
        return x.get('name') or x.get('text') or ''
    return x if isinstance(x, str) else ''


def num(x):
    if isinstance(x, dict):
        x = x.get('number')
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and x else None


def types_of(resources):
    out = set()
    for r in resources or []:
        if not isinstance(r, dict):
            continue
        ts = r.get('types')
        if isinstance(ts, list):
            out.update(t for t in ts if isinstance(t, str))
        if isinstance(r.get('type'), str):
            out.add(r['type'])
    return out


def sort_year(b):
    d = b.get('dating')
    if isinstance(d, dict):
        if isinstance(d.get('year_range'), list) and d['year_range'] and isinstance(d['year_range'][0], int):
            return d['year_range'][0]
        if isinstance(d.get('year'), int):
            return d['year']
    return None


def dating_text(b):
    d = b.get('dating')
    if isinstance(d, dict):
        return ' '.join(str(d[k]) for k in ('era', 'reign') if isinstance(d.get(k), (str, int)) and d.get(k))
    return ''


def first_dynasty(w):
    if isinstance(w.get('dynasty'), str) and w['dynasty']:
        return w['dynasty']
    for a in w.get('authors') or []:
        if isinstance(a, dict) and isinstance(a.get('dynasty'), str) and a['dynasty']:
            return a['dynasty']
    return None


def book_key(b):
    y = sort_year(b)
    return (0 if y is not None else 1, y if y is not None else 0, b['id'])


def contained(x):
    """contained_in 項 → (id, 附帶屬性)。"""
    i = V.ref_id(x)
    attrs = {}
    if isinstance(x, dict):
        for k_src, k_out in (('volume_index', 'vol'), ('sub_items', 'sub'), ('group', 'group')):
            if x.get(k_src) not in (None, '', []):
                attrs[k_out] = x[k_src]
        m = re.search(r'叢編原序\s*(\d+)', x.get('details') or '') if isinstance(x.get('details'), str) else None
        if m:                          # 叢編側原序號（遷移 M1 記入 details；目錄總管 10-07：build 據以排序）
            attrs['ord'] = int(m.group(1))
    return i, attrs


class Build:
    def __init__(self, recs, ref_recs=None, classification=None, promotions=None, hub=HUB, text_index=None):
        self.R = {t: {i: r.data for i, r in recs[t].items()} for t in V.TYPES}
        self.own = {t: set(self.R[t]) for t in V.TYPES}
        self.paths = {i: r.path for t in V.TYPES for i, r in recs[t].items()}
        if ref_recs:
            for t in V.TYPES:
                for i, r in ref_recs[t].items():
                    self.R[t].setdefault(i, r.data)
        self.cls = classification
        self.promotions = promotions or {}
        self.hub_threshold = hub
        self.dangling = collections.defaultdict(list)
        self.notes = collections.Counter()
        self._index()
        self._text_index(text_index)
        self.names = N.Names(self.R['Entity'], self.promotions, self.card)   # 專名派生與鍵表（F6-5b）

    # ---------- 反查圖（一次掃描） ----------
    def kind_of(self, i):
        for t in V.TYPES:
            if i in self.R[t]:
                return t
        return None

    def _dangle(self, field, src, tgt):
        if src in self.paths:          # 只報本倉記錄引出的懸空
            self.dangling[field].append([src, tgt])

    def _index(self):
        R = self.R
        self.books_of = collections.defaultdict(set)
        self.works_of = collections.defaultdict(dict)     # eid -> {wid: role}
        self.members = collections.defaultdict(dict)      # cid -> {(t,id): attrs}
        self.children = collections.defaultdict(set)
        self.catalog = collections.defaultdict(dict)      # 志書 wid -> {wid: entry}
        self.derived_by = collections.defaultdict(list)   # bid -> [(bid, relation)]
        self.edges = {}                                   # 規範邊 -> [notes]
        self.indeg = collections.Counter()

        for bid, b in R['Book'].items():
            wid = b.get('work_id')
            if isinstance(wid, str) and wid:
                if wid in R['Work']:
                    self.books_of[wid].add(bid)
                else:
                    self._dangle('Book.work_id', bid, wid)
            for x in b.get('contained_in') or []:
                cid, attrs = contained(x)
                if cid in R['Collection']:
                    self.members[cid].setdefault(('Book', bid), {}).update(attrs)
                elif cid:
                    self._dangle('Book.contained_in', bid, cid)
            lin = b.get('lineage')
            if isinstance(lin, dict):
                for x in lin.get('derived_from') or []:
                    if isinstance(x, dict) and x.get('ref_type', 'book') == 'book':
                        tgt = x.get('ref') or x.get('book_id')
                        if tgt in R['Book']:
                            self.derived_by[tgt].append((bid, x.get('relation')))
                        elif tgt:
                            self._dangle('Book.lineage.derived_from', bid, tgt)
        for wid, w in R['Work'].items():
            for a in w.get('authors') or []:
                if isinstance(a, dict) and isinstance(a.get('entity_id'), str) and a['entity_id']:
                    eid = a['entity_id']
                    if eid in R['Entity']:
                        if wid not in self.works_of[eid] or not self.works_of[eid][wid]:
                            self.works_of[eid][wid] = a.get('role') or None
                    else:
                        self._dangle('Work.authors.entity_id', wid, eid)
            for x in w.get('contained_in') or []:
                cid, attrs = contained(x)
                if cid in R['Collection']:
                    self.members[cid].setdefault(('Work', wid), {}).update(attrs)
                elif cid:
                    self._dangle('Work.contained_in', wid, cid)
            for r in w.get('related_works') or []:
                tgt = V.rel_target(r)
                if not tgt:
                    continue
                if tgt not in R['Work'] and tgt not in R['Collection']:
                    self._dangle('Work.related_works', wid, tgt)
                    continue
                key = V.canon_edge(wid, tgt, r.get('relation'))
                self.edges.setdefault(key, []).append((key[0] == wid, r.get('note')))
            for ib in w.get('indexed_by') or []:
                if isinstance(ib, dict) and isinstance(ib.get('source_bid'), str) and ib['source_bid']:
                    sb = ib['source_bid']
                    if sb in R['Work']:
                        self.catalog[sb].setdefault(wid, ib)
                    else:
                        self._dangle('Work.indexed_by.source_bid', wid, sb)
        for cid, c in R['Collection'].items():
            for x in c.get('contained_in') or []:
                p = V.ref_id(x)
                if p in R['Collection']:
                    self.children[p].add(cid)
                elif p:
                    self._dangle('Collection.contained_in', cid, p)
        # ----- 過渡期：舊反向欄取併集（M3 刪除後為空操作） -----
        for wid, w in R['Work'].items():
            for bid in w.get('books') or []:
                if bid in R['Book']:
                    if R['Book'][bid].get('work_id') != wid and wid in self.paths:
                        self.notes['legacy Work.books 與 Book.work_id 不符'] += 1
                    self.books_of[wid].add(bid)
                elif isinstance(bid, str):
                    self._dangle('Work.books(legacy)', wid, bid)
        for eid, e in R['Entity'].items():
            for x in e.get('works') or []:
                wid = x.get('work_id') if isinstance(x, dict) else None
                if wid in R['Work']:
                    cur = self.works_of[eid].get(wid)
                    if wid not in self.works_of[eid] and eid in self.paths:
                        self.notes['legacy Entity.works 有而 Work.authors 無（併入）'] += 1
                    if not cur:
                        self.works_of[eid][wid] = x.get('role') or None
                elif wid:
                    self._dangle('Entity.works(legacy)', eid, wid)
        for cid, c in R['Collection'].items():
            for x in c.get('books') or []:
                bid = V.ref_id(x, 'book_id', 'id')
                if bid in R['Book']:
                    self.members[cid].setdefault(('Book', bid), {})
                elif bid:
                    self._dangle('Collection.books(legacy)', cid, bid)
            for x in c.get('contained_works') or []:
                wid = V.ref_id(x, 'id', 'work_id')
                if wid in R['Work']:
                    attrs = {}
                    if isinstance(x, dict):
                        if x.get('volume_index') not in (None, ''):
                            attrs['vol'] = x['volume_index']
                        if x.get('group'):
                            attrs['group'] = x['group']
                    m = self.members[cid].setdefault(('Work', wid), {})
                    for k, v in attrs.items():
                        m.setdefault(k, v)
                elif wid:
                    self._dangle('Collection.contained_works(legacy)', cid, wid)
        # ----- 入度 → 樞紐 -----
        for wid, bs in self.books_of.items():
            self.indeg[wid] += len(bs)
        for eid, ws in self.works_of.items():
            self.indeg[eid] += len(ws)
        for cid, ms in self.members.items():
            self.indeg[cid] += len(ms)
        for (s, d, _rel) in self.edges:
            self.indeg[s] += 1
            self.indeg[d] += 1
        for sb, ms in self.catalog.items():
            self.indeg[sb] += len(ms)
        self.hubs = {i for i, n in self.indeg.items() if n > self.hub_threshold}
        # 成員側看到的所屬叢編（含過渡期只寫在叢編側者）
        self.colls_of = collections.defaultdict(dict)
        for cid, ms in self.members.items():
            for (t, i), attrs in ms.items():
                self.colls_of[i][cid] = attrs
        # 每條記錄看到的關聯（out＝本記錄存儲；in＝對方存儲）
        self.rel_view = collections.defaultdict(dict)
        for (s, d, rel), ns in sorted(self.edges.items()):
            # 規範側的 note 排前（遷移前兩側都寫時，以規範側為先）
            note = V.merge_notes([n for side, n in ns if side] + [n for side, n in ns if not side])
            # SCHEMA〈九〉：`direction` 為 out（本記錄存儲）／in（對方存儲；成對者取反向詞，對稱者仍 related）
            self.rel_view[s][(d, rel)] = ('out', note)
            inv = V.REVERSE_OF.get(rel, rel)
            self.rel_view[d].setdefault((s, inv), ('in', note))
        # Book.related_books、Collection.related_books／related_collections：對稱關係只存 id 較小一側
        #（SCHEMA〈一〉3），另一側由此補。值為 {對方 id: 'out'（本記錄存儲）／'in'（對方存儲）}。
        self.sym_view = collections.defaultdict(dict)
        for t in ('Book', 'Collection'):
            for i, r in sorted(self.R[t].items()):
                for f in ('related_books', 'related_collections'):
                    for o in r.get(f) or []:
                        if isinstance(o, str) and o != i and self.kind_of(o) in ('Book', 'Collection'):
                            self.sym_view[i][o] = 'out'
                            self.sym_view[o].setdefault(i, 'in')

    # ---------- book-text 文本索引（工作包 C） ----------
    def _text_index(self, text_index):
        """text_index＝{id: [版本…]}（textindex.load）或 None。None＝保持舊行為（`_has_text`／`_has_collated`
        仍認源裡舊值）；給了就以 resources＋book-text 為唯一來源，源裡舊值不再算。
        id 沿 merged_into 解析到存活記錄；解析不了的悬空 id 記進 self.dangling_text_ids。"""
        self.ti = text_index
        self.txt_ok, self.col_ok = set(), set()
        self.dangling_text_ids = {}
        self.text_merged = 0
        if text_index is None:
            return
        for i, vs in sorted(text_index.items()):
            tgt = self.resolve_live(i)
            if tgt is None:
                self.dangling_text_ids[i] = '記錄不存在' if self.kind_of(i) is None else 'merged_into 成環或斷鏈'
                continue
            if tgt != i:
                self.text_merged += 1
            t, c = TX.flags(vs)
            if t:
                self.txt_ok.add(tgt)
            if c:
                self.col_ok.add(tgt)

    def resolve_live(self, i):
        """沿 merged_into 走到存活（非墓碑）的 Work／Book；斷鏈或成環→None。"""
        seen = set()
        while i not in seen:
            seen.add(i)
            t = self.kind_of(i)
            if t is None:
                return None
            m = self.R[t][i].get('merged_into')
            if not (isinstance(m, str) and m):
                return i
            i = m
        return None

    def legacy_flag(self, d, key):
        """源裡舊 `_has_text`／`_has_collated`：給了 text_index 就不認。"""
        return self.ti is None and bool(d.get(key))

    # ---------- 卡片（F4-2 §二） ----------
    def has(self, d, kind):
        """`_has_image`／`_has_text`／`_has_collated`：resources[].types；text／collated 另看 book-text；Work 另併其 Book。"""
        if kind in types_of(d.get('resources')):
            return True
        if self.ti is not None and kind in ('text', 'collated'):
            return d.get('id') in (self.txt_ok if kind == 'text' else self.col_ok)
        return False

    def put_has(self, v, src, computed):
        """`_has_image`／`_has_text`／`_has_collated`：resources（與 book-text，見 _text_index）推得者；
        未給 text_index 時另認源裡舊值為真者（過渡，見 README「未決」）。＝假不寫。"""
        for kind, key in (('image', '_has_image'), ('text', '_has_text'), ('collated', '_has_collated')):
            got = computed(kind)
            legacy = bool(src.get(key)) or bool(src.get(key[1:]))
            if self.ti is not None and kind != 'image':
                legacy = False
            if got or legacy:
                v[key] = True
                if legacy and not got:
                    self.notes[f'{key} 僅憑源裡舊值（resources 推不出）'] += 1

    def work_has(self, wid, kind):
        w = self.R['Work'][wid]
        if self.has(w, kind):
            return True
        return any(self.has(self.R['Book'][b], kind) for b in self.books_of.get(wid, ()))

    def cls_of(self, wid):
        if self.cls is not None:              # F2-3 補／F4-2：列表卡片的分類只寫節點 id，標籤由讀者查 tree.json
            rows = self.cls.get(wid)
            return rows[0]['node'] if rows else None
        c = self.R['Work'][wid].get('classification')
        if isinstance(c, dict) and c.get('l1'):
            return [c.get('l1'), c.get('l2') or None]
        return None

    def book_card(self, bid):
        b = self.R['Book'][bid]
        lin = b.get('lineage') if isinstance(b.get('lineage'), dict) else {}
        frm = sorted({x.get('ref') or x.get('book_id') for x in lin.get('derived_from') or []
                      if isinstance(x, dict) and x.get('ref_type', 'book') == 'book' and (x.get('ref') or x.get('book_id'))})
        pub = b.get('publication_info')
        return clean({
            'id': bid, 'title': b.get('title'), 'edition': b.get('edition'), 'etype': b.get('edition_type'),
            'dating': dating_text(b), 'y': sort_year(b), 'holder': text(b.get('current_location')),
            'juan': num(b.get('juan_count')),
            'img': self.has(b, 'image') or bool(b.get('_has_image')), 'txt': self.has(b, 'text') or self.legacy_flag(b, '_has_text'),
            'nres': len(b.get('resources') or []),
            'pub': pub.get('year') if isinstance(pub, dict) and isinstance(pub.get('year'), (str, int)) else None,
            'meas': b.get('measure_info') if isinstance(b.get('measure_info'), str) else None,
            'from': frm, 'alias': lin.get('alias') if isinstance(lin.get('alias'), str) else None,
        })

    def work_card(self, wid):
        w = self.R['Work'][wid]
        return clean({
            'id': wid, 'title': w.get('title'), 'dyn': first_dynasty(w), 'juan': num(w.get('juan_count')),
            'au': [a.get('name') for a in (w.get('authors') or [])[:3] if isinstance(a, dict) and a.get('name')],
            'cls': self.cls_of(wid), 'nb': len(self.books_of.get(wid, ())),
            'img': self.work_has(wid, 'image') or bool(w.get('_has_image')),
            'txt': self.work_has(wid, 'text') or self.legacy_flag(w, '_has_text'),
        })

    def ent_card(self, eid):
        e = self.R['Entity'][eid]
        return clean({'id': eid, 'name': e.get('primary_name'), 'dyn': e.get('dynasty'),
                      'dates': e.get('dates') if isinstance(e.get('dates'), (str, dict)) else None})

    def coll_card(self, cid):
        return clean({'id': cid, 'title': self.R['Collection'][cid].get('title')})

    def card(self, i, maker, **extra):
        """樞紐只寫 id＋h:1；其餘照卡片。extra 是邊屬性（role、vol…），兩種都帶。"""
        c = {'id': i, 'h': 1} if i in self.hubs else maker(i)
        c.update({k: v for k, v in extra.items() if v not in (None, '', [])})
        return c

    def any_card(self, i):
        t = self.kind_of(i)
        if t == 'Work':
            return self.card(i, self.work_card)
        if t == 'Collection':
            return self.card(i, self.coll_card)
        return {'id': i}

    def sym_related(self, i):
        """Book／Collection 的 `_related`：對稱關係兩側並集，按 id 排序；卡片帶 `t` 與 `direction`。"""
        out = []
        for o, direction in sorted(self.sym_view.get(i, {}).items()):
            t = self.kind_of(o)
            base = self.book_card(o) if t == 'Book' else self.card(o, self.coll_card)
            out.append(dict(base, t=t.lower(), relation='related', direction=direction))
        return out

    # ---------- 各類產物 ----------
    def collections_of(self, d):
        """本記錄 contained_in 之序在前；過渡期只見於叢編側者按 id 補在後（M3 後為空）。"""
        out = []
        seen = set()
        for x in d.get('contained_in') or []:
            cid, attrs = contained(x)
            if cid in self.R['Collection'] and cid not in seen:
                seen.add(cid)
                out.append(self.card(cid, self.coll_card, **attrs))
        for cid, attrs in sorted(self.colls_of.get(d['id'], {}).items()):
            if cid not in seen:
                seen.add(cid)
                out.append(self.card(cid, self.coll_card, **attrs))
        return out

    def build_work(self, wid):
        R = self.R
        w = R['Work'][wid]
        v = self.strip(w, 'Work')
        books = sorted(self.books_of.get(wid, ()), key=lambda b: book_key(R['Book'][b]))
        v['_books'] = [self.book_card(b) for b in books]
        v['_edition_count'] = len(books)
        auth = []
        for a in w.get('authors') or []:
            if not isinstance(a, dict):
                continue
            eid = a.get('entity_id')
            base = clean({'name': a.get('name'), 'role': a.get('role'), 'dyn': a.get('dynasty')}, keep=())
            if eid in R['Entity']:
                c = {'id': eid, 'h': 1} if eid in self.hubs else self.ent_card(eid)
                c.update(base)
                auth.append(c)
            else:
                auth.append(base)
        v['_authors'] = auth
        cats, seen = [], set()
        for ib in w.get('indexed_by') or []:
            sb = ib.get('source_bid') if isinstance(ib, dict) else None
            if sb in R['Work'] and sb not in seen:
                seen.add(sb)
                c = {'bid': sb, 'h': 1} if sb in self.hubs else clean(
                    {'bid': sb, 'title': R['Work'][sb].get('title'), 'dyn': first_dynasty(R['Work'][sb])}, keep=('bid',))
                if isinstance(ib.get('section'), str) and ib['section']:
                    c['section'] = ib['section']
                cats.append(c)
        v['_catalogs'] = cats
        rel = []
        for (other, r), (direction, note) in self.rel_view.get(wid, {}).items():
            c = self.any_card(other)
            c.update(clean({'relation': r, 'direction': direction, 'note': note}, keep=()))
            rel.append(c)
        rel.sort(key=lambda c: (c['relation'], c['direction'], c['id']))
        pages = []
        if len(rel) > PAGE:
            pages = [rel[i:i + PAGE] for i in range(PAGE, len(rel), PAGE)]
            rel = rel[:PAGE]
        v['_related'] = rel
        if pages:
            v['_related_total'] = len(rel) + sum(len(p) for p in pages)
            v['_related_pages'] = len(pages) + 1
        v['_collections'] = self.collections_of(w)
        self.put_has(v, w, lambda kind: self.work_has(wid, kind))
        if self.cls is not None and self.cls.get(wid):
            v['_classifications'] = self.cls[wid]
        cat_pages = []
        if self.catalog.get(wid):
            ents = []
            for mid, ib in self.catalog[wid].items():
                ents.append(clean({'id': mid, 'h': 1 if mid in self.hubs else None,
                                   'title': None if mid in self.hubs else R['Work'][mid].get('title'),
                                   'section': ib.get('section') if isinstance(ib.get('section'), str) else None,
                                   'title_info': ib.get('title_info'), 'attested_status': ib.get('attested_status')}))
            ents.sort(key=lambda c: (c.get('section') or '', c['id']))
            cat_pages = [ents[i:i + PAGE] for i in range(0, len(ents), PAGE)]
            v['_member_catalog'] = {'total': len(ents), 'pages': len(cat_pages)}
        v.update(self.names.dynasty_ref(first_dynasty(w)))   # `_dynasty_id`／`_dynasty_candidates`（F6-5b）
        if self.promotions.get(wid):
            v['promoted_to'] = self.promotions[wid]      # SCHEMA〈九〉：草稿記錄回填 promoted_to
        lineage = self.lineage_graph(wid, books)
        if lineage:
            v['_lineage_graph_ref'] = f'lineage/{wid}.json'
        return v, {'related': pages, 'catalog': cat_pages, 'lineage': lineage}

    def lineage_graph(self, wid, books):
        R = self.R
        edges = []
        for b in books:
            lin = R['Book'][b].get('lineage')
            if not isinstance(lin, dict):
                continue
            for x in lin.get('derived_from') or []:
                if isinstance(x, dict) and (x.get('ref') or x.get('book_id')):
                    edges.append(clean({'from': x.get('ref') or x.get('book_id'), 'to': b, 'rel': x.get('relation'),
                                        'ref_type': x.get('ref_type'), 'confidence': x.get('confidence')}, keep=('from', 'to')))
            for x in lin.get('related_to') or []:
                if isinstance(x, dict) and (x.get('ref') or x.get('book_id')):
                    edges.append(clean({'a': b, 'b': x.get('ref') or x.get('book_id'), 'rel': x.get('relation'),
                                        'ref_type': x.get('ref_type')}, keep=('a', 'b')))
        if not edges:
            return None
        nodes = [self.book_card(b) for b in books]
        known = set(books)
        for e in edges:
            for k in ('from', 'b'):
                t = e.get(k)
                if t and t not in known and t in R['Book']:
                    known.add(t)
                    nodes.append(self.book_card(t))
        edges.sort(key=lambda e: json.dumps(e, sort_keys=True, ensure_ascii=False))
        return {'work_id': wid, 'nodes': nodes, 'edges': edges}

    def build_book(self, bid):
        R = self.R
        b = R['Book'][bid]
        v = self.strip(b, 'Book')
        wid = b.get('work_id')
        if wid in R['Work']:
            v['_work'] = self.card(wid, self.work_card)
            sib = sorted((x for x in self.books_of.get(wid, ()) if x != bid), key=lambda x: book_key(R['Book'][x]))
            v['_siblings'] = [self.book_card(x) for x in sib[:SIBLINGS_MAX]]
            if len(sib) > SIBLINGS_MAX:
                v['_siblings_more'] = True
                v['_siblings_total'] = len(sib)
        v['_collections'] = self.collections_of(b)
        if self.sym_view.get(bid):
            v['_related'] = self.sym_related(bid)
        refs = {}
        lin = b.get('lineage')
        if isinstance(lin, dict):
            for x in (lin.get('derived_from') or []) + (lin.get('related_to') or []):
                t = (x.get('ref') or x.get('book_id')) if isinstance(x, dict) else None
                if t in R['Book']:
                    refs[t] = clean({'title': R['Book'][t].get('title'), 'edition': R['Book'][t].get('edition')}, keep=())
        if refs:
            v['_lineage_refs'] = refs
        der = sorted(self.derived_by.get(bid, ()), key=lambda x: x[0])
        if der:
            v['_derived_by'] = [clean({'id': x, 'title': R['Book'][x].get('title'), 'edition': R['Book'][x].get('edition'),
                                       'rel': r}) for x, r in der]
        self.put_has(v, b, lambda kind: self.has(b, kind))
        if self.promotions.get(bid):
            v['promoted_to'] = self.promotions[bid]
        if wid in R['Work'] and self.has_lineage(wid):
            v['_lineage_graph_ref'] = f'lineage/{wid}.json'
        return v, {}

    def has_lineage(self, wid):
        if not hasattr(self, '_lin_cache'):
            self._lin_cache = {}
        if wid not in self._lin_cache:
            self._lin_cache[wid] = any(
                isinstance(self.R['Book'][b].get('lineage'), dict) and (
                    self.R['Book'][b]['lineage'].get('derived_from') or self.R['Book'][b]['lineage'].get('related_to'))
                for b in self.books_of.get(wid, ()))
        return self._lin_cache[wid]

    def build_collection(self, cid):
        R = self.R
        c = R['Collection'][cid]
        v = self.strip(c, 'Collection')
        cards = []
        for (t, i), attrs in self.members.get(cid, {}).items():
            base = self.book_card(i) if t == 'Book' else self.work_card(i)
            card = dict(base, t='book' if t == 'Book' else 'work')
            if t == 'Book' and isinstance(R['Book'][i].get('section'), str) and R['Book'][i]['section']:
                card['section'] = R['Book'][i]['section']
            card.update(attrs)
            cards.append(card)
        cards.sort(key=lambda x: (x['t'], 'ord' not in x, x.get('ord', 0), x['id']))
        pages = [cards[i:i + PAGE] for i in range(0, len(cards), PAGE)]
        if self.sym_view.get(cid):
            v['_related'] = self.sym_related(cid)
        v['_members'] = cards[:MEMBER_HEAD]
        v['_member_count'] = len(cards)
        v['_member_pages'] = len(pages)
        has_b = any(x['t'] == 'book' for x in cards)
        has_w = any(x['t'] == 'work' for x in cards)
        mt = 'mixed' if has_b and has_w else 'Book' if has_b else 'Work' if has_w else None
        if mt:
            v['_member_type'] = mt
        ch = sorted(self.children.get(cid, ()))
        if ch:
            v['_children'] = [self.card(x, self.coll_card) for x in ch]
        self.put_has(v, c, lambda kind: self.has(c, kind))
        return v, {'members': pages}

    def build_entity(self, eid):
        R = self.R
        v = self.strip(R['Entity'][eid], 'Entity')
        ws = []
        for wid, role in self.works_of.get(eid, {}).items():
            if not role:
                self.notes['Entity._works 缺 role（以「撰」補）'] += 1   # build_entity 只跑本倉記錄
            c = self.work_card(wid)
            c['work_id'] = c.pop('id')            # SCHEMA〈九〉：Entity._works 以 work_id 為鍵
            c['role'] = role or DEFAULT_ROLE
            ws.append(c)
        ws.sort(key=lambda c: (str(c['cls'] if isinstance(c.get('cls'), str) else (c.get('cls') or [''])[0] or ''),
                               c.get('title') or '', c['work_id']))
        v['_works'] = ws
        v.update(self.names.derive(eid, R['Entity'][eid]))
        return v, {}

    def strip(self, d, typ):
        """產物以源記錄為底；舊 `_` 派生欄一律丟掉重算（以生成值為準，SCHEMA 既有規矩）。"""
        return {k: x for k, x in d.items() if not k.startswith('_') and k != 'promoted_to'}

    # ---------- 全量 ----------
    def products(self, ids=None):
        """產生 {relpath: obj}。ids=None 為本倉全部。"""
        out = {}
        builders = (('Work', self.build_work), ('Book', self.build_book),
                    ('Collection', self.build_collection), ('Entity', self.build_entity))
        for t, fn in builders:
            for i in sorted(self.own[t]):
                if ids is not None and i not in ids:
                    continue
                v, extra = fn(i)
                out[f'entry/{i}.json'] = v
                for n, pg in enumerate(extra.get('related') or [], start=2):
                    out[f'related/{i}/{n}.json'] = pg
                for n, pg in enumerate(extra.get('catalog') or [], start=1):
                    out[f'catalog/{i}/{n}.json'] = pg
                for n, pg in enumerate(extra.get('members') or [], start=1):
                    out[f'members/{i}/{n}.json'] = pg
                if extra.get('lineage'):
                    out[f'lineage/{i}.json'] = extra['lineage']
        hubs = {}
        for i in sorted(self.hubs):
            t = self.kind_of(i)
            x = self.R[t][i]
            hubs[i] = clean({'t': t[0].lower(), 'title': x.get('title') or x.get('primary_name'),
                             'dyn': first_dynasty(x) if t == 'Work' else x.get('dynasty')}, keep=('t',))
        out['_hubs.json'] = hubs
        if ids is None:
            out.update(self.names.products())
        return out


# ---------- index/（原 reindex.py／bim entry_extractor 併入；F2-3 §一、SCHEMA〈九〉） ----------
INDEX_FAMILY = {'Work': 'works', 'Book': 'books', 'Entity': 'entities', 'Collection': 'collections'}


def shard_of(i, n=16):
    """與 bim storage.shard_of、reindex.shard 同：h=h*31+ord(c)，取模 16。"""
    h = 0
    for c in i:
        h = ((h * 31) + ord(c)) & 0xFFFFFFFF
    return h % n


def _titles(raw):
    out = []
    for t in raw if isinstance(raw, list) else []:
        if isinstance(t, str) and t:
            out.append(t)
        elif isinstance(t, dict) and t.get('book_title'):
            out.append(t['book_title'])
    return out


def _res_flags(d):
    txt = img = False
    for r in d.get('resources') or [] if isinstance(d.get('resources'), list) else []:
        if not isinstance(r, dict):
            continue
        ts = r.get('types')
        if isinstance(ts, list) and ts:
            txt = txt or 'text' in ts
            img = img or 'image' in ts
        else:
            rt = r.get('type', '')
            txt = txt or rt in ('text', 'text+image')
            img = img or rt in ('image', 'text+image')
    return txt, img


def index_entry(d, typ, rel_path, promoted_to=None, build=None):
    """逐字照 book_index_manager/entry_extractor.py（build_index_entry／build_entity_index_entry）。
    promoted_to：record 上的舊值優先（遷移前），否則取 promotions.json（M3 後 record 不再帶）。
    build：給了且帶 text_index 時，`has_text`／`has_collated` 與 entry 的 `_has_text`／`_has_collated` 同口徑
    （Work 並其 Book、book-text、merged_into 解析），否則照舊只看本記錄 resources 與源裡舊值。"""
    pt = d.get('_promoted_to') or d.get('promoted_to') or promoted_to
    if typ == 'Entity':
        ext = d.get('external_ids') or {}
        e = {'id': d.get('id'), 'type': 'entity', 'subtype': d.get('subtype', 'people'),
             'primary_name': d.get('primary_name', ''), 'path': rel_path}
        if d.get('dynasty'):
            e['dynasty'] = d['dynasty']
        dt = d.get('dates') if isinstance(d.get('dates'), dict) else {}
        for k, dk in (('birth_year', 'birth'), ('death_year', 'death')):
            v = dt.get(dk)
            if v is None:
                v = d.get(k)  # 回退源：schema-v2 過渡期仍有的 birth_year／death_year
            if v is not None:
                e[k] = v
        if isinstance(ext, dict) and ext.get('cbdb_id') is not None:
            e['cbdb_id'] = ext['cbdb_id']
        if d.get('period'):
            e['period'] = d['period']
        if pt:
            e['promoted_to'] = pt
        return e
    au = d.get('authors', [])
    a0 = {'name': '', 'dynasty': '', 'role': ''}
    if isinstance(au, list) and au:
        if isinstance(au[0], dict):
            a0 = {k: au[0].get(k, '') for k in a0}
        else:
            a0['name'] = str(au[0])
    elif isinstance(au, str):
        a0['name'] = au
    e = {'id': d.get('id'), 'title': d.get('title', '未命名'), 'type': typ, 'path': rel_path}
    if a0['name']:
        e['author'] = a0['name']
    dt = d.get('dating')
    if isinstance(dt, dict):
        if isinstance(dt.get('era'), str) and dt['era']:
            e['era'] = dt['era']
        y = dt.get('year')
        if isinstance(y, int) and not isinstance(y, bool):
            e['sort_year'] = y
        else:
            rng = dt.get('year_range')
            if isinstance(rng, list) and len(rng) == 2 and isinstance(rng[0], int):
                e['sort_year'] = rng[0]
    loc = d.get('current_location')
    holder = loc.get('name', '') if isinstance(loc, dict) else loc if isinstance(loc, str) else ''
    if holder:
        e['holder'] = holder
    # 撰人朝代：第一个有朝代的作者优先，顶层 dynasty 兜底（overview#496 §六-1；与 bim entry_extractor、ui storage.ts 同）。
    # 注意 index 的 dynasty 是撰人朝代，卡片 dyn／_dynasty_id 取 first_dynasty（成书朝代优先），二者语义不同、不统一。
    dyn = next((a['dynasty'] for a in (au if isinstance(au, list) else [])
                if isinstance(a, dict) and isinstance(a.get('dynasty'), str) and a['dynasty']), '') \
        or d.get('dynasty') or ''
    if dyn:
        e['dynasty'] = dyn
    if a0['role']:
        e['role'] = a0['role']
    jc = d.get('juan_count')
    jn = (jc.get('number', 0) or 0) if isinstance(jc, dict) else int(jc) if isinstance(jc, (int, float)) else 0
    if jn:
        e['juan_count'] = jn
    if d.get('measure_info'):
        e['measure_info'] = d['measure_info']
    for k in ('additional_titles', 'attached_texts'):
        t = _titles(d.get(k, []))
        if t:
            e[k] = t
    txt, img = _res_flags(d)
    col = bool(d.get('_has_collated') or d.get('has_collated'))
    if build is not None and build.ti is not None:
        has = build.work_has if typ == 'Work' else (lambda _i, kind: build.has(d, kind))
        txt, col = has(d.get('id'), 'text'), has(d.get('id'), 'collated')
    if txt:
        e['has_text'] = True
    if img:
        e['has_image'] = True
    if col:
        e['has_collated'] = True          # 整理本標記：源欄（目錄總管 10-07 定保留），既有 index 帶此欄
    for k in ('edition', 'subtype', 'period', 'loss_status', 'original_title', 'work_id'):
        if d.get(k):
            e[k] = d[k]
    if pt:
        e['promoted_to'] = pt
    return e


def build_index(recs, promotions=None, build=None):
    """→ {'index/works/<h>.json': {...}, …, 'index/collections.json': {...}}（鍵按 id 排序）。"""
    promotions = promotions or {}
    out = {}
    for t in V.TYPES:
        fam = INDEX_FAMILY[t]
        for i in sorted(recs[t]):
            r = recs[t][i]
            rel = f'index/{fam}.json' if fam == 'collections' else f'index/{fam}/{shard_of(i):x}.json'
            out.setdefault(rel, {})[i] = index_entry(r.data, t, r.path.replace(os.sep, '/'), promotions.get(i), build)
    return {k: dict(sorted(v.items())) for k, v in sorted(out.items())}


def index_file_content(root, rel, data):
    """→ (舊內容或 None, 新內容)：沿用該分片既有縮排與尾換行（bim write_shard 同法）。"""
    p = os.path.join(root, rel)
    indent, trailing = 2, False
    try:
        with open(p, encoding='utf-8') as f:
            raw = f.read()
        second = raw.split('\n', 2)[1] if raw.count('\n') >= 1 else ''
        st = second.lstrip(' ')
        if st and not st.startswith('}'):
            indent = len(second) - len(st) or 2
        trailing = raw.endswith('\n')
    except FileNotFoundError:
        raw = None
    return raw, json.dumps(data, ensure_ascii=False, indent=indent) + ('\n' if trailing else '')


def write_index(root, shards):
    """寫回倉內 index/，只寫有變的檔。"""
    n = 0
    for rel, data in shards.items():
        p = os.path.join(root, rel)
        raw, new = index_file_content(root, rel, data)
        if new != raw:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new)
            n += 1
    return n


# ---------- 分類檔（F3-2；M4 之後才有） ----------
def load_classification(root):
    """讀 classification/（F3-2、SCHEMA〈八〉）→ ({work_id: [_classifications 項…]}, 問題清單, 舊式 classific.json)。
    問題清單即 `classify check`：①節點存在且未 retired ②（記錄存在由 run 查）③互斥分類法一部只出現一次
    ④成員檔名＝其 node。無 classification/ 回 (None, [], None)。"""
    base = os.path.join(root, 'classification')
    sp = os.path.join(base, 'schemes.json')
    if not os.path.exists(sp):
        return None, [], None
    schemes = json.load(open(sp, encoding='utf-8'))
    schemes = schemes.get('schemes', schemes) if isinstance(schemes, dict) else schemes
    schemes = sorted(schemes, key=lambda s: (not s.get('primary'), s['id']))
    out = collections.defaultdict(list)
    problems = []
    legacy = None
    for s in schemes:
        tree = json.load(open(os.path.join(base, s.get('tree') or f"{s['id']}/tree.json"), encoding='utf-8'))
        nodes = {n['id']: n for n in tree['nodes']}

        def path(nid):
            p = []
            while nid:
                p.append(nodes[nid]['label'])
                nid = nodes[nid].get('parent')
            return p[::-1]
        if s.get('primary'):
            parents = {n.get('parent') for n in tree['nodes']}
            legacy = [{f'cata_l{k + 1}': lab for k, lab in enumerate(path(n['id']))}
                      for n in tree['nodes'] if n['id'] not in parents and not n.get('retired')]
        seen = {}
        mdir = os.path.join(base, s['id'], 'members')
        for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
            m = json.load(open(os.path.join(mdir, fn), encoding='utf-8'))
            node = m.get('node')
            if fn != f'{node}.json':
                problems.append(f'{s["id"]}/members/{fn}: 檔名與 node {node} 不符')
            if node not in nodes or nodes[node].get('retired'):
                problems.append(f'{s["id"]}/members/{fn}: 節點 {node} 不存在或已 retired')
                continue
            p = path(node)
            for row in m['members']:
                if s.get('exclusive') and row[0] in seen:
                    problems.append(f'{s["id"]}: {row[0]} 同在 {seen[row[0]]} 與 {node}（互斥分類法）')
                seen[row[0]] = node
                ls = (p + ['', '', '', ''])[:4]
                out[row[0]].append(clean({'scheme': s['id'], 'node': node, 'path': p, 'l1': ls[0], 'l2': ls[1],
                                          'l3': ls[2], 'l4': ls[3], 'source': row[1] if len(row) > 1 else None},
                                         keep=('scheme', 'node', 'path', 'l1', 'l2', 'l3', 'l4')))
    return dict(out), problems, legacy


def load_promotions(root):
    """`{草稿id: 正式id}`；整檔、分片（`promotions/`）兩種形狀都認（V.read_promotions_raw）。"""
    out = {}
    for k, v in V.read_promotions_raw(root).items():
        out[k] = v if isinstance(v, str) else (v.get('production_id') or v.get('to') or v.get('official_id') or v.get('id')) if isinstance(v, dict) else None
    return {k: v for k, v in out.items() if v}


def load_promotions_all(root, ref_roots=()):
    """promotions.json 2026-10-06 起只在正式庫根（overview#432）：草稿庫 build 時 root 下沒有，
    要從 --ref-root 取，否則草稿 index 的 promoted_to 全丟。root 自己的優先。"""
    out = {}
    for r in list(ref_roots)[::-1] + [root]:
        out.update(load_promotions(r))
    return out


# ---------- 校驗 ----------
def source_checks(recs):
    """源檔裡不該有的：`_` 欄（舊派生，M3 刪；其他一律算錯）、舊反向欄。"""
    legacy, unknown, rev = collections.Counter(), collections.Counter(), collections.Counter()
    unknown_where = []
    for t in V.TYPES:
        for i, r in recs[t].items():
            for k in r.data:
                if k.startswith('_'):
                    if k in V.LEGACY_DERIVED[t]:
                        legacy[f'{t}.{k}'] += 1
                    else:
                        unknown[f'{t}.{k}'] += 1
                        if len(unknown_where) < 200:
                            unknown_where.append([i, k])
            for k in V.LEGACY_REVERSE[t]:
                if k in r.data:
                    rev[f'{t}.{k}'] += 1
    return {'legacy_underscore_fields': dict(sorted(legacy.items())),
            'unknown_underscore_fields': dict(sorted(unknown.items())), 'unknown_underscore_where': unknown_where,
            'legacy_reverse_fields': dict(sorted(rev.items()))}


def self_checks(b, prods):
    """派生值自洽、卡片可解析、h:1 都在 _hubs、條數守恒。"""
    errs = []
    hubs = prods['_hubs.json']
    n_entries = sum(1 for k in prods if k.startswith('entry/'))
    n_src = sum(len(b.own[t]) for t in V.TYPES)
    if n_entries != n_src:
        errs.append(f'條數不守恒：源 {n_src}，entry {n_entries}')

    def chk_cards(where, cards, idk='id'):
        for c in cards:
            if c.get('h') == 1 and c[idk] not in hubs:
                errs.append(f'{where}: 樞紐 {c[idk]} 不在 _hubs.json')
            if b.kind_of(c[idk]) is None:
                errs.append(f'{where}: 卡片 {c[idk]} 無對應記錄')
    for k, v in prods.items():
        if not k.startswith('entry/'):
            continue
        i = k[6:-5]
        if '_books' in v and v['_edition_count'] != len(v['_books']):
            errs.append(f'{i}: _edition_count≠len(_books)')
        if '_member_count' in v:
            pages = [prods.get(f'members/{i}/{n}.json', []) for n in range(1, v['_member_pages'] + 1)]
            if sum(len(p) for p in pages) != v['_member_count']:
                errs.append(f'{i}: 成員分頁合計≠_member_count')
            if v['_members'] != (pages[0][:MEMBER_HEAD] if pages else []):
                errs.append(f'{i}: _members 首段≠第 1 頁前段')
            for p in pages:
                chk_cards(i, p)
        if '_related_total' in v:
            tot = len(v['_related']) + sum(len(prods.get(f'related/{i}/{n}.json', []))
                                          for n in range(2, v['_related_pages'] + 1))
            if tot != v['_related_total']:
                errs.append(f'{i}: 關聯分頁合計≠_related_total')
        if '_member_catalog' in v:
            for n in range(1, v['_member_catalog']['pages'] + 1):
                chk_cards(i, prods.get(f'catalog/{i}/{n}.json', []))
            tot = sum(len(prods.get(f'catalog/{i}/{n}.json', [])) for n in range(1, v['_member_catalog']['pages'] + 1))
            if tot != v['_member_catalog']['total']:
                errs.append(f'{i}: 志書成員分頁合計≠total')
        for f in ('_related', '_collections', '_children', '_siblings', '_books'):
            chk_cards(i, v.get(f) or [])
        chk_cards(i, v.get('_works') or [], 'work_id')
        chk_cards(i, v.get('_catalogs') or [], 'bid')
        if '_work' in v:
            chk_cards(i, [v['_work']])
        for a in v.get('_authors') or []:
            if 'id' in a:
                chk_cards(i, [a])
    return errs


def legacy_diffs(recs, prods):
    """舊派生欄（源裡手寫的）與重算值的差：只報，供 M3 前後對表。"""
    d = collections.Counter()
    for t in V.TYPES:
        for i, r in recs[t].items():
            v = prods[f'entry/{i}.json']
            for k in V.LEGACY_DERIVED[t]:
                if k in ('_promoted_to', '_promoted_at', '_has_collated'):
                    continue
                if k in r.data and r.data[k] != v.get(k):
                    d[f'{t}.{k} 源值≠重算'] += 1
                if k not in r.data and v.get(k) not in (None, False, 0):
                    d[f'{t}.{k} 源缺、重算有'] += 1
            if t == 'Work' and 'books' in r.data:
                if sorted(r.data['books'] or []) != sorted(x['id'] for x in v['_books']):
                    d['Work.books 集合≠_books'] += 1
            if t == 'Entity' and 'works' in r.data:
                old = {x.get('work_id') for x in r.data['works'] or [] if isinstance(x, dict)}
                if old != {x['work_id'] for x in v['_works']}:
                    d['Entity.works 集合≠_works'] += 1
    return dict(sorted(d.items()))


def hub_check(b, prods, limit=HUB_CHECK_MAX):
    """每類取入度最大的樞紐，記憶體裡改名後重算，數產物變了幾個檔（F2-3 補：寫進自校驗）。"""
    base = {k: hashlib.sha256(jb(v)).hexdigest() for k, v in prods.items()}
    res = []
    for t, fld in (('Collection', 'title'), ('Work', 'title'), ('Entity', 'primary_name')):
        cand = [i for i in b.hubs if i in b.own[t]]
        if not cand:
            continue
        i = max(cand, key=lambda x: (b.indeg[x], x))
        rec = b.R[t][i]
        old = rec.get(fld)
        rec[fld] = (old or '') + '〔改名測試〕'
        try:
            new = b.products()
        finally:
            rec[fld] = old
        changed = sorted(k for k, v in new.items() if base.get(k) != hashlib.sha256(jb(v)).hexdigest())
        res.append({'type': t, 'id': i, 'indegree': b.indeg[i], 'changed': len(changed), 'files': changed[:10],
                    'ok': len(changed) <= limit})
    return res


# ---------- 寫出 ----------
def write_products(out_dir, prods):
    written = unchanged = removed = 0
    want = set()
    for rel, obj in prods.items():
        p = os.path.join(out_dir, rel)
        want.add(os.path.normpath(p))
        data = jb(obj)
        try:
            with open(p, 'rb') as f:
                if f.read() == data:
                    unchanged += 1
                    continue
        except FileNotFoundError:
            os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)
        written += 1
    for sub in ('entry', 'members', 'catalog', 'related', 'lineage'):
        base = os.path.join(out_dir, sub)
        for dp, dns, fns in os.walk(base, topdown=False):
            for fn in fns:
                p = os.path.normpath(os.path.join(dp, fn))
                if p not in want:
                    os.remove(p)
                    removed += 1
            if dp != base and not os.listdir(dp):
                os.rmdir(dp)
    return {'written': written, 'unchanged': unchanged, 'removed': removed}


def index_drift(root, shards):
    """倉內現有 index/ 與重生值之差（逐欄計數）：舊索引漂移，重生後即消。"""
    c = collections.Counter()
    for rel, new in shards.items():
        p = os.path.join(root, rel)
        old = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        for k in set(old) | set(new):
            if k not in new:
                c['舊 index 有、記錄無'] += 1
            elif k not in old:
                c['記錄有、舊 index 無'] += 1
            else:
                for f in set(old[k]) | set(new[k]):
                    if old[k].get(f) != new[k].get(f):
                        c[f'欄 {f}'] += 1
    return dict(sorted(c.items()))


def text_index_report(b, recs):
    """book-text 文本索引的接入報告；未給 text_index 時只標 enabled=False。
    has_text_lost／gained：本倉源檔 `_has_text:true` 而重算為假（舊假陽性）／源檔無而重算為真，只列 Work 清單。"""
    if b.ti is None:
        return {'enabled': False}
    lost, gained = [], []
    for wid, r in recs['Work'].items():
        got = b.work_has(wid, 'text')
        src = bool(r.data.get('_has_text'))
        if src and not got:
            lost.append(wid)
        elif got and not src:
            gained.append(wid)
    counts = {}
    for t in ('Work', 'Book'):
        counts[f'{t}._has_text'] = sum(1 for i in recs[t] if (b.work_has(i, 'text') if t == 'Work' else b.has(b.R[t][i], 'text')))
        counts[f'{t}._has_collated'] = sum(1 for i in recs[t] if (b.work_has(i, 'collated') if t == 'Work' else b.has(b.R[t][i], 'collated')))
    return {'enabled': True, 'ids': len(b.ti), 'merged_resolved': b.text_merged,
            'dangling': len(b.dangling_text_ids), 'counts': counts,
            'has_text_lost_work': {'count': len(lost), 'ids': sorted(lost)},
            'has_text_gained_work': {'count': len(gained)}}


def run(root, ref_roots=(), out_dir=None, check_only=False, strict=False, do_hub_check=False, hub=HUB, quiet=False,
        write_repo_index=False, text_index=None):
    recs, sidecars, problems = V.load_repo(root)
    ref = None
    for rr in ref_roots:
        r2, _, _ = V.load_repo(rr)
        if ref is None:
            ref = r2
        else:
            for t in V.TYPES:
                for k, x in r2[t].items():
                    ref[t].setdefault(k, x)
    cls, cls_problems, legacy_vocab = load_classification(root)
    b = Build(recs, ref, cls, load_promotions_all(root, ref_roots), hub=hub, text_index=text_index)
    prods = b.products()
    if legacy_vocab is not None:
        prods['classific.json'] = legacy_vocab      # F3-2 §六⑤：舊詞表改為 tree.json 的生成物，供舊讀者
    if cls is not None:
        for wid in sorted(cls):
            if b.kind_of(wid) != 'Work':
                cls_problems.append(f'成員行 {wid} 不是本倉（或參照倉）的 Work')
    src = source_checks(recs)
    if cls is not None:                       # 分類檔已在（M4a 後）：Work 裡還留舊 classification 即殘留
        n = sum(1 for r in recs['Work'].values() if 'classification' in r.data)
        if n:
            src['legacy_reverse_fields']['Work.classification'] = n
    errs = self_checks(b, prods)
    report = {
        'contract': CONTRACT,
        'root': os.path.basename(os.path.abspath(root)),
        'records': {t: len(recs[t]) for t in V.TYPES},
        'entries': sum(1 for k in prods if k.startswith('entry/')),
        'files_total': len(prods),
        'pages': {s: sum(1 for k in prods if k.startswith(s + '/')) for s in ('members', 'catalog', 'related', 'lineage')},
        'hubs': len(b.hubs), 'hub_threshold': hub,
        'sidecars_ignored': sidecars,
        'load_problems': problems,
        'dangling': {k: {'count': len(v), 'sample': sorted(v)[:50]} for k, v in sorted(b.dangling.items())},
        'source_fields': src,
        'legacy_vs_rebuilt': legacy_diffs(recs, prods),
        'notes': dict(sorted(b.notes.items())),
        'text_index': text_index_report(b, recs),
        'dangling_text_ids': dict(sorted(b.dangling_text_ids.items())),
        'self_check_errors': errs[:200], 'self_check_error_count': len(errs),
        'classification': None if cls is None else {'works': len(cls), 'problems': cls_problems[:200],
                                                    'problem_count': len(cls_problems)},
    }
    if do_hub_check:
        report['hub_check'] = hub_check(b, prods)
    fatal = []
    if errs:
        fatal.append(f'自洽校驗 {len(errs)} 項失敗')
    if problems:
        fatal.append(f'讀檔問題 {len(problems)} 項')
    if cls_problems:
        fatal.append(f'分類檔校驗 {len(cls_problems)} 項失敗')
    if src['unknown_underscore_fields']:
        fatal.append('源檔含非舊有之 `_` 欄：' + ', '.join(src['unknown_underscore_fields']))
    if strict and (src['legacy_underscore_fields'] or src['legacy_reverse_fields']):
        fatal.append('--strict：源檔仍含舊派生／反向欄')
    if do_hub_check and not all(x['ok'] for x in report['hub_check']):
        fatal.append('改樞紐名牽動產物檔超過上限')
    report['fatal'] = fatal   # 之後 index 校驗還會往裡加
    shards = build_index(recs, load_promotions_all(root, ref_roots), b)
    n_idx = sum(len(v) for v in shards.values())
    report['index'] = {'files': len(shards), 'entries': n_idx, 'drift_vs_repo_index': index_drift(root, shards)}
    if n_idx != report['entries']:
        fatal.append(f'index 條數不守恒：記錄 {report["entries"]}，index {n_idx}')
    if not check_only:
        out_dir = out_dir or os.path.join(root, '_build')
        os.makedirs(out_dir, exist_ok=True)
        report['write'] = write_products(out_dir, prods)
        report['write']['index_files_written'] = write_index(out_dir, shards)
        if write_repo_index:
            report['write']['repo_index_files_written'] = write_index(root, shards)
        with open(os.path.join(out_dir, 'report.json'), 'w', encoding='utf-8') as f:
            json.dump({k: v for k, v in report.items() if k != 'write'}, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
    if not quiet:
        brief = {k: report[k] for k in ('records', 'entries', 'files_total', 'pages', 'hubs', 'notes', 'index',
                                       'legacy_vs_rebuilt', 'self_check_error_count', 'fatal')}
        brief['dangling'] = {k: v['count'] for k, v in report['dangling'].items()}
        brief['source_fields'] = {k: v for k, v in src.items() if k != 'unknown_underscore_where'}
        if 'write' in report:
            brief['write'] = report['write']
        if 'hub_check' in report:
            brief['hub_check'] = [{k: x[k] for k in ('type', 'id', 'indegree', 'changed', 'ok')} for x in report['hub_check']]
        print(json.dumps(brief, ensure_ascii=False, indent=1))
    return report, prods


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help='數據倉根（預設本倉）')
    ap.add_argument('--ref-root', action='append', default=[],
                    help='只讀參照倉（草稿庫 build 時指正式庫，解析指向正式記錄的 id）')
    ap.add_argument('--out', help='輸出目錄（預設 <root>/_build）')
    ap.add_argument('--check-only', action='store_true', help='只校驗，不寫產物')
    ap.add_argument('--strict', action='store_true', help='源檔有舊派生／反向欄也算失敗（M3 之後用）')
    ap.add_argument('--hub-check', action='store_true', help='加跑改樞紐名牽動檔數自校驗（多一次全量重算）')
    ap.add_argument('--hub', type=int, default=HUB, help=f'樞紐閾值（預設 {HUB}）')
    ap.add_argument('--text-index', metavar='DIR',
                    help='book-text 的 index/texts 目錄；給了，`_has_text`／`_has_collated` 與 index 的 has_text／has_collated '
                         '由 resources＋book-text 推（源裡舊值不再算）；不給＝保持舊行為並警告')
    ap.add_argument('--write-index', action='store_true',
                    help='另把 index/ 寫回倉內（沿用各分片縮排；預設只寫 <out>/index/）')
    a = ap.parse_args(argv)
    ti = None
    if a.text_index:
        ti = TX.load(a.text_index)
    else:
        print('WARN: 未給 --text-index：_has_text／_has_collated 仍認源檔舊值（過渡行為，與 book-text 可能不一致）', file=sys.stderr)
    report, _ = run(a.root, a.ref_root, a.out, a.check_only, a.strict, a.hub_check, a.hub,
                    write_repo_index=a.write_index, text_index=ti)
    if report['fatal']:
        print('FAIL: ' + '；'.join(report['fatal']), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
