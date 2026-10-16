"""印章反查表 `index/seals.json` 與分頁 `index/seals/<seal_id>/<n>.json`（GUJI-542 P2）。

來源只有 `Book.provenance[].seal_marks[].seal_id`（單向存，印章條不存全量）。純函式，build_derived 與 verify 共用。

- 計數口徑：`count`＝不同 Book 數（同一 Book 多個館藏本都有此印只算 1）；`seal_id` 沿 `merged_into` 歸到現行印章條；
  不是 seal 或不存在的引用不計（check_v2 的 B-S01 另報）；墓碑 Book 不計。
- 分頁：每頁 ≤PAGE 個 Book id（升序）；`seals.json` 只存 `{seal_id: {count, pages}}`，現行印章條都列（無鈐印者 count 0、pages 0）。
"""
import json
import os

PAGE = 500
MANIFEST = 'index/seals.json'
PAGE_DIR = 'index/seals'


def resolve(sid, ents):
    """沿 merged_into 走到現行印章條；中途斷或成環回 None。"""
    seen = set()
    while sid in ents and isinstance(ents[sid], dict) and ents[sid].get('merged_into'):
        if sid in seen:
            return None
        seen.add(sid)
        sid = ents[sid]['merged_into']
    return sid


def live_seals(ents):
    return sorted(i for i, e in ents.items() if isinstance(e, dict) and e.get('subtype') == 'seal'
                  and not e.get('merged_into'))


def derive(books, ents, page=PAGE):
    """books：iterable of (book_id, book dict)；ents：{entity_id: entity dict}。
    → (manifest, pages, stats)；pages＝{相對路徑: {'seal_id','page','books'}}。"""
    live = set(live_seals(ents))
    by = {s: set() for s in live}
    ignored = 0
    for bid, b in books:
        if not isinstance(b, dict) or b.get('merged_into'):
            continue
        for pv in b.get('provenance') or []:
            marks = pv.get('seal_marks') if isinstance(pv, dict) else None
            if not isinstance(marks, list):
                continue
            for m in marks:
                sid = resolve(m.get('seal_id'), ents) if isinstance(m, dict) else None
                if sid in live:
                    by[sid].add(bid)
                else:
                    ignored += 1
    manifest, pages = {}, {}
    for sid in sorted(by):
        ids = sorted(by[sid])
        n = (len(ids) + page - 1) // page
        manifest[sid] = {'count': len(ids), 'pages': n}
        for k in range(n):
            pages[f'{PAGE_DIR}/{sid}/{k + 1}.json'] = {'seal_id': sid, 'page': k + 1, 'books': ids[k * page:(k + 1) * page]}
    return manifest, pages, {'ignored_marks': ignored}


def files(manifest, pages):
    """→ {相對路徑: 內容（JSON 文本，縮排 2、尾一換行）}。"""
    out = {MANIFEST: json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'}
    for rel, d in pages.items():
        out[rel] = json.dumps(d, ensure_ascii=False, indent=2) + '\n'
    return out


def reconcile(ents, manifest, pages):
    """手寫 `appears_in`（Book 項）與派生表的對賬。→ {seal_id: {'handwritten': n, 'derived': n, 'not_in_derived': [Book id…]}}。
    P5 之前兩者不必相等（appears_in 是代表例，seal_marks 逐步回填）；本函式只報差，不擋。"""
    derived = {}
    for rel, d in pages.items():
        derived.setdefault(d['seal_id'], set()).update(d['books'])
    out = {}
    for sid in sorted(manifest):
        hand = [x.get('id') for x in (ents.get(sid) or {}).get('appears_in') or []
                if isinstance(x, dict) and x.get('ref_type') == 'Book']
        miss = sorted(set(hand) - derived.get(sid, set()))
        if hand or manifest[sid]['count']:
            out[sid] = {'handwritten': len(set(hand)), 'derived': manifest[sid]['count'], 'not_in_derived': miss}
    return out


def prune_stale(root, files_new):
    """刪 root/index/seals/ 下不再產出的頁檔與空目錄；回刪檔數。"""
    n = 0
    base = os.path.join(root, PAGE_DIR)
    for dp, _, fns in os.walk(base, topdown=False):
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, '/')
            if rel not in files_new:
                os.remove(os.path.join(dp, fn))
                n += 1
        if dp != base and not os.listdir(dp):
            os.rmdir(dp)
    return n


def write(root, files_new):
    """寫有變的檔；回 (寫入數, 刪除數)。"""
    w = 0
    for rel, txt in files_new.items():
        p = os.path.join(root, rel)
        try:
            old = open(p, encoding='utf-8').read()
        except FileNotFoundError:
            old = None
        if old != txt:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(txt)
            w += 1
    return w, prune_stale(root, files_new)


def drift(root, files_new):
    """root 內現有檔與重生值之差：[(相對路徑, 'missing'|'differs'|'stale')]。比解析後的 JSON，不比空白。"""
    out = []
    for rel, txt in files_new.items():
        try:
            old = json.load(open(os.path.join(root, rel), encoding='utf-8'))
        except FileNotFoundError:
            out.append((rel, 'missing'))
            continue
        except ValueError:
            out.append((rel, 'differs'))
            continue
        if old != json.loads(txt):
            out.append((rel, 'differs'))
    base = os.path.join(root, PAGE_DIR)
    for dp, _, fns in os.walk(base):
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, '/')
            if rel not in files_new:
                out.append((rel, 'stale'))
    return sorted(out)
