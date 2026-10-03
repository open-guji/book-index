#!/usr/bin/env python3
"""S5e·「印刷本」候选扫描（overview#233，据 #230 用户答复新增之词）：

只扫不改——扫全库 Book，找出可能该归「印刷本」（现代出版社出版、非鉛印之印本，
如膠印、平版、數碼印刷）的候选。判断依据（二者居一）：
  1. `edition` 原文带现代出版社名（「…出版社」「…書局」「…印書館」「…出版公司」等）
     且伴一個阿拉伯数字紀年（如「19xx 年版」）——阿拉伯數字紀年本身即現代出版慣例之標記，
     與傳統刻本慣用之干支／帝號紀年不同；
  2. 可判定之刊年（`Book.dating.year`，或 `edition` 原文中之阿拉伯數字紀年）在 1949 年以后。

候选只列出、不改库；是否改判由用户另行裁决。輸出 CSV：id、edition 原文、edition_type 现值。

用法：python3 .claude/qa/s5/s5e_q4_yinshuaben_candidates.py [--out PATH]
"""
import argparse
import csv
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

PUBLISHER_RE = re.compile(r'出版社|出版公司|印刷[所局廠厂]|書局|书局|印書館')
ARABIC_YEAR_RE = re.compile(r'(19[4-9]\d|20\d{2})\s*年')


def arabic_years(text):
    return [int(m.group(1)) for m in ARABIC_YEAR_RE.finditer(text or '')]


def is_candidate(ed, dating_year):
    ed = ed or ''
    years = arabic_years(ed)
    if PUBLISHER_RE.search(ed) and years:
        return True
    if any(y >= 1949 for y in years):
        return True
    if isinstance(dating_year, int) and dating_year >= 1949:
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, '.claude', 'qa', 's5', '印刷本候选.csv'))
    a = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True)):
        d = json.load(open(f, encoding='utf-8'))
        ed = d.get('edition')
        dating = d.get('dating') or {}
        if is_candidate(ed, dating.get('year')):
            rows.append({
                'id': d.get('id'),
                'edition': ed or '',
                'edition_type_现值': d.get('edition_type') or '',
            })

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'edition', 'edition_type_现值'])
        w.writeheader()
        w.writerows(rows)

    print(f'候选 {len(rows)} 条，已写 {a.out}')


if __name__ == '__main__':
    main()
