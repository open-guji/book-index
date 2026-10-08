"""專名子類型的 build 派生欄與匹配鍵表（F6-5b，overview#464／#458）。

依據 SCHEMA〈九〉末幾行、overview `專名建檔/給S-字段清單.md` §三·7／§五、D 設計檔 §八、P3c 官署設計 §八，
鍵表形狀照 `專名建檔/P4-升格/dynasty_reign_keys-交接.md`、`office_keys-交接.md`（N 的原型 gen_*_keys.py）。

    派生欄（只在 _build/entry/，源檔不寫）
      dynasty   _children、_ancestors、_reigns
      reign     _dynasty、_ruler、_index_in_reign、_same_name
      office    _children（概念→具體）、_compounds（base_office_id 反查）
      place     _children（沿革項 parent_id 反查）、_span
      官署      _children（概念→具體）、_subordinates（superiors 反查）、_members（group_ids 反查）、
                _offices（office.institution_ref 反查）
      people／Work  _dynasty_id（朝代名唯一命中）／_dynasty_candidates（歧義名的候選 id）
    產物
      dynasty_reign_keys.json、office_keys.json、place_keys.json（地名：鍵源另有沿革當時名、去通名；
      候選可帶 segments、default，規則見 `專名建檔/P4-升格/place_keys-交接.md` §一～§四）

已升格的草稿條（在 promotions 裡）以正式條為準：不進反查、不進鍵表；一切 id 引用先經 promotions 換成正式 id。
純函數、確定性；列表一律按固定鍵排序。
"""
import collections

NORMALIZE = {'尙': '尚', '郞': '郎', '戸': '戶', '叅': '參', '秘': '祕', '歴': '曆', '淸': '清'}   # 三表共用
VARIANT = str.maketrans(NORMALIZE)
KEYS_VERSION = 1
LEVEL_ORDER = {'concept': 0, 'group': 1, 'concrete': 2}
PLACE_SUFFIX = ('縣', '州', '府', '軍', '路', '道', '省', '廳')   # 去通名（基名至少 2 字）
# 地名默認候選：同名多候選時取最低一級的實地（place_keys-交接 §四）
PLACE_RANK = {'縣': 1, '廳': 1, '州': 2, '軍': 2, '監': 2, '府': 3, '郡': 3, '路': 4, '道': 4, '省': 5, '國': 5}


def _dates(d):
    x = d.get('dates')
    return x if isinstance(x, dict) else {}


def _start(d):
    s = _dates(d).get('start')
    return s if isinstance(s, int) else None


def _end(d):
    e = _dates(d).get('end')
    return e if isinstance(e, int) else None


def _ids(x):
    return [i for i in (x or []) if isinstance(i, str) and i]


def is_institution(d):
    return d.get('subtype') == 'collective' and d.get('collective_kind') == '官署'


def _names(d):
    """(名, via, ambiguous)：primary_name 與 alt_names（全稱不參與匹配，給S-字段清單 §三·1）。"""
    out = [(d['primary_name'], 'primary_name', False)] if isinstance(d.get('primary_name'), str) else []
    for al in d.get('alt_names') or []:
        if isinstance(al, dict) and isinstance(al.get('name'), str) and al['name'] and al.get('type') != '全稱':
            out.append((al['name'], al.get('type') or 'alt', bool(al.get('ambiguous'))))
    return out


class Names:
    def __init__(self, entities, promotions, card):
        """entities：{id: data}（本倉＋參照倉）；promotions：{草稿 id: 正式 id}；
        card(id, maker)：Build.card（樞紐規則）。"""
        self.P = promotions or {}
        self.E = {i: d for i, d in entities.items() if i not in self.P}     # 已升格草稿以正式條為準
        self.card = card
        self._index()

    def rid(self, x):
        return self.P.get(x, x) if isinstance(x, str) else x

    def _index(self):
        E, rid = self.E, self.rid
        self.children = collections.defaultdict(set)      # dynasty／office／官署 parent_id 反查；place 沿革上級
        self.reigns = collections.defaultdict(set)        # dynasty -> reign
        self.compounds = collections.defaultdict(set)     # office base_office_id 反查
        self.subordinates = collections.defaultdict(set)  # 官署 superiors 反查
        self.members = collections.defaultdict(set)       # 官署 group_ids 反查
        self.offices = collections.defaultdict(set)       # office.institution_ref 反查
        self.by_ruler = collections.defaultdict(list)     # (dynasty_id, ruler 名) -> [reign]
        self.by_name = collections.defaultdict(list)      # 年號名 -> [reign]
        for i, d in sorted(E.items()):
            st = d.get('subtype')
            if st in ('dynasty', 'office') or is_institution(d):
                p = rid(d.get('parent_id'))
                if p in E and p != i:
                    self.children[p].add(i)
            if st == 'reign':
                dy = rid(d.get('dynasty_id'))
                if dy in E:
                    self.reigns[dy].add(i)
                ru = (d.get('ruler') or {}).get('name') if isinstance(d.get('ruler'), dict) else None
                if ru:
                    self.by_ruler[(dy, ru)].append(i)
                if isinstance(d.get('primary_name'), str):
                    self.by_name[d['primary_name']].append(i)
            if st == 'office':
                b = rid(d.get('base_office_id'))
                if b in E:
                    self.compounds[b].add(i)
                ins = rid(d.get('institution_ref'))
                if ins in E:
                    self.offices[ins].add(i)
            if st == 'place':
                for h in d.get('history') or []:
                    p = rid(h.get('parent_id')) if isinstance(h, dict) else None
                    if p in E and p != i:
                        self.children[p].add(i)
            if is_institution(d):
                for s in d.get('superiors') or []:
                    sid = rid(s.get('id')) if isinstance(s, dict) else None
                    if sid in E:
                        self.subordinates[sid].add(i)
                for g in _ids(d.get('group_ids')):
                    if rid(g) in E:
                        self.members[rid(g)].add(i)
        for lst in list(self.by_ruler.values()) + list(self.by_name.values()):
            lst.sort(key=lambda r: (_start(E[r]) is None, _start(E[r]) or 0, r))
        self.dyn_keys = self._keys(lambda d: d.get('subtype') in ('dynasty', 'reign'), self._dr_cand,
                                   lambda c: (c['subtype'] != 'dynasty', c.get('start') or 0, c['id']))
        self.off_keys = self._keys(lambda d: d.get('subtype') == 'office' or is_institution(d), self._off_cand,
                                   lambda c: (c['subtype'] != 'office', LEVEL_ORDER.get(c.get('level'), 3), c['id']))
        self.pl_keys = self._place_keys()

    # ---------- 卡片 ----------
    def name(self, i):
        return (self.E.get(self.rid(i)) or {}).get('primary_name')

    def dyn_card(self, i):
        d = self.E[i]
        return _clean({'id': i, 'name': d.get('primary_name'), 'start': _start(d), 'end': _end(d)})

    def reign_card(self, i):
        d = self.E[i]
        ru = d.get('ruler') if isinstance(d.get('ruler'), dict) else {}
        return _clean({'id': i, 'name': d.get('primary_name'), 'start': _start(d), 'end': _end(d),
                       'ruler': ru.get('name'), 'dynasty': self.name(d.get('dynasty_id'))})

    def office_card(self, i):
        d = self.E[i]
        dy = [self.rid(x) for x in _ids(d.get('dynasty_ids'))]
        return _clean({'id': i, 'name': d.get('primary_name'),
                       'level': d.get('office_level') or d.get('institution_level'),
                       'dynasties': [self.name(x) for x in dy if self.name(x)]})

    def place_card(self, i):
        d = self.E[i]
        return _clean({'id': i, 'name': d.get('primary_name'), **(self.span(d) or {})})

    def people_card(self, i):
        d = self.E[i]
        return _clean({'id': i, 'name': d.get('primary_name'), 'dyn': d.get('dynasty')})

    def cards(self, ids, maker, key=None):
        ids = sorted(ids, key=key or (lambda x: x))
        return [self.card(x, maker) for x in ids]

    def by_start(self, x):
        d = self.E[x]
        return (_start(d) is None, _start(d) or 0, x)

    @staticmethod
    def span(d):
        ss = [h.get('start') for h in d.get('history') or [] if isinstance(h, dict) and isinstance(h.get('start'), int)]
        ee = [h.get('end') for h in d.get('history') or [] if isinstance(h, dict) and isinstance(h.get('end'), int)]
        if not ss and not ee:
            return None
        return _clean({'start': min(ss) if ss else None, 'end': max(ee) if ee else None})

    # ---------- 派生欄 ----------
    def derive(self, eid, d):
        """回本條應加的 `_` 欄（dict）。eid 是本倉記錄 id（草稿已升格者也照算，以其正式條為準不重複）。"""
        v = {}
        if eid not in self.E:          # 已升格的草稿條：產物照舊出，但不另派生（正式條才有）
            return v
        st = d.get('subtype')
        if st == 'dynasty':
            ch = self.children.get(eid)
            if ch:
                v['_children'] = self.cards(ch, self.dyn_card, self.by_start)
            anc, seen, p = [], {eid}, self.rid(d.get('parent_id'))
            while p in self.E and p not in seen and len(anc) < 3:
                anc.append(self.card(p, self.dyn_card))
                seen.add(p)
                p = self.rid(self.E[p].get('parent_id'))
            if anc:
                v['_ancestors'] = anc
            rs = self.reigns.get(eid)
            if rs:
                v['_reigns'] = self.cards(rs, self.reign_card, self.by_start)
        elif st == 'reign':
            dy = self.rid(d.get('dynasty_id'))
            if dy in self.E:
                v['_dynasty'] = self.card(dy, self.dyn_card)
            ru = d.get('ruler') if isinstance(d.get('ruler'), dict) else {}
            pe = self.rid(ru.get('entity_id'))
            if pe in self.E:
                v['_ruler'] = self.card(pe, self.people_card)
            if ru.get('name'):
                lst = self.by_ruler.get((dy, ru['name'])) or []
                if eid in lst:
                    v['_index_in_reign'] = lst.index(eid) + 1
            same = [x for x in self.by_name.get(d.get('primary_name'), ()) if x != eid]
            if same:
                v['_same_name'] = [self.card(x, self.reign_card) for x in same]
        elif st == 'office':
            ch = self.children.get(eid)
            if ch:
                v['_children'] = self.cards(ch, self.office_card)
            co = self.compounds.get(eid)
            if co:
                v['_compounds'] = self.cards(co, self.office_card)
        elif st == 'place':
            ch = self.children.get(eid)
            if ch:
                v['_children'] = self.cards(ch, self.place_card)
            sp = self.span(d)
            if sp:
                v['_span'] = sp
        elif is_institution(d):
            for key, src in (('_children', self.children), ('_subordinates', self.subordinates),
                             ('_members', self.members)):
                got = src.get(eid)
                if got:
                    v[key] = self.cards(got, self.office_card)
            of = self.offices.get(eid)
            if of:
                v['_offices'] = self.cards(of, self.office_card)
        if st == 'people':
            v.update(self.dynasty_ref(d.get('dynasty')))
        return v

    def dynasty_ref(self, name):
        """按朝代名解出朝代條：唯一且不歧義 → `_dynasty_id`；否則有候選 → `_dynasty_candidates`。"""
        if not isinstance(name, str) or not name:
            return {}
        cs = [c for c in self.dyn_keys.get(name) or self.dyn_keys.get(name.translate(VARIANT)) or []
              if c['subtype'] == 'dynasty']
        ids = sorted({c['id'] for c in cs})
        if len(ids) == 1 and not any(c.get('ambiguous') for c in cs):
            return {'_dynasty_id': ids[0]}
        if ids:
            return {'_dynasty_candidates': ids}
        return {}

    # ---------- 鍵表 ----------
    def _keys(self, want, cand, order):
        keys = collections.defaultdict(dict)        # 鍵 -> {id: 候選}；同條的規範名與別名歸一後同鍵者只留先出現的一條
        for i, d in sorted(self.E.items()):
            if not want(d):
                continue
            for nm, via, amb in _names(d):
                c = cand(i, d, via, amb)
                for k in {nm, nm.translate(VARIANT)}:
                    keys[k].setdefault(i, c)
        return {k: sorted(v.values(), key=order) for k, v in sorted(keys.items())}

    def _dr_cand(self, i, d, via, amb):
        c = {'id': i, 'subtype': d['subtype'], 'primary_name': d['primary_name'], 'via': via}
        if amb:
            c['ambiguous'] = True
        if _start(d) is not None:
            c['start'] = _start(d)
        if _end(d) is not None:
            c['end'] = _end(d)
        if d['subtype'] == 'reign':
            dy = self.rid(d.get('dynasty_id'))
            c['dynasty_id'] = dy
            c['dynasty'] = self.name(dy)
            ru = d.get('ruler') if isinstance(d.get('ruler'), dict) else {}
            if ru.get('name'):
                c['ruler'] = ru['name']
        elif d.get('parent_id'):
            c['parent_id'] = self.rid(d['parent_id'])
        return _clean(c)

    def _off_cand(self, i, d, via, amb):
        off = d.get('subtype') == 'office'
        c = {'id': i, 'subtype': 'office' if off else '官署',
             'level': d.get('office_level' if off else 'institution_level'),
             'primary_name': d['primary_name'], 'via': via}
        if amb:
            c['ambiguous'] = True
        dy = [self.rid(x) for x in _ids(d.get('dynasty_ids'))]
        if dy:
            c['dynasty_ids'] = dy
            c['dynasties'] = [self.name(x) for x in dy]
        for k in ('parent_id', 'base_office_id', 'institution_ref'):
            if d.get(k):
                c[k] = self.rid(d[k])
        if isinstance(d.get('qualifier'), dict):
            q = dict(d['qualifier'])
            if q.get('target'):
                q['target'] = self.rid(q['target'])
            c['qualifier'] = q
        if d.get('office_class'):
            c['office_class'] = d['office_class']
        if isinstance(d.get('rank'), dict) and d['rank'].get('text'):
            c['rank'] = d['rank']['text']
        return _clean(c)

    # ---------- 地名鍵表 ----------
    def _seg(self, h):
        s = {'name_then': h.get('name'), 'start': h.get('start'), 'end': h.get('end'), 'level': h.get('level')}
        p = self.rid(h.get('parent_id'))
        if p:
            s['parent_id'] = p
            s['parent'] = self.name(p)
        s['dynasties'] = [self.name(x) for x in _ids(h.get('dynasty_ids'))]
        return _clean(s)

    def _place_cand(self, i, d, via, amb, segs):
        hist = [h for h in d.get('history') or [] if isinstance(h, dict)]
        c = {'id': i, 'subtype': 'place', 'primary_name': d['primary_name'], 'via': via,
             'level': hist[-1].get('level') if hist else None,
             'start': min((h['start'] for h in hist if isinstance(h.get('start'), int)), default=None),
             'end': max((h['end'] for h in hist if isinstance(h.get('end'), int)), default=None),
             'modern': (d.get('modern') or {}).get('text') if isinstance(d.get('modern'), dict) else None,
             'segments': segs}
        if amb:
            c['ambiguous'] = True
        return _clean(c)

    def _place_keys(self):
        """via 先後：primary_name → 別名（全稱除外）→ 沿革（各段當時名）→ 去通名；同條同鍵只留先出現者。
        排序：只靠去通名命中者在後，其餘按 start、id。≥2 候選時至多標一個 default（mark_default）。"""
        places = {i: d for i, d in self.E.items() if d.get('subtype') == 'place' and isinstance(d.get('primary_name'), str)}
        keys = collections.defaultdict(dict)
        for i, d in sorted(places.items()):
            names = [(nm, via, amb, []) for nm, via, amb in _names(d)]
            bynm = collections.defaultdict(list)
            for h in d.get('history') or []:
                if isinstance(h, dict) and isinstance(h.get('name'), str) and h['name']:
                    bynm[h['name']].append(self._seg(h))
            names += [(nm, '沿革', False, sg) for nm, sg in bynm.items()]
            names += [(nm[:-1], '去通名', amb, sg) for nm, _, amb, sg in list(names)
                      if nm.endswith(PLACE_SUFFIX) and len(nm) >= 3]
            for nm, via, amb, sg in names:
                c = self._place_cand(i, d, via, amb, sg)
                for k in {nm, nm.translate(VARIANT)}:
                    keys[k].setdefault(i, c)
        out = {k: sorted(v.values(), key=lambda c: (c['via'] == '去通名', c.get('start') or 0, c['id']))
               for k, v in sorted(keys.items())}
        up = {i: {self.rid(h['parent_id']) for h in d.get('history') or [] if isinstance(h, dict) and h.get('parent_id')}
              for i, d in places.items()}
        anc = {}
        for i in places:
            seen, stack = set(), list(up.get(i, ()))
            while stack:
                x = stack.pop()
                if x not in seen:
                    seen.add(x)
                    stack.extend(up.get(x, ()))
            anc[i] = seen
        for v in out.values():
            mark_default(v, anc)
        self.n_place = len(places)
        return out

    def products(self):
        E = self.E
        n = collections.Counter('官署' if is_institution(d) else d.get('subtype') for d in E.values())
        dr = {'version': KEYS_VERSION,
              'count': {'keys': len(self.dyn_keys), 'dynasty': n['dynasty'], 'reign': n['reign']},
              'normalize': NORMALIZE, 'keys': self.dyn_keys}
        of = {'version': KEYS_VERSION,
              'count': {'keys': len(self.off_keys), 'office': n['office'], '官署': n['官署'],
                        'multi_candidate_keys': sum(1 for v in self.off_keys.values() if len(v) > 1)},
              'normalize': NORMALIZE, 'keys': self.off_keys}
        pl = {'version': KEYS_VERSION,
              'count': {'keys': len(self.pl_keys), 'place': self.n_place,
                        'multi_candidate_keys': sum(1 for v in self.pl_keys.values() if len(v) > 1),
                        'default_marked': sum(1 for v in self.pl_keys.values() if any(c.get('default') for c in v))},
              'normalize': NORMALIZE, 'keys': self.pl_keys}
        return {'dynasty_reign_keys.json': dr, 'office_keys.json': of, 'place_keys.json': pl}


def mark_default(cands, anc):
    """≥2 候選時至多標一個 `default`（place_keys-交接 §四）：① 恰有一個候選是 primary_name 命中 → 標它；
    ② 否則取級別最低者 L（最低一級有兩個以上則不標），僅當其餘候選都在 L 的沿革上級鏈閉包裡時標 L；③ 其餘不標。"""
    if len(cands) < 2:
        return
    prim = [c for c in cands if c['via'] == 'primary_name']
    if len(prim) == 1:
        prim[0]['default'] = True
        return
    ranks = [PLACE_RANK.get(c.get('level'), 9) for c in cands]
    lo = min(ranks)
    if ranks.count(lo) > 1:
        return
    low = cands[ranks.index(lo)]
    if all(c is low or c['id'] in anc.get(low['id'], ()) for c in cands):
        low['default'] = True


def _clean(d):
    return {k: v for k, v in d.items() if v not in (None, '', [], {})}
