#!/usr/bin/env python3
"""S2b·Book physical_description＋edition_type 吸收（overview issue #157）：
台北故宮批次的機械回填，接 S2 `provenance` 吸收（overview#129）。

有 `provenance[].source == "metadata.npm_item_id"` 的 Book（約 17,540 條），按其
`call_number`（＝典藏號）與資料倉 open-guji-core/book_index_json
`library_data/臺灣故宮博物院善本古籍/`（`holding_id`＝典藏號）對照——**同一 holding_id
可能是一函/一冊裝訂多部書之合訂號**（如《船山遺書》《古今說海》各書共用一個典藏號），
須按書名（及書名尾之「N卷」）挑出本書那一條（`pick_record()`），挑不出（含仍二義）者
`physical_description` 不寫，列入 `physical_description-同號多書挑不出清單.json`：
  - `extra.行格` ＋「；」＋ `extra.版式`，原文接續，不挑詞 → `physical_description.leaf_style`
    （2026-09-28 協調者驗收①訂正：原版只挑邊欄/口/魚尾三詞會把線口、花口、粗黑口、
    細黑口與中縫等站方原文丟掉，違「保留站方措辭」之旨）
  - `extra.裝訂形式`（無則退 `extra.裝訂`） → `binding`
  - `extra.版框高廣`（形如「23.5x14.5公分」，先高後廣） → `dimensions`
  - `extra.保存現況` → `condition`
  - `extra.版本類型`（推不出依次退 `edition`／`version`／本書自己的 `Book.edition`） → `edition_type`
只讀資料倉，不改它。四內容子欄全空者 `physical_description` 不寫；`edition_type` 判不出留空。

用法：
  python3 .claude/qa/s2/backfill_physical_description_npm.py --warehouse <book_index_json checkout> [--limit N] [--dry-run]

每次執行皆按上述規則對候選 Book 重算 `physical_description`／`edition_type` 並與現值比較，
僅相異者改寫（故可重跑收斂，也用於改規則後之全量重算，如 2026-09-28 之訂正）。
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
sys.path.insert(0, os.path.dirname(__file__))
import jio
from backfill_edition_type import classify

SOURCE_NOTE = 'library_data/臺灣故宮博物院善本古籍（依 provenance.call_number＝holding_id 對照，同號多書按書名/卷數挑選）'

DIM_RE = re.compile(r'([\d.]+)\s*[x×*ｘＸ]\s*([\d.]+)\s*(?:公分|cm)', re.IGNORECASE)

_TITLE_NOISE = re.compile(r'[《》「」『』\s]')
_JUAN_SUFFIX = re.compile(r'(?:附[^0-9]*)?(?:存)?[一二三四五六七八九十百千兩]+卷.*$|不分卷.*$')
# 常見異體字（脈脉、岩巖、弦絃、閒閑、注註），書名比對時視同一字——非猜測，係傳統目錄學
# 通行之異體，資料倉與本庫各自習慣不同才致同書兩號比不上（協調者驗收②之 18 條殘餘半數屬此）
_VARIANTS = str.maketrans({'脉': '脈', '巖': '岩', '絃': '弦', '閑': '閒', '註': '注'})


def _normalize_title(s):
    s = _TITLE_NOISE.sub('', s or '')
    s = _JUAN_SUFFIX.sub('', s)
    return s.translate(_VARIANTS)


def load_warehouse_holdings(warehouse_root):
    """holding_id → 該號下全部候選記錄（同號可能不止一書，見協調者驗收②）。"""
    d = os.path.join(warehouse_root, 'library_data', '臺灣故宮博物院善本古籍')
    holding = {}
    for f in sorted(glob.glob(os.path.join(d, 'part-*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            hid = r.get('holding_id')
            if hid:
                holding.setdefault(hid, []).append(r)
    return holding


def pick_record(book_title, candidates):
    """同一 holding_id 可能是一函/一冊裝訂多部書之合訂號（如《船山遺書》《古今說海》之一），
    須按書名（及卷數，含在書名尾之「N卷」）挑出本書那一條；挑不出（含仍二義）者回傳 None，
    不猜（協調者驗收②）。"""
    if len(candidates) == 1:
        return candidates[0]
    nt = _normalize_title(book_title)
    if not nt:
        return None
    exact = [c for c in candidates if _normalize_title(c.get('bookName') or c.get('title') or '') == nt]
    if len(exact) == 1:
        return exact[0]
    contain = [c for c in candidates
               if _normalize_title(c.get('bookName') or c.get('title') or '') in (nt,)
               or nt in _normalize_title(c.get('bookName') or c.get('title') or '')]
    if len(contain) == 1:
        return contain[0]
    return None


def build_leaf_style(xingge, banshi):
    """行款＝行格＋版式原文接續，不挑詞（協調者驗收①：原「只挑邊欄/口/魚尾三詞」會把
    線口／花口／粗黑口／細黑口與中縫等站方原文丟掉，違「保留站方措辭」之旨）。"""
    xingge = (xingge or '').strip()
    banshi = (banshi or '').strip()
    if xingge and banshi:
        return f'{xingge}；{banshi}'
    return xingge or banshi


def build_dimensions(raw):
    if not raw:
        return ''
    m = DIM_RE.search(raw)
    if m:
        h, w = m.group(1), m.group(2)
        return f'版框高{h}公分，廣{w}公分'
    raw = raw.strip()
    # 「公分」「不等」「x公分」「每半葉框x公分」之類無實際數字的佔位文字，不當尺寸資料寫入
    if not re.search(r'\d', raw):
        return ''
    return raw


def npm_call_number(book):
    for p in (book.get('provenance') or []):
        if isinstance(p, dict) and p.get('source') == 'metadata.npm_item_id':
            return p.get('call_number')
    return (book.get('metadata') or {}).get('npm_item_id')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--warehouse', required=True)
    ap.add_argument('--limit', type=int, default=None, help='本批最多處理幾條（用於分批）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    holding = load_warehouse_holdings(a.warehouse)
    print(f'資料倉典藏號 {len(holding)} 個（含同號多書）', file=sys.stderr)

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_candidates = n_ambiguous = n_pd_written = n_pd_cleared = n_et_written = 0
    et_dist = {}
    ambiguous_list, changed_pd_ids, changed_et_ids = [], [], []

    n_batch = 0
    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        cn = npm_call_number(d)
        if not cn:
            continue
        if a.limit is not None and n_batch >= a.limit:
            continue
        n_batch += 1
        n_candidates += 1

        cands = holding.get(cn, [])
        rec = pick_record(d.get('title'), cands) if cands else None
        if cands and rec is None:
            n_ambiguous += 1
            ambiguous_list.append({'id': d['id'], 'title': d.get('title'), 'call_number': cn,
                                    'candidates': [c.get('bookName') for c in cands]})
        extra = (rec.get('extra') or {}) if rec else {}

        pd_entry = None
        if rec:
            leaf_style = build_leaf_style(extra.get('行格'), extra.get('版式'))
            binding = (extra.get('裝訂形式') or extra.get('裝訂') or '').strip().rstrip('。')
            dimensions = build_dimensions(extra.get('版框高廣'))
            condition = (extra.get('保存現況') or '').strip().rstrip('。')
            if leaf_style or binding or dimensions or condition:
                pd_entry = {
                    'leaf_style': leaf_style, 'binding': binding,
                    'dimensions': dimensions, 'condition': condition,
                    'source': SOURCE_NOTE,
                }

        et_value = (classify(extra.get('版本類型')) or classify(rec.get('edition') if rec else None)
                    or classify(rec.get('version') if rec else None) or classify(d.get('edition')))

        if not a.dry_run:
            dd, fmt = jio.load(rel)
            changed = False
            cur_pd = dd.get('physical_description')
            if pd_entry != cur_pd:
                if pd_entry:
                    dd['physical_description'] = pd_entry
                    changed_pd_ids.append(d['id'])
                    changed = True
                elif isinstance(cur_pd, dict) and str(cur_pd.get('source', '')).startswith('library_data/臺灣故宮博物院'):
                    del dd['physical_description']
                    changed_pd_ids.append(d['id'])
                    changed = True
            if et_value and dd.get('edition_type') != et_value:
                dd['edition_type'] = et_value
                changed_et_ids.append(d['id'])
                changed = True
            if changed:
                jio.save(rel, dd, fmt)

        if pd_entry:
            n_pd_written += 1
        elif cands:  # 候選存在但本條清空／未寫（挑不出或四子欄全空）
            n_pd_cleared += 1
        if et_value:
            n_et_written += 1
            et_dist[et_value] = et_dist.get(et_value, 0) + 1

    print(f'台北故宮候選（provenance.source=npm_item_id） {n_candidates}')
    print(f'  同號多書而挑不出（physical_description 不寫）  {n_ambiguous}')
    print(f'physical_description 有內容（本輪計算結果）      {n_pd_written}')
    print(f'physical_description 無內容或挑不出（不寫/清空） {n_pd_cleared}')
    print(f'edition_type 有值（本輪計算結果）                {n_et_written}')
    for k, v in sorted(et_dist.items(), key=lambda x: -x[1]):
        print(f'  {k:6s} {v}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')
        if ambiguous_list:
            out = os.path.join(ROOT, '.claude', 'qa', 's2', 'physical_description-同號多書挑不出清單.json')
            json.dump(ambiguous_list, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print(f'挑不出清單已寫 {out}（{len(ambiguous_list)} 條）')
    else:
        print(f'實際改動：physical_description {len(changed_pd_ids)} 檔，edition_type {len(changed_et_ids)} 檔')


if __name__ == '__main__':
    main()
