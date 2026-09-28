#!/usr/bin/env python3
"""S2·Book provenance 吸收（overview issue #129）：current_location（約 113 條）機械拆分。

113 條有 current_location 的 Book 裡：
  - 19 條同時有 metadata.npm_item_id，其統一編號與 current_location.description 裡的
    「統一編號」逐一核對皆同值——已由 backfill_npm_provenance.py 蓋過，此處不重複加。
  - 其餘 94 條，能機械拆出「單一機構＋索書號」的只有 8 條（見 CURATED 手工表，逐條讀過
    original 之 name／description 訂出，非泛用正則——本批異質性高：多機構混列、無索書號、
    石碑類無「索書號」概念等皆不可強拆，見 skill〈立新檢前先抽樣估假陽性率〉）。
  - 拆不了的 86 條列出清單、不動資料，供人工／後續另開卡處理。

用法：
  python3 .claude/qa/s2/backfill_current_location.py [--dry-run]

冪等：已有 provenance 含 source=="current_location" 之項者跳過。
"""
import argparse, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

# 手工表：book id -> (institution, call_number, notes)。逐條讀 current_location.name／
# description 原文訂出，僅收「單一機構＋可辨識索書號」者（見卡內判準）。
CURATED = {
    '988g9az1my': ('中国国家图书馆', '12433／1148',
                    '／前为原书索书号；后为缩微胶卷号'),
    '988g9az1n2': ('中国国家图书馆', '10708／1146—1148',
                    '28 册（陈杭 1950 捐）'),
    '988g9d5pfy': ('中國國家圖書館', '04110', ''),
    '988g9baa68': ('北京大学图书馆', 'MSB／813．395／0811',
                    '马廉旧藏 6 函 36 册；孤本完帙'),
    '988g9az1mo': ('北京大學圖書館', 'LSB／7308',
                    '孤本，原中屋幸三郎、李盛鐸舊藏，4 函 20 冊'),
    '98ji05um83': ('國家圖書館（臺灣）', '401 09285', '二卷，線裝二冊。'),
    '988g9d5pfk': ('日本東京大學文學部', 'L34432', '孤本，2 函 26 冊。印「南氏／文庫」'),
    '988g9baa6l': ('美國加利福尼亞大學伯克利分校東亞圖書館', 'PL2694．S5　S47',
                    '孤本，薄井恭一舊藏'),
}


def already_has(prov, source):
    return any(isinstance(p, dict) and p.get('source') == source for p in (prov or []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_total = n_added = n_skipped_done = n_covered_by_npm = 0
    unparsed = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        if not d.get('current_location'):
            continue
        n_total += 1
        bid = d['id']
        prov = d.get('provenance') or []

        if already_has(prov, 'metadata.npm_item_id'):
            n_covered_by_npm += 1
            continue
        if already_has(prov, 'current_location'):
            n_skipped_done += 1
            continue

        if bid in CURATED:
            institution, call_number, notes = CURATED[bid]
            entry = {'institution': institution, 'call_number': call_number,
                     'seals': [], 'notes': notes, 'source': 'current_location'}
            if not a.dry_run:
                dd, fmt = jio.load(rel)
                dd.setdefault('provenance', [])
                if not already_has(dd['provenance'], 'current_location'):
                    dd['provenance'].append(entry)
                    jio.save(rel, dd, fmt)
            n_added += 1
        else:
            cl = d['current_location']
            unparsed.append({'id': bid, 'title': d.get('title'),
                              'name': cl.get('name', ''), 'description': cl.get('description', '')})

    print(f'有 current_location 之 Book 總數        {n_total}')
    print(f'已由 npm_item_id 覆蓋（不重複加）        {n_covered_by_npm}')
    print(f'已有 current_location 之 provenance（冪等跳過） {n_skipped_done}')
    print(f'本次新增 provenance                      {n_added}')
    print(f'拆不了、列清單不動                        {len(unparsed)}')
    if not a.dry_run:
        out = os.path.join(ROOT, '.claude', 'qa', 's2', 'current_location-未拆清单.json')
        json.dump(unparsed, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'清單已寫入 {os.path.relpath(out, ROOT)}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')


if __name__ == '__main__':
    main()
