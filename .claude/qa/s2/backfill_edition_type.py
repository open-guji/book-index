#!/usr/bin/env python3
"""S2b·Book edition_type 吸收（overview issue #157）：由 `edition` 文字機械推。

對全庫**尚無** `edition_type` 的 Book（含台北故宮批次跑過 `backfill_physical_description_npm.py`
之後剩下未定者），把 `edition` 欄位的文字丟進 `classify()`，能決者寫入受控十詞表之一；
判不出者（多為出土簡帛整理本、碑刻殘石、單一朝代字之類）留空，不猜。

用法：
  python3 .claude/qa/s2/backfill_edition_type.py [--limit N] [--dry-run]

冪等：已有 `edition_type` 者跳過，可在合流後重跑。
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

EDITION_TYPES = ('刻本', '抄本', '稿本', '活字本', '石印本', '鉛印本', '影印本', '套印本', '拓本', '其他')


def classify(text):
    """由版本說明文字（Book.edition 或資料倉之 extra.版本類型／edition／version）推 edition_type。
    規則按強特徵詞優先序逐條試，能決一即回傳；試盡不決回傳 None（不猜）。"""
    if not text:
        return None
    t = text
    if re.search('聚珍|活字', t):
        return '活字本'
    if re.search('拓本|拓片|搨本', t):
        return '拓本'
    if re.search('石印', t):
        return '石印本'
    if re.search('鉛印|鉛字|排印', t):
        return '鉛印本'
    if re.search('影印|景印|摹印', t):
        return '影印本'
    if re.search('套印|三色套|五色套', t):
        # 裸「朱墨」不足判套印：「朱墨鈔本／朱墨寫本」是雙色手抄（形容墨色，非刷印技法），
        # 全庫核對 84 條「朱墨」+明確套印字樣者與 18 條「朱墨」無套印字樣者，後者本體皆是
        # 鈔／寫／石印／鉛印，無一例外真是套印本（overview#214 體檢確認 7 條同類誤判）。
        return '套印本'
    if re.search('稿本', t):
        return '稿本'
    if re.search('寫刻|寫刊', t):
        # 版本學術語「寫刻本／寫刊本」＝依名家手跡上板精刻之刻本，仍屬刻本，非手寫抄本；
        # 須先於裸「寫」判准攔截，否則被誤判抄本（overview#214 體檢新發現之 pipeline bug）。
        return '刻本'
    if re.search('鈔本|抄本|寫本|寫', t):
        return '抄本'
    if '四庫全書' in t and re.search('文淵閣|文溯閣|文津閣|文瀾閣|摛藻堂|薈要', t):
        return '抄本'
    if re.search('銅版|珂羅版', t):
        return '其他'
    if re.search('朱印', t):
        return '刻本'
    if re.search('刊本|刻本|刊刻|雕本|槧本|刊|刻', t):
        return '刻本'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None, help='本批最多新增幾條（用於先試批）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    n_total = n_has_edition_field = n_skipped_done = n_added = n_unmapped = 0
    dist = {}
    unmapped_ids = []
    touched = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        n_total += 1
        if 'edition_type' in d:
            n_skipped_done += 1
            continue
        ed = d.get('edition')
        if not ed:
            continue
        n_has_edition_field += 1
        if a.limit is not None and n_added >= a.limit:
            continue
        t = classify(ed)
        if not t:
            n_unmapped += 1
            unmapped_ids.append({'id': d['id'], 'edition': ed})
            continue
        dist[t] = dist.get(t, 0) + 1
        if not a.dry_run:
            dd, fmt = jio.load(rel)
            if 'edition_type' not in dd:
                dd['edition_type'] = t
                jio.save(rel, dd, fmt)
        touched.append(d['id'])
        n_added += 1

    print(f'Book 總數                       {n_total}')
    print(f'已有 edition_type（冪等跳過）    {n_skipped_done}')
    print(f'有 edition 欄位待判              {n_has_edition_field}')
    print(f'本次新增 edition_type            {n_added}')
    for k, v in sorted(dist.items(), key=lambda x: -x[1]):
        print(f'  {k:6s} {v}')
    print(f'判不出（留空）                   {n_unmapped}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')
        if unmapped_ids:
            out = os.path.join(ROOT, '.claude', 'qa', 's2', 'edition_type-判不出清單.json')
            json.dump(unmapped_ids, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print(f'判不出清單已寫 {out}（{len(unmapped_ids)} 條）')
    else:
        print(f'已寫入 {len(touched)} 個 Book 檔')


if __name__ == '__main__':
    main()
