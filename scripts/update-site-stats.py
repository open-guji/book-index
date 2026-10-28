#!/usr/bin/env python3
"""重算 resource-site.json 各站点的 imported（正式库实数）。

    python3 scripts/update-site-stats.py            # 只看差异
    python3 scripts/update-site-stats.py --apply    # 写回 resource-site.json

口径（同 2026-10-25 D1）：扫 Work／Book／Collection 三层，不含已并条目（merged_into），
imported＝三层 resources 项数合计。资源 id 按「站点 id 或其别名＋'-'／'_' 前缀」归站。
变动的站点在 notes 开头加一句带日期的分层数。total 不动（来自 library_data）。
"""
import argparse
import collections
import datetime
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIASES = {
    'commons': ['commons', 'wikimedia'],
    'archive': ['archive', 'archive_org', 'internet', 'ia'],
    'nat-archives-jp': ['nat'],
    'ncl-tw': ['ncl'],
    'npm-rarebooks': ['npm'],
    'ioc-shanben': ['ioc'],
    'kyoto-rmda': ['kyoto'],
    'nagoya-u': ['nagoya'],
    'utokyo-da': ['utokyo'],
    'zinbun-toho': ['zinbun'],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    args = ap.parse_args()

    path = os.path.join(ROOT, 'resource-site.json')
    data = json.load(open(path, encoding='utf-8'))
    prefixes = [(p, s['id']) for s in data['resources'] for p in ALIASES.get(s['id'], [s['id']])]

    def site_of(rid):
        for p, sid in prefixes:
            if rid == p or rid.startswith(p + '-') or rid.startswith(p + '_'):
                return sid

    cnt = collections.Counter()
    scanned = collections.Counter()
    for layer in ('Work', 'Book', 'Collection'):
        for f in glob.glob(os.path.join(ROOT, layer, '*', '*', '*', '*.json')):
            d = json.load(open(f, encoding='utf-8'))
            scanned[layer] += 1
            if d.get('merged_into'):
                continue
            for r in d.get('resources') or []:
                sid = site_of(r.get('id', ''))
                if sid:
                    cnt[sid, layer] += 1
    print('扫描文件数', dict(scanned))
    if not all(scanned.values()):
        raise SystemExit('某层扫了 0 个文件，中止')

    changed = 0
    for s in data['resources']:
        w, b, c = (cnt[s['id'], l] for l in ('Work', 'Book', 'Collection'))
        new = w + b + c
        if new == s.get('imported', 0):
            continue
        print(f"{s['id']}: {s.get('imported', 0)} → {new} (Work {w} / Book {b} / Collection {c})")
        s['imported'] = new
        s['notes'] = (f"{args.date} 重新統計：Work 層 {w} 項，Book 層 {b} 項，Collection 層 {c} 項；"
                      f"imported＝三層資源項合計（不含已併條目）。" + (s.get('notes') or ''))
        changed += 1
    print(f'{changed} 个站点有变动')
    if args.apply and changed:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write('\n')


if __name__ == '__main__':
    main()
