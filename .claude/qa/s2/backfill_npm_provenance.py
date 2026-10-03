#!/usr/bin/env python3
"""S2·Book provenance 吸收（overview issue #129）：故宮 metadata.npm_item_id → provenance 機械回填。

有 metadata.npm_item_id 的 Book（約 17,540 條，故宮）一律加一項
{institution:"國立故宮博物院", call_number:<npm_item_id>, source:"metadata.npm_item_id"}；
再與資料倉 open-guji-core/book_index_json 的
library_data/臺灣故宮博物院善本古籍/（holding_id＝典藏號）按 call_number＝holding_id 對照，
對上的把該檔 extra.收藏印記 拆成 seals；只讀資料倉，不改它。

用法：
  python3 .claude/qa/s2/backfill_npm_provenance.py --warehouse <book_index_json checkout> [--limit N] [--dry-run]

冪等：已有 provenance 含 source=="metadata.npm_item_id" 之項者跳過，可在合流後重跑。
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

# 「收藏印記」偶爾記的是著錄出處而非藏印本身（全庫僅 3 條，皆故宮舊籍合冊範圍號），
# 含此類詞者不拆為 seals，寧缺毋濫。
CITATION_MARKERS = ('圖書館典藏', '善本書目', '書目版本')


def load_warehouse_holdings(warehouse_root):
    d = os.path.join(warehouse_root, 'library_data', '臺灣故宮博物院善本古籍')
    holding = {}
    for f in sorted(glob.glob(os.path.join(d, 'part-*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            hid = r.get('holding_id')
            if hid:
                holding[hid] = r
    return holding


def extract_seals(record):
    """把 extra.收藏印記 依頓號／逗號拆成 seals 數組（原文照錄，不再拆印文與描述）。"""
    extra = record.get('extra') or {}
    v = extra.get('收藏印記')
    if not v:
        return []
    if any(m in v for m in CITATION_MARKERS):
        return []
    v = v.strip().rstrip('。')
    return [s.strip() for s in re.split('[，、]', v) if s.strip()]


def already_has(prov, source):
    return any(isinstance(p, dict) and p.get('source') == source for p in (prov or []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--warehouse', required=True, help='open-guji-core/book_index_json 的本地 checkout 路徑')
    ap.add_argument('--limit', type=int, default=None, help='本批最多新增幾條 provenance（用於先試 200）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    holding = load_warehouse_holdings(a.warehouse)
    print(f'資料倉典藏號 {len(holding)} 條', file=sys.stderr)

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_total = n_added = n_skipped_done = n_with_seals = n_matched = n_unmatched = 0
    unmatched_ids = []
    touched = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        md = d.get('metadata') or {}
        npm_id = md.get('npm_item_id')
        if not npm_id:
            continue
        n_total += 1
        if already_has(d.get('provenance'), 'metadata.npm_item_id'):
            n_skipped_done += 1
            continue
        if a.limit is not None and n_added >= a.limit:
            continue

        rec = holding.get(npm_id)
        if rec:
            n_matched += 1
        else:
            n_unmatched += 1
            unmatched_ids.append(d['id'])
        seals = extract_seals(rec) if rec else []
        if seals:
            n_with_seals += 1
        entry = {'institution': '國立故宮博物院', 'call_number': npm_id,
                 'seals': seals, 'notes': '', 'source': 'metadata.npm_item_id'}

        if not a.dry_run:
            dd, fmt = jio.load(rel)
            dd.setdefault('provenance', [])
            if not already_has(dd['provenance'], 'metadata.npm_item_id'):
                dd['provenance'].append(entry)
                jio.save(rel, dd, fmt)
        touched.append(d['id'])
        n_added += 1

    print(f'metadata.npm_item_id 之 Book 總數      {n_total}')
    print(f'已有 provenance（冪等跳過）            {n_skipped_done}')
    print(f'本次新增 provenance                    {n_added}')
    print(f'  其中對上資料倉典藏號（含藏印回填）  {n_matched}')
    print(f'  其中帶 seals                         {n_with_seals}')
    print(f'  對不上資料倉典藏號                   {n_unmatched}')
    if unmatched_ids:
        print(f'  對不上清單: {unmatched_ids}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')
    else:
        print(f'已寫入 {len(touched)} 個 Book 檔')


if __name__ == '__main__':
    main()
