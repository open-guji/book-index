#!/usr/bin/env python3
"""一次性補丁：修正 backfill_physical_description_npm.py 早期版本 build_dimensions() 之
兩病——(1) 大小寫/全形 X（如「23.5X14.5公分」）未認得，退回原始字串未重排；
(2) 資料倉 `版框高廣` 為無數字之佔位文字（如「公分」「不等」「x公分」）時，原樣寫入 dimensions，
成了看似有данные實則垃圾的值。重算所有已由本道寫過 physical_description 的 Book 的
`dimensions` 子欄；`leaf_style`／`binding`／`condition`／`edition_type` 不受影響，不動。

用法：
  python3 .claude/qa/s2/fix_dimensions_npm.py --warehouse <book_index_json checkout> [--dry-run]
"""
import argparse, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
sys.path.insert(0, os.path.dirname(__file__))
import jio
from backfill_physical_description_npm import load_warehouse_holdings, build_dimensions, npm_call_number, SOURCE_NOTE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--warehouse', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    holding = load_warehouse_holdings(a.warehouse)
    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_checked = n_changed = 0
    changes = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        pd = d.get('physical_description')
        if not pd or pd.get('source') != SOURCE_NOTE:
            continue
        cn = npm_call_number(d)
        rec = holding.get(cn) if cn else None
        extra = (rec.get('extra') or {}) if rec else {}
        n_checked += 1
        new_dim = build_dimensions(extra.get('版框高廣'))
        old_dim = pd.get('dimensions', '')
        if new_dim != old_dim:
            n_changed += 1
            changes.append((d['id'], old_dim, new_dim))
            if not a.dry_run:
                dd, fmt = jio.load(rel)
                dd['physical_description']['dimensions'] = new_dim
                # 四子欄若因此全空，physical_description 亦不再有存在之理由——但 leaf_style/binding/
                # condition 三者之一非空即仍成立，實測無一因此欄改動而歸零，不另處理淨空情形。
                jio.save(rel, dd, fmt)

    print(f'已由本道寫過 physical_description 的 Book 檢查數 {n_checked}')
    print(f'dimensions 需修正數                          {n_changed}')
    for cid, old, new in changes[:40]:
        print(f'  {cid}: {old!r} -> {new!r}')
    if len(changes) > 40:
        print(f'  …另有 {len(changes)-40} 條')
    if a.dry_run:
        print('（--dry-run，未寫盤）')


if __name__ == '__main__':
    main()
