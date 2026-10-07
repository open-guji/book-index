"""schema-v2 共用件：讀記錄、辨 sidecar、保格式寫回、關係詞表。

build_derived.py 與 migrate_v2.py 同用，故詞表與「哪些是記錄檔」只在此定一處。
依據：overview `項目進展/古籍目錄/進度/F-數據結構/` F2-2、F2-3、F2-7（§二、§六）。
純標準庫。
"""
import json
import os

TYPES = ('Work', 'Book', 'Collection', 'Entity')

# ---------- 關係詞表（F2-2 §二、F2-7 §六 #1，用戶 10-07 定） ----------
# 成對關係：源檔只存「規範方向」；反向詞只出現在 build 產物。
REVERSE_OF = {
    'part_of': 'has_part',
    'studies': 'studied_by',
    'contains_text_of': 'text_carried_by',
    'preceded_by': 'followed_by',
    'pseudepigraph_of': 'has_pseudepigraph',
    'adapted_from': 'has_adaptation',
}
CANON_OF = {v: k for k, v in REVERSE_OF.items()}      # 反向詞 → 規範詞
RENAME = {'commentary_on': 'studies', 'related_to': 'related'}   # 詞表外、併入既有詞
SYMMETRIC = {'related'}                                 # 對稱：存 id 較小一側
ONE_WAY = {'collected_in', 'derived_from', 'same_entry', 'suspected_same',
           'excerpted_from', 'source_of'}               # 單向，原樣保留
KNOWN_RELATIONS = set(REVERSE_OF) | set(CANON_OF) | set(RENAME) | SYMMETRIC | ONE_WAY

# 迄 M3 前源檔裡仍有、M3 才刪的舊派生欄（build 照算、只報不擋；--strict 時擋）
LEGACY_DERIVED = {
    'Work': {'_edition_count', '_has_image', '_has_text', '_has_collated', '_promoted_to', '_promoted_at'},
    'Book': {'_has_image', '_has_text', '_has_collated', '_promoted_to', '_promoted_at'},
    'Collection': {'_member_count', '_member_type', '_has_image', '_has_text'},
    'Entity': set(),
}
# 迄 M3 前源檔裡仍有的「應派生」非底線欄（反向／副本）
LEGACY_REVERSE = {
    'Work': ('books', 'has_text', 'has_image', 'has_collated'),
    'Book': ('has_text', 'has_image'),
    'Collection': ('books', 'contained_works', 'has_text', 'has_image'),
    'Entity': ('works',),
}


def canon_edge(src, dst, rel):
    """一條 related_works 項 → 規範存儲形 (存儲側, 對方, 規範詞)。未知詞原樣。"""
    rel = RENAME.get(rel, rel)
    if rel in CANON_OF:
        return dst, src, CANON_OF[rel]
    if rel in SYMMETRIC:
        return (src, dst, rel) if src <= dst else (dst, src, rel)
    return src, dst, rel


def expand_edge(s, d, rel):
    """規範邊 → 兩側看到的邊（build 展開）。"""
    out = {(s, d, rel)}
    if rel in REVERSE_OF:
        out.add((d, s, REVERSE_OF[rel]))
    elif rel in SYMMETRIC:
        out.add((d, s, rel))
    return out


def is_stored_form(rec_id, other, rel):
    """這一項在遷移後的源檔裡該不該存在（規範方向、對稱者在小 id 側）。"""
    rel = RENAME.get(rel, rel)
    if rel in CANON_OF:
        return False
    if rel in SYMMETRIC:
        return rec_id <= other
    return True


def merge_notes(notes):
    """兩側 note 簡單拼接（用戶 10-07 定，不設 note_reverse）。去重、保序、去空。"""
    out = []
    for n in notes:
        if not isinstance(n, str):
            continue
        n = n.strip()
        if n and n not in out and not any(n in o for o in out):
            out = [o for o in out if o not in n]
            out.append(n)
    return '；'.join(out) if out else None


def rel_target(r):
    """related_works 項之對方 id：`id` 為正，`work_id` 為舊形（backrefs「坑 54」）。"""
    if not isinstance(r, dict):
        return None
    return r.get('id') or r.get('work_id')


def ref_id(x, *keys):
    """contained_in／books 之項：str 或 dict 兩形。"""
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        for k in keys or ('id',):
            if isinstance(x.get(k), str) and x.get(k):
                return x[k]
    return None


# ---------- 讀檔 ----------
def is_record_path(root, path):
    """記錄檔＝`<Type>/<a>/<b>/<c>/<id>[-題名].json`（正好三層分片）。
    其餘（如 `Collection/h/h/f/<id>/catalog/volume_book_mapping.json`）是 sidecar。"""
    rel = os.path.relpath(path, root).split(os.sep)
    return len(rel) == 5 and rel[0] in TYPES and rel[-1].endswith('.json')


def iter_json(root, typ):
    base = os.path.join(root, typ)
    for dp, dns, fns in os.walk(base):
        dns.sort()
        for fn in sorted(fns):
            if fn.endswith('.json'):
                yield os.path.join(dp, fn)


def detect_format(raw, d):
    """沿用 .claude/qa/jio.py 的判法：縮排 2／1／4，結尾有無換行。"""
    for ind in (2, 1, 4):
        for nl in ('\n', ''):
            if raw == json.dumps(d, ensure_ascii=False, indent=ind) + nl:
                return ind, nl
    return None


def dump(d, fmt):
    ind, nl = fmt or (2, '\n')
    return json.dumps(d, ensure_ascii=False, indent=ind) + nl


class Record:
    __slots__ = ('type', 'id', 'path', 'data', 'raw', 'fmt', 'dup_keys')

    def __init__(self, typ, path, data, raw, fmt, dup_keys=()):
        self.type, self.path, self.data, self.raw, self.fmt = typ, path, data, raw, fmt
        self.dup_keys = list(dup_keys)
        self.id = data.get('id')


def _pairs_hook(dups):
    def hook(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                dups.append(k)
            d[k] = v
        return d
    return hook


def load_repo(root, keep_raw=False):
    """回傳 (records{type:{id:Record}}, sidecars[path], problems[])。
    problems：讀不了的檔、無 id、type 不符、同 id 重複——全列，不吞。"""
    recs = {t: {} for t in TYPES}
    sidecars, problems = [], []
    for t in TYPES:
        for p in iter_json(root, t):
            rel = os.path.relpath(p, root)
            if not is_record_path(root, p):
                sidecars.append(rel)
                continue
            dups = []
            try:
                raw = open(p, encoding='utf-8').read()
                # 遷移時要寫回，故查重複鍵（json 只留後者，寫回即丟前者）
                d = json.loads(raw, object_pairs_hook=_pairs_hook(dups)) if keep_raw else json.loads(raw)
            except Exception as e:  # noqa: BLE001 — 列入報告
                problems.append({'path': rel, 'problem': f'unreadable: {e.__class__.__name__}'})
                continue
            if not isinstance(d, dict) or not isinstance(d.get('id'), str):
                problems.append({'path': rel, 'problem': 'no id'})
                continue
            if str(d.get('type', '')).lower() != t.lower():
                problems.append({'path': rel, 'problem': f"type {d.get('type')!r} under {t}/"})
            if d['id'] in recs[t]:
                problems.append({'path': rel, 'problem': f"duplicate id {d['id']} (also {recs[t][d['id']].path})"})
                continue
            fmt = detect_format(raw, d) if keep_raw else None
            recs[t][d['id']] = Record(t, rel, d, raw if keep_raw else None, fmt, dups)
    return recs, sorted(sidecars), problems
