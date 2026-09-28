#!/usr/bin/env python3
"""S2b·Book physical_description＋edition_type 吸收（overview issue #157）：
台北故宮批次的機械回填，接 S2 `provenance` 吸收（overview#129）。

有 `provenance[].source == "metadata.npm_item_id"` 的 Book（約 17,540 條），按其
`call_number`（＝典藏號）與資料倉 open-guji-core/book_index_json
`library_data/臺灣故宮博物院善本古籍/`（`holding_id`＝典藏號）對照：
  - `extra.行格` ＋ `extra.版式` 中可辨之邊欄／版心／魚尾詞 → `physical_description.leaf_style`
  - `extra.裝訂形式`（無則退 `extra.裝訂`） → `binding`
  - `extra.版框高廣`（形如「23.5x14.5公分」，先高後廣） → `dimensions`
  - `extra.保存現況` → `condition`
  - `extra.版本類型`（推不出退 `edition`／`version`） → `Book.edition_type`
只讀資料倉，不改它。四內容子欄全空者 `physical_description` 不寫；`edition_type` 判不出留空。

用法：
  python3 .claude/qa/s2/backfill_physical_description_npm.py --warehouse <book_index_json checkout> [--limit N] [--dry-run]

冪等：已有 `physical_description` 者跳過該欄，已有 `edition_type` 者跳過該欄，可在合流後重跑。
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
sys.path.insert(0, os.path.dirname(__file__))
import jio
from backfill_edition_type import classify

SOURCE_NOTE = 'library_data/臺灣故宮博物院善本古籍（依 provenance.call_number＝holding_id 對照）'

BORDER_RE = re.compile(r'(?:左右|四周|上下)(?:雙邊|單邊|雙欄|單欄)')
MOUTH_RE = re.compile(r'[白黑]口')
FISHTAIL_RE = re.compile(r'(?:無|單|雙)(?:黑)?魚尾')
DIM_RE = re.compile(r'([\d.]+)\s*[x×*]\s*([\d.]+)\s*公分')


def load_warehouse_holdings(warehouse_root):
    d = os.path.join(warehouse_root, 'library_data', '臺灣故宮博物院善本古籍')
    holding = {}
    for f in sorted(glob.glob(os.path.join(d, 'part-*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            hid = r.get('holding_id')
            if hid:
                holding[hid] = r
    return holding


def build_leaf_style(xingge, banshi):
    parts = []
    if xingge:
        parts.append(xingge.strip().rstrip('。'))
    if banshi:
        for pat in (BORDER_RE, MOUTH_RE, FISHTAIL_RE):
            m = pat.search(banshi)
            if m:
                parts.append(m.group(0))
    return '，'.join(p for p in parts if p)


def build_dimensions(raw):
    if not raw:
        return ''
    m = DIM_RE.search(raw)
    if m:
        h, w = m.group(1), m.group(2)
        return f'版框高{h}公分，廣{w}公分'
    return raw.strip()


def npm_call_number(book):
    for p in (book.get('provenance') or []):
        if isinstance(p, dict) and p.get('source') == 'metadata.npm_item_id':
            return p.get('call_number')
    return (book.get('metadata') or {}).get('npm_item_id')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--warehouse', required=True)
    ap.add_argument('--limit', type=int, default=None, help='本批最多新增幾條 physical_description（用於先試 200）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    holding = load_warehouse_holdings(a.warehouse)
    print(f'資料倉典藏號 {len(holding)} 條', file=sys.stderr)

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_candidates = n_pd_skipped = n_pd_added = n_pd_empty = n_unmatched = 0
    n_et_added = 0
    et_dist = {}
    touched_pd, touched_et = [], []

    n_batch = 0
    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        cn = npm_call_number(d)
        if not cn:
            continue
        if 'physical_description' in d and 'edition_type' in d:
            n_pd_skipped += 1
            continue
        if a.limit is not None and n_batch >= a.limit:
            continue
        n_batch += 1
        n_candidates += 1
        rec = holding.get(cn)
        if not rec:
            n_unmatched += 1
        extra = (rec.get('extra') or {}) if rec else {}

        need_pd = 'physical_description' not in d
        need_et = 'edition_type' not in d

        pd_entry = None
        if need_pd:
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
                n_pd_added += 1
            else:
                n_pd_empty += 1

        et_value = None
        if need_et:
            et_value = classify(extra.get('版本類型')) or classify(rec.get('edition') if rec else None) or classify(rec.get('version') if rec else None)
            if et_value:
                n_et_added += 1
                et_dist[et_value] = et_dist.get(et_value, 0) + 1

        if not a.dry_run and (pd_entry or et_value):
            dd, fmt = jio.load(rel)
            changed = False
            if pd_entry and 'physical_description' not in dd:
                dd['physical_description'] = pd_entry
                changed = True
            if et_value and 'edition_type' not in dd:
                dd['edition_type'] = et_value
                changed = True
            if changed:
                jio.save(rel, dd, fmt)
        if pd_entry:
            touched_pd.append(d['id'])
        if et_value:
            touched_et.append(d['id'])

    print(f'台北故宮候選（provenance.source=npm_item_id） {n_candidates}')
    print(f'  對不上資料倉典藏號                        {n_unmatched}')
    print(f'physical_description 已有（冪等跳過）        {n_pd_skipped}')
    print(f'physical_description 本次新增                {n_pd_added}')
    print(f'  四子欄全空未寫                             {n_pd_empty}')
    print(f'edition_type 本次新增                        {n_et_added}')
    for k, v in sorted(et_dist.items(), key=lambda x: -x[1]):
        print(f'  {k:6s} {v}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')
    else:
        print(f'physical_description 寫入 {len(touched_pd)} 檔，edition_type 寫入 {len(touched_et)} 檔')


if __name__ == '__main__':
    main()
