#!/usr/bin/env python3
"""S2b·Book physical_description 吸收（overview issue #157）：
其余 Book（非台北故宮批）之 description 原文行款抽取。

只在 `description.text` 明寫半葉行款原文時抽取 `leaf_style`（如「每半葉十行行二十二字，
白口，四周單邊，無魚尾」），偶帶 `dimensions`（如原文明寫「板框高19.9公分，寬14.5公分」）；
每行字數隨圖文分佈而不一者（如「因兩端各二行無圖，中間有圖的十一行行二十六字」），只取
半葉行數，不臆補一個劃一的字數。抽不到、或只抽到孤立數字而無把握者，不寫。

用法：
  python3 .claude/qa/s2/backfill_physical_description_desc.py [--dry-run]

冪等：已有 physical_description 者跳過；台北故宮批（provenance.source=metadata.npm_item_id）
不在本腳本範圍內，見 backfill_physical_description_npm.py。
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

NUM = r'(?:[一二三四五六七八九十百廿卅]+|\d+)'
LEAF_CORE = re.compile(rf'每?半葉\s*{NUM}\s*行(?:[，、\s]*行)?(?:\s*{NUM}\s*字)?')
CATS = [
    re.compile(r'[白黑]口'),
    re.compile(r'(?:左右|四周|上下)(?:雙邊|單邊|雙欄|單欄)'),
    re.compile(r'(?:無|單|雙)(?:黑)?魚尾'),
]
STOP_CHARS = '。；\n'
DIM_RE = re.compile(r'(?:板框高|框高|書高)\s*[\d.．]+\s*公分[，,]?\s*寬\s*[\d.．]+\s*公分')


def extract_leaf(text):
    m = LEAF_CORE.search(text)
    if not m:
        return None
    kept = [m.group(0)]
    pos = m.end()
    tail = text[pos:]
    while True:
        stop_idx = min([i for i in (tail.find(c) for c in STOP_CHARS) if i != -1], default=len(tail))
        segment = tail[:stop_idx]
        if not re.match(r'^[，、]', segment):
            break
        clause = segment[1:]
        sub = clause.split('，')[0].split('、')[0]
        if any(p.search(sub) for p in CATS):
            kept.append(sub)
            tail = tail[1 + len(sub):]
            continue
        break
    return '，'.join(kept)


def extract_dimensions(text):
    m = DIM_RE.search(text)
    return m.group(0) if m else ''


def get_text(book):
    desc = book.get('description')
    if isinstance(desc, dict):
        return desc.get('text') or ''
    if isinstance(desc, str):
        return desc
    return ''


def is_npm(book):
    return any(isinstance(p, dict) and p.get('source') == 'metadata.npm_item_id'
               for p in (book.get('provenance') or []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_total = n_skipped = n_added = n_no_leaf = 0
    touched = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        if is_npm(d):
            continue
        if 'physical_description' in d:
            n_skipped += 1
            continue
        text = get_text(d)
        if not text or '半葉' not in text:
            continue
        n_total += 1
        leaf = extract_leaf(text)
        if not leaf:
            n_no_leaf += 1
            continue
        dims = extract_dimensions(text)
        entry = {
            'leaf_style': leaf, 'binding': '', 'dimensions': dims, 'condition': '',
            'source': 'description 原文抽取',
        }
        if not a.dry_run:
            dd, fmt = jio.load(rel)
            if 'physical_description' not in dd:
                dd['physical_description'] = entry
                jio.save(rel, dd, fmt)
        touched.append((d['id'], leaf, dims))
        n_added += 1

    print(f'description 含「半葉」候選數           {n_total}')
    print(f'已有 physical_description（冪等跳過）  {n_skipped}')
    print(f'本次新增 physical_description           {n_added}')
    print(f'  含 dimensions                          {sum(1 for _, _, dm in touched if dm)}')
    print(f'抽不到 leaf_style（不寫）                {n_no_leaf}')
    for cid, leaf, dims in touched:
        print(f'  {cid}: {leaf}' + (f'　|　{dims}' if dims else ''))
    if a.dry_run:
        print('（--dry-run，未寫盤）')
    else:
        print(f'已寫入 {len(touched)} 個 Book 檔')


if __name__ == '__main__':
    main()
